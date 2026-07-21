"""Offline meetbank voor het bronquotum: mag een deel van de top-K gereserveerd
worden voor de best gerangschikte NL-chunk?

Aanleiding (21 jul 2026): de vier UAIV-cases faalden alle vier op retrieval —
77 NL-chunks verliezen structureel van 900 EU-chunks die dezelfde begrippen
letterlijker gebruiken. Deze bank meet varianten zonder generatiekosten
(alleen query-embeddings), net als meet_fusie.py.

Gebruik: PYTHONPATH=backend:. .venv/bin/python evals/meet_bronquotum.py
"""
from pathlib import Path

import yaml
from sqlalchemy import Text, cast, func, select
from sqlalchemy.orm import joinedload

from app.db import SessionLocal
from app.models import Chunk
from app.rag import mistral
from app.rag.retrieval import GEWICHT_VECTOR, KANDIDATEN, rrf_fuseer
from evals import scoring

NL_PREFIX = "nl-guidance/"
QUOTA = [0, 1, 2]        # 0 = huidige gedrag (nulmeting)
KANDIDATENREEKS = [KANDIDATEN, 50, 100]   # kandidatendiepte per zoekpad
TOP_K = 5


def fuseer_ids(sessie, vraag: str, vector: list[float], kandidaten: int) -> list[int]:
    """Zelfde fusie als retrieval.zoek_chunks, maar zonder afkappen op top_k."""
    vector_ids = list(sessie.scalars(
        select(Chunk.id).order_by(Chunk.embedding.cosine_distance(vector)).limit(kandidaten)))
    and_vorm = sessie.scalar(select(cast(func.plainto_tsquery("dutch", vraag), Text)))
    kw_ids: list[int] = []
    if and_vorm:
        tsq = func.to_tsquery("dutch", and_vorm.replace(" & ", " | "))
        tsv = func.to_tsvector("dutch", Chunk.tekst)
        kw_ids = list(sessie.scalars(
            select(Chunk.id).where(tsv.op("@@")(tsq))
            .order_by(func.ts_rank(tsv, tsq).desc()).limit(kandidaten)))
    return rrf_fuseer(vector_ids, kw_ids, gewichten=[GEWICHT_VECTOR, 1.0])


def pas_quotum_toe(gerangschikt: list[int], is_nl: dict[int, bool],
                   quotum: int, top_k: int = TOP_K) -> list[int]:
    """Reserveert maximaal `quotum` plaatsen voor de best gerangschikte NL-chunks.

    Promotie kan alleen uit de fusiekandidaten: staat er geen NL-chunk in, dan
    verandert er niets (het quotum verzint geen bron). De oorspronkelijke
    rangorde blijft leidend, zodat de promotie niet ook nog de volgorde in het
    promptvenster verstoort (lost-in-the-middle).
    """
    top = gerangschikt[:top_k]
    if quotum <= 0:
        return top
    tekort = quotum - sum(1 for cid in top if is_nl[cid])
    if tekort <= 0:
        return top
    promoveren = [cid for cid in gerangschikt if is_nl[cid] and cid not in top][:tekort]
    if not promoveren:
        return top
    behouden = top[: top_k - len(promoveren)]
    gekozen = set(behouden) | set(promoveren)
    return [cid for cid in gerangschikt if cid in gekozen][:top_k]


def main() -> None:
    cases = [c for c in yaml.safe_load(Path("evals/golden_set.yaml").read_text())
             if c["retrieval_refs"]]
    vectoren = mistral.embed([c["vraag"] for c in cases])

    varianten = [(k, q) for k in KANDIDATENREEKS for q in QUOTA]
    with SessionLocal() as sessie:
        rijen = []
        for case, vector in zip(cases, vectoren, strict=True):
            rij = {"id": case["id"]}
            for kandidaten in KANDIDATENREEKS:
                gerangschikt = fuseer_ids(sessie, case["vraag"], vector, kandidaten)
                chunks = {c.id: c for c in sessie.scalars(
                    select(Chunk).options(joinedload(Chunk.source))
                    .where(Chunk.id.in_(gerangschikt)))}
                is_nl = {cid: chunks[cid].source.slug.startswith(NL_PREFIX)
                         for cid in gerangschikt}
                # Rang van de eerste chunk die de case écht verwacht: laat zien of
                # de juiste bron überhaupt kandidaat is (promoveren kan niet wat
                # er niet in staat).
                doelrang = next((i + 1 for i, cid in enumerate(gerangschikt)
                                 if any(scoring.ref_matcht(v, chunks[cid].ref)
                                        for v in case["retrieval_refs"])), None)
                rij[f"doel{kandidaten}"] = doelrang
                for q in QUOTA:
                    ids = pas_quotum_toe(gerangschikt, is_nl, q)
                    refs = [chunks[cid].ref for cid in ids]
                    rij[(kandidaten, q)] = any(scoring.ref_matcht(v, r)
                                               for v in case["retrieval_refs"] for r in refs)
            rijen.append(rij)

    kop = "case".ljust(36) + "doelrang(k=20/50/100)   " + " ".join(
        f"k{k}q{q}" for k, q in varianten)
    print(kop)
    print("-" * len(kop))
    for r in rijen:
        rangen = "/".join(str(r[f"doel{k}"] or "-") for k in KANDIDATENREEKS).rjust(12)
        vlaggen = " ".join(("  ✓  " if r[(k, q)] else "  ✗  ") for k, q in varianten)
        print(f"{r['id'][:35].ljust(36)}{rangen}        {vlaggen}")
    print()
    for k, q in varianten:
        print(f"kandidaten {k:3}, quotum {q}: retrieval "
              f"{sum(1 for r in rijen if r[(k, q)])}/{len(rijen)}")


if __name__ == "__main__":
    main()
