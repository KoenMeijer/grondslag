"""Opt-in ingezonden vragen: opslag met afgedwongen retentie en een dagcap.

Waarom dit bestaat: de geen-bron-teller laat zien dát vragen onbeantwoord
blijven, maar bewust niet waarover (geen vraagtekst in de statistiek). Wie na
een weigering zelf op de inzendknop drukt, geeft de vraagtekst expliciet af —
alleen de tekst, niets erbij — zodat corpusgaten vindbaar worden.

Anders dan bij de tellingen wordt een fout hier níét gedempt: de bezoeker heeft
op een knop gedrukt en hoort het te merken als het bewaren mislukt.
"""
import datetime

from sqlalchemy import delete

from app.db import SessionLocal
from app.models import IngezondenVraag

# Retentie hoort bij de belofte op /transparantie — wijzig je die termijn,
# wijzig dan ook de tekst daar. Afgedwongen bij elke inzending, dus zonder
# aparte cron: uiterlijk bij de eerstvolgende inzending is oud materiaal weg.
RETENTIE_DAGEN = 90
# Cap tegen volschrijven van de tabel (zelfde motief als de pagina-witte-lijst
# van de bezoekteller). Ruim boven echt gebruik; een 429 is dan misbruik, geen
# gemiste feedback.
DAGCAP = 200


def bewaar(vraag: str) -> bool:
    """Bewaart de vraagtekst met de datum van vandaag. False als de dagcap
    bereikt is (de opschoning is dan wél gedaan)."""
    vandaag = datetime.datetime.now(datetime.UTC).date()
    grens = (vandaag - datetime.timedelta(days=RETENTIE_DAGEN)).isoformat()
    with SessionLocal() as sessie:
        sessie.execute(delete(IngezondenVraag).where(IngezondenVraag.datum < grens))
        vol = (sessie.query(IngezondenVraag)
               .filter_by(datum=vandaag.isoformat()).count() >= DAGCAP)
        if not vol:
            sessie.add(IngezondenVraag(datum=vandaag.isoformat(), vraag=vraag))
        sessie.commit()
        return not vol
