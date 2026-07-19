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
const fragment = computed(() => props.citaat.fragment.replace(/^[^:]+:\s*/, ''))
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
