"""Scaffolding: draft gegronde concept-vraagpagina's via de eigen RAG-engine.

Publiceert NIETS. Voor elke kandidaat-vraag (uit scripts/vraag_kandidaten.yaml +
de IngezondenVraag-tabel) draait het de eigen `service.beantwoord` en schrijft:
- gegrond antwoord  → content/vragen/_concept/<slug>.md  (frontmatter + body +
  reviewer-notitie); een mens redigeert en verplaatst 'm naar content/vragen/.
- geen_bron         → een regel in content/vragen/_concept/_corpusgaten.md
  (corpusgat of adviesvraag — niet publiceren).

De _concept-map wordt niet door de site geladen (de glob pakt alleen
content/vragen/*.md). Idempotent: bestaande slugs worden overgeslagen.

Gebruik: python scripts/draft_vragen.py [--dry-run] [--limit N]
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, timezone, datetime
from pathlib import Path

import yaml

from app import contentdraft
from app.db import SessionLocal
from app.models import IngezondenVraag
from app.rag import service

ROOT = Path(__file__).resolve().parents[1]
VRAGEN_DIR = ROOT / "frontend" / "content" / "vragen"
CONCEPT_DIR = VRAGEN_DIR / "_concept"
SEED_YAML = ROOT / "scripts" / "vraag_kandidaten.yaml"

slug = contentdraft.slug


def laad_kandidaten(pad_yaml: str, ingezonden: list[str]) -> list[dict]:
    """Voeg seed-yaml + ingezonden vragen samen, ontdubbeld op slug (eerste wint,
    zodat een seed-item met sector voorrang heeft op een kale ingezonden dubbele)."""
    items: list[dict] = []
    with open(pad_yaml, encoding="utf-8") as f:
        for rij in yaml.safe_load(f) or []:
            items.append({"vraag": str(rij["vraag"]).strip(),
                          "sector": rij.get("sector")})
    for v in ingezonden:
        items.append({"vraag": v.strip(), "sector": None})
    gezien: set[str] = set()
    uniek: list[dict] = []
    for it in items:
        s = slug(it["vraag"])
        if s and s not in gezien:
            gezien.add(s)
            uniek.append(it)
    return uniek


def _bestaande_slugs(directory: Path, met_submap: bool = False) -> set[str]:
    if not directory.exists():
        return set()
    return {p.stem for p in directory.glob("*.md") if not p.name.startswith("_")}


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--limit", type=int, default=0)
    args = p.parse_args(argv)

    vandaag = datetime.now(timezone.utc).date().isoformat()
    with SessionLocal() as sessie:
        ingezonden = [r.vraag for r in sessie.query(IngezondenVraag).all()]
        kandidaten = laad_kandidaten(str(SEED_YAML), ingezonden)
        gepubliceerd = _bestaande_slugs(VRAGEN_DIR)
        concepten = _bestaande_slugs(CONCEPT_DIR)

        todo = [k for k in kandidaten
                if not contentdraft.bestaat_al(slug(k["vraag"]), gepubliceerd, concepten)]
        if args.limit:
            todo = todo[: args.limit]

        print(f"{len(kandidaten)} kandidaten, {len(todo)} nieuw te draften"
              f"{' (dry-run)' if args.dry_run else ''}.")
        if args.dry_run:
            for k in todo:
                print(f"  zou draften: {slug(k['vraag'])}  ({k['vraag']})")
            return 0

        CONCEPT_DIR.mkdir(parents=True, exist_ok=True)
        gaten: list[str] = []
        for k in todo:
            res = service.beantwoord(sessie, k["vraag"])
            if res.geen_bron or not res.citaten:
                gaten.append(contentdraft.corpusgat_regel(k["vraag"], vandaag))
                continue
            md = contentdraft.render_concept(
                vraag=k["vraag"], artikel=res.citaten[0].ref,
                stand=res.stand_van_wetgeving, bijgewerkt=vandaag,
                sector=k.get("sector"), antwoord=res.antwoord, citaten=res.citaten,
            )
            (CONCEPT_DIR / f"{slug(k['vraag'])}.md").write_text(md, encoding="utf-8")
            print(f"  concept: {slug(k['vraag'])}")
        if gaten:
            (CONCEPT_DIR / "_corpusgaten.md").write_text(
                "# Corpusgaten / adviesvragen (niet publiceren)\n\n" + "\n".join(gaten) + "\n",
                encoding="utf-8")
            print(f"  {len(gaten)} corpusgaten weggeschreven.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
