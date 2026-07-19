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
