# Ontwerp — Eerste bouwsteen: corpus indexeren + golden set + grounding-eval

Datum: 2026-07-19 · Status: goedgekeurd in brainstormsessie

## Doel

De eerste oplever uit CLAUDE.md: de NL-wettekst (en geselecteerde NL-guidance)
indexeren, vragen beantwoorden met citaten, en ~10 golden-set-cases met
deterministische eval. Inclusief een dunne FastAPI-laag (`POST /ask`).

## Besluiten (met waarom)

| Keuze | Besluit | Waarom |
| --- | --- | --- |
| Corpustaal | Nederlands (EUR-Lex NL-taalversie) | Gebruikers vragen in het NL; citaten in het citaat-paneel moeten NL zijn |
| Modellaag | Mistral API (EU): `mistral-embed` + `mistral-small-latest` | Kwaliteit zonder lokale hardware-eis, EU-gehost (soevereiniteits-eis); klein generatiemodel eerst — opschalen is een gemeten knop |
| Opslag | Postgres + pgvector (docker compose) | Direct de doelstack; hybride zoeken kan later zonder migratie |
| Corpusscope | Verordening 2024/1689 (NL, incl. bijlagen/overwegingen, stand incl. Digital Omnibus) + 1–3 NL-guidance-bronnen | Alle vijf evalcategorieën echt gedekt, incl. NL-doorwerking |
| Corpusvorm | Gestructureerde markdown in `corpus/` (aanpak B) | Git-diffbaar corpusbeheer (versie/datum per bron, wijziging = commit + eval-run); parser blijft triviaal omdat wij het formaat bepalen |
| Interface | FastAPI direct erbij (`POST /ask`, `GET /health`) | Bouwsteen 2 (frontend) wordt kleiner; eval draait in-process, niet via HTTP |
| Temperatuur | 0 | Reproduceerbare evals; variatie is bij juridische antwoorden onacceptabel |
| TOP_K | 5 (startwaarde) | Les uit eerder project: meer context ≠ beter; K is een meetbare knop |

## Repostructuur

```
AiActWijzer/
├── corpus/
│   ├── verordening-2024-1689/     # NL-wettekst als markdown (gescripte conversie EUR-Lex)
│   └── nl-guidance/               # geselecteerde NL-bronnen, zelfde formaat
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI: POST /ask, GET /health
│   │   ├── config.py              # .env: MISTRAL_API_KEY, DB-url, TOP_K, modelnamen
│   │   ├── db.py, models.py       # SQLAlchemy + pgvector
│   │   ├── ingest/                # markdown-parser → chunks → embeddings → db
│   │   └── rag/                   # retrieval, promptopbouw, Mistral-client
│   └── tests/                     # pytest: parser + eval-scoring
├── evals/
│   ├── golden_set.yaml
│   ├── run_evals.py               # scorekaart; exit ≠ 0 bij falende case
│   └── results/                   # JSON-resultaten met tijdstempel (regressiespoor)
└── docker-compose.yml             # postgres met pgvector
```

## Corpusformaat

Elk markdown-bestand heeft frontmatter: `bron`, `url`, `versie`, `datum-opgehaald`,
`stand-wetgeving`, `type` (wettekst/guidance). Vaste kopstructuur:

- `## Artikel 6 — <kop>` met `### Lid 2` eronder
- `## Bijlage III — <kop>` met `### Punt 4` eronder
- `## Overweging 61`

De omnibus-datumwijzigingen zitten ín de tekst (geconsolideerde stand); de
versie-vermelding staat in de frontmatter. Een latere wetswijziging is een
zichtbare git-diff + eval-run.

## Datamodel

- **sources**: slug, titel, url, versie, datum, type.
- **chunks**: source-id, `ref` (citatie-anker, bv. "Artikel 6, lid 2"), kop, tekst,
  embedding (vector, 1024 dims voor `mistral-embed`).

Hybride keyword-zoeken is bewust een látere knop; het schema staat het toe
zonder migratie-pijn.

## Pijplijn

1. **Ingest** (`python -m app.ingest`): parseert corpus-markdown, chunkt op
   natuurlijke grenzen — één chunk per lid (artikel zonder leden → per artikel),
   per bijlagepunt, per overweging. Chunktekst krijgt de hiërarchie als prefix
   ("Artikel 6, lid 2 (<artikelkop>): …") — de "kop als context"-les. Embedden in
   batches, opslaan. Idempotent: per bron oude chunks weg, dan opnieuw.
2. **Retrieval**: vraag embedden, cosine-similarity in pgvector, top-K.
3. **Generatie**: `mistral-small-latest`, temperatuur 0. Prompt: context-chunks
   elk gelabeld met hun `ref`; antwoord uitsluitend op basis van de context, per
   claim een ref; buiten dekking eerlijk abstineren en bij advies-vragen
   doorverwijzen naar een jurist (productprincipe 2).
4. **API**: `POST /ask` → `{antwoord, citaten: [{ref, fragment, bron}],
   stand_van_wetgeving}`. Citaten zijn de daadwerkelijk opgehaalde chunks waarnaar
   het antwoord verwijst: het model kiest refs, de fragmenten komen uit de
   database — het model kan geen citaat verzinnen. Mistral-fouten → nette 502.

## Eval-suite

Golden set: ~10 cases over vijf categorieën (actualiteit, risicoclassificatie,
rolbepaling, NL-doorwerking, abstentie). Per case:

```yaml
- id: actualiteit-hoog-risico-deadline
  categorie: actualiteit
  vraag: "Wanneer gelden de verplichtingen voor hoog-risico-AI-systemen uit bijlage III?"
  retrieval_refs: ["Artikel 113"]          # minstens één hiervan in de top-K
  grounding_markers: ["2 december 2027"]   # moet in het antwoord staan
  verboden_markers: ["2 augustus 2026"]    # mag niet als geldende deadline verschijnen
  abstentie: false
```

`verboden_markers` is een toevoeging op de drie metrics uit `docs/eval-aanpak.md`:
bij de actualiteits-case is "noemt hij de verouderde datum niet" de halve test.
Abstentie-cases: `abstentie: true` + weiger-markers; markerlijst steekproefsgewijs
handmatig controleren ("evalueer je eval"-les).

Runner: roept de RAG-functies in-process aan (zelfde codepad als de API), scoort
deterministisch op marker-matching, print een scorekaart (per case ✓/✗ per metric
+ totalen) en schrijft JSON met tijdstempel naar `evals/results/` — regressiespoor
én governance-bewijs. Exit-code ≠ 0 bij een falende case.

## Testen

`pytest` op de twee plekken waar een stille fout de eval waardeloos maakt:

- **Parser**: voorbeeld-markdown → verwachte chunks met juiste refs, incl.
  randgevallen (artikel zonder leden, bijlagepunten).
- **Scoringslogica**: marker aanwezig/afwezig, verboden marker, abstentie-detectie.

De RAG-keten zelf wordt door de eval-suite gedekt; niet dubbel unit-testen.

## Randvoorwaarden en risico's

- **EUR-Lex-conversie**: de NL-geconsolideerde versie incl. Digital Omnibus is het
  uitgangspunt. Als EUR-Lex die consolidatie nog niet aanbiedt: basis-verordening
  converteren en de omnibus-wijzigingen handmatig in de markdown doorvoeren, met
  vermelding in de frontmatter. In beide gevallen: steekproef op de kritieke
  artikelen (6, 50, 113, bijlage III) vóór het indexeren.
- **NL-guidance-selectie**: 1–3 bronnen uit de naslag
  (`../persoonlijk/naslag/eu-ai-act-nl.md`), zelfde markdown-formaat.
- **Kosten**: corpus embedden is eenmalig (~duizend chunks, centen); een eval-run
  ~10 generaties — verwaarloosbaar. Evals draaien bij elke wijziging.

## Buiten scope van deze bouwsteen

Frontend/citaat-paneel (bouwsteen 2), hybride zoeken, LLM-judge, intake-beslisboom,
accounts, deploy naar Hetzner.
