import { createTestingPinia } from '@pinia/testing'
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import CitaatBlok from '~/components/CitaatBlok.vue'

const CITAAT = {
  ref: 'Artikel 6, lid 2',
  fragment: 'Artikel 6, lid 2 (Classificatieregels): AI-systemen als bedoeld in bijlage III…',
  bron: 'Verordening (EU) 2024/1689',
  url: 'https://example.org',
}

describe('CitaatBlok', () => {
  it('toont ref als kopje, stript de prefix uit het fragment en toont de bron', () => {
    const w = mount(CitaatBlok, {
      props: { citaat: CITAAT },
      global: { plugins: [createTestingPinia({ createSpy: vi.fn })] },
    })
    expect(w.find('.artnr').text()).toBe('Artikel 6, lid 2')
    // De prefix "Artikel 6, lid 2 (…): " is dubbelop naast het kopje
    expect(w.find('.citaattekst').text()).toBe('AI-systemen als bedoeld in bijlage III…')
    expect(w.find('.bronregel').text()).toContain('Verordening (EU) 2024/1689')
    expect(w.attributes('id')).toBe('citaat-Artikel 6, lid 2')
    const link = w.find('.bronregel a')
    expect(link.text()).toBe('bekijk de bron')
    expect(link.attributes('href')).toBe('https://example.org')
  })

  it('verankert de prefix-strip op de ref, zodat een dubbelepunt in de kop het citaat niet verminkt', () => {
    const citaat = {
      ref: 'Toezicht: rolverdeling',
      fragment: 'Toezicht: rolverdeling: De AP coördineert.',
      bron: 'B',
      url: 'https://example.org',
    }
    const w = mount(CitaatBlok, {
      props: { citaat },
      global: { plugins: [createTestingPinia({ createSpy: vi.fn })] },
    })
    expect(w.find('.citaattekst').text()).toBe('De AP coördineert.')
  })
})
