<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { $fetch } from 'ofetch'

// Losse, insluitbare mini-versie van de vraagtool. Geen app-chrome (layout:false)
// en niet indexeren — dit is een widget-doel, geen contentpagina. Praat
// same-origin met /api/ask, dus geen CORS nodig.
definePageMeta({ layout: false })
useSeoMeta({ title: 'Vraag het aan Grondslag', robots: 'noindex, nofollow' })

interface Citaat { ref: string, fragment: string, bron: string, url: string }
interface Antwoord { antwoord: string, citaten: Citaat[], stand_van_wetgeving: string, geen_bron: boolean }

const vraag = ref('')
const bezig = ref(false)
const fout = ref('')
const resultaat = ref<Antwoord | null>(null)

async function vraagStellen() {
  if (!vraag.value.trim() || bezig.value) return
  bezig.value = true
  fout.value = ''
  resultaat.value = null
  try {
    resultaat.value = await $fetch<Antwoord>('/api/ask', { method: 'POST', body: { vraag: vraag.value } })
  } catch (e) {
    const status = (e as { statusCode?: number, response?: { status?: number } })
    fout.value = (status.statusCode === 429 || status.response?.status === 429)
      ? 'Te veel vragen in korte tijd. Probeer het zo opnieuw.'
      : 'Er ging iets mis. Probeer het later opnieuw.'
  } finally {
    bezig.value = false
  }
}

// Hoogte naar de insluitende pagina posten zodat widget.js de iframe meeschaalt.
let ro: ResizeObserver | undefined
onMounted(() => {
  const meld = () => window.parent?.postMessage(
    { type: 'grondslag:height', height: document.documentElement.scrollHeight }, '*')
  ro = new ResizeObserver(meld)
  ro.observe(document.documentElement)
  meld()
})
onBeforeUnmount(() => ro?.disconnect())
</script>

<template>
  <div class="embed">
    <form class="invoer" @submit.prevent="vraagStellen">
      <label for="v" class="label">Vraag over de AI-verordening</label>
      <textarea id="v" v-model="vraag" rows="3" placeholder="Bijv. Valt cv-screening onder de AI Act?" />
      <button type="submit" :disabled="bezig">{{ bezig ? 'Zoeken…' : 'Vraag het' }}</button>
    </form>

    <p v-if="fout" class="fout" role="alert">{{ fout }}</p>

    <div v-if="resultaat" class="antwoord">
      <p class="tekst">{{ resultaat.antwoord }}</p>
      <ul v-if="resultaat.citaten.length" class="citaten">
        <li v-for="c in resultaat.citaten" :key="c.ref">
          <span class="ref">{{ c.ref }}</span>
          <a :href="c.url" target="_blank" rel="noopener">{{ c.bron }}</a>
        </li>
      </ul>
      <p class="stempel">stand van wetgeving: {{ resultaat.stand_van_wetgeving }}</p>
    </div>

    <p class="merk">
      <a href="https://grondslag.eu" target="_blank" rel="noopener">Grondslag</a> —
      informatie, geen juridisch advies
    </p>
  </div>
</template>

<style scoped>
.embed {
  font-family: var(--font-ui, system-ui, sans-serif);
  color: var(--inkt, #14213D); background: var(--papier, #FAFAF7);
  padding: 16px; box-sizing: border-box;
}
.invoer { display: flex; flex-direction: column; gap: 8px; }
.label { font-size: 13px; font-weight: 600; }
textarea {
  width: 100%; box-sizing: border-box; padding: 10px; font: inherit;
  border: 1px solid var(--lijn, #E2E4E3); border-radius: 4px; resize: vertical;
}
button {
  align-self: flex-start; padding: 8px 16px; font: inherit; font-weight: 600;
  color: #fff; background: var(--oker-donker, #8A6A1F);
  border: 0; border-radius: 4px; cursor: pointer;
}
button:disabled { opacity: 0.6; cursor: default; }
.fout { color: var(--fout, #8C3A2E); font-size: 14px; }
.antwoord { margin-top: 14px; }
.tekst { margin: 0 0 10px; line-height: 1.5; }
.citaten { margin: 0 0 8px; padding-left: 18px; font-size: 14px; }
.ref { font-weight: 600; margin-right: 6px; }
.stempel { font-size: 12px; opacity: 0.7; margin: 0; }
.merk { margin: 14px 0 0; font-size: 12px; opacity: 0.7; }
.merk a { color: var(--oker-donker, #8A6A1F); }
</style>
