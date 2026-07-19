"""Deterministische scoring: marker-matching, geen LLM-judge (docs/eval-aanpak.md).
Reproduceerbaar en gratis; nuance kan later met een judge als de set groeit."""
import re


def ref_matcht(verwacht: str, ref: str) -> bool:
    # Woordgrens-check: "Artikel 6" matcht "Artikel 6, lid 2" maar niet "Artikel 60"
    return re.search(rf"(?<!\w){re.escape(verwacht)}(?!\w)", ref, re.IGNORECASE) is not None


def score_retrieval(verwachte_refs: list[str], opgehaalde_refs: list[str]) -> bool:
    if not verwachte_refs:
        return True   # abstentie-cases stellen geen retrieval-eis
    return any(ref_matcht(v, ref) for v in verwachte_refs for ref in opgehaalde_refs)


def score_grounding(markers: list[str], verboden: list[str], antwoord: str) -> bool:
    laag = antwoord.lower()
    return (all(m.lower() in laag for m in markers)
            and not any(v.lower() in laag for v in verboden))


# Steekproefsgewijs handmatig blijven controleren: een geldige weigering die hier
# niet in staat is een false negative van de eval, niet van het systeem.
WEIGER_MARKERS = [
    "kan ik niet beantwoorden",
    "niet in mijn bronnen",
    "raadpleeg een jurist",
    "jurist te raadplegen",
]


def score_abstentie(moet_abstineren: bool, antwoord: str) -> bool:
    if not moet_abstineren:
        return True   # n.v.t.; een onterecht weigerend antwoord zakt op grounding
    laag = antwoord.lower()
    return any(m in laag for m in WEIGER_MARKERS)
