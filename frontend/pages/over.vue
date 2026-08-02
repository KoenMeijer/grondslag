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
useSeoMeta({
  title: 'Over de AI-verordening',
  description: 'Waarom de AI-verordening bestaat, wie haar heeft vastgesteld en welke evaluatiemomenten er nog komen — met citaten uit de wettekst.',
  ogImage: 'https://grondslag.eu/og/over.png',
  ogImageAlt: 'Grondslag — Over de AI-verordening',
})

// Veelgestelde vragen: één bron voor de zichtbare tekst én de FAQPage-JSON-LD,
// zodat schema en pagina niet uiteenlopen (Google eist dat de FAQ ook echt op
// de pagina staat). Redactioneel gegrond; artikel-/bijlageverwijzing in elk
// antwoord. Informatie, geen juridisch advies (zie de disclaimer in de footer).
const faq = [
  {
    slug: 'valt-mijn-ai-systeem-onder-de-ai-verordening',
    v: 'Valt mijn AI-systeem onder de AI-verordening?',
    a: 'De verordening werkt risicogebaseerd: elk systeem valt in één van vier categorieën — verboden, hoog-risico, beperkt risico met een transparantieplicht, of minimaal risico. De meeste systemen zijn beperkt of minimaal en kennen alleen lichte verplichtingen; de zware eisen gelden bij hoog-risico. De classificatie loopt via artikel 6 en bijlage III.',
  },
  {
    slug: 'wanneer-gaan-de-verplichtingen-in',
    v: 'Wanneer gaan de verplichtingen in — klopt 2 augustus 2026 nog?',
    a: 'Deels gelden ze al: verboden praktijken sinds 2 februari 2025 en de regels voor AI voor algemene doeleinden (GPAI) sinds 2 augustus 2025. De hoog-risico-verplichtingen zijn na de Digital Omnibus verschoven van 2 augustus 2026 naar 2 december 2027 en 2 augustus 2028 — veel bronnen noemen nog de oude datum.',
  },
  {
    slug: 'welke-ai-praktijken-zijn-verboden',
    v: 'Welke AI-praktijken zijn verboden?',
    a: 'Artikel 5 verbiedt onder meer social scoring door overheden, manipulatie die schade veroorzaakt, emotieherkenning op de werkvloer en in het onderwijs, en real-time biometrische identificatie in de openbare ruimte, met beperkte uitzonderingen.',
  },
  {
    slug: 'wanneer-is-een-ai-systeem-hoog-risico',
    v: 'Wanneer is een AI-systeem "hoog-risico"?',
    a: 'Er zijn twee routes: het systeem is een veiligheidscomponent van een gereguleerd product (bijlage I), of het valt onder een gebruik uit bijlage III — zoals werving en cv-screening, onderwijs, kritieke infrastructuur of rechtshandhaving. De regel staat in artikel 6.',
  },
  {
    slug: 'verplichtingen-hoog-risico-systeem',
    v: 'Welke verplichtingen gelden bij een hoog-risico-systeem?',
    a: 'Onder andere een risicomanagementsysteem, eisen aan datakwaliteit, technische documentatie, logging, betekenisvol menselijk toezicht en een conformiteitsbeoordeling met CE-markering vóór ingebruikname. Deze eisen staan in de artikelen 8 tot en met 17.',
  },
  {
    slug: 'moet-ik-vertellen-dat-het-ai-is',
    v: 'Moet ik gebruikers vertellen dat ze met AI praten?',
    a: 'Ja. Voor systemen die met mensen interacteren, zoals chatbots, en voor AI-gegenereerde of gemanipuleerde content zoals deepfakes geldt een transparantieplicht: de gebruiker moet weten dat het om AI gaat. Dat staat in artikel 50.',
  },
]

useSchemaOrg([
  defineWebPage({ '@type': 'FAQPage' }),
  ...faq.map(f => defineQuestion({ name: f.v, acceptedAnswer: f.a })),
])
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
        wetgeving. Een overzicht van alle verplichtingen met hun actuele data
        staat op de pagina <NuxtLink to="/deadlines">deadlines</NuxtLink>.
      </p>
    </section>

    <section class="faq">
      <h2>Veelgestelde vragen</h2>
      <div v-for="item in faq" :key="item.slug" class="vraag">
        <h3><NuxtLink :to="`/vraag/${item.slug}`">{{ item.v }}</NuxtLink></h3>
        <p>{{ item.a }}</p>
      </div>
      <p class="alle"><NuxtLink to="/vraag">Alle vragen over de AI-verordening →</NuxtLink></p>
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
.faq .vraag { padding: 14px 0; border-top: 1px solid var(--lijn); }
.faq h3 { font-size: 15px; font-weight: 600; margin: 0 0 4px; }
.slot { margin-top: 28px; }
</style>
