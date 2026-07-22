<script setup lang="ts">
// Eigen foutpagina i.p.v. Nuxts standaardscherm: een bezoeker die verdwaalt
// hoort niet plots buiten het ontwerp te vallen. Toon kalm wat er is, en één
// weg terug — geen technische details, geen excuses (design-brief §5).
import type { NuxtError } from '#app'

const props = defineProps<{ error: NuxtError }>()
const nietGevonden = computed(() => props.error?.statusCode === 404)

useHead({ title: nietGevonden.value ? 'Pagina niet gevonden · Grondslag' : 'Er ging iets mis · Grondslag' })
</script>

<template>
  <div class="fout">
    <h1>{{ nietGevonden ? 'Deze pagina bestaat niet' : 'Er ging iets mis' }}</h1>
    <p v-if="nietGevonden">
      De link klopt niet of de pagina is verplaatst. Je vraag over de
      AI-verordening kun je gewoon op de startpagina stellen.
    </p>
    <p v-else>
      De pagina kon niet worden geladen. Probeer het opnieuw; blijft het
      misgaan, dan ligt het aan ons.
    </p>
    <NuxtLink to="/" @click="clearError({ redirect: '/' })">Terug naar de startpagina</NuxtLink>
  </div>
</template>

<style scoped>
/* error.vue valt buiten de layout, dus de kadering staat hier zelf. */
.fout {
  max-width: 60ch;
  margin: 0 auto;
  padding: 64px 24px;
  font-family: var(--font-ui);
  color: var(--inkt);
}
.fout h1 {
  font-family: var(--font-citaat);
  font-weight: 400;
  font-size: 28px;
  margin: 0 0 12px;
}
.fout p { margin: 0 0 20px; }
</style>
