"""Half-automatische nieuwsaanvoer voor de pagina "Laatste ontwikkelingen".

Waarom half-automatisch: het model doet alleen het voorwerk (RSS-feeds volgen
en een concept-samenvatting schrijven); publiceren blijft mensenwerk via het
beheerscherm. Juridische precisie is de belofte van deze site, en die geef je
niet uit handen aan een ongecontroleerde samenvatting.

Zelfde patronen als de bronnencheck (app/bronnen.py): httpx met een eigen
user-agent, een fetch-fout is overslaan (geen alarm — de watchdog ziet een
structureel dode feed vanzelf doordat er geen nieuws meer binnenkomt), en de
database als geheugen: de unieke URL is de dedupe, óók voor afgewezen items.
"""
import datetime
import email.utils
import logging
import re
import xml.etree.ElementTree as ET

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select

from app.models import NieuwsItem
from app.rag import mistral

logger = logging.getLogger(__name__)

TIMEOUT = 30
UA = "grondslag-nieuws (+https://grondslag.eu/transparantie)"

# Starterset, geverifieerd (beide leveren RSS 2.0; de AP-feed eist een nette
# user-agent). Het filter beperkt de aanvoer tot AI-onderwerpen — beide feeds
# zijn breder (DSA, AVG, ransomware). Bron toevoegen = regel toevoegen; ruis
# die door het filter glipt wijst de redacteur alsnog af.
FEEDS = [
    {"naam": "Europese Commissie",
     "url": "https://digital-strategy.ec.europa.eu/en/rss.xml",
     "filter": r"\bAI\b|artificial intelligence"},
    {"naam": "Autoriteit Persoonsgegevens",
     "url": "https://www.autoriteitpersoonsgegevens.nl/rss",
     "filter": r"\bAI\b|algoritme|kunstmatige intelligentie"},
]

# Begrenst de allereerste run (die anders de hele feed-historie zou
# samenvatten) én de modelkosten per dag.
MAX_NIEUW_PER_FEED = 5

SAMENVAT_PROMPT = (
    "Je schrijft een concept-nieuwsbericht voor de nieuwspagina van Grondslag, "
    "een Nederlandse site over de AI-verordening (EU AI Act). Vat het "
    "aangeleverde bericht samen in drie tot vier zinnen eenvoudig Nederlands, "
    "voor ondernemers zonder juridische achtergrond. Sluit af met één zin die "
    "begint met 'Voor u betekent dit' over wat dit praktisch betekent. Gebruik "
    "alleen informatie die in de aangeleverde tekst staat; voeg niets toe en "
    "noem geen artikelen of datums die er niet in staan. Een redacteur "
    "controleert en herschrijft dit concept vóór publicatie."
)


def _haal_op(url: str) -> str:
    resp = httpx.get(url, timeout=TIMEOUT, follow_redirects=True,
                     headers={"User-Agent": UA})
    resp.raise_for_status()
    return resp.text


def _parse_datum(pubdate: str | None) -> str:
    try:
        return email.utils.parsedate_to_datetime(pubdate).date().isoformat()
    except Exception:   # noqa: BLE001 — geen of onleesbare datum: vandaag
        return datetime.datetime.now(datetime.UTC).date().isoformat()


def lees_feed(xml_tekst: str) -> list[dict]:
    """RSS 2.0 → [{titel, url, omschrijving, datum}]. Beide startbronnen
    leveren RSS 2.0; Atom-steun kan erbij zodra een bron dat nodig heeft."""
    items = []
    for item in ET.fromstring(xml_tekst).iterfind("./channel/item"):
        url = (item.findtext("link") or "").strip()
        if not url:
            continue
        items.append({
            "titel": (item.findtext("title") or "").strip(),
            "url": url,
            "omschrijving": (item.findtext("description") or "").strip(),
            "datum": _parse_datum(item.findtext("pubDate")),
        })
    return items


def artikeltekst(html: str) -> str:
    tekst = BeautifulSoup(html, "html.parser").get_text(separator=" ")
    # Afkappen begrenst de prompt-kosten; kop en kern staan bij nieuws voorin.
    return re.sub(r"\s+", " ", tekst).strip()[:8000]


def vat_samen(titel: str, tekst: str) -> str:
    return mistral.genereer(SAMENVAT_PROMPT, f"Titel: {titel}\n\n{tekst}").strip()


def verwerk(sessie, feeds: list[dict] | None = None) -> int:
    """Haalt de feeds op en zet nieuwe, bij het filter passende items klaar
    als concept. Geeft het aantal nieuwe concepten terug. Elke fout per feed
    of per item: loggen en doorgaan — nieuws mag de app nooit breken."""
    nieuw = 0
    for feed in (feeds if feeds is not None else FEEDS):
        try:
            items = lees_feed(_haal_op(feed["url"]))
        except Exception:   # noqa: BLE001
            logger.warning("nieuws: feed ophalen mislukt: %s", feed["url"], exc_info=True)
            continue
        per_feed = 0
        for item in items:
            if per_feed >= MAX_NIEUW_PER_FEED:
                break
            if feed.get("filter") and not re.search(
                    feed["filter"], f"{item['titel']} {item['omschrijving']}",
                    re.IGNORECASE):
                continue
            if sessie.scalar(select(NieuwsItem).where(NieuwsItem.url == item["url"])) is not None:
                continue
            try:
                # Samenvatten op de volledige artikeltekst, niet op de vaak
                # ingekorte feed-omschrijving; lukt het ophalen niet, dan is
                # de omschrijving de terugvaloptie.
                try:
                    tekst = artikeltekst(_haal_op(item["url"])) or item["omschrijving"]
                except Exception:   # noqa: BLE001
                    tekst = item["omschrijving"]
                samenvatting = vat_samen(item["titel"], tekst)
            except Exception:   # noqa: BLE001 — modelfout: morgen opnieuw
                logger.warning("nieuws: samenvatten mislukt: %s", item["url"], exc_info=True)
                continue
            sessie.add(NieuwsItem(bron=feed["naam"], url=item["url"],
                                  titel=item["titel"], datum=item["datum"],
                                  samenvatting=samenvatting))
            per_feed += 1
            nieuw += 1
    sessie.commit()
    return nieuw


def gepubliceerd(sessie) -> list[NieuwsItem]:
    return list(sessie.scalars(
        select(NieuwsItem).where(NieuwsItem.status == "gepubliceerd")
        .order_by(NieuwsItem.datum.desc(), NieuwsItem.id.desc())))


def concepten(sessie) -> list[NieuwsItem]:
    return list(sessie.scalars(
        select(NieuwsItem).where(NieuwsItem.status == "concept")
        .order_by(NieuwsItem.datum.desc(), NieuwsItem.id.desc())))
