"""Parser voor corpus-markdown: frontmatter + kopstructuur → chunks.

Chunkgrenzen volgen de wetsstructuur (docs/rag-aanpak.md): één chunk per lid,
bijlagepunt of overweging; guidance chunkt per ##-sectie. De hiërarchie gaat
als prefix mee in de chunktekst ("kop als context") — een chunk zonder zijn
artikelaanduiding is ambigu voor retrieval én generatie.
"""
import re
from dataclasses import dataclass

import yaml

_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_H2 = re.compile(r"^## (.+)$")
_H3 = re.compile(r"^### (.+)$")


@dataclass
class ParsedChunk:
    ref: str
    kop: str
    tekst: str


@dataclass
class ParsedDocument:
    meta: dict
    chunks: list[ParsedChunk]


def parse_document(md: str) -> ParsedDocument:
    m = _FRONTMATTER.match(md)
    if not m:
        raise ValueError("corpusbestand mist frontmatter (--- ... ---)")
    meta = yaml.safe_load(m.group(1))
    body = md[m.end():]
    # De prompt ziet alleen ref + chunktekst, geen bron-metadata. Een status als
    # "concept-wetsvoorstel" moet dus in de tekst zelf staan, anders kan het
    # model niet melden dat een bron nog geen geldend recht is.
    stempel = _statusstempel(meta.get("status"))
    if meta.get("type") == "wettekst":
        chunks = _parse_wettekst(body, stempel)
    else:
        chunks = _parse_guidance(body, stempel)
    return ParsedDocument(meta=meta, chunks=chunks)


_STATUSTEKST = {"concept-wetsvoorstel": "concept-wetsvoorstel, nog niet in werking"}


def _statusstempel(status: str | None) -> str:
    # Bewust géén blokhaken: die zijn in de prompt gereserveerd voor refs. Met
    # blokhaken schreef het model "[concept-wetsvoorstel, nog niet in werking]"
    # als citatie-anker, waardoor vind_citaten niets vond en het citaat-paneel
    # leeg bleef.
    if not status:
        return ""
    return f" — status: {_STATUSTEKST.get(status, status)}"


def _splits_kop(titel: str) -> tuple[str, str]:
    # "Artikel 6 — Kop" → anker + kop; "Overweging 61" heeft geen eigen kop
    delen = titel.split(" — ", 1)
    return delen[0].strip(), delen[1].strip() if len(delen) > 1 else ""


def _parse_wettekst(body: str, stempel: str = "") -> list[ParsedChunk]:
    chunks: list[ParsedChunk] = []
    anker = kop = ""
    sub: str | None = None
    regels: list[str] = []

    def sluit_af() -> None:
        tekst = "\n".join(regels).strip()
        regels.clear()
        if not anker or not tekst:
            return
        ref = f"{anker}, {sub}" if sub else anker
        prefix = f"{ref} ({kop}){stempel}: " if kop else f"{ref}{stempel}: "
        chunks.append(ParsedChunk(ref=ref, kop=kop, tekst=prefix + tekst))

    for regel in body.splitlines():
        if m := _H2.match(regel):
            sluit_af()
            anker, kop = _splits_kop(m.group(1))
            sub = None
        elif m := _H3.match(regel):
            sluit_af()
            s = m.group(1).strip()
            # "Lid 2" → "lid 2": de ref moet lezen als een juridische verwijzing
            sub = s[0].lower() + s[1:]
        else:
            regels.append(regel)
    sluit_af()
    return chunks


def _parse_guidance(body: str, stempel: str = "") -> list[ParsedChunk]:
    chunks: list[ParsedChunk] = []
    kop = ""
    regels: list[str] = []

    def sluit_af() -> None:
        tekst = "\n".join(regels).strip()
        regels.clear()
        if not kop or not tekst:
            return
        chunks.append(ParsedChunk(ref=kop, kop=kop, tekst=f"{kop}{stempel}: {tekst}"))

    for regel in body.splitlines():
        if m := _H2.match(regel):
            sluit_af()
            kop = m.group(1).strip()
        else:
            regels.append(regel)
    sluit_af()
    return chunks
