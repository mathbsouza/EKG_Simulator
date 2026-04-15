from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter

from ...domain.leads import AHA_SEGMENTS, DISPLAY_LEADS, LEAD_VECTORS
from ...schemas.simulation import SimulationRequest, SimulationResponse
from ...services.simulation_service import run_simulation

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/meta")
def metadata() -> dict[str, object]:
    return {
        "display_leads": DISPLAY_LEADS,
        "lead_vectors": {
            name: [round(float(value), 6) for value in vector.tolist()]
            for name, vector in LEAD_VECTORS.items()
        },
        "aha_segments": AHA_SEGMENTS,
    }


@router.post("", response_model=SimulationResponse)
def simulate(payload: SimulationRequest) -> SimulationResponse:
    result = run_simulation(
        x=payload.x,
        y=payload.y,
        z=payload.z,
        st_gain=payload.st_gain,
    )
    return SimulationResponse(**asdict(result))
