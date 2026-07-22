"""FastAPI-laag: dun schilletje om de RAG-service. Geen fallback-antwoorden bij
een modelfout — liever een eerlijke 502 dan een half juridisch antwoord."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

from app.db import SessionLocal, init_db
from app.rag import service
from app.rag.mistral import MistralFout
from app.rag.prompt import ABSTENTIEZIN
from app.tellen import tel_op

logger = logging.getLogger(__name__)


@asynccontextmanager
async def levensduur(app: FastAPI):
    # Ontbrekende tabellen aanmaken bij het opstarten (create_all is idempotent
    # en raakt bestaande tabellen niet). Zonder dit zou een nieuwe tabel pas
    # ontstaan bij een corpus-herindexering — en die kost embeddingcalls.
    # Faalt de database, dan start de app alsnog: /health blijft antwoorden en
    # de fout is zichtbaar in de log, in plaats van een crash-loop bij koude start.
    try:
        init_db()
    except Exception:   # noqa: BLE001
        logger.warning("init_db bij opstarten mislukt", exc_info=True)
    yield


app = FastAPI(title="Grondslag", lifespan=levensduur)

# Witte lijst voor de bezoekteller: alleen bestaande pagina's. Zonder deze lijst
# kan iedereen de tabel volschrijven met verzonnen paden.
PAGINAS = {"/", "/over", "/transparantie"}


class AskVraag(BaseModel):
    vraag: str


class CitaatUit(BaseModel):
    ref: str
    fragment: str
    bron: str
    url: str


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
            antwoord = service.beantwoord(sessie, body.vraag)
        except MistralFout as e:
            tel_op("vraag:fout")
            raise HTTPException(status_code=502, detail=f"Modelaanroep mislukt: {e}")
    # Alleen dát er gevraagd is, nooit wát. De drie uitkomsten worden apart
    # geteld omdat ze om verschillende actie vragen: een modelfout is infra,
    # een abstentie een gat in het corpus, en een antwoord zonder citaat een
    # kwaliteitsrisico (ongegrond, terwijl grounding de belofte is).
    tel_op("vraag")
    if ABSTENTIEZIN.lower() in antwoord.antwoord.lower():
        tel_op("vraag:geen-bron")
    elif not antwoord.citaten:
        tel_op("vraag:zonder-citaat")
    return antwoord


class Bezoek(BaseModel):
    pad: str


@app.post("/bezoek", status_code=204)
def bezoek(body: Bezoek) -> Response:
    """Telt een paginabezoek. Geen IP, geen cookie, geen user-agent — alleen het
    pad, en alleen als het een bestaande pagina is."""
    if body.pad in PAGINAS:
        tel_op(f"bezoek:{body.pad}")
    return Response(status_code=204)
