from types import SimpleNamespace

import pytest

from app.rag import mistral


class NepEmbeddings:
    def create(self, model, inputs):
        return SimpleNamespace(data=[SimpleNamespace(embedding=[0.5] * 3) for _ in inputs])


class NepChat:
    def complete(self, model, temperature, messages):
        assert temperature == 0  # reproduceerbaarheid is een harde eis
        return SimpleNamespace(choices=[SimpleNamespace(
            message=SimpleNamespace(content="antwoord"))])


def test_embed_geeft_vector_per_tekst(monkeypatch):
    monkeypatch.setattr(mistral, "_klant",
                        lambda: SimpleNamespace(embeddings=NepEmbeddings()))
    assert mistral.embed(["a", "b"]) == [[0.5] * 3, [0.5] * 3]


def test_genereer_geeft_antwoordtekst(monkeypatch):
    monkeypatch.setattr(mistral, "_klant",
                        lambda: SimpleNamespace(chat=NepChat()))
    assert mistral.genereer("systeem", "vraag") == "antwoord"


def test_api_fout_wordt_mistralfout(monkeypatch):
    def kapot():
        raise RuntimeError("netwerk stuk")
    monkeypatch.setattr(mistral, "_klant", kapot)
    with pytest.raises(mistral.MistralFout):
        mistral.embed(["a"])
