# SEO-contentpijplijn: scaffolding + sector-hubs + interne links — ontwerp

**Datum:** 2026-08-03
**Status:** goedgekeurd (ontwerp), klaar voor implementatieplan
**Doel:** topical authority op "EU AI Act" vergroten door (a) veel meer adresseerbare
`/vraag`-pagina's te kunnen maken zonder handmatig elk antwoord uit te typen, en (b) de
kennisbank te structureren met sector-hubs en interne links.

## Context

De site heeft de technische SEO al op orde (`@nuxtjs/seo`, zelf-gegenereerde sitemap,
QAPage-schema per `/vraag`, Dataset op `/deadlines`, `llms.txt`, RSS). De grootste
resterende hefboom is **contentdiepte**: er zijn nu 9 adresseerbare vraag-pagina's; het
zoekvolume rond de AI Act in het Nederlands is een grote longtail.

Bouwstenen die er al zijn en die we hergebruiken:
- **Vragen-pijplijn:** `content/vragen/*.md` (frontmatter + body) → `utils/vragen.ts`
  (`import.meta.glob`, `alleVragen`, `vindVraag`) → `pages/vraag/[slug].vue` met
  QAPage-schema. Een nieuwe pagina = een nieuw `.md`-bestand.
- **Eigen RAG-engine:** `backend/app/rag/service.py` `beantwoord(sessie, vraag) ->
  AskResultaat` met `antwoord`, `citaten: list[Citaat]` (`ref`, `fragment`, `bron`,
  `url`), `stand_van_wetgeving`, `geen_bron`.
- **Demand-signaal:** `IngezondenVraag` (opt-in ingezonden onbeantwoorde vragen — alleen
  tekst + datum) en de geen-bron-teller.

## Kernprincipe

**Het script publiceert niets automatisch.** Het draft gegronde concepten via de eigen
engine; de mens redigeert en publiceert. Op een juridisch-informatieproduct zonder
auto-verificatietool blijft de redactionele pen bij de mens. (Beslissing: scaffolding +
redactionele gate, niet auto-publiceren.)

## Deel A — Scaffolding-script (`scripts/draft_vragen.py`)

Een handmatig te draaien script (stijl `scripts/converteer_eurlex.py`), in-process tegen
de corpus-DB + Mistral.

- **Kandidaat-vragen** uit twee bronnen:
  1. `scripts/vraag_kandidaten.yaml` — een verzorgde seed-lijst (keyword-clusters +
     sectorvragen), zodat het werkt ook nu de inzendingen dun zijn. Elk item:
     `{ vraag: str, sector?: str }`.
  2. de `IngezondenVraag`-tabel (echte onbeantwoorde vragen).
- **Per vraag** → `service.beantwoord(sessie, vraag)`:
  - `geen_bron` → regel naar `content/vragen/_concept/_corpusgaten.md` (corpusgat of
    adviesvraag; **niet** publiceren).
  - anders → `content/vragen/_concept/<slug>.md` schrijven met frontmatter
    (`vraag`, `artikel` = `citaten[0].ref` (of samengevoegd), `stand-wetgeving` =
    `stand_van_wetgeving`, `bijgewerkt` = draai-datum, `sector` uit het seed-item) +
    body = `antwoord` + een reviewer-notitieblok met de citaten (`ref` + `url`).
- **Redactionele gate:** de frontend-glob is `content/vragen/*.md` — die matcht géén
  submap, dus `content/vragen/_concept/` is onzichtbaar voor de site. De redacteur
  redigeert een concept en verplaatst het één map omhoog om te publiceren.
- **Idempotent:** sla een kandidaat over als de slug al bestaat in `content/vragen/`
  (gepubliceerd) of in `_concept/` (al gedraft). `--dry-run` toont wat het zou doen
  zonder te schrijven of de engine te bellen.
- **Slug:** genormaliseerde vraag (lowercase, niet-alfanumeriek → `-`), zoals de
  bestaande bestandsnamen.

## Deel B — Sector-hubs (`/sector/[slug]`)

- **Frontmatter:** optioneel veld `sector: <slug>` op vraag-`.md`'s (één sector).
- **`utils/vragen.ts`:** `sector` meenemen in de `Vraag`-interface + parser; helpers
  `vragenPerSector(sector)` en `alleSectoren()`.
- **Hub-content:** `content/sectoren/<slug>.md` (frontmatter `naam`, `titel`,
  `beschrijving` + body-intro). `utils/sectoren.ts` (`alleSectoren`, `vindSector`),
  zelfde `import.meta.glob`-patroon.
- **Pagina:** `pages/sector/[slug].vue` — intro uit de sector-markdown + auto-lijst van
  `vragenPerSector(slug)` + link naar `/vraag` en `/`. `useSeoMeta` + `useSchemaOrg`
  (`CollectionPage`). Onbekende slug → echte 404 (zoals `vraag/[slug].vue`).
- **Start-sectoren:** `zorg`, `overheid`, `hr`, `financieel`.
- **Sitemap:** de bestaande hook (`nitro:build:public-assets`) leest nu
  `content/vragen/`; breid uit met `content/sectoren/` → `/sector/<slug>`-routes.

## Deel C — Interne links (hub-and-spoke)

- **`utils/vragen.ts`:** `gerelateerde(vraag, max=4)` — andere vragen gerangschikt op
  gedeelde `sector` (zwaarst) en gedeeld `artikel` (lichter), exclusief de vraag zelf.
- **`pages/vraag/[slug].vue`:** een "Gerelateerde vragen"-blok (lijst met links) onder het
  antwoord; en als de vraag een `sector` heeft, een kruimel/teruglink naar de sector-hub
  ("AI Act voor de zorg"). Puur interne `NuxtLink`s.
- Van hub → vragen (de lijst), van vraag → hub (kruimel) + vraag → verwante vragen: de
  klassieke hub-and-spoke die Google de samenhang laat zien.

## Buiten scope (bewust)

- **Sitemap `lastmod`/prioriteit** — niet in deze klus (aparte kleine ingreep).
- **Auto-publiceren / eval-gate** — bewust niet; redactionele gate blijft.
- Geen wijziging aan de RAG-engine of het corpus; het script consumeert alleen.

## Verificatie

- **Script (pytest):** met een fake `beantwoord` — gegrond → concept met correcte
  frontmatter; `geen_bron` → corpusgaten-rapport, geen concept; idempotentie (bestaande
  slug overgeslagen); `--dry-run` schrijft niets.
- **Frontend:** `nuxt build` groen; een sector-hub rendert met z'n vragenlijst en staat in
  `sitemap.xml`; het gerelateerde-vragen-blok + kruimel renderen op een vraagpagina;
  CollectionPage/QAPage-schema aanwezig. Smoke via de preview-server (zoals eerder).

## Bestanden

- **Nieuw:** `scripts/draft_vragen.py`, `scripts/vraag_kandidaten.yaml`,
  `backend/tests/test_draft_vragen.py` (of `tests/` naast het script), `utils/sectoren.ts`,
  `pages/sector/[slug].vue`, `content/sectoren/{zorg,overheid,hr,financieel}.md`.
- **Wijzigen:** `frontend/utils/vragen.ts` (sector + `vragenPerSector`/`alleSectoren`/
  `gerelateerde`), `frontend/pages/vraag/[slug].vue` (related-blok + kruimel),
  `frontend/nuxt.config.ts` (sitemap-hook: `content/sectoren`).
- **Geen** DB-schemawijziging; **geen** nieuwe frontend-dependency (yaml lezen kan het
  script met de al aanwezige `js-yaml` in de frontend — maar het script is Python, dus
  `pyyaml`/`ruamel`; check requirements, anders stdlib-parse of toevoegen).
