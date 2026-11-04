"""Standby palette and badge ids. Color does not identify a team."""

from __future__ import annotations

PALETTE = {
    "wet_concrete": {"id": "mat.wet_concrete", "hex": "#3E4644", "role": "environment"},
    "worn_yellow": {"id": "mat.worn_yellow", "hex": "#C4A15A", "role": "environment"},
    "sign_cyan": {"id": "env.sign_cyan", "hex": "#2EC8C3", "role": "environment"},
    "sign_magenta": {"id": "env.sign_magenta", "hex": "#D24B7A", "role": "environment"},
    "sea_wall": {"id": "env.sea_wall", "hex": "#6E7570", "role": "environment"},
    "tide_cyan": {"id": "aux.tide_cyan", "hex": "#3DDFD4", "role": "auxiliary"},
    "hazard_amber": {"id": "aux.hazard_amber", "hex": "#E2A23A", "role": "auxiliary"},
}

BADGES = {
    "A": {
        "id": "badge.A.open_chevron",
        "shape": "open_chevron",
        "light_id": "light.A.shoulder_left",
        "light_slot": "shoulder_left",
        "aux": "tide_cyan",
        "file": "docs/art/badges/badge_A_open_chevron.svg",
    },
    "B": {
        "id": "badge.B.closed_ring",
        "shape": "closed_ring",
        "light_id": "light.B.shoulder_right",
        "light_slot": "shoulder_right",
        "aux": "hazard_amber",
        "file": "docs/art/badges/badge_B_closed_ring.svg",
    },
}

_VIEWBOX = "0 0 64 64"


def badge_svg(faction: str) -> str:
    badge = BADGES[faction]
    color = PALETTE[badge["aux"]]["hex"]
    if badge["shape"] == "open_chevron":
        geometry = (
            f'<polyline points="16,44 32,20 48,44" fill="none" stroke="{color}" '
            'stroke-width="6" stroke-linecap="square"/>'
        )
    else:
        geometry = f'<circle cx="32" cy="32" r="16" fill="none" stroke="{color}" stroke-width="6"/>'
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{_VIEWBOX}" '
        f'data-badge-id="{badge["id"]}" data-shape="{badge["shape"]}" '
        f'data-light-slot="{badge["light_slot"]}" data-color-role="auxiliary" '
        f'data-aux-color="{badge["aux"]}">'
        f"<title>{badge['id']}</title>{geometry}</svg>\n"
    )
