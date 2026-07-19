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
      title: 'AiActWijzer',
      meta: [{ name: 'description', content: 'Antwoorden over de EU AI Act, gegrond in de wettekst.' }],
    },
  },
  nitro: {
    devProxy: { '/api': { target: 'http://localhost:8000', changeOrigin: true } },
  },
})
