// Eén plek voor de omschrijving: hij staat zowel in de meta-description als in
// de deelkaart, en die twee horen niet uit elkaar te lopen.
const BESCHRIJVING = 'Stel een vraag over de AI-verordening (AI Act) en krijg een antwoord met het letterlijke wetsartikel erbij, inclusief de actuele deadlines na de Digital Omnibus. Informatie, geen juridisch advies.'

const SITE_URL = 'https://grondslag.eu'

// Verzameld tijdens `pages:extend`; de build-hook onderaan schrijft hieruit de
// sitemap. Zo blijft 'ie automatisch in sync met de file-based routes zonder de
// (op Nuxt 3.21 kapotte) runtime-sitemap-module.
const sitemapRoutes: string[] = []

// Waarom devProxy: de browser praat met /api/* op de Nuxt-origin; nitro stuurt
// dat door naar FastAPI op :8000 — geen CORS-gedoe, en straks op productie
// dezelfde same-origin-aanpak.
export default defineNuxtConfig({
  compatibilityDate: '2026-07-19',
  modules: ['@pinia/nuxt', '@nuxt/eslint', '@nuxtjs/seo'],
  css: [
    '@fontsource/public-sans/400.css',
    '@fontsource/public-sans/600.css',
    '@fontsource/literata/400.css',
    '@fontsource/literata/600.css',
    '~/assets/css/tokens.css',
  ],
  // Basis voor @nuxtjs/seo: canonical, og:url, sitemap-locs en robots-host
  // worden hieruit afgeleid. Eén bron van waarheid voor het domein.
  site: {
    url: 'https://grondslag.eu',
    name: 'Grondslag',
    description: BESCHRIJVING,
    defaultLocale: 'nl',
  },
  app: {
    head: {
      htmlAttrs: { lang: 'nl' },
      // Titel-template: @nuxtjs/seo maakt er "%s · Grondslag" van. Pagina's
      // zetten een kále titel (zonder sitenaam); de homepage doet dat in
      // pages/index.vue. Zo geen dubbele sitenaam.
      templateParams: { separator: '·' },
      // og:type/og:site_name/og:locale + per-route canonical & og:url zet
      // @nuxtjs/seo automatisch uit `site`. Hier alleen wat de module niet
      // kent: de statische deelkaart (echte schermafdruk) als site-brede
      // default, en de twitter-card. Pagina's overschrijven titel/beschrijving
      // via useSeoMeta; contentpagina's hun eigen og-image via defineOgImage.
      meta: [
        { name: 'description', content: BESCHRIJVING },
        // og:image zetten pagina's zelf (homepage = screenshot, contentpagina's
        // hun eigen kaart) zodat er nooit twee og:image-tags ontstaan. Formaat
        // is overal 1200x630, dus width/height mogen site-breed blijven.
        { property: 'og:image:width', content: '1200' },
        { property: 'og:image:height', content: '630' },
        { name: 'twitter:card', content: 'summary_large_image' },
      ],
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
      ],
    },
  },
  // Alleen het beheerscherm hoort niet in Google; de rest is publiek.
  robots: {
    disallow: ['/beheer'],
    // De sitemap genereren we zelf (zie hooks onderaan); verwijs er expliciet
    // naar zodat de regel in robots.txt blijft nu de sitemap-module uit is.
    sitemap: `${SITE_URL}/sitemap.xml`,
  },
  // @nuxtjs/sitemap 8 gaat uit van h3 v2 (event.url); Nuxt 3.21 draait h3 v1,
  // waardoor de runtime /sitemap.xml-handler `new URL('/sitemap.xml')` doet en
  // 500't. Module uit → sitemap zelf bij de build genereren (hooks onderaan),
  // auto uit de routes zodat 'ie niet verouderd (het eerder ontbrekende
  // /nieuws komt er nu vanzelf in, /beheer blijft eruit).
  sitemap: { enabled: false },
  // Site-brede structured data: Organization + WebSite. Per pagina voegt de
  // module automatisch een WebPage toe. (FAQPage volgt later, apart.)
  schemaOrg: {
    identity: {
      type: 'Organization',
      name: 'Grondslag',
      url: 'https://grondslag.eu',
      logo: 'https://grondslag.eu/favicon.svg',
    },
  },
  // og-image-generatie via de module uit (het runtime-endpoint heeft dezelfde
  // h3-incompatibiliteit als de sitemap). De statische og-grondslag.png (zie
  // app.head) is de default; per-pagina kaarten genereren we bij de build als
  // statische PNG's en hangen we per pagina via useSeoMeta({ ogImage }).
  ogImage: { enabled: false },
  hooks: {
    // Verzamel de statische, indexeerbare routes voor onze eigen sitemap.
    'pages:extend'(pages) {
      const verzamel = (lijst: { path?: string, children?: unknown[] }[]) => {
        for (const p of lijst) {
          if (p.path && !p.path.includes(':') && !p.path.startsWith('/beheer')) {
            sitemapRoutes.push(p.path)
          }
          if (Array.isArray(p.children)) verzamel(p.children as { path?: string }[])
        }
      }
      verzamel(pages as { path?: string }[])
    },
    // Schrijf de sitemap als statisch bestand in de public-output. Vervangt de
    // kapotte runtime-module; blijft in sync omdat de routes uit pages komen.
    async 'nitro:build:public-assets'(nitro) {
      const { writeFile } = await import('node:fs/promises')
      const { join } = await import('node:path')
      const routes = [...new Set(sitemapRoutes)].sort()
      const urls = routes.map(r => `  <url><loc>${SITE_URL}${r}</loc></url>`).join('\n')
      const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`
      await writeFile(join(nitro.options.output.publicDir, 'sitemap.xml'), xml, 'utf8')
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
