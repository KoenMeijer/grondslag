from pathlib import Path

from app.db import SessionLocal
from app.ingest.__main__ import indexeer_bestand
from app.models import Source

VOORBEELD = """---
bron: "Verordening (EU) 2024/1689"
url: https://example.org
versie: "test"
datum-opgehaald: 2026-07-19
stand-wetgeving: juli 2026
type: wettekst
---
## Artikel 1 — Onderwerp
### Lid 1
Eerste lid.
### Lid 2
Tweede lid.
"""


def nep_embed(teksten):
    return [[0.1] * 1024 for _ in teksten]


def test_indexeren_en_idempotent_herindexeren(db, tmp_path: Path):
    (tmp_path / "wet").mkdir()
    bestand = tmp_path / "wet" / "artikelen.md"
    bestand.write_text(VOORBEELD)

    with SessionLocal() as sessie:
        sessie.query(Source).filter_by(slug="wet/artikelen").delete()
        sessie.commit()

        n = indexeer_bestand(sessie, bestand, tmp_path, embed=nep_embed)
        sessie.commit()
        assert n == 2

        # Idempotentie: nogmaals indexeren mag geen duplicaten opleveren
        indexeer_bestand(sessie, bestand, tmp_path, embed=nep_embed)
        sessie.commit()
        bron = sessie.query(Source).filter_by(slug="wet/artikelen").one()
        assert len(bron.chunks) == 2
        assert bron.chunks[0].ref == "Artikel 1, lid 1"

        sessie.delete(bron)
        sessie.commit()
