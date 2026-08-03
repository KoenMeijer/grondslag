// Sector-hubs: intro-content uit content/sectoren/*.md, zelfde build-time glob
// als de vragen. De vragenlijst per sector komt uit utils/vragen (vragenPerSector).
import { load as parseFrontmatter } from 'js-yaml'
import { marked } from 'marked'

export interface Sector {
  slug: string
  naam: string
  titel: string
  beschrijving: string
  introHtml: string
}

const bestanden = import.meta.glob('../content/sectoren/*.md', {
  query: '?raw', import: 'default', eager: true,
}) as Record<string, string>

function parse(pad: string, ruw: string): Sector {
  const slug = pad.split('/').pop()!.replace(/\.md$/, '')
  const m = ruw.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/)
  const fm = (m ? parseFrontmatter(m[1]) : {}) as Record<string, unknown>
  const body = (m ? m[2] : ruw).trim()
  return {
    slug,
    naam: String(fm.naam ?? slug),
    titel: String(fm.titel ?? fm.naam ?? slug),
    beschrijving: String(fm.beschrijving ?? ''),
    introHtml: marked.parse(body) as string,
  }
}

const _sectoren = Object.entries(bestanden).map(([p, r]) => parse(p, r))
  .sort((a, b) => a.naam.localeCompare(b.naam, 'nl'))

export function alleSectoren(): Sector[] { return _sectoren }
export function vindSector(slug: string): Sector | undefined {
  return _sectoren.find(s => s.slug === slug)
}
