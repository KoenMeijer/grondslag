import pytest

from app.ingest.parser import parse_document

FRONTMATTER = """---
bron: "Verordening (EU) 2024/1689"
url: https://example.org
versie: "geconsolideerd juli 2026"
datum-opgehaald: 2026-07-19
stand-wetgeving: juli 2026
type: wettekst
---
"""


def test_frontmatter_verplicht():
    with pytest.raises(ValueError):
        parse_document("## Artikel 1 — Onderwerp\ntekst")


def test_artikel_met_leden():
    doc = parse_document(FRONTMATTER + """
## Artikel 6 — Classificatieregels
### Lid 1
Eerste lid.
### Lid 2
Tweede lid.
""")
    assert [c.ref for c in doc.chunks] == ["Artikel 6, lid 1", "Artikel 6, lid 2"]
    # "Kop als context": de hiërarchie zit letterlijk in de chunktekst
    assert doc.chunks[0].tekst == "Artikel 6, lid 1 (Classificatieregels): Eerste lid."
    assert doc.meta["type"] == "wettekst"


def test_artikel_zonder_leden():
    doc = parse_document(FRONTMATTER + """
## Artikel 4 — AI-geletterdheid
Aanbieders nemen maatregelen.
""")
    assert doc.chunks[0].ref == "Artikel 4"
    assert doc.chunks[0].tekst == "Artikel 4 (AI-geletterdheid): Aanbieders nemen maatregelen."


def test_aanhef_voor_eerste_lid_wordt_eigen_chunk():
    doc = parse_document(FRONTMATTER + """
## Artikel 5 — Verboden praktijken
Aanhefregel.
### Lid 1
Eerste lid.
""")
    assert [c.ref for c in doc.chunks] == ["Artikel 5", "Artikel 5, lid 1"]


def test_bijlage_per_punt():
    doc = parse_document(FRONTMATTER + """
## Bijlage III — AI-systemen met een hoog risico
### Punt 4
Werkgelegenheid en personeelsbeheer.
""")
    assert doc.chunks[0].ref == "Bijlage III, punt 4"


def test_overweging_zonder_kop():
    doc = parse_document(FRONTMATTER + """
## Overweging 61
Tekst van de overweging.
""")
    assert doc.chunks[0].ref == "Overweging 61"
    assert doc.chunks[0].tekst == "Overweging 61: Tekst van de overweging."


def test_guidance_chunkt_per_sectie():
    guidance = FRONTMATTER.replace("type: wettekst", "type: guidance")
    doc = parse_document(guidance + """
## UAIV — beoogde toezichthouders
De AP coördineert.
""")
    assert doc.chunks[0].ref == "UAIV — beoogde toezichthouders"
    assert doc.chunks[0].tekst == "UAIV — beoogde toezichthouders: De AP coördineert."
