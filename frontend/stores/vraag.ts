// Enige API-koppeling van de frontend. ofetch expliciet geïmporteerd (niet de
// Nuxt-global) zodat kale vitest de module kan mocken.
import { $fetch } from 'ofetch'
import { defineStore } from 'pinia'

export interface Citaat {
  ref: string
  fragment: string
  bron: string
  url: string
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
    // Onthouden voor "Probeer opnieuw" bij een mislukte aanroep.
    laatsteVraag: '',
    // Textarea-inhoud leeft in de store, zodat wis() óók het formulier leegt.
    invoer: '',
  }),
  actions: {
    async stel(vraag: string) {
      this.laatsteVraag = vraag
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
    async opnieuw() {
      if (this.laatsteVraag) await this.stel(this.laatsteVraag)
    },
    // Terug naar de begintoestand (logo-klik en "Stel een nieuwe vraag").
    // Bewust een eigen actie i.p.v. Pinia's $reset: bezig hoort er niet bij
    // (een lopende aanroep afbreken is een ander gebaar) en een actie is
    // in tests als spy zichtbaar.
    wis() {
      this.fout = ''
      this.resultaat = null
      this.actieveRef = ''
      this.laatsteVraag = ''
      this.invoer = ''
    },
    markeer(ref: string) {
      this.actieveRef = ref
    },
  },
})
