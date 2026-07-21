<script setup lang="ts">
import { useVraagStore } from '~/stores/vraag'

const store = useVraagStore()
</script>

<template>
  <aside class="citaatpaneel" aria-label="Bronnen uit de wettekst">
    <h2 class="label">Bronnen</h2>
    <p v-if="!store.resultaat?.citaten.length" class="geen">
      Dit antwoord verwijst niet naar een specifiek artikel.
    </p>
    <CitaatBlok v-for="c in store.resultaat?.citaten ?? []" :key="c.ref" :citaat="c" />
  </aside>
</template>

<style scoped>
/* Geen kaart: de citaatblokken zijn zelf het gebaar en staan direct op het
   papier — een rand eromheen verpakte ze als generieke widget. */
.citaatpaneel h2 { margin: 0 0 12px; }
.geen { font-size: 14px; opacity: 0.75; }
</style>
