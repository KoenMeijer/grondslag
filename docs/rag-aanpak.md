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

## Soevereine stack

Embeddings + generatie draaien lokaal (Ollama) en/of bij Mistral (EU). Geen
Amerikaanse cloud — de gebruiker moet AI Act-vragen over eigen systemen kunnen stellen
zonder dat de vraag zelf een compliance-risico wordt. Modelkeuze is zelf een
governance-keuze: herkomst en hosting van het model horen in de transparantie-pagina.
