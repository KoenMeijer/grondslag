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
PYTHONPATH=backend:. .venv/bin/python evals/run_evals.py # golden set (10 cases)
.venv/bin/pytest                                         # unit- en integratietests
```

De eval-suite draait bij elke wijziging aan chunking, prompt of model —
zie `docs/eval-aanpak.md`. Corpusbeheer: `corpus/` is de bron van waarheid,
elke wijziging is een git-diff + eval-run.

**Bekende stand (2026-07-21, na opname van het UAIV-wetsvoorstel):** retrieval
8/10, grounding 9/10, abstentie 10/10. Was 8/7/10; de twee grounding-winsten
(`nl-toezicht-uaiv`, `rol-fria-overheid`) komen door de primaire NL-brontekst in
het corpus (`corpus/nl-guidance/uaiv-wetsvoorstel.md`, 77 chunks) plus de
gecorrigeerde wegwijzer. Daarvóór: 6/6/10 → 8/7/10 via artikel 3-splitsing en
hybride zoeken (vector 1.5 : trefwoord 1, RRF — onderbouwing:
`evals/meet_fusie.py`). Een tussenstand van 9/9/10 bleek deels memorisatie
(golden-vragen waren letterlijk in eigen guidance gelekt; verwijderd — zie de
les in `docs/eval-aanpak.md`). Twee open punten, beide met eerlijke abstentie of
een correct-maar-onvolledig antwoord (nooit de verouderde datum):
`actualiteit-hoogrisico-deadline` en `rol-fria-overheid` (semantische afstand
vraag ↔ wetstekst; kandidaat-knoppen: query-expansie naar wetsvocabulaire,
reranker). Een exit-code ≠ 0 op deze stand is dus verwacht.

**Waargenomen zwakte, nog niet in de golden set:** bij UAIV-specifieke vragen
haalt retrieval het juiste artikel vaak wél op, maar niet altijd hoog genoeg —
in ad-hoc proeven wisselde het antwoord tussen een correct gegrond antwoord en
een eerlijke abstentie, afhankelijk van welke EU-chunks meekwamen
(lost-in-the-middle, zie `docs/rag-aanpak.md`). Volgende stap: UAIV-cases aan de
golden set toevoegen (formulering nooit letterlijk uit het corpus), dán pas aan
knoppen draaien.
