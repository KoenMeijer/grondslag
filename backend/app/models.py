"""Datamodel: bronnen en chunks. `ref` is het citatie-anker ("Artikel 6, lid 2")
dat het citaat-paneel en de eval-suite voeden — zie de spec."""
from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.config import settings


class Base(DeclarativeBase):
    pass


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(unique=True)   # relatief corpuspad zonder .md
    titel: Mapped[str]
    url: Mapped[str]
    versie: Mapped[str]
    datum: Mapped[str]      # datum-opgehaald uit frontmatter (ISO-string volstaat)
    type: Mapped[str]       # "wettekst" | "guidance"
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    # ondelete: ook op DB-niveau cascaden, zodat opruimen nooit op de FK strandt
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"))
    ref: Mapped[str]        # citatie-anker, bv. "Artikel 6, lid 2"
    kop: Mapped[str]
    tekst: Mapped[str] = mapped_column(Text)   # inclusief hiërarchie-prefix
    volgorde: Mapped[int]
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embed_dim))
    source: Mapped[Source] = relationship(back_populates="chunks")


class Dagtelling(Base):
    """Gebruikstellingen per dag. Bewust géén IP, sessie, user-agent of
    vraagtekst: de transparantie-pagina belooft dat wij dat niet bijhouden, en
    een tabel zonder die kolommen kan die belofte niet per ongeluk breken.
    Eén rij per (datum, sleutel), opgehoogd via upsert — de tabel groeit dus met
    het aantal dagen, niet met het aantal bezoeken."""

    __tablename__ = "dagtellingen"
    __table_args__ = (UniqueConstraint("datum", "sleutel", name="uq_dagtelling"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    datum: Mapped[str]      # ISO-datum (UTC); string volstaat en leest in psql prettig
    sleutel: Mapped[str]    # "bezoek:/", "bezoek:/over", "vraag"
    aantal: Mapped[int]
