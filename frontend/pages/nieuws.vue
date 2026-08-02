<script setup lang="ts">
// Client-side geladen (zelfde ofetch-patroon als de vraag-store): de
// devProxy/nginx routeert /api, en nieuws is geen SEO-kritische inhoud —
// de pagina zelf is dat wel, de items mogen na hydratie verschijnen.
import { $fetch } from 'ofetch'

interface NieuwsItem {
  id: number
  bron: string
  url: string
  titel: string
  datum: string
  samenvatting: string
}

const items = ref<NieuwsItem[] | null>(null)
const fout = ref(false)

onMounted(async () => {
  try {
    items.value = await $fetch<NieuwsItem[]>('/api/nieuws')
  } catch {
    fout.value = true
  }
})

function datumTekst(iso: string): string {
  return new Date(iso).toLocaleDateString('nl-NL', {
    day: 'numeric', month: 'long', year: 'numeric',
  })
}

useSeoMeta({
  title: 'Laatste ontwikkelingen',
  description: 'Ontwikkelingen rond de AI-verordening (EU AI Act), door de redactie geselecteerd en in gewone taal samengevat, met link naar de oorspronkelijke bron.',
  ogImage: 'https://grondslag.eu/og/nieuws.png',
  ogImageAlt: 'Grondslag — Laatste ontwikkelingen rond de AI-verordening',
})
</script>

<template>
  <article class="nieuws">
    <h1>Laatste ontwikkelingen</h1>
    <p class="intro">
      Ontwikkelingen rond de AI-verordening, geselecteerd uit officiële
      bronnen en door de redactie in gewone taal samengevat. Elk bericht
      linkt naar de oorspronkelijke bron.
    </p>
    <p class="volg">
      <a href="/api/nieuws.xml">Volg via RSS</a>
    </p>

    <p v-if="fout" class="leeg">Het nieuws kon niet worden geladen. Probeer het later opnieuw.</p>
    <p v-else-if="items && items.length === 0" class="leeg">Nog geen berichten.</p>

    <section v-for="item in items ?? []" :key="item.id" class="bericht">
      <p class="meta">{{ datumTekst(item.datum) }} · {{ item.bron }}</p>
      <h2>{{ item.titel }}</h2>
      <p>{{ item.samenvatting }}</p>
      <p class="bronlink">
        <a :href="item.url" target="_blank" rel="noopener">Lees het bericht bij de bron</a>
      </p>
    </section>
  </article>
</template>

<style scoped>
.nieuws { max-width: 68ch; }
.nieuws h1 { font-size: 26px; margin: 0 0 12px; }
.intro { margin: 0 0 8px; opacity: 0.85; }
.volg { margin: 0 0 24px; font-size: 14px; }
.leeg { opacity: 0.75; }
.bericht { padding: 16px 0; border-top: 1px solid var(--lijn); }
.bericht h2 { font-size: 17px; margin: 4px 0 6px; }
.bericht p { margin: 0; }
.meta { font-size: 13px; opacity: 0.7; }
.bronlink { margin-top: 8px; font-size: 14px; }
</style>
