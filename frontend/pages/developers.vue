<script setup lang="ts">
useSeoMeta({
  title: 'Voor ontwikkelaars — API en widget',
  description: 'Integreer Grondslag: de publieke /ask-API (gegronde antwoorden over de AI-verordening met citaat) en de embed-widget voor je eigen site.',
})

const curlVoorbeeld = `curl -X POST https://grondslag.eu/api/ask \\
  -H "Content-Type: application/json" \\
  -d '{"vraag": "Valt cv-screening onder de AI Act?"}'`

const antwoordVoorbeeld = `{
  "antwoord": "…",
  "citaten": [
    { "ref": "Artikel 6", "fragment": "…", "bron": "…", "url": "https://…" }
  ],
  "stand_van_wetgeving": "juli 2026",
  "geen_bron": false
}`

// Tagnaam gesplitst zodat de SFC-compiler de letterlijke script-tag in deze
// string niet als een tweede <script>-blok oppikt.
const widgetSnippet = '<scr' + 'ipt src="https://grondslag.eu/widget.js"></scr' + 'ipt>'
</script>

<template>
  <article class="dev">
    <h1>Voor ontwikkelaars</h1>
    <p class="intro">
      Integreer de gegronde antwoorden van Grondslag in je eigen product of site.
      Twee manieren: de <a href="#api">publieke API</a> of de
      <a href="#widget">embed-widget</a>. Vrij te gebruiken met bronvermelding
      (CC&nbsp;BY&nbsp;4.0). Informatie, geen juridisch advies.
    </p>

    <section id="api">
      <h2>Publieke API</h2>
      <p>
        <code>POST https://grondslag.eu/api/ask</code> — stuur een vraag, krijg
        een antwoord met citaten (artikelnummer, fragment, bron-URL) en de stand
        van de wetgeving. Per IP gerate-limit; bij overschrijding volgt
        <code>HTTP 429</code>.
      </p>
      <p class="klein">Verzoek: <code>{ "vraag": "…" }</code> (3–1000 tekens).</p>
      <pre><code>{{ curlVoorbeeld }}</code></pre>
      <p class="klein">Antwoord:</p>
      <pre><code>{{ antwoordVoorbeeld }}</code></pre>
      <!-- /api/** wordt naar de backend geproxyd; geen Nuxt-routes, dus de
           link-checker overslaan. -->
      <!-- eslint-disable link-checker/valid-route, link-checker/valid-sitemap-link -->
      <p>
        Volledige spec: <a href="/api/openapi.json">OpenAPI (JSON)</a> ·
        <a href="/api/docs">interactieve docs</a>.
      </p>
      <!-- eslint-enable link-checker/valid-route, link-checker/valid-sitemap-link -->
    </section>

    <section id="widget">
      <h2>Embed-widget</h2>
      <p>
        Plaats de vraagtool op je eigen pagina met één regel. Het script sluit
        een geïsoleerde iframe in en schaalt de hoogte automatisch mee. Laad het
        synchroon (geen <code>async</code>/<code>defer</code>).
      </p>
      <pre><code>{{ widgetSnippet }}</code></pre>
    </section>

    <section>
      <h2>Voorwaarden</h2>
      <ul>
        <li>Bronvermelding: "Grondslag (grondslag.eu), op basis van Verordening (EU) 2024/1689" — CC&nbsp;BY&nbsp;4.0.</li>
        <li>Grondslag geeft informatie, geen juridisch advies; verwijs voor een concrete situatie naar een jurist.</li>
        <li>Houd rekening met de rate-limit; vraag bij intensief gebruik even contact op.</li>
      </ul>
    </section>
  </article>
</template>

<style scoped>
.dev { max-width: 72ch; }
.dev h1 {
  font-family: var(--font-citaat); font-weight: 400;
  font-size: 28px; margin: 0 0 16px;
}
.dev h2 { font-size: 18px; margin: 28px 0 8px; }
.intro { margin: 0 0 8px; opacity: 0.9; }
.klein { font-size: 14px; opacity: 0.85; margin: 12px 0 4px; }
.dev p { margin: 0 0 10px; }
.dev code { font-family: var(--font-mono, ui-monospace, monospace); font-size: 0.9em; }
pre {
  background: var(--oker-licht, #F3EBD8); border: 1px solid var(--lijn, #E2E4E3);
  border-radius: 4px; padding: 12px 14px; overflow-x: auto; font-size: 13px;
}
pre code { font-size: inherit; }
.dev ul { padding-left: 18px; }
.dev li { margin: 0 0 6px; }
</style>
