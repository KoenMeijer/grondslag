# SEO-contentpijplijn — implementatieplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Scaffolding-script dat via de eigen RAG-engine gegronde concept-`/vraag`-pagina's draft (redactionele gate), plus sector-hubs en interne hub-and-spoke-links.

**Architecture:** Pure draft-logica in `backend/app/contentdraft.py` (testbaar, DB-vrij); dunne orchestrator `scripts/draft_vragen.py`. Frontend: `utils/vragen.ts` krijgt sector + relatie-helpers, nieuwe `/sector/[slug]`-hubs uit `content/sectoren/*.md`, en een gerelateerde-vragen-blok op de vraagpagina's. Alles hergebruikt de bestaande markdown→glob→schema-pijplijn.

**Tech Stack:** Python (FastAPI-app-context, pyyaml — al aanwezig), pytest; Nuxt 3 + `@nuxtjs/seo` (`useSchemaOrg`). Geen nieuwe dependency.

## Global Constraints

- **Script publiceert nooit automatisch.** Concepten landen in `content/vragen/_concept/`; die map wordt NIET door de site geladen (`import.meta.glob('../content/vragen/*.md')` matcht geen submap). Mens verplaatst een goedgekeurd bestand één map omhoog.
- Pure, DB-vrije logica in `backend/app/contentdraft.py`; het script (`scripts/draft_vragen.py`) doet DB/engine/bestand-IO. Tests importeren `from app import contentdraft` (net als `test_feed.py`).
- Slug = lowercase, niet-alfanumeriek → `-`, randstreepjes weg (zelfde vorm als bestaande bestandsnamen in `content/vragen/`).
- Frontmatter-velden exact: `vraag`, `artikel`, `stand-wetgeving`, `bijgewerkt`, optioneel `sector`.
- Start-sectoren: `zorg`, `overheid`, `hr`, `financieel`.
- Geen DB-schemawijziging, geen nieuwe frontend-dependency.
- Backend-tests: `cd /home/koenmeijer/projecten/AiActWijzer && python -m pytest backend/tests/test_contentdraft.py -v` (repo-root; `pytest.ini` zet `pythonpath = backend .`). Frontend heeft géén unit-runner → verificatie via `cd frontend && npm run build` + preview-smoke.
- Nederlandse "waarom"-comments (huisstijl).

---

### Task 1: Pure draft-logica `app/contentdraft.py`

**Files:**
- Create: `backend/app/contentdraft.py`
- Test: `backend/tests/test_contentdraft.py`

**Interfaces:**
- Produces:
  - `slug(vraag: str) -> str`
  - `render_concept(vraag, artikel, stand, bijgewerkt, sector, antwoord, citaten) -> str` (`citaten`: lijst van objecten/dicts met `.ref`/`.url`; render frontmatter + body + reviewer-notitie)
  - `corpusgat_regel(vraag: str, bijgewerkt: str) -> str`
  - `bestaat_al(slug: str, gepubliceerd: set[str], concepten: set[str]) -> bool`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_contentdraft.py
"""Pure draft-logica — DB-vrij, geen engine-aanroep (zoals test_feed)."""
from app import contentdraft as cd


class _Cit:
    def __init__(self, ref, url):
        self.ref, self.url = ref, url


def test_slug():
    assert cd.slug("Valt mijn AI-systeem onder de AI-verordening?") == "valt-mijn-ai-systeem-onder-de-ai-verordening"
    assert cd.slug("  GPAI: wat nu?  ") == "gpai-wat-nu"


def test_render_concept_has_frontmatter_and_citations():
    md = cd.render_concept(
        vraag="Wat is een hoog-risico-systeem?",
        artikel="Artikel 6",
        stand="juli 2026",
        bijgewerkt="2026-08-03",
        sector="zorg",
        antwoord="Een hoog-risico-systeem is ...",
        citaten=[_Cit("artikel 6", "https://eur-lex.europa.eu/x")],
    )
    assert md.startswith("---\n")
    assert 'vraag: "Wat is een hoog-risico-systeem?"' in md
    assert "artikel: \"Artikel 6\"" in md
    assert "stand-wetgeving: \"juli 2026\"" in md
    assert "bijgewerkt: \"2026-08-03\"" in md
    assert "sector: zorg" in md
    assert "Een hoog-risico-systeem is ..." in md
    # Reviewer-notitie met de citaten (wordt vóór publicatie weggehaald/gecheckt).
    assert "artikel 6" in md and "https://eur-lex.europa.eu/x" in md


def test_render_concept_without_sector_omits_field():
    md = cd.render_concept(vraag="X?", artikel="Artikel 2", stand="juli 2026",
                           bijgewerkt="2026-08-03", sector=None,
                           antwoord="...", citaten=[])
    assert "sector:" not in md


def test_bestaat_al():
    assert cd.bestaat_al("x", {"x"}, set()) is True       # al gepubliceerd
    assert cd.bestaat_al("x", set(), {"x"}) is True         # al concept
    assert cd.bestaat_al("x", set(), set()) is False


def test_corpusgat_regel():
    assert cd.corpusgat_regel("Mag ik X?", "2026-08-03") == "- 2026-08-03 — Mag ik X?"
```

- [ ] **Step 2: Run test — verify it fails**

Run: `python -m pytest backend/tests/test_contentdraft.py -v`
Expected: FAIL (`ModuleNotFoundError: app.contentdraft`).

- [ ] **Step 3: Implement**

```python
# backend/app/contentdraft.py
"""Pure, DB-vrije bouwstenen voor het scaffolding-script (scripts/draft_vragen.py).

Gescheiden van het script zodat de renderer/slug/idempotentie testbaar zijn zonder
DB of Mistral-aanroep — zelfde patroon als app/feed.py. Het script publiceert
nooit; het schrijft concepten die een mens redigeert en handmatig publiceert.
"""
from __future__ import annotations

import re


def slug(vraag: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", vraag.strip().lower())
    return s.strip("-")


def bestaat_al(slug: str, gepubliceerd: set[str], concepten: set[str]) -> bool:
    """Idempotent: sla over als de vraag al gepubliceerd of al gedraft is."""
    return slug in gepubliceerd or slug in concepten


def corpusgat_regel(vraag: str, bijgewerkt: str) -> str:
    """Eén regel voor het corpusgaten-rapport (geen_bron-vragen — niet publiceren)."""
    return f"- {bijgewerkt} — {vraag}"


def render_concept(*, vraag: str, artikel: str, stand: str, bijgewerkt: str,
                   sector: str | None, antwoord: str, citaten) -> str:
    """Render een concept-vraagpagina: frontmatter (zoals content/vragen/*.md) +
    het gedrafte antwoord + een reviewer-notitie met de citaten. De redacteur
    controleert/knipt de notitie vóór publicatie."""
    fm = [
        "---",
        f'vraag: "{vraag}"',
        f'artikel: "{artikel}"',
        f'stand-wetgeving: "{stand}"',
        f'bijgewerkt: "{bijgewerkt}"',
    ]
    if sector:
        fm.append(f"sector: {sector}")
    fm.append("---")

    notitie = ["", "<!-- REVIEW — verwijder dit blok vóór publicatie.",
               "Concept via de eigen RAG-engine; controleer tegen de wettekst.",
               "Citaten:"]
    for c in citaten:
        notitie.append(f"- {getattr(c, 'ref', '')} — {getattr(c, 'url', '')}")
    notitie.append("-->")

    return "\n".join(fm) + "\n\n" + antwoord.strip() + "\n" + "\n".join(notitie) + "\n"
```

- [ ] **Step 4: Run test — verify it passes**

Run: `python -m pytest backend/tests/test_contentdraft.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/contentdraft.py backend/tests/test_contentdraft.py
git commit -m "feat(content): pure draft-logica voor de vraag-scaffolding"
```

---

### Task 2: Orchestrator-script + seed-vragen

**Files:**
- Create: `scripts/draft_vragen.py`, `scripts/vraag_kandidaten.yaml`
- Test: `backend/tests/test_draft_vragen_kandidaten.py`

**Interfaces:**
- `draft_vragen.laad_kandidaten(pad_yaml, ingezonden: list[str]) -> list[dict]` (samengevoegd + ontdubbeld op slug; elk `{vraag, sector}`)
- CLI: `python scripts/draft_vragen.py [--dry-run] [--limit N]`

**Consumes:** `app.contentdraft` (Task 1), `app.rag.service.beantwoord`, `app.db.SessionLocal`, `app.models.IngezondenVraag`.

- [ ] **Step 1: Write the failing test** (alleen de pure kandidaat-samenvoeging; de engine-loop is integratie)

```python
# backend/tests/test_draft_vragen_kandidaten.py
import importlib.util
from pathlib import Path

_pad = Path(__file__).resolve().parents[2] / "scripts" / "draft_vragen.py"
_spec = importlib.util.spec_from_file_location("draft_vragen", _pad)
draft_vragen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(draft_vragen)


def test_laad_kandidaten_merges_and_dedupes(tmp_path):
    yaml_pad = tmp_path / "k.yaml"
    yaml_pad.write_text(
        "- vraag: Wat is een AI-systeem?\n  sector: zorg\n"
        "- vraag: Wat is een AI-systeem?\n"          # dubbele → één keer
        "- vraag: Wanneer gelden de plichten?\n",
        encoding="utf-8",
    )
    kandidaten = draft_vragen.laad_kandidaten(str(yaml_pad), ["Wat is GPAI?"])
    vragen = [k["vraag"] for k in kandidaten]
    assert "Wat is een AI-systeem?" in vragen
    assert "Wat is GPAI?" in vragen                  # ingezonden meegevoegd
    assert len(vragen) == len(set(draft_vragen.slug(v) for v in vragen))  # uniek op slug
    # eerste (met sector) wint bij een dubbele
    z = next(k for k in kandidaten if k["vraag"] == "Wat is een AI-systeem?")
    assert z.get("sector") == "zorg"
```

- [ ] **Step 2: Run test — verify it fails**

Run: `python -m pytest backend/tests/test_draft_vragen_kandidaten.py -v`
Expected: FAIL (script/functie bestaat nog niet).

- [ ] **Step 3: Implement the script**

```python
# scripts/draft_vragen.py
"""Scaffolding: draft gegronde concept-vraagpagina's via de eigen RAG-engine.

Publiceert NIETS. Voor elke kandidaat-vraag (uit scripts/vraag_kandidaten.yaml +
de IngezondenVraag-tabel) draait het de eigen `service.beantwoord` en schrijft:
- gegrond antwoord  → content/vragen/_concept/<slug>.md  (frontmatter + body +
  reviewer-notitie); een mens redigeert en verplaatst 'm naar content/vragen/.
- geen_bron         → een regel in content/vragen/_concept/_corpusgaten.md
  (corpusgat of adviesvraag — niet publiceren).

De _concept-map wordt niet door de site geladen (de glob pakt alleen
content/vragen/*.md). Idempotent: bestaande slugs worden overgeslagen.

Gebruik: python scripts/draft_vragen.py [--dry-run] [--limit N]
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, timezone, datetime
from pathlib import Path

import yaml

from app import contentdraft
from app.db import SessionLocal
from app.models import IngezondenVraag
from app.rag import service

ROOT = Path(__file__).resolve().parents[1]
VRAGEN_DIR = ROOT / "frontend" / "content" / "vragen"
CONCEPT_DIR = VRAGEN_DIR / "_concept"
SEED_YAML = ROOT / "scripts" / "vraag_kandidaten.yaml"

slug = contentdraft.slug


def laad_kandidaten(pad_yaml: str, ingezonden: list[str]) -> list[dict]:
    """Voeg seed-yaml + ingezonden vragen samen, ontdubbeld op slug (eerste wint,
    zodat een seed-item met sector voorrang heeft op een kale ingezonden dubbele)."""
    items: list[dict] = []
    with open(pad_yaml, encoding="utf-8") as f:
        for rij in yaml.safe_load(f) or []:
            items.append({"vraag": str(rij["vraag"]).strip(),
                          "sector": rij.get("sector")})
    for v in ingezonden:
        items.append({"vraag": v.strip(), "sector": None})
    gezien: set[str] = set()
    uniek: list[dict] = []
    for it in items:
        s = slug(it["vraag"])
        if s and s not in gezien:
            gezien.add(s)
            uniek.append(it)
    return uniek


def _bestaande_slugs(directory: Path, met_submap: bool = False) -> set[str]:
    if not directory.exists():
        return set()
    return {p.stem for p in directory.glob("*.md") if not p.name.startswith("_")}


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--limit", type=int, default=0)
    args = p.parse_args(argv)

    vandaag = datetime.now(timezone.utc).date().isoformat()
    with SessionLocal() as sessie:
        ingezonden = [r.vraag for r in sessie.query(IngezondenVraag).all()]
        kandidaten = laad_kandidaten(str(SEED_YAML), ingezonden)
        gepubliceerd = _bestaande_slugs(VRAGEN_DIR)
        concepten = _bestaande_slugs(CONCEPT_DIR)

        todo = [k for k in kandidaten
                if not contentdraft.bestaat_al(slug(k["vraag"]), gepubliceerd, concepten)]
        if args.limit:
            todo = todo[: args.limit]

        print(f"{len(kandidaten)} kandidaten, {len(todo)} nieuw te draften"
              f"{' (dry-run)' if args.dry_run else ''}.")
        if args.dry_run:
            for k in todo:
                print(f"  zou draften: {slug(k['vraag'])}  ({k['vraag']})")
            return 0

        CONCEPT_DIR.mkdir(parents=True, exist_ok=True)
        gaten: list[str] = []
        for k in todo:
            res = service.beantwoord(sessie, k["vraag"])
            if res.geen_bron or not res.citaten:
                gaten.append(contentdraft.corpusgat_regel(k["vraag"], vandaag))
                continue
            md = contentdraft.render_concept(
                vraag=k["vraag"], artikel=res.citaten[0].ref,
                stand=res.stand_van_wetgeving, bijgewerkt=vandaag,
                sector=k.get("sector"), antwoord=res.antwoord, citaten=res.citaten,
            )
            (CONCEPT_DIR / f"{slug(k['vraag'])}.md").write_text(md, encoding="utf-8")
            print(f"  concept: {slug(k['vraag'])}")
        if gaten:
            (CONCEPT_DIR / "_corpusgaten.md").write_text(
                "# Corpusgaten / adviesvragen (niet publiceren)\n\n" + "\n".join(gaten) + "\n",
                encoding="utf-8")
            print(f"  {len(gaten)} corpusgaten weggeschreven.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Write the seed candidates**

Create `scripts/vraag_kandidaten.yaml` with ~24 questions across keyword-clusters (risicoclassificatie, verboden praktijken, GPAI, transparantie, deadlines, boetes/handhaving, scope) and the 4 sectors. Each item `{ vraag, sector? }`. Example shape (write ~24, Dutch, real search-style questions):

```yaml
# Kandidaat-vragen voor de scaffolding. Het script draait deze door de eigen
# engine; alleen gegronde antwoorden worden concept (mens publiceert).
- vraag: "Hoe bepaal ik of mijn AI-systeem hoog risico is?"
- vraag: "Welke boetes staan er op overtreding van de AI-verordening?"
- vraag: "Wat is het verschil tussen een aanbieder en een gebruiksverantwoordelijke?"
- vraag: "Moet ik een chatbot labelen als AI?"
- vraag: "Val ik onder de AI-verordening als ik alleen een AI-tool gebruik?"
- vraag: "Wat betekent de AI-verordening voor een ziekenhuis?"
  sector: zorg
- vraag: "Is een AI-triagesysteem in de zorg hoog risico?"
  sector: zorg
- vraag: "Mag de overheid AI gebruiken voor fraudedetectie?"
  sector: overheid
- vraag: "Wat moet een gemeente regelen voor de AI-verordening?"
  sector: overheid
- vraag: "Is AI-gebaseerde cv-selectie toegestaan onder de AI-verordening?"
  sector: hr
- vraag: "Mag ik AI gebruiken om sollicitanten te beoordelen?"
  sector: hr
- vraag: "Wat betekent de AI-verordening voor een bank of verzekeraar?"
  sector: financieel
- vraag: "Is AI-kredietscoring hoog risico?"
  sector: financieel
# ... vul aan tot ~24, gespreid over de clusters hierboven.
```

- [ ] **Step 5: Run the kandidaten-test + a dry-run smoke**

Run: `python -m pytest backend/tests/test_draft_vragen_kandidaten.py -v`
Expected: PASS.
Dry-run smoke (leest yaml + bestaande slugs; raakt de engine niet): `python scripts/draft_vragen.py --dry-run` — verwacht een lijst "zou draften: …" zonder te schrijven. (Vereist DB-verbinding voor de IngezondenVraag-query; als lokaal geen DB draait, noteer dat en vertrouw op de unit-test.)

- [ ] **Step 6: Commit**

```bash
git add scripts/draft_vragen.py scripts/vraag_kandidaten.yaml backend/tests/test_draft_vragen_kandidaten.py
git commit -m "feat(content): scaffolding-script + seed-kandidaten (redactionele gate)"
```

---

### Task 3: Frontend data-laag — sector + relatie-helpers

**Files:**
- Modify: `frontend/utils/vragen.ts`
- Create: `frontend/utils/sectoren.ts`, `frontend/content/sectoren/{zorg,overheid,hr,financieel}.md`
- Modify: enkele `frontend/content/vragen/*.md` (voeg `sector:` toe waar passend)

**Interfaces:**
- `Vraag` krijgt `sector?: string`.
- `vragenPerSector(sector: string): Vraag[]`, `alleSectoren(): string[]`, `gerelateerde(vraag: Vraag, max?: number): Vraag[]`.
- `utils/sectoren.ts`: `interface Sector { slug, naam, titel, beschrijving, introHtml }`; `alleSectoren()`, `vindSector(slug)`.

- [ ] **Step 1: Extend `utils/vragen.ts`**

In de `Vraag`-interface `sector?: string` toevoegen; in `parse()` `sector: fm.sector ? String(fm.sector) : undefined`. Voeg toe (na `alleVragen`):

```ts
export function vragenPerSector(sector: string): Vraag[] {
  return alleVragen().filter(v => v.sector === sector)
}

export function alleSectoren(): string[] {
  return [...new Set(alleVragen().map(v => v.sector).filter(Boolean) as string[])].sort()
}

// Hub-and-spoke: verwante vragen op gedeelde sector (zwaar) en gedeeld artikel
// (licht). Zo ziet Google (en de lezer) de samenhang binnen het onderwerp.
export function gerelateerde(vraag: Vraag, max = 4): Vraag[] {
  return alleVragen()
    .filter(v => v.slug !== vraag.slug)
    .map(v => ({
      v,
      score: (v.sector && v.sector === vraag.sector ? 2 : 0)
           + (v.artikel && v.artikel === vraag.artikel ? 1 : 0),
    }))
    .filter(x => x.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, max)
    .map(x => x.v)
}
```

- [ ] **Step 2: Create `utils/sectoren.ts`** (spiegel `utils/vragen.ts`)

```ts
// Sector-hubs: intro-content uit content/sectoren/*.md, zelfde build-time glob
// als de vragen. De vragenlijst per sector komt uit utils/vragen (vragenPerSector).
import { load as parseFrontmatter } from 'js-yaml'
import { marked } from 'marked'

export interface Sector {
  slug: string
  naam: string
  titel: string
  beschrijving: string
  introHtml: string
}

const bestanden = import.meta.glob('../content/sectoren/*.md', {
  query: '?raw', import: 'default', eager: true,
}) as Record<string, string>

function parse(pad: string, ruw: string): Sector {
  const slug = pad.split('/').pop()!.replace(/\.md$/, '')
  const m = ruw.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/)
  const fm = (m ? parseFrontmatter(m[1]) : {}) as Record<string, unknown>
  const body = (m ? m[2] : ruw).trim()
  return {
    slug,
    naam: String(fm.naam ?? slug),
    titel: String(fm.titel ?? fm.naam ?? slug),
    beschrijving: String(fm.beschrijving ?? ''),
    introHtml: marked.parse(body) as string,
  }
}

const _sectoren = Object.entries(bestanden).map(([p, r]) => parse(p, r))
  .sort((a, b) => a.naam.localeCompare(b.naam))

export function alleSectoren(): Sector[] { return _sectoren }
export function vindSector(slug: string): Sector | undefined {
  return _sectoren.find(s => s.slug === slug)
}
```

- [ ] **Step 3: Create the 4 sector-content files**

`frontend/content/sectoren/zorg.md` (en overheid/hr/financieel analoog), frontmatter + korte, gegronde intro. Voorbeeld:

```markdown
---
naam: "Zorg"
titel: "AI-verordening voor de zorg"
beschrijving: "Wat de EU AI-verordening (AI Act) betekent voor zorginstellingen: risicoclassificatie, hoog-risico-toepassingen en verplichtingen."
---
Zorginstellingen zetten AI in voor triage, diagnose-ondersteuning en administratie.
Veel van die toepassingen kunnen onder de **hoog-risico**-categorie van de
AI-verordening vallen (bijlage III). Hieronder de veelgestelde vragen voor de zorg,
elk met het wetsartikel erbij.
```

(Schrijf overheid/hr/financieel in dezelfde stijl; houd de intro's kort en gegrond, geen juridisch advies.)

- [ ] **Step 4: Tag bestaande vragen met een sector waar passend**

Voeg `sector:` toe aan de frontmatter van bestaande `content/vragen/*.md` die duidelijk bij een sector horen (bv. een werving-vraag → `hr`). Laat generieke vragen zónder sector. Dit vult de hubs met bestaande content.

- [ ] **Step 5: Verify (build)**

Run: `cd frontend && npm run build`
Expected: build slaagt (types kloppen: `sector?` optioneel, helpers compileren).

- [ ] **Step 6: Commit**

```bash
git add frontend/utils/vragen.ts frontend/utils/sectoren.ts frontend/content/sectoren/ frontend/content/vragen/
git commit -m "feat(seo): sector-taxonomie + relatie-helpers in de vragen-datalaag"
```

---

### Task 4: Sector-hubpagina's + interne links + sitemap

**Files:**
- Create: `frontend/pages/sector/[slug].vue`
- Modify: `frontend/pages/vraag/[slug].vue` (related-blok + kruimel), `frontend/nuxt.config.ts` (sitemap-hook)

**Interfaces:** consumeert `utils/sectoren.ts` + `utils/vragen.ts` (Task 3).

- [ ] **Step 1: Sector-hubpagina** `frontend/pages/sector/[slug].vue`

Spiegel `pages/vraag/[slug].vue`: haal `vindSector(slug)` (404 bij onbekend), `vragenPerSector(slug)`. `useSeoMeta({ title: sector.titel, description: sector.beschrijving })`. `useSchemaOrg([defineWebPage({ '@type': 'CollectionPage' })])`. Template: `<h1>{{ sector.titel }}</h1>`, intro `v-html="sector.introHtml"`, een `<ul>` met `<NuxtLink :to="/vraag/${v.slug}">{{ v.vraag }}</NuxtLink>` voor elke vraag, en een link naar `/vraag` + `/`. Bij lege lijst een nette "nog geen vragen"-tekst.

- [ ] **Step 2: Related-blok + kruimel op de vraagpagina**

In `pages/vraag/[slug].vue`: importeer `gerelateerde` (en `vindSector` voor de sectornaam). Bereken `const verwant = gerelateerde(vraag)`. In de template, ná het antwoord:
- als `vraag.sector`: een kruimel/teruglink boven of onder de titel: `<NuxtLink :to="/sector/${vraag.sector}">← AI-verordening voor {{ sectorNaam }}</NuxtLink>`.
- een `<section class="gerelateerd" v-if="verwant.length">` met `<h2>Gerelateerde vragen</h2>` + `<ul>` van `<NuxtLink :to="/vraag/${v.slug}">{{ v.vraag }}</NuxtLink>`.

Voeg géén nieuwe schema toe (QAPage blijft); dit zijn interne links.

- [ ] **Step 3: Sitemap-hook uitbreiden voor /sector**

In `frontend/nuxt.config.ts`, in de `nitro:build:public-assets`-hook waar `vraagRoutes` uit `content/vragen` worden gelezen, voeg analoog `sectorRoutes` uit `content/sectoren` toe (`/sector/<bestandsnaam-zonder-.md>`, `_`-bestanden overslaan) en neem ze mee in de `routes`-set voor de sitemap.

- [ ] **Step 4: Verify (build + preview-smoke)**

Run: `cd frontend && npm run build`
Expected: slaagt.
Smoke: `PORT=3199 node .output/server/index.mjs &` dan:
- `curl -s localhost:3199/sitemap.xml | grep -c '/sector/'` → ≥ 4.
- `curl -s localhost:3199/sector/zorg | grep -c 'gerelateerd\|<h1'` en de sectortitel aanwezig; render niet leeg.
- `curl -s localhost:3199/vraag/verplichtingen-hoog-risico-systeem` bevat "Gerelateerde vragen" (mits die vraag verwanten heeft na de sector-tagging).
Stop de server na de smoke.

- [ ] **Step 5: Commit**

```bash
git add frontend/pages/sector/ frontend/pages/vraag/[slug].vue frontend/nuxt.config.ts
git commit -m "feat(seo): sector-hubpagina's + gerelateerde-vragen-blok + sitemap"
```

---

## Self-Review (uitgevoerd)

- **Spec-dekking:** scaffolding-pure-logica (T1) · orchestrator + seed + idempotentie/dry-run (T2) · sector + relatie-helpers (T3) · hubs + interne links + sitemap (T4). Redactionele gate (`_concept/` onzichtbaar) in T1/T2 geborgd.
- **Placeholders:** de Vue-pagina's en sector-/seed-content zijn beschreven met exacte patronen + voorbeelden (geen kant-en-klare copy voor elk van de 24 seedvragen/4 sectorteksten — dat is redactioneel invulwerk binnen het gegeven format, bewust).
- **Type-consistentie:** `Vraag.sector?`, `vragenPerSector`/`alleSectoren`/`gerelateerde` en `Sector`/`vindSector` overal gelijk; script gebruikt `contentdraft.slug`/`render_concept`/`bestaat_al`/`corpusgat_regel` met dezelfde signaturen als T1.

## Uitrol

Frontend-only wijzigingen (hubs, links, sitemap) gaan mee met de gewone deploy. Het
scaffolding-script is een **lokale/ops-tool** — het draait niet in productie; de redacteur
draait het, redigeert de concepten en commit de gepubliceerde `/vraag`-pagina's. `_concept/`
blijft buiten de site (glob) en kan desgewenst in `.gitignore` of juist getrackt voor
samenwerking — keuze van de redacteur.
