# RAG-aanpak

Hoe AiActWijzer antwoorden grondt in de EU AI Act. Dit document is zelfstandig:
de lessen komen uit een eerder lokaal RAG-project (notitie-corpus, Ollama) en zijn
hier vertaald naar de wettekst-context.

## Pijplijn

1. **Indexeren** — corpus (verordening 2024/1689 + omnibus-wijzigingen + NL-guidance)
   chunken, elk chunk embedden, opslaan met metadata (bron, artikel/lid/overweging).
2. **Vragen** — vraag embedden, chunks scoren op gelijkenis, top-K als context aan het
   model geven met de instructie: antwoord alléén op basis van deze context, mét
   bronvermelding per claim.
3. **Citeren** — elk antwoord verwijst naar artikelnummer + letterlijk fragment.
   Het artikelnummer is het citatie-anker (dit voedt het citaat-paneel, zie
   design-principes in `../CLAUDE.md`).

## Chunking: benut de structuur van de wettekst

Een verordening is géén vlakke tekst — artikel, lid, punt en overweging zijn natuurlijke,
betekenisvolle grenzen. Chunk dáárop (niet op tekenaantal) en neem de hiërarchie op als
metadata én als context in het chunk zelf ("Art. 6, lid 2: …"). Bijlagen (zoals bijlage III,
de hoog-risico-lijst) verdienen eigen behandeling: per punt, niet als één blok.

## Meegenomen lessen (eval-gedreven vastgesteld, zie `eval-aanpak.md`)

- **Meer context ≠ beter.** TOP_K verhogen van 5 naar 8 maakte grounding aantoonbaar
  *slechter* (lost-in-the-middle). Draai niet blind aan de context-knop; meet.
- **Temperatuur 0** voor feitelijke antwoorden — en voor reproduceerbare evals.
  Bij juridische vragen is variatie per run onacceptabel.
- **De bottleneck verschuift.** Na de eerste iteraties zat de fout niet in het model maar
  in retrieval-granulariteit: juiste document, verkeerde chunk. De volgende knop is dan
  fijnere chunking of hybride zoeken (keyword + embedding), niet een groter model.
  Voor wetteksten is hybride extra kansrijk: gebruikers noemen vaak letterlijke termen
  ("artikel 6", "GPAI", "deployer") die exact matchen.
- **Kop als context.** Een chunk zonder zijn kop/artikelaanduiding is ambigu voor
  zowel retrieval als generatie.
- **Meer kandidaten ≠ beter** (gemeten 21 jul 2026, `evals/meet_bronquotum.py`).
  De kandidatendiepte per zoekpad verhogen van 20 naar 50/100 verslechterde
  retrieval van 6/12 naar 4/12: RRF verwatert. Chunks die in beide paden
  middelmatig scoren stapelen twee bijdragen en verdringen een chunk die in één
  pad hoog staat — de doelchunk van `risico-cv-screening` zakte van rang 4 naar
  8 naar 10. Zelfde les als TOP_K: de knop die "meer informatie" belooft, kost
  precisie. Meten, niet aannemen.
- **Bronquotum lost geen semantische afstand op** (zelfde meting). Plaatsen in de
  top-K reserveren voor de ondervertegenwoordigde bron (77 NL-chunks tegen 900
  EU-chunks) leverde één case op van de vier: bij de andere drie stond de
  doelchunk op rang 56, 92 en 95 — die haal je met geen enkel quotum binnen.
  Oorzaak is vocabulaire, niet volume: de vraag zegt "boete", "uittesten",
  "aanspreekpunt"; de wet zegt "bestuurlijke boete ten hoogste het bedrag,
  genoemd in artikel 99, vierde lid", "AI-testomgeving voor regelgeving",
  "centraal contactpunt, bedoeld in artikel 70, tweede lid". Dát is de knop:
  query-expansie naar wetsvocabulaire (of een reranker), niet meer kandidaten.
- **Query-herschrijving gemeten en afgevoerd** (24 jul 2026,
  `evals/meet_herschrijven.py`). De vraag vóór het zoeken naar wetsvocabulaire
  laten herschrijven (generiek, met corpus-terminologielijst, vervangen /
  samenvoegen / extra RRF-pad / alleen-trefwoordpad) wint niet stabiel:
  beste variant 7-7-6 over drie runs tegen baseline 6/12, met per run ándere
  case-flips — dat is API-ruis, geen effect (zie de reproduceerbaarheids-les in
  `eval-aanpak.md`). Doorslaggevend: de hardnekkige NL-cases falen ook wanneer
  de herschrijving de juiste wetsterm létterlijk bevat. Het probleem zit dus
  niet meer aan de vraagkant maar in de rangschikking: de NL-doelchunks
  verliezen het óók met de goede termen van EU-chunks over hetzelfde begrip.
  Alle query-kant-knoppen zijn nu gemeten (kandidaten, quotum, herschrijving);
  de aangewezen volgende knop is een **reranker** over een diepe
  kandidatenlijst (top-50/100), of vraaggerichte verrijking van de
  NL-guidance-chunks zelf — met de memorisatie-waarschuwing uit
  `eval-aanpak.md` in acht genomen.

## Soevereine stack

Embeddings + generatie draaien lokaal (Ollama) en/of bij Mistral (EU). Geen
Amerikaanse cloud — de gebruiker moet AI Act-vragen over eigen systemen kunnen stellen
zonder dat de vraag zelf een compliance-risico wordt. Modelkeuze is zelf een
governance-keuze: herkomst en hosting van het model horen in de transparantie-pagina.
