<script setup lang="ts">
import { alleVragen } from '~/utils/vragen'

useSeoMeta({
  title: 'Vragen over de AI-verordening',
  description: 'Veelgestelde vragen over de EU AI-verordening (AI Act) — elk antwoord met de wetsverwijzing en de stand van de wetgeving.',
})
</script>

<template>
  <article class="vragen">
    <h1>Vragen over de AI-verordening</h1>
    <p class="intro">
      Antwoorden op veelgestelde vragen, elk met de verwijzing naar het
      wetsartikel en de stand van de wetgeving. Informatie, geen juridisch advies.
    </p>
    <ul class="lijst">
      <li v-for="v in alleVragen" :key="v.slug">
        <NuxtLink :to="`/vraag/${v.slug}`">{{ v.vraag }}</NuxtLink>
      </li>
    </ul>
    <p class="slot">
      Staat jouw vraag er niet bij? <NuxtLink to="/">Stel 'm rechtstreeks</NuxtLink> —
      het antwoord komt met het artikel erbij.
    </p>
  </article>
</template>

<style scoped>
.vragen { max-width: 68ch; }
.vragen h1 {
  font-family: var(--font-citaat); font-weight: 400;
  font-size: 28px; margin: 0 0 20px;
}
.intro { margin: 0 0 20px; opacity: 0.85; }
.lijst { margin: 0 0 24px; padding: 0; list-style: none; }
.lijst li { padding: 12px 0; border-top: 1px solid var(--lijn); }
.slot { margin-top: 24px; }
</style>
