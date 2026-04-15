from __future__ import annotations

import numpy as np


def unit(vector: np.ndarray | list[float] | tuple[float, ...]) -> np.ndarray:
    values = np.asarray(vector, dtype=float)
    norm = np.linalg.norm(values)
    if norm <= 1e-12:
        return np.zeros_like(values, dtype=float)
    return values / norm


def frontal_lead(angle_deg: float) -> np.ndarray:
    angle_rad = np.deg2rad(angle_deg)
    return np.array([-np.cos(angle_rad), 0.0, np.sin(angle_rad)], dtype=float)


def chest_lead(x: float, y: float, z: float) -> np.ndarray:
    return unit(np.array([x, y, z], dtype=float))


def spherical_to_cartesian(azimuth_deg: float, elevation_deg: float, magnitude: float) -> np.ndarray:
    azimuth_rad = np.deg2rad(azimuth_deg)
    elevation_rad = np.deg2rad(elevation_deg)
    x = magnitude * np.cos(elevation_rad) * np.cos(azimuth_rad)
    y = magnitude * np.cos(elevation_rad) * np.sin(azimuth_rad)
    z = magnitude * np.sin(elevation_rad)
    return np.array([x, y, z], dtype=float)
