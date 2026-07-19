"""Retrieval: hybride — vectorgelijkenis + trefwoorden (NL-full-text), samengevoegd
met Reciprocal Rank Fusion. Waarom hybride: gebruikers noemen letterlijke wetstermen
("bijlage III", "artikel 27") die embeddings te weinig gewicht geven — eval-gedreven
vastgesteld: artikel 113 stond op rang 355 voor de deadlinevraag (zie evals/results).
TOP_K blijft de enige externe knop; kandidaten- en dempingsconstanten staan hier.
"""
from sqlalchemy import Text, cast, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Chunk
from app.rag import mistral

KANDIDATEN = 20  # per zoekpad; ruim boven top_k zodat de fusie echt kan mengen
RRF_K = 60       # gangbare dempingsfactor: verschil tussen rang 1 en 2 telt zwaarder dan 19 en 20


def rrf_fuseer(*rangschikkingen: list[int], k: int = RRF_K) -> list[int]:
    """Voegt rangschikkingen (beste eerst) samen; wie in meer lijsten hoog staat, wint."""
    scores: dict[int, float] = {}
    for lijst in rangschikkingen:
        for rang, chunk_id in enumerate(lijst):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rang + 1)
    return sorted(scores, key=lambda cid: -scores[cid])


def zoek_chunks(sessie: Session, vraag: str, top_k: int | None = None) -> list[Chunk]:
    vraagvector = mistral.embed([vraag])[0]
    vector_ids = list(sessie.scalars(
        select(Chunk.id)
        .order_by(Chunk.embedding.cosine_distance(vraagvector))
        .limit(KANDIDATEN)
    ))

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

    beste = rrf_fuseer(vector_ids, trefwoord_ids)[: top_k or settings.top_k]
    per_id = {c.id: c for c in sessie.scalars(select(Chunk).where(Chunk.id.in_(beste)))}
    return [per_id[cid] for cid in beste]
