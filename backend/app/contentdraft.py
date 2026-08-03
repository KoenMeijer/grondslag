"""Pure, DB-vrije bouwstenen voor het scaffolding-script (scripts/draft_vragen.py).

Gescheiden van het script zodat de renderer/slug/idempotentie testbaar zijn zonder
DB of Mistral-aanroep — zelfde patroon als app/feed.py. Het script publiceert
nooit; het schrijft concepten die een mens redigeert en handmatig publiceert.
"""
from __future__ import annotations

import re


def slug(vraag: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", vraag.strip().lower())
    return s.strip("-")


def bestaat_al(slug: str, gepubliceerd: set[str], concepten: set[str]) -> bool:
    """Idempotent: sla over als de vraag al gepubliceerd of al gedraft is."""
    return slug in gepubliceerd or slug in concepten


def corpusgat_regel(vraag: str, bijgewerkt: str) -> str:
    """Eén regel voor het corpusgaten-rapport (geen_bron-vragen — niet publiceren)."""
    return f"- {bijgewerkt} — {vraag}"


def render_concept(*, vraag: str, artikel: str, stand: str, bijgewerkt: str,
                   sector: str | None, antwoord: str, citaten) -> str:
    """Render een concept-vraagpagina: frontmatter (zoals content/vragen/*.md) +
    het gedrafte antwoord + een reviewer-notitie met de citaten. De redacteur
    controleert/knipt de notitie vóór publicatie."""
    fm = [
        "---",
        f'vraag: "{vraag}"',
        f'artikel: "{artikel}"',
        f'stand-wetgeving: "{stand}"',
        f'bijgewerkt: "{bijgewerkt}"',
    ]
    if sector:
        fm.append(f"sector: {sector}")
    fm.append("---")

    notitie = ["", "<!-- REVIEW — verwijder dit blok vóór publicatie.",
               "Concept via de eigen RAG-engine; controleer tegen de wettekst.",
               "Citaten:"]
    for c in citaten:
        notitie.append(f"- {getattr(c, 'ref', '')} — {getattr(c, 'url', '')}")
    notitie.append("-->")

    return "\n".join(fm) + "\n\n" + antwoord.strip() + "\n" + "\n".join(notitie) + "\n"
