"""Integratietests voor de opt-in-inzendingen: opslag, retentie en dagcap.
Draaien tegen de echte database (db-fixture), net als test_tellingen."""
import datetime

from sqlalchemy import text

from app import inzendingen
from app.db import SessionLocal
from app.models import IngezondenVraag


def _wis_testrijen(conn):
    conn.execute(text("DELETE FROM ingezonden_vragen WHERE vraag LIKE 'TESTINZ%'"))


def test_bewaar_slaat_vraag_op_met_datum(db):
    with db.connect() as conn, conn.begin():
        _wis_testrijen(conn)

    assert inzendingen.bewaar("TESTINZ valt onze chatbot onder artikel 50?") is True

    with SessionLocal() as sessie:
        rij = (sessie.query(IngezondenVraag)
               .filter(IngezondenVraag.vraag.like("TESTINZ%")).one())
        assert rij.datum == datetime.datetime.now(datetime.UTC).date().isoformat()
        sessie.delete(rij)
        sessie.commit()


def test_bewaar_ruimt_rijen_ouder_dan_de_retentie_op(db):
    # De bewaarbelofte op /transparantie is in code afgedwongen: elke nieuwe
    # inzending ruimt eerst alles op dat over de retentietermijn heen is.
    with db.connect() as conn, conn.begin():
        _wis_testrijen(conn)
    oud = (datetime.datetime.now(datetime.UTC).date()
           - datetime.timedelta(days=inzendingen.RETENTIE_DAGEN + 1)).isoformat()
    with SessionLocal() as sessie:
        sessie.add(IngezondenVraag(datum=oud, vraag="TESTINZ verouderde vraag"))
        sessie.commit()

    assert inzendingen.bewaar("TESTINZ nieuwe vraag") is True

    with SessionLocal() as sessie:
        rijen = [r.vraag for r in sessie.query(IngezondenVraag)
                 .filter(IngezondenVraag.vraag.like("TESTINZ%"))]
        assert rijen == ["TESTINZ nieuwe vraag"]
        _wis_testrijen(sessie.connection())
        sessie.commit()


def test_bewaar_weigert_boven_de_dagcap(db, monkeypatch):
    with db.connect() as conn, conn.begin():
        _wis_testrijen(conn)
    # Cap relatief aan wat er vandaag al staat (lokale db kan rijen bevatten):
    # de eerste testinzending vult de cap precies, de tweede moet weigeren.
    vandaag = datetime.datetime.now(datetime.UTC).date().isoformat()
    with SessionLocal() as sessie:
        bestaand = sessie.query(IngezondenVraag).filter_by(datum=vandaag).count()
    monkeypatch.setattr(inzendingen, "DAGCAP", bestaand + 1)

    assert inzendingen.bewaar("TESTINZ eerste") is True
    assert inzendingen.bewaar("TESTINZ tweede") is False

    with SessionLocal() as sessie:
        rijen = [r.vraag for r in sessie.query(IngezondenVraag)
                 .filter(IngezondenVraag.vraag.like("TESTINZ%"))]
        assert rijen == ["TESTINZ eerste"]
        _wis_testrijen(sessie.connection())
        sessie.commit()
