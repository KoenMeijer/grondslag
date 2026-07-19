"""De RAG-keten: retrieval → generatie → citaten. Eén codepad voor API én
eval-suite, zodat de eval meet wat de gebruiker echt krijgt."""
from dataclasses import dataclass

from app.config import settings
from app.rag import mistral, prompt, retrieval


@dataclass
class Citaat:
    ref: str
    fragment: str
    bron: str


@dataclass
class AskResultaat:
    antwoord: str
    citaten: list[Citaat]
    stand_van_wetgeving: str
    opgehaalde_refs: list[str]   # voor de retrieval-metric; niet in de API-respons


def beantwoord(sessie, vraag: str) -> AskResultaat:
    chunks = retrieval.zoek_chunks(sessie, vraag)
    antwoord = mistral.genereer(prompt.SYSTEEMPROMPT,
                                prompt.bouw_vraagprompt(vraag, chunks))
    citaten = [Citaat(ref=c.ref, fragment=c.tekst, bron=c.source.titel)
               for c in prompt.vind_citaten(antwoord, chunks)]
    return AskResultaat(antwoord=antwoord, citaten=citaten,
                        stand_van_wetgeving=settings.stand_van_wetgeving,
                        opgehaalde_refs=[c.ref for c in chunks])
