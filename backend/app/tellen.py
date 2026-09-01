"""Gebruikstellingen: hoeveel bezoeken en hoeveel vragen, per dag.

Bewust minimaal (productprincipe 4): geen IP, geen cookie, geen sessie, geen
vraagtekst. Alleen een teller per (datum, sleutel), zodat je groei kunt zien
zonder ook maar iets over een individuele bezoeker vast te leggen.

Tellen is bijzaak: elke fout wordt gedempt. Een bezoeker hoort nooit een
foutmelding te krijgen omdat de statistiek niet lukte.
"""
import datetime
import logging

from sqlalchemy import case, func, select
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


def overzicht(sessie, dagen: int = 30) -> dict:
    """Leest de dagtellers terug voor het beheer-cijferblok: per dag het aantal
    bezoeken (som over alle bezoek:*-paden) en het aantal vragen (de teller
    'vraag'; subtellers als vraag:geen-bron blijven eruit — die zijn een
    verfijning, geen extra vraag). Alleen geaggregeerd: er zit sowieso geen
    persoonsgegeven in de tabel, maar het beheerscherm heeft de losse paden
    niet nodig. `dagen` begrenst het terugkijkvenster (vandaag meegeteld)."""
    vandaag = datetime.datetime.now(datetime.UTC).date()
    vanaf = (vandaag - datetime.timedelta(days=dagen - 1)).isoformat()
    bezoek_som = func.sum(
        case((Dagtelling.sleutel.like("bezoek:%"), Dagtelling.aantal), else_=0))
    vraag_som = func.sum(
        case((Dagtelling.sleutel == "vraag", Dagtelling.aantal), else_=0))
    rijen = sessie.execute(
        select(Dagtelling.datum,
               bezoek_som.label("bezoeken"),
               vraag_som.label("vragen"))
        .where(Dagtelling.datum >= vanaf)
        .group_by(Dagtelling.datum)
        .order_by(Dagtelling.datum.desc())
    ).all()
    # Dagen zonder bezoek én zonder vraag (bv. alleen een inzending) laten we
    # weg: die vertroebelen de tabel zonder iets te zeggen over vindbaarheid.
    reeks = [{"datum": r.datum, "bezoeken": int(r.bezoeken or 0),
              "vragen": int(r.vragen or 0)}
             for r in rijen if (r.bezoeken or 0) or (r.vragen or 0)]
    return {
        "dagen": dagen,
        "reeks": reeks,
        "totaal_bezoeken": sum(r["bezoeken"] for r in reeks),
        "totaal_vragen": sum(r["vragen"] for r in reeks),
    }
