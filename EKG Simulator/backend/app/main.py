from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .api.routes.simulation import router as simulation_router

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

app = FastAPI(
    title="EKG Simulator API",
    version="0.1.0",
    description=(
        "API para simular ECG vetorial, aplicar vetor de injúria no segmento ST "
        "e retornar projeções/dano segmentar para um app web."
    ),
)

app.include_router(simulation_router)
app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/app/")
