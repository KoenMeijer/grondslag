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
    url: str


@dataclass
class AskResultaat:
    antwoord: str
    citaten: list[Citaat]
    stand_van_wetgeving: str
    opgehaalde_refs: list[str]   # voor de retrieval-metric; niet in de API-respons
    beste_afstand: float | None = None   # voor de signaalsplitsing van de teller; niet in de API-respons
    # Abstentiedetectie hoort hier, niet in de client: teller (main) en
    # inzendknop (frontend) beslissen op ditzelfde veld — één bron van waarheid.
    geen_bron: bool = False


def beantwoord(sessie, vraag: str) -> AskResultaat:
    zoek = retrieval.zoek_chunks(sessie, vraag)
    antwoord = mistral.genereer(prompt.SYSTEEMPROMPT,
                                prompt.bouw_vraagprompt(vraag, zoek.chunks))
    citaten = [Citaat(ref=c.ref, fragment=c.tekst, bron=c.source.titel,
                      url=c.source.url)
               for c in prompt.vind_citaten(antwoord, zoek.chunks)]
    # Geen-bron = weigerzin zónder citaten. Een mengvorm (weigerzin gevolgd
    # door een gegrond antwoord mét citaat — gemeten gedrag) ís een antwoord;
    # anders telt de statistiek een vals gat en toont de frontend onterecht
    # de inzendknop naast een inhoudelijk antwoord.
    return AskResultaat(antwoord=antwoord, citaten=citaten,
                        stand_van_wetgeving=settings.stand_van_wetgeving,
                        opgehaalde_refs=[c.ref for c in zoek.chunks],
                        beste_afstand=zoek.beste_afstand,
                        geen_bron=(prompt.ABSTENTIEZIN.lower() in antwoord.lower()
                                   and not citaten))
