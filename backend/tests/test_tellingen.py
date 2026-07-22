"""Tellingen: alleen aantallen per dag, nooit iets over personen.

Deze tests bewaken die belofte net zo hard als het gedrag: de tabel heeft geen
kolom voor IP, sessie of vraagtekst, en die mag er ook niet stiekem bij komen —
de transparantie-pagina zegt dat wij dat niet bijhouden.
"""
from sqlalchemy import text

from app.models import Dagtelling
from app.tellen import tel_op


def test_tabel_heeft_geen_persoonsgegevens():
    kolommen = set(Dagtelling.__table__.columns.keys())
    assert kolommen == {"id", "datum", "sleutel", "aantal"}


def test_eerste_telling_maakt_rij(db):
    with db.begin() as conn:
        conn.execute(text("DELETE FROM dagtellingen WHERE sleutel = 'test:eerste'"))
    tel_op("test:eerste", datum="2026-07-22")
    with db.connect() as conn:
        n = conn.execute(text(
            "SELECT aantal FROM dagtellingen WHERE datum='2026-07-22' AND sleutel='test:eerste'"
        )).scalar()
    assert n == 1


def test_tweede_telling_hoogt_op_zonder_dubbele_rij(db):
    with db.begin() as conn:
        conn.execute(text("DELETE FROM dagtellingen WHERE sleutel = 'test:tweede'"))
    for _ in range(3):
        tel_op("test:tweede", datum="2026-07-22")
    with db.connect() as conn:
        rijen = conn.execute(text(
            "SELECT aantal FROM dagtellingen WHERE datum='2026-07-22' AND sleutel='test:tweede'"
        )).fetchall()
    # Eén rij per (datum, sleutel): upsert, geen groeiende tabel per bezoek
    assert [r[0] for r in rijen] == [3]


def test_tellen_mag_de_aanroep_nooit_laten_falen(monkeypatch):
    # Een kapotte database mag geen bezoeker een foutmelding geven; tellen is
    # bijzaak, antwoorden is de hoofdzaak.
    from app import tellen

    def stuk(*a, **k):
        raise RuntimeError("db weg")

    monkeypatch.setattr(tellen, "_schrijf", stuk)
    tel_op("test:faalt")   # mag geen exception opleveren
