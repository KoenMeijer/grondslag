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
    // De footer draagt alle links (ook op mobiel bereikbaar naast de
    // bottom-tabbalk), dus beide pagina's moeten hier staan.
    expect(footer.find('a[href="/over"]').exists()).toBe(true)
    const eurlex = footer.find('a[href*="eur-lex.europa.eu"]')
    expect(eurlex.text()).toContain('EUR-Lex')
    const maker = footer.find('a[href*="linkedin.com/in/koen-meijer-5b47239"]')
    expect(maker.text()).toBe('Gemaakt door Koen Meijer')
    expect(maker.attributes('rel')).toContain('noopener')
    const broncode = footer.find('a[href*="github.com/KoenMeijer/grondslag"]')
    expect(broncode.text()).toBe('Broncode op GitHub')
    expect(broncode.attributes('rel')).toContain('noopener')
  })
})

describe('mobiele bottom-tabbalk', () => {
  it('draagt de drie hoofdpagina-links', () => {
    const menu = maak().find('.mobielmenu')
    expect(menu.exists()).toBe(true)
    expect(menu.attributes('aria-label')).toBe('Hoofdmenu')
    expect(menu.find('a[href="/nieuws"]').exists()).toBe(true)
    expect(menu.find('a[href="/over"]').exists()).toBe(true)
    expect(menu.find('a[href="/transparantie"]').exists()).toBe(true)
  })
})
