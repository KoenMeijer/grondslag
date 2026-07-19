from dataclasses import dataclass

from app.rag import service


@dataclass
class NepSource:
    titel: str
    url: str = "https://example.org"


@dataclass
class NepChunk:
    ref: str
    tekst: str
    source: NepSource


def test_beantwoord_bundelt_antwoord_citaten_en_refs(monkeypatch):
    chunks = [NepChunk(ref="Artikel 6, lid 2",
                       tekst="Artikel 6, lid 2 (Classificatie): tekst A",
                       source=NepSource(titel="Verordening (EU) 2024/1689")),
              NepChunk(ref="Overweging 61", tekst="Overweging 61: tekst B",
                       source=NepSource(titel="Verordening (EU) 2024/1689"))]
    monkeypatch.setattr(service.retrieval, "zoek_chunks", lambda s, v: chunks)
    monkeypatch.setattr(service.mistral, "genereer",
                        lambda systeem, vraag: "Zie [Artikel 6, lid 2].")

    r = service.beantwoord(None, "Wat is hoog risico?")

    assert r.antwoord == "Zie [Artikel 6, lid 2]."
    assert [c.ref for c in r.citaten] == ["Artikel 6, lid 2"]
    assert r.citaten[0].bron == "Verordening (EU) 2024/1689"
    assert r.citaten[0].url == "https://example.org"
    assert r.opgehaalde_refs == ["Artikel 6, lid 2", "Overweging 61"]
    assert r.stand_van_wetgeving == "juli 2026"
