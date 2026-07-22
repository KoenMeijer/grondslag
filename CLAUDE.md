# CLAUDE.md — AiActWijzer

## Wat is dit

Self-hosted assistent die vragen over de **EU AI Act** beantwoordt, gegrond in de
wettekst + NL-doorwerking. Kernvraag van de gebruiker: *"wij bouwen/gebruiken X —
valt dat onder de AI Act, welke risicocategorie, welke verplichtingen, welke deadline?"*

De RAG- en eval-aanpak staan zelfstandig in dit project: `docs/rag-aanpak.md` en
`docs/eval-aanpak.md`. Privécontext (persoonlijke doelen, concurrentie-analyse,
infradetails) staat in het niet-getrackte `CLAUDE.local.md` — deze repo is
publiek, dus houd die scheiding aan bij nieuwe notities.

- **Naam:** **Grondslag** (gekozen 21 jul 2026; woordspeling juridische grondslag ↔
  RAG-grounding). Domein: **grondslag.eu** — `.eu` past bij de EU-verordening + soevereine
  stack. **Geregistreerd en live op https://grondslag.eu** (21 jul 2026; ook
  `www.grondslag.eu`). Een subdomein van een ander project draaide als eerste livegang
  en loopt nog mee zodat eerder gedeelde links blijven werken — omzetten naar één
  canonieke naam is stap 4 in
  `docs/deploy.md`. *AiActWijzer* was de werknaam en leunde op de Engelse term; in de
  copy hanteren we consequent "AI-verordening (AI Act)". De codebase draagt nog
  grotendeels de oude naam — hernoemen is een aparte actie.
- **Eerste oplever (2–3 avonden):** wettekst indexeren + 10 golden-set-vragen met
  grounding-eval. **Gerealiseerd 19 jul 2026**; na de retrieval-experimenten
  (artikel 3-splitsing, hybride zoeken 1.5:1) staat de eval op **retrieval 8/14,
  grounding 9/14, abstentie 14/14** (21 jul 2026; de set groeide van 10 naar 14
  cases met de UAIV-nulmeting — de vier NL-cases falen alle vier op retrieval,
  dus de daling is nieuw meetbereik, geen achteruitgang) — knoppen in de
  README; de memorisatie-les (golden-vraag nooit letterlijk in het corpus)
  staat in docs/eval-aanpak.md.
- **Publiek moment:** demo + LinkedIn-post.
- **Privacy-grens:** alles op publieke data (wetgeving); géén privé-/vastgoeddata.

## Waarom interessant voor organisaties (de pitch)

1. **Verplichtingen komen eraan, niemand weet wat voor hén geldt** — risicoclassificatie
   is de kernvraag en het antwoord staat verspreid over verordening, bijlagen en NL-guidance.
2. **Rondzwervende info is massaal verouderd** — de Digital Omnibus (jul 2026) schoof de
   hoog-risico-deadline van 2 aug 2026 naar 2 dec 2027 / 2 aug 2028; veel bronnen online,
   inclusief bestaande AI Act-tools, noemen nog de oude datum. Actualiteit is direct
   onderscheidend.
3. **Triage-tool, geen juristvervanger** — laat zien wélke vragen naar de advocaat moeten;
   verlaagt kosten en ontdooit stilliggende AI-projecten.
4. **Self-hosted** — juist de doelgroep met de meeste AI Act-vragen (overheid, zorg,
   financieel) wil die vragen niet in een Amerikaanse cloud-chatbot typen.
5. **Controleerbaar** — grounding met citaat + artikelnummer maakt elk antwoord herleidbaar;
   bij juridische vragen de voorwaarde voor vertrouwen.

In één zin: *organisaties willen AI adopteren maar durven niet, omdat niemand precies weet
wat de AI Act voor hun situatie betekent en de informatie online verouderd of
Amerikaans-generiek is; deze tool geeft gegronde, actuele, controleerbare antwoorden —
op een stack die zelf AVG-proof is.*

## Positionering

Bestaande AI Act-tools werken vaak als statische beslisboom met een rapport per
e-mail, zonder bronverwijzing en zonder NL-doorwerking. Wij onderscheiden ons met:
vrije vragen + doorvragen, citaten uit de wettekst, actuele omnibus-tijdlijn,
NL-toezicht (UAIV), self-hosted. **Wel van leren:** een beslisboom dwingt
volledigheid af — evt. latere iteratie: kort gestructureerd intake-moment dat de
RAG-context voedt, daarna vrij doorvragen. Uitgewerkte concurrentie-analyse:
`CLAUDE.local.md`.

## Product- en governance-principes

1. **De tool valt zélf onder de AI Act — en is zijn eigen schoolvoorbeeld.**
   Als AI-systeem geldt minimaal de art. 50-transparantieplicht (gebruiker weet dat
   hij met AI praat). Practice what you preach: transparantie-pagina, model card
   (welk model, herkomst/hosting), eigen risicoclassificatie gedocumenteerd in de repo.
   Dit is tegelijk het portfolio-verhaal.
2. **Informatie, geen juridisch advies.** Vastgelegd als productprincipe: in de copy,
   in het abstentie-gedrag (doorverwijzen bij advies-vragen) en straks in de
   voorwaarden van een publieke demo. Antwoorden zijn een startpunt voor de eigen
   jurist, geen vervanging.
3. **Corpusbeheer en actualiteits-stempel.** Corpus = geconsolideerde wettekst
   (EUR-Lex, verordening 2024/1689 incl. Digital Omnibus) + geselecteerde NL-guidance;
   elke bron met versie/datum geadministreerd. Elk antwoord draagt een stempel
   ("stand van wetgeving: <maand jaar>"). Wijziging in wet/guidance = corpus-update
   + eval-run — anders veroudert deze tool net zo stil als de concurrentie.
4. **Privacy van gebruikersvragen.** Bij een door ons gehoste demo: geen of minimale,
   geanonimiseerde logging, korte retentie, en dit benoemd op de transparantie-pagina.
   Vragen worden nooit trainings- of evaldata zonder dat expliciet te melden.
   → Ingevuld (22 jul 2026): nginx `access_log off`, en gebruikscijfers als
   dagtellers zonder IP, cookie of vraagtekst (`backend/app/tellen.py`). Geen
   bewaartermijn nodig omdat er geen persoonsgegevens in zitten. Wie hier iets
   aan wijzigt, past ook `/transparantie` aan — die pagina doet de belofte.
5. **Licentie en kanaal.** Open source onder **MIT** (`LICENSE`); gepubliceerd op
   **github.com/KoenMeijer/grondslag** via een push-mirror vanaf GitLab, waar CI
   en deploy naar Hetzner blijven draaien. Privécontext hoort in het
   niet-getrackte `CLAUDE.local.md`, niet hier.

## Scope v1 (wat er wél en níet in zit)

**Wél:** vraag-antwoord met citaten (artikelnummer + fragment), golden set + eval-suite,
actualiteits-stempel, transparantie-pagina. **Stand 19 jul 2026: dit alles is
functioneel compleet** (bouwsteen 1 backend + bouwsteen 2 frontend met citaat-paneel).
**Live sinds 21 jul 2026 op https://grondslag.eu** (GitLab CI → Hetzner,
TLS via certbot, corpus geïndexeerd); nog niet gedaan: het publieke moment.
**Níet:** accounts, intake-beslisboom (bewust "later", zie de positionering
hierboven), betaalfunctie, andere wetgeving dan de AI Act.
Uitbreiden mag pas als v1 af is en de eval-suite groen — uitzondering (21 jul 2026,
expliciet akkoord): statische, gegronde content die de RAG-keten niet raakt, zoals
de pagina "Over de AI-verordening" (elke sectie leunt op een wetscitaat; de
stand-constante in `frontend/utils/bron.ts` beweegt mee met corpus-updates).

## Design-principes (anti-AI-sjabloon)

Het "AI-gegenereerde" gevoel zit in generiekheid: bouwstenen en copy die op elk onderwerp
passen (countdown, stat-tegels, ✓-lijstjes, 1-2-3-4-stappen, urgentie-teksten). Daarom:

1. **De wettekst draagt het ontwerp.** Signatuur-element = het **gegronde citaat-paneel**:
   antwoord met daarnaast het letterlijke wetsfragment, vormgegeven als document
   (artikelnummer als kopje, eigen letter voor het citaat, bronregel
   "Verordening 2024/1689, art. 6 lid 2"). Vorm en USP vallen samen.
2. **Copy nuchter.** Kalm, actief Nederlands ("Stel je vraag", "Bekijk de bron").
   Geen countdown, boete-dreiging, emoji, superlatieven of verkoop-register.
3. **Structuur codeert betekenis.** Nummering/tegels alleen waar de inhoud écht een
   volgorde of meetwaarde is. Een deadline-tijdlijn (omnibus) is wél gerechtvaardigd.
4. **Bewust afwijken van stack-defaults.** @nuxt/ui-defaults (Inter-achtig, standaard
   radius/kleur) lezen als sjabloon. Vermijd AI-clichés: crème+terracotta+serif,
   near-black+acid-green, paarse gradients, glassmorphism — en ook EU-vlagblauw.
   Richting: eigen donker "inkt"-blauw + papier-wit, alsof uit een gedrukte verordening.
5. **Eén gebaar, verder discipline.** Durf zit in het citaat-paneel; de rest stil:
   veel wit, strak grid, minimale animatie.
6. **Design-tokens vóór het bouwen vastleggen** (palet als hex-tokens, twee lettertypen,
   signatuur-element, toon) en elke UI-taak daarnaar laten verwijzen — nooit "maak het
   modern en clean" prompten. → Vastgelegd in `docs/design-brief.md` (19 jul 2026):
   nachtinkt `#14213D` + papier `#FAFAF7` + oker-accent, Public Sans + Literata
   (zelf gehost), citaat-paneel als ingetogen blok.

## Stack

Zelfde stack als mijn andere projecten (zie `CLAUDE.local.md`), zodat patronen en
tooling herbruikbaar zijn: **FastAPI + SQLAlchemy + Postgres · Nuxt 3 + Pinia ·
Docker/Docker Compose · GitLab CI → Hetzner**. Afwijking daarvan: géén
@nuxt/ui maar kale Nuxt + eigen CSS op de design-tokens (keuze 19 jul 2026 — de
design-brief eist juist afwijken van de library-defaults; heroverwegen als de UI groeit). AI-laag soeverein/EU (AVG): pgvector voor
embeddings, Ollama en/of Mistral (EU) als model — voor v1 gekozen: Mistral API
(`mistral-embed` + `mistral-small-latest`), zie het goedgekeurde ontwerp in
`docs/superpowers/specs/2026-07-19-eerste-bouwsteen-design.md`. Details: `docs/rag-aanpak.md`.
Eval-driven vanaf dag 1: golden set + retrieval-/grounding-/abstentie-metrics —
zie `docs/eval-aanpak.md` (later te generaliseren in referentieproject 2).

## Werkafspraken

- **Communiceer in het Nederlands**; code-comments ook in het Nederlands, en leg het
  *waarom* uit, niet het *wat*.
- **Leg bij elke fix/keuze het waarom uit** — de oorzaak begrijpen weegt zwaarder dan
  snel een werkende oplossing.
- **Scope-discipline:** doe precies wat gevraagd is, geen ongevraagde extra
  features/UI/links; bevestig bij twijfel.
- **Test/verifieer vóór "klaar":** lokaal `pytest` / `npm run lint` waar van toepassing,
  en controleer het resultaat echt. Bij dit project extra: de eval-suite
  (`docs/eval-aanpak.md`) draait mee bij elke RAG-/prompt-/modelwijziging.
- **Bevestig vóór onomkeerbare of risicovolle acties** (verwijderen, overschrijven,
  externe/publieke acties); maak waar zinvol eerst een backup. Nooit automatisch
  naar productie pushen.
- **Behandel feedback/observaties (screenshots, productie) als waarheid** en
  heronderzoek, in plaats van het vorige antwoord te verdedigen.
- **Wees kort en direct**; geef een aanbeveling i.p.v. een lange optie-opsomming.
- **Contextonderhoud:** na elke commit checken of dit bestand nog klopt
  (afgedwongen via de hook in `.claude/settings.json`).
- **Specifiek voor dit project:** publieke data only (wetgeving/guidance, geen
  privédata); naam is nog niet definitief.
