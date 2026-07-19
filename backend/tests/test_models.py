from app.db import SessionLocal
from app.models import Chunk, Source


def test_bron_met_chunk_rondreis(db):
    # Waarom: bewijst dat schema, vector-kolom en cascade werken vóór we ingest bouwen
    with SessionLocal() as sessie:
        sessie.query(Source).filter_by(slug="test/rondreis").delete()
        bron = Source(slug="test/rondreis", titel="Testbron", url="http://x",
                      versie="1", datum="2026-07-19", type="wettekst")
        bron.chunks.append(Chunk(ref="Artikel 1", kop="Onderwerp",
                                 tekst="Artikel 1 (Onderwerp): tekst",
                                 volgorde=0, embedding=[0.1] * 1024))
        sessie.add(bron)
        sessie.commit()

        terug = sessie.query(Source).filter_by(slug="test/rondreis").one()
        assert terug.chunks[0].ref == "Artikel 1"
        assert len(terug.chunks[0].embedding) == 1024

        sessie.delete(terug)   # cascade moet ook de chunk verwijderen
        sessie.commit()
        assert sessie.query(Chunk).filter_by(ref="Artikel 1").count() == 0
