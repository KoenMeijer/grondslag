import { createTestingPinia } from '@pinia/testing'
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import InzendVak from '~/components/InzendVak.vue'
import { useVraagStore } from '~/stores/vraag'

// Het vak zelf gaat alleen over de inzendflow; of het vak überhaupt getoond
// wordt (alleen bij geen_bron) is de verantwoordelijkheid van de pagina.
function maak(initialState: Record<string, unknown> = {}) {
  return mount(InzendVak, {
    global: {
      plugins: [createTestingPinia({ createSpy: vi.fn, initialState: { vraag: initialState } })],
    },
  })
}

describe('InzendVak', () => {
  it('toont uitleg en een knop die de inzendactie aanroept', async () => {
    const w = maak({ laatsteVraag: 'x' })
    expect(w.text()).toContain('anoniem')
    expect(w.text()).toContain('alleen de vraagtekst')
    await w.find('button').trigger('click')
    expect(useVraagStore().zendIn).toHaveBeenCalled()
  })

  it('toont na inzenden een dankmelding zonder knop', () => {
    const w = maak({ ingezonden: true })
    expect(w.text()).toContain('Dank')
    expect(w.find('button').exists()).toBe(false)
  })

  it('toont een inzendfout als kalme melding', () => {
    const w = maak({ inzendFout: 'Versturen is niet gelukt. Probeer het opnieuw.' })
    expect(w.text()).toContain('niet gelukt')
    expect(w.find('button').exists()).toBe(true)
  })
})
