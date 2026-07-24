"""Retrieval: hybride — vectorgelijkenis + trefwoorden (NL-full-text), samengevoegd
met Reciprocal Rank Fusion. Waarom hybride: gebruikers noemen letterlijke wetstermen
("bijlage III", "artikel 27") die embeddings te weinig gewicht geven — eval-gedreven
vastgesteld: artikel 113 stond op rang 355 voor de deadlinevraag (zie evals/results).
TOP_K blijft de enige externe knop; kandidaten- en dempingsconstanten staan hier.
"""
from dataclasses import dataclass

from sqlalchemy import Text, cast, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Chunk
from app.rag import mistral

KANDIDATEN = 20      # per zoekpad; ruim boven top_k zodat de fusie echt kan mengen
RRF_K = 60           # gangbare dempingsfactor: verschil tussen rang 1 en 2 telt zwaarder dan 19 en 20
GEWICHT_VECTOR = 1.5 # vector blijft leidend; trefwoorden zijn het steuntje voor letterlijke
                     # wetstermen. Offline gemeten (19 jul 2026): 1:1 verdringt de
                     # artikel 3-definities (ts_rank kent geen zeldzaamheidsweging),
                     # alles ≥1.25 scoort 6/8 op de retrieval-cases; 1.5 is het robuuste midden.


def rrf_fuseer(*rangschikkingen: list[int], gewichten: list[float] | None = None,
               k: int = RRF_K) -> list[int]:
    """Voegt rangschikkingen (beste eerst) samen; wie in meer lijsten hoog staat, wint.
    Gewichten laten één pad zwaarder tellen (vector leidend, trefwoorden als steun)."""
    gewichten = gewichten or [1.0] * len(rangschikkingen)
    scores: dict[int, float] = {}
    for lijst, gewicht in zip(rangschikkingen, gewichten, strict=True):
        for rang, chunk_id in enumerate(lijst):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + gewicht / (k + rang + 1)
    return sorted(scores, key=lambda cid: -scores[cid])


@dataclass
class ZoekResultaat:
    chunks: list[Chunk]
    # Cosine-afstand van de beste vectorkandidaat (None bij leeg corpus). Dit is
    # het absolute relevantiesignaal — RRF-scores zijn rang-gebaseerd en zeggen
    # niets over hoe dichtbij de beste match werkelijk was. Gebruikt om bij een
    # abstentie te onderscheiden: niets relevants gevonden (vraag buiten scope)
    # of wél relevante chunks en tóch geweigerd (retrieval-/promptprobleem).
    beste_afstand: float | None


def zoek_chunks(sessie: Session, vraag: str, top_k: int | None = None) -> ZoekResultaat:
    vraagvector = mistral.embed([vraag])[0]
    afstand = Chunk.embedding.cosine_distance(vraagvector)
    vector_rijen = list(sessie.execute(
        select(Chunk.id, afstand)
        .order_by(afstand)
        .limit(KANDIDATEN)
    ))
    vector_ids = [rij[0] for rij in vector_rijen]
    beste_afstand = float(vector_rijen[0][1]) if vector_rijen else None

    # plainto_tsquery geeft AND-semantiek: één vraagwoord dat nergens voorkomt
    # maakt het hele trefwoordpad leeg (gemeten: 0 matches op de deadlinevraag).
    # Daarom herschrijven we de gestemde query naar OR; ts_rank beloont daarna
    # chunks waarin de meeste termen samenkomen.
    and_vorm = sessie.scalar(select(cast(func.plainto_tsquery("dutch", vraag), Text)))
    trefwoord_ids: list[int] = []
    if and_vorm:
        tsq = func.to_tsquery("dutch", and_vorm.replace(" & ", " | "))
        tsv = func.to_tsvector("dutch", Chunk.tekst)
        trefwoord_ids = list(sessie.scalars(
            select(Chunk.id)
            .where(tsv.op("@@")(tsq))
            .order_by(func.ts_rank(tsv, tsq).desc())
            .limit(KANDIDATEN)
        ))

    beste = rrf_fuseer(vector_ids, trefwoord_ids,
                       gewichten=[GEWICHT_VECTOR, 1.0])[: top_k or settings.top_k]
    per_id = {c.id: c for c in sessie.scalars(select(Chunk).where(Chunk.id.in_(beste)))}
    return ZoekResultaat(chunks=[per_id[cid] for cid in beste],
                         beste_afstand=beste_afstand)
