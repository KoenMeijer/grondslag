"""Gedeelde fixtures. De db-fixture slaat tests over i.p.v. te falen als de
database niet draait: parser- en scoringtests moeten ook zonder Docker kunnen."""
import pytest
from sqlalchemy import text


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
