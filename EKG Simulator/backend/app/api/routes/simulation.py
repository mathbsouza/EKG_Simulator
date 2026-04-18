from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter

from ...domain.leads import AHA_SEGMENTS, DISPLAY_LEADS, LEAD_VECTORS
from ...schemas.simulation import LeadEditorResponse, LeadEditorUpdateRequest, SimulationRequest, SimulationResponse
from ...services.lead_editor_service import LEADS_FILE, load_precordial_leads, save_precordial_leads
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


@router.get("/lead-editor", response_model=LeadEditorResponse)
def get_lead_editor_state() -> LeadEditorResponse:
    lead_order, leads = load_precordial_leads()
    return LeadEditorResponse(
        lead_order=lead_order,
        leads=leads,
        source_file=str(LEADS_FILE),
    )


@router.put("/lead-editor", response_model=LeadEditorResponse)
def update_lead_editor_state(payload: LeadEditorUpdateRequest) -> LeadEditorResponse:
    lead_order, leads = save_precordial_leads(
        leads={
            lead: {"x": values.x, "y": values.y, "z": values.z}
            for lead, values in payload.leads.items()
        }
    )
    return LeadEditorResponse(
        lead_order=lead_order,
        leads=leads,
        source_file=str(LEADS_FILE),
    )


@router.post("", response_model=SimulationResponse)
def simulate(payload: SimulationRequest) -> SimulationResponse:
    result = run_simulation(
        x=payload.x,
        y=payload.y,
        z=payload.z,
        st_gain=payload.st_gain,
    )
    return SimulationResponse(**asdict(result))
