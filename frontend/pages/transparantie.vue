<template>
  <article class="transparantie">
    <h1>Transparantie</h1>

    <section>
      <h2>Je praat met AI</h2>
      <p>
        AiActWijzer is een AI-systeem (artikel 50 van de AI-verordening vraagt
        dat we dat duidelijk zeggen). Antwoorden worden gegenereerd door een
        taalmodel en zijn uitsluitend gebaseerd op de bronnen hieronder — met
        bij elke claim een letterlijk citaat, zodat je het antwoord zelf kunt
        controleren.
      </p>
    </section>

    <section>
      <h2>Model en hosting</h2>
      <p>
        Generatie en embeddings draaien via de API van Mistral AI (EU-gehost).
        De zoekindex en de wettekst staan in onze eigen database; er gaat geen
        data naar niet-Europese clouddiensten.
      </p>
    </section>

    <section>
      <h2>Bronnen en actualiteit</h2>
      <p>
        Het corpus bestaat uit de Nederlandse taalversie van Verordening (EU)
        2024/1689 (de AI-verordening), de tijdlijnwijzigingen uit de Digital
        Omnibus on AI (juli 2026) en geselecteerde Nederlandse bronnen over
        toezicht (UAIV). Elke bron is met versie en datum geadministreerd; elk
        antwoord draagt een stempel met de stand van de wetgeving. Wijzigt de
        wet, dan wordt het corpus bijgewerkt en de kwaliteitscontrole opnieuw
        gedraaid.
      </p>
    </section>

    <section>
      <h2>Onze eigen risicoclassificatie</h2>
      <p>
        AiActWijzer valt zelf onder de AI-verordening. Het is geen
        hoog-risico-toepassing uit bijlage III; er geldt wel de
        transparantieplicht van artikel 50 — deze pagina is daar de invulling
        van. De kwaliteitscontrole (een herhaalbare testset met
        controleerbare uitkomsten) is onderdeel van de broncode.
      </p>
    </section>

    <section>
      <h2>Informatie, geen advies</h2>
      <p>
        Antwoorden zijn een startpunt voor je eigen jurist, geen vervanging.
        Bij vragen over jouw specifieke situatie verwijst AiActWijzer bewust
        door in plaats van te gokken.
      </p>
    </section>

    <section>
      <h2>Privacy</h2>
      <p>
        Er zijn geen accounts. Vragen worden niet opgeslagen en niet gebruikt
        als trainings- of testdata.
      </p>
    </section>
  </article>
</template>

<style scoped>
.transparantie { max-width: 68ch; }
.transparantie h1 { font-size: 26px; margin: 0 0 20px; }
.transparantie h2 { font-size: 17px; margin: 24px 0 6px; }
.transparantie p { margin: 0; }
</style>
