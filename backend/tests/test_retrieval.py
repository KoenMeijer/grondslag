from sqlalchemy import select

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
        resultaat = retrieval.zoek_chunks(sessie, "vraag", top_k=1)
        assert [c.ref for c in resultaat.chunks] == ["A"]
        # De vraagvector valt exact samen met chunk A, dus de beste
        # cosine-afstand is 0 — dit signaal voedt de sterk/laag-splitsing
        # van de geen-bron-teller.
        assert resultaat.beste_afstand is not None
        assert resultaat.beste_afstand < 0.001

        sessie.delete(sessie.query(Source).filter_by(slug="test/retrieval").one())
        sessie.commit()


def test_rrf_beloont_documenten_die_in_beide_lijsten_staan():
    from app.rag.retrieval import rrf_fuseer
    # id 2 staat in beide rangschikkingen en moet daarom bovenaan eindigen
    assert rrf_fuseer([1, 2, 3], [2, 4])[0] == 2


def test_trefwoord_haalt_chunk_op_die_vector_mist(db, monkeypatch):
    with SessionLocal() as sessie:
        sessie.query(Source).filter_by(slug="test/hybride").delete()
        bron = Source(slug="test/hybride", titel="T", url="u", versie="1",
                      datum="2026-07-19", type="wettekst")
        # Chunk C bevat de letterlijke termen maar heeft een orthogonale vector:
        # zuiver vector-zoeken zou hem missen, het trefwoordpad moet hem vinden.
        # De vraag bevat bewust ook een woord dat nergens voorkomt: bij
        # AND-semantiek zou het trefwoordpad dan leeg zijn (de gemeten no-op).
        bron.chunks.append(Chunk(ref="A", kop="", tekst="iets heel anders", volgorde=0,
                                 embedding=[1.0] + [0.0] * 1023))
        bron.chunks.append(Chunk(ref="B", kop="", tekst="nog een ander onderwerp", volgorde=1,
                                 embedding=[0.8, 0.6] + [0.0] * 1022))
        # Verzonnen termen die alléén in dit testchunk bestaan: ts_rank heeft
        # geen zeldzaamheidsweging, dus met gewone woorden verdringt het echte
        # corpus (zelfde database) het testchunk uit de trefwoord-top — de test
        # moet per constructie corpus-onafhankelijk zijn. "zwiepzwap" komt
        # nergens voor: bij AND-semantiek (de gemeten no-op-bug) zou het
        # trefwoordpad daardoor leeg zijn.
        bron.chunks.append(Chunk(ref="C", kop="", tekst="flarpicon knorvel systemen",
                                 volgorde=2, embedding=[0.0, 0.0, 1.0] + [0.0] * 1021))
        sessie.add(bron)
        sessie.commit()

        monkeypatch.setattr(mistral, "embed", lambda t: [[1.0] + [0.0] * 1023])

        # Preconditie: C moet in de vector-kandidatenlijst zitten — de
        # trefwoordboost alléén haalt de top-2 nooit. Zit C er niet in, dan
        # verdringt het echte corpus (zelfde database) hem en meet deze test
        # niets; dat hoort een duidelijke fout te zijn, geen stille pass/fail.
        kandidaat_ids = list(sessie.scalars(
            select(Chunk.id)
            .order_by(Chunk.embedding.cosine_distance([1.0] + [0.0] * 1023))
            .limit(retrieval.KANDIDATEN)))
        c_id = sessie.query(Chunk).filter_by(ref="C").one().id
        assert c_id in kandidaat_ids, (
            "corpus verdringt testchunk C uit de vector-top-20; "
            "draai de test tegen een lege database of verhoog KANDIDATEN")

        refs = [c.ref for c in retrieval.zoek_chunks(
            sessie, "flarpicon knorvel zwiepzwap", top_k=2).chunks]
        assert "C" in refs

        sessie.delete(sessie.query(Source).filter_by(slug="test/hybride").one())
        sessie.commit()
