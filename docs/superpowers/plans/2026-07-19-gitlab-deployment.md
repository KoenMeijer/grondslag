# GitLab-deployment — Implementatieplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploybare AiActWijzer via GitLab CI naar Hetzner: Dockerfiles, prod-compose, pipeline en variabelen-/VPS-documentatie.

**Architecture:** WK Poule-patroon — CI test, rsync't de repo naar de VPS, genereert `.env` uit CI/CD-variabelen en draait `docker compose -f docker-compose.prod.yml build + up`. Containers binden op 127.0.0.1 (8094/3094); nginx op de host doet TLS en de `/api`-split. Corpus wordt read-only in de backend-container gemount; indexeren is een handmatige CI-job.

**Tech Stack:** Docker (python:3.12-slim, node:24-alpine, pgvector/pgvector:pg16) · GitLab CI · rsync/ssh · nginx + certbot (host).

Spec: `docs/superpowers/specs/2026-07-19-gitlab-deployment-design.md`.

## Global Constraints

- Bestaand `docker-compose.yml` (dev, db op 5433) blijft ongewijzigd.
- Poorten prod: backend `127.0.0.1:8094`, frontend `127.0.0.1:3094` (geen conflict met Alma/WK Poule).
- CI/CD-variabelen exact: `SSH_USER`, `SSH_HOST`, `SSH_PRIVATE_KEY`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `MISTRAL_API_KEY` — niets meer.
- Eval-suite bewust NIET in CI; corpus-indexering alleen als handmatige job.
- rsync zonder `--delete`; `.env` nooit in de repo.
- Taal: comments/commits Nederlands, *waarom*; commits eindigen op `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- Placeholder-domein in documentatie: `aiactwijzer.example.nl`.

---

### Task 1: Dockerfiles + dockerignore

**Files:**
- Create: `backend/Dockerfile`, `frontend/Dockerfile`, `.dockerignore`, `frontend/.dockerignore`

**Interfaces:**
- Produces: backend-image (uvicorn op 8000, `UVICORN_WORKERS` env, entrypoint draait eerst `init_db()`); frontend-image (Nitro op 3000). Task 2 verwijst naar deze builds.

- [ ] **Step 1: Schrijf `backend/Dockerfile`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app

EXPOSE 8000

# init_db is idempotent (CREATE EXTENSION/TABLE IF NOT EXISTS): bij de eerste
# start bestaan de tabellen nog niet, en /ask zou dan 500 geven.
CMD ["sh", "-c", "python -c 'from app.db import init_db; init_db()' && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-2}"]
```

- [ ] **Step 2: Schrijf `.dockerignore`** (repo-root; backend-context is `.`)

```
.git
.venv
.env
.superpowers
.pytest_cache
__pycache__
frontend/node_modules
frontend/.nuxt
frontend/.output
evals/results
docs
```

- [ ] **Step 3: Schrijf `frontend/Dockerfile`** (context: `./frontend`)

```dockerfile
# Buildfase: volledige toolchain; runtime krijgt alleen de Nitro-output.
FROM node:24-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:24-alpine

WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/.output ./.output

EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
```

- [ ] **Step 4: Schrijf `frontend/.dockerignore`**

```
node_modules
.nuxt
.output
```

- [ ] **Step 5: Valideer beide builds lokaal**

```bash
docker build -f backend/Dockerfile -t aiact-backend-test . && \
docker build -t aiact-frontend-test frontend/
```

Verwacht: beide builds eindigen zonder fout. Rooktest entrypoint-shellsyntax:
`docker run --rm aiact-backend-test sh -c 'echo ok'` → `ok`.

- [ ] **Step 6: Commit**

```bash
git add backend/Dockerfile frontend/Dockerfile .dockerignore frontend/.dockerignore
git commit -m "Dockerfiles: backend (init_db + uvicorn) en frontend (Nitro), met dockerignores"
```

---

### Task 2: docker-compose.prod.yml

**Files:**
- Create: `docker-compose.prod.yml`

**Interfaces:**
- Consumes: de twee Dockerfiles uit Task 1.
- Produces: services `db`/`backend`/`frontend`, volume `aiact_pg_data`; `.env`-contract: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `MISTRAL_API_KEY`, optioneel `UVICORN_WORKERS`.

- [ ] **Step 1: Schrijf `docker-compose.prod.yml`**

```yaml
# Productie-compose (zelfstandig bestand, géén overlay): docker-compose.yml
# blijft het dev-bestand met alleen de database op 5433. Containers binden
# op 127.0.0.1 — nginx op de VPS-host is de enige publieke ingang.
services:
  db:
    image: pgvector/pgvector:pg16
    container_name: aiact-db-prod
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:?POSTGRES_USER ontbreekt in .env}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD ontbreekt in .env}
      POSTGRES_DB: ${POSTGRES_DB:?POSTGRES_DB ontbreekt in .env}
    volumes:
      - aiact_pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: aiact-backend-prod
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      MISTRAL_API_KEY: ${MISTRAL_API_KEY:?MISTRAL_API_KEY ontbreekt in .env}
      UVICORN_WORKERS: ${UVICORN_WORKERS:-2}
    ports:
      - "127.0.0.1:8094:8000"   # 8094: vrij naast alma (8080) en wkpoule (8092)
    volumes:
      # Corpus read-only gemount i.p.v. in de image gebakken: een corpus-update
      # is dan rsync + handmatige index-job, zonder image-rebuild.
      - ./corpus:/app/corpus:ro
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
    container_name: aiact-frontend-prod
    restart: unless-stopped
    ports:
      - "127.0.0.1:3094:3000"   # 3094: vrij naast wkpoule (3091) en alma (3001)
    depends_on:
      - backend

volumes:
  aiact_pg_data:
```

- [ ] **Step 2: Valideer de compose-syntax met dummy-variabelen**

```bash
POSTGRES_USER=x POSTGRES_PASSWORD=x POSTGRES_DB=x MISTRAL_API_KEY=x \
  docker compose -f docker-compose.prod.yml config >/dev/null && echo "compose ok"
```

Verwacht: `compose ok`. Controleer ook dat een ontbrekende variabele hard faalt:
`docker compose -f docker-compose.prod.yml config 2>&1 | head -2` → foutmelding over `POSTGRES_USER`.

- [ ] **Step 3: Commit**

```bash
git add docker-compose.prod.yml
git commit -m "Prod-compose: db+backend+frontend op 127.0.0.1, corpus read-only gemount"
```

---

### Task 3: .gitlab-ci.yml

**Files:**
- Create: `.gitlab-ci.yml`

**Interfaces:**
- Consumes: `docker-compose.prod.yml` (Task 2); het `.env`-contract.
- Produces: jobs `backend_tests`, `frontend_tests`, `deploy_hetzner` (master), `index_corpus` (handmatig).

- [ ] **Step 1: Schrijf `.gitlab-ci.yml`**

```yaml
# AiActWijzer — CI/CD. Volgt het wkpoule/alma-patroon: testen → rsync naar de
# Hetzner-VPS → .env genereren uit CI/CD-variabelen → compose build + up.
# Containers op 127.0.0.1; nginx op de host doet TLS en de /api-split
# (eenmalige VPS-setup: zie docs/deploy.md).
#
# Vereiste GitLab CI/CD-variabelen (Settings → CI/CD → Variables):
#   SSH_USER          — VPS-gebruiker (bv. 'koen')
#   SSH_HOST          — VPS-IP of hostnaam
#   SSH_PRIVATE_KEY   — type Variable; volledige key incl. BEGIN/END-regels
#                       en afsluitende newline
#   POSTGRES_USER, POSTGRES_DB
#   POSTGRES_PASSWORD — markeer als Masked
#   MISTRAL_API_KEY   — markeer als Masked
#
# Bewust NIET in CI: de eval-suite (kost per run geld; bekende stand geeft
# verwacht exit ≠ 0 — zie README). Evals draaien lokaal bij RAG-wijzigingen.
# Corpus-indexering is een handmatige job: herindexeren kost embeddingcalls
# en is alleen nodig bij de eerste deploy of een corpuswijziging.

stages:
  - test
  - deploy

variables:
  APP_DIR: "aiactwijzer"   # relatief t.o.v. $HOME van SSH_USER op de VPS

backend_tests:
  stage: test
  image: python:3.12-slim
  script:
    - pip install --no-cache-dir -r requirements.txt
    # Geen Postgres in deze job: de db-fixture skipt die tests netjes
    # (bestaand gedrag); parser/scoring/prompt/API-tests draaien wél.
    - pytest
  rules:
    - if: $CI_PIPELINE_SOURCE == "push"

frontend_tests:
  stage: test
  image: node:24-alpine
  script:
    - cd frontend
    - npm ci
    # nuxt prepare genereert .nuxt/ (o.a. de eslint-config) die lint nodig heeft
    - npx nuxt prepare
    - npm run lint
    - npm run test
  rules:
    - if: $CI_PIPELINE_SOURCE == "push"

.ssh_setup: &ssh_setup
  - apk add --no-cache openssh-client rsync bash
  - eval $(ssh-agent -s)
  # tr -d '\r' voorkomt CRLF-issues als de key ooit via Windows is geplakt
  - echo "$SSH_PRIVATE_KEY" | tr -d '\r' | ssh-add -
  - mkdir -p ~/.ssh && chmod 700 ~/.ssh
  # Host-key live ophalen (trust-on-first-use): een VPS-rebuild met nieuwe
  # host-key breekt de pipeline dan niet.
  - ssh-keyscan -H "$SSH_HOST" >> ~/.ssh/known_hosts 2>/dev/null
  - chmod 644 ~/.ssh/known_hosts

deploy_hetzner:
  stage: deploy
  image: alpine:3.20
  only:
    - master
  before_script: *ssh_setup
  script:
    - ssh $SSH_USER@$SSH_HOST "mkdir -p $APP_DIR"
    # Bewust GEEN --delete: named volumes en per-ongeluk-verwijderingen
    # blijven zo buiten schot.
    - >
      rsync -az --no-perms --no-owner --no-group
      --exclude=.git
      --exclude=.env
      --exclude=.venv
      --exclude=.superpowers
      --exclude=.pytest_cache
      --exclude=__pycache__
      --exclude=frontend/node_modules
      --exclude=frontend/.nuxt
      --exclude=frontend/.output
      --exclude=evals/results
      ./ $SSH_USER@$SSH_HOST:$APP_DIR/
    # .env op de VPS genereren; heredoc zodat speciale tekens in wachtwoorden
    # geen escaping nodig hebben.
    - |
      ssh $SSH_USER@$SSH_HOST "cat > $APP_DIR/.env" <<EOF
      POSTGRES_USER=$POSTGRES_USER
      POSTGRES_PASSWORD=$POSTGRES_PASSWORD
      POSTGRES_DB=$POSTGRES_DB
      MISTRAL_API_KEY=$MISTRAL_API_KEY
      EOF
    - >
      ssh $SSH_USER@$SSH_HOST "
      cd $APP_DIR &&
      docker compose -f docker-compose.prod.yml pull &&
      docker compose -f docker-compose.prod.yml build &&
      docker compose -f docker-compose.prod.yml up -d --remove-orphans &&
      docker image prune -f
      "

index_corpus:
  stage: deploy
  image: alpine:3.20
  when: manual
  only:
    - master
  needs: ["deploy_hetzner"]
  before_script: *ssh_setup
  script:
    # Handmatig: herindexeren embedt het volledige corpus opnieuw
    # (Mistral-calls). Draaien na de eerste deploy en na elke corpuswijziging.
    - >
      ssh $SSH_USER@$SSH_HOST "
      cd $APP_DIR &&
      docker compose -f docker-compose.prod.yml exec -T backend python -m app.ingest
      "
```

- [ ] **Step 2: Valideer de YAML-syntax**

```bash
.venv/bin/python -c "import yaml; yaml.safe_load(open('.gitlab-ci.yml')); print('yaml ok')"
```

Verwacht: `yaml ok`.

- [ ] **Step 3: Commit**

```bash
git add .gitlab-ci.yml
git commit -m "GitLab CI: test-fase, deploy naar Hetzner, handmatige corpus-indexjob"
```

---

### Task 4: docs/deploy.md + README-verwijzing

**Files:**
- Create: `docs/deploy.md`
- Modify: `README.md` (één verwijzingsregel onder Snelstart)

**Interfaces:**
- Consumes: variabelen-/poortcontract uit Task 2/3.

- [ ] **Step 1: Schrijf `docs/deploy.md`**

```markdown
# Deployment — GitLab CI → Hetzner

Patroon: identiek aan WK Poule/Alma. CI test, rsync't de repo naar de VPS,
genereert `.env` uit CI/CD-variabelen en draait
`docker compose -f docker-compose.prod.yml build + up`. Containers binden op
127.0.0.1 (backend 8094, frontend 3094); nginx op de host is de publieke ingang.

## CI/CD-variabelen (Settings → CI/CD → Variables)

| Variabele | Markering | Toelichting |
| --- | --- | --- |
| `SSH_USER` | — | VPS-gebruiker (bv. `koen`) |
| `SSH_HOST` | — | VPS-IP of hostnaam |
| `SSH_PRIVATE_KEY` | type **Variable** | Volledige private key incl. `-----BEGIN/END-----`-regels en afsluitende newline |
| `POSTGRES_USER` | — | bv. `aiact` |
| `POSTGRES_PASSWORD` | **Masked** | sterk wachtwoord (`openssl rand -hex 24`) |
| `POSTGRES_DB` | — | bv. `aiact` |
| `MISTRAL_API_KEY` | **Masked** | zelfde soort key als lokaal in `.env` |

`DATABASE_URL` is géén variabele: compose bouwt hem op naar `@db:5432` binnen
het compose-netwerk.

## Eenmalige VPS-setup

1. Docker + docker compose aanwezig (staat er al voor de andere projecten).
2. Nginx-serverblok (vervang het placeholder-domein zodra er een domein is):

```nginx
server {
    server_name aiactwijzer.example.nl;

    # API: prefix /api wordt gestript door de trailing slash in proxy_pass.
    location /api/ {
        proxy_pass http://127.0.0.1:8094/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Al het andere: de Nuxt-frontend.
    location / {
        proxy_pass http://127.0.0.1:3094;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    listen 80;
}
```

3. TLS: `certbot --nginx -d aiactwijzer.example.nl` (zelfde werkwijze als de
   andere projecten; certbot herschrijft het blok naar 443).

## Eerste deploy (runbook)

1. GitLab-project aanmaken/koppelen; de 7 variabelen hierboven instellen.
2. Push naar `master` → pipeline draait `backend_tests` + `frontend_tests` →
   `deploy_hetzner`.
3. Draai daarna eenmalig de handmatige job **`index_corpus`** (pipeline-pagina
   → play-knop): indexeert het corpus (~duizend chunks, centen aan
   embedding-calls). Zonder deze stap antwoordt de API met lege bronnen.
4. Controleer: `https://<domein>/api/health` → `{"status":"ok"}`, stel via de
   site een vraag, bekijk `/transparantie`.

## Corpus- of RAG-wijziging

Werkafspraak: eval-suite lokaal draaien vóór de push (zie README — exit ≠ 0 is
op de bekende stand verwacht; beoordeel de scorekaart). Na een corpuswijziging:
push → deploy → handmatig `index_corpus` draaien.

## Bewuste keuzes

- **Evals niet in CI**: elke run kost Mistral-calls, en de bekende stand
  (8/7/10) zou de pipeline permanent rood kleuren. Kwaliteitsbewaking is een
  bewuste lokale actie met menselijke beoordeling van de scorekaart.
- **Corpus als bind-mount, niet in de image**: corpus-update = rsync +
  index-job, zonder rebuild.
- **rsync zonder `--delete`**: een hernoemde map kan nooit per ongeluk data op
  de VPS weggooien; named volume `aiact_pg_data` staat sowieso buiten de
  rsync-target.
- **Geen registry**: images worden op de VPS gebouwd (zelfde als WK Poule) —
  één machine, geen registry-beheer nodig.
```

- [ ] **Step 2: Voeg onder het Snelstart-blok in `README.md` toe**

```markdown
Deployment (GitLab CI → Hetzner): zie `docs/deploy.md`.
```

- [ ] **Step 3: Commit**

```bash
git add docs/deploy.md README.md
git commit -m "Deploy-documentatie: variabelen, nginx-setup, runbook eerste deploy"
```

---

## Zelfreview (uitgevoerd bij het schrijven)

- **Spec-dekking:** Dockerfiles (T1), prod-compose met poorten/volume/corpus-mount (T2), pipeline met test/deploy/index_corpus en variabelen-comment (T3), deploy.md met variabelentabel + nginx + runbook (T4). Dev-compose ongemoeid; evals buiten CI; placeholder-domein consistent.
- **Typeconsistentie:** variabelenamen identiek in compose (T2), CI-heredoc (T3) en tabel (T4); poorten 8094/3094 overal gelijk; `APP_DIR` alleen in CI gebruikt.
- **Open risico (bewust):** de pipeline zelf is pas te testen met een echte GitLab-remote + VPS; lokaal valideren we builds, compose-config en YAML-syntax.
