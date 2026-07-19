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
    stand_van_wetgeving: str = "juli 2026"

    model_config = {"env_file": ".env"}


settings = Settings()
