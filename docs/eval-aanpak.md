# Eval-aanpak

Eval-driven development is hier geen bijzaak maar de kernpraktijk: de golden set
bestaat vóórdat er features zijn. Dit document is zelfstandig; de werkwijze is
beproefd in een eerder lokaal RAG-project en hier toegespitst op de AI Act.

## Werkwijze

Elke wijziging is een experiment:
**hypothese → één knop draaien → delta voorspellen → meten → verklaren.**
Nooit twee knoppen tegelijk; een onverklaarde verbetering is geen verbetering.

## Drie metrics (deterministisch, geen LLM-judge)

| Metric | Vraag | Voorbeeld-check |
| --- | --- | --- |
| **Retrieval** | Zit de juiste bron in de top-K? | verwacht artikel in opgehaalde chunks |
| **Grounding** | Staan de kernfeiten (correct) in het antwoord? | verplichte kernwoorden/datums aanwezig |
| **Abstentie** | Zegt hij eerlijk "weet ik niet" buiten de dekking? | weiger-markers bij een vraag buiten het corpus |

Deterministisch scoren (marker-matching) volstaat om te beginnen en is reproduceerbaar
en gratis. Een LLM-judge kan later, als de nuance het vraagt.

## Golden set — AiActWijzer-specifieke cases

De eerste oplever is ~10 cases; uitbreiden naarmate het corpus groeit. Categorieën:

1. **Actualiteit** — "Wanneer gelden de hoog-risico-verplichtingen (bijlage III)?"
   Goed: **2 dec 2027** (Digital Omnibus). Fout: 2 aug 2026 (de verouderde datum die
   het halve internet — en concurrenten — nog noemen). Dit is de onderscheidende case.
2. **Risicoclassificatie** — "LLM voor cv-screening in een uitzendcontext?" →
   hoog-risico, bijlage III, met de bijbehorende verplichtingen.
3. **Rolbepaling** — provider vs. deployer en de verschillen in verplichtingen.
4. **NL-doorwerking** — toezicht/UAIV-vragen die generieke (EU-brede) tools missen.
5. **Abstentie** — vragen buiten scope (concreet juridisch advies, niet-AI-Act-recht):
   eerlijk doorverwijzen, niet hallucineren. Voor een juridische tool is dit een
   kernfeature, geen randgeval.

## Meegenomen lessen

- **Evalueer je eval.** In het eerdere project had de eval zelf een false-negative
  (abstentie-markers dekten een geldige weigering niet). Een groene score kan een
  kapotte meting zijn — controleer steekproefsgewijs handmatig.
- **Temperatuur 0**, anders varieert grounding per run en meet je ruis.
- **Regressie is het doel.** De set draait bij elke wijziging (chunking, model, prompt);
  een knop die één metric verbetert mag geen andere stilletjes slopen.

## Governance-koppeling

De eval-suite is niet alleen dev-gereedschap maar ook **governance-bewijs**: aantoonbare,
herhaalbare kwaliteitscontrole hoort bij transparantie/auditbaarheid onder de AI Act.
De scorekaart is dus een deliverable, niet alleen een hulpmiddel.

## Later

Deze aanpak wordt na dit project gegeneraliseerd tot een klein open-source eval-tool
(golden-set-formaat + runner + regressierapport) — referentieproject 2; AiActWijzer
is daarvan de eerste gebruiker.
