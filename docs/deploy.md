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

## Stappenplan livegang (van nul naar draaiende demo)

Volgorde is bewust: variabelen vóór de eerste push (anders faalt de
deploy-job), DNS vóór certbot (anders faalt de challenge).

**Stap 1 — Naam en domein.**
De projectnaam is nog niet definitief (CLAUDE.md: werknaam AiActWijzer,
alternatief *Grondslag* — domeincheck stond nog open). Kies de naam, registreer
het domein en zet een **A-record** naar het VPS-IP. DNS mag alvast propageren
terwijl je verder gaat.

**Stap 2 — Deploy-sleutelpaar.**
Maak een eigen keypair voor de pipeline (niet je persoonlijke sleutel):

```bash
ssh-keygen -t ed25519 -f ~/.ssh/aiactwijzer_deploy -N "" -C "gitlab-deploy aiactwijzer"
ssh-copy-id -i ~/.ssh/aiactwijzer_deploy.pub <SSH_USER>@<SSH_HOST>
```

**Stap 3 — GitLab-project + variabelen.**
Maak een (privé) GitLab-project aan en zet **vóór de eerste push** de 7
variabelen uit de tabel hierboven (Settings → CI/CD → Variables).
`SSH_PRIVATE_KEY` = de inhoud van `~/.ssh/aiactwijzer_deploy` (incl.
BEGIN/END-regels en afsluitende newline); `POSTGRES_PASSWORD` genereer je met
`openssl rand -hex 24`; markeer beide wachtwoord-achtigen als **Masked**.

**Stap 4 — Nginx op de VPS.**
Plaats het serverblok hierboven (met het echte domein i.p.v. het placeholder),
activeer en herlaad:

```bash
sudo nano /etc/nginx/sites-available/<domein>
sudo ln -s /etc/nginx/sites-available/<domein> /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

**Stap 5 — Eerste push.**

```bash
git remote add origin git@gitlab.com:<jouw-namespace>/<project>.git
git push -u origin master
```

Volg de pipeline: `backend_tests` + `frontend_tests` → `deploy_hetzner`. De
eerste deploy bouwt beide images op de VPS en duurt enkele minuten.

**Stap 6 — TLS.**
Zodra DNS doorverwijst: `sudo certbot --nginx -d <domein>` (herschrijft het
blok naar 443 + redirect).

**Stap 7 — Corpus indexeren (eenmalig).**
Pipeline-pagina → play-knop bij **`index_corpus`**. Dit embedt ~duizend chunks
(centen aan Mistral-calls). Zonder deze stap antwoordt de API met lege bronnen.

**Stap 8 — Controle.**
`https://<domein>/api/health` → `{"status":"ok"}`; stel via de site de
cv-screeningvraag (verwacht: antwoord met citaatblok en klikbare ref); klik
"bekijk de bron" (EUR-Lex opent); bekijk `/transparantie`; check smal venster
(paneel onder het antwoord).

**Stap 9 — Nazorg publiek moment (optioneel, uit CLAUDE.md).**
Domein vermelden op de transparantie-pagina waar relevant; MIT-licentie +
GitHub-publicatie (vindbaarheid/portfolio — CI blijft op GitLab); demo +
LinkedIn-post.

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
- **`APP_DIR` is relatief** (`aiactwijzer` t.o.v. de home-dir van `SSH_USER`),
  waar wkpoule/alma een absoluut pad hardcoden — zo blijft de pipeline werken
  als de VPS-gebruiker ooit anders heet.
- **Geen backend-healthcheck in compose**: bij een koude start kunnen de
  eerste `/api`-requests kort een 502 geven totdat uvicorn luistert
  (zelfherstellend; acceptabel voor een low-traffic demo op één VPS).
