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

interface DagCijfer {
  datum: string
  bezoeken: number
  vragen: number
}

interface Cijfers {
  dagen: number
  reeks: DagCijfer[]
  totaal_bezoeken: number
  totaal_vragen: number
}

const token = ref('')
const items = ref<Concept[]>([])
const cijfers = ref<Cijfers | null>(null)
const geladen = ref(false)
const melding = ref('')
const bezig = ref(false)

function koppen() {
  return { 'X-Admin-Token': token.value }
}

async function laad() {
  melding.value = ''
  try {
    // Concepten en cijfers achter hetzelfde token; samen ophalen zodat het
    // beheerscherm in één slag compleet is.
    items.value = await $fetch<Concept[]>('/api/nieuws/concepten', { headers: koppen() })
    cijfers.value = await $fetch<Cijfers>('/api/cijfers', { headers: koppen() })
    geladen.value = true
  } catch {
    geladen.value = false
    cijfers.value = null
    melding.value = 'Laden mislukt: token onjuist of beheer niet geconfigureerd.'
  }
}

function datumTekst(iso: string): string {
  return new Date(iso).toLocaleDateString('nl-NL', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
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

    <section v-if="cijfers" class="cijfers">
      <h2>Gebruikscijfers</h2>
      <p class="samenvatting">
        Laatste {{ cijfers.dagen }} dagen:
        <strong>{{ cijfers.totaal_bezoeken }}</strong> bezoeken,
        <strong>{{ cijfers.totaal_vragen }}</strong> vragen.
      </p>
      <p v-if="cijfers.reeks.length === 0" class="leeg">Nog geen bezoeken of vragen geteld.</p>
      <table v-else class="cijfertabel">
        <thead>
          <tr><th>Dag</th><th>Bezoeken</th><th>Vragen</th></tr>
        </thead>
        <tbody>
          <tr v-for="dag in cijfers.reeks" :key="dag.datum">
            <td>{{ datumTekst(dag.datum) }}</td>
            <td>{{ dag.bezoeken }}</td>
            <td>{{ dag.vragen }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <h2 v-if="geladen" class="conceptenkop">Nieuwsconcepten</h2>
    <p v-if="geladen && items.length === 0" class="leeg">
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
.cijfers { margin-bottom: 28px; }
.cijfers h2, .conceptenkop { font-size: 18px; margin: 0 0 8px; }
.conceptenkop { padding-top: 16px; border-top: 1px solid var(--lijn); }
.cijfers .samenvatting { margin: 0 0 12px; }
.cijfertabel { border-collapse: collapse; font-size: 14px; }
.cijfertabel th, .cijfertabel td {
  padding: 4px 16px 4px 0; text-align: left; border-bottom: 1px solid var(--lijn);
}
.cijfertabel th:not(:first-child), .cijfertabel td:not(:first-child) {
  text-align: right; font-variant-numeric: tabular-nums;
}
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
