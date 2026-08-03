<script setup lang="ts">
import { vindSector } from '~/utils/sectoren'
import { vragenPerSector } from '~/utils/vragen'

const route = useRoute()
const gevonden = vindSector(String(route.params.slug))
if (!gevonden) {
  // Onbekende slug → echte 404 (geen lege pagina die Google zou indexeren).
  throw createError({ statusCode: 404, statusMessage: 'Onbekende sector', fatal: true })
}
const sector = gevonden
const vragen = vragenPerSector(sector.slug)

useSeoMeta({
  title: sector.titel,
  description: sector.beschrijving,
})

// CollectionPage: dit is een verzamelpagina van vragen binnen één sector, geen
// los antwoord (dat is QAPage, zie pages/vraag/[slug].vue).
useSchemaOrg([
  defineWebPage({ '@type': 'CollectionPage' }),
])
</script>

<template>
  <article class="sector">
    <p class="kruimel"><NuxtLink to="/vraag">← Alle vragen</NuxtLink></p>
    <h1>{{ sector.titel }}</h1>
    <!-- Body komt uit onze eigen markdown-bron (redactioneel), geen invoer. -->
    <!-- eslint-disable-next-line vue/no-v-html -->
    <div class="intro" v-html="sector.introHtml" />

    <ul v-if="vragen.length" class="lijst">
      <li v-for="v in vragen" :key="v.slug">
        <NuxtLink :to="`/vraag/${v.slug}`">{{ v.vraag }}</NuxtLink>
      </li>
    </ul>
    <p v-else class="leeg">
      Nog geen vragen voor deze sector — die volgen binnenkort. Bekijk
      ondertussen <NuxtLink to="/vraag">alle vragen</NuxtLink>.
    </p>

    <p class="slot">
      <NuxtLink to="/">Stel je eigen vraag</NuxtLink> — het antwoord komt met het
      artikel erbij. Informatie, geen juridisch advies.
    </p>
  </article>
</template>

<style scoped>
.sector { max-width: 68ch; }
.kruimel { font-size: 14px; margin: 0 0 12px; }
.sector h1 {
  font-family: var(--font-citaat); font-weight: 400;
  font-size: 28px; margin: 0 0 16px;
}
.intro :deep(p) { margin: 0 0 12px; }
.lijst { margin: 8px 0 24px; padding: 0; list-style: none; }
.lijst li { padding: 12px 0; border-top: 1px solid var(--lijn); }
.leeg { margin: 8px 0 24px; opacity: 0.85; }
.slot { margin-top: 24px; }
</style>
