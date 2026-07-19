<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useVraagStore, type Citaat } from '~/stores/vraag'

const props = defineProps<{ citaat: Citaat }>()
const store = useVraagStore()
const licht = ref(false)

// Korte highlight, daarna rust (design-brief §3) — geen blijvende markering.
watch(() => store.actieveRef, (nieuw) => {
  if (nieuw === props.citaat.ref) {
    licht.value = true
    setTimeout(() => {
      licht.value = false
      store.markeer('')
    }, 1600)
  }
})

// Het fragment draagt zijn eigen "ref (kop): "-prefix (kop-als-context voor
// retrieval); naast het artikelnummer-kopje is die prefix dubbelop.
const fragment = computed(() => {
  const f = props.citaat.fragment
  // Strip alleen de bekende retrieval-prefix ("<ref> (kop): " of "<ref>: ");
  // ankeren op de ref voorkomt dat een dubbelepunt in een kop het citaat verminkt.
  if (f.startsWith(props.citaat.ref)) {
    const scheiding = f.indexOf(': ', props.citaat.ref.length)
    if (scheiding !== -1) return f.slice(scheiding + 2)
  }
  return f
})
</script>

<template>
  <blockquote :id="`citaat-${citaat.ref}`" class="citaatblok" :class="{ licht }">
    <span class="artnr label">{{ citaat.ref }}</span>
    <p class="citaattekst">{{ fragment }}</p>
    <footer class="bronregel">{{ citaat.bron }} · <span class="stempel-inline">stand: {{ store.resultaat?.stand_van_wetgeving }}</span> · <a :href="citaat.url" target="_blank" rel="noopener">bekijk de bron</a></footer>
  </blockquote>
</template>

<style scoped>
.citaatblok {
  margin: 0 0 12px;
  border-left: 3px solid var(--oker);
  background: var(--papier);
  padding: 12px 14px;
  transition: background 0.4s ease;
}
.citaatblok.licht { background: var(--oker-licht); }
.artnr { display: block; margin-bottom: 5px; }
.citaattekst {
  margin: 0;
  font-family: var(--font-citaat);
  font-size: 17px;
  line-height: 1.6;
  color: var(--citaat-tekst);
}
.bronregel { font-size: 11.5px; margin-top: 8px; opacity: 0.7; }
</style>
