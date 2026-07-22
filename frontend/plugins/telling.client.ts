// Meldt een paginabezoek aan de backend: alleen het pad, verder niets.
// Client-only en bewust "fire and forget" — mislukt de melding, dan merkt de
// bezoeker daar niets van; statistiek mag de site nooit ophouden.
//
// Dat dit vanuit de browser gebeurt heeft een prettig neveneffect: crawlers die
// geen JavaScript uitvoeren tellen niet mee, dus de cijfers gaan over mensen.
import { $fetch } from 'ofetch'

export default defineNuxtPlugin(() => {
  const meld = (pad: string) => {
    $fetch('/api/bezoek', { method: 'POST', body: { pad } }).catch(() => {})
  }

  const router = useRouter()
  meld(router.currentRoute.value.path)
  router.afterEach((naar) => meld(naar.path))
})
