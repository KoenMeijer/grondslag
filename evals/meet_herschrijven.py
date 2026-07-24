"""Offline meetbank voor query-herschrijving naar wetsvocabulaire.

Aanleiding (24 jul 2026): retrieval staat op 8/14 en de gemeten oorzaak is
vocabulaire — de bezoeker zegt "boete", de wet zegt "bestuurlijke boete ten
hoogste het bedrag, genoemd in artikel 99, vierde lid". Meer kandidaten en een
bronquotum zijn al gemeten en afgevoerd; de aangewezen knop is de vraag zelf
naar wetstermen vertalen vóór het zoeken.

Ronde 1 (generieke herschrijving): vervangen 5/12, extra RRF-pad 6/12,
aanvullen (concat) 7/12 tegen baseline 6/12. Twee lessen: het model strooit
markdown-opmaak door de zoektekst, en het rádt formele termen die de wet net
niet gebruikt ("bestuursrechtelijke sanctie" waar de wet "bestuurlijke boete"
zegt). Ronde 2 meet daarom herschrijven mét de terminologie van het corpus
zelf: de 163 distinct-koppen uit de database als woordenlijst in de prompt.
Dat is corpus-kennis, geen eval-kennis — de lijst komt systematisch uit de
chunks, niet uit de golden set.

Varianten, tegen de baseline, op álle golden-set-cases (een winnaar mag de
slagende cases niet slopen):
  V0  baseline — huidige zoek_chunks
  G   generiek herschreven, samengevoegd met het origineel (winnaar ronde 1)
  T   herschreven mét terminologielijst, samengevoegd met het origineel
  TK  idem, maar alléén in het trefwoordpad — het vectorpad houdt de
      onvervuilde oorspronkelijke vraag

Kosten: één chat-call per case (herschrijving, hergebruikt over varianten) plus
query-embeddings; geen generatie van antwoorden.

De herschrijfprompt is bewust generiek gehouden — geen voorbeelden die één-op-één
uit de golden set komen, anders meet de bank memorisatie van de eval i.p.v.
generalisatie (zelfde les als bij corpus-herformulering, zie eval-aanpak.md).

Gebruik: PYTHONPATH=backend:. .venv/bin/python evals/meet_herschrijven.py
"""
from pathlib import Path

import yaml
from sqlalchemy import Text, cast, func, select

from app.db import SessionLocal
from app.models import Chunk
from app.rag import mistral
from app.rag.retrieval import GEWICHT_VECTOR, KANDIDATEN, rrf_fuseer
from evals import scoring

TOP_K = 5

HERSCHRIJF_SYSTEEM = """\
Je bent een zoekhulp voor de EU AI-verordening (2024/1689) en de Nederlandse
uitvoeringswetgeving. Herschrijf de vraag van een bezoeker naar het formele
vocabulaire van die wetteksten, zodat een zoekmachine de juiste artikelen
vindt: vervang alledaagse woorden door de officiële wetstermen en voeg de
belangrijkste formele termen als trefwoorden toe.
Antwoord met alleen de herschreven zoektekst op één regel, als platte tekst
zonder opmaak en zonder uitleg."""

TERMINOLOGIE_SYSTEEM = """\
Je bent een zoekhulp voor de EU AI-verordening (2024/1689) en de Nederlandse
uitvoeringswetgeving. Herschrijf de vraag van een bezoeker naar het formele
vocabulaire van die wetteksten, zodat een zoekmachine de juiste artikelen
vindt. Gebruik daarbij uitsluitend termen die in de onderstaande lijst met
wetstermen voorkomen waar ze passen bij de vraag, en voeg de best passende
termen uit de lijst toe als trefwoorden.
Antwoord met alleen de herschreven zoektekst op één regel, als platte tekst
zonder opmaak en zonder uitleg.

Wetstermen:
{termen}"""


def herschrijf(vraag: str) -> str:
    return mistral.genereer(HERSCHRIJF_SYSTEEM, vraag).strip()


def herschrijf_met_termen(vraag: str, termen: list[str]) -> str:
    systeem = TERMINOLOGIE_SYSTEEM.format(termen="\n".join(f"- {t}" for t in termen))
    return mistral.genereer(systeem, vraag).strip()


def corpus_termen(sessie) -> list[str]:
    return sorted({k for k in sessie.scalars(select(Chunk.kop).distinct()) if k})


def vector_ids(sessie, tekst: str) -> list[int]:
    vraagvector = mistral.embed([tekst])[0]
    return list(sessie.scalars(
        select(Chunk.id)
        .order_by(Chunk.embedding.cosine_distance(vraagvector))
        .limit(KANDIDATEN)))


def trefwoord_ids(sessie, tekst: str) -> list[int]:
    and_vorm = sessie.scalar(select(cast(func.plainto_tsquery("dutch", tekst), Text)))
    if not and_vorm:
        return []
    tsq = func.to_tsquery("dutch", and_vorm.replace(" & ", " | "))
    tsv = func.to_tsvector("dutch", Chunk.tekst)
    return list(sessie.scalars(
        select(Chunk.id)
        .where(tsv.op("@@")(tsq))
        .order_by(func.ts_rank(tsv, tsq).desc())
        .limit(KANDIDATEN)))


def refs_van(sessie, ids: list[int]) -> list[str]:
    per_id = {c.id: c.ref for c in sessie.scalars(select(Chunk).where(Chunk.id.in_(ids)))}
    return [per_id[i] for i in ids]


def top_refs(sessie, rangschikkingen: list[list[int]], gewichten: list[float]) -> list[str]:
    beste = rrf_fuseer(*rangschikkingen, gewichten=gewichten)[:TOP_K]
    return refs_van(sessie, beste)


def main() -> None:
    cases = yaml.safe_load(Path("evals/golden_set.yaml").read_text())
    cases = [c for c in cases if c["retrieval_refs"]]

    # Ronde 3: terminologielijst afgevoerd (T=6, TK=5 — helpt per saldo niet).
    # G (generiek + samenvoegen) won twee rondes met 7/12 maar breekt telkens
    # rol-aanbieder: de samenvoeging verwatert het vectorpad van een al goed
    # geformuleerde vraag. G2 houdt daarom het oorspronkelijke vectorpad als
    # eigen RRF-pad naast het samengevoegde pad.
    volgorde = ["V0", "G", "G2"]
    telling = dict.fromkeys(volgorde, 0)
    with SessionLocal() as sessie:
        for case in cases:
            vraag = case["vraag"]
            gen = herschrijf(vraag)

            v_orig, t_orig = vector_ids(sessie, vraag), trefwoord_ids(sessie, vraag)
            gen_samen = f"{vraag}\n{gen}"
            v_samen = vector_ids(sessie, gen_samen)
            t_samen = trefwoord_ids(sessie, gen_samen)

            per_variant = {
                "V0": top_refs(sessie, [v_orig, t_orig], [GEWICHT_VECTOR, 1.0]),
                "G": top_refs(sessie, [v_samen, t_samen], [GEWICHT_VECTOR, 1.0]),
                "G2": top_refs(sessie, [v_orig, v_samen, t_samen],
                               [GEWICHT_VECTOR, GEWICHT_VECTOR, 1.0]),
            }
            uitslag = {}
            for naam, refs in per_variant.items():
                raak = scoring.score_retrieval(case["retrieval_refs"], refs)
                telling[naam] += raak
                uitslag[naam] = "✓" if raak else "✗"
            print(f"{case['id']:<36} " + "  ".join(f"{n}:{uitslag[n]}" for n in volgorde))
            print(f"    herschreven: {gen[:105]}")

    print(f"\ntotaal ({len(cases)} cases): " +
          "  ".join(f"{n}={telling[n]}" for n in volgorde))


if __name__ == "__main__":
    main()
