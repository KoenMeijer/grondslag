<script setup lang="ts">
// Redactiescherm voor de nieuwsaanvoer: concepten doornemen, de samenvatting
// herschrijven en per item publiceren of afwijzen. Eén redacteur, één geheim
// token (alleen in .env op de server) — bewust geen loginsysteem. Het token
// wordt niet opgeslagen: plakken per sessie is de veilige standaard.
import { $fetch } from 'ofetch'

interface Concept {
  id: number
  bron: string
  url: string
  titel: string
  datum: string
  samenvatting: string
}

const token = ref('')
const items = ref<Concept[]>([])
const geladen = ref(false)
const melding = ref('')
const bezig = ref(false)

function koppen() {
  return { 'X-Admin-Token': token.value }
}

async function laad() {
  melding.value = ''
  try {
    items.value = await $fetch<Concept[]>('/api/nieuws/concepten', { headers: koppen() })
    geladen.value = true
  } catch {
    geladen.value = false
    melding.value = 'Laden mislukt: token onjuist of beheer niet geconfigureerd.'
  }
}

async function werkBij(item: Concept, status: 'gepubliceerd' | 'afgewezen') {
  bezig.value = true
  melding.value = ''
  try {
    // De (eventueel herschreven) samenvatting gaat mee in dezelfde aanroep,
    // zodat publiceren nooit een oude tekst publiceert.
    await $fetch(`/api/nieuws/${item.id}`, {
      method: 'PATCH',
      headers: koppen(),
      body: { samenvatting: item.samenvatting, status },
    })
    items.value = items.value.filter(i => i.id !== item.id)
  } catch {
    melding.value = 'Bijwerken mislukt. Controleer het token en probeer opnieuw.'
  } finally {
    bezig.value = false
  }
}

useHead({
  title: 'Beheer',
  // Redactiescherm: niet voor zoekmachines.
  meta: [{ name: 'robots', content: 'noindex, nofollow' }],
})
</script>

<template>
  <article class="beheer">
    <h1>Nieuwsredactie</h1>

    <form class="tokenvorm" @submit.prevent="laad">
      <input
        v-model="token"
        type="password"
        placeholder="Beheertoken"
        autocomplete="off"
      >
      <button type="submit" :disabled="!token">Concepten laden</button>
    </form>

    <p v-if="melding" class="melding">{{ melding }}</p>
    <p v-else-if="geladen && items.length === 0" class="leeg">
      Geen concepten — alles is beoordeeld.
    </p>

    <section v-for="item in items" :key="item.id" class="concept">
      <p class="meta">{{ item.datum }} · {{ item.bron }}</p>
      <h2>{{ item.titel }}</h2>
      <p class="bronlink">
        <a :href="item.url" target="_blank" rel="noopener">Bekijk het oorspronkelijke bericht</a>
      </p>
      <textarea v-model="item.samenvatting" rows="5" />
      <div class="acties">
        <button :disabled="bezig || !item.samenvatting.trim()" @click="werkBij(item, 'gepubliceerd')">
          Publiceren
        </button>
        <button class="afwijzen" :disabled="bezig" @click="werkBij(item, 'afgewezen')">
          Afwijzen
        </button>
      </div>
    </section>
  </article>
</template>

<style scoped>
.beheer { max-width: 68ch; }
.beheer h1 { font-size: 26px; margin: 0 0 16px; }
.tokenvorm { display: flex; gap: 8px; margin-bottom: 20px; }
.tokenvorm input { flex: 1; padding: 8px 10px; border: 1px solid var(--lijn); }
.melding { color: #a33; }
.leeg { opacity: 0.75; }
.concept { padding: 16px 0; border-top: 1px solid var(--lijn); }
.concept h2 { font-size: 17px; margin: 4px 0 6px; }
.meta { font-size: 13px; opacity: 0.7; margin: 0; }
.bronlink { font-size: 14px; margin: 0 0 8px; }
.concept textarea {
  width: 100%; padding: 8px 10px; border: 1px solid var(--lijn);
  font: inherit; resize: vertical;
}
.acties { display: flex; gap: 8px; margin-top: 8px; }
.acties button { padding: 6px 14px; }
.afwijzen { opacity: 0.8; }
</style>
