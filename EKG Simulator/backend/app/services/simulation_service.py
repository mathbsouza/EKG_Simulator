from __future__ import annotations

from ..domain.simulator import SimulationResult, simulate_from_vector


def run_simulation(x: float, y: float, z: float, st_gain: float) -> SimulationResult:
    return simulate_from_vector(x=x, y=y, z=z, st_gain=st_gain)
