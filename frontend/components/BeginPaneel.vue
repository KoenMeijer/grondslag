<script setup lang="ts">
// Begintoestand van de bronnen-kolom: laat zien wát de tool maakt vóór er
// iets gevraagd is. Artikel 50 is bewust gekozen — de transparantieplicht
// waar deze tool zélf onder valt (governance-principe 1, eigen schoolvoorbeeld).

// Ingekort naar de kernzin; het volledige lid staat één klik verder op EUR-Lex.
const ART50 =
  'Aanbieders zorgen ervoor dat AI-systemen die voor directe interactie met ' +
  'natuurlijke personen zijn bedoeld, zodanig worden ontworpen en ontwikkeld ' +
  'dat de betrokken natuurlijke personen worden geïnformeerd dat zij ' +
  'interageren met een AI-systeem […]'

// Uit het corpus: artikel 113 + de Digital Omnibus-verschuivingen. De
// vervallen datum staat er expliciet bij — het internet noemt massaal nog
// 2 augustus 2026, en dát corrigeren is de bestaansreden van deze tool.
const TIJDLIJN = [
  { datum: '2 feb 2025', tekst: 'Verboden praktijken van toepassing (art. 5)' },
  { datum: '2 aug 2025', tekst: 'Regels voor AI-modellen voor algemene doeleinden (GPAI)' },
  { datum: '2 aug 2026', tekst: 'Algemene toepassing van de verordening' },
  { datum: '2 dec 2027', tekst: 'Hoog risico, bijlage III — verschoven door de Digital Omnibus (was: 2 augustus 2026)' },
  { datum: '2 aug 2028', tekst: 'Hoog risico in gereguleerde producten (art. 6, lid 1)' },
]
</script>

<template>
  <aside class="beginpaneel" aria-label="Voorbeeld uit de wettekst en tijdlijn">
    <h2 class="label">Zo antwoordt Grondslag</h2>
    <WetCitaat artnr="Artikel 50, lid 1" :tekst="ART50" />
    <p class="toelichting">
      Deze transparantieplicht geldt ook voor deze tool: je praat hier met AI.
    </p>

    <h2 class="label tijdlijnkop">Deadlines na de Digital Omnibus</h2>
    <dl class="tijdlijn">
      <template v-for="regel in TIJDLIJN" :key="regel.datum">
        <dt class="label">{{ regel.datum }}</dt>
        <dd>{{ regel.tekst }}</dd>
      </template>
    </dl>
  </aside>
</template>

<style scoped>
.beginpaneel h2 { margin: 0 0 12px; }
.toelichting { font-size: 13px; opacity: 0.75; margin: 8px 0 28px; }

.tijdlijnkop { margin-top: 0; }
.tijdlijn { margin: 0; }
/* Wetsregels, geen infographic: datum als kantlijnlabel, gebeurtenis als tekst. */
.tijdlijn dt { float: left; clear: left; width: 88px; padding-top: 2px; }
.tijdlijn dd { margin: 0 0 10px 100px; font-size: 14.5px; line-height: 1.5; }
</style>
