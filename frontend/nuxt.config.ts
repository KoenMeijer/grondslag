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
      meta: [{ name: 'description', content: 'Antwoorden over de AI-verordening (AI Act), gegrond in de wettekst.' }],
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
