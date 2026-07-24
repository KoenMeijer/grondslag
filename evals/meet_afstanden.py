"""Kalibratiemeting voor `signaal_grens`: welke cosine-afstand scheidt
"er wás iets relevants" van "vraag valt buiten het corpus"?

Aanleiding (24 jul 2026): ~38% van de productievragen eindigt in geen-bron,
maar die teller gooit terechte abstenties en retrieval-missers op één hoop.
De splitsing (vraag:geen-bron:sterk-signaal) heeft een gemeten grens nodig,
geen gegokte. Deze bank meet de beste vectorafstand voor alle golden-set-vragen
(in-corpus én abstentie-cases) plus een reeks bewust buiten-scope-vragen —
alleen query-embeddings, geen generatiekosten.

Gebruik: PYTHONPATH=backend:. .venv/bin/python evals/meet_afstanden.py
"""
from pathlib import Path

import yaml

from app.db import SessionLocal
from app.rag import retrieval

# Vragen die een echte bezoeker zou stellen maar die níét in het corpus horen:
# ander rechtsgebied, advieswerk of volslagen off-topic. Hier hoort de tool te
# weigeren — de gemeten afstand laat zien hoe "ver weg" zulke vragen zitten.
BUITEN_SCOPE = [
    "Mag ik onder de AVG klantgegevens gebruiken om een mailinglijst te bouwen?",
    "Schrijf een DPIA voor mijn nieuwe HR-systeem.",
    "Welke cookiemelding moet ik op mijn website zetten?",
    "Valt mijn webshop onder de NIS2-richtlijn?",
    "Hoeveel mag de huur van een woning in 2026 maximaal stijgen?",
    "Wat is een goed recept voor lasagne?",
]


def main() -> None:
    cases = yaml.safe_load(Path("evals/golden_set.yaml").read_text())
    metingen = []   # (afstand, label, id)
    with SessionLocal() as sessie:
        for case in cases:
            afstand = retrieval.zoek_chunks(sessie, case["vraag"]).beste_afstand
            label = "abstentie" if case["abstentie"] else "in-corpus"
            metingen.append((afstand, label, case["id"]))
        for vraag in BUITEN_SCOPE:
            afstand = retrieval.zoek_chunks(sessie, vraag).beste_afstand
            metingen.append((afstand, "buiten-scope", vraag[:48]))

    print(f"{'afstand':>8}  {'soort':<12} case")
    for afstand, label, naam in sorted(metingen):
        print(f"{afstand:>8.4f}  {label:<12} {naam}")

    in_corpus = [a for a, label, _ in metingen if label == "in-corpus"]
    buiten = [a for a, label, _ in metingen if label != "in-corpus"]
    print(f"\nin-corpus: max {max(in_corpus):.4f} · "
          f"buiten corpus (abstentie + buiten-scope): min {min(buiten):.4f}")
    print("Kies signaal_grens tussen die twee waarden in (marge naar beide kanten);"
          "\noverlappen ze, dan is afstand alléén geen zuivere scheider — meld dat eerlijk.")


if __name__ == "__main__":
    main()
