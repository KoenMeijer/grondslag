<script setup lang="ts">
import { useVraagStore } from '~/stores/vraag'

const store = useVraagStore()
</script>

<template>
  <!-- Eén grid vanaf het begin: links vraag + antwoord, rechts de vaste
       bronnen-plek (beginpaneel → zoekstatus → echte bronnen). Zo ziet de
       bezoeker het antwoord-formaat vóór hij iets vraagt. -->
  <div class="pagina">
    <div class="links">
      <section class="intro">
        <h1>Antwoorden over de AI&#8209;verordening, gegrond in de wettekst</h1>
        <p>
          Stel een vraag; elk antwoord verwijst naar het letterlijke artikel,
          met de actuele deadlines na de Digital Omnibus.
        </p>
      </section>

      <VraagFormulier />

      <div aria-live="polite">
        <p v-if="store.fout" class="fout" role="alert">{{ store.fout }}</p>
        <div v-if="store.resultaat" class="antwoordvak">
          <AntwoordWeergave />
          <p class="stempel">stand van wetgeving: {{ store.resultaat.stand_van_wetgeving }}</p>
        </div>
      </div>
    </div>

    <div class="rechts">
      <p v-if="store.bezig" class="zoekstatus label">Zoeken in de wettekst…</p>
      <CitaatPaneel v-else-if="store.resultaat" />
      <BeginPaneel v-else />
    </div>
  </div>
</template>

<style scoped>
.pagina {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 40px;
}
/* De stem van de wet als eerste indruk: de kop in de citaat-letter. */
.intro h1 {
  font-family: var(--font-citaat);
  font-weight: 400;
  font-size: clamp(28px, 4vw, 38px);
  line-height: 1.25;
  margin: 0 0 12px;
}
.intro p { margin: 0 0 24px; max-width: 60ch; }
.fout { color: var(--fout); margin-top: 16px; }
.antwoordvak { margin-top: 28px; }
.stempel { font-size: 12px; opacity: 0.7; margin-top: 16px; }
.zoekstatus { margin: 0; }
@media (max-width: 760px) {
  .pagina { grid-template-columns: 1fr; gap: 28px; }
}
</style>
