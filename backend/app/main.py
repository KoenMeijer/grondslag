"""FastAPI-laag: dun schilletje om de RAG-service. Geen fallback-antwoorden bij
een modelfout — liever een eerlijke 502 dan een half juridisch antwoord."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.db import SessionLocal
from app.rag import service
from app.rag.mistral import MistralFout

app = FastAPI(title="AiActWijzer")


class AskVraag(BaseModel):
    vraag: str


class CitaatUit(BaseModel):
    ref: str
    fragment: str
    bron: str
    url: str


class AskAntwoord(BaseModel):
    antwoord: str
    citaten: list[CitaatUit]
    stand_van_wetgeving: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=AskAntwoord)
def ask(body: AskVraag):
    with SessionLocal() as sessie:
        try:
            return service.beantwoord(sessie, body.vraag)
        except MistralFout as e:
            raise HTTPException(status_code=502, detail=f"Modelaanroep mislukt: {e}")
