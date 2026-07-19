import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('ofetch', () => ({ $fetch: vi.fn() }))

import { $fetch } from 'ofetch'
import { useVraagStore } from '~/stores/vraag'

const ANTWOORD = {
  antwoord: 'Hoog risico [Artikel 6, lid 2].',
  citaten: [{ ref: 'Artikel 6, lid 2', fragment: 'Artikel 6, lid 2 (Kop): tekst', bron: 'Verordening (EU) 2024/1689', url: 'https://example.org' }],
  stand_van_wetgeving: 'juli 2026',
}

describe('vraagStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.mocked($fetch).mockReset()
  })

  it('zet resultaat na een geslaagde vraag', async () => {
    vi.mocked($fetch).mockResolvedValue(ANTWOORD)
    const store = useVraagStore()
    await store.stel('Is cv-screening hoog risico?')
    expect(store.resultaat?.citaten[0].ref).toBe('Artikel 6, lid 2')
    expect(store.bezig).toBe(false)
    expect(store.fout).toBe('')
  })

  it('vertaalt een API-fout naar een kalme NL-melding', async () => {
    vi.mocked($fetch).mockRejectedValue(new Error('502'))
    const store = useVraagStore()
    await store.stel('x')
    expect(store.resultaat).toBeNull()
    expect(store.fout).toContain('Probeer het opnieuw')
  })

  it('markeer zet de actieve ref', () => {
    const store = useVraagStore()
    store.markeer('Artikel 6, lid 2')
    expect(store.actieveRef).toBe('Artikel 6, lid 2')
  })
})
