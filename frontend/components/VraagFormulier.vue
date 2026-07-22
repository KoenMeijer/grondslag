<script setup lang="ts">
import { computed } from 'vue'
import { useVraagStore } from '~/stores/vraag'

const store = useVraagStore()
const kanVersturen = computed(() => store.invoer.trim().length > 0 && !store.bezig)

// Uit de golden set (evals/golden_set.yaml): vragen waarvan retrieval
// aantoonbaar werkt. Samen tonen ze de breedte van wat je kunt vragen:
// hoog risico · deadline · verboden praktijk · transparantieplicht.
const voorbeelden = [
  "Wij screenen cv's met AI bij sollicitaties — in welke risicocategorie valt dat?",
  'Vanaf wanneer gelden de verplichtingen voor hoog-risico-AI-systemen?',
  'Mag een gemeente inwoners met AI een sociale score geven?',
  'Moet ik gebruikers vertellen dat ze met AI praten?',
]

function verstuur() {
  if (kanVersturen.value) store.stel(store.invoer.trim())
}

// Textarea meevullen zodat zichtbaar blijft wélke vraag er gesteld is.
function stelVoorbeeld(tekst: string) {
  store.invoer = tekst
  store.stel(tekst)
}
</script>

<template>
  <form class="vraagformulier" @submit.prevent="verstuur">
    <label class="label" for="vraag">Stel je vraag</label>
    <textarea
      id="vraag"
      v-model="store.invoer"
      rows="3"
      placeholder="Beschrijf je situatie of stel je vraag"
      @keydown.enter.exact.prevent="verstuur"
    />
    <button type="submit" :disabled="!kanVersturen">
      {{ store.bezig ? 'Bezig met zoeken in de wettekst…' : 'Stel je vraag' }}
    </button>

    <!-- Wegwijzer voor de eerste bezoeker; na de eerste vraag is de pagina
         van het antwoord en verdwijnt dit blok. -->
    <div v-if="!store.resultaat && !store.bezig" class="voorbeelden">
      <p class="voorbeelden-label">Bijvoorbeeld:</p>
      <ul>
        <li v-for="v in voorbeelden" :key="v">
          <button type="button" @click="stelVoorbeeld(v)">{{ v }}</button>
        </li>
      </ul>
    </div>
  </form>
</template>

<style scoped>
.vraagformulier { display: flex; flex-direction: column; gap: 8px; }
textarea {
  font-family: var(--font-ui); font-size: 16px; line-height: 1.55;
  padding: 12px; border: 1px solid var(--lijn); border-radius: var(--radius);
  background: var(--wit); color: var(--inkt); resize: vertical;
}
textarea:focus { outline: 2px solid var(--oker); outline-offset: 1px; }
button {
  align-self: flex-start;
  font-family: var(--font-ui); font-size: 15px; font-weight: 600;
  background: var(--inkt); color: var(--papier);
  border: none; border-radius: var(--radius); padding: 10px 18px; cursor: pointer;
}
button:disabled { opacity: 0.5; cursor: default; }

/* Kalme tekstlinks, geen knop-styling — de voorbeelden wijzen de weg,
   ze schreeuwen niet (design-brief §4/5). */
.voorbeelden { margin-top: 12px; }
.voorbeelden-label { margin: 0 0 4px; font-size: 13px; opacity: 0.7; }
.voorbeelden ul { list-style: none; margin: 0; padding: 0; }
.voorbeelden li { margin: 2px 0; }
.voorbeelden li button {
  background: none; border: none; padding: 2px 0; cursor: pointer;
  align-self: auto;
  font-family: var(--font-ui); font-size: 15px; font-weight: 400;
  color: var(--oker-donker); text-align: left; line-height: 1.5;
  text-decoration: underline; text-underline-offset: 3px;
  text-decoration-color: color-mix(in srgb, var(--oker-donker) 40%, transparent);
}
.voorbeelden li button:hover { text-decoration-color: var(--oker-donker); }
.voorbeelden li button:focus-visible { outline: 2px solid var(--oker); outline-offset: 2px; border-radius: var(--radius); }
</style>
