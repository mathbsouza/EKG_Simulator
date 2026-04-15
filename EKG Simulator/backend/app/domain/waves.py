from __future__ import annotations

import numpy as np

from .geometry import unit


def gaussian(time_axis: np.ndarray, mu: float, sigma: float, amp: float = 1.0) -> np.ndarray:
    return amp * np.exp(-0.5 * ((time_axis - mu) / sigma) ** 2)


def gate(time_axis: np.ndarray, start: float, end: float) -> np.ndarray:
    return ((time_axis >= start) & (time_axis <= end)).astype(float)


def wave_windowed(
    time_axis: np.ndarray,
    mu: float,
    sigma: float,
    amp: float,
    direction: np.ndarray | list[float],
    start: float,
    end: float,
) -> np.ndarray:
    return np.outer(
        gaussian(time_axis, mu, sigma, amp) * gate(time_axis, start, end),
        unit(direction),
    )


def p_wave(time_axis: np.ndarray) -> np.ndarray:
    return wave_windowed(time_axis, 0.16, 0.018, 0.10, [-0.4, 0.3, -0.85], 0.10, 0.22)


def pr_segment(time_axis: np.ndarray) -> np.ndarray:
    return np.zeros((len(time_axis), 3), dtype=float)


def qrs_complex(time_axis: np.ndarray) -> np.ndarray:
    gain = 0.75
    q_wave = wave_windowed(time_axis, 0.34, 0.010, 0.08 * gain, [0.9, 0.0, 0.1], 0.30, 0.38)
    r_wave = wave_windowed(time_axis, 0.38, 0.015, 1.00 * gain, [-0.7, 0.25, -0.65], 0.34, 0.43)
    s_wave = wave_windowed(time_axis, 0.42, 0.012, 0.15 * gain, [-0.3, -0.4, 0.7], 0.38, 0.46)
    return q_wave + r_wave + s_wave


def st_segment(
    time_axis: np.ndarray,
    elevation: float = 0.0,
    direction: np.ndarray | list[float] = (-0.2, 0.3, -0.9),
    start: float = 0.44,
    end: float = 0.56,
) -> np.ndarray:
    return np.outer(elevation * gate(time_axis, start, end), unit(direction))


def t_wave(time_axis: np.ndarray) -> np.ndarray:
    return wave_windowed(time_axis, 0.70, 0.060, 0.25, [-0.6, 0.2, -0.6], 0.58, 0.86)
