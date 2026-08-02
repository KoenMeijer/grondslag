"""FastAPI-laag: dun schilletje om de RAG-service. Geen fallback-antwoorden bij
een modelfout — liever een eerlijke 502 dan een half juridisch antwoord."""
import asyncio
import datetime
import logging
import secrets
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from app import bronnen, feed, inzendingen, nieuws
from app.config import settings
from app.db import SessionLocal, init_db
from app.rag import service
from app.rag.mistral import MistralFout
from app.tellen import tel_op

logger = logging.getLogger(__name__)


async def _bronnenwacht() -> None:
    """Dagelijkse bronnencheck als achtergrondtaak. Draait per worker (bij
    twee uvicorn-workers dus dubbel) — dat is bewust geaccepteerd: de check is
    idempotent en vier extra fetches per dag kosten niets, terwijl een aparte
    scheduler-container wél beheer kost. Eerste run kort na de start, zodat
    een verse deploy meteen een nulmeting heeft."""
    await asyncio.sleep(120)
    while True:
        try:
            with SessionLocal() as sessie:
                await asyncio.to_thread(bronnen.controleer, sessie)
        except Exception:   # noqa: BLE001 — de wacht mag nooit de app breken
            logger.warning("bronnencheck-run mislukt", exc_info=True)
        await asyncio.sleep(settings.broncheck_interval_uren * 3600)


async def _nieuwswacht() -> None:
    """Dagelijkse nieuwsaanvoer als achtergrondtaak, zelfde patroon (en
    dezelfde bewust geaccepteerde per-worker-duplicatie) als _bronnenwacht:
    verwerk() is idempotent door de unieke URL. Start later dan de
    bronnencheck zodat de twee niet tegelijk naar buiten bellen."""
    await asyncio.sleep(300)
    while True:
        try:
            with SessionLocal() as sessie:
                await asyncio.to_thread(nieuws.verwerk, sessie)
        except Exception:   # noqa: BLE001 — de wacht mag nooit de app breken
            logger.warning("nieuwsaanvoer-run mislukt", exc_info=True)
        await asyncio.sleep(settings.nieuws_interval_uren * 3600)


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
    wachten = [asyncio.create_task(_bronnenwacht()),
               asyncio.create_task(_nieuwswacht())]
    yield
    for wacht in wachten:
        wacht.cancel()


app = FastAPI(title="Grondslag", lifespan=levensduur)

# Witte lijst voor de bezoekteller: alleen bestaande pagina's. Zonder deze lijst
# kan iedereen de tabel volschrijven met verzonnen paden.
PAGINAS = {"/", "/over", "/transparantie", "/nieuws"}


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


@app.get("/bronnen/status")
def bronnen_status() -> JSONResponse:
    """Stand van de dagelijkse bronnencheck. Niet-200 bij een gedetecteerde
    wijziging is bewust: de AI-OS-watchdog ziet alles behalve 200 als alarm,
    dus de melding loopt via de bestaande route zonder extra integratie."""
    with SessionLocal() as sessie:
        stand = bronnen.status(sessie)
    code = 200 if stand["status"] == "ok" else 409
    return JSONResponse(status_code=code, content=stand)


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


class NieuwsUit(BaseModel):
    id: int
    bron: str
    url: str
    titel: str
    datum: str
    samenvatting: str


class NieuwsWijziging(BaseModel):
    # Beide velden optioneel: samenvatting bijwerken en publiceren mag in één
    # aanroep, maar ook los van elkaar.
    samenvatting: str | None = Field(default=None, min_length=3, max_length=2000)
    status: Literal["gepubliceerd", "afgewezen"] | None = None


def _eis_beheer(token: str | None) -> None:
    """Beheer is één redacteur met één geheim token uit .env — bewust geen
    loginsysteem. Zonder geconfigureerd token staat beheer uit (403), en de
    vergelijking is timing-veilig (compare_digest)."""
    if not settings.admin_token:
        raise HTTPException(status_code=403, detail="Beheer is niet geconfigureerd.")
    if not (token and secrets.compare_digest(token, settings.admin_token)):
        raise HTTPException(status_code=401, detail="Ongeldig beheertoken.")


@app.get("/nieuws", response_model=list[NieuwsUit])
def nieuws_lijst():
    """Gepubliceerde nieuwsitems, nieuwste eerst. Alleen wat de redacteur
    expliciet heeft goedgekeurd — concepten zijn hier onzichtbaar."""
    with SessionLocal() as sessie:
        return [NieuwsUit(id=n.id, bron=n.bron, url=n.url, titel=n.titel,
                          datum=n.datum, samenvatting=n.samenvatting)
                for n in nieuws.gepubliceerd(sessie)]


@app.get("/nieuws.xml")
def nieuws_feed():
    """RSS 2.0 van de gepubliceerde nieuwsitems, zodat nieuwsbrieven en
    aggregators de AI-Act-updates automatisch oppikken. Publiek bereikbaar via
    /api/nieuws.xml (zelfde /api-mapping als /api/nieuws)."""
    with SessionLocal() as sessie:
        items = [NieuwsUit(id=n.id, bron=n.bron, url=n.url, titel=n.titel,
                           datum=n.datum, samenvatting=n.samenvatting)
                 for n in nieuws.gepubliceerd(sessie)]
    xml = feed.rss(items, site_url="https://grondslag.eu",
                   feed_url="https://grondslag.eu/api/nieuws.xml")
    return Response(content=xml, media_type="application/rss+xml; charset=utf-8")


@app.get("/nieuws/concepten", response_model=list[NieuwsUit])
def nieuws_concepten(x_admin_token: str | None = Header(default=None)):
    _eis_beheer(x_admin_token)
    with SessionLocal() as sessie:
        return [NieuwsUit(id=n.id, bron=n.bron, url=n.url, titel=n.titel,
                          datum=n.datum, samenvatting=n.samenvatting)
                for n in nieuws.concepten(sessie)]


@app.patch("/nieuws/{item_id}", response_model=NieuwsUit)
def nieuws_bijwerken(item_id: int, body: NieuwsWijziging,
                     x_admin_token: str | None = Header(default=None)):
    """Redactieslag: samenvatting bijwerken en/of publiceren/afwijzen.
    Afgewezen items blijven bestaan (de URL is de dedupe), maar verdwijnen
    uit de conceptenlijst en komen nooit op de site."""
    _eis_beheer(x_admin_token)
    with SessionLocal() as sessie:
        item = sessie.get(nieuws.NieuwsItem, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Onbekend nieuwsitem.")
        if body.samenvatting is not None:
            item.samenvatting = body.samenvatting.strip()
        if body.status is not None:
            item.status = body.status
            if body.status == "gepubliceerd":
                item.gepubliceerd_op = datetime.datetime.now(datetime.UTC).date().isoformat()
        sessie.commit()
        return NieuwsUit(id=item.id, bron=item.bron, url=item.url,
                         titel=item.titel, datum=item.datum,
                         samenvatting=item.samenvatting)
