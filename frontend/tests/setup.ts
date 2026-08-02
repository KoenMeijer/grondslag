// Kale vitest kent Nuxts auto-imports niet. De composables die onze componenten
// gebruiken worden hier als no-op gestubd: de tests gaan over ons gedrag, niet
// over dat van Nuxt.
import { vi } from 'vitest'

vi.stubGlobal('useHead', () => {})
vi.stubGlobal('useSeoMeta', () => {})
