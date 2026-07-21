import { createTestingPinia } from '@pinia/testing'
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import IndexPagina from '~/pages/index.vue'
import { useVraagStore } from '~/stores/vraag'

// Kale vitest kent Nuxt's auto-import niet; de kindcomponenten zijn hier
// niet het onderwerp — alleen wélke kolominhoud de pagina toont.
const STUBS = {
  VraagFormulier: { template: '<form class="stub-formulier" />' },
  BeginPaneel: { template: '<aside class="stub-beginpaneel" />' },
  AntwoordWeergave: { template: '<article class="stub-antwoord" />' },
  CitaatPaneel: { template: '<aside class="stub-citaatpaneel" />' },
}

function maak(initialState: Record<string, unknown> = {}) {
  return mount(IndexPagina, {
    global: {
      stubs: STUBS,
      plugins: [createTestingPinia({ createSpy: vi.fn, initialState: { vraag: initialState } })],
    },
  })
}

describe('index-pagina (kolomwissel rechts)', () => {
  it('toont in rust het beginpaneel, geen status of bronnen', () => {
    const w = maak()
    expect(w.find('.stub-beginpaneel').exists()).toBe(true)
    expect(w.find('.zoekstatus').exists()).toBe(false)
    expect(w.find('.stub-citaatpaneel').exists()).toBe(false)
  })

  it('toont tijdens het zoeken de statusregel op de bronnen-plek', () => {
    const w = maak({ bezig: true })
    expect(w.find('.zoekstatus').text()).toContain('Zoeken in de wettekst')
    expect(w.find('.stub-beginpaneel').exists()).toBe(false)
  })

  it('toont bij een fout een probeer-opnieuw-knop die de vraag herhaalt', async () => {
    const w = maak({ fout: 'Het antwoord kon niet worden opgehaald. Probeer het opnieuw.' })
    const knop = w.find('.foutvak button')
    expect(knop.text()).toBe('Probeer opnieuw')
    await knop.trigger('click')
    const store = useVraagStore()
    expect(store.opnieuw).toHaveBeenCalled()
  })

  it('toont na een antwoord het antwoord en de echte bronnen', () => {
    const w = maak({
      resultaat: { antwoord: 'a', citaten: [], stand_van_wetgeving: 'juli 2026' },
    })
    expect(w.find('.stub-antwoord').exists()).toBe(true)
    expect(w.find('.stub-citaatpaneel').exists()).toBe(true)
    expect(w.find('.stub-beginpaneel').exists()).toBe(false)
  })

  it('biedt onder het antwoord een link terug naar de begintoestand', async () => {
    const w = maak({
      resultaat: { antwoord: 'a', citaten: [], stand_van_wetgeving: 'juli 2026' },
    })
    const link = w.find('.nieuwevraag')
    expect(link.text()).toBe('Stel een nieuwe vraag')
    await link.trigger('click')
    const store = useVraagStore()
    expect(store.wis).toHaveBeenCalled()
  })
})
