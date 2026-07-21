<script setup lang="ts">
// Statisch citaatblok voor redactionele pagina's (beginpaneel, over-pagina):
// zelfde vorm als CitaatBlok, maar zonder antwoord-gedrag (highlight,
// scroll-anker, store). Zo blijft het signatuur-element één gebaar,
// zonder dat de gedrags-component overal een store nodig heeft.
import { BRON_VERORDENING, EURLEX_URL, STAND_WETGEVING } from '~/utils/bron'

withDefaults(defineProps<{
  artnr: string
  tekst: string
  bron?: string
  url?: string
  stand?: string
}>(), {
  bron: BRON_VERORDENING,
  url: EURLEX_URL,
  stand: STAND_WETGEVING,
})
</script>

<template>
  <blockquote class="citaatblok">
    <span class="artnr label">{{ artnr }}</span>
    <p class="citaattekst">{{ tekst }}</p>
    <footer class="bronregel">
      {{ bron }} · <span>stand: {{ stand }}</span> ·
      <a :href="url" target="_blank" rel="noopener">bekijk de bron</a>
    </footer>
  </blockquote>
</template>

<style scoped>
.citaatblok {
  margin: 0 0 8px;
  border-left: 3px solid var(--oker);
  background: var(--papier);
  padding: 12px 14px;
}
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
