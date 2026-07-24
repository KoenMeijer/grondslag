import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { $fetch } from 'ofetch'
import { useVraagStore } from '~/stores/vraag'

vi.mock('ofetch', () => ({ $fetch: vi.fn() }))

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

  it('vertaalt een 429 naar een uitleg over de limiet, niet naar een storing', async () => {
    vi.mocked($fetch).mockRejectedValue({ response: { status: 429 } })
    const store = useVraagStore()
    await store.stel('Is cv-screening hoog risico?')
    expect(store.fout).toContain('kort wachten')
    expect(store.fout).not.toContain('Probeer het opnieuw.')
  })

  it('markeer zet de actieve ref', () => {
    const store = useVraagStore()
    store.markeer('Artikel 6, lid 2')
    expect(store.actieveRef).toBe('Artikel 6, lid 2')
  })

  it('opnieuw herhaalt de laatst gestelde vraag', async () => {
    vi.mocked($fetch).mockRejectedValueOnce(new Error('502')).mockResolvedValueOnce(ANTWOORD)
    const store = useVraagStore()
    await store.stel('Is cv-screening hoog risico?')
    expect(store.fout).not.toBe('')
    await store.opnieuw()
    expect(store.fout).toBe('')
    expect(store.resultaat?.citaten[0].ref).toBe('Artikel 6, lid 2')
    expect(vi.mocked($fetch)).toHaveBeenLastCalledWith('/api/ask', {
      method: 'POST',
      body: { vraag: 'Is cv-screening hoog risico?' },
    })
  })

  it('opnieuw zonder eerdere vraag doet niets', async () => {
    const store = useVraagStore()
    await store.opnieuw()
    expect(vi.mocked($fetch)).not.toHaveBeenCalled()
  })

  it('wis brengt de store terug naar de begintoestand', async () => {
    vi.mocked($fetch).mockResolvedValue(ANTWOORD)
    const store = useVraagStore()
    store.invoer = 'Is cv-screening hoog risico?'
    await store.stel(store.invoer)
    store.wis()
    expect(store.resultaat).toBeNull()
    expect(store.fout).toBe('')
    expect(store.invoer).toBe('')
    expect(store.laatsteVraag).toBe('')
    expect(store.actieveRef).toBe('')
  })

  it('zendIn stuurt de laatste vraag naar /api/inzending en markeert ingezonden', async () => {
    vi.mocked($fetch).mockResolvedValue(undefined)
    const store = useVraagStore()
    store.laatsteVraag = 'Wat zegt de verordening over cookiebanners?'
    await store.zendIn()
    expect(vi.mocked($fetch)).toHaveBeenCalledWith('/api/inzending', {
      method: 'POST',
      body: { vraag: 'Wat zegt de verordening over cookiebanners?' },
    })
    expect(store.ingezonden).toBe(true)
    expect(store.inzendFout).toBe('')
  })

  it('zendIn zonder eerdere vraag doet niets', async () => {
    const store = useVraagStore()
    await store.zendIn()
    expect(vi.mocked($fetch)).not.toHaveBeenCalled()
    expect(store.ingezonden).toBe(false)
  })

  it('zendIn vertaalt de dagcap (429) naar een kalme melding', async () => {
    vi.mocked($fetch).mockRejectedValue({ response: { status: 429 } })
    const store = useVraagStore()
    store.laatsteVraag = 'x'
    await store.zendIn()
    expect(store.ingezonden).toBe(false)
    expect(store.inzendFout).toContain('morgen')
  })

  it('zendIn vertaalt een storing naar een probeer-opnieuw-melding', async () => {
    vi.mocked($fetch).mockRejectedValue(new Error('502'))
    const store = useVraagStore()
    store.laatsteVraag = 'x'
    await store.zendIn()
    expect(store.ingezonden).toBe(false)
    expect(store.inzendFout).toContain('opnieuw')
  })

  it('wis zet ook de inzendstatus terug', () => {
    const store = useVraagStore()
    store.ingezonden = true
    store.inzendFout = 'melding'
    store.wis()
    expect(store.ingezonden).toBe(false)
    expect(store.inzendFout).toBe('')
  })
})
