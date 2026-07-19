import { createTestingPinia } from '@pinia/testing'
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import VraagFormulier from '~/components/VraagFormulier.vue'
import { useVraagStore } from '~/stores/vraag'

function maak() {
  return mount(VraagFormulier, {
    global: { plugins: [createTestingPinia({ createSpy: vi.fn })] },
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
})
