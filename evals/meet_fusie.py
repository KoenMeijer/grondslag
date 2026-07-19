"""Offline retrieval-meetbank: scoort fusievarianten op de golden set zonder
generatiekosten (alleen query-embeddings). Hiermee is de gewichtskeuze in
backend/app/rag/retrieval.py (GEWICHT_VECTOR) onderbouwd én reproduceerbaar.

Gebruik: PYTHONPATH=backend:. .venv/bin/python evals/meet_fusie.py
"""
from pathlib import Path

import yaml
from sqlalchemy import Text, cast, func, select

from app.db import SessionLocal
from app.models import Chunk
from app.rag import mistral
from evals import scoring

VARIANTEN = [  # (vector-gewicht, trefwoord-kandidaten)
    (1.0, 20), (1.25, 20), (1.5, 20), (1.75, 20), (2.0, 20), (1.5, 10),
]


def meet(sessie, vraag, vector, gewicht, kw_kand, top_k=5):
    vector_ids = list(sessie.scalars(
        select(Chunk.id).order_by(Chunk.embedding.cosine_distance(vector)).limit(20)))
    and_vorm = sessie.scalar(select(cast(func.plainto_tsquery("dutch", vraag), Text)))
    kw_ids = []
    if and_vorm:
        tsq = func.to_tsquery("dutch", and_vorm.replace(" & ", " | "))
        tsv = func.to_tsvector("dutch", Chunk.tekst)
        kw_ids = list(sessie.scalars(
            select(Chunk.id).where(tsv.op("@@")(tsq))
            .order_by(func.ts_rank(tsv, tsq).desc()).limit(kw_kand)))
    scores: dict[int, float] = {}
    for lijst, w in ((vector_ids, gewicht), (kw_ids, 1.0)):
        for rang, cid in enumerate(lijst):
            scores[cid] = scores.get(cid, 0.0) + w / (61 + rang)
    beste = sorted(scores, key=lambda c: -scores[c])[:top_k]
    return [sessie.get(Chunk, cid).ref for cid in beste]


def main() -> None:
    cases = [c for c in yaml.safe_load(Path("evals/golden_set.yaml").read_text())
             if c["retrieval_refs"]]
    vectoren = mistral.embed([c["vraag"] for c in cases])
    with SessionLocal() as sessie:
        for gewicht, kw_kand in VARIANTEN:
            hits, fouten = 0, []
            for case, vector in zip(cases, vectoren, strict=True):
                refs = meet(sessie, case["vraag"], vector, gewicht, kw_kand)
                ok = scoring.score_retrieval(case["retrieval_refs"], refs)
                hits += ok
                if not ok:
                    fouten.append(case["id"])
            print(f"gewicht {gewicht}:1, kw-kandidaten {kw_kand}: "
                  f"{hits}/{len(cases)}  rood: {fouten}")


if __name__ == "__main__":
    main()
