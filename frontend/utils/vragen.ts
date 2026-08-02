// Kennisbank: adresseerbare vraag-antwoord-pagina's, gevoed uit markdown-
// bronbestanden (content/vragen/*.md). Waarom los adresseerbaar: zo kan iemand
// naar één antwoord linken/citeren in plaats van naar de dynamische vraagtool.
// Build-time ingelezen via import.meta.glob — geen zware content-module nodig.
import { load as parseFrontmatter } from 'js-yaml'
import { marked } from 'marked'

export interface Vraag {
  slug: string
  vraag: string
  artikel: string
  standWetgeving: string
  bijgewerkt: string
  antwoordHtml: string
  antwoordTekst: string
}

const bestanden = import.meta.glob('../content/vragen/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>

function parse(pad: string, ruw: string): Vraag {
  const slug = pad.split('/').pop()!.replace(/\.md$/, '')
  // Frontmatter (tussen de --- regels) en body scheiden.
  const m = ruw.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/)
  const fm = (m ? parseFrontmatter(m[1]) : {}) as Record<string, unknown>
  const body = (m ? m[2] : ruw).trim()
  return {
    slug,
    vraag: String(fm.vraag ?? slug),
    artikel: String(fm.artikel ?? ''),
    standWetgeving: String(fm['stand-wetgeving'] ?? ''),
    bijgewerkt: String(fm.bijgewerkt ?? ''),
    antwoordHtml: marked.parse(body) as string,
    antwoordTekst: body,
  }
}

export const alleVragen: Vraag[] = Object.entries(bestanden)
  .map(([pad, ruw]) => parse(pad, ruw))
  .sort((a, b) => a.vraag.localeCompare(b.vraag, 'nl'))

export function vindVraag(slug: string): Vraag | undefined {
  return alleVragen.find(v => v.slug === slug)
}
