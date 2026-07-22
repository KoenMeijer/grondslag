"""Gebruikstellingen: hoeveel bezoeken en hoeveel vragen, per dag.

Bewust minimaal (productprincipe 4): geen IP, geen cookie, geen sessie, geen
vraagtekst. Alleen een teller per (datum, sleutel), zodat je groei kunt zien
zonder ook maar iets over een individuele bezoeker vast te leggen.

Tellen is bijzaak: elke fout wordt gedempt. Een bezoeker hoort nooit een
foutmelding te krijgen omdat de statistiek niet lukte.
"""
import datetime
import logging

from sqlalchemy.dialects.postgresql import insert

from app.db import SessionLocal
from app.models import Dagtelling

logger = logging.getLogger(__name__)


def _schrijf(sleutel: str, datum: str) -> None:
    # Upsert: één rij per dag per sleutel. ON CONFLICT houdt gelijktijdige
    # verzoeken correct — twee bezoekers tegelijk geven +2, geen verloren update.
    stmt = (insert(Dagtelling)
            .values(datum=datum, sleutel=sleutel, aantal=1)
            .on_conflict_do_update(
                constraint="uq_dagtelling",
                set_={"aantal": Dagtelling.__table__.c.aantal + 1}))
    with SessionLocal() as sessie:
        sessie.execute(stmt)
        sessie.commit()


def tel_op(sleutel: str, datum: str | None = None) -> None:
    try:
        _schrijf(sleutel, datum or datetime.datetime.now(datetime.UTC).date().isoformat())
    except Exception:   # noqa: BLE001 — bewust breed: statistiek mag nooit de app breken
        logger.warning("telling %s mislukt", sleutel, exc_info=True)
