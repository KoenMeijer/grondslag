<script setup lang="ts">
import dataset from '~/data/deadlines.json'

useSeoMeta({
  title: 'Deadlines van de AI-verordening',
  description: dataset.beschrijving,
})

// schema.org Dataset: maakt de deadline-tabel een citeerbare, machine-leesbare
// bron met verwijzing naar de CSV/JSON-downloads. nuxt-schema-org heeft geen
// Dataset-helper, dus als losse JSON-LD via useHead.
const ld = {
  '@context': 'https://schema.org',
  '@type': 'Dataset',
  name: dataset.naam,
  description: dataset.beschrijving,
  url: 'https://grondslag.eu/deadlines',
  dateModified: dataset.bijgewerkt,
  creator: { '@type': 'Organization', name: 'Grondslag', url: 'https://grondslag.eu' },
  license: dataset.licentie,
  isBasedOn: dataset.bron,
  distribution: [
    { '@type': 'DataDownload', encodingFormat: 'text/csv', contentUrl: 'https://grondslag.eu/deadlines.csv' },
    { '@type': 'DataDownload', encodingFormat: 'application/json', contentUrl: 'https://grondslag.eu/deadlines.json' },
  ],
}
useHead({ script: [{ type: 'application/ld+json', innerHTML: JSON.stringify(ld) }] })

function toonDatum(d: string) {
  return new Date(`${d}T00:00:00Z`).toLocaleDateString('nl-NL', {
    day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC',
  })
}
</script>

<template>
  <article class="deadlines">
    <h1>Deadlines van de AI-verordening</h1>
    <p class="intro">
      {{ dataset.beschrijving }} Stand van wetgeving: {{ dataset.standWetgeving }}.
    </p>
    <p class="ombuiging">
      Zoek je de datum <strong>2 augustus 2026</strong>? Die is achterhaald:
      <NuxtLink to="/vraag/gaat-de-ai-verordening-in-op-2-augustus-2026">lees wat er
      door de Digital Omnibus verschoof en wat nu geldt</NuxtLink>.
    </p>
    <p class="download">
      Download de data: <a href="/deadlines.json">JSON</a> · <a href="/deadlines.csv">CSV</a>
      <span class="licentie"> · vrij te gebruiken met bronvermelding (CC&nbsp;BY&nbsp;4.0)</span>
    </p>

    <div class="tabelwrap">
      <table>
        <thead>
          <tr><th>Fase</th><th>Artikel</th><th>Deadline</th></tr>
        </thead>
        <tbody>
          <tr v-for="m in dataset.mijlpalen" :key="m.fase">
            <td>
              <strong>{{ m.fase }}</strong>
              <span class="wat">{{ m.verplichting }}</span>
            </td>
            <td class="art">{{ m.artikel }}</td>
            <td class="datum">
              <span :class="m.status === 'van kracht' ? 'vankracht' : 'komt'">{{ toonDatum(m.datum) }}</span>
              <span v-if="m.was" class="was">was {{ toonDatum(m.was) }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <p class="disclaimer">
      Informatie, geen juridisch advies. Bron:
      <a :href="dataset.bron" target="_blank" rel="noopener">Verordening (EU) 2024/1689 op EUR-Lex</a>,
      met de deadlineverschuivingen na de Digital Omnibus.
    </p>
    <p class="slot">
      <NuxtLink to="/vraag">Bekijk de veelgestelde vragen</NuxtLink> of
      <NuxtLink to="/">stel je eigen vraag</NuxtLink> — het antwoord komt met het artikel erbij.
    </p>
  </article>
</template>

<style scoped>
.deadlines { max-width: 76ch; }
.deadlines h1 {
  font-family: var(--font-citaat); font-weight: 400;
  font-size: 28px; margin: 0 0 16px;
}
.intro { margin: 0 0 8px; opacity: 0.85; }
.download { margin: 0 0 20px; font-size: 14px; }
.licentie { opacity: 0.7; }
.tabelwrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 15px; }
th, td { text-align: left; padding: 12px 10px; border-top: 1px solid var(--lijn); vertical-align: top; }
th { font-size: 13px; opacity: 0.7; font-weight: 600; }
.wat { display: block; margin-top: 4px; font-size: 13px; opacity: 0.8; }
.art { white-space: nowrap; }
.datum { white-space: nowrap; }
.vankracht { color: var(--oker-donker); font-weight: 600; }
.komt { font-weight: 600; }
.was { display: block; font-size: 12px; opacity: 0.65; text-decoration: line-through; }
.disclaimer { margin: 24px 0 0; font-size: 13px; opacity: 0.8; }
.slot { margin-top: 16px; }
</style>
