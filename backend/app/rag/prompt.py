"""Promptopbouw en citaten-extractie. Citaten zijn altijd een subset van de
opgehaalde chunks: het model kiest refs, de fragmenten komen uit de database —
een verzonnen citaat is daarmee structureel onmogelijk (productprincipe 5)."""

import re

# Letterlijk dezelfde zin als in de systeemprompt hieronder. De gebruiksteller
# herkent hieraan dat een vraag onbeantwoord bleef; een test bewaakt dat de twee
# niet uit elkaar lopen. Bewust géén f-string in de prompt: die tekst is
# eval-gevoelig en mag niet per ongeluk van vorm veranderen.
ABSTENTIEZIN = "Dat kan ik niet beantwoorden op basis van mijn bronnen."

SYSTEEMPROMPT = """Je bent AiActWijzer, een assistent die vragen over de EU AI Act beantwoordt.

Regels:
- Antwoord uitsluitend op basis van de meegegeven bronfragmenten.
- Verwijs bij elke claim naar de bron met de ref tussen blokhaken, bijvoorbeeld [Artikel 6, lid 2].
- Neem de ref exact over zoals die boven het fragment staat; voeg niets toe aan de ref.
- Gebruik geen opmaak zoals sterretjes of koppen; schrijf gewone lopende tekst.
- Staat het antwoord niet in de fragmenten, zeg dan: "Dat kan ik niet beantwoorden op basis van mijn bronnen."
- Staat achter een ref "status: concept-wetsvoorstel, nog niet in werking",
  meld dan in je antwoord dat die regel nog geen geldend recht is en nog kan wijzigen.
- Je geeft informatie, geen juridisch advies. Vraagt iemand om een oordeel over
  zijn specifieke situatie, leg dan uit wat de wet zegt en adviseer een jurist te raadplegen.
- Antwoord in het Nederlands, nuchter en zonder overdrijving."""


def bouw_vraagprompt(vraag: str, chunks) -> str:
    context = "\n\n".join(f"[{c.ref}]\n{c.tekst}" for c in chunks)
    return f"Bronfragmenten:\n\n{context}\n\nVraag: {vraag}"


def vind_citaten(antwoord: str, chunks) -> list:
    # Het model mag een ref verfijnen ("…, onder a)"); match daarom op de langste
    # chunk-ref die als prefix in een geciteerde ref past. De garantie blijft:
    # citaten zijn altijd een subset van de opgehaalde chunks.
    geciteerd = re.findall(r"\[([^\]]+)\]", antwoord)
    gekozen = []
    for g in geciteerd:
        passend = [c for c in chunks if g == c.ref or g.startswith(c.ref + ",")]
        if passend:
            beste = max(passend, key=lambda c: len(c.ref))
            if beste not in gekozen:
                gekozen.append(beste)
    # volgorde van de opgehaalde chunks aanhouden, niet de citeer-volgorde
    return [c for c in chunks if c in gekozen]
