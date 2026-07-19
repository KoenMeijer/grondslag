<script setup lang="ts">
import { computed, ref } from 'vue'
import { useVraagStore } from '~/stores/vraag'

const store = useVraagStore()
const vraag = ref('')
const kanVersturen = computed(() => vraag.value.trim().length > 0 && !store.bezig)

function verstuur() {
  if (kanVersturen.value) store.stel(vraag.value.trim())
}
</script>

<template>
  <form class="vraagformulier" @submit.prevent="verstuur">
    <label class="label" for="vraag">Stel je vraag</label>
    <textarea
      id="vraag"
      v-model="vraag"
      rows="3"
      placeholder="Bijvoorbeeld: valt cv-screening met AI onder hoog risico?"
    />
    <button type="submit" :disabled="!kanVersturen">
      {{ store.bezig ? 'Bezig met zoeken in de wettekst…' : 'Stel je vraag' }}
    </button>
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
</style>
