import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import OverPagina from '~/pages/over.vue'
import WetCitaat from '~/components/WetCitaat.vue'

const NuxtLink = { template: '<a :href="to"><slot /></a>', props: ['to'] }

function maak() {
  // WetCitaat expliciet registreren: kale vitest kent Nuxts auto-import niet.
  return mount(OverPagina, { global: { components: { WetCitaat }, stubs: { NuxtLink } } })
}

describe('over-pagina', () => {
  it('beantwoordt waarom, wie en wat er nog komt — gegrond', () => {
    const w = maak()
    expect(w.find('h1').text()).toBe('Over de AI-verordening')
    // Waarom: het doel uit de wettekst zelf
    expect(w.text()).toContain('Artikel 1, lid 1')
    expect(w.text()).toContain('mensgerichte en betrouwbare')
    // Wie: verordening werkt rechtstreeks; NL regelt alleen toezicht (UAIV)
    expect(w.text()).toContain('Europees Parlement')
    expect(w.text()).toContain('UAIV')
    // Toekomst: de evaluatiemomenten die de wet zelf inplant
    expect(w.text()).toContain('Artikel 112')
    expect(w.text()).toContain('2 augustus 2028')
    // Gegrond: bron-link naar EUR-Lex aanwezig
    expect(w.find('a[href*="eur-lex.europa.eu"]').exists()).toBe(true)
  })

  it('eindigt met een kalme uitnodiging terug naar de vraagpagina', () => {
    const w = maak()
    const naarHuis = w.findAll('a[href="/"]').map((a) => a.text())
    expect(naarHuis).toContain('Stel je vraag')
  })
})
