"""Centrale configuratie. Alle knoppen (model, TOP_K) staan hier zodat een
experiment één plek heeft om te draaien — zie docs/eval-aanpak.md."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mistral_api_key: str = ""
    database_url: str = "postgresql+psycopg://aiact:aiact@localhost:5433/aiact"
    embed_model: str = "mistral-embed"
    chat_model: str = "mistral-small-latest"
    embed_dim: int = 1024          # dimensie van mistral-embed
    top_k: int = 5                 # startwaarde; verhogen is een gemeten knop, geen reflex
    random_seed: int = 42          # vaste seed voor generatie: dempt API-run-ruis in de evals
    broncheck_interval_uren: int = 24   # dagelijkse bronnencheck (zie app/bronnen.py)
    nieuws_interval_uren: int = 24      # dagelijkse nieuwsaanvoer (zie app/nieuws.py)
    # Geheim token voor het nieuws-beheerscherm; alleen in .env op de server.
    # Leeg = beheer-endpoints staan uit (403) — veilige standaard.
    admin_token: str = ""
    stand_van_wetgeving: str = "juli 2026"
    # Cosine-afstandsgrens voor de geen-bron-splitsing: abstentie mét een
    # vectorkandidaat op afstand <= grens telt als "sterk signaal". Gemeten
    # (evals/meet_afstanden.py, 24 jul 2026): on-topic-vragen — ook de terechte
    # abstenties — zitten ≤ 0.163, buiten-scope-vragen ≥ 0.191; 0.175 ligt
    # midden in die kloof. De afstand scheidt dus ónderwerp, niet juistheid:
    # sterk signaal = "vraag lag binnen het onderwerp, uitzoeken waard".
    signaal_grens: float = 0.175

    model_config = {"env_file": ".env"}


settings = Settings()
