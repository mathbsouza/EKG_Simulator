from __future__ import annotations

import numpy as np

from .geometry import chest_lead, frontal_lead


LIMB_LEADS: dict[str, np.ndarray] = {
    "I": frontal_lead(0),
    "II": frontal_lead(-60),
    "III": frontal_lead(-120),
    "aVF": frontal_lead(-90),
    "aVL": frontal_lead(30),
    "aVR": frontal_lead(150),
}

PRECORDIAL_LEADS: dict[str, np.ndarray] = {
    "V1": chest_lead(0.55, 0.85, 0.05),
    "V2": chest_lead(0.35, 0.90, 0.05),
    "V3": chest_lead(0.10, 0.95, 0.00),
    "V4": chest_lead(-0.20, 0.95, -0.05),
    "V5": chest_lead(-0.45, 0.85, -0.05),
    "V6": chest_lead(-0.65, 0.75, 0.00),
    "V3R": chest_lead(0.60, 0.60, 0.00),
    "V4R": chest_lead(0.70, 0.50, -0.05),
    "V7": chest_lead(-0.75, -0.20, 0.00),
    "V8": chest_lead(-0.70, -0.45, 0.00),
    "V9": chest_lead(-0.60, -0.65, 0.00),
}

LEAD_VECTORS: dict[str, np.ndarray] = {**LIMB_LEADS, **PRECORDIAL_LEADS}

DISPLAY_LEADS: list[str] = [
    "I",
    "II",
    "III",
    "aVR",
    "aVL",
    "aVF",
    "V1",
    "V2",
    "V3",
    "V4",
    "V5",
    "V6",
]

CONTIGUOUS_GROUPS: list[list[str]] = [
    ["II", "III", "aVF"],
    ["I", "aVL"],
    ["V5", "V6"],
    ["V1", "V2"],
    ["V2", "V3", "V4"],
    ["V3R", "V4R"],
    ["V7", "V8", "V9"],
]

AHA_SEGMENTS: list[dict[str, object]] = [
    {"id": 1, "name": "Basal anterior", "azimuth": 60.0, "elevation": 55.0},
    {"id": 2, "name": "Basal anteroseptal", "azimuth": 20.0, "elevation": 55.0},
    {"id": 3, "name": "Basal inferoseptal", "azimuth": -20.0, "elevation": 55.0},
    {"id": 4, "name": "Basal inferior", "azimuth": -90.0, "elevation": 55.0},
    {"id": 5, "name": "Basal inferolateral", "azimuth": -160.0, "elevation": 55.0},
    {"id": 6, "name": "Basal anterolateral", "azimuth": 140.0, "elevation": 55.0},
    {"id": 7, "name": "Mid anterior", "azimuth": 60.0, "elevation": 15.0},
    {"id": 8, "name": "Mid anteroseptal", "azimuth": 20.0, "elevation": 15.0},
    {"id": 9, "name": "Mid inferoseptal", "azimuth": -20.0, "elevation": 15.0},
    {"id": 10, "name": "Mid inferior", "azimuth": -90.0, "elevation": 15.0},
    {"id": 11, "name": "Mid inferolateral", "azimuth": -160.0, "elevation": 15.0},
    {"id": 12, "name": "Mid anterolateral", "azimuth": 140.0, "elevation": 15.0},
    {"id": 13, "name": "Apical anterior", "azimuth": 45.0, "elevation": -35.0},
    {"id": 14, "name": "Apical septal", "azimuth": 0.0, "elevation": -35.0},
    {"id": 15, "name": "Apical inferior", "azimuth": -90.0, "elevation": -35.0},
    {"id": 16, "name": "Apical lateral", "azimuth": 160.0, "elevation": -35.0},
    {"id": 17, "name": "Apex", "azimuth": 0.0, "elevation": -90.0},
]
