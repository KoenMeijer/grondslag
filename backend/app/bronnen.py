"""Dagelijkse bronnencheck: verandert een bron-pagina, dan hoort het corpus
bijgewerkt te worden.

Waarom dit bestaat: de kast vult zichzelf bewust níét (een corpuswijziging is
een gecontroleerde stap: bron bijwerken → herindexeren → eval-run), maar hij
mag ook niet stil verouderen — de actualiteitsbelofte is het kernonderscheid
van deze tool. Dit proces detecteert dus alleen en alarmeert; het wijzigt
nooit zelf het corpus.

De vingerafdruk hasht de zichtbare tekst (opmaak en witruimte genormaliseerd),
zodat cosmetische HTML-wijzigingen geen vals alarm geven. Een gezette
alarmvlag blijft staan tot de herindexering (reset) — geen stil zelfherstel,
zelfde guardrail-principe als de AI-OS-watchdog.
"""
import datetime
import hashlib
import logging
import re

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import delete, select

from app.models import Broncheck, Source

logger = logging.getLogger(__name__)

TIMEOUT = 30
UA = "grondslag-bronnencheck (+https://grondslag.eu/transparantie)"


def _haal_op(url: str) -> str:
    resp = httpx.get(url, timeout=TIMEOUT, follow_redirects=True,
                     headers={"User-Agent": UA})
    resp.raise_for_status()
    return resp.text


def vingerafdruk(html: str) -> str:
    tekst = BeautifulSoup(html, "html.parser").get_text(separator=" ")
    genormaliseerd = re.sub(r"\s+", " ", tekst).strip()
    return hashlib.sha256(genormaliseerd.encode()).hexdigest()


def bron_urls(sessie) -> list[str]:
    return sorted(set(sessie.scalars(select(Source.url))))


def controleer(sessie, urls: list[str] | None = None) -> None:
    """Vergelijkt elke bron-URL met de vastgelegde nulmeting. Eerste keer =
    nulmeting vastleggen; daarna zet een afwijking gewijzigd_sinds (en die
    blijft staan). Een fetch-fout verandert de stand niet: onbereikbaar is
    geen wijziging, en de watchdog ziet een structureel dode site zelf al."""
    vandaag = datetime.datetime.now(datetime.UTC).date().isoformat()
    for url in (urls if urls is not None else bron_urls(sessie)):
        try:
            afdruk = vingerafdruk(_haal_op(url))
        except Exception:   # noqa: BLE001 — elke faalwijze: loggen en doorgaan
            logger.warning("bronnencheck: ophalen mislukt voor %s", url, exc_info=True)
            continue
        rij = sessie.scalar(select(Broncheck).where(Broncheck.url == url))
        if rij is None:
            sessie.add(Broncheck(url=url, vingerafdruk=afdruk,
                                 laatst_gecontroleerd=vandaag))
        else:
            if rij.vingerafdruk != afdruk and rij.gewijzigd_sinds is None:
                rij.gewijzigd_sinds = vandaag
                logger.warning("bronnencheck: wijziging gedetecteerd op %s", url)
            rij.laatst_gecontroleerd = vandaag
    sessie.commit()


def status(sessie) -> dict:
    rijen = list(sessie.scalars(select(Broncheck)))
    gewijzigd = sorted(r.url for r in rijen if r.gewijzigd_sinds)
    return {
        "status": "bronnen-gewijzigd" if gewijzigd else "ok",
        "gewijzigd": gewijzigd,
        "laatst_gecontroleerd": max((r.laatst_gecontroleerd for r in rijen),
                                    default=None),
    }


def reset(sessie) -> None:
    """Nieuwe corpusversie = nieuwe nulmeting: de eerstvolgende dagcheck legt
    verse vingerafdrukken vast. Aangeroepen door de herindexering."""
    sessie.execute(delete(Broncheck))
