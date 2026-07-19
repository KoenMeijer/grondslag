"""Retrieval: vraag embedden en de dichtstbijzijnde chunks ophalen (cosine).
TOP_K staat in config; verhogen is een gemeten knop (les: meer context ≠ beter)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Chunk
from app.rag import mistral


def zoek_chunks(sessie: Session, vraag: str, top_k: int | None = None) -> list[Chunk]:
    vraagvector = mistral.embed([vraag])[0]
    stmt = (
        select(Chunk)
        .order_by(Chunk.embedding.cosine_distance(vraagvector))
        .limit(top_k or settings.top_k)
    )
    return list(sessie.scalars(stmt))
