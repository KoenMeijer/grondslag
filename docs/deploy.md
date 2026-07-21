# Deployment — GitLab CI → Hetzner

Patroon: identiek aan WK Poule/Alma. CI test, rsync't de repo naar de VPS,
genereert `.env` uit CI/CD-variabelen en draait
`docker compose -f docker-compose.prod.yml build + up`. Containers binden op
127.0.0.1 (backend 8094, frontend 3094); nginx op de host is de publieke ingang.

## CI/CD-variabelen (Settings → CI/CD → Variables)

| Variabele | Markering | Toelichting |
| --- | --- | --- |
| `SSH_USER` | — | VPS-gebruiker: `root` (app komt in `/root/aiactwijzer`, want `APP_DIR` is relatief) |
| `SSH_HOST` | — | VPS-IP of hostnaam |
| `SSH_PRIVATE_KEY` | type **Variable**, Protected | Erft van de groep `alma-group1` (gedeeld met alma/wkpoule) — niet projecteigen instellen. Zie stap 3: `master` moet protected zijn, anders komt hij leeg binnen |
| `POSTGRES_USER` | — | bv. `aiact` |
| `POSTGRES_PASSWORD` | **Masked** | sterk wachtwoord (`openssl rand -hex 24`) |
| `POSTGRES_DB` | — | bv. `aiact` |
| `MISTRAL_API_KEY` | **Masked** | zelfde soort key als lokaal in `.env` |

`DATABASE_URL` is géén variabele: compose bouwt hem op naar `@db:5432` binnen
het compose-netwerk.

## Eenmalige VPS-setup

1. Docker + docker compose aanwezig (staat er al voor de andere projecten).
2. Nginx-serverblok: staat in de repo als
   `deploy/nginx/grondslag.almaconecta.eu.conf` (v1 draait op het subdomein,
   zie stap 1) — één bron, zodat doc en VPS niet uit elkaar lopen. Plaatsen:
   zie stap 4 hieronder.
3. TLS: `certbot --nginx -d grondslag.almaconecta.eu` (zelfde werkwijze als de
   andere projecten; certbot herschrijft het blok naar 443).

## Stappenplan livegang (van nul naar draaiende demo)

Dit is het traject zoals het op 21 jul 2026 is gelopen, met het subdomein als
startpunt. **De site draait inmiddels op https://grondslag.eu** — zie de sectie
over het eigen domein hieronder. Zet je dit ooit op een nieuwe machine, lees dan
beide secties samen: de stappen kloppen, alleen de domeinnaam is inmiddels
`grondslag.eu`.

Volgorde is bewust: variabelen vóór de eerste push (anders faalt de
deploy-job), DNS vóór certbot (anders faalt de challenge).

**Stap 1 — Domein: eerst een subdomein van alma.**
Naam gekozen: **Grondslag** (CLAUDE.md, 21 jul 2026); `grondslag.eu` is het doel,
maar voor de eerste livegang draaien we op een subdomein van het bestaande
`almaconecta.eu`: **`grondslag.almaconecta.eu`**. Reden: geen registratie en geen
wachttijd op beschikbaarheid, en de VPS is dezelfde machine — alleen een
**A-record** `grondslag` → het VPS-IP bij de DNS-provider van `almaconecta.eu`.
Overstappen naar een eigen domein is later een kwestie van DNS + nginx + certbot;
zie *Later: naar een eigen domein* onderaan.

**Stap 2 — Deploy-sleutel: hergebruikt uit de groep.**
`SSH_PRIVATE_KEY` is een **group-level variabele van `alma-group1`**, gedeeld met
alma en wkpoule; die is bij livegang (21 jul 2026) hergebruikt. Er is dus géén
eigen keypair nodig — een projecteigen sleutel zou wel netter isoleren, maar
betekent een tweede secret beheren voor dezelfde VPS. Alleen als je die route
tóch wilt:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/aiactwijzer_deploy -N "" -C "gitlab-deploy aiactwijzer"
ssh-copy-id -i ~/.ssh/aiactwijzer_deploy.pub root@<SSH_HOST>
```

**Stap 3 — GitLab-project, branch-instellingen en variabelen.**
Maak een (privé) GitLab-project aan — **zonder** "Initialize repository with a
README", anders krijg je een `main` met een losse historie naast je `master`.

Zet daarna, **vóór de eerste push**:

1. **Default branch op `master`** (Settings → Repository → Branch defaults) —
   de CI-rules draaien op `$CI_COMMIT_BRANCH == "master"`.
2. **`master` als protected branch** (Settings → Repository → Protected
   branches). Dit is geen formaliteit: group-variabelen staan op *Protected* en
   worden aan een onbeschermde branch **niet** uitgeleverd. Het gevolg is
   verraderlijk — `$SSH_PRIVATE_KEY` is dan leeg en `ssh-add` meldt
   `Error loading key "(stdin)": error in libcrypto`, wat leest als een kapotte
   sleutel terwijl er simpelweg niets in de variabele zat.
3. De projectvariabelen uit de tabel hierboven (Settings → CI/CD → Variables).
   `POSTGRES_PASSWORD` genereer je met `openssl rand -hex 24`; markeer die en
   `MISTRAL_API_KEY` als **Masked**.

**Stap 4 — Nginx op de VPS.**
Het serverblok staat als bestand in de repo, dus kopiëren i.p.v. overtikken
(geen quoting-gedoe met heredocs door twee shells heen):

```bash
scp deploy/nginx/grondslag.almaconecta.eu.conf \
  root@<SSH_HOST>:/etc/nginx/sites-available/grondslag.almaconecta.eu
ssh root@<SSH_HOST> "ln -sf /etc/nginx/sites-available/grondslag.almaconecta.eu \
  /etc/nginx/sites-enabled/ && nginx -t && systemctl reload nginx"
```

`nginx -t` staat bewust vóór de reload: nginx weigert bij een fout de héle
config, dus een typefout hier zou ook alma en wkpoule offline halen.
Controleer eerst dat 8094/3094 vrij zijn — meerdere projecten delen deze VPS:
`ssh root@<SSH_HOST> "ss -tlnp | grep -E '8094|3094' || echo 'poorten vrij'"`.

**Stap 5 — Eerste push.**

```bash
git remote add origin git@gitlab.com:<jouw-namespace>/<project>.git
git push -u origin master
```

Volg de pipeline: `backend_tests` + `frontend_tests` → `deploy_hetzner`. De
eerste deploy bouwt beide images op de VPS en duurt enkele minuten.

**Stap 6 — TLS.**
Zodra DNS doorverwijst: `sudo certbot --nginx -d grondslag.almaconecta.eu`
(herschrijft het blok naar 443 + redirect). Dit is een **los certificaat** voor
het subdomein; het bestaande cert van alma wordt niet aangeraakt en hoeft niet
uitgebreid te worden — de twee sites blijven onafhankelijk.

**Stap 7 — Corpus indexeren (eenmalig).**
Pipeline-pagina → play-knop bij **`index_corpus`**. Dit embedt ~duizend chunks
(centen aan Mistral-calls). Zonder deze stap antwoordt de API met lege bronnen.

**Stap 8 — Controle.**
Snelle rooktest vanaf je eigen machine (health, redirect, en de RAG-keten —
citaten leeg betekent dat stap 7 niet gelukt is):

```bash
curl -s https://grondslag.eu/api/health
curl -s -o /dev/null -w '%{http_code} -> %{redirect_url}\n' http://grondslag.eu/api/health
curl -s -X POST https://grondslag.eu/api/ask \
  -H 'Content-Type: application/json' \
  -d '{"vraag":"Wij screenen cvs met AI. Valt dat onder de AI Act?"}'
```

Verder handmatig: stel via de site de
cv-screeningvraag (verwacht: antwoord met citaatblok en klikbare ref); klik
"bekijk de bron" (EUR-Lex opent); bekijk `/transparantie`; check smal venster
(paneel onder het antwoord).

**Stap 9 — Nazorg publiek moment (optioneel, uit CLAUDE.md).**
Domein vermelden op de transparantie-pagina waar relevant; MIT-licentie +
GitHub-publicatie (vindbaarheid/portfolio — CI blijft op GitLab); demo +
LinkedIn-post.

## Eigen domein grondslag.eu — gedaan op 21 jul 2026

De code kent het domein niet: de frontend praat relatief via `/api`, er is geen
CORS-config en geen `BASE_URL`-variabele. De overstap was dus puur infra — DNS,
nginx, certbot — zonder deploy of rebuild.

Stappen 1 t/m 3 zijn **uitgevoerd**; het certificaat draagt nu drie namen
(`grondslag.eu`, `www.grondslag.eu`, `grondslag.almaconecta.eu`) en beide
domeinen serveren de site. Stappen 4 t/m 6 staan nog open.

1. ✅ **Geregistreerd**, zone bij Hetzner DNS, **A-records** `@` en `www` naar
   het VPS-IP. Bewust **geen AAAA**: de VPS heeft wel IPv6, maar nginx luistert
   alleen op IPv4 (`listen 80;` / `listen 443`, niet `[::]`) — een AAAA-record
   zou IPv6-bezoekers naar een dichte poort sturen. Alma doet dit om dezelfde
   reden IPv4-only.
2. ✅ **Nginx: domein toegevoegd, niet vervangen.** Het nieuwe domein staat
   *naast* het subdomein in beide serverblokken (443 én de poort-80-redirect),
   zodat gedeelde links blijven werken:
   `server_name grondslag.eu www.grondslag.eu grondslag.almaconecta.eu;` →
   `nginx -t && systemctl reload nginx`. Tussenstand daarna: `http://grondslag.eu`
   gaf 404 en https een certfout — normaal, dat sluit stap 3.
3. ✅ **Certificaat uitgebreid.**
   `certbot --nginx --expand --redirect -d grondslag.almaconecta.eu -d grondslag.eu -d www.grondslag.eu`
   — certbot vervangt het bestaande cert door één met alle namen erin. Doe dit
   pas als de DNS van het nieuwe domein daadwerkelijk het VPS-IP teruggeeft
   (`dig +short grondslag.eu`), anders faalt de HTTP-01-challenge en rolt certbot
   de hele wijziging terug.
4. **Omzetten.** Maak het nieuwe domein de canonieke naam en laat het subdomein
   een tijdje 301'en, zodat gedeelde links blijven werken:

```nginx
server {
    listen 443 ssl;
    server_name grondslag.almaconecta.eu;
    return 301 https://grondslag.eu$request_uri;
    # ssl_certificate-regels van certbot hier laten staan
}
```

5. **Opruimen.** Pas als niemand het subdomein meer gebruikt: het redirect-blok
   weg, het A-record weg, en het subdomein uit het certificaat halen met
   `sudo certbot --nginx -d grondslag.eu -d www.grondslag.eu` (certbot vraagt om
   bevestiging dat het cert de oude naam verliest).
6. **Nalopen op vermeldingen.** Domeinnaam staat verder alleen in tekst:
   `CLAUDE.md`, dit bestand, de transparantie-pagina en de LinkedIn/README-links.
   `grep -rn "almaconecta" .` vóór je afsluit.

## Corpus- of RAG-wijziging

Werkafspraak: eval-suite lokaal draaien vóór de push (zie README — exit ≠ 0 is
op de bekende stand verwacht; beoordeel de scorekaart). Na een corpuswijziging:
push → deploy → handmatig `index_corpus` draaien.

## Bewuste keuzes

- **Evals niet in CI**: elke run kost Mistral-calls, en de bekende stand
  (8/9/10, juli 2026) zou de pipeline permanent rood kleuren. Kwaliteitsbewaking is een
  bewuste lokale actie met menselijke beoordeling van de scorekaart.
- **Eerst een subdomein van alma, niet meteen een eigen domein**: het domein
  zit nergens in de code, dus registratie is geen blokkade voor livegang. Zo
  komt de demo online zonder te wachten op domeincheck/registratie, en blijft
  `grondslag.eu` een losse, omkeerbare stap.
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
