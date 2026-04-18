from __future__ import annotations

import re
from pathlib import Path


LEADS_FILE = Path(__file__).resolve().parents[1] / "domain" / "leads.py"
PRECORDIAL_BLOCK_PATTERN = re.compile(
    r"PRECORDIAL_LEADS: dict\[str, np\.ndarray\] = \{\n(?P<body>.*?)\n\}",
    re.DOTALL,
)
ENTRY_PATTERN = re.compile(
    r'^\s*"(?P<lead>[^"]+)":\s*chest_lead\((?P<x>[-\d.]+),\s*(?P<y>[-\d.]+),\s*(?P<z>[-\d.]+)\),?$'
)


def load_precordial_leads() -> tuple[list[str], dict[str, dict[str, float]]]:
    content = LEADS_FILE.read_text(encoding="utf-8")
    block_match = PRECORDIAL_BLOCK_PATTERN.search(content)
    if block_match is None:
        raise RuntimeError("Nao foi possivel localizar PRECORDIAL_LEADS em leads.py")

    lead_order: list[str] = []
    leads: dict[str, dict[str, float]] = {}
    for raw_line in block_match.group("body").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        entry_match = ENTRY_PATTERN.match(line)
        if entry_match is None:
            continue
        lead = entry_match.group("lead")
        lead_order.append(lead)
        leads[lead] = {
            "x": float(entry_match.group("x")),
            "y": float(entry_match.group("y")),
            "z": float(entry_match.group("z")),
        }

    if not leads:
        raise RuntimeError("Nenhuma derivacao precordial foi lida de leads.py")
    return lead_order, leads


def save_precordial_leads(leads: dict[str, dict[str, float]], lead_order: list[str] | None = None) -> tuple[list[str], dict[str, dict[str, float]]]:
    current_order, current_leads = load_precordial_leads()
    resolved_order = lead_order or current_order
    content = LEADS_FILE.read_text(encoding="utf-8")

    normalized_leads: dict[str, dict[str, float]] = {}
    lines = ["PRECORDIAL_LEADS: dict[str, np.ndarray] = {"]
    for lead in resolved_order:
        values = leads.get(lead, current_leads.get(lead))
        if values is None:
            raise ValueError(f"Derivacao ausente: {lead}")
        x = round(float(values["x"]), 2)
        y = round(float(values["y"]), 2)
        z = round(float(values["z"]), 2)
        normalized_leads[lead] = {"x": x, "y": y, "z": z}
        lines.append(f'    "{lead}": chest_lead({x:.2f}, {y:.2f}, {z:.2f}),')
    lines.append("}")

    replacement = "\n".join(lines)
    updated = PRECORDIAL_BLOCK_PATTERN.sub(replacement, content, count=1)
    LEADS_FILE.write_text(updated, encoding="utf-8")
    return resolved_order, normalized_leads
