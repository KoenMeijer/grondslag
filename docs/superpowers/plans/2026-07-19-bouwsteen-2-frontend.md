# Bouwsteen 2 — Frontend met citaat-paneel — Implementatieplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Nuxt 3-frontend voor AiActWijzer: vraagformulier, antwoord met klikbare refs, het citaat-paneel als signatuur-element, actualiteits-stempel en transparantie-pagina — exact volgens `docs/design-brief.md`.

**Architecture:** Kale Nuxt 3 (geen @nuxt/ui — bewuste keuze, zie design-brief) + Pinia-store als enige API-koppeling (`POST /api/ask` via nitro-devProxy naar FastAPI op :8000). Componenten: VraagFormulier → store → AntwoordWeergave (parseert `[refs]` naar klikbare knoppen) + CitaatPaneel/CitaatBlok (highlight bij klik). Fonts self-hosted via fontsource-packages.

**Tech Stack:** Nuxt 3 · Pinia · @fontsource/public-sans + @fontsource/literata · vitest + @vue/test-utils + happy-dom + @pinia/testing · @nuxt/eslint. Node v24 aanwezig.

Ontwerp: `docs/design-brief.md` (tokens, signatuur-element, toon) — elke UI-stap volgt dat document.

## Global Constraints

- **Tokens exact uit de design-brief:** `--inkt #14213D`, `--papier #FAFAF7`, `--wit #FFFFFF`, `--lijn #E2E4E3`, `--oker #B98A2F`, `--oker-donker #8A6A1F`, `--fout #8C3A2E`; radius 4px; geen schaduwen/gradients; alleen lichte modus; animatie alleen citaat-highlight.
- **Typografie:** UI Public Sans (400/600), citaten Literata (400/600), self-hosted via fontsource — géén Google-CDN. Basis 16px/1.55; citaattekst 17px/1.6.
- **Copy:** kalm actief Nederlands; verplicht zichtbaar: "informatie, geen juridisch advies" (footer) en de actualiteits-stempel bij elk antwoord. Verboden register per design-brief §5.
- **Expliciete imports** in alle componenten/stores (`import { ref } from 'vue'`, `import { useVraagStore } from '~/stores/vraag'`) — zodat kale vitest zonder Nuxt-runtime werkt.
- **Scope:** géén streaming, géén dark mode, géén accounts, géén deploy/Docker voor de frontend, géén extra pagina's naast index + transparantie.
- **Commando's:** vanuit `frontend/` tenzij anders vermeld; backend-API draait op :8000 (zie README).
- **Taal:** code-comments en commitberichten Nederlands (waarom, niet wat); commits eindigen op `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.

---

### Task 1: Nuxt-scaffold, tokens en fonts

**Files:**
- Create: `frontend/package.json`, `frontend/nuxt.config.ts`, `frontend/tsconfig.json`, `frontend/eslint.config.mjs`, `frontend/app.vue`, `frontend/layouts/default.vue`, `frontend/assets/css/tokens.css`
- Modify: `.gitignore` (repo-root)

**Interfaces:**
- Produces: draaiende Nuxt-dev-server met tokens/fonts geladen; layout met header (merk + nav naar /transparantie) en footer met de geen-advies-regel. Latere taken hangen pagina's/componenten hierin.

- [ ] **Step 1: Voeg aan de repo-root-`.gitignore` toe**

```gitignore
frontend/node_modules/
frontend/.nuxt/
frontend/.output/
```

- [ ] **Step 2: Schrijf `frontend/package.json`**

```json
{
  "name": "aiactwijzer-frontend",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "nuxt dev",
    "build": "nuxt build",
    "lint": "eslint .",
    "test": "vitest run"
  },
  "dependencies": {
    "@fontsource/literata": "^5",
    "@fontsource/public-sans": "^5",
    "@pinia/nuxt": "^0.10",
    "nuxt": "^3.17",
    "ofetch": "^1",
    "pinia": "^2.3"
  },
  "devDependencies": {
    "@nuxt/eslint": "^1",
    "@pinia/testing": "^0.1",
    "@vitejs/plugin-vue": "^5",
    "@vue/test-utils": "^2",
    "eslint": "^9",
    "happy-dom": "^15",
    "typescript": "^5",
    "vitest": "^2"
  }
}
```

> Versieranges zijn een startpunt; als `npm install` een peer-conflict geeft
> (pinia/@pinia-versies bewegen), los het op met de door npm voorgestelde
> compatibele versies en noteer de uiteindelijke keuze in je rapport.

- [ ] **Step 3: Schrijf `frontend/nuxt.config.ts`**

```ts
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
```

- [ ] **Step 4: Schrijf `frontend/tsconfig.json` en `frontend/eslint.config.mjs`**

```json
{ "extends": "./.nuxt/tsconfig.json" }
```

```js
import withNuxt from './.nuxt/eslint.config.mjs'

export default withNuxt()
```

- [ ] **Step 5: Schrijf `frontend/assets/css/tokens.css`** (de design-brief als CSS)

```css
/* Tokens uit docs/design-brief.md — wijzig ze dáár eerst, dan hier. */
:root {
  --inkt: #14213D;
  --papier: #FAFAF7;
  --wit: #FFFFFF;
  --lijn: #E2E4E3;
  --oker: #B98A2F;
  --oker-donker: #8A6A1F;
  --fout: #8C3A2E;
  --font-ui: 'Public Sans', system-ui, sans-serif;
  --font-citaat: 'Literata', Georgia, serif;
  --radius: 4px;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--papier);
  color: var(--inkt);
  font-family: var(--font-ui);
  font-size: 16px;
  line-height: 1.55;
}

a { color: var(--oker-donker); }

.label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 600;
  color: var(--oker-donker);
}
```

- [ ] **Step 6: Schrijf `frontend/app.vue` en `frontend/layouts/default.vue`**

```vue
<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
```

```vue
<template>
  <div class="app">
    <header class="siteheader">
      <NuxtLink to="/" class="merk">AiActWijzer</NuxtLink>
      <nav><NuxtLink to="/transparantie">Transparantie</NuxtLink></nav>
    </header>
    <main class="inhoud"><slot /></main>
    <footer class="sitefooter">
      <p>AiActWijzer geeft informatie, geen juridisch advies. Raadpleeg voor je eigen situatie een jurist.</p>
    </footer>
  </div>
</template>

<style scoped>
.app { min-height: 100vh; display: flex; flex-direction: column; }
.siteheader {
  display: flex; justify-content: space-between; align-items: baseline;
  padding: 20px 24px; border-bottom: 1px solid var(--lijn); background: var(--wit);
}
.merk { font-weight: 600; font-size: 18px; color: var(--inkt); text-decoration: none; }
.siteheader nav a { font-size: 14px; }
.inhoud { flex: 1; width: 100%; max-width: 960px; margin: 0 auto; padding: 32px 24px; }
.sitefooter {
  border-top: 1px solid var(--lijn); background: var(--wit);
  padding: 16px 24px; font-size: 13px; color: var(--inkt); opacity: 0.75;
}
.sitefooter p { margin: 0; }
</style>
```

- [ ] **Step 7: Installeer en verifieer**

```bash
cd frontend && npm install
npm run dev &
sleep 8 && curl -s localhost:3000 | grep -o "AiActWijzer" | head -1
kill %1
```

Verwacht: `AiActWijzer` in de HTML (404 op de root-pagina is oké zolang de layout rendert; pagina's komen in Task 3 — als Nuxt zonder `pages/` niet start, maak dan alvast een lege `frontend/pages/index.vue` met alleen `<template><div /></template>` en vervang die in Task 4).

- [ ] **Step 8: Commit**

```bash
git add .gitignore frontend/
git commit -m "Frontend-scaffold: Nuxt 3, design-tokens, self-hosted fonts, basislayout"
```

---

### Task 2: Pinia-store en API-koppeling

**Files:**
- Create: `frontend/stores/vraag.ts`, `frontend/vitest.config.ts`
- Test: `frontend/tests/vraag.spec.ts`

**Interfaces:**
- Produces: `useVraagStore` met state `{ bezig, fout, resultaat, actieveRef }`, actions `stel(vraag)`, `markeer(ref)`; types `Citaat { ref, fragment, bron }`, `AskAntwoord { antwoord, citaten, stand_van_wetgeving }`. Alle componenten gebruiken uitsluitend deze store.

- [ ] **Step 1: Schrijf `frontend/vitest.config.ts`**

```ts
import { fileURLToPath } from 'node:url'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [vue()],
  test: { environment: 'happy-dom' },
  resolve: { alias: { '~': fileURLToPath(new URL('.', import.meta.url)) } },
})
```

- [ ] **Step 2: Schrijf de falende tests `frontend/tests/vraag.spec.ts`**

```ts
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('ofetch', () => ({ $fetch: vi.fn() }))

import { $fetch } from 'ofetch'
import { useVraagStore } from '~/stores/vraag'

const ANTWOORD = {
  antwoord: 'Hoog risico [Artikel 6, lid 2].',
  citaten: [{ ref: 'Artikel 6, lid 2', fragment: 'Artikel 6, lid 2 (Kop): tekst', bron: 'Verordening (EU) 2024/1689' }],
  stand_van_wetgeving: 'juli 2026',
}

describe('vraagStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.mocked($fetch).mockReset()
  })

  it('zet resultaat na een geslaagde vraag', async () => {
    vi.mocked($fetch).mockResolvedValue(ANTWOORD)
    const store = useVraagStore()
    await store.stel('Is cv-screening hoog risico?')
    expect(store.resultaat?.citaten[0].ref).toBe('Artikel 6, lid 2')
    expect(store.bezig).toBe(false)
    expect(store.fout).toBe('')
  })

  it('vertaalt een API-fout naar een kalme NL-melding', async () => {
    vi.mocked($fetch).mockRejectedValue(new Error('502'))
    const store = useVraagStore()
    await store.stel('x')
    expect(store.resultaat).toBeNull()
    expect(store.fout).toContain('Probeer het opnieuw')
  })

  it('markeer zet de actieve ref', () => {
    const store = useVraagStore()
    store.markeer('Artikel 6, lid 2')
    expect(store.actieveRef).toBe('Artikel 6, lid 2')
  })
})
```

- [ ] **Step 3: Draai de tests, verwacht falen (module bestaat niet)**

```bash
cd frontend && npm run test
```

- [ ] **Step 4: Schrijf `frontend/stores/vraag.ts`**

```ts
// Enige API-koppeling van de frontend. ofetch expliciet geïmporteerd (niet de
// Nuxt-global) zodat kale vitest de module kan mocken.
import { $fetch } from 'ofetch'
import { defineStore } from 'pinia'

export interface Citaat {
  ref: string
  fragment: string
  bron: string
}

export interface AskAntwoord {
  antwoord: string
  citaten: Citaat[]
  stand_van_wetgeving: string
}

export const useVraagStore = defineStore('vraag', {
  state: () => ({
    bezig: false,
    fout: '',
    resultaat: null as AskAntwoord | null,
    actieveRef: '',
  }),
  actions: {
    async stel(vraag: string) {
      this.bezig = true
      this.fout = ''
      this.resultaat = null
      try {
        this.resultaat = await $fetch<AskAntwoord>('/api/ask', {
          method: 'POST',
          body: { vraag },
        })
      } catch {
        // Kalme melding, geen technische details — toon per design-brief §5
        this.fout = 'Het antwoord kon niet worden opgehaald. Probeer het opnieuw.'
      } finally {
        this.bezig = false
      }
    },
    markeer(ref: string) {
      this.actieveRef = ref
    },
  },
})
```

- [ ] **Step 5: Draai de tests, verwacht 3× PASS**

```bash
cd frontend && npm run test
```

- [ ] **Step 6: Commit**

```bash
git add frontend/stores/ frontend/tests/ frontend/vitest.config.ts
git commit -m "Vraag-store: enige API-koppeling, kalme foutmelding"
```

---

### Task 3: VraagFormulier en AntwoordWeergave

**Files:**
- Create: `frontend/components/VraagFormulier.vue`, `frontend/components/AntwoordWeergave.vue`
- Test: `frontend/tests/antwoord-weergave.spec.ts`, `frontend/tests/vraag-formulier.spec.ts`

**Interfaces:**
- Consumes: `useVraagStore`
- Produces: `<VraagFormulier />` (textarea + knop "Stel je vraag", disabled bij leeg/bezig); `<AntwoordWeergave />` (antwoordtekst waarin elke `[ref]` die in `resultaat.citaten` voorkomt een knop wordt die `markeer(ref)` aanroept en naar `#citaat-<ref>` scrollt; onbekende `[x]` blijft platte tekst).

- [ ] **Step 1: Schrijf de falende tests**

`frontend/tests/antwoord-weergave.spec.ts`:

```ts
import { createTestingPinia } from '@pinia/testing'
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import AntwoordWeergave from '~/components/AntwoordWeergave.vue'
import { useVraagStore } from '~/stores/vraag'

function maak(antwoord: string) {
  return mount(AntwoordWeergave, {
    global: {
      plugins: [createTestingPinia({
        createSpy: vi.fn,
        initialState: {
          vraag: {
            resultaat: {
              antwoord,
              citaten: [{ ref: 'Artikel 6, lid 2', fragment: 'f', bron: 'b' }],
              stand_van_wetgeving: 'juli 2026',
            },
          },
        },
      })],
    },
  })
}

describe('AntwoordWeergave', () => {
  it('maakt van een bekende ref een klikbare knop', async () => {
    const w = maak('Hoog risico [Artikel 6, lid 2].')
    const knop = w.find('button.refknop')
    expect(knop.text()).toBe('[Artikel 6, lid 2]')
    await knop.trigger('click')
    const store = useVraagStore()
    expect(store.markeer).toHaveBeenCalledWith('Artikel 6, lid 2')
  })

  it('laat een onbekende ref als platte tekst staan', () => {
    const w = maak('Zie [Artikel 99] hiervoor.')
    expect(w.find('button.refknop').exists()).toBe(false)
    expect(w.text()).toContain('[Artikel 99]')
  })
})
```

`frontend/tests/vraag-formulier.spec.ts`:

```ts
import { createTestingPinia } from '@pinia/testing'
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import VraagFormulier from '~/components/VraagFormulier.vue'
import { useVraagStore } from '~/stores/vraag'

function maak() {
  return mount(VraagFormulier, {
    global: { plugins: [createTestingPinia({ createSpy: vi.fn })] },
  })
}

describe('VraagFormulier', () => {
  it('knop is uitgeschakeld bij een lege vraag', () => {
    const w = maak()
    expect(w.find('button').attributes('disabled')).toBeDefined()
  })

  it('verstuurt de getrimde vraag naar de store', async () => {
    const w = maak()
    await w.find('textarea').setValue('  Is cv-screening hoog risico?  ')
    await w.find('form').trigger('submit')
    const store = useVraagStore()
    expect(store.stel).toHaveBeenCalledWith('Is cv-screening hoog risico?')
  })
})
```

- [ ] **Step 2: Draai de tests, verwacht falen (componenten bestaan niet)**

```bash
cd frontend && npm run test
```

- [ ] **Step 3: Schrijf `frontend/components/VraagFormulier.vue`**

```vue
<script setup lang="ts">
import { computed, ref } from 'vue'
import { useVraagStore } from '~/stores/vraag'

const store = useVraagStore()
const vraag = ref('')
const kanVersturen = computed(() => vraag.value.trim().length > 0 && !store.bezig)

function verstuur() {
  if (kanVersturen.value) store.stel(vraag.value.trim())
}
</script>

<template>
  <form class="vraagformulier" @submit.prevent="verstuur">
    <label class="label" for="vraag">Stel je vraag</label>
    <textarea
      id="vraag"
      v-model="vraag"
      rows="3"
      placeholder="Bijvoorbeeld: valt cv-screening met AI onder hoog risico?"
    />
    <button type="submit" :disabled="!kanVersturen">
      {{ store.bezig ? 'Bezig met zoeken in de wettekst…' : 'Stel je vraag' }}
    </button>
  </form>
</template>

<style scoped>
.vraagformulier { display: flex; flex-direction: column; gap: 8px; }
textarea {
  font-family: var(--font-ui); font-size: 16px; line-height: 1.55;
  padding: 12px; border: 1px solid var(--lijn); border-radius: var(--radius);
  background: var(--wit); color: var(--inkt); resize: vertical;
}
textarea:focus { outline: 2px solid var(--oker); outline-offset: 1px; }
button {
  align-self: flex-start;
  font-family: var(--font-ui); font-size: 15px; font-weight: 600;
  background: var(--inkt); color: var(--papier);
  border: none; border-radius: var(--radius); padding: 10px 18px; cursor: pointer;
}
button:disabled { opacity: 0.5; cursor: default; }
</style>
```

- [ ] **Step 4: Schrijf `frontend/components/AntwoordWeergave.vue`**

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { useVraagStore } from '~/stores/vraag'

const store = useVraagStore()

// Splits het antwoord op [ref]-patronen; alleen refs die echt als citaat zijn
// meegeleverd worden klikbaar — een niet-opgehaalde ref blijft platte tekst.
const delen = computed(() => {
  const resultaat = store.resultaat
  if (!resultaat) return []
  const bekend = new Set(resultaat.citaten.map((c) => c.ref))
  return resultaat.antwoord.split(/(\[[^\]]+\])/).map((stuk) => {
    const m = stuk.match(/^\[([^\]]+)\]$/)
    if (m && bekend.has(m[1])) return { type: 'ref' as const, ref: m[1], tekst: stuk }
    return { type: 'tekst' as const, ref: '', tekst: stuk }
  })
})

function ga(refNaam: string) {
  store.markeer(refNaam)
  document.getElementById(`citaat-${refNaam}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}
</script>

<template>
  <article class="antwoord" aria-label="Antwoord">
    <template v-for="(deel, i) in delen" :key="i">
      <button v-if="deel.type === 'ref'" class="refknop" type="button" @click="ga(deel.ref)">
        {{ deel.tekst }}
      </button>
      <span v-else>{{ deel.tekst }}</span>
    </template>
  </article>
</template>

<style scoped>
.antwoord { white-space: pre-wrap; }
.refknop {
  display: inline; padding: 0; border: none; background: none; cursor: pointer;
  font: inherit; color: var(--oker-donker); text-decoration: underline;
  text-underline-offset: 2px;
}
</style>
```

- [ ] **Step 5: Draai de tests, verwacht 4× PASS (plus de 3 van Task 2)**

```bash
cd frontend && npm run test
```

- [ ] **Step 6: Commit**

```bash
git add frontend/components/ frontend/tests/
git commit -m "Vraagformulier en antwoordweergave met klikbare refs"
```

---

### Task 4: CitaatPaneel, CitaatBlok en de indexpagina

**Files:**
- Create: `frontend/components/CitaatPaneel.vue`, `frontend/components/CitaatBlok.vue`, `frontend/pages/index.vue`
- Test: `frontend/tests/citaat-blok.spec.ts`

**Interfaces:**
- Consumes: `useVraagStore`, `Citaat`-type
- Produces: `<CitaatPaneel />` (lijst CitaatBlokken + stempel "stand van wetgeving: …"); `<CitaatBlok :citaat />` (id `citaat-<ref>`, highlight wanneer `actieveRef` matcht, dooft na 1,6 s); indexpagina die alles samenbrengt (antwoord links, paneel rechts op desktop; onder elkaar op mobiel).

- [ ] **Step 1: Schrijf de falende test `frontend/tests/citaat-blok.spec.ts`**

```ts
import { createTestingPinia } from '@pinia/testing'
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import CitaatBlok from '~/components/CitaatBlok.vue'

const CITAAT = {
  ref: 'Artikel 6, lid 2',
  fragment: 'Artikel 6, lid 2 (Classificatieregels): AI-systemen als bedoeld in bijlage III…',
  bron: 'Verordening (EU) 2024/1689',
}

describe('CitaatBlok', () => {
  it('toont ref als kopje, stript de prefix uit het fragment en toont de bron', () => {
    const w = mount(CitaatBlok, {
      props: { citaat: CITAAT },
      global: { plugins: [createTestingPinia({ createSpy: vi.fn })] },
    })
    expect(w.find('.artnr').text()).toBe('Artikel 6, lid 2')
    // De prefix "Artikel 6, lid 2 (…): " is dubbelop naast het kopje
    expect(w.find('.citaattekst').text()).toBe('AI-systemen als bedoeld in bijlage III…')
    expect(w.find('.bronregel').text()).toContain('Verordening (EU) 2024/1689')
    expect(w.attributes('id')).toBe('citaat-Artikel 6, lid 2')
  })
})
```

- [ ] **Step 2: Draai de test, verwacht falen**

```bash
cd frontend && npm run test
```

- [ ] **Step 3: Schrijf `frontend/components/CitaatBlok.vue`**

```vue
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useVraagStore, type Citaat } from '~/stores/vraag'

const props = defineProps<{ citaat: Citaat }>()
const store = useVraagStore()
const licht = ref(false)

// Korte highlight, daarna rust (design-brief §3) — geen blijvende markering.
watch(() => store.actieveRef, (nieuw) => {
  if (nieuw === props.citaat.ref) {
    licht.value = true
    setTimeout(() => {
      licht.value = false
      store.markeer('')
    }, 1600)
  }
})

// Het fragment draagt zijn eigen "ref (kop): "-prefix (kop-als-context voor
// retrieval); naast het artikelnummer-kopje is die prefix dubbelop.
const fragment = computed(() => props.citaat.fragment.replace(/^[^:]+:\s*/, ''))
</script>

<template>
  <blockquote :id="`citaat-${citaat.ref}`" class="citaatblok" :class="{ licht }">
    <span class="artnr label">{{ citaat.ref }}</span>
    <p class="citaattekst">{{ fragment }}</p>
    <footer class="bronregel">{{ citaat.bron }} · <span class="stempel-inline">stand: {{ store.resultaat?.stand_van_wetgeving }}</span></footer>
  </blockquote>
</template>

<style scoped>
.citaatblok {
  margin: 0 0 12px;
  border-left: 3px solid var(--oker);
  background: var(--papier);
  padding: 12px 14px;
  transition: background 0.4s ease;
}
.citaatblok.licht { background: #F3EBD8; }
.artnr { display: block; margin-bottom: 5px; }
.citaattekst {
  margin: 0;
  font-family: var(--font-citaat);
  font-size: 17px;
  line-height: 1.6;
  color: #1F2937;
}
.bronregel { font-size: 11.5px; margin-top: 8px; opacity: 0.7; }
</style>
```

- [ ] **Step 4: Schrijf `frontend/components/CitaatPaneel.vue`**

```vue
<script setup lang="ts">
import { useVraagStore } from '~/stores/vraag'

const store = useVraagStore()
</script>

<template>
  <aside class="citaatpaneel" aria-label="Bronnen uit de wettekst">
    <h2 class="label">Bronnen</h2>
    <p v-if="!store.resultaat?.citaten.length" class="geen">
      Dit antwoord verwijst niet naar een specifiek artikel.
    </p>
    <CitaatBlok v-for="c in store.resultaat?.citaten ?? []" :key="c.ref" :citaat="c" />
  </aside>
</template>

<style scoped>
.citaatpaneel { background: var(--wit); border: 1px solid var(--lijn); border-radius: var(--radius); padding: 16px; }
.citaatpaneel h2 { margin: 0 0 12px; }
.geen { font-size: 14px; opacity: 0.75; }
</style>
```

- [ ] **Step 5: Schrijf `frontend/pages/index.vue`** (vervang een eventuele placeholder uit Task 1)

```vue
<script setup lang="ts">
import { useVraagStore } from '~/stores/vraag'

const store = useVraagStore()
</script>

<template>
  <div>
    <section class="intro">
      <h1>Antwoorden over de EU AI Act, gegrond in de wettekst</h1>
      <p>
        Stel een vraag over de AI-verordening; elk antwoord verwijst naar het
        letterlijke artikel, met de actuele deadlines na de Digital Omnibus.
      </p>
    </section>

    <VraagFormulier />

    <p v-if="store.fout" class="fout">{{ store.fout }}</p>

    <div v-if="store.resultaat" class="resultaat">
      <div>
        <AntwoordWeergave />
        <p class="stempel">stand van wetgeving: {{ store.resultaat.stand_van_wetgeving }}</p>
      </div>
      <CitaatPaneel />
    </div>
  </div>
</template>

<style scoped>
.intro h1 { font-size: 26px; line-height: 1.3; margin: 0 0 8px; }
.intro p { margin: 0 0 24px; max-width: 60ch; }
.fout { color: var(--fout); margin-top: 16px; }
.resultaat {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 24px;
  margin-top: 28px;
}
.stempel { font-size: 12px; opacity: 0.7; margin-top: 16px; }
@media (max-width: 760px) {
  .resultaat { grid-template-columns: 1fr; }
}
</style>
```

- [ ] **Step 6: Draai alle tests, verwacht 8× PASS**

```bash
cd frontend && npm run test
```

- [ ] **Step 7: Commit**

```bash
git add frontend/components/ frontend/pages/ frontend/tests/
git commit -m "Citaat-paneel met highlight en indexpagina met actualiteits-stempel"
```

---

### Task 5: Transparantie-pagina

**Files:**
- Create: `frontend/pages/transparantie.vue`

**Interfaces:**
- Produces: statische pagina op `/transparantie` — productprincipe 1 (de tool is zijn eigen schoolvoorbeeld: art. 50-transparantie, model card, eigen risicoclassificatie).

- [ ] **Step 1: Schrijf `frontend/pages/transparantie.vue`**

```vue
<template>
  <article class="transparantie">
    <h1>Transparantie</h1>

    <section>
      <h2>Je praat met AI</h2>
      <p>
        AiActWijzer is een AI-systeem (artikel 50 van de AI-verordening vraagt
        dat we dat duidelijk zeggen). Antwoorden worden gegenereerd door een
        taalmodel en zijn uitsluitend gebaseerd op de bronnen hieronder — met
        bij elke claim een letterlijk citaat, zodat je het antwoord zelf kunt
        controleren.
      </p>
    </section>

    <section>
      <h2>Model en hosting</h2>
      <p>
        Generatie en embeddings draaien via de API van Mistral AI (EU-gehost).
        De zoekindex en de wettekst staan in onze eigen database; er gaat geen
        data naar niet-Europese clouddiensten.
      </p>
    </section>

    <section>
      <h2>Bronnen en actualiteit</h2>
      <p>
        Het corpus bestaat uit de Nederlandse taalversie van Verordening (EU)
        2024/1689 (de AI-verordening), de tijdlijnwijzigingen uit de Digital
        Omnibus on AI (juli 2026) en geselecteerde Nederlandse bronnen over
        toezicht (UAIV). Elke bron is met versie en datum geadministreerd; elk
        antwoord draagt een stempel met de stand van de wetgeving. Wijzigt de
        wet, dan wordt het corpus bijgewerkt en de kwaliteitscontrole opnieuw
        gedraaid.
      </p>
    </section>

    <section>
      <h2>Onze eigen risicoclassificatie</h2>
      <p>
        AiActWijzer valt zelf onder de AI-verordening. Het is geen
        hoog-risico-toepassing uit bijlage III; er geldt wel de
        transparantieplicht van artikel 50 — deze pagina is daar de invulling
        van. De kwaliteitscontrole (een herhaalbare testset met
        controleerbare uitkomsten) is onderdeel van de broncode.
      </p>
    </section>

    <section>
      <h2>Informatie, geen advies</h2>
      <p>
        Antwoorden zijn een startpunt voor je eigen jurist, geen vervanging.
        Bij vragen over jouw specifieke situatie verwijst AiActWijzer bewust
        door in plaats van te gokken.
      </p>
    </section>

    <section>
      <h2>Privacy</h2>
      <p>
        Er zijn geen accounts. Vragen worden niet opgeslagen en niet gebruikt
        als trainings- of testdata.
      </p>
    </section>
  </article>
</template>

<style scoped>
.transparantie { max-width: 68ch; }
.transparantie h1 { font-size: 26px; margin: 0 0 20px; }
.transparantie h2 { font-size: 17px; margin: 24px 0 6px; }
.transparantie p { margin: 0; }
</style>
```

- [ ] **Step 2: Verifieer dat de pagina rendert**

```bash
cd frontend && npm run dev &
sleep 8 && curl -s localhost:3000/transparantie | grep -o "Je praat met AI" | head -1
kill %1
```

Verwacht: `Je praat met AI`.

- [ ] **Step 3: Commit**

```bash
git add frontend/pages/transparantie.vue
git commit -m "Transparantie-pagina: art. 50-invulling, model card, eigen classificatie"
```

---

### Task 6: End-to-end tegen de echte API, lint en afronding

**Files:**
- Modify: `README.md` (frontend-sectie toevoegen)

**Interfaces:**
- Consumes: alles hiervoor; de backend uit bouwsteen 1.

- [ ] **Step 1: Start backend en frontend samen**

```bash
docker compose up -d
PYTHONPATH=backend .venv/bin/uvicorn app.main:app --port 8000 &
cd frontend && npm run dev &
sleep 8
```

- [ ] **Step 2: Rooktest de proxy en de volledige keten** (echte Mistral-call, centen)

```bash
curl -s -X POST localhost:3000/api/ask -H 'content-type: application/json' \
  -d '{"vraag": "Valt cv-screening met AI onder hoog risico?"}' | head -c 400
```

Verwacht: JSON met `antwoord` en `citaten` — de proxy werkt. Controleer daarna in de browser op `localhost:3000`: stel dezelfde vraag via het formulier, zie het antwoord met klikbare refs, klik een ref en zie het citaatblok oplichten en in beeld scrollen; controleer de stempel en de footer-regel; bekijk `/transparantie`. Controleer het mobiele gedrag (smal venster: paneel onder het antwoord). Leg wat je zag vast in je rapport — dit is de echte verificatie van het signatuur-element.

- [ ] **Step 3: Lint en volledige tests**

```bash
cd frontend && npm run lint && npm run test
cd .. && .venv/bin/pytest
```

Verwacht: lint schoon, 8 frontend-tests groen, 25 backend-tests groen.

- [ ] **Step 4: Stop de dev-processen en voeg de frontend-sectie aan `README.md` toe** (na het Snelstart-blok)

````markdown
## Frontend

```bash
cd frontend && npm install
npm run dev            # UI op :3000, praat via /api met de backend op :8000
npm run test           # componenttests (vitest)
npm run lint
```

Ontwerp-tokens en signatuur-element: `docs/design-brief.md`.
````

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "Bouwsteen 2 afgerond: frontend end-to-end geverifieerd, README"
```

---

## Zelfreview (uitgevoerd bij het schrijven)

- **Brief-dekking:** tokens als CSS-variabelen (T1), fonts self-hosted (T1), citaat-paneel per §3 incl. highlight-en-doof (T4), klikbare refs (T3), stempel altijd zichtbaar (T4: bij antwoord én in bronregel), footer-regel geen-advies (T1), transparantie-pagina (T5), verboden-register nergens gebruikt in copy. Kale Nuxt zonder @nuxt/ui conform gebruikerskeuze.
- **Typeconsistentie:** `Citaat`/`AskAntwoord`/`useVraagStore` (T2) ↔ componenten (T3/T4); `markeer`/`actieveRef` ↔ AntwoordWeergave/CitaatBlok; id-formaat `citaat-<ref>` consistent tussen T3 (scroll) en T4 (blok).
- **Open risico (bewust):** npm-versieranges kunnen verschuiven (T1 bevat de afhandelingsinstructie); Nuxt-zonder-pages-gedrag in T1 heeft een expliciete fallback.
