import { createTestingPinia } from '@pinia/testing'
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import AntwoordWeergave from '~/components/AntwoordWeergave.vue'
import { useVraagStore } from '~/stores/vraag'

function maak(
  antwoord: string,
  citaten = [{ ref: 'Artikel 6, lid 2', fragment: 'f', bron: 'b', url: 'https://example.org' }],
) {
  return mount(AntwoordWeergave, {
    global: {
      plugins: [createTestingPinia({
        createSpy: vi.fn,
        initialState: {
          vraag: {
            resultaat: {
              antwoord,
              citaten,
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

  it('koppelt een verfijnde ref aan het citaat waarvan de ref een prefix is', async () => {
    const w = maak('Zie [Artikel 6, lid 2, onder a)].')
    const knop = w.find('button.refknop')
    expect(knop.exists()).toBe(true)
    expect(knop.text()).toBe('[Artikel 6, lid 2, onder a)]')
    await knop.trigger('click')
    const store = useVraagStore()
    expect(store.markeer).toHaveBeenCalledWith('Artikel 6, lid 2')
  })

  it('kiest bij meerdere passende citaten de langste prefix', async () => {
    const w = maak('Zie [Artikel 6, lid 2].', [
      { ref: 'Artikel 6', fragment: 'f', bron: 'b', url: 'https://example.org' },
      { ref: 'Artikel 6, lid 2', fragment: 'f', bron: 'b', url: 'https://example.org' },
    ])
    await w.find('button.refknop').trigger('click')
    const store = useVraagStore()
    expect(store.markeer).toHaveBeenCalledWith('Artikel 6, lid 2')
  })
})
