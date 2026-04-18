from __future__ import annotations

from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    x: float = Field(default=0.0, ge=-1.5, le=1.5)
    y: float = Field(default=0.0, ge=-1.5, le=1.5)
    z: float = Field(default=0.0, ge=-1.5, le=1.5)
    st_gain: float = Field(default=0.25, ge=0.0, le=1.0)


class DamageSegment(BaseModel):
    id: int
    name: str
    score: float


class SimulationResponse(BaseModel):
    time_ms: list[float]
    baseline_vector_loop: list[list[float]]
    vector_loop: list[list[float]]
    input_vector: list[float]
    normalized_vector: list[float]
    injury_vector: list[float]
    ecg: dict[str, list[float]]
    lead_projection: dict[str, float]
    damage_segments: list[DamageSegment]


class LeadPosition(BaseModel):
    x: float
    y: float
    z: float


class LeadEditorResponse(BaseModel):
    lead_order: list[str]
    leads: dict[str, LeadPosition]
    source_file: str


class LeadEditorUpdateRequest(BaseModel):
    leads: dict[str, LeadPosition]
