"""Eenmalige conversie: EUR-Lex NL-tekst van Verordening (EU) 2024/1689 (HTML) → corpus-markdown.

Werkt op de tekststructuur (regels), niet op CSS-klassen: EUR-Lex-markup wisselt
per versie, maar de tekstconventies ("Artikel 6" op een eigen regel) zijn stabiel.
De sanity-checks onderaan falen hard als de structuur afwijkt — dan de regexes
bijstellen, niet de checks.

Bronkeuze (zie task-9-report.md voor de volledige onderbouwing): de "huidige
geconsolideerde versie" op EUR-Lex (02024R1689-20240712) bevat GEEN overwegingen
— EUR-Lex' CONSLEG-tool consolideert alleen de bepalende artikelen, niet de
considerans. Daarom is de oorspronkelijke PB-publicatie (CELEX 32024R1689) als
enige bron gebruikt: die bevat overwegingen + artikelen + bijlagen in één
consistente structuur. Steekproef op art. 6 en art. 50 bevestigt dat de
artikeltekst inhoudelijk identiek is aan de geconsolideerde versie (alleen de
regel-opmaak verschilt); de 2 corrigenda (C1 19-12-2025, C2 4-5-2026) van de
consolidatie zijn niet op elk artikel geverifieerd.

Gebruik: python scripts/converteer_eurlex.py <eurlex.html> <bron-url> <versie-label>
"""
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

# EUR-Lex zet "Artikel", "Lid"-/puntnummers e.d. vaak met non-breaking spaces (\xa0)
# aan elkaar; die worden bij het inlezen genormaliseerd naar gewone spaties, dus
# de regexes hieronder gaan uit van gewone spaties.
ARTIKEL = re.compile(r"^Artikel (\d+)$")
BIJLAGE = re.compile(r"^BIJLAGE ([IVXLC]+)$")
# Genummerde markering aan het begin van een regel; de inhoud staat er soms
# direct achter (artikel-leden: "1.   Een aanbieder ...") en soms op een
# volgende regel (bijlagepunten: "1." gevolgd door een aparte inhoudsregel).
# group(2) kan dus leeg zijn — de volgende regel(s) worden dan als los element
# toegevoegd en komen bij het uiteindelijke parsen alsnog na de kop terecht.
LID = re.compile(r"^(\d+)\.\s*(.*)$")
# Definitie-/wijzigingspunten: "3)" op een eigen regel (art. 3 en art. 108).
# Elk punt wordt een eigen chunk: één 19KB-definitieblok verdunt het
# embeddingsignaal zodanig dat definitievragen artikel 3 niet ophalen
# (eval-gedreven vastgesteld; zie evals/results en docs/rag-aanpak.md).
DEFINITIEPUNT = re.compile(r"^(\d+)\)$")
OVERWEGING = re.compile(r"^\((\d+)\)$")
STRUCTUURKOP = re.compile(r"^(HOOFDSTUK|AFDELING)\b")
EINDE_PREAMBULE = "HEBBEN DE VOLGENDE VERORDENING VASTGESTELD"
EINDE_ARTIKELEN = "Gedaan te"  # ondertekenformule vóór voetnoten + bijlagen


def frontmatter(url: str, versie: str) -> str:
    return f"""---
bron: "Verordening (EU) 2024/1689 (AI-verordening)"
url: {url}
versie: "{versie}"
datum-opgehaald: 2026-07-19
stand-wetgeving: juli 2026
type: wettekst
---

"""


def lees_regels(html_pad: Path) -> list[str]:
    soup = BeautifulSoup(html_pad.read_text(), "html.parser")
    ruw = soup.get_text("\n").splitlines()
    # non-breaking spaces → gewone spatie, en meervoudige spaties (ontstaan uit
    # opeenvolgende \xa0's, bv. "1.\xa0\xa0\xa0tekst") comprimeren tot één spatie.
    regels = [re.sub(r"\s+", " ", r.replace("\xa0", " ")).strip() for r in ruw]
    # EUR-Lex-consolidaties bevatten wijzigingsmarkeringen (▼M1 e.d.) — geen inhoud
    return [r for r in regels if r and not r.startswith("▼")]


def schrijf_overwegingen(regels: list[str], uit: Path, url: str, versie: str) -> int:
    einde = next(i for i, r in enumerate(regels) if EINDE_PREAMBULE in r)
    delen: list[str] = []
    nummer = None
    for r in regels[:einde]:
        if m := OVERWEGING.match(r):
            nummer = m.group(1)
            delen.append(f"\n## Overweging {nummer}")
        elif nummer is not None:
            delen.append(r)
    uit.write_text(frontmatter(url, versie) + "\n".join(delen) + "\n")
    return len([d for d in delen if d.startswith("\n## ")])


def _verwerk_lichaam(regels: list[str], kop_label: str) -> list[str]:
    """Gedeelde logica voor artikelen én bijlagen: kop-detectie, Lid/Punt-nummering,
    en het overslaan van structuurkoppen (HOOFDSTUK/AFDELING + hun titelregel)."""
    delen: list[str] = []
    actief = False
    verwacht_kop = False
    sla_over = False
    for r in regels:
        if sla_over:
            sla_over = False
            continue
        if STRUCTUURKOP.match(r):
            sla_over = True  # de titelregel die op HOOFDSTUK/AFDELING volgt ook overslaan
            continue
        if (m := ARTIKEL.match(r)) or (m := BIJLAGE.match(r)):
            label = f"Artikel {m.group(1)}" if r.startswith("Artikel") else f"Bijlage {m.group(1)}"
            delen.append(f"\n## {label}")
            actief = True
            verwacht_kop = True
        elif verwacht_kop:
            delen[-1] += f" — {r}"
            verwacht_kop = False
        elif actief and (m := DEFINITIEPUNT.match(r)):
            # Altijd "Punt" (juridische verwijzing: "artikel 3, punt 3"),
            # ongeacht het kop_label van de omringende structuur.
            delen.append(f"\n### Punt {m.group(1)}")
        elif actief and (m := LID.match(r)):
            inhoud = m.group(2)
            kop = f"\n### {kop_label} {m.group(1)}"
            delen.append(f"{kop}\n\n{inhoud}" if inhoud else kop)
        elif actief:
            delen.append(r)
    return delen


def schrijf_artikelen(regels: list[str], uit: Path, url: str, versie: str) -> int:
    start = next(i for i, r in enumerate(regels) if EINDE_PREAMBULE in r)
    # Na art. 113 volgen ondertekenformule + ~50 voetnoten vóór de eerste bijlage;
    # die horen niet bij art. 113 en worden hier buiten de scanrange gehouden.
    einde = next(i for i, r in enumerate(regels) if EINDE_ARTIKELEN in r)
    delen = _verwerk_lichaam(regels[start + 1:einde], "Lid")
    uit.write_text(frontmatter(url, versie) + "\n".join(delen) + "\n")
    return len([d for d in delen if d.startswith("\n## ")])


def schrijf_bijlagen(regels: list[str], uit: Path, url: str, versie: str) -> int:
    start = next((i for i, r in enumerate(regels) if BIJLAGE.match(r)), None)
    if start is None:
        raise SystemExit("geen bijlagen gevonden — controleer de HTML")
    delen = _verwerk_lichaam(regels[start:], "Punt")
    uit.write_text(frontmatter(url, versie) + "\n".join(delen) + "\n")
    return len([d for d in delen if d.startswith("\n## ")])


OMNIBUS_VERVANGINGEN = [
    # De omnibus verschuift NIET de algemene toepassingsdatum (2 aug 2026 blijft
    # staan — anders zou bv. art. 50 óók pas eind 2027 lijken te gelden), maar
    # alléén de hoog-risico-verplichtingen. Bijlage I (via art. 6 lid 1, al als
    # uitzondering c aanwezig): 2 aug 2027 → 2 aug 2028. Bijlage III (via art. 6
    # lid 2): had geen eigen uitzondering en krijgt er een nieuwe — uitzondering
    # d), 2 dec 2027 — direct ná c) ingevoegd.
    (
        "artikel 6, lid 1, en de overeenkomstige verplichtingen van deze verordening "
        "van toepassing met ingang van 2 augustus 2027.",
        "artikel 6, lid 1, en de overeenkomstige verplichtingen van deze verordening "
        "van toepassing met ingang van 2 augustus 2028.\n"
        "d)\n"
        "de verplichtingen voor AI-systemen met een hoog risico als bedoeld in "
        "artikel 6, lid 2, en bijlage III van toepassing met ingang van 2 december 2027.",
    ),
]


def pas_omnibus_datums_toe(pad: Path) -> list[str]:
    """Voert in art. 113 de deadlineverschuivingen van de Digital Omnibus on AI
    door (bijlage III: nieuwe uitzondering d, 2 dec 2027; bijlage I: uitzondering
    c, 2 aug 2027 → 2 aug 2028). Elke anker-zin moet exact één keer voorkomen —
    dat borgt dat we niet per ongeluk een andere, niet-omnibus-datum (bv.
    evaluatietermijnen) raken. De overige omnibus-wijzigingen (art. 50-watermerken
    bestaande systemen per 2 dec 2026, nieuwe verbodsbepalingen) hebben geen
    tekstueel anker in deze wettekst en staan daarom — geadministreerd, niet
    verzonnen — in corpus/verordening-2024-1689/digital-omnibus-tijdlijn.md."""
    tekst = pad.read_text()
    toegepast = []
    for oud, nieuw in OMNIBUS_VERVANGINGEN:
        aantal = tekst.count(oud)
        assert aantal == 1, f"verwacht 1 match voor omnibus-anker, kreeg {aantal}: {oud!r}"
        tekst = tekst.replace(oud, nieuw)
        toegepast.append(f"{oud!r} -> {nieuw!r}")
    pad.write_text(tekst)
    return toegepast


def main() -> None:
    html_pad, url, versie = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    regels = lees_regels(html_pad)
    doel = Path("corpus/verordening-2024-1689")
    doel.mkdir(parents=True, exist_ok=True)

    # Alleen artikelen.md wijkt af van de bron (omnibus-datums in art. 113);
    # de versie-administratie moet die afwijking per bestand exact benoemen.
    versie_artikelen = (
        f"{versie}; Digital Omnibus-datums handmatig doorgevoerd in art. 113 "
        "(bijlage III → 2 dec 2027 als nieuwe uitzondering d; bijlage I → "
        "2 aug 2028); bron: Digital Omnibus on AI, jul 2026"
    )

    n_ov = schrijf_overwegingen(regels, doel / "overwegingen.md", url, versie)
    n_art = schrijf_artikelen(regels, doel / "artikelen.md", url, versie_artikelen)
    n_bijl = schrijf_bijlagen(regels, doel / "bijlagen.md", url, versie)
    print(f"overwegingen: {n_ov}, artikelen: {n_art}, bijlagen: {n_bijl}")

    # Sanity-checks: falen hard, want een stil half corpus is erger dan geen corpus
    assert n_art == 113, f"verwacht 113 artikelen, kreeg {n_art}"
    assert n_ov >= 150, f"verwacht ≥150 overwegingen, kreeg {n_ov}"
    # Experiment 1 (retrieval-granulariteit): artikel 3 moet per definitie chunken
    art3 = (Path("corpus/verordening-2024-1689/artikelen.md").read_text()
            .split("## Artikel 3 ")[1].split("## Artikel 4 ")[0])
    n_def = art3.count("### Punt ")
    assert n_def == 68, f"verwacht 68 definitiepunten in art. 3, kreeg {n_def}"
    tekst = (doel / "bijlagen.md").read_text()
    assert "## Bijlage III" in tekst, "bijlage III ontbreekt"

    toegepast = pas_omnibus_datums_toe(doel / "artikelen.md")
    for regel in toegepast:
        print(f"omnibus-datum toegepast: {regel}")


if __name__ == "__main__":
    main()
