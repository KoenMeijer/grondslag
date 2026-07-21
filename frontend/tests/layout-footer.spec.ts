import { createTestingPinia } from '@pinia/testing'
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import Layout from '~/layouts/default.vue'

// NuxtLink is een Nuxt-global; in kale vitest volstaat een anker-stub.
const NuxtLink = { template: '<a :href="to"><slot /></a>', props: ['to'] }

function maak() {
  return mount(Layout, {
    global: {
      stubs: { NuxtLink },
      plugins: [createTestingPinia({ createSpy: vi.fn })],
    },
  })
}

describe('footer', () => {
  it('draagt de disclaimer en de drie links', () => {
    const w = maak()
    const footer = w.find('.sitefooter')
    expect(footer.text()).toContain('geen juridisch advies')
    expect(footer.find('a[href="/transparantie"]').exists()).toBe(true)
    // Op mobiel is de footer de enige navigatie (header-nav is dan verborgen),
    // dus beide pagina's moeten hier bereikbaar zijn.
    expect(footer.find('a[href="/over"]').exists()).toBe(true)
    const eurlex = footer.find('a[href*="eur-lex.europa.eu"]')
    expect(eurlex.text()).toContain('EUR-Lex')
    const maker = footer.find('a[href*="linkedin.com/in/koenmeijer"]')
    expect(maker.text()).toBe('Gemaakt door Koen Meijer')
    expect(maker.attributes('rel')).toContain('noopener')
  })
})
