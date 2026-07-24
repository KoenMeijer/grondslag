"""Dunne wrapper om de Mistral-API. Aparte module zodat tests en evals de API
kunnen vervangen, en een latere modelwissel (een 'gemeten knop') op één plek
gebeurt. Elke API-fout wordt MistralFout: de API-laag vertaalt die naar 502."""
from mistralai.client import Mistral

from app.config import settings


class MistralFout(Exception):
    pass


_client: Mistral | None = None


def _klant() -> Mistral:
    global _client
    if _client is None:
        _client = Mistral(api_key=settings.mistral_api_key)
    return _client


def embed(teksten: list[str]) -> list[list[float]]:
    try:
        resp = _klant().embeddings.create(model=settings.embed_model, inputs=teksten)
    except Exception as e:
        raise MistralFout(str(e)) from e
    return [d.embedding for d in resp.data]


def genereer(systeem: str, vraag: str) -> str:
    try:
        resp = _klant().chat.complete(
            model=settings.chat_model,
            temperature=0,   # juridische antwoorden mogen niet per run variëren
            # Vaste seed: temperatuur 0 alleen bleek via de API niet
            # bit-reproduceerbaar (gemeten, zie docs/eval-aanpak.md); de seed
            # dempt run-ruis zodat eval-verschillen echte effecten zijn.
            random_seed=settings.random_seed,
            messages=[
                {"role": "system", "content": systeem},
                {"role": "user", "content": vraag},
            ],
        )
    except Exception as e:
        raise MistralFout(str(e)) from e
    return resp.choices[0].message.content
