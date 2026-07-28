"""Tests voor de dagelijkse bronnencheck: vingerafdruk-logica (unit) en de
detectie-flow tegen de echte database (db-fixture, net als test_tellingen)."""
from sqlalchemy import text

from app import bronnen
from app.db import SessionLocal
from app.models import Broncheck

TESTURL = "https://example.org/TESTBRON"


def _wis_testrijen(conn):
    conn.execute(text("DELETE FROM bronchecks WHERE url LIKE '%TESTBRON%'"))


def test_vingerafdruk_negeert_opmaak_en_witruimte():
    a = bronnen.vingerafdruk("<html><body><p>Artikel  1 </p>\n<p>tekst</p></body></html>")
    b = bronnen.vingerafdruk("<html><div>Artikel 1\n\n   tekst</div></html>")
    assert a == b


def test_vingerafdruk_verandert_bij_andere_inhoud():
    a = bronnen.vingerafdruk("<p>deadline 2 augustus 2026</p>")
    b = bronnen.vingerafdruk("<p>deadline 2 december 2027</p>")
    assert a != b


def test_eerste_check_legt_nulmeting_vast_zonder_alarm(db, monkeypatch):
    with db.connect() as conn, conn.begin():
        _wis_testrijen(conn)
    monkeypatch.setattr(bronnen, "_haal_op", lambda url: "<p>versie een</p>")

    with SessionLocal() as sessie:
        bronnen.controleer(sessie, urls=[TESTURL])
        sessie.commit()
        rij = sessie.query(Broncheck).filter_by(url=TESTURL).one()
        assert rij.gewijzigd_sinds is None
        _wis_testrijen(sessie.connection())
        sessie.commit()


def test_gewijzigde_bron_wordt_gemarkeerd_en_blijft_gemarkeerd(db, monkeypatch):
    with db.connect() as conn, conn.begin():
        _wis_testrijen(conn)

    with SessionLocal() as sessie:
        monkeypatch.setattr(bronnen, "_haal_op", lambda url: "<p>versie een</p>")
        bronnen.controleer(sessie, urls=[TESTURL])
        # Bron wijzigt: alarmvlag gaat aan…
        monkeypatch.setattr(bronnen, "_haal_op", lambda url: "<p>versie twee</p>")
        bronnen.controleer(sessie, urls=[TESTURL])
        rij = sessie.query(Broncheck).filter_by(url=TESTURL).one()
        assert rij.gewijzigd_sinds is not None
        eerste_melding = rij.gewijzigd_sinds
        # …en blijft aan bij volgende checks (geen stil zelfherstel: de vlag
        # verdwijnt pas als het corpus is bijgewerkt en reset() draait).
        bronnen.controleer(sessie, urls=[TESTURL])
        rij = sessie.query(Broncheck).filter_by(url=TESTURL).one()
        assert rij.gewijzigd_sinds == eerste_melding
        _wis_testrijen(sessie.connection())
        sessie.commit()


def test_fetchfout_verandert_de_stand_niet(db, monkeypatch):
    with db.connect() as conn, conn.begin():
        _wis_testrijen(conn)

    with SessionLocal() as sessie:
        monkeypatch.setattr(bronnen, "_haal_op", lambda url: "<p>versie een</p>")
        bronnen.controleer(sessie, urls=[TESTURL])

        def kapot(url):
            raise RuntimeError("tijdelijk onbereikbaar")
        monkeypatch.setattr(bronnen, "_haal_op", kapot)
        bronnen.controleer(sessie, urls=[TESTURL])
        rij = sessie.query(Broncheck).filter_by(url=TESTURL).one()
        assert rij.gewijzigd_sinds is None  # onbereikbaar is geen wijziging
        _wis_testrijen(sessie.connection())
        sessie.commit()


def test_reset_wist_de_nulmeting(db, monkeypatch):
    # Na een corpus-herindexering begint de meting opnieuw: de eerstvolgende
    # dagcheck legt verse vingerafdrukken vast tegen de nieuwe corpusstand.
    with db.connect() as conn, conn.begin():
        _wis_testrijen(conn)

    with SessionLocal() as sessie:
        monkeypatch.setattr(bronnen, "_haal_op", lambda url: "<p>versie een</p>")
        bronnen.controleer(sessie, urls=[TESTURL])
        bronnen.reset(sessie)
        assert sessie.query(Broncheck).filter_by(url=TESTURL).count() == 0
        sessie.commit()
