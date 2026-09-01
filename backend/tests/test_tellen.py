"""Tests voor het lees-endpoint van de dagtellers (het beheer-cijferblok).
Zelfde aanpak als test_nieuws: token-check op het endpoint, en voor de
aggregatie testrijen op herkenbare datums (2099-*, botsen nooit met echte
tellingen en vallen altijd binnen het venster) die na afloop worden opgeruimd.
Het schrijven van tellingen zelf is al gedekt; hier gaat het om teruglezen.
"""
from fastapi.testclient import TestClient
from sqlalchemy import text

from app import tellen
from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.models import Dagtelling

client = TestClient(app)

# Datums ver in de toekomst: altijd binnen elk terugkijkvenster (datum >= vanaf),
# en herkenbaar voor het opruimen zonder echte tellingen te raken.
DAG_A = "2099-01-02"
DAG_B = "2099-01-01"


def _wis_testrijen(conn):
    conn.execute(text("DELETE FROM dagtellingen WHERE datum LIKE '2099-%'"))


def _zaai(sessie):
    sessie.add_all([
        Dagtelling(datum=DAG_A, sleutel="bezoek:/", aantal=3),
        Dagtelling(datum=DAG_A, sleutel="bezoek:/over", aantal=2),
        Dagtelling(datum=DAG_A, sleutel="vraag", aantal=4),
        Dagtelling(datum=DAG_A, sleutel="vraag:geen-bron", aantal=1),  # subteller telt niet mee als 'vraag'
        Dagtelling(datum=DAG_B, sleutel="bezoek:/nieuws", aantal=5),
        Dagtelling(datum=DAG_B, sleutel="vraag", aantal=1),
    ])
    sessie.commit()


def test_overzicht_aggregeert_per_dag(db):
    with db.connect() as conn, conn.begin():
        _wis_testrijen(conn)
    with SessionLocal() as sessie:
        _zaai(sessie)
        data = tellen.overzicht(sessie, dagen=365 * 100)  # venster ruim genoeg voor 2099
        per_datum = {r["datum"]: r for r in data["reeks"]}

        # Bezoeken = som over alle bezoek:*-paden; vragen = alleen de teller 'vraag'.
        assert per_datum[DAG_A]["bezoeken"] == 5   # 3 + 2
        assert per_datum[DAG_A]["vragen"] == 4     # de subteller vraag:geen-bron telt niet mee
        assert per_datum[DAG_B]["bezoeken"] == 5
        assert per_datum[DAG_B]["vragen"] == 1

        # Nieuwste dag eerst.
        datums = [r["datum"] for r in data["reeks"]]
        assert datums.index(DAG_A) < datums.index(DAG_B)

        # Totalen tellen minstens de gezaaide rijen (test-DB is verder leeg).
        assert data["totaal_bezoeken"] >= 10
        assert data["totaal_vragen"] >= 5

        _wis_testrijen(sessie.connection())
        sessie.commit()


def test_overzicht_venster_sluit_oude_dagen_uit(db):
    # Een datum ver in het verleden valt buiten een kort venster.
    with db.connect() as conn, conn.begin():
        _wis_testrijen(conn)
        conn.execute(text(
            "DELETE FROM dagtellingen WHERE datum = '2000-01-01'"))
    with SessionLocal() as sessie:
        sessie.add(Dagtelling(datum="2000-01-01", sleutel="bezoek:/", aantal=9))
        sessie.commit()
        data = tellen.overzicht(sessie, dagen=30)
        assert all(r["datum"] != "2000-01-01" for r in data["reeks"])
        sessie.execute(text("DELETE FROM dagtellingen WHERE datum = '2000-01-01'"))
        sessie.commit()


def test_cijfers_beheer_uit_zonder_token_in_config(db, monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "")
    assert client.get("/cijfers").status_code == 403


def test_cijfers_weigert_fout_token(db, monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "geheim")
    assert client.get("/cijfers").status_code == 401
    assert client.get("/cijfers", headers={"X-Admin-Token": "fout"}).status_code == 401


def test_cijfers_endpoint_geeft_aggregatie(db, monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "geheim")
    kop = {"X-Admin-Token": "geheim"}
    with db.connect() as conn, conn.begin():
        _wis_testrijen(conn)
    with SessionLocal() as sessie:
        _zaai(sessie)
    r = client.get("/cijfers?dagen=36500", headers=kop)
    assert r.status_code == 200
    body = r.json()
    per_datum = {d["datum"]: d for d in body["reeks"]}
    assert per_datum[DAG_A]["bezoeken"] == 5
    assert per_datum[DAG_A]["vragen"] == 4
    with SessionLocal() as sessie:
        _wis_testrijen(sessie.connection())
        sessie.commit()
