"""Database-toegang. init_db() zet de pgvector-extensie vóór create_all,
omdat de Vector-kolom anders niet aangemaakt kan worden."""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    from app.models import Base

    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)
