from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .geometry import spherical_to_cartesian, unit
from .leads import AHA_SEGMENTS, DISPLAY_LEADS, LEAD_VECTORS
from .waves import p_wave, pr_segment, qrs_complex, st_segment, t_wave


DEFAULT_SAMPLING_FREQUENCY = 1000


@dataclass(slots=True)
class SimulationResult:
    time_ms: list[float]
    vector_loop: list[list[float]]
    baseline_vector_loop: list[list[float]]
    input_vector: list[float]
    normalized_vector: list[float]
    injury_vector: list[float]
    ecg: dict[str, list[float]]
    lead_projection: dict[str, float]
    damage_segments: list[dict[str, float | int | str]]


def build_time_axis(fs: int = DEFAULT_SAMPLING_FREQUENCY, duration_s: float = 1.0) -> np.ndarray:
    return np.linspace(0.0, duration_s, int(fs * duration_s), endpoint=False)


def build_baseline_vector(time_axis: np.ndarray) -> np.ndarray:
    vector = np.zeros((len(time_axis), 3), dtype=float)
    vector += p_wave(time_axis)
    vector += pr_segment(time_axis)
    vector += qrs_complex(time_axis)
    vector += st_segment(time_axis)
    vector += t_wave(time_axis)
    return vector


def apply_injury_to_baseline(
    baseline_xyz: np.ndarray,
    time_axis: np.ndarray,
    injury_vector: np.ndarray,
    st_gain: float = 0.25,
    st_start: float = 0.44,
    st_end: float = 0.60,
) -> np.ndarray:
    injury_direction = unit(injury_vector)
    if np.linalg.norm(injury_direction) <= 1e-12:
        return baseline_xyz.copy()

    injury_component = st_segment(
        time_axis=time_axis,
        elevation=st_gain,
        direction=injury_direction,
        start=st_start,
        end=st_end,
    )
    return baseline_xyz + injury_component


def project_ecg(vector_loop: np.ndarray) -> dict[str, np.ndarray]:
    projected = {name: vector_loop @ lead for name, lead in LEAD_VECTORS.items()}
    max_amplitude = max(float(np.max(np.abs(values))) for values in projected.values())
    scale = 1.0 if max_amplitude <= 1e-12 else 1.0 / max_amplitude
    return {name: values * scale for name, values in projected.items()}


def project_static_vector(vector: np.ndarray) -> dict[str, float]:
    return {lead: float(np.dot(vector, axis)) for lead, axis in LEAD_VECTORS.items()}


def compute_damage_segments(injury_vector: np.ndarray) -> list[dict[str, float | int | str]]:
    direction = unit(injury_vector)
    if np.linalg.norm(direction) <= 1e-12:
        return [
            {"id": int(segment["id"]), "name": str(segment["name"]), "score": 0.0}
            for segment in AHA_SEGMENTS
        ]

    output: list[dict[str, float | int | str]] = []
    for segment in AHA_SEGMENTS:
        segment_vector = spherical_to_cartesian(
            azimuth_deg=float(segment["azimuth"]),
            elevation_deg=float(segment["elevation"]),
            magnitude=1.0,
        )
        score = max(0.0, float(np.dot(direction, unit(segment_vector))))
        output.append(
            {
                "id": int(segment["id"]),
                "name": str(segment["name"]),
                "score": round(score, 4),
            }
        )
    return output


def simulate_from_vector(
    x: float,
    y: float,
    z: float,
    st_gain: float = 0.25,
    fs: int = DEFAULT_SAMPLING_FREQUENCY,
    duration_s: float = 1.0,
) -> SimulationResult:
    time_axis = build_time_axis(fs=fs, duration_s=duration_s)
    baseline = build_baseline_vector(time_axis)
    injury_vector = np.array([x, y, z], dtype=float)
    result_vector = apply_injury_to_baseline(baseline, time_axis, injury_vector, st_gain=st_gain)
    ecg = project_ecg(result_vector)

    return SimulationResult(
        time_ms=np.round(time_axis * 1000.0, 3).tolist(),
        baseline_vector_loop=np.round(baseline, 6).tolist(),
        vector_loop=np.round(result_vector, 6).tolist(),
        input_vector=np.round(injury_vector, 6).tolist(),
        normalized_vector=np.round(unit(injury_vector), 6).tolist(),
        injury_vector=np.round(unit(injury_vector) * st_gain, 6).tolist(),
        ecg={lead: np.round(ecg[lead], 6).tolist() for lead in DISPLAY_LEADS},
        lead_projection={lead: round(value, 4) for lead, value in project_static_vector(injury_vector).items()},
        damage_segments=compute_damage_segments(injury_vector),
    )
