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

## Evals

```bash
PYTHONPATH=backend:. .venv/bin/python evals/run_evals.py # golden set (10 cases)
.venv/bin/pytest                                         # unit- en integratietests
```

De eval-suite draait bij elke wijziging aan chunking, prompt of model —
zie `docs/eval-aanpak.md`. Corpusbeheer: `corpus/` is de bron van waarheid,
elke wijziging is een git-diff + eval-run.

**Bekende stand (baseline 2026-07-19, eerste run):** retrieval 6/10, grounding 6/10,
abstentie 10/10. De rode cases zijn gediagnosticeerd als retrieval-granulariteit
(artikel 3 is één megachunk; de omnibus-tijdlijn-chunks vallen net buiten de top-5)
en staan bewust open als eerstvolgende gemeten experiment — een exit-code ≠ 0 op
deze stand is dus verwacht, geen regressie.
