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
    # De frontend beslist op dit veld of de inzendknop verschijnt — de
    # abstentiedetectie hoort bij de backend, niet gedupliceerd in de client.
    assert data["geen_bron"] is False
    # interne refs horen niet in de publieke respons
    assert "opgehaalde_refs" not in data


def test_mistralfout_wordt_502(monkeypatch):
    def kapot(sessie, vraag):
        raise MistralFout("api plat")
    monkeypatch.setattr(service, "beantwoord", kapot)

    r = client.post("/ask", json={"vraag": "Is cv-screening hoog risico?"})
    assert r.status_code == 502


def _stel_vraag(monkeypatch, antwoord: str, citaten=(), beste_afstand=None,
                geen_bron=False):
    resultaat = AskResultaat(antwoord=antwoord, citaten=list(citaten),
                             stand_van_wetgeving="juli 2026", opgehaalde_refs=[],
                             beste_afstand=beste_afstand, geen_bron=geen_bron)
    monkeypatch.setattr(service, "beantwoord", lambda sessie, vraag: resultaat)
    geteld = []
    monkeypatch.setattr("app.main.tel_op", lambda sleutel: geteld.append(sleutel))
    client.post("/ask", json={"vraag": "Is cv-screening hoog risico?"})
    return geteld


CITAAT = Citaat(ref="Artikel 6, lid 2", fragment="t", bron="b", url="https://example.org")


def test_geslaagd_antwoord_telt_alleen_de_vraag(monkeypatch):
    assert _stel_vraag(monkeypatch, "Hoog risico [Artikel 6, lid 2].", [CITAAT]) == ["vraag"]


def test_abstentie_wordt_apart_geteld(monkeypatch):
    from app.rag.prompt import ABSTENTIEZIN

    geteld = _stel_vraag(monkeypatch, ABSTENTIEZIN, geen_bron=True)
    assert geteld == ["vraag", "vraag:geen-bron"]


def test_abstentie_met_sterk_signaal_telt_de_subsleutel(monkeypatch):
    # Relevante chunks gevonden (kleine afstand) en tóch een weigering:
    # dat duidt op een retrieval-/promptprobleem, niet op een vraag buiten scope.
    from app.rag.prompt import ABSTENTIEZIN

    monkeypatch.setattr("app.main.settings.signaal_grens", 0.5)
    geteld = _stel_vraag(monkeypatch, ABSTENTIEZIN, beste_afstand=0.10, geen_bron=True)
    assert geteld == ["vraag", "vraag:geen-bron", "vraag:geen-bron:sterk-signaal"]


def test_abstentie_met_laag_signaal_telt_alleen_geen_bron(monkeypatch):
    from app.rag.prompt import ABSTENTIEZIN

    monkeypatch.setattr("app.main.settings.signaal_grens", 0.5)
    geteld = _stel_vraag(monkeypatch, ABSTENTIEZIN, beste_afstand=0.95, geen_bron=True)
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

    assert client.post("/ask", json={"vraag": "Is cv-screening hoog risico?"}).status_code == 502
    assert geteld == ["vraag:fout"]


def test_inzending_bewaart_en_telt(monkeypatch):
    bewaard = []
    monkeypatch.setattr("app.main.inzendingen.bewaar",
                        lambda vraag: bewaard.append(vraag) or True)
    geteld = []
    monkeypatch.setattr("app.main.tel_op", lambda sleutel: geteld.append(sleutel))

    r = client.post("/inzending", json={"vraag": "Valt onze chatbot onder artikel 50?"})

    assert r.status_code == 204
    assert bewaard == ["Valt onze chatbot onder artikel 50?"]
    assert geteld == ["inzending"]


def test_inzending_boven_dagcap_geeft_429(monkeypatch):
    monkeypatch.setattr("app.main.inzendingen.bewaar", lambda vraag: False)
    geteld = []
    monkeypatch.setattr("app.main.tel_op", lambda sleutel: geteld.append(sleutel))

    assert client.post("/inzending", json={"vraag": "nog een vraag"}).status_code == 429
    assert geteld == []


def test_te_korte_inzending_wordt_geweigerd():
    assert client.post("/inzending", json={"vraag": "ab"}).status_code == 422


def test_bronnenstatus_ok_geeft_200(monkeypatch):
    monkeypatch.setattr("app.main.bronnen.status", lambda sessie: {
        "status": "ok", "gewijzigd": [], "laatst_gecontroleerd": "2026-07-25"})
    r = client.get("/bronnen/status")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_bronnenstatus_gewijzigde_bron_geeft_409(monkeypatch):
    # Niet-200 is bewust: de bestaande AI-OS-watchdog (os/sites.conf) ziet
    # alles behalve 200 als alarm — geen extra integratie nodig.
    monkeypatch.setattr("app.main.bronnen.status", lambda sessie: {
        "status": "bronnen-gewijzigd",
        "gewijzigd": ["https://eur-lex.europa.eu/..."],
        "laatst_gecontroleerd": "2026-07-25"})
    r = client.get("/bronnen/status")
    assert r.status_code == 409
    assert "eur-lex" in r.json()["gewijzigd"][0]


def test_te_lange_vraag_wordt_geweigerd():
    # Zonder bovengrens betaalt elke lange vraag zich uit in embedding- en
    # generatietokens; 422 is goedkoper dan een rekening.
    r = client.post("/ask", json={"vraag": "a" * 1001})
    assert r.status_code == 422


def test_lege_vraag_wordt_geweigerd():
    assert client.post("/ask", json={"vraag": "  "}).status_code == 422
