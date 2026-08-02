// Genereert per contentpagina een statische og-deelkaart (1200x630) in
// public/og/. Waarom statisch + bij de hand: het runtime-og-image-endpoint van
// @nuxtjs/seo gaat uit van h3 v2 en crasht op deze Nuxt 3.21 — dus renderen we
// de kaarten los met headless Chrome, in de merkstijl (papier + okerrand +
// Literata). Draai opnieuw als een titel/omschrijving wijzigt:
//   node scripts/gen-og-images.mjs
import { writeFile, mkdir, rm } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'

const execFileP = promisify(execFile)
const here = dirname(fileURLToPath(import.meta.url))
const root = join(here, '..')
const fontDir = join(root, 'node_modules', '@fontsource')
const outDir = join(root, 'public', 'og')
const tmpDir = join(root, '.og-tmp')

const font = (pkg, file) => 'file://' + join(fontDir, pkg, 'files', file)

// Titel + omschrijving spiegelen useSeoMeta op de pagina's zelf.
const paginas = [
  { slug: 'over', titel: 'Over de AI-verordening', desc: 'Waarom de wet bestaat, wie haar heeft vastgesteld en welke evaluatiemomenten er nog komen — met citaten uit de wettekst.' },
  { slug: 'nieuws', titel: 'Laatste ontwikkelingen', desc: 'Ontwikkelingen rond de AI-verordening, door de redactie geselecteerd en in gewone taal samengevat, met link naar de bron.' },
  { slug: 'transparantie', titel: 'Transparantie', desc: 'Welk model Grondslag gebruikt, waar het draait, welke bronnen erin zitten en wat er wel en niet wordt bijgehouden.' },
]

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

const html = ({ titel, desc }) => `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:'Literata';font-weight:400;src:url('${font('literata', 'literata-latin-400-normal.woff2')}')}
@font-face{font-family:'Literata';font-weight:600;src:url('${font('literata', 'literata-latin-600-normal.woff2')}')}
@font-face{font-family:'Public Sans';font-weight:400;src:url('${font('public-sans', 'public-sans-latin-400-normal.woff2')}')}
@font-face{font-family:'Public Sans';font-weight:600;src:url('${font('public-sans', 'public-sans-latin-600-normal.woff2')}')}
html,body{margin:0;padding:0}
.card{width:1200px;height:630px;background:#FAFAF7;position:relative;box-sizing:border-box;padding:88px 100px;font-family:'Public Sans',system-ui,sans-serif;overflow:hidden}
.rand{position:absolute;left:0;top:0;bottom:0;width:16px;background:#B98A2F}
.merk{display:flex;align-items:center;gap:16px;margin-bottom:54px}
.g{width:56px;height:56px;border-radius:8px;background:#fff;border:1px solid #E2E4E3;position:relative}
.g .bar{position:absolute;left:10px;top:10px;bottom:10px;width:4px;background:#B98A2F}
.g .letter{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;padding-left:8px;box-sizing:border-box;font-family:'Literata',serif;font-size:34px;color:#14213D}
.merknaam{font-family:'Literata',serif;font-size:32px;font-weight:600;color:#14213D}
.titel{font-family:'Literata',serif;font-weight:600;font-size:76px;line-height:1.08;color:#14213D;max-width:960px}
.desc{font-size:29px;line-height:1.5;color:#1F2937;max-width:940px;margin-top:32px}
.voet{position:absolute;left:100px;bottom:60px;font-size:22px;font-weight:600;letter-spacing:.4px;color:#8A6A1F}
</style></head><body>
<div class="card">
  <div class="rand"></div>
  <div class="merk"><div class="g"><div class="bar"></div><div class="letter">G</div></div><div class="merknaam">Grondslag</div></div>
  <div class="titel">${esc(titel)}</div>
  <div class="desc">${esc(desc)}</div>
  <div class="voet">grondslag.eu · AI-verordening (AI Act)</div>
</div>
</body></html>`

const chrome = process.env.CHROME_BIN || 'google-chrome'

await mkdir(outDir, { recursive: true })
await mkdir(tmpDir, { recursive: true })
for (const p of paginas) {
  const htmlPath = join(tmpDir, `${p.slug}.html`)
  const pngPath = join(outDir, `${p.slug}.png`)
  await writeFile(htmlPath, html(p), 'utf8')
  await execFileP(chrome, [
    '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars',
    '--force-device-scale-factor=1', '--window-size=1200,630',
    `--screenshot=${pngPath}`, `file://${htmlPath}`,
  ])
  console.log('og-image:', pngPath)
}
await rm(tmpDir, { recursive: true, force: true })
