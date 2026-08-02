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


class Broncheck(Base):
    """Nulmeting per bron-URL voor de dagelijkse bronnencheck. De vingerafdruk
    is een hash van de zichtbare tekst van de pagina; wijkt de dagelijkse
    ophaling af, dan wordt gewijzigd_sinds gezet en blijft staan tot het corpus
    is bijgewerkt (herindexering reset deze tabel — zie app/bronnen.py)."""

    __tablename__ = "bronchecks"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(unique=True)
    vingerafdruk: Mapped[str]
    laatst_gecontroleerd: Mapped[str]           # ISO-datum (UTC)
    gewijzigd_sinds: Mapped[str | None] = mapped_column(default=None)


class NieuwsItem(Base):
    """Half-automatische nieuwsaanvoer voor de pagina "Laatste ontwikkelingen":
    het dagelijkse proces (app/nieuws.py) zet concepten klaar, de redacteur
    publiceert of wijst af via het beheerscherm. De URL is uniek en blijft ook
    na afwijzen bewaard — dat ís de dedupe: een afgewezen bericht duikt de
    volgende dag niet opnieuw op als concept."""

    __tablename__ = "nieuws_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    bron: Mapped[str]       # naam van de nieuwsbron (zie app/nieuws.py FEEDS)
    url: Mapped[str] = mapped_column(unique=True)
    titel: Mapped[str]
    datum: Mapped[str]      # publicatiedatum bij de bron (ISO)
    # Concept van het model; de redacteur herschrijft vóór publicatie.
    samenvatting: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(default="concept")   # concept | gepubliceerd | afgewezen
    gepubliceerd_op: Mapped[str | None] = mapped_column(default=None)


class IngezondenVraag(Base):
    """Opt-in ingezonden vragen na een onbeantwoorde vraag. Alleen de
    vraagtekst en de datum — bewust geen IP, sessie of user-agent, zelfde
    principe als Dagtelling: een tabel zonder die kolommen kan de
    transparantiebelofte niet per ongeluk breken. Retentie wordt bij elke
    nieuwe inzending afgedwongen (zie app/inzendingen.py)."""

    __tablename__ = "ingezonden_vragen"

    id: Mapped[int] = mapped_column(primary_key=True)
    datum: Mapped[str]      # ISO-datum (UTC)
    vraag: Mapped[str] = mapped_column(Text)
