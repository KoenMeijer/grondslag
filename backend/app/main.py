"""FastAPI-laag: dun schilletje om de RAG-service. Geen fallback-antwoorden bij
een modelfout — liever een eerlijke 502 dan een half juridisch antwoord."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field, field_validator

from app import inzendingen
from app.config import settings
from app.db import SessionLocal, init_db
from app.rag import service
from app.rag.mistral import MistralFout
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
    # Bovengrens is een kostenmaatregel: elke vraag wordt geëmbed én meegestuurd
    # in de prompt, dus lengte vertaalt zich direct in tokens. 1000 tekens is
    # ruim voor een situatieschets en te krap voor misbruik.
    vraag: str = Field(min_length=3, max_length=1000)

    @field_validator("vraag")
    @classmethod
    def niet_alleen_witruimte(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("vraag mag niet leeg zijn")
        return v


class CitaatUit(BaseModel):
    ref: str
    fragment: str
    bron: str
    url: str


class AskAntwoord(BaseModel):
    antwoord: str
    citaten: list[CitaatUit]
    stand_van_wetgeving: str
    geen_bron: bool   # de frontend toont hierop de opt-in-inzendknop


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
    if antwoord.geen_bron:
        tel_op("vraag:geen-bron")
        # Subsleutel náást (niet in plaats van) geen-bron, zodat de historische
        # reeks vergelijkbaar blijft. Sterk signaal = de vraag lag binnen het
        # onderwerp (kan een corpusgat, retrieval-misser óf adviesvraag zijn:
        # uitzoeken waard); laag signaal = ander onderwerp, weigering terecht.
        # Grens gekalibreerd op afstandsmeting — zie signaal_grens in config.
        if (antwoord.beste_afstand is not None
                and antwoord.beste_afstand <= settings.signaal_grens):
            tel_op("vraag:geen-bron:sterk-signaal")
    elif not antwoord.citaten:
        tel_op("vraag:zonder-citaat")
    return antwoord


@app.post("/inzending", status_code=204)
def inzending(body: AskVraag) -> Response:
    """Opt-in na een onbeantwoorde vraag: bewaart alléén de vraagtekst (zelfde
    grenzen als /ask), zodat corpusgaten vindbaar worden. Geen IP, geen sessie;
    retentie en dagcap zitten in app/inzendingen.py."""
    if not inzendingen.bewaar(body.vraag.strip()):
        raise HTTPException(status_code=429,
                            detail="Vandaag zijn er al veel inzendingen; probeer het morgen opnieuw.")
    tel_op("inzending")
    return Response(status_code=204)


class Bezoek(BaseModel):
    pad: str


@app.post("/bezoek", status_code=204)
def bezoek(body: Bezoek) -> Response:
    """Telt een paginabezoek. Geen IP, geen cookie, geen user-agent — alleen het
    pad, en alleen als het een bestaande pagina is."""
    if body.pad in PAGINAS:
        tel_op(f"bezoek:{body.pad}")
    return Response(status_code=204)
