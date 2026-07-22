from fastapi.testclient import TestClient

from app.main import app
from app.rag import service
from app.rag.mistral import MistralFout
from app.rag.service import AskResultaat, Citaat

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_bezoek_telt_alleen_het_pad(monkeypatch):
    geteld = []
    monkeypatch.setattr("app.main.tel_op", lambda sleutel: geteld.append(sleutel))

    r = client.post("/bezoek", json={"pad": "/over"})

    assert r.status_code == 204
    assert geteld == ["bezoek:/over"]


def test_bezoek_weigert_onbekende_paden(monkeypatch):
    # Een open teller is een open deur: zonder witte lijst kan iedereen de
    # tabel volschrijven met verzonnen paden.
    geteld = []
    monkeypatch.setattr("app.main.tel_op", lambda sleutel: geteld.append(sleutel))

    assert client.post("/bezoek", json={"pad": "/verzonnen"}).status_code == 204
    assert geteld == []


def test_ask_geeft_antwoord_met_citaten(monkeypatch):
    resultaat = AskResultaat(
        antwoord="Zie [Artikel 6, lid 2].",
        citaten=[Citaat(ref="Artikel 6, lid 2", fragment="tekst", bron="Verordening",
                        url="https://example.org")],
        stand_van_wetgeving="juli 2026",
        opgehaalde_refs=["Artikel 6, lid 2"],
    )
    monkeypatch.setattr(service, "beantwoord", lambda sessie, vraag: resultaat)

    data = client.post("/ask", json={"vraag": "Wat is hoog risico?"}).json()

    assert data["antwoord"] == "Zie [Artikel 6, lid 2]."
    assert data["citaten"][0]["ref"] == "Artikel 6, lid 2"
    assert data["citaten"][0]["url"] == "https://example.org"
    # interne refs horen niet in de publieke respons
    assert "opgehaalde_refs" not in data


def test_mistralfout_wordt_502(monkeypatch):
    def kapot(sessie, vraag):
        raise MistralFout("api plat")
    monkeypatch.setattr(service, "beantwoord", kapot)

    r = client.post("/ask", json={"vraag": "x"})
    assert r.status_code == 502


def _stel_vraag(monkeypatch, antwoord: str, citaten=()):
    resultaat = AskResultaat(antwoord=antwoord, citaten=list(citaten),
                             stand_van_wetgeving="juli 2026", opgehaalde_refs=[])
    monkeypatch.setattr(service, "beantwoord", lambda sessie, vraag: resultaat)
    geteld = []
    monkeypatch.setattr("app.main.tel_op", lambda sleutel: geteld.append(sleutel))
    client.post("/ask", json={"vraag": "v"})
    return geteld


CITAAT = Citaat(ref="Artikel 6, lid 2", fragment="t", bron="b", url="https://example.org")


def test_geslaagd_antwoord_telt_alleen_de_vraag(monkeypatch):
    assert _stel_vraag(monkeypatch, "Hoog risico [Artikel 6, lid 2].", [CITAAT]) == ["vraag"]


def test_abstentie_wordt_apart_geteld(monkeypatch):
    from app.rag.prompt import ABSTENTIEZIN

    geteld = _stel_vraag(monkeypatch, ABSTENTIEZIN)
    assert geteld == ["vraag", "vraag:geen-bron"]


def test_antwoord_zonder_citaat_wordt_apart_geteld(monkeypatch):
    geteld = _stel_vraag(monkeypatch, "Een antwoord zonder enige bronverwijzing.")
    assert geteld == ["vraag", "vraag:zonder-citaat"]


def test_modelfout_telt_als_fout_en_niet_als_vraag(monkeypatch):
    def stuk(sessie, vraag):
        raise MistralFout("time-out")

    monkeypatch.setattr(service, "beantwoord", stuk)
    geteld = []
    monkeypatch.setattr("app.main.tel_op", lambda sleutel: geteld.append(sleutel))

    assert client.post("/ask", json={"vraag": "v"}).status_code == 502
    assert geteld == ["vraag:fout"]
