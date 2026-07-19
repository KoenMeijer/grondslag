# Ontwerp — GitLab CI-deployment naar Hetzner

Datum: 2026-07-19 · Status: goedgekeurd in brainstormsessie.
Patroon: hergebruik van WK Poule/Alma (rsync → .env uit CI/CD-variabelen →
`docker compose build + up`; containers op 127.0.0.1, nginx op de host als
TLS/router).

## Nieuwe bestanden

| Bestand | Verantwoordelijkheid |
| --- | --- |
| `backend/Dockerfile` | python:3.12-slim; requirements installeren; entrypoint draait `init_db()` (idempotent) en start uvicorn op 0.0.0.0:8000 met `UVICORN_WORKERS` (default 2) |
| `frontend/Dockerfile` | node:24-alpine multi-stage; `npm ci` + `nuxt build`; runtime draait `.output/server/index.mjs` op 3000 |
| `docker-compose.prod.yml` | Zelfstandig prod-bestand (géén overlay): db (postgres+pgvector, named volume, geen host-poort), backend (127.0.0.1:8094→8000), frontend (127.0.0.1:3094→3000); healthchecks; `DATABASE_URL` opgebouwd naar `@db:5432` |
| `.gitlab-ci.yml` | Fasen `test` (backend-pytest, frontend test+lint) en `deploy` (alleen master, wkpoule-recept) + handmatige job `index_corpus` |
| `docs/deploy.md` | Variabelenoverzicht, eenmalige VPS-stappen (nginx-serverblok met /api-split + certbot), eerste-deploy-runbook |

Het bestaande `docker-compose.yml` blijft ongewijzigd het dev-bestand
(alleen db, poort 5433); de lokale workflow verandert niet.

## Pipeline

1. **test** — `backend-tests`: `pytest` op python:3.12 (db-afhankelijke tests
   skippen netjes zonder Postgres — dat is bestaand fixture-gedrag);
   `frontend-tests`: node:24-alpine, `npm ci`, `npm run test`, `npm run lint`.
   Falen blokkeert de deploy.
2. **deploy** (alleen `master`) — ssh-agent + keyscan, rsync zonder `--delete`
   (excl. .git/.env/node_modules/.venv/.nuxt/.output/__pycache__/.superpowers/
   evals/results), `.env` op de VPS genereren uit CI/CD-variabelen,
   `docker compose -f docker-compose.prod.yml pull + build + up -d
   --remove-orphans`, `docker image prune -f`.
3. **index_corpus** (handmatig, na deploy) — `docker compose exec -T backend
   python -m app.ingest` via SSH. Bewust handmatig: herindexeren kost
   Mistral-embeddingcalls en is alleen nodig bij eerste deploy of
   corpuswijziging.

De eval-suite draait bewust níét in CI: elke run kost geld en de bekende
stand (8/7/10, zie README) geeft verwacht exit ≠ 0. Evals blijven een
lokale, bewuste actie bij RAG-wijzigingen (werkafspraak).

## Routing (same-origin)

De frontend praat relatief met `/api` (zelfde als de dev-proxy). Op de VPS
splitst nginx: `location /api/` → `proxy_pass http://127.0.0.1:8094/`
(prefix wordt gestript door de trailing slash), `location /` →
`http://127.0.0.1:3094`. Serverblok in `docs/deploy.md` met placeholder-domein
`aiactwijzer.example.nl` (nog geen domein gekozen); TLS via certbot zoals bij
de andere projecten.

## CI/CD-variabelen (Settings → CI/CD → Variables)

| Variabele | Type/markering | Toelichting |
| --- | --- | --- |
| `SSH_USER` | Variable | VPS-gebruiker (bij de andere projecten: `koen`) |
| `SSH_HOST` | Variable | VPS-IP of hostnaam |
| `SSH_PRIVATE_KEY` | Variable | Volledige private key incl. BEGIN/END-regels en afsluitende newline |
| `POSTGRES_USER` | Variable | bv. `aiact` |
| `POSTGRES_PASSWORD` | **Masked** | sterk wachtwoord |
| `POSTGRES_DB` | Variable | bv. `aiact` |
| `MISTRAL_API_KEY` | **Masked** | zelfde soort key als lokaal in `.env` |

`DATABASE_URL` wordt niet als variabele gezet maar in compose opgebouwd
(`postgresql+psycopg://$POSTGRES_USER:$POSTGRES_PASSWORD@db:5432/$POSTGRES_DB`).
Poortkeuze 8094/3094 vermijdt conflicten met Alma en WK Poule op dezelfde VPS.

## Verificatie (lokaal, vóór eerste echte deploy)

- `docker compose -f docker-compose.prod.yml config` valideert de compose-syntax.
- `docker build` van beide Dockerfiles slaagt lokaal.
- CI-yml lint (structuur) meegenomen in review; de pipeline zelf kan pas
  draaien zodra het project een GitLab-remote heeft.

## Buiten scope

Domeinkeuze, DNS, daadwerkelijke eerste deploy en het aanmaken van de
GitLab-repo/variabelen (handmatige stappen van de gebruiker, beschreven in
`docs/deploy.md`).
