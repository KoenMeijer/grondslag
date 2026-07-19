<script setup lang="ts">
import { computed } from 'vue'
import { useVraagStore, type Citaat } from '~/stores/vraag'

const store = useVraagStore()

// Splits het antwoord op [ref]-patronen; alleen refs die aan een meegeleverd
// citaat te koppelen zijn worden klikbaar — een niet-opgehaalde ref blijft platte tekst.
const delen = computed(() => {
  const resultaat = store.resultaat
  if (!resultaat) return []
  return resultaat.antwoord.split(/(\[[^\]]+\])/).map((stuk) => {
    const m = stuk.match(/^\[([^\]]+)\]$/)
    if (m) {
      const doel = vindCitaatRef(m[1], resultaat.citaten)
      if (doel) return { type: 'ref' as const, ref: doel, tekst: stuk }
    }
    return { type: 'tekst' as const, ref: '', tekst: stuk }
  })
})

// Zelfde regel als de backend (vind_citaten): het model mag een ref verfijnen
// ("…, onder a)"); de langste chunk-ref die als prefix past wint.
function vindCitaatRef(geciteerd: string, citaten: Citaat[]): string {
  const passend = citaten.filter((c) => geciteerd === c.ref || geciteerd.startsWith(c.ref + ','))
  if (!passend.length) return ''
  return passend.reduce((a, b) => (a.ref.length >= b.ref.length ? a : b)).ref
}

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
