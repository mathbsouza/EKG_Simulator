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
    "V1": chest_lead(0.61, 0.59, 0.43),
    "V2": chest_lead(0.37, 0.61, 0.43),
    "V3": chest_lead(0.13, 0.58, 0.11),
    "V4": chest_lead(-0.11, 0.51, -0.32),
    "V5": chest_lead(-0.32, 0.34, -0.32),
    "V6": chest_lead(-0.48, 0.11, -0.32),
    "V3R": chest_lead(0.91, 0.51, 0.12),
    "V4R": chest_lead(1.13, 0.46, -0.30),
    "V7": chest_lead(-0.54, -0.10, -0.32),
    "V8": chest_lead(-0.60, -0.34, -0.32),
    "V9": chest_lead(-0.68, -0.64, -0.32),
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
