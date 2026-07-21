// Eén plek voor de bron-constanten die op meerdere pagina's terugkomen.
//
// STAND_WETGEVING: handmatig gelijk houden met de corpus-frontmatter
// (corpus/*/digital-omnibus-tijdlijn.md, veld stand-wetgeving). Bewuste keuze:
// een backend-endpoint alleen hiervoor is zwaarder dan dit ene onderhoudspunt;
// corpus-update = ook deze constante bijwerken (zie docs/deploy.md).
export const STAND_WETGEVING = 'juli 2026'

export const EURLEX_URL = 'https://eur-lex.europa.eu/legal-content/NL/TXT/?uri=CELEX:32024R1689'

export const BRON_VERORDENING = 'Verordening (EU) 2024/1689'
