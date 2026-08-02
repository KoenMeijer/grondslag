<script setup lang="ts">
import { vindVraag } from '~/utils/vragen'

const route = useRoute()
const gevonden = vindVraag(String(route.params.slug))
if (!gevonden) {
  // Onbekende slug → echte 404 (geen lege pagina die Google zou indexeren).
  throw createError({ statusCode: 404, statusMessage: 'Onbekende vraag', fatal: true })
}
const vraag = gevonden

useSeoMeta({
  title: vraag.vraag,
  description: vraag.antwoordTekst.replace(/\s+/g, ' ').slice(0, 155),
})

// QAPage: dit ís de canonieke plek voor deze vraag, met de laatst-bijgewerkt-
// datum zodat de actualiteit (het onderscheidende punt) machine-leesbaar is.
useSchemaOrg([
  defineWebPage({ '@type': 'QAPage', dateModified: vraag.bijgewerkt }),
  defineQuestion({ name: vraag.vraag, acceptedAnswer: vraag.antwoordTekst }),
])
</script>

<template>
  <article class="vraag">
    <p class="kruimel"><NuxtLink to="/vraag">← Alle vragen</NuxtLink></p>
    <h1>{{ vraag.vraag }}</h1>
    <!-- Body komt uit onze eigen markdown-bron (redactioneel), geen invoer. -->
    <!-- eslint-disable-next-line vue/no-v-html -->
    <div class="antwoord" v-html="vraag.antwoordHtml" />
    <p class="grond">
      Gegrond op {{ vraag.artikel }}<span v-if="vraag.standWetgeving"> · stand van wetgeving: {{ vraag.standWetgeving }}</span>
    </p>
    <p v-if="vraag.bijgewerkt" class="meta">Bijgewerkt: {{ vraag.bijgewerkt }}</p>
    <p class="slot">
      <NuxtLink to="/">Stel je eigen vraag</NuxtLink> — het antwoord komt met het
      artikel erbij. Informatie, geen juridisch advies.
    </p>
  </article>
</template>

<style scoped>
.vraag { max-width: 68ch; }
.kruimel { font-size: 14px; margin: 0 0 12px; }
.vraag h1 {
  font-family: var(--font-citaat); font-weight: 400;
  font-size: 26px; margin: 0 0 16px;
}
.antwoord :deep(p) { margin: 0 0 12px; }
.grond {
  margin: 20px 0 4px; font-size: 14px;
  color: var(--oker-donker); font-weight: 600;
}
.meta { margin: 0 0 20px; font-size: 13px; opacity: 0.75; }
.slot { margin-top: 24px; }
</style>
