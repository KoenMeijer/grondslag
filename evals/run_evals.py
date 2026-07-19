"""Draait de golden set door de echte RAG-keten (in-process, zelfde codepad als
de API) en print een scorekaart. Het JSON-resultaat in evals/results/ is het
regressiespoor én governance-bewijs: aantoonbare, herhaalbare kwaliteitscontrole."""
import datetime
import json
import sys
from pathlib import Path

import yaml

from app.config import settings
from app.db import SessionLocal
from app.rag import service
from evals import scoring

METRICS = ("retrieval", "grounding", "abstentie")


def main() -> None:
    cases = yaml.safe_load(Path("evals/golden_set.yaml").read_text())
    resultaten = []
    with SessionLocal() as sessie:
        for case in cases:
            r = service.beantwoord(sessie, case["vraag"])
            resultaten.append({
                "id": case["id"],
                "categorie": case["categorie"],
                "retrieval": scoring.score_retrieval(case["retrieval_refs"], r.opgehaalde_refs),
                "grounding": scoring.score_grounding(case["grounding_markers"],
                                                     case["verboden_markers"], r.antwoord),
                "abstentie": scoring.score_abstentie(case["abstentie"], r.antwoord),
                "antwoord": r.antwoord,
                "opgehaalde_refs": r.opgehaalde_refs,
            })

    print(f"\n{'case':<40} {'retr':>5} {'grond':>6} {'abst':>5}")
    for r in resultaten:
        v = {m: "✓" if r[m] else "✗" for m in METRICS}
        print(f"{r['id']:<40} {v['retrieval']:>5} {v['grounding']:>6} {v['abstentie']:>5}")
    for m in METRICS:
        n = sum(r[m] for r in resultaten)
        print(f"{m}: {n}/{len(resultaten)}")

    stempel = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    uit = Path("evals/results") / f"run-{stempel}.json"
    uit.write_text(json.dumps({
        "tijdstip": stempel,
        "config": {"chat_model": settings.chat_model, "embed_model": settings.embed_model,
                   "top_k": settings.top_k},
        "resultaten": resultaten,
    }, ensure_ascii=False, indent=2))
    print(f"\nresultaat: {uit}")

    geslaagd = all(all(r[m] for m in METRICS) for r in resultaten)
    sys.exit(0 if geslaagd else 1)


if __name__ == "__main__":
    main()
