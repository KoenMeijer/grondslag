# Beginscherm-herziening — ontwerp

Goedgekeurd 21 jul 2026 (brainstorm in sessie). Bouwt voort op
`docs/design-brief.md`; tokens en verboden blijven onverkort gelden.

## Diagnose

De tokens zijn goed, maar de compositie van het eerste scherm is het
AI-sjabloon dat de brief wil vermijden: kop + alinea + leeg formulier, het
signatuur-element (citaat-paneel, Literata) onzichtbaar tot ná de eerste
vraag, header/footer als standaard SaaS-balken, citaat-paneel verpakt in een
generieke witte kaart. Naam toont nog de werknaam AiActWijzer.

## Kernidee

**Het lege beginscherm toont alvast wat de tool maakt.** De rechterkolom is
de vaste "bronnen-plek": in de begintoestand een écht citaatblok met
artikel 50, lid 1 (transparantieplicht — de tool als eigen schoolvoorbeeld,
governance-principe 1) plus de omnibus-tijdlijn; tijdens het zoeken een kalme
statusregel; na een antwoord de echte bronnen. De bezoeker ziet het
antwoord-formaat vóór hij iets vraagt.

## Wijzigingen

1. **Paginalayout (`pages/index.vue`)**: één grid `1.1fr 1fr` vanaf het
   begin. Links: intro + formulier + (na antwoord) het antwoord. Rechts:
   begintoestand → status → citaat-paneel. Mobiel (<760px): één kolom.
2. **Hero-typografie**: kop in Literata, `clamp(28px, 4vw, 38px)` — de stem
   van de wet als eerste indruk (het ene bewuste risico).
3. **Beginpaneel (nieuw component `BeginPaneel.vue`)**:
   - Citaatblok art. 50 lid 1 (ingekort fragment, EUR-Lex-link), zelfde vorm
     als `CitaatBlok`.
   - Omnibus-tijdlijn als wetsregels: datum als kantlijnlabel (kapitaaltjes
     oker), gebeurtenis als tekst. Géén infographic/bolletjes. Data uit het
     corpus (art. 113 + digital-omnibus-tijdlijn.md): 2 feb 2025 verboden
     praktijken · 2 aug 2025 GPAI · 2 aug 2026 algemene toepassing ·
     2 dec 2027 hoog risico bijlage III (was 2 aug 2026 — expliciet genoemd,
     dít is de actualiteits-USP) · 2 aug 2028 hoog risico in producten.
   - Actualiteits-stempel "stand: juli 2026" als één frontend-constante met
     verwijzing naar de corpus-frontmatter. Bewuste keuze: hardcoden is een
     onderhoudspunt, maar een backend-endpoint alleen hiervoor is zwaarder;
     corpus-update = ook deze constante bijwerken (staat in deploy.md-flow).
4. **Wachtervaring**: bij `store.bezig` toont de rechterkolom "Zoeken in de
   wettekst…" (labelstijl). Geen animatie — de brief staat alleen functionele
   animatie toe en de knoptekst beweegt al mee.
5. **Citaat-paneel zonder kaart (`CitaatPaneel.vue`)**: witte kaart + rand
   weg; blokken direct op papier, "Bronnen" als kantlijnlabel.
6. **Header/footer (`layouts/default.vue`)**: wit vlak weg (papier loopt
   door), merk **Grondslag** in Literata 600, dunne lijnen; footer-copy op
   naam Grondslag.
7. **Naamvoering**: `nuxt.config.ts` title/description → Grondslag;
   codebase-hernoeming blijft een aparte actie (CLAUDE.md).

## Buiten scope

Streaming (backend), donkere modus, intake, hernoeming van mappen/repo.

## Verificatie

`npm run lint` + `npm run test` (nieuwe tests: BeginPaneel-inhoud,
kolom-wissel op de pagina, CitaatBlok-stempel zonder resultaat); visueel op
de dev-server tegen de live API, inclusief smal venster.
