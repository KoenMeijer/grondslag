# Design-brief — AiActWijzer

Vastgesteld 19 jul 2026 (gekozen via visuele vergelijking: palet, letterparing en
citaat-paneel in drie varianten naast elkaar). Elke UI-taak verwijst naar dít
document — nooit "maak het modern en clean" prompten. De principes erachter
staan in `../CLAUDE.md` (Design-principes); dit is de concrete invulling.

## 1. Palet (tokens)

| Token | Hex | Gebruik |
| --- | --- | --- |
| `--inkt` | `#14213D` | Primaire tekst, vlakken, knoppen — het "nachtinkt"-blauw |
| `--papier` | `#FAFAF7` | Pagina-achtergrond |
| `--wit` | `#FFFFFF` | Kaarten en invoervlakken |
| `--lijn` | `#E2E4E3` | Randen en scheidingen |
| `--oker` | `#B98A2F` | Accentrand citaat-paneel, markering |
| `--oker-donker` | `#8A6A1F` | Artikelnummers, links, ref-verwijzingen (donkerder: contrast ≥ 4.5:1 op papier) |
| `--fout` | `#8C3A2E` | Alleen foutmeldingen |
| `--oker-licht` | `#F3EBD8` | Achtergrond van de korte citaat-highlight |
| `--citaat-tekst` | `#1F2937` | Tekstkleur van het wetscitaat (zachter dan `--inkt`) |

**Bewust géén stoplichtkleuren voor risicocategorieën.** "Hoog risico" staat in
woorden en citaten, niet in rood alarm — nuchterheid is het merk. Ook verboden:
EU-vlagblauw, paarse gradients, crème+terracotta, near-black+acid-green.

## 2. Typografie

- **UI: Public Sans** (400, 600) — nuchtere overheidsletter, geen Inter-sjabloon.
- **Citaten: Literata** (400, 600) — boekleesletter; de wettekst krijgt een eigen stem.
- Beide open source en **zelf gehost als woff2** — geen Google-CDN: de stack is
  zijn eigen AVG-verhaal.
- Basis 16px / regelafstand 1.55; **citaattekst 17px / 1.6** — de wettekst krijgt
  letterlijk meer ruimte dan de interface.
- Artikelnummers/labels: Public Sans 600, kapitaaltjes, letterspacing 0.08em.

## 3. Signatuur-element: het citaat-paneel ("ingetogen blok")

Het enige gebaar van het ontwerp; de rest is stil.

- Positie: naast het antwoord (desktop), eronder (mobiel).
- Per citaat een blok: **3px okerrand links** (`--oker`), achtergrond `--papier`,
  binnenmarge 12–14px, geen schaduw.
- Opbouw: artikelnummer als kopje (Public Sans kapitaaltjes, `--oker-donker`) →
  letterlijk wetsfragment (Literata) → bronregel klein en gedempt:
  `Verordening (EU) 2024/1689 · stand: juli 2026 · bekijk de bron`.
- Refs in het antwoord (`[Artikel 6, lid 2]`) zijn klikbaar in `--oker-donker`
  en scrollen naar / markeren het bijbehorende blok (korte highlight, daarna rust).
- De actualiteits-stempel ("stand: juli 2026") is altijd zichtbaar — dit is
  productprincipe 3, niet decoratie.

## 4. Verder discipline

- Radius **4px**, overal; geen pills.
- **Geen schaduwen**, geen gradients, geen glassmorphism.
- Animatie alleen functioneel: antwoord-streaming en de citaat-highlight. Niets beweegt zomaar.
- Veel wit, strak grid; nummering/tegels alleen waar de inhoud écht volgorde of
  meetwaarde is (een omnibus-tijdlijn mag, een 1-2-3-4-verkooppraatje niet).
- **Alleen lichte modus in v1** — donkere modus is een bewuste niet-nu.

## 5. Toon en copy

- Kalm, actief Nederlands: "Stel je vraag", "Bekijk de bron", "Dat kan ik niet
  beantwoorden op basis van mijn bronnen."
- Altijd zichtbaar: informatie, geen juridisch advies (productprincipe 2).
- **Verboden register:** countdown, boete-dreiging, urgentie, emoji,
  superlatieven, ✓-lijstjes, stat-tegels zonder echte meetwaarde.

## Herkomst van de keuzes

- Palet "Nachtinkt + oker" gekozen boven een warmer archief-palet (wetboekrood)
  en een koeler staal-palet (zegelgroen): strakst en formeelst, zonder EU-blauw.
- Letterparing gekozen boven IBM Plex Sans + Source Serif 4 (meer eigen karakter,
  minder publicatie-gevoel) en Source Sans 3 + STIX (wetenschappelijker).
- Citaat-paneel "ingetogen blok" gekozen boven "documentvel" en "gedrukte
  pagina": de durf zit in het paneel-concept (antwoord + letterlijke wettekst
  naast elkaar), niet in papier-imitatie.
