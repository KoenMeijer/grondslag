<script setup lang="ts">
import { useVraagStore } from '~/stores/vraag'

// Logo-klik = terug naar de begintoestand, de conventie die iedereen kent.
const store = useVraagStore()
</script>

<template>
  <div class="app">
    <!-- Geen wit vlak: het papier loopt door, alleen een dunne lijn scheidt.
         Het merk in de citaat-letter — dezelfde stem als de wettekst. -->
    <header class="siteheader">
      <NuxtLink to="/" class="merk" @click="store.wis()">Grondslag</NuxtLink>
      <nav><NuxtLink to="/transparantie">Transparantie</NuxtLink></nav>
    </header>
    <main class="inhoud"><slot /></main>
    <footer class="sitefooter">
      <p>Grondslag geeft informatie, geen juridisch advies. Raadpleeg voor je eigen situatie een jurist.</p>
    </footer>
  </div>
</template>

<style scoped>
.app { min-height: 100vh; display: flex; flex-direction: column; }
.siteheader {
  display: flex; justify-content: space-between; align-items: baseline;
  padding: 20px 24px; border-bottom: 1px solid var(--lijn);
}
.merk {
  font-family: var(--font-citaat); font-weight: 600; font-size: 20px;
  color: var(--inkt); text-decoration: none;
}
.siteheader nav a { font-size: 14px; }
.inhoud { flex: 1; width: 100%; max-width: 960px; margin: 0 auto; padding: 32px 24px; }
.sitefooter {
  border-top: 1px solid var(--lijn);
  padding: 16px 24px; font-size: 13px; color: var(--inkt); opacity: 0.75;
}
.sitefooter p { margin: 0; }
</style>
