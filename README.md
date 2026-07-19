# AiActWijzer

Assistent die vragen over de EU AI Act beantwoordt, gegrond in de NL-wettekst
(verordening 2024/1689, incl. Digital Omnibus) en NL-guidance. Elke claim draagt
een citaat met artikelnummer; elk antwoord een actualiteits-stempel.
Informatie, geen juridisch advies.

## Snelstart

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env          # MISTRAL_API_KEY invullen
docker compose up -d          # Postgres + pgvector (poort 5433)
PYTHONPATH=backend .venv/bin/python -m app.ingest        # corpus indexeren
PYTHONPATH=backend .venv/bin/uvicorn app.main:app        # API op :8000
```

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
PYTHONPATH=backend:. .venv/bin/python evals/run_evals.py # golden set (10 cases)
.venv/bin/pytest                                         # unit- en integratietests
```

De eval-suite draait bij elke wijziging aan chunking, prompt of model —
zie `docs/eval-aanpak.md`. Corpusbeheer: `corpus/` is de bron van waarheid,
elke wijziging is een git-diff + eval-run.

**Bekende stand (2026-07-19, na retrieval-experimenten 1–3):** retrieval 9/10,
grounding 9/10, abstentie 10/10. Was 6/6/10; verbeterd via artikel 3-splitsing,
hybride zoeken (vector 1.5 : trefwoord 1, RRF) en vraaggerichte herformulering
van de eigen guidance-bestanden. Twee bewust open punten: `rol-fria-overheid`
(artikel 27 wordt niet opgehaald — semantische afstand; kandidaat-knoppen:
query-expansie of reranker) en `nl-toezicht-uaiv` (generatie noemt wisselend
"Uitvoeringswet" óf de toezichthouders, zelden beide — generatie-onvolledigheid,
geen retrieval-fout). Een exit-code ≠ 0 op deze stand is dus verwacht.
