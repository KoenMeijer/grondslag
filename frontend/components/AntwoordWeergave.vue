<script setup lang="ts">
import { computed } from 'vue'
import { useVraagStore } from '~/stores/vraag'

const store = useVraagStore()

// Splits het antwoord op [ref]-patronen; alleen refs die echt als citaat zijn
// meegeleverd worden klikbaar — een niet-opgehaalde ref blijft platte tekst.
const delen = computed(() => {
  const resultaat = store.resultaat
  if (!resultaat) return []
  const bekend = new Set(resultaat.citaten.map((c) => c.ref))
  return resultaat.antwoord.split(/(\[[^\]]+\])/).map((stuk) => {
    const m = stuk.match(/^\[([^\]]+)\]$/)
    if (m && bekend.has(m[1])) return { type: 'ref' as const, ref: m[1], tekst: stuk }
    return { type: 'tekst' as const, ref: '', tekst: stuk }
  })
})

function ga(refNaam: string) {
  store.markeer(refNaam)
  document.getElementById(`citaat-${refNaam}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}
</script>

<template>
  <article class="antwoord" aria-label="Antwoord">
    <template v-for="(deel, i) in delen" :key="i">
      <button v-if="deel.type === 'ref'" class="refknop" type="button" @click="ga(deel.ref)">
        {{ deel.tekst }}
      </button>
      <span v-else>{{ deel.tekst }}</span>
    </template>
  </article>
</template>

<style scoped>
.antwoord { white-space: pre-wrap; }
.refknop {
  display: inline; padding: 0; border: none; background: none; cursor: pointer;
  font: inherit; color: var(--oker-donker); text-decoration: underline;
  text-underline-offset: 2px;
}
</style>
