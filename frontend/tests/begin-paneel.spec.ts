import { createTestingPinia } from '@pinia/testing'
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import BeginPaneel from '~/components/BeginPaneel.vue'

function maak() {
  return mount(BeginPaneel, {
    global: { plugins: [createTestingPinia({ createSpy: vi.fn })] },
  })
}

describe('BeginPaneel', () => {
  it('toont het artikel 50-citaat met EUR-Lex-link', () => {
    const w = maak()
    expect(w.text()).toContain('Artikel 50, lid 1')
    expect(w.text()).toContain('interageren met een AI-systeem')
    const link = w.find('a[href*="eur-lex.europa.eu"]')
    expect(link.exists()).toBe(true)
  })

  it('toont de omnibus-tijdlijn met de nieuwe én de vervallen deadline', () => {
    const w = maak()
    // De actualiteits-USP: de verschoven datum mét de vervallen datum erbij,
    // want het internet noemt massaal nog de oude.
    expect(w.text()).toContain('2 dec 2027')
    expect(w.text()).toContain('2 augustus 2026')
    expect(w.text()).toContain('Verboden praktijken')
  })

  it('draagt de actualiteits-stempel', () => {
    const w = maak()
    expect(w.text()).toContain('stand: juli 2026')
  })
})
