"""RSS 2.0-feed voor de nieuwspagina. Pure opbouw, DB-vrij: zo blijft de
endpoint dun en is de XML zonder database te testen — zelfde stijl als de rest
(berekening los van I/O). Waarom een feed: nieuwsbrieven en aggregators pikken
de AI-Act-updates dan automatisch op, wat Grondslag een bron voor anderen maakt.
"""
from __future__ import annotations

import datetime
from email.utils import format_datetime
from typing import Iterable, Protocol
from xml.sax.saxutils import escape


class NieuwsRegel(Protocol):
    """Duck-type: alles met deze velden (o.a. NieuwsUit) past."""
    id: int
    bron: str
    url: str
    titel: str
    datum: str
    samenvatting: str


def _rfc822(datum: str) -> str | None:
    """De opgeslagen datum is een ISO-string van de bron; RSS wil RFC-822.
    Lukt het parsen niet, dan liever géén pubDate dan een ongeldige."""
    try:
        d = datetime.date.fromisoformat(datum[:10])
    except (ValueError, TypeError):
        return None
    dt = datetime.datetime(d.year, d.month, d.day, tzinfo=datetime.timezone.utc)
    return format_datetime(dt)


def rss(items: Iterable[NieuwsRegel], *, site_url: str, feed_url: str) -> str:
    """Bouw een RSS 2.0-document van de gepubliceerde nieuwsitems. Elk item
    linkt naar de oorspronkelijke bron (dat is de waarde voor een lezer); de
    guid is stabiel en losgekoppeld van die link."""
    r = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        '  <channel>',
        '    <title>Grondslag — Laatste ontwikkelingen</title>',
        f'    <link>{escape(site_url)}/nieuws</link>',
        f'    <atom:link href="{escape(feed_url)}" rel="self" type="application/rss+xml"/>',
        '    <description>Ontwikkelingen rond de AI-verordening (AI Act), door de '
        'redactie geselecteerd en in gewone taal samengevat.</description>',
        '    <language>nl</language>',
    ]
    for n in items:
        r.append('    <item>')
        r.append(f'      <title>{escape(n.titel)}</title>')
        r.append(f'      <link>{escape(n.url)}</link>')
        r.append(f'      <guid isPermaLink="false">grondslag-nieuws-{n.id}</guid>')
        r.append(f'      <category>{escape(n.bron)}</category>')
        pub = _rfc822(n.datum)
        if pub:
            r.append(f'      <pubDate>{pub}</pubDate>')
        r.append(f'      <description>{escape(n.samenvatting)}</description>')
        r.append('    </item>')
    r.append('  </channel>')
    r.append('</rss>')
    return '\n'.join(r) + '\n'
