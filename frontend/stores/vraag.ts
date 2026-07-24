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
  geen_bron: boolean
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
    // Opt-in-inzending na een onbeantwoorde vraag (zie InzendVak).
    ingezonden: false,
    inzendFout: '',
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
      } catch (e) {
        // Kalme melding, geen technische details — toon per design-brief §5.
        // 429 apart: dat is geen storing maar de snelheidslimiet, en dan is
        // "probeer het opnieuw" juist het verkeerde advies.
        const status = (e as { response?: { status?: number } })?.response?.status
        this.fout = status === 429
          ? 'Er komen op dit moment veel vragen binnen. Na kort wachten kun je het opnieuw proberen.'
          : 'Het antwoord kon niet worden opgehaald. Probeer het opnieuw.'
      } finally {
        this.bezig = false
      }
    },
    async opnieuw() {
      if (this.laatsteVraag) await this.stel(this.laatsteVraag)
    },
    // Opt-in: stuurt alléén de vraagtekst in, en alleen na een expliciete klik.
    async zendIn() {
      if (!this.laatsteVraag || this.ingezonden) return
      this.inzendFout = ''
      try {
        await $fetch('/api/inzending', {
          method: 'POST',
          body: { vraag: this.laatsteVraag },
        })
        this.ingezonden = true
      } catch (e) {
        const status = (e as { response?: { status?: number } })?.response?.status
        this.inzendFout = status === 429
          ? 'Vandaag zijn er al veel inzendingen — probeer het morgen opnieuw.'
          : 'Versturen is niet gelukt. Probeer het opnieuw.'
      }
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
      this.ingezonden = false
      this.inzendFout = ''
    },
    markeer(ref: string) {
      this.actieveRef = ref
    },
  },
})
