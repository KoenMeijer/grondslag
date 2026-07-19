from app.db import SessionLocal
from app.models import Chunk, Source
from app.rag import mistral, retrieval


def test_dichtstbijzijnde_chunk_eerst(db, monkeypatch):
    with SessionLocal() as sessie:
        sessie.query(Source).filter_by(slug="test/retrieval").delete()
        bron = Source(slug="test/retrieval", titel="T", url="u", versie="1",
                      datum="2026-07-19", type="wettekst")
        # Twee orthogonale vectoren: de vraagvector wijst exact naar chunk A
        bron.chunks.append(Chunk(ref="A", kop="", tekst="A", volgorde=0,
                                 embedding=[1.0] + [0.0] * 1023))
        bron.chunks.append(Chunk(ref="B", kop="", tekst="B", volgorde=1,
                                 embedding=[0.0, 1.0] + [0.0] * 1022))
        sessie.add(bron)
        sessie.commit()

        monkeypatch.setattr(mistral, "embed", lambda t: [[1.0] + [0.0] * 1023])
        chunks = retrieval.zoek_chunks(sessie, "vraag", top_k=1)
        assert [c.ref for c in chunks] == ["A"]

        sessie.delete(sessie.query(Source).filter_by(slug="test/retrieval").one())
        sessie.commit()
