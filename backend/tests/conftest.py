"""Gedeelde fixtures. De db-fixture slaat tests over i.p.v. te falen als de
database niet draait: parser- en scoringtests moeten ook zonder Docker kunnen."""
import pytest
from sqlalchemy import text


@pytest.fixture(autouse=True)
def geen_echte_tellingen(monkeypatch):
    """Tests mogen de gebruiksstatistiek niet vervuilen. Tests die het tellen
    zélf controleren, zetten hier hun eigen spy overheen."""
    monkeypatch.setattr("app.main.tel_op", lambda *a, **k: None, raising=False)


@pytest.fixture(scope="session")
def db():
    from app.db import engine, init_db

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        pytest.skip("database niet bereikbaar — start eerst: docker compose up -d")
    init_db()
    return engine
