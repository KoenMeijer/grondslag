// Eén plek voor de omschrijving: hij staat zowel in de meta-description als in
// de deelkaart, en die twee horen niet uit elkaar te lopen.
const BESCHRIJVING = 'Stel een vraag over de AI-verordening (AI Act) en krijg een antwoord met het letterlijke wetsartikel erbij, inclusief de actuele deadlines na de Digital Omnibus. Informatie, geen juridisch advies.'

// Waarom devProxy: de browser praat met /api/* op de Nuxt-origin; nitro stuurt
// dat door naar FastAPI op :8000 — geen CORS-gedoe, en straks op productie
// dezelfde same-origin-aanpak.
export default defineNuxtConfig({
  compatibilityDate: '2026-07-19',
  modules: ['@pinia/nuxt', '@nuxt/eslint'],
  css: [
    '@fontsource/public-sans/400.css',
    '@fontsource/public-sans/600.css',
    '@fontsource/literata/400.css',
    '@fontsource/literata/600.css',
    '~/assets/css/tokens.css',
  ],
  app: {
    head: {
      htmlAttrs: { lang: 'nl' },
      title: 'Grondslag',
      meta: [
        { name: 'description', content: BESCHRIJVING },
        // Deelkaart (LinkedIn, Slack, WhatsApp). Zonder deze tags tonen die een
        // kale link; het beeld is een echte schermafdruk, geen mock-up.
        { property: 'og:type', content: 'website' },
        { property: 'og:site_name', content: 'Grondslag' },
        { property: 'og:title', content: 'Grondslag — antwoorden over de AI-verordening' },
        { property: 'og:description', content: BESCHRIJVING },
        { property: 'og:url', content: 'https://grondslag.eu/' },
        { property: 'og:image', content: 'https://grondslag.eu/og-grondslag.png' },
        { property: 'og:image:width', content: '1200' },
        { property: 'og:image:height', content: '630' },
        { property: 'og:image:alt', content: 'Een vraag over cv-screening met daarnaast het letterlijke wetsartikel uit bijlage III.' },
        { property: 'og:locale', content: 'nl_NL' },
        { name: 'twitter:card', content: 'summary_large_image' },
      ],
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
        { rel: 'canonical', href: 'https://grondslag.eu/' },
      ],
    },
  },
  nitro: {
    // Overschrijfbaar zodat je zonder lokale backend tegen de live API kunt
    // testen: NUXT_DEV_API_PROXY=https://grondslag.almaconecta.eu/api npm run dev
    devProxy: {
      '/api': {
        target: process.env.NUXT_DEV_API_PROXY || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
