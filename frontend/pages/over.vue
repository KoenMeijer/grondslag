<script setup lang="ts">
// Redactionele context, maar gegrond zoals alles hier: elke sectie leunt op
// een citaat uit de verordening zelf. Datums alleen als ze in het corpus
// staan (12 juli 2024 = publicatiedatum uit de corpus-frontmatter; de
// UAIV-stand komt uit corpus/nl-guidance/uaiv-toezicht.md).

// Artikel 1, lid 1 — integraal: dit ís het waarom, in één zin van de wetgever.
const ART1 =
  'Deze verordening heeft tot doel de werking van de interne markt te ' +
  'verbeteren en de toepassing van mensgerichte en betrouwbare artificiële ' +
  'intelligentie (AI) te bevorderen, en tegelijkertijd een hoog niveau van ' +
  'bescherming van de gezondheid, de veiligheid en de in het Handvest ' +
  'verankerde grondrechten te waarborgen, met inbegrip van de democratie, de ' +
  'rechtsstaat en de bescherming van het milieu, tegen de schadelijke ' +
  'gevolgen van AI-systemen in de Unie, en innovatie te ondersteunen.'

const ART112 =
  'Uiterlijk op 2 augustus 2028 en vervolgens om de vier jaar verricht de ' +
  'Commissie een evaluatie en brengt zij verslag uit bij het Europees ' +
  'Parlement en de Raad […]'
useHead({
  title: 'Over de AI-verordening · Grondslag',
  meta: [{ name: 'description', content: 'Waarom de AI-verordening bestaat, wie haar heeft vastgesteld en welke evaluatiemomenten er nog komen — met citaten uit de wettekst.' }],
})
</script>

<template>
  <article class="over">
    <h1>Over de AI-verordening</h1>

    <section>
      <h2>Waarom deze wet bestaat</h2>
      <p>
        AI-systemen worden in vrijwel elke sector gebruikt en circuleren
        moeiteloos over grenzen. Als elke lidstaat eigen regels zou stellen,
        versnippert de interne markt en weet niemand meer waar hij aan toe is
        (overweging 3). De Unie koos daarom voor één uniform kader, met een
        dubbel doel — bescherming én ruimte voor innovatie. De wetgever zegt
        het zelf zo:
      </p>
      <WetCitaat artnr="Artikel 1, lid 1" :tekst="ART1" />
    </section>

    <section>
      <h2>Wie de regels heeft gemaakt</h2>
      <p>
        De verordening is vastgesteld door het Europees Parlement en de Raad
        van de Europese Unie en op 12 juli 2024 gepubliceerd in het
        Publicatieblad. Het is een <em>verordening</em>, geen richtlijn: de
        regels gelden rechtstreeks in alle lidstaten, zonder nationale
        omzettingswet. Nederland regelt alleen het toezicht en de handhaving
        zelf, via de Uitvoeringswet AI-verordening (UAIV). Die wet is er nog
        niet — de internetconsultatie sloot in juni 2026 en het voorstel moet
        nog naar de Tweede Kamer. Beoogd wordt het toezicht te beleggen bij
        bestaande toezichthouders, met een coördinerende rol voor de
        Autoriteit Persoonsgegevens.
      </p>
    </section>

    <section>
      <h2>Wat er nog komt</h2>
      <p>
        De verplichtingen treden gefaseerd in werking — de tijdlijn staat op
        de <NuxtLink to="/">beginpagina</NuxtLink>. En de wet is uitdrukkelijk
        niet af: de Commissie beoordeelt jaarlijks of de lijst met verboden
        praktijken en de hoog-risicolijst van bijlage III bijstelling nodig
        hebben, en evalueert de hele verordening op vaste momenten:
      </p>
      <WetCitaat artnr="Artikel 112, lid 2" :tekst="ART112" />
      <p>
        Dat het kader beweegt is geen theorie: de Digital Omnibus verschoof in
        2026 al deadlines die online nog volop in hun oude vorm rondzingen.
        Daarom draagt elk antwoord hier een stempel met de stand van de
        wetgeving.
      </p>
    </section>

    <p class="slot">
      Wat dit voor jouw organisatie betekent, hangt af van wat je bouwt of
      gebruikt. <NuxtLink to="/">Stel je vraag</NuxtLink> — het antwoord komt
      met het artikel erbij.
    </p>
  </article>
</template>

<style scoped>
.over { max-width: 68ch; }
.over h1 {
  font-family: var(--font-citaat); font-weight: 400;
  font-size: 28px; margin: 0 0 20px;
}
.over h2 { font-size: 17px; margin: 28px 0 6px; }
.over p { margin: 0 0 12px; }
.slot { margin-top: 28px; }
</style>
