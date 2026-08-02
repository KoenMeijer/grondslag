"""Tests voor de half-automatische nieuwsaanvoer: feed-parsing (unit), de
verwerk-flow met dedupe (db-fixture) en de beheer-endpoints met token-check.
Zelfde aanpak als test_bronnen: nep-fetch via monkeypatch, testrijen herkenbaar
aan een TESTNIEUWS-marker en na afloop opgeruimd."""
from fastapi.testclient import TestClient
from sqlalchemy import text

from app import nieuws
from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.models import NieuwsItem

client = TestClient(app)

FEEDURL = "https://example.org/TESTNIEUWS/feed.xml"

FEED = """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"><channel><title>Testbron</title>
<item>
  <title>Commissie start handhaving AI Act</title>
  <link>https://example.org/TESTNIEUWS/ai-act</link>
  <description>De Commissie begint met handhaven.</description>
  <pubDate>Fri, 31 Jul 2026 10:00:00 +0200</pubDate>
</item>
<item>
  <title>Ransomware bij ziekenhuis</title>
  <link>https://example.org/TESTNIEUWS/ransomware</link>
  <description>Cyberaanval, verder niets digitaals-wettelijks.</description>
</item>
</channel></rss>"""

TESTFEEDS = [{"naam": "Testbron", "url": FEEDURL, "filter": r"\bAI\b"}]


def _wis_testrijen(conn):
    conn.execute(text("DELETE FROM nieuws_items WHERE url LIKE '%TESTNIEUWS%'"))


def _nep_fetch(url: str) -> str:
    return FEED if url == FEEDURL else "<html><p>Volledige artikeltekst.</p></html>"


def test_lees_feed_parseert_rss():
    items = nieuws.lees_feed(FEED)
    assert len(items) == 2
    assert items[0]["titel"] == "Commissie start handhaving AI Act"
    assert items[0]["url"] == "https://example.org/TESTNIEUWS/ai-act"
    assert items[0]["datum"] == "2026-07-31"   # RFC822-pubDate → ISO


def test_parse_datum_valt_terug_op_vandaag():
    # Geen of een onleesbare datum mag een item niet laten sneuvelen.
    assert len(nieuws._parse_datum(None)) == 10
    assert len(nieuws._parse_datum("gisteren ofzo")) == 10


def test_artikeltekst_strips_html_en_witruimte():
    assert nieuws.artikeltekst("<p>Artikel  1 </p>\n<p>tekst</p>") == "Artikel 1 tekst"


def test_verwerk_filtert_en_dedupliceert(db, monkeypatch):
    with db.connect() as conn, conn.begin():
        _wis_testrijen(conn)
    monkeypatch.setattr(nieuws, "_haal_op", _nep_fetch)
    monkeypatch.setattr(nieuws, "vat_samen", lambda titel, tekst: "Concept-samenvatting.")

    with SessionLocal() as sessie:
        # Eerste run: alleen het AI-item passeert het filter.
        assert nieuws.verwerk(sessie, feeds=TESTFEEDS) == 1
        rij = sessie.query(NieuwsItem).filter_by(
            url="https://example.org/TESTNIEUWS/ai-act").one()
        assert rij.status == "concept"
        assert rij.samenvatting == "Concept-samenvatting."
        # Tweede run: de URL is al bekend — niets nieuws (dedupe).
        assert nieuws.verwerk(sessie, feeds=TESTFEEDS) == 0
        # Ook een afgewezen item komt niet opnieuw binnen: de rij blijft
        # bestaan en de URL blijft de dedupe dragen.
        rij.status = "afgewezen"
        sessie.commit()
        assert nieuws.verwerk(sessie, feeds=TESTFEEDS) == 0
        _wis_testrijen(sessie.connection())
        sessie.commit()


def test_kapotte_feed_breekt_niets(db, monkeypatch):
    def kapot(url):
        raise RuntimeError("feed onbereikbaar")
    monkeypatch.setattr(nieuws, "_haal_op", kapot)
    with SessionLocal() as sessie:
        assert nieuws.verwerk(sessie, feeds=TESTFEEDS) == 0


def test_beheer_uit_zonder_token_in_config(db, monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "")
    assert client.get("/nieuws/concepten").status_code == 403


def test_beheer_weigert_fout_token(db, monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "geheim")
    assert client.get("/nieuws/concepten").status_code == 401
    assert client.get("/nieuws/concepten",
                      headers={"X-Admin-Token": "fout"}).status_code == 401


def test_redactieflow_publiceren_en_afwijzen(db, monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "geheim")
    kop = {"X-Admin-Token": "geheim"}
    with db.connect() as conn, conn.begin():
        _wis_testrijen(conn)
    with SessionLocal() as sessie:
        a = NieuwsItem(bron="Testbron", url="https://example.org/TESTNIEUWS/a",
                       titel="Item A", datum="2026-07-30", samenvatting="concept a")
        b = NieuwsItem(bron="Testbron", url="https://example.org/TESTNIEUWS/b",
                       titel="Item B", datum="2026-07-31", samenvatting="concept b")
        sessie.add_all([a, b])
        sessie.commit()
        a_id, b_id = a.id, b.id

    concept_ids = {n["id"] for n in client.get("/nieuws/concepten", headers=kop).json()}
    assert {a_id, b_id} <= concept_ids

    # Publiceren mét geredigeerde samenvatting in één slag.
    r = client.patch(f"/nieuws/{a_id}", headers=kop,
                     json={"samenvatting": "Geredigeerde tekst.", "status": "gepubliceerd"})
    assert r.status_code == 200
    # Afwijzen: verdwijnt uit de concepten, komt nooit op de site.
    assert client.patch(f"/nieuws/{b_id}", headers=kop,
                        json={"status": "afgewezen"}).status_code == 200

    publiek = {n["id"]: n for n in client.get("/nieuws").json()}
    assert publiek[a_id]["samenvatting"] == "Geredigeerde tekst."
    assert b_id not in publiek
    concept_ids = {n["id"] for n in client.get("/nieuws/concepten", headers=kop).json()}
    assert a_id not in concept_ids and b_id not in concept_ids

    with SessionLocal() as sessie:
        _wis_testrijen(sessie.connection())
        sessie.commit()


def test_onbekend_item_geeft_404(db, monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "geheim")
    r = client.patch("/nieuws/999999999", headers={"X-Admin-Token": "geheim"},
                     json={"status": "afgewezen"})
    assert r.status_code == 404
