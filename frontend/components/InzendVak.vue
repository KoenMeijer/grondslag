<script setup lang="ts">
// Opt-in na een onbeantwoorde vraag. De pagina bepaalt wanneer dit vak
// verschijnt (alleen bij geen_bron); hier leeft alleen de inzendflow zelf.
// De copy belooft precies wat de backend doet: alleen de vraagtekst.
import { useVraagStore } from '~/stores/vraag'

const store = useVraagStore()
</script>

<template>
  <div class="inzendvak">
    <p v-if="store.ingezonden" class="dank">
      Dank — je vraag is anoniem opgeslagen en helpt de bronnen aan te vullen.
    </p>
    <template v-else>
      <p class="uitleg">
        Ging je vraag wél over de AI&#8209;verordening? Stuur hem anoniem op —
        alleen de vraagtekst wordt bewaard, zodat de bronnen aangevuld kunnen worden.
      </p>
      <button type="button" @click="store.zendIn()">Stuur deze vraag anoniem op</button>
      <p v-if="store.inzendFout" class="fout">{{ store.inzendFout }}</p>
    </template>
  </div>
</template>

<style scoped>
/* Zelfde stille vorm als het foutvak: geen kader, geen kleuraccent — het
   antwoord blijft het onderwerp, dit is een voetnoot eronder. */
.inzendvak { margin-top: 16px; }
.uitleg, .dank { font-size: 14px; opacity: 0.85; margin: 0 0 8px; max-width: 60ch; }
.dank { margin-bottom: 0; }
.inzendvak button {
  font-family: var(--font-ui); font-size: 14px; font-weight: 600;
  background: none; color: var(--inkt);
  border: 1px solid var(--lijn); border-radius: var(--radius);
  padding: 6px 14px; cursor: pointer;
}
.fout { color: var(--fout); font-size: 14px; margin: 8px 0 0; }
</style>
