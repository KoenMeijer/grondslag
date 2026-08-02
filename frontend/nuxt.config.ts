// Eén plek voor de omschrijving: hij staat zowel in de meta-description als in
// de deelkaart, en die twee horen niet uit elkaar te lopen.
const BESCHRIJVING = 'Stel een vraag over de AI-verordening (AI Act) en krijg een antwoord met het letterlijke wetsartikel erbij, inclusief de actuele deadlines na de Digital Omnibus. Informatie, geen juridisch advies.'

const SITE_URL = 'https://grondslag.eu'

// Wie de embed-widget (/embed) mag insluiten. Standaard iedereen (*), zodat
// de publieke widget werkt. Zet NUXT_PUBLIC_EMBED_ANCESTORS in productie om te
// beperken tot partnerdomeinen, bv. "https://partner1.nl https://partner2.nl".
const EMBED_ANCESTORS = process.env.NUXT_PUBLIC_EMBED_ANCESTORS || '*'

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
        // Feed-autodiscovery: nieuwslezers/aggregators vinden de RSS zo vanzelf.
        { rel: 'alternate', type: 'application/rss+xml', title: 'Grondslag — Laatste ontwikkelingen', href: `${SITE_URL}/api/nieuws.xml` },
      ],
    },
  },
  // Alleen het beheerscherm hoort niet in Google; de rest is publiek.
  robots: {
    // /beheer = admin; /embed = widget-doel (hoort niet los in Google).
    disallow: ['/beheer', '/embed'],
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
          if (p.path && !p.path.includes(':')
            && !p.path.startsWith('/beheer') && p.path !== '/embed') {
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
      const { writeFile, readdir, readFile } = await import('node:fs/promises')
      const { join } = await import('node:path')
      const pub = nitro.options.output.publicDir
      // Kennisbank-slugs toevoegen: de dynamische /vraag/[slug]-routes pikt
      // pages:extend niet op, dus lezen we de bronbestanden zelf.
      let vraagRoutes: string[] = []
      try {
        const files = await readdir(join(process.cwd(), 'content', 'vragen'))
        vraagRoutes = files.filter(f => f.endsWith('.md'))
          .map(f => `/vraag/${f.replace(/\.md$/, '')}`)
      } catch { /* geen kennisbank → niets toevoegen */ }
      const routes = [...new Set([...sitemapRoutes, ...vraagRoutes])].sort()
      const urls = routes.map(r => `  <url><loc>${SITE_URL}${r}</loc></url>`).join('\n')
      const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`
      await writeFile(join(pub, 'sitemap.xml'), xml, 'utf8')

      // Deadline-dataset als machine-leesbare downloads (JSON + CSV) naast de
      // /deadlines-pagina. Bron van waarheid: data/deadlines.json.
      try {
        const data = JSON.parse(await readFile(join(process.cwd(), 'data', 'deadlines.json'), 'utf8'))
        await writeFile(join(pub, 'deadlines.json'), `${JSON.stringify(data, null, 2)}\n`, 'utf8')
        const kolommen = ['fase', 'artikel', 'verplichting', 'datum', 'was', 'status']
        const esc = (v: unknown) => {
          const s = v == null ? '' : String(v)
          return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
        }
        const csv = [
          kolommen.join(','),
          ...data.mijlpalen.map((m: Record<string, unknown>) => kolommen.map(k => esc(m[k])).join(',')),
        ].join('\n') + '\n'
        await writeFile(join(pub, 'deadlines.csv'), csv, 'utf8')
      } catch { /* geen dataset → overslaan */ }
    },
  },
  nitro: {
    routeRules: {
      // Standaard niet insluitbaar (clickjacking-bescherming).
      '/**': {
        headers: {
          'X-Frame-Options': 'DENY',
          'Content-Security-Policy': "frame-ancestors 'none'",
        },
      },
      // Uitzondering: de embed-widget mág ingesloten worden — door iedereen, of
      // door de partnerdomeinen uit EMBED_ANCESTORS. X-Frame-Options kent geen
      // allowlist-waarde, dus die zetten we leeg (browsers negeren 'm dan) en
      // laten CSP frame-ancestors de toegang regelen.
      '/embed': {
        headers: {
          'X-Frame-Options': '',
          'Content-Security-Policy': `frame-ancestors ${EMBED_ANCESTORS}`,
        },
      },
    },
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
