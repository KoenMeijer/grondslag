"""Indexeert het corpus: markdown → chunks → embeddings → database.

Idempotent per bron: bestaande chunks van dezelfde slug gaan eerst weg (cascade),
zodat een herindexering nooit een halve stand achterlaat. De hele run is één
transactie: bij een fout blijft de oude index intact.
"""
import sys
from pathlib import Path

from sqlalchemy import select

from app import bronnen
from app.db import SessionLocal, init_db
from app.ingest.parser import parse_document
from app.models import Chunk, Source
from app.rag import mistral

BATCH = 64  # embed-batchgrootte; ruim onder de API-limiet


def indexeer_bestand(sessie, pad: Path, corpus_root: Path, embed=mistral.embed) -> int:
    doc = parse_document(pad.read_text())
    slug = str(pad.relative_to(corpus_root).with_suffix(""))

    bestaande = sessie.scalar(select(Source).where(Source.slug == slug))
    if bestaande is not None:
        sessie.delete(bestaande)
        sessie.flush()

    bron = Source(slug=slug, titel=doc.meta["bron"], url=str(doc.meta["url"]),
                  versie=str(doc.meta["versie"]), datum=str(doc.meta["datum-opgehaald"]),
                  type=doc.meta["type"])
    sessie.add(bron)

    teksten = [c.tekst for c in doc.chunks]
    vectoren: list[list[float]] = []
    for i in range(0, len(teksten), BATCH):
        vectoren.extend(embed(teksten[i:i + BATCH]))

    for volgorde, (chunk, vector) in enumerate(zip(doc.chunks, vectoren, strict=True)):
        sessie.add(Chunk(source=bron, ref=chunk.ref, kop=chunk.kop,
                         tekst=chunk.tekst, volgorde=volgorde, embedding=vector))
    return len(doc.chunks)


def main() -> None:
    corpus_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("corpus")
    init_db()
    with SessionLocal() as sessie:
        for pad in sorted(corpus_root.rglob("*.md")):
            n = indexeer_bestand(sessie, pad, corpus_root)
            print(f"{pad}: {n} chunks")
        # Nieuwe corpusversie = nieuwe nulmeting voor de bronnencheck: de
        # eerstvolgende dagcheck legt verse vingerafdrukken vast en een
        # openstaand bronnen-alarm dooft — het corpus is immers net bijgewerkt.
        bronnen.reset(sessie)
        sessie.commit()


if __name__ == "__main__":
    main()
