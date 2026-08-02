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
      <nav>
        <NuxtLink to="/nieuws">Laatste ontwikkelingen</NuxtLink>
        <NuxtLink to="/over">Over de verordening</NuxtLink>
        <NuxtLink to="/transparantie">Transparantie</NuxtLink>
      </nav>
    </header>
    <main class="inhoud"><slot /></main>
    <!-- Twee regels, geen kolommen of iconen: disclaimer (productprincipe 2)
         en drie tekstlinks — controleerbaarheid (EUR-Lex) en maker (portfolio). -->
    <footer class="sitefooter">
      <p>Grondslag geeft informatie, geen juridisch advies. Raadpleeg voor je eigen situatie een jurist.</p>
      <p class="footerlinks">
        <NuxtLink to="/nieuws">Laatste ontwikkelingen</NuxtLink>
        <span aria-hidden="true">·</span>
        <NuxtLink to="/over">Over de verordening</NuxtLink>
        <span aria-hidden="true">·</span>
        <NuxtLink to="/transparantie">Transparantie</NuxtLink>
        <span aria-hidden="true">·</span>
        <a href="https://eur-lex.europa.eu/legal-content/NL/TXT/?uri=CELEX:32024R1689" target="_blank" rel="noopener">Bron: Verordening (EU) 2024/1689 op EUR-Lex</a>
        <span aria-hidden="true">·</span>
        <a href="https://www.linkedin.com/in/koen-meijer-5b47239/" target="_blank" rel="noopener">Gemaakt door Koen Meijer</a>
        <span aria-hidden="true">·</span>
        <a href="https://github.com/KoenMeijer/grondslag" target="_blank" rel="noopener">Broncode op GitHub</a>
      </p>
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
.siteheader nav { display: flex; gap: 16px; }
.siteheader nav a { font-size: 14px; }
/* Op smalle schermen dringen twee navlinks naast het merk; de footer draagt
   dezelfde links, dus daar navigeer je onderin. Geen vaste balk: die zou
   permanent hoogte kosten en bij een open toetsenbord over de textarea vallen. */
@media (max-width: 640px) {
  .siteheader nav { display: none; }
}
.inhoud { flex: 1; width: 100%; max-width: 960px; margin: 0 auto; padding: 32px 24px; }
.sitefooter {
  border-top: 1px solid var(--lijn);
  padding: 16px 24px; font-size: 13px; color: var(--inkt);
}
.sitefooter p { margin: 0; }
/* Alleen de disclaimer gedempt; de links houden vol contrast. */
.sitefooter p:first-of-type { opacity: 0.75; }
.footerlinks { margin-top: 6px; display: flex; flex-wrap: wrap; gap: 4px 8px; }
.footerlinks a { text-underline-offset: 3px; }
</style>
