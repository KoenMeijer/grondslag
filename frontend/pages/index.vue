<script setup lang="ts">
import { useVraagStore } from '~/stores/vraag'

const store = useVraagStore()
</script>

<template>
  <div>
    <section class="intro">
      <h1>Antwoorden over de EU AI Act, gegrond in de wettekst</h1>
      <p>
        Stel een vraag over de AI-verordening; elk antwoord verwijst naar het
        letterlijke artikel, met de actuele deadlines na de Digital Omnibus.
      </p>
    </section>

    <VraagFormulier />

    <p v-if="store.fout" class="fout">{{ store.fout }}</p>

    <div v-if="store.resultaat" class="resultaat">
      <div>
        <AntwoordWeergave />
        <p class="stempel">stand van wetgeving: {{ store.resultaat.stand_van_wetgeving }}</p>
      </div>
      <CitaatPaneel />
    </div>
  </div>
</template>

<style scoped>
.intro h1 { font-size: 26px; line-height: 1.3; margin: 0 0 8px; }
.intro p { margin: 0 0 24px; max-width: 60ch; }
.fout { color: var(--fout); margin-top: 16px; }
.resultaat {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 24px;
  margin-top: 28px;
}
.stempel { font-size: 12px; opacity: 0.7; margin-top: 16px; }
@media (max-width: 760px) {
  .resultaat { grid-template-columns: 1fr; }
}
</style>
