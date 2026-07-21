import { createTestingPinia } from '@pinia/testing'
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import IndexPagina from '~/pages/index.vue'

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

  it('toont na een antwoord het antwoord en de echte bronnen', () => {
    const w = maak({
      resultaat: { antwoord: 'a', citaten: [], stand_van_wetgeving: 'juli 2026' },
    })
    expect(w.find('.stub-antwoord').exists()).toBe(true)
    expect(w.find('.stub-citaatpaneel').exists()).toBe(true)
    expect(w.find('.stub-beginpaneel').exists()).toBe(false)
  })
})
