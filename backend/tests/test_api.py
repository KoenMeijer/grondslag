from fastapi.testclient import TestClient

from app.main import app
from app.rag import service
from app.rag.mistral import MistralFout
from app.rag.service import AskResultaat, Citaat

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_ask_telt_een_vraag(monkeypatch):
    resultaat = AskResultaat(antwoord="a", citaten=[], stand_van_wetgeving="juli 2026",
                             opgehaalde_refs=[])
    monkeypatch.setattr(service, "beantwoord", lambda sessie, vraag: resultaat)
    geteld = []
    monkeypatch.setattr("app.main.tel_op", lambda sleutel: geteld.append(sleutel))

    client.post("/ask", json={"vraag": "Wat is hoog risico?"})

    # Alleen dát er een vraag was, niet welke
    assert geteld == ["vraag"]


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
