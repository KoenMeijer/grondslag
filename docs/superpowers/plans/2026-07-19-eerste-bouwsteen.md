# Eerste bouwsteen — Implementatieplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** NL-corpus (verordening 2024/1689 + NL-guidance) indexeren in pgvector, vragen beantwoorden met citaten via Mistral en FastAPI, en een deterministische eval-suite met ~10 golden-set-cases.

**Architecture:** Corpus als gestructureerde markdown in `corpus/` (git-diffbaar corpusbeheer). Ingest parseert op wetsstructuur (lid/bijlagepunt/overweging), embedt via `mistral-embed`, slaat op in Postgres+pgvector. RAG-service: vraag embedden → top-K cosine → generatie op temperatuur 0 met ref-gelabelde context → citaten zijn de opgehaalde chunks waarnaar het antwoord verwijst. Eval-runner draait in-process door dezelfde service.

**Tech Stack:** Python 3.12 · FastAPI · SQLAlchemy 2 · Postgres 16 + pgvector · Mistral API (`mistral-embed`, `mistral-small-latest`) · pytest · Docker Compose.

Spec: `docs/superpowers/specs/2026-07-19-eerste-bouwsteen-design.md`.

## Global Constraints

- **Taal:** alle copy, prompts, code-comments en commitberichten in het Nederlands; comments leggen het *waarom* uit.
- **Modellen:** embeddings `mistral-embed` (1024 dims), generatie `mistral-small-latest`, **temperatuur 0** — nooit anders.
- **TOP_K = 5** als startwaarde (configureerbaar, niet hardcoden buiten config).
- **Database:** Postgres op poort **5433** (5432 vrijlaten voor andere lokale projecten), user/db/wachtwoord `aiact`.
- **Commando's draaien vanuit de repo-root**; Python-modules via `PYTHONPATH=backend`; `pytest` werkt kaal vanuit de root (zie `pytest.ini`).
- **Scope:** exact wat hier staat — geen frontend, geen hybride zoeken, geen extra endpoints.
- **Commits:** eindigen op `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- **Secrets:** `MISTRAL_API_KEY` alleen via `.env` (in `.gitignore`); nooit committen.

---

### Task 1: Projectscaffold — dependencies, database, config

**Files:**
- Create: `.gitignore`, `.env.example`, `requirements.txt`, `docker-compose.yml`, `pytest.ini`, `backend/app/__init__.py`, `backend/app/config.py`

**Interfaces:**
- Produces: `app.config.settings` (velden: `mistral_api_key: str`, `database_url: str`, `embed_model: str`, `chat_model: str`, `embed_dim: int`, `top_k: int`, `stand_van_wetgeving: str`). Alle latere taken importeren dit.

- [ ] **Step 1: Schrijf `.gitignore`**

```gitignore
.venv/
__pycache__/
*.pyc
.env
.pytest_cache/
```

- [ ] **Step 2: Schrijf `requirements.txt`**

```
fastapi
uvicorn[standard]
sqlalchemy>=2.0
psycopg[binary]
pgvector
pydantic-settings
mistralai>=1.0
pyyaml
httpx
beautifulsoup4
pytest
```

- [ ] **Step 3: Schrijf `docker-compose.yml`**

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: aiact
      POSTGRES_PASSWORD: aiact
      POSTGRES_DB: aiact
    ports:
      - "5433:5432"   # 5433: laat 5432 vrij voor andere lokale projecten
    volumes:
      - dbdata:/var/lib/postgresql/data

volumes:
  dbdata:
```

- [ ] **Step 4: Schrijf `pytest.ini`** (in de repo-root, zodat `pytest` kaal werkt en zowel `app` als `evals` importeerbaar zijn)

```ini
[pytest]
testpaths = backend/tests evals
pythonpath = backend .
```

- [ ] **Step 5: Schrijf `.env.example`**

```
MISTRAL_API_KEY=
# Standaardwaarde volstaat lokaal; alleen zetten als je afwijkt:
# DATABASE_URL=postgresql+psycopg://aiact:aiact@localhost:5433/aiact
```

- [ ] **Step 6: Schrijf `backend/app/__init__.py`** (leeg bestand) **en `backend/app/config.py`**

```python
"""Centrale configuratie. Alle knoppen (model, TOP_K) staan hier zodat een
experiment één plek heeft om te draaien — zie docs/eval-aanpak.md."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mistral_api_key: str = ""
    database_url: str = "postgresql+psycopg://aiact:aiact@localhost:5433/aiact"
    embed_model: str = "mistral-embed"
    chat_model: str = "mistral-small-latest"
    embed_dim: int = 1024          # dimensie van mistral-embed
    top_k: int = 5                 # startwaarde; verhogen is een gemeten knop, geen reflex
    stand_van_wetgeving: str = "juli 2026"

    model_config = {"env_file": ".env"}


settings = Settings()
```

- [ ] **Step 7: Installeer en start de database**

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
docker compose up -d
cp .env.example .env   # vul MISTRAL_API_KEY handmatig in (niet committen)
```

Verwacht: pip installeert zonder fouten; `docker compose ps` toont de db als `running`.

- [ ] **Step 8: Verifieer dat de config laadt**

```bash
PYTHONPATH=backend .venv/bin/python -c "from app.config import settings; print(settings.database_url)"
```

Verwacht: `postgresql+psycopg://aiact:aiact@localhost:5433/aiact`

- [ ] **Step 9: Commit**

```bash
git add .gitignore .env.example requirements.txt docker-compose.yml pytest.ini backend/
git commit -m "Scaffold: dependencies, pgvector-database, config"
```

---

### Task 2: Datamodel — sources en chunks met pgvector

**Files:**
- Create: `backend/app/models.py`, `backend/app/db.py`, `backend/tests/__init__.py`, `backend/tests/conftest.py`
- Test: `backend/tests/test_models.py`

**Interfaces:**
- Consumes: `app.config.settings`
- Produces: `app.models.Source` (velden `id, slug, titel, url, versie, datum, type, chunks`), `app.models.Chunk` (velden `id, source_id, ref, kop, tekst, volgorde, embedding, source`), `app.db.engine`, `app.db.SessionLocal`, `app.db.init_db()`. Testfixture `db` (slaat over als de database niet draait).

- [ ] **Step 1: Schrijf `backend/app/models.py`**

```python
"""Datamodel: bronnen en chunks. `ref` is het citatie-anker ("Artikel 6, lid 2")
dat het citaat-paneel en de eval-suite voeden — zie de spec."""
from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Text
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
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    ref: Mapped[str]        # citatie-anker, bv. "Artikel 6, lid 2"
    kop: Mapped[str]
    tekst: Mapped[str] = mapped_column(Text)   # inclusief hiërarchie-prefix
    volgorde: Mapped[int]
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embed_dim))
    source: Mapped[Source] = relationship(back_populates="chunks")
```

- [ ] **Step 2: Schrijf `backend/app/db.py`**

```python
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
```

- [ ] **Step 3: Schrijf `backend/tests/__init__.py`** (leeg) **en `backend/tests/conftest.py`**

```python
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
```

- [ ] **Step 4: Schrijf de falende test `backend/tests/test_models.py`**

```python
from app.db import SessionLocal
from app.models import Chunk, Source


def test_bron_met_chunk_rondreis(db):
    # Waarom: bewijst dat schema, vector-kolom en cascade werken vóór we ingest bouwen
    with SessionLocal() as sessie:
        sessie.query(Source).filter_by(slug="test/rondreis").delete()
        bron = Source(slug="test/rondreis", titel="Testbron", url="http://x",
                      versie="1", datum="2026-07-19", type="wettekst")
        bron.chunks.append(Chunk(ref="Artikel 1", kop="Onderwerp",
                                 tekst="Artikel 1 (Onderwerp): tekst",
                                 volgorde=0, embedding=[0.1] * 1024))
        sessie.add(bron)
        sessie.commit()

        terug = sessie.query(Source).filter_by(slug="test/rondreis").one()
        assert terug.chunks[0].ref == "Artikel 1"
        assert len(terug.chunks[0].embedding) == 1024

        sessie.delete(terug)   # cascade moet ook de chunk verwijderen
        sessie.commit()
        assert sessie.query(Chunk).filter_by(ref="Artikel 1").count() == 0
```

- [ ] **Step 5: Draai de test — eerst falend, dan groen**

```bash
.venv/bin/pytest backend/tests/test_models.py -v
```

Verwacht bij ontbrekende code: ImportError. Na Steps 1–3: PASS (of SKIP als de db niet draait — dan `docker compose up -d`).

- [ ] **Step 6: Commit**

```bash
git add backend/app/models.py backend/app/db.py backend/tests/
git commit -m "Datamodel: sources en chunks met pgvector"
```

---

### Task 3: Corpus-parser — markdown → chunks op wetsstructuur

**Files:**
- Create: `backend/app/ingest/__init__.py`, `backend/app/ingest/parser.py`
- Test: `backend/tests/test_parser.py`

**Interfaces:**
- Produces: `app.ingest.parser.parse_document(md: str) -> ParsedDocument` met `ParsedDocument(meta: dict, chunks: list[ParsedChunk])` en `ParsedChunk(ref: str, kop: str, tekst: str)`. Ref-formaten: `"Artikel 6, lid 2"`, `"Artikel 4"`, `"Bijlage III, punt 4"`, `"Overweging 61"`, guidance: de `##`-kop.

- [ ] **Step 1: Schrijf de falende tests `backend/tests/test_parser.py`**

```python
import pytest

from app.ingest.parser import parse_document

FRONTMATTER = """---
bron: "Verordening (EU) 2024/1689"
url: https://example.org
versie: "geconsolideerd juli 2026"
datum-opgehaald: 2026-07-19
stand-wetgeving: juli 2026
type: wettekst
---
"""


def test_frontmatter_verplicht():
    with pytest.raises(ValueError):
        parse_document("## Artikel 1 — Onderwerp\ntekst")


def test_artikel_met_leden():
    doc = parse_document(FRONTMATTER + """
## Artikel 6 — Classificatieregels
### Lid 1
Eerste lid.
### Lid 2
Tweede lid.
""")
    assert [c.ref for c in doc.chunks] == ["Artikel 6, lid 1", "Artikel 6, lid 2"]
    # "Kop als context": de hiërarchie zit letterlijk in de chunktekst
    assert doc.chunks[0].tekst == "Artikel 6, lid 1 (Classificatieregels): Eerste lid."
    assert doc.meta["type"] == "wettekst"


def test_artikel_zonder_leden():
    doc = parse_document(FRONTMATTER + """
## Artikel 4 — AI-geletterdheid
Aanbieders nemen maatregelen.
""")
    assert doc.chunks[0].ref == "Artikel 4"
    assert doc.chunks[0].tekst == "Artikel 4 (AI-geletterdheid): Aanbieders nemen maatregelen."


def test_aanhef_voor_eerste_lid_wordt_eigen_chunk():
    doc = parse_document(FRONTMATTER + """
## Artikel 5 — Verboden praktijken
Aanhefregel.
### Lid 1
Eerste lid.
""")
    assert [c.ref for c in doc.chunks] == ["Artikel 5", "Artikel 5, lid 1"]


def test_bijlage_per_punt():
    doc = parse_document(FRONTMATTER + """
## Bijlage III — AI-systemen met een hoog risico
### Punt 4
Werkgelegenheid en personeelsbeheer.
""")
    assert doc.chunks[0].ref == "Bijlage III, punt 4"


def test_overweging_zonder_kop():
    doc = parse_document(FRONTMATTER + """
## Overweging 61
Tekst van de overweging.
""")
    assert doc.chunks[0].ref == "Overweging 61"
    assert doc.chunks[0].tekst == "Overweging 61: Tekst van de overweging."


def test_guidance_chunkt_per_sectie():
    guidance = FRONTMATTER.replace("type: wettekst", "type: guidance")
    doc = parse_document(guidance + """
## UAIV — beoogde toezichthouders
De AP coördineert.
""")
    assert doc.chunks[0].ref == "UAIV — beoogde toezichthouders"
    assert doc.chunks[0].tekst == "UAIV — beoogde toezichthouders: De AP coördineert."
```

- [ ] **Step 2: Draai de tests, verwacht ImportError**

```bash
.venv/bin/pytest backend/tests/test_parser.py -v
```

- [ ] **Step 3: Schrijf `backend/app/ingest/__init__.py`** (leeg) **en `backend/app/ingest/parser.py`**

```python
"""Parser voor corpus-markdown: frontmatter + kopstructuur → chunks.

Chunkgrenzen volgen de wetsstructuur (docs/rag-aanpak.md): één chunk per lid,
bijlagepunt of overweging; guidance chunkt per ##-sectie. De hiërarchie gaat
als prefix mee in de chunktekst ("kop als context") — een chunk zonder zijn
artikelaanduiding is ambigu voor retrieval én generatie.
"""
import re
from dataclasses import dataclass

import yaml

_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_H2 = re.compile(r"^## (.+)$")
_H3 = re.compile(r"^### (.+)$")


@dataclass
class ParsedChunk:
    ref: str
    kop: str
    tekst: str


@dataclass
class ParsedDocument:
    meta: dict
    chunks: list[ParsedChunk]


def parse_document(md: str) -> ParsedDocument:
    m = _FRONTMATTER.match(md)
    if not m:
        raise ValueError("corpusbestand mist frontmatter (--- ... ---)")
    meta = yaml.safe_load(m.group(1))
    body = md[m.end():]
    if meta.get("type") == "wettekst":
        chunks = _parse_wettekst(body)
    else:
        chunks = _parse_guidance(body)
    return ParsedDocument(meta=meta, chunks=chunks)


def _splits_kop(titel: str) -> tuple[str, str]:
    # "Artikel 6 — Kop" → anker + kop; "Overweging 61" heeft geen eigen kop
    delen = titel.split(" — ", 1)
    return delen[0].strip(), delen[1].strip() if len(delen) > 1 else ""


def _parse_wettekst(body: str) -> list[ParsedChunk]:
    chunks: list[ParsedChunk] = []
    anker = kop = ""
    sub: str | None = None
    regels: list[str] = []

    def sluit_af() -> None:
        tekst = "\n".join(regels).strip()
        regels.clear()
        if not anker or not tekst:
            return
        ref = f"{anker}, {sub}" if sub else anker
        prefix = f"{ref} ({kop}): " if kop else f"{ref}: "
        chunks.append(ParsedChunk(ref=ref, kop=kop, tekst=prefix + tekst))

    for regel in body.splitlines():
        if m := _H2.match(regel):
            sluit_af()
            anker, kop = _splits_kop(m.group(1))
            sub = None
        elif m := _H3.match(regel):
            sluit_af()
            s = m.group(1).strip()
            # "Lid 2" → "lid 2": de ref moet lezen als een juridische verwijzing
            sub = s[0].lower() + s[1:]
        else:
            regels.append(regel)
    sluit_af()
    return chunks


def _parse_guidance(body: str) -> list[ParsedChunk]:
    chunks: list[ParsedChunk] = []
    kop = ""
    regels: list[str] = []

    def sluit_af() -> None:
        tekst = "\n".join(regels).strip()
        regels.clear()
        if not kop or not tekst:
            return
        chunks.append(ParsedChunk(ref=kop, kop=kop, tekst=f"{kop}: {tekst}"))

    for regel in body.splitlines():
        if m := _H2.match(regel):
            sluit_af()
            kop = m.group(1).strip()
        else:
            regels.append(regel)
    sluit_af()
    return chunks
```

- [ ] **Step 4: Draai de tests, verwacht 7× PASS**

```bash
.venv/bin/pytest backend/tests/test_parser.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/ingest/ backend/tests/test_parser.py
git commit -m "Corpus-parser: chunken op wetsstructuur met kop-als-context"
```

---

### Task 4: Mistral-wrapper — embeddings en generatie

**Files:**
- Create: `backend/app/rag/__init__.py`, `backend/app/rag/mistral.py`
- Test: `backend/tests/test_mistral.py`

**Interfaces:**
- Consumes: `app.config.settings`
- Produces: `app.rag.mistral.embed(teksten: list[str]) -> list[list[float]]`, `app.rag.mistral.genereer(systeem: str, vraag: str) -> str`, `app.rag.mistral.MistralFout(Exception)`. Tests en evals vervangen `_klant()` via monkeypatch.

- [ ] **Step 1: Schrijf de falende tests `backend/tests/test_mistral.py`**

```python
from types import SimpleNamespace

import pytest

from app.rag import mistral


class NepEmbeddings:
    def create(self, model, inputs):
        return SimpleNamespace(data=[SimpleNamespace(embedding=[0.5] * 3) for _ in inputs])


class NepChat:
    def complete(self, model, temperature, messages):
        assert temperature == 0  # reproduceerbaarheid is een harde eis
        return SimpleNamespace(choices=[SimpleNamespace(
            message=SimpleNamespace(content="antwoord"))])


def test_embed_geeft_vector_per_tekst(monkeypatch):
    monkeypatch.setattr(mistral, "_klant",
                        lambda: SimpleNamespace(embeddings=NepEmbeddings()))
    assert mistral.embed(["a", "b"]) == [[0.5] * 3, [0.5] * 3]


def test_genereer_geeft_antwoordtekst(monkeypatch):
    monkeypatch.setattr(mistral, "_klant",
                        lambda: SimpleNamespace(chat=NepChat()))
    assert mistral.genereer("systeem", "vraag") == "antwoord"


def test_api_fout_wordt_mistralfout(monkeypatch):
    def kapot():
        raise RuntimeError("netwerk stuk")
    monkeypatch.setattr(mistral, "_klant", kapot)
    with pytest.raises(mistral.MistralFout):
        mistral.embed(["a"])
```

- [ ] **Step 2: Draai de tests, verwacht ImportError**

```bash
.venv/bin/pytest backend/tests/test_mistral.py -v
```

- [ ] **Step 3: Schrijf `backend/app/rag/__init__.py`** (leeg) **en `backend/app/rag/mistral.py`**

```python
"""Dunne wrapper om de Mistral-API. Aparte module zodat tests en evals de API
kunnen vervangen, en een latere modelwissel (een 'gemeten knop') op één plek
gebeurt. Elke API-fout wordt MistralFout: de API-laag vertaalt die naar 502."""
from mistralai import Mistral

from app.config import settings


class MistralFout(Exception):
    pass


_client: Mistral | None = None


def _klant() -> Mistral:
    global _client
    if _client is None:
        _client = Mistral(api_key=settings.mistral_api_key)
    return _client


def embed(teksten: list[str]) -> list[list[float]]:
    try:
        resp = _klant().embeddings.create(model=settings.embed_model, inputs=teksten)
    except Exception as e:
        raise MistralFout(str(e)) from e
    return [d.embedding for d in resp.data]


def genereer(systeem: str, vraag: str) -> str:
    try:
        resp = _klant().chat.complete(
            model=settings.chat_model,
            temperature=0,   # juridische antwoorden mogen niet per run variëren
            messages=[
                {"role": "system", "content": systeem},
                {"role": "user", "content": vraag},
            ],
        )
    except Exception as e:
        raise MistralFout(str(e)) from e
    return resp.choices[0].message.content
```

- [ ] **Step 4: Draai de tests, verwacht 3× PASS**

```bash
.venv/bin/pytest backend/tests/test_mistral.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/rag/ backend/tests/test_mistral.py
git commit -m "Mistral-wrapper: embeddings en generatie op temperatuur 0"
```

---

### Task 5: Prompt en citaten-extractie

**Files:**
- Create: `backend/app/rag/prompt.py`
- Test: `backend/tests/test_prompt.py`

**Interfaces:**
- Consumes: objecten met `.ref` en `.tekst` (ORM-`Chunk` of test-fakes)
- Produces: `app.rag.prompt.SYSTEEMPROMPT: str`, `bouw_vraagprompt(vraag: str, chunks) -> str`, `vind_citaten(antwoord: str, chunks) -> list` (subset van `chunks`).

- [ ] **Step 1: Schrijf de falende tests `backend/tests/test_prompt.py`**

```python
from dataclasses import dataclass

from app.rag import prompt


@dataclass
class NepChunk:
    ref: str
    tekst: str


CHUNKS = [
    NepChunk(ref="Artikel 6, lid 2", tekst="Artikel 6, lid 2 (Classificatie): tekst A"),
    NepChunk(ref="Overweging 61", tekst="Overweging 61: tekst B"),
]


def test_vraagprompt_labelt_elk_fragment_met_ref():
    p = prompt.bouw_vraagprompt("Wat is hoog risico?", CHUNKS)
    assert "[Artikel 6, lid 2]" in p
    assert "tekst A" in p
    assert "Wat is hoog risico?" in p


def test_vind_citaten_alleen_daadwerkelijk_genoemde_refs():
    # Het model kán geen citaat verzinnen: we matchen alleen tegen opgehaalde chunks
    antwoord = "Hoog risico volgt uit [Artikel 6, lid 2]."
    citaten = prompt.vind_citaten(antwoord, CHUNKS)
    assert [c.ref for c in citaten] == ["Artikel 6, lid 2"]


def test_vind_citaten_leeg_bij_abstentie():
    assert prompt.vind_citaten("Dat kan ik niet beantwoorden op basis van mijn bronnen.", CHUNKS) == []


def test_systeemprompt_bevat_abstentie_en_geen_advies():
    assert "geen juridisch advies" in prompt.SYSTEEMPROMPT
    assert "jurist" in prompt.SYSTEEMPROMPT
```

- [ ] **Step 2: Draai de tests, verwacht ImportError**

```bash
.venv/bin/pytest backend/tests/test_prompt.py -v
```

- [ ] **Step 3: Schrijf `backend/app/rag/prompt.py`**

```python
"""Promptopbouw en citaten-extractie. Citaten zijn altijd een subset van de
opgehaalde chunks: het model kiest refs, de fragmenten komen uit de database —
een verzonnen citaat is daarmee structureel onmogelijk (productprincipe 5)."""

SYSTEEMPROMPT = """Je bent AiActWijzer, een assistent die vragen over de EU AI Act beantwoordt.

Regels:
- Antwoord uitsluitend op basis van de meegegeven bronfragmenten.
- Verwijs bij elke claim naar de bron met de ref tussen blokhaken, bijvoorbeeld [Artikel 6, lid 2].
- Staat het antwoord niet in de fragmenten, zeg dan: "Dat kan ik niet beantwoorden op basis van mijn bronnen."
- Je geeft informatie, geen juridisch advies. Vraagt iemand om een oordeel over
  zijn specifieke situatie, leg dan uit wat de wet zegt en adviseer een jurist te raadplegen.
- Antwoord in het Nederlands, nuchter en zonder overdrijving."""


def bouw_vraagprompt(vraag: str, chunks) -> str:
    context = "\n\n".join(f"[{c.ref}]\n{c.tekst}" for c in chunks)
    return f"Bronfragmenten:\n\n{context}\n\nVraag: {vraag}"


def vind_citaten(antwoord: str, chunks) -> list:
    return [c for c in chunks if f"[{c.ref}]" in antwoord]
```

- [ ] **Step 4: Draai de tests, verwacht 4× PASS**

```bash
.venv/bin/pytest backend/tests/test_prompt.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/rag/prompt.py backend/tests/test_prompt.py
git commit -m "Prompt en citaten-extractie: refs alleen uit opgehaalde chunks"
```

---

### Task 6: Ingest — corpus naar database

**Files:**
- Create: `backend/app/ingest/__main__.py`
- Test: `backend/tests/test_ingest.py`

**Interfaces:**
- Consumes: `parse_document`, `Source`/`Chunk`, `mistral.embed`, `SessionLocal`, `init_db`
- Produces: `app.ingest.__main__.indexeer_bestand(sessie, pad: Path, corpus_root: Path, embed=...) -> int` (aantal chunks) en CLI `PYTHONPATH=backend python -m app.ingest [corpuspad]`.

- [ ] **Step 1: Schrijf de falende tests `backend/tests/test_ingest.py`**

```python
from pathlib import Path

from app.db import SessionLocal
from app.ingest.__main__ import indexeer_bestand
from app.models import Source

VOORBEELD = """---
bron: "Verordening (EU) 2024/1689"
url: https://example.org
versie: "test"
datum-opgehaald: 2026-07-19
stand-wetgeving: juli 2026
type: wettekst
---
## Artikel 1 — Onderwerp
### Lid 1
Eerste lid.
### Lid 2
Tweede lid.
"""


def nep_embed(teksten):
    return [[0.1] * 1024 for _ in teksten]


def test_indexeren_en_idempotent_herindexeren(db, tmp_path: Path):
    (tmp_path / "wet").mkdir()
    bestand = tmp_path / "wet" / "artikelen.md"
    bestand.write_text(VOORBEELD)

    with SessionLocal() as sessie:
        sessie.query(Source).filter_by(slug="wet/artikelen").delete()
        sessie.commit()

        n = indexeer_bestand(sessie, bestand, tmp_path, embed=nep_embed)
        sessie.commit()
        assert n == 2

        # Idempotentie: nogmaals indexeren mag geen duplicaten opleveren
        indexeer_bestand(sessie, bestand, tmp_path, embed=nep_embed)
        sessie.commit()
        bron = sessie.query(Source).filter_by(slug="wet/artikelen").one()
        assert len(bron.chunks) == 2
        assert bron.chunks[0].ref == "Artikel 1, lid 1"

        sessie.delete(bron)
        sessie.commit()
```

- [ ] **Step 2: Draai de test, verwacht ImportError**

```bash
.venv/bin/pytest backend/tests/test_ingest.py -v
```

- [ ] **Step 3: Schrijf `backend/app/ingest/__main__.py`**

```python
"""Indexeert het corpus: markdown → chunks → embeddings → database.

Idempotent per bron: bestaande chunks van dezelfde slug gaan eerst weg (cascade),
zodat een herindexering nooit een halve stand achterlaat. De hele run is één
transactie: bij een fout blijft de oude index intact.
"""
import sys
from pathlib import Path

from sqlalchemy import select

from app.db import SessionLocal, init_db
from app.ingest.parser import parse_document
from app.models import Chunk, Source
from app.rag import mistral

BATCH = 64  # embed-batchgrootte; ruim onder de API-limiet


def indexeer_bestand(sessie, pad: Path, corpus_root: Path, embed=mistral.embed) -> int:
    doc = parse_document(pad.read_text())
    slug = str(pad.relative_to(corpus_root).with_suffix(""))

    bestaande = sessie.scalar(select(Source).where(Source.slug == slug))
    if bestaande is not None:
        sessie.delete(bestaande)
        sessie.flush()

    bron = Source(slug=slug, titel=doc.meta["bron"], url=str(doc.meta["url"]),
                  versie=str(doc.meta["versie"]), datum=str(doc.meta["datum-opgehaald"]),
                  type=doc.meta["type"])
    sessie.add(bron)

    teksten = [c.tekst for c in doc.chunks]
    vectoren: list[list[float]] = []
    for i in range(0, len(teksten), BATCH):
        vectoren.extend(embed(teksten[i:i + BATCH]))

    for volgorde, (chunk, vector) in enumerate(zip(doc.chunks, vectoren)):
        sessie.add(Chunk(source=bron, ref=chunk.ref, kop=chunk.kop,
                         tekst=chunk.tekst, volgorde=volgorde, embedding=vector))
    return len(doc.chunks)


def main() -> None:
    corpus_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("corpus")
    init_db()
    with SessionLocal() as sessie:
        for pad in sorted(corpus_root.rglob("*.md")):
            n = indexeer_bestand(sessie, pad, corpus_root)
            print(f"{pad}: {n} chunks")
        sessie.commit()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Draai de test, verwacht PASS**

```bash
.venv/bin/pytest backend/tests/test_ingest.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/ingest/__main__.py backend/tests/test_ingest.py
git commit -m "Ingest: idempotent indexeren van corpus naar pgvector"
```

---

### Task 7: Retrieval en RAG-service

**Files:**
- Create: `backend/app/rag/retrieval.py`, `backend/app/rag/service.py`
- Test: `backend/tests/test_retrieval.py`, `backend/tests/test_service.py`

**Interfaces:**
- Consumes: `mistral.embed`, `mistral.genereer`, `prompt.*`, `Chunk`, `settings.top_k`
- Produces: `app.rag.retrieval.zoek_chunks(sessie, vraag: str, top_k: int | None = None) -> list[Chunk]`; `app.rag.service.beantwoord(sessie, vraag: str) -> AskResultaat` met `AskResultaat(antwoord: str, citaten: list[Citaat], stand_van_wetgeving: str, opgehaalde_refs: list[str])` en `Citaat(ref: str, fragment: str, bron: str)`. `opgehaalde_refs` is voor de eval-suite (retrieval-metric); de API-laag geeft dit veld niet terug.

- [ ] **Step 1: Schrijf de falende test `backend/tests/test_retrieval.py`**

```python
from app.db import SessionLocal
from app.models import Chunk, Source
from app.rag import mistral, retrieval


def test_dichtstbijzijnde_chunk_eerst(db, monkeypatch):
    with SessionLocal() as sessie:
        sessie.query(Source).filter_by(slug="test/retrieval").delete()
        bron = Source(slug="test/retrieval", titel="T", url="u", versie="1",
                      datum="2026-07-19", type="wettekst")
        # Twee orthogonale vectoren: de vraagvector wijst exact naar chunk A
        bron.chunks.append(Chunk(ref="A", kop="", tekst="A", volgorde=0,
                                 embedding=[1.0] + [0.0] * 1023))
        bron.chunks.append(Chunk(ref="B", kop="", tekst="B", volgorde=1,
                                 embedding=[0.0, 1.0] + [0.0] * 1022))
        sessie.add(bron)
        sessie.commit()

        monkeypatch.setattr(mistral, "embed", lambda t: [[1.0] + [0.0] * 1023])
        chunks = retrieval.zoek_chunks(sessie, "vraag", top_k=1)
        assert [c.ref for c in chunks] == ["A"]

        sessie.delete(sessie.query(Source).filter_by(slug="test/retrieval").one())
        sessie.commit()
```

- [ ] **Step 2: Schrijf de falende test `backend/tests/test_service.py`**

```python
from dataclasses import dataclass

from app.rag import service


@dataclass
class NepSource:
    titel: str


@dataclass
class NepChunk:
    ref: str
    tekst: str
    source: NepSource


def test_beantwoord_bundelt_antwoord_citaten_en_refs(monkeypatch):
    chunks = [NepChunk(ref="Artikel 6, lid 2",
                       tekst="Artikel 6, lid 2 (Classificatie): tekst A",
                       source=NepSource(titel="Verordening (EU) 2024/1689")),
              NepChunk(ref="Overweging 61", tekst="Overweging 61: tekst B",
                       source=NepSource(titel="Verordening (EU) 2024/1689"))]
    monkeypatch.setattr(service.retrieval, "zoek_chunks", lambda s, v: chunks)
    monkeypatch.setattr(service.mistral, "genereer",
                        lambda systeem, vraag: "Zie [Artikel 6, lid 2].")

    r = service.beantwoord(None, "Wat is hoog risico?")

    assert r.antwoord == "Zie [Artikel 6, lid 2]."
    assert [c.ref for c in r.citaten] == ["Artikel 6, lid 2"]
    assert r.citaten[0].bron == "Verordening (EU) 2024/1689"
    assert r.opgehaalde_refs == ["Artikel 6, lid 2", "Overweging 61"]
    assert r.stand_van_wetgeving == "juli 2026"
```

- [ ] **Step 3: Draai beide tests, verwacht ImportError**

```bash
.venv/bin/pytest backend/tests/test_retrieval.py backend/tests/test_service.py -v
```

- [ ] **Step 4: Schrijf `backend/app/rag/retrieval.py`**

```python
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
```

- [ ] **Step 5: Schrijf `backend/app/rag/service.py`**

```python
"""De RAG-keten: retrieval → generatie → citaten. Eén codepad voor API én
eval-suite, zodat de eval meet wat de gebruiker echt krijgt."""
from dataclasses import dataclass

from app.config import settings
from app.rag import mistral, prompt, retrieval


@dataclass
class Citaat:
    ref: str
    fragment: str
    bron: str


@dataclass
class AskResultaat:
    antwoord: str
    citaten: list[Citaat]
    stand_van_wetgeving: str
    opgehaalde_refs: list[str]   # voor de retrieval-metric; niet in de API-respons


def beantwoord(sessie, vraag: str) -> AskResultaat:
    chunks = retrieval.zoek_chunks(sessie, vraag)
    antwoord = mistral.genereer(prompt.SYSTEEMPROMPT,
                                prompt.bouw_vraagprompt(vraag, chunks))
    citaten = [Citaat(ref=c.ref, fragment=c.tekst, bron=c.source.titel)
               for c in prompt.vind_citaten(antwoord, chunks)]
    return AskResultaat(antwoord=antwoord, citaten=citaten,
                        stand_van_wetgeving=settings.stand_van_wetgeving,
                        opgehaalde_refs=[c.ref for c in chunks])
```

- [ ] **Step 6: Draai beide tests, verwacht PASS**

```bash
.venv/bin/pytest backend/tests/test_retrieval.py backend/tests/test_service.py -v
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/rag/retrieval.py backend/app/rag/service.py backend/tests/test_retrieval.py backend/tests/test_service.py
git commit -m "Retrieval en RAG-service: één codepad voor API en eval"
```

---

### Task 8: FastAPI-laag — POST /ask en GET /health

**Files:**
- Create: `backend/app/main.py`
- Test: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: `service.beantwoord`, `MistralFout`, `SessionLocal`
- Produces: `POST /ask` (body `{"vraag": str}` → `{"antwoord", "citaten": [{"ref","fragment","bron"}], "stand_van_wetgeving"}`), `GET /health`. `MistralFout` → HTTP 502.

- [ ] **Step 1: Schrijf de falende tests `backend/tests/test_api.py`**

```python
from fastapi.testclient import TestClient

from app.main import app
from app.rag import service
from app.rag.mistral import MistralFout
from app.rag.service import AskResultaat, Citaat

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_ask_geeft_antwoord_met_citaten(monkeypatch):
    resultaat = AskResultaat(
        antwoord="Zie [Artikel 6, lid 2].",
        citaten=[Citaat(ref="Artikel 6, lid 2", fragment="tekst", bron="Verordening")],
        stand_van_wetgeving="juli 2026",
        opgehaalde_refs=["Artikel 6, lid 2"],
    )
    monkeypatch.setattr(service, "beantwoord", lambda sessie, vraag: resultaat)

    data = client.post("/ask", json={"vraag": "Wat is hoog risico?"}).json()

    assert data["antwoord"] == "Zie [Artikel 6, lid 2]."
    assert data["citaten"][0]["ref"] == "Artikel 6, lid 2"
    # interne refs horen niet in de publieke respons
    assert "opgehaalde_refs" not in data


def test_mistralfout_wordt_502(monkeypatch):
    def kapot(sessie, vraag):
        raise MistralFout("api plat")
    monkeypatch.setattr(service, "beantwoord", kapot)

    r = client.post("/ask", json={"vraag": "x"})
    assert r.status_code == 502
```

- [ ] **Step 2: Draai de tests, verwacht ImportError**

```bash
.venv/bin/pytest backend/tests/test_api.py -v
```

- [ ] **Step 3: Schrijf `backend/app/main.py`**

```python
"""FastAPI-laag: dun schilletje om de RAG-service. Geen fallback-antwoorden bij
een modelfout — liever een eerlijke 502 dan een half juridisch antwoord."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.db import SessionLocal
from app.rag import service
from app.rag.mistral import MistralFout

app = FastAPI(title="AiActWijzer")


class AskVraag(BaseModel):
    vraag: str


class CitaatUit(BaseModel):
    ref: str
    fragment: str
    bron: str


class AskAntwoord(BaseModel):
    antwoord: str
    citaten: list[CitaatUit]
    stand_van_wetgeving: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=AskAntwoord)
def ask(body: AskVraag):
    with SessionLocal() as sessie:
        try:
            return service.beantwoord(sessie, body.vraag)
        except MistralFout as e:
            raise HTTPException(status_code=502, detail=f"Modelaanroep mislukt: {e}")
```

- [ ] **Step 4: Draai de tests, verwacht 3× PASS**

```bash
.venv/bin/pytest backend/tests/test_api.py -v
```

- [ ] **Step 5: Draai de volledige suite**

```bash
.venv/bin/pytest
```

Verwacht: alles PASS (db-tests eventueel SKIP zonder Docker).

- [ ] **Step 6: Commit**

```bash
git add backend/app/main.py backend/tests/test_api.py
git commit -m "FastAPI-laag: POST /ask met citaten, nette 502 bij modelfout"
```

---

### Task 9: Wettekst-corpus — EUR-Lex converteren naar markdown

**Files:**
- Create: `scripts/converteer_eurlex.py`, `corpus/verordening-2024-1689/overwegingen.md`, `corpus/verordening-2024-1689/artikelen.md`, `corpus/verordening-2024-1689/bijlagen.md`

> De spec noemt als voorbeeld meerdere artikel-bestanden; één `artikelen.md` is
> eenvoudiger en voor parser en retrieval gelijkwaardig — de chunks zijn hetzelfde.

**Interfaces:**
- Produces: drie corpus-markdownbestanden in het formaat van Task 3 (frontmatter + `## Artikel N — Kop` / `### Lid N` / `## Bijlage III — Kop` / `### Punt N` / `## Overweging N`).

- [ ] **Step 1: Zoek de geconsolideerde NL-versie op EUR-Lex**

Open `https://eur-lex.europa.eu/legal-content/NL/TXT/?uri=CELEX:32024R1689` en zoek onder "Huidige geconsolideerde versie" de meest recente datum (na de Digital Omnibus, jul 2026, verwacht formaat `02024R1689-2026MMDD`). Download de HTML:

```bash
curl -sL "https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:02024R1689-<DATUM>" \
  -o /tmp/claude-1000/-home-koenmeijer-projecten-AiActWijzer/bf2b1c43-e8b9-4aee-98c3-a713e3ab2ada/scratchpad/eurlex.html
```

Verwacht: een HTML-bestand van meerdere MB. **Als er geen consolidatie ná jul 2026 bestaat**, pak dan de nieuwste die er wél is en noteer dat — Step 5 repareert de omnibus-datums dan handmatig.

- [ ] **Step 2: Schrijf `scripts/converteer_eurlex.py`**

```python
"""Eenmalige conversie: EUR-Lex geconsolideerde NL-tekst (HTML) → corpus-markdown.

Werkt op de tekststructuur (regels), niet op CSS-klassen: EUR-Lex-markup wisselt
per versie, maar de tekstconventies ("Artikel 6" op een eigen regel) zijn stabiel.
De sanity-checks onderaan falen hard als de structuur afwijkt — dan de regexes
bijstellen, niet de checks.

Gebruik: python scripts/converteer_eurlex.py <eurlex.html> <bron-url> <versie-label>
"""
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

ARTIKEL = re.compile(r"^Artikel (\d+)$")
BIJLAGE = re.compile(r"^BIJLAGE ([IVXLC]+)$")
LID = re.compile(r"^(\d+)\.\s+")
OVERWEGING = re.compile(r"^\((\d+)\)\s+")
EINDE_PREAMBULE = "HEBBEN DE VOLGENDE VERORDENING VASTGESTELD"


def frontmatter(url: str, versie: str) -> str:
    return f"""---
bron: "Verordening (EU) 2024/1689 (AI-verordening)"
url: {url}
versie: "{versie}"
datum-opgehaald: 2026-07-19
stand-wetgeving: juli 2026
type: wettekst
---

"""


def lees_regels(html_pad: Path) -> list[str]:
    soup = BeautifulSoup(html_pad.read_text(), "html.parser")
    regels = [r.strip() for r in soup.get_text("\n").splitlines()]
    # EUR-Lex-consolidaties bevatten wijzigingsmarkeringen (▼M1 e.d.) — geen inhoud
    return [r for r in regels if r and not r.startswith("▼")]


def schrijf_overwegingen(regels: list[str], uit: Path, url: str, versie: str) -> int:
    einde = next(i for i, r in enumerate(regels) if EINDE_PREAMBULE in r)
    delen: list[str] = []
    nummer = None
    for r in regels[:einde]:
        if m := OVERWEGING.match(r):
            nummer = m.group(1)
            delen.append(f"\n## Overweging {nummer}\n\n{OVERWEGING.sub('', r)}")
        elif nummer is not None:
            delen.append(r)
    uit.write_text(frontmatter(url, versie) + "\n".join(delen) + "\n")
    return len([d for d in delen if d.startswith("\n## ")])


def schrijf_artikelen(regels: list[str], uit: Path, url: str, versie: str) -> int:
    start = next(i for i, r in enumerate(regels) if EINDE_PREAMBULE in r)
    einde = next((i for i, r in enumerate(regels) if BIJLAGE.match(r)), len(regels))
    delen: list[str] = []
    in_artikel = False
    verwacht_kop = False
    for r in regels[start + 1:einde]:
        if ARTIKEL.match(r):
            delen.append(f"\n## {r}")   # kop volgt op de volgende regel
            in_artikel = True
            verwacht_kop = True
        elif verwacht_kop:
            delen[-1] += f" — {r}"
            verwacht_kop = False
        elif in_artikel and LID.match(r):
            delen.append(f"\n### Lid {LID.match(r).group(1)}\n\n{LID.sub('', r)}")
        elif in_artikel and not r.startswith(("HOOFDSTUK", "AFDELING")):
            delen.append(r)
    uit.write_text(frontmatter(url, versie) + "\n".join(delen) + "\n")
    return len([d for d in delen if d.startswith("\n## ")])


def schrijf_bijlagen(regels: list[str], uit: Path, url: str, versie: str) -> int:
    start = next((i for i, r in enumerate(regels) if BIJLAGE.match(r)), None)
    if start is None:
        raise SystemExit("geen bijlagen gevonden — controleer de HTML")
    delen: list[str] = []
    verwacht_kop = False
    for r in regels[start:]:
        if m := BIJLAGE.match(r):
            delen.append(f"\n## Bijlage {m.group(1)}")
            verwacht_kop = True
        elif verwacht_kop:
            delen[-1] += f" — {r}"
            verwacht_kop = False
        elif LID.match(r):
            delen.append(f"\n### Punt {LID.match(r).group(1)}\n\n{LID.sub('', r)}")
        else:
            delen.append(r)
    uit.write_text(frontmatter(url, versie) + "\n".join(delen) + "\n")
    return len([d for d in delen if d.startswith("\n## ")])


def main() -> None:
    html_pad, url, versie = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    regels = lees_regels(html_pad)
    doel = Path("corpus/verordening-2024-1689")
    doel.mkdir(parents=True, exist_ok=True)

    n_ov = schrijf_overwegingen(regels, doel / "overwegingen.md", url, versie)
    n_art = schrijf_artikelen(regels, doel / "artikelen.md", url, versie)
    n_bijl = schrijf_bijlagen(regels, doel / "bijlagen.md", url, versie)
    print(f"overwegingen: {n_ov}, artikelen: {n_art}, bijlagen: {n_bijl}")

    # Sanity-checks: falen hard, want een stil half corpus is erger dan geen corpus
    assert n_art == 113, f"verwacht 113 artikelen, kreeg {n_art}"
    assert n_ov >= 150, f"verwacht ≥150 overwegingen, kreeg {n_ov}"
    tekst = (doel / "bijlagen.md").read_text()
    assert "## Bijlage III" in tekst, "bijlage III ontbreekt"


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Draai de conversie**

```bash
.venv/bin/python scripts/converteer_eurlex.py \
  <scratchpad>/eurlex.html \
  "https://eur-lex.europa.eu/legal-content/NL/TXT/?uri=CELEX:02024R1689-<DATUM>" \
  "geconsolideerde versie <DATUM>"
```

Verwacht: `overwegingen: ~180, artikelen: 113, bijlagen: 13` en geen assert-fout. **Faalt een assert**: bekijk de eerste 200 regels van `lees_regels`-uitvoer, stel de regexes bij tot de checks slagen (dit hoort bij deze taak; de checks zelf blijven staan).

- [ ] **Step 4: Steekproef op de kritieke artikelen**

```bash
grep -A3 "## Artikel 6 " corpus/verordening-2024-1689/artikelen.md | head -8
grep -A3 "## Artikel 50 " corpus/verordening-2024-1689/artikelen.md | head -8
grep -A3 "## Artikel 113 " corpus/verordening-2024-1689/artikelen.md | head -20
grep -c "### Punt" corpus/verordening-2024-1689/bijlagen.md
```

Verwacht: art. 6 gaat over classificatie, art. 50 over transparantie, art. 113 over toepassingsdatums; bijlagen bevatten punten. Lees de output echt — dit is de controle dat het corpus klopt.

- [ ] **Step 5: Controleer de omnibus-datums**

```bash
grep -n "2 december 2027\|2 augustus 2026\|2 december 2026" corpus/verordening-2024-1689/artikelen.md
```

Verwacht (consolidatie ná omnibus): art. 113 noemt **2 december 2027** voor bijlage III-systemen en **2 augustus 2028** voor bijlage I. **Zo niet** (oudere consolidatie): pas de datums handmatig aan volgens de omnibus-tabel — bijlage III-deadline `2 augustus 2026` → `2 december 2027`; bijlage I `augustus 2027` → `2 augustus 2028`; art. 50-watermerken bestaande systemen → `2 december 2026` — en zet in de frontmatter-`versie`: `"geconsolideerd <DATUM>, omnibus-datums handmatig doorgevoerd (bron: Digital Omnibus on AI, jul 2026)"`.

- [ ] **Step 6: Commit**

```bash
git add scripts/converteer_eurlex.py corpus/verordening-2024-1689/
git commit -m "Wettekst-corpus: NL-verordening 2024/1689 als markdown (incl. omnibus-datums)"
```

---

### Task 10: NL-guidance-corpus

**Files:**
- Create: `corpus/nl-guidance/uaiv-toezicht.md`

**Interfaces:**
- Produces: guidance-corpus waarvan de `##`-koppen de refs zijn; de golden set (Task 11) verwijst met prefixen "UAIV" en "Algoritmeregister" naar deze koppen.

- [ ] **Step 1: Schrijf `corpus/nl-guidance/uaiv-toezicht.md`**

> Inhoud is een eigen samenvatting op basis van publieke bronnen (stand jul 2026),
> geadministreerd in de frontmatter. Feiten komen uit de bronnenset van het project.

```markdown
---
bron: "NL-doorwerking AI-verordening — samenvatting UAIV en toezicht (eigen redactie op basis van publieke bronnen)"
url: https://www.internetconsultatie.nl/uaiv/b1
versie: "stand juli 2026 — consultatie gesloten (1 juni 2026), advies Raad van State loopt, nog niet bij de Tweede Kamer"
datum-opgehaald: 2026-07-19
stand-wetgeving: juli 2026
type: guidance
---

## UAIV — wat de Uitvoeringswet AI-verordening regelt

De AI-verordening (EU) 2024/1689 werkt als verordening rechtstreeks in Nederland;
er is geen omzettingswet nodig zoals bij een richtlijn. Nederland regelt zelf
alleen het toezicht en de handhaving, via de Uitvoeringswet AI-verordening (UAIV).
Stand juli 2026: de internetconsultatie is gesloten (liep tot 1 juni 2026); na
advies van de Raad van State gaat het wetsvoorstel naar de Tweede Kamer. Er is
dus nog geen vastgestelde Nederlandse toezichtswet.

## UAIV — beoogde toezichthouders in Nederland

Het kabinet kiest niet voor één nieuwe AI-toezichthouder, maar belegt het
markttoezicht bij bestaande toezichthouders binnen hun eigen domein. Beoogd zijn
onder meer: de Autoriteit Persoonsgegevens (AP, met een coördinerende rol via de
Directie Coördinatie Algoritmes), de Rijksinspectie Digitale Infrastructuur (RDI),
de ILT, de IGJ, de NVWA en de Arbeidsinspectie, en voor de financiële sector de
AFM en DNB. Voor de rechtspraak gelden bijzondere voorzieningen (procureur-generaal
bij de Hoge Raad, Afdeling bestuursrechtspraak van de Raad van State). De ACM
staat niet in het rijtje beoogde AI-markttoezichthouders. Uit de uitvoeringstoetsen
kwam kritiek: taakverdeling, capaciteit en gegevensdeling tussen toezichthouders
moeten scherper.

## Algoritmeregister — rijksbeleid, geen eis uit de AI-verordening

Het Algoritmeregister (algoritmes.overheid.nl) is een Nederlands
transparantie-initiatief. Publicatie is voor de rijksoverheid deels verplicht op
grond van rijksbeleid, maar het is géén verplichting uit de AI-verordening. De
twee worden vaak verward; houd ze uit elkaar bij compliance-vragen.

## IAMA en FRIA — Nederlands instrument naast een Europese plicht

Het Impact Assessment Mensenrechten en Algoritmes (IAMA) is een Nederlands
instrument en de voorloper van de grondrechteneffectbeoordeling (FRIA) die de
AI-verordening in artikel 27 verplicht stelt voor onder meer overheidsorganen
die hoog-risico-AI-systemen inzetten. Een uitgevoerd IAMA is geen automatische
FRIA; de FRIA-eisen uit de verordening zijn leidend.
```

- [ ] **Step 2: Verifieer dat de parser het bestand accepteert**

```bash
PYTHONPATH=backend .venv/bin/python -c "
from pathlib import Path
from app.ingest.parser import parse_document
doc = parse_document(Path('corpus/nl-guidance/uaiv-toezicht.md').read_text())
print([c.ref for c in doc.chunks])"
```

Verwacht: vier refs, beginnend met `UAIV — wat de Uitvoeringswet AI-verordening regelt`.

- [ ] **Step 3: Commit**

```bash
git add corpus/nl-guidance/
git commit -m "NL-guidance-corpus: UAIV, toezichthouders, Algoritmeregister, IAMA/FRIA"
```

---

### Task 11: Eval-suite — scoring, golden set, runner

**Files:**
- Create: `evals/__init__.py`, `evals/scoring.py`, `evals/golden_set.yaml`, `evals/run_evals.py`, `evals/results/.gitkeep`
- Test: `evals/test_scoring.py`

**Interfaces:**
- Consumes: `service.beantwoord` (veld `opgehaalde_refs`), `SessionLocal`
- Produces: `evals.scoring.ref_matcht(verwacht, ref) -> bool`, `score_retrieval(verwachte_refs, opgehaalde_refs) -> bool`, `score_grounding(markers, verboden, antwoord) -> bool`, `score_abstentie(moet_abstineren, antwoord) -> bool`; CLI `PYTHONPATH=backend python evals/run_evals.py` (exit ≠ 0 bij falen).

- [ ] **Step 1: Schrijf de falende tests `evals/test_scoring.py`**

```python
from evals import scoring


def test_ref_prefix_matcht_maar_geen_cijferbotsing():
    assert scoring.ref_matcht("Artikel 113", "Artikel 113, lid 2")
    assert scoring.ref_matcht("UAIV", "UAIV — beoogde toezichthouders in Nederland")
    # "Artikel 6" mag niet stiekem "Artikel 60" goedkeuren
    assert not scoring.ref_matcht("Artikel 6", "Artikel 60")


def test_retrieval_een_verwachte_ref_volstaat():
    assert scoring.score_retrieval(["Artikel 6", "Bijlage III"], ["Bijlage III, punt 4"])
    assert not scoring.score_retrieval(["Artikel 6"], ["Artikel 50"])
    assert scoring.score_retrieval([], ["wat dan ook"])  # abstentie-case: geen eis


def test_grounding_vereist_alle_markers_en_geen_verboden():
    assert scoring.score_grounding(["2 december 2027"], ["2 augustus 2026"],
                                   "De deadline is 2 december 2027.")
    assert not scoring.score_grounding(["2 december 2027"], ["2 augustus 2026"],
                                       "De deadline is 2 augustus 2026.")
    assert not scoring.score_grounding(["2 december 2027"], [], "Geen datum genoemd.")


def test_abstentie_eist_weigering_alleen_als_dat_moet():
    assert scoring.score_abstentie(True, "Dat kan ik niet beantwoorden op basis van mijn bronnen.")
    assert not scoring.score_abstentie(True, "Het antwoord is 42.")
    assert scoring.score_abstentie(False, "Het antwoord is 42.")
```

- [ ] **Step 2: Draai de tests, verwacht ImportError**

```bash
.venv/bin/pytest evals/test_scoring.py -v
```

- [ ] **Step 3: Schrijf `evals/__init__.py`** (leeg) **en `evals/scoring.py`**

```python
"""Deterministische scoring: marker-matching, geen LLM-judge (docs/eval-aanpak.md).
Reproduceerbaar en gratis; nuance kan later met een judge als de set groeit."""
import re


def ref_matcht(verwacht: str, ref: str) -> bool:
    # Woordgrens-check: "Artikel 6" matcht "Artikel 6, lid 2" maar niet "Artikel 60"
    return re.search(rf"(?<!\w){re.escape(verwacht)}(?!\w)", ref, re.IGNORECASE) is not None


def score_retrieval(verwachte_refs: list[str], opgehaalde_refs: list[str]) -> bool:
    if not verwachte_refs:
        return True   # abstentie-cases stellen geen retrieval-eis
    return any(ref_matcht(v, ref) for v in verwachte_refs for ref in opgehaalde_refs)


def score_grounding(markers: list[str], verboden: list[str], antwoord: str) -> bool:
    laag = antwoord.lower()
    return (all(m.lower() in laag for m in markers)
            and not any(v.lower() in laag for v in verboden))


# Steekproefsgewijs handmatig blijven controleren: een geldige weigering die hier
# niet in staat is een false negative van de eval, niet van het systeem.
WEIGER_MARKERS = [
    "kan ik niet beantwoorden",
    "niet in mijn bronnen",
    "raadpleeg een jurist",
    "jurist te raadplegen",
]


def score_abstentie(moet_abstineren: bool, antwoord: str) -> bool:
    if not moet_abstineren:
        return True   # n.v.t.; een onterecht weigerend antwoord zakt op grounding
    laag = antwoord.lower()
    return any(m in laag for m in WEIGER_MARKERS)
```

- [ ] **Step 4: Draai de tests, verwacht 4× PASS**

```bash
.venv/bin/pytest evals/test_scoring.py -v
```

- [ ] **Step 5: Schrijf `evals/golden_set.yaml`** (10 cases, vijf categorieën)

```yaml
# Golden set — draait bij elke wijziging aan chunking, prompt of model.
# Markers zijn deterministisch; bij aanpassing altijd handmatig een antwoord
# nalezen ("evalueer je eval").

- id: actualiteit-hoogrisico-deadline
  categorie: actualiteit
  vraag: "Vanaf wanneer moeten hoog-risico-AI-systemen uit bijlage III aan de verplichtingen van de AI-verordening voldoen?"
  retrieval_refs: ["Artikel 113"]
  grounding_markers: ["2 december 2027"]
  verboden_markers: ["2 augustus 2026"]
  abstentie: false

- id: actualiteit-watermerken
  categorie: actualiteit
  vraag: "Wanneer moeten bestaande AI-systemen voldoen aan de transparantie- en watermerkverplichtingen van artikel 50?"
  retrieval_refs: ["Artikel 50", "Artikel 113", "Digital Omnibus"]
  grounding_markers: ["2 december 2026"]
  verboden_markers: []
  abstentie: false

- id: risico-cv-screening
  categorie: risicoclassificatie
  vraag: "Wij gebruiken een AI-systeem om cv's te screenen bij werving en selectie. In welke risicocategorie valt dat?"
  retrieval_refs: ["Bijlage III", "Artikel 6"]
  grounding_markers: ["hoog risico", "bijlage III"]
  verboden_markers: []
  abstentie: false

- id: risico-social-scoring
  categorie: risicoclassificatie
  vraag: "Mag een gemeente inwoners met AI een sociale score geven op basis van hun gedrag?"
  retrieval_refs: ["Artikel 5"]
  grounding_markers: ["verboden"]
  verboden_markers: []
  abstentie: false

- id: rol-aanbieder-gebruiksverantwoordelijke
  categorie: rolbepaling
  vraag: "Wat is het verschil tussen een aanbieder en een gebruiksverantwoordelijke onder de AI-verordening?"
  retrieval_refs: ["Artikel 3"]
  grounding_markers: ["aanbieder", "gebruiksverantwoordelijke"]
  verboden_markers: []
  abstentie: false

- id: rol-fria-overheid
  categorie: rolbepaling
  vraag: "Moet een overheidsorganisatie iets extra's doen voordat zij een hoog-risico-AI-systeem in gebruik neemt?"
  retrieval_refs: ["Artikel 27"]
  grounding_markers: ["grondrechten"]
  verboden_markers: []
  abstentie: false

- id: nl-toezicht-uaiv
  categorie: nl-doorwerking
  vraag: "Wie gaat er in Nederland toezicht houden op de naleving van de AI-verordening?"
  retrieval_refs: ["UAIV"]
  grounding_markers: ["Uitvoeringswet", "Autoriteit Persoonsgegevens"]
  verboden_markers: []
  abstentie: false

- id: nl-algoritmeregister
  categorie: nl-doorwerking
  vraag: "Is publicatie in het Algoritmeregister verplicht op grond van de AI-verordening?"
  retrieval_refs: ["Algoritmeregister"]
  grounding_markers: ["rijksbeleid"]
  verboden_markers: []
  abstentie: false

- id: abstentie-juridisch-advies
  categorie: abstentie
  vraag: "Kunnen jullie voor ons bedrijf beoordelen of ons systeem aan de AI-verordening voldoet en dat schriftelijk bevestigen?"
  retrieval_refs: []
  grounding_markers: []
  verboden_markers: []
  abstentie: true

- id: abstentie-buiten-scope
  categorie: abstentie
  vraag: "Welke verplichtingen legt de Data Act op aan cloudaanbieders?"
  retrieval_refs: []
  grounding_markers: []
  verboden_markers: []
  abstentie: true
```

- [ ] **Step 6: Schrijf `evals/run_evals.py`**

```python
"""Draait de golden set door de echte RAG-keten (in-process, zelfde codepad als
de API) en print een scorekaart. Het JSON-resultaat in evals/results/ is het
regressiespoor én governance-bewijs: aantoonbare, herhaalbare kwaliteitscontrole."""
import datetime
import json
import sys
from pathlib import Path

import yaml

from app.config import settings
from app.db import SessionLocal
from app.rag import service
from evals import scoring

METRICS = ("retrieval", "grounding", "abstentie")


def main() -> None:
    cases = yaml.safe_load(Path("evals/golden_set.yaml").read_text())
    resultaten = []
    with SessionLocal() as sessie:
        for case in cases:
            r = service.beantwoord(sessie, case["vraag"])
            resultaten.append({
                "id": case["id"],
                "categorie": case["categorie"],
                "retrieval": scoring.score_retrieval(case["retrieval_refs"], r.opgehaalde_refs),
                "grounding": scoring.score_grounding(case["grounding_markers"],
                                                     case["verboden_markers"], r.antwoord),
                "abstentie": scoring.score_abstentie(case["abstentie"], r.antwoord),
                "antwoord": r.antwoord,
                "opgehaalde_refs": r.opgehaalde_refs,
            })

    print(f"\n{'case':<40} {'retr':>5} {'grond':>6} {'abst':>5}")
    for r in resultaten:
        v = {m: "✓" if r[m] else "✗" for m in METRICS}
        print(f"{r['id']:<40} {v['retrieval']:>5} {v['grounding']:>6} {v['abstentie']:>5}")
    for m in METRICS:
        n = sum(r[m] for r in resultaten)
        print(f"{m}: {n}/{len(resultaten)}")

    stempel = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    uit = Path("evals/results") / f"run-{stempel}.json"
    uit.write_text(json.dumps({
        "tijdstip": stempel,
        "config": {"chat_model": settings.chat_model, "embed_model": settings.embed_model,
                   "top_k": settings.top_k},
        "resultaten": resultaten,
    }, ensure_ascii=False, indent=2))
    print(f"\nresultaat: {uit}")

    geslaagd = all(all(r[m] for m in METRICS) for r in resultaten)
    sys.exit(0 if geslaagd else 1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 7: Maak `evals/results/.gitkeep`** (leeg bestand) en voeg aan `.gitignore` toe:

```gitignore
evals/results/*.json
```

> Resultaten zijn een lokaal regressiespoor; de scorekaart die we wél delen
> committen we bewust in Task 12.

- [ ] **Step 8: Draai de volledige testsuite**

```bash
.venv/bin/pytest
```

Verwacht: alles PASS.

- [ ] **Step 9: Commit**

```bash
git add evals/ .gitignore
git commit -m "Eval-suite: deterministische scoring, golden set (10 cases), runner"
```

---

### Task 12: End-to-end — indexeren, eval draaien, README

**Files:**
- Create: `README.md`
- Modify: `evals/golden_set.yaml` (alleen als de handmatige controle een eval-fout aantoont), `.gitignore`

**Interfaces:**
- Consumes: alles hiervoor. Dit is de integratietaak: echte Mistral-calls, echt corpus.

- [ ] **Step 1: Indexeer het volledige corpus**

```bash
docker compose up -d
PYTHONPATH=backend .venv/bin/python -m app.ingest
```

Verwacht: per corpusbestand een regel met chunk-aantallen (orde honderden voor artikelen/overwegingen, 4 voor guidance). Kosten: eenmalig, centen.

- [ ] **Step 2: Stel één losse vraag als rooktest**

```bash
PYTHONPATH=backend .venv/bin/python -c "
from app.db import SessionLocal
from app.rag import service
with SessionLocal() as s:
    r = service.beantwoord(s, 'In welke risicocategorie valt cv-screening met AI?')
    print(r.antwoord)
    print([c.ref for c in r.citaten])"
```

Verwacht: een NL-antwoord met bijlage III/hoog risico en minstens één citaat-ref. Lees het antwoord echt.

- [ ] **Step 3: Draai de eval-suite**

```bash
PYTHONPATH=backend:. .venv/bin/python evals/run_evals.py
```

Verwacht: scorekaart met 10 cases. **Bij falende cases**: eerst per case vaststellen wáár de fout zit (retrieval? grounding? eval zelf?) — lees het opgeslagen antwoord in `evals/results/`. Marker- of ref-aanpassingen in de golden set mogen alleen als de handmatige lezing aantoont dat de *eval* fout zat, niet om het systeem groen te krijgen; systeemfouten zijn bevindingen en mogen (gedocumenteerd) rood blijven staan als de oorzaak buiten deze bouwsteen ligt.

- [ ] **Step 4: "Evalueer je eval" — handmatige steekproef**

Lees in het JSON-resultaat de volledige antwoorden van minimaal: één abstentie-case (weigert hij écht netjes?), de actualiteits-case (klopt de datum-claim inhoudelijk?) en één NL-case. Noteer afwijkingen als bevinding in het commitbericht van Step 6.

- [ ] **Step 5: Start de API als rooktest**

```bash
PYTHONPATH=backend .venv/bin/uvicorn app.main:app --port 8000 &
sleep 2
curl -s localhost:8000/health
curl -s -X POST localhost:8000/ask -H 'content-type: application/json' \
  -d '{"vraag": "Is cv-screening met AI hoog risico?"}' | head -c 600
kill %1
```

Verwacht: `{"status":"ok"}` en een JSON-antwoord met citaten.

- [ ] **Step 6: Schrijf `README.md`**

````markdown
# AiActWijzer

Assistent die vragen over de EU AI Act beantwoordt, gegrond in de NL-wettekst
(verordening 2024/1689, incl. Digital Omnibus) en NL-guidance. Elke claim draagt
een citaat met artikelnummer; elk antwoord een actualiteits-stempel.
Informatie, geen juridisch advies.

## Snelstart

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env          # MISTRAL_API_KEY invullen
docker compose up -d          # Postgres + pgvector (poort 5433)
PYTHONPATH=backend .venv/bin/python -m app.ingest        # corpus indexeren
PYTHONPATH=backend .venv/bin/uvicorn app.main:app        # API op :8000
```

## Evals

```bash
PYTHONPATH=backend:. .venv/bin/python evals/run_evals.py   # golden set (10 cases)
.venv/bin/pytest                                         # unit- en integratietests
```

De eval-suite draait bij elke wijziging aan chunking, prompt of model —
zie `docs/eval-aanpak.md`. Corpusbeheer: `corpus/` is de bron van waarheid,
elke wijziging is een git-diff + eval-run.
````

- [ ] **Step 7: Draai de volledige testsuite nog één keer**

```bash
.venv/bin/pytest
```

Verwacht: alles PASS.

- [ ] **Step 8: Commit** (vermeld de eval-uitslag en eventuele bevindingen uit Step 4 in het bericht)

```bash
git add README.md evals/
git commit -m "End-to-end: corpus geïndexeerd, eval-scorekaart <X>/10, README"
```

---

## Zelfreview (uitgevoerd bij het schrijven)

- **Spec-dekking:** corpusformaat+frontmatter (T9/T10), parser op wetsstructuur (T3), datamodel (T2), ingest idempotent (T6), retrieval top-K (T7), generatie temp 0 + abstentie-prompt (T4/T5), citaten uit database (T5/T7), API met 502 (T8), golden set 10 cases in 5 categorieën incl. `verboden_markers` (T11), runner in-process + JSON-regressiespoor + exit-code (T11), omnibus-datumcontrole (T9 Step 5), "evalueer je eval" (T12 Step 4). Buiten scope-lijst van de spec: niets van dat alles zit in dit plan.
- **Open risico (bewust):** de EUR-Lex-conversie (T9) kan regex-bijstelling vergen; de sanity-checks bakenen dat af.
- **Typeconsistentie:** `ParsedChunk/ParsedDocument/parse_document` (T3) ↔ ingest (T6); `AskResultaat.opgehaalde_refs` (T7) ↔ runner (T11); `MistralFout` (T4) ↔ API (T8); `ref_matcht`-gedrag (T11) ↔ guidance-koppen (T10).
```
