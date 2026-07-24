# Grondslag

**Live: [grondslag.eu](https://grondslag.eu)**

Assistent die vragen over de AI-verordening (AI Act) beantwoordt, gegrond in de
Nederlandse wettekst: verordening (EU) 2024/1689 inclusief de Digital
Omnibus-wijzigingen, plus de Nederlandse doorwerking (het UAIV-wetsvoorstel en
guidance). Elke claim draagt een citaat met artikelnummer, elk antwoord een
stempel met de stand van de wetgeving. Informatie, geen juridisch advies.

Zelf gehost op een EU-stack (Mistral voor embeddings en generatie, pgvector voor
de index) — de doelgroep met de meeste AI Act-vragen wil die vragen niet in een
Amerikaanse cloud-chatbot typen. De repo-naam draagt nog de werknaam
*AiActWijzer*; hernoemen van de codebase is een aparte actie.

## Snelstart

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env          # MISTRAL_API_KEY invullen
docker compose up -d          # Postgres + pgvector (poort 5433)
PYTHONPATH=backend .venv/bin/python -m app.ingest        # corpus indexeren
PYTHONPATH=backend .venv/bin/uvicorn app.main:app        # API op :8000
```

Deployment (GitLab CI → Hetzner): zie `docs/deploy.md`.

## Frontend

```bash
cd frontend && npm install
npm run dev            # UI op :3000, praat via /api met de backend op :8000
npm run test           # componenttests (vitest)
npm run lint
```

Ontwerp-tokens en signatuur-element: `docs/design-brief.md`.

## Evals

```bash
PYTHONPATH=backend:. .venv/bin/python evals/run_evals.py # golden set (14 cases)
.venv/bin/pytest                                         # unit- en integratietests
```

De eval-suite draait bij elke wijziging aan chunking, prompt of model —
zie `docs/eval-aanpak.md`. Corpusbeheer: `corpus/` is de bron van waarheid,
elke wijziging is een git-diff + eval-run.

**Bekende stand (2026-07-24, 21 cases): retrieval 10/21, grounding 11/21,
abstentie 21/21.** Een exit-code ≠ 0 op deze stand is dus verwacht.
(Grounding wisselt per run op cases met kapotte retrieval — bekende API-ruis,
zie `docs/eval-aanpak.md`.)

De zeven nieuwe **alledaags**-cases (jip-en-janneke-formuleringen, nulmeting
24 jul: retrieval 2/7, grounding 0/7) zijn de meetlat voor de huidige
verbeterfase: gewone-mensen-taal moet net zo goed werken als jurist-taal.
Abstentie blijft ook op deze vragen 7/7 — hij verzint niets, maar helpt de
vrager nog niet verder.

*Verloop op de oorspronkelijke 10 cases:* 6/6/10 → 8/7/10 via artikel
3-splitsing en hybride zoeken (vector 1.5 : trefwoord 1, RRF — onderbouwing:
`evals/meet_fusie.py`) → 8/9/10 door opname van de primaire NL-brontekst
(`corpus/nl-guidance/uaiv-wetsvoorstel.md`, 77 chunks) plus de gecorrigeerde
wegwijzer. Een tussenstand van 9/9/10 bleek deels memorisatie (golden-vragen
waren letterlijk in eigen guidance gelekt; verwijderd — zie de les in
`docs/eval-aanpak.md`). Twee hardnekkige punten daarin:
`actualiteit-hoogrisico-deadline` en `rol-fria-overheid`, beide semantische
afstand vraag ↔ wetstekst, beide met eerlijke abstentie of een
correct-maar-onvolledig antwoord (nooit de verouderde datum).

*Daarna uitgebreid naar 14 cases (nulmeting NL-doorwerking):* de vier nieuwe
UAIV-cases falen **alle vier** op retrieval. Dat de cijfers dalen betekent niet
dat het systeem slechter werd — we meten nu iets dat de set van 10 niet zag.

Het failure-patroon is bovendien scherper dan verwacht: de NL-vragen krijgen
geen eerlijke abstentie maar een **zelfverzekerd EU-antwoord**. "In welke taal
moet ik documentatie aanleveren?" levert artikel 21 ("een taal die gemakkelijk
te begrijpen is") in plaats van UAIV artikel 3.10 ("Nederlands of Engels");
"kan een toezichthouder een boete opleggen?" levert artikel 100 (boetes voor
EU-instellingen) in plaats van UAIV artikel 3.7. De 77 NL-chunks verliezen het
structureel van 900 EU-chunks die dezelfde begrippen letterlijker gebruiken.

**Bronquotum gemeten en afgevoerd (21 jul 2026, `evals/meet_bronquotum.py`).**
Het idee — 1 à 2 van de vijf top-K-plaatsen reserveren voor de best scorende
NL-chunk — leverde één extra case op (7/12 tegen 6/12) en kost twee van de vijf
plaatsen bij élke vraag. Niet doorgevoerd; `retrieval.py` is ongewijzigd. De
meetbank staat in de repo als onderbouwing, net als `meet_fusie.py`.

Twee lessen uit die meting, beide contra-intuïtief:
- **Kandidatendiepte verhogen maakt het slechter**: 20 → 50 → 100 kandidaten per
  zoekpad gaf 6/12 → 4/12 → 4/12. RRF verwatert; middelmatige chunks uit twee
  paden verdringen een chunk die in één pad hoog staat.
- **Volume was niet de oorzaak, vocabulaire wel.** Bij drie van de vier NL-cases
  stond de doelchunk op rang 56, 92 en 95 — onbereikbaar voor welk quotum ook.
  De vraag zegt "boete" en "uittesten", de wet zegt "bestuurlijke boete ten
  hoogste het bedrag, genoemd in artikel 99, vierde lid" en "AI-testomgeving
  voor regelgeving".

Volgende knop, nu met bewijs onderbouwd: **query-expansie naar wetsvocabulaire**.
Die raakt niet alleen de NL-cases maar ook `actualiteit-hoogrisico-deadline`
(doelrang 24) en `rol-fria-overheid` (rang 23) — dezelfde oorzaak. Daarna pas
een reranker (zwaarder: extra modelaanroep per vraag). TOP_K verhogen blijft
afgeraden: dat maakte grounding eerder aantoonbaar slechter.

**Meetruis:** `nl-toezicht-uaiv` sloeg tussen twee runs om van ✓ naar ✗ bij
identiek corpus, identieke prompt en temperatuur 0 — zelfde retrieval, andere
formulering. Beoordeel een enkele run dus niet als bewijs; kijk naar het patroon
over runs.

## Licentie

Code en documentatie: **MIT** (zie `LICENSE`) — vrij te gebruiken, aan te passen
en te verspreiden, met behoud van de copyrightvermelding en zonder garantie.

Het `corpus/` valt daar buiten: dat zijn overheidspublicaties die onder hun eigen
regime vallen. De verordeningstekst komt van EUR-Lex (© Europese Unie,
hergebruik toegestaan met bronvermelding); het UAIV-wetsvoorstel is een
Nederlandse overheidspublicatie van internetconsultatie.nl. Herkomst, versie en
ophaaldatum staan per bestand in de frontmatter.
