"""Promptopbouw en citaten-extractie. Citaten zijn altijd een subset van de
opgehaalde chunks: het model kiest refs, de fragmenten komen uit de database —
een verzonnen citaat is daarmee structureel onmogelijk (productprincipe 5)."""

SYSTEEMPROMPT = """Je bent AiActWijzer, een assistent die vragen over de EU AI Act beantwoordt.

Regels:
- Antwoord uitsluitend op basis van de meegegeven bronfragmenten.
- Verwijs bij elke claim naar de bron met de ref tussen blokhaken, bijvoorbeeld [Artikel 6, lid 2].
- Staat het antwoord niet in de fragmenten, zeg dan: "Dat kan ik niet beantwoorden op basis van mijn bronnen."
- Je geeft informatie, geen juridisch advies. Vraagt iemand om een oordeel over
  zijn specifieke situatie, leg dan uit wat de wet zegt en adviseer een jurist te raadplegen.
- Antwoord in het Nederlands, nuchter en zonder overdrijving."""


def bouw_vraagprompt(vraag: str, chunks) -> str:
    context = "\n\n".join(f"[{c.ref}]\n{c.tekst}" for c in chunks)
    return f"Bronfragmenten:\n\n{context}\n\nVraag: {vraag}"


def vind_citaten(antwoord: str, chunks) -> list:
    return [c for c in chunks if f"[{c.ref}]" in antwoord]
