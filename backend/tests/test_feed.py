"""Feed-opbouw is DB-vrij en dus zonder Docker/Postgres te testen."""
from xml.dom import minidom

from app import feed


class _Regel:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def _voorbeeld():
    return [_Regel(
        id=1, bron="Europese Commissie", url="https://ex.eu/a",
        titel="Digital Omnibus verschuift de hoog-risico-deadline",
        datum="2026-07-19",
        samenvatting="Samenvatting met <tekens> & een ampersand.",
    )]


def test_welgevormde_rss_met_self_link_en_item():
    xml = feed.rss(_voorbeeld(), site_url="https://grondslag.eu",
                   feed_url="https://grondslag.eu/api/nieuws.xml")
    doc = minidom.parseString(xml)  # werpt bij niet-welgevormde XML
    assert doc.getElementsByTagName("rss")
    assert len(doc.getElementsByTagName("item")) == 1
    assert 'href="https://grondslag.eu/api/nieuws.xml"' in xml
    # ISO-datum wordt RFC-822, niet ruw doorgegeven.
    assert "19 Jul 2026" in xml
    assert "<pubDate>" in xml


def test_escapet_bijzondere_tekens():
    xml = feed.rss(_voorbeeld(), site_url="https://grondslag.eu",
                   feed_url="https://grondslag.eu/f.xml")
    assert "&lt;tekens&gt; &amp; een ampersand" in xml
    minidom.parseString(xml)  # blijft welgevormd


def test_ongeldige_datum_laat_pubdate_weg():
    items = [_Regel(id=2, bron="X", url="https://ex/2", titel="Titel",
                    datum="onbekend", samenvatting="S")]
    xml = feed.rss(items, site_url="https://grondslag.eu",
                   feed_url="https://grondslag.eu/f.xml")
    assert "<pubDate>" not in xml
    minidom.parseString(xml)


def test_lege_lijst_blijft_geldig():
    xml = feed.rss([], site_url="https://grondslag.eu",
                   feed_url="https://grondslag.eu/f.xml")
    doc = minidom.parseString(xml)
    assert doc.getElementsByTagName("channel")
    assert not doc.getElementsByTagName("item")
