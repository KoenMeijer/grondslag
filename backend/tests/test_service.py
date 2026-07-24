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
    monkeypatch.setattr(
        service.retrieval, "zoek_chunks",
        lambda s, v: service.retrieval.ZoekResultaat(chunks=chunks, beste_afstand=0.12))
    monkeypatch.setattr(service.mistral, "genereer",
                        lambda systeem, vraag: "Zie [Artikel 6, lid 2].")

    r = service.beantwoord(None, "Wat is hoog risico?")

    assert r.antwoord == "Zie [Artikel 6, lid 2]."
    assert [c.ref for c in r.citaten] == ["Artikel 6, lid 2"]
    assert r.citaten[0].bron == "Verordening (EU) 2024/1689"
    assert r.citaten[0].url == "https://example.org"
    assert r.opgehaalde_refs == ["Artikel 6, lid 2", "Overweging 61"]
    assert r.beste_afstand == 0.12
    assert r.geen_bron is False
    assert r.stand_van_wetgeving == "juli 2026"


def test_beantwoord_herkent_abstentie(monkeypatch):
    # De abstentiedetectie hoort in de service: één bron van waarheid voor
    # teller én API-veld, geen gedupliceerde stringcheck in de frontend.
    from app.rag.prompt import ABSTENTIEZIN

    monkeypatch.setattr(
        service.retrieval, "zoek_chunks",
        lambda s, v: service.retrieval.ZoekResultaat(chunks=[], beste_afstand=0.3))
    monkeypatch.setattr(service.mistral, "genereer",
                        lambda systeem, vraag: ABSTENTIEZIN)

    assert service.beantwoord(None, "Wat is de cookieregelgeving?").geen_bron is True


def test_mengvorm_met_citaat_telt_als_beantwoord(monkeypatch):
    # Gemeten mengvorm (24 jul): weigerzin gevolgd door een gegrond antwoord
    # mét citaat. Dat ís een antwoord — de weigerzin alléén mag niet als
    # geen-bron tellen zodra er een citaat staat, anders toont de frontend
    # onterecht de inzendknop en telt de statistiek een vals gat.
    from app.rag.prompt import ABSTENTIEZIN

    chunks = [NepChunk(ref="Bijlage III, punt 4",
                       tekst="Bijlage III, punt 4: werving en selectie",
                       source=NepSource(titel="Verordening (EU) 2024/1689"))]
    monkeypatch.setattr(
        service.retrieval, "zoek_chunks",
        lambda s, v: service.retrieval.ZoekResultaat(chunks=chunks, beste_afstand=0.1))
    monkeypatch.setattr(
        service.mistral, "genereer",
        lambda systeem, vraag: ABSTENTIEZIN + " Wel valt dit onder hoog risico [Bijlage III, punt 4].")

    r = service.beantwoord(None, "Mag cv-screening met AI?")
    assert r.citaten and r.geen_bron is False
