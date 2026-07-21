import { createTestingPinia } from '@pinia/testing'
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import VraagFormulier from '~/components/VraagFormulier.vue'
import { useVraagStore } from '~/stores/vraag'

function maak(initialState: Record<string, unknown> = {}) {
  return mount(VraagFormulier, {
    global: {
      plugins: [createTestingPinia({ createSpy: vi.fn, initialState: { vraag: initialState } })],
    },
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

  it('stelt een voorbeeldvraag direct en vult de textarea', async () => {
    const w = maak()
    const eerste = w.find('.voorbeelden button')
    expect(eerste.exists()).toBe(true)
    const tekst = eerste.text()
    await eerste.trigger('click')
    const store = useVraagStore()
    expect(store.stel).toHaveBeenCalledWith(tekst)
    // Textarea meevullen: de bezoeker ziet zo wélke vraag er gesteld is.
    expect((w.find('textarea').element as HTMLTextAreaElement).value).toBe(tekst)
  })

  it('verbergt de voorbeelden zodra er een resultaat is', () => {
    const w = maak({
      resultaat: { antwoord: 'a', citaten: [], stand_van_wetgeving: 'juli 2026' },
    })
    expect(w.find('.voorbeelden').exists()).toBe(false)
  })

  it('verbergt de voorbeelden tijdens het zoeken', () => {
    const w = maak({ bezig: true })
    expect(w.find('.voorbeelden').exists()).toBe(false)
  })
})
