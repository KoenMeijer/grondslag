"""Pure draft-logica — DB-vrij, geen engine-aanroep (zoals test_feed)."""
from app import contentdraft as cd


class _Cit:
    def __init__(self, ref, url):
        self.ref, self.url = ref, url


def test_slug():
    assert cd.slug("Valt mijn AI-systeem onder de AI-verordening?") == "valt-mijn-ai-systeem-onder-de-ai-verordening"
    assert cd.slug("  GPAI: wat nu?  ") == "gpai-wat-nu"


def test_render_concept_has_frontmatter_and_citations():
    md = cd.render_concept(
        vraag="Wat is een hoog-risico-systeem?",
        artikel="Artikel 6",
        stand="juli 2026",
        bijgewerkt="2026-08-03",
        sector="zorg",
        antwoord="Een hoog-risico-systeem is ...",
        citaten=[_Cit("artikel 6", "https://eur-lex.europa.eu/x")],
    )
    assert md.startswith("---\n")
    assert 'vraag: "Wat is een hoog-risico-systeem?"' in md
    assert "artikel: \"Artikel 6\"" in md
    assert "stand-wetgeving: \"juli 2026\"" in md
    assert "bijgewerkt: \"2026-08-03\"" in md
    assert "sector: zorg" in md
    assert "Een hoog-risico-systeem is ..." in md
    # Reviewer-notitie met de citaten (wordt vóór publicatie weggehaald/gecheckt).
    assert "artikel 6" in md and "https://eur-lex.europa.eu/x" in md


def test_render_concept_without_sector_omits_field():
    md = cd.render_concept(vraag="X?", artikel="Artikel 2", stand="juli 2026",
                           bijgewerkt="2026-08-03", sector=None,
                           antwoord="...", citaten=[])
    assert "sector:" not in md


def test_bestaat_al():
    assert cd.bestaat_al("x", {"x"}, set()) is True       # al gepubliceerd
    assert cd.bestaat_al("x", set(), {"x"}) is True         # al concept
    assert cd.bestaat_al("x", set(), set()) is False


def test_corpusgat_regel():
    assert cd.corpusgat_regel("Mag ik X?", "2026-08-03") == "- 2026-08-03 — Mag ik X?"
