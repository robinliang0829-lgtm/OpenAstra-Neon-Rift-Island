"""Standby palette and badge ids. Color does not identify a team."""

from __future__ import annotations

import re
import xml.etree.ElementTree as etree

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
        light = (
            f'<rect x="4" y="28" width="6" height="8" fill="{color}" stroke="none" '
            'data-light-slot="shoulder_left"/>'
        )
    else:
        geometry = f'<circle cx="32" cy="32" r="16" fill="none" stroke="{color}" stroke-width="6"/>'
        light = (
            f'<rect x="54" y="28" width="6" height="8" fill="{color}" stroke="none" '
            'data-light-slot="shoulder_right"/>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{_VIEWBOX}" '
        f'data-badge-id="{badge["id"]}" data-shape="{badge["shape"]}" '
        f'data-light-slot="{badge["light_slot"]}" data-color-role="auxiliary" '
        f'data-aux-color="{badge["aux"]}">'
        f"<title>{badge['id']}</title>{geometry}{light}</svg>\n"
    )


_SVG = "{http://www.w3.org/2000/svg}"
_COLOR_ATTRS = {"stroke", "fill", "stroke-width", "stroke-linecap", "data-aux-color", "data-color-role"}
# Channel mixes drop hue for the readability check. They are not a clinical simulator.
_COLORBLIND = {
    "protanopia": ((0.57, 0.43, 0.0), (0.56, 0.44, 0.0), (0.0, 0.24, 0.76)),
    "deuteranopia": ((0.63, 0.38, 0.0), (0.70, 0.30, 0.0), (0.0, 0.30, 0.70)),
    "tritanopia": ((0.95, 0.05, 0.0), (0.0, 0.43, 0.57), (0.0, 0.48, 0.52)),
}


def _map_hex(svg: str, fn) -> str:
    def repl(match: re.Match[str]) -> str:
        value = match.group(0)
        red = int(value[1:3], 16)
        green = int(value[3:5], 16)
        blue = int(value[5:7], 16)
        channels = [max(0, min(255, int(round(channel)))) for channel in fn(red, green, blue)]
        return f"#{channels[0]:02X}{channels[1]:02X}{channels[2]:02X}"

    return re.sub(r"#[0-9A-Fa-f]{6}", repl, svg)


def greyscale_badge(svg: str) -> str:
    def fn(red: int, green: int, blue: int) -> tuple[float, float, float]:
        luma = 0.2126 * red + 0.7152 * green + 0.0722 * blue
        return luma, luma, luma

    return _map_hex(svg, fn)


def colorblind_badge(svg: str, mode: str) -> str:
    rows = _COLORBLIND[mode]

    def fn(red: int, green: int, blue: int) -> tuple[float, float, float]:
        mixed = tuple(coef_r * red + coef_g * green + coef_b * blue for coef_r, coef_g, coef_b in rows)
        return mixed[0], mixed[1], mixed[2]

    return _map_hex(svg, fn)


def geometry_signature(svg: str) -> str:
    """Markup with color attributes removed. Team identity has to survive this."""
    root = etree.fromstring(svg)
    for title in list(root.findall(f"{_SVG}title")):
        root.remove(title)
    for element in root.iter():
        for attr in list(element.attrib):
            if attr in _COLOR_ATTRS:
                del element.attrib[attr]
    return etree.tostring(root, encoding="unicode")


def badge_identity(svg: str) -> tuple[str, str]:
    """Read shape and shoulder slot from geometry. Stroke and fill are ignored."""
    root = etree.fromstring(svg)
    polys = root.findall(f"{_SVG}polyline")
    circles = root.findall(f"{_SVG}circle")
    rects = root.findall(f"{_SVG}rect")
    if len(polys) == 1 and not circles:
        shape = "open_chevron"
    elif len(circles) == 1 and not polys:
        shape = "closed_ring"
    else:
        shape = "ambiguous"
    if len(rects) != 1:
        slot = "ambiguous"
    else:
        x = float(rects[0].attrib["x"])
        if x < 32:
            slot = "shoulder_left"
        elif x > 32:
            slot = "shoulder_right"
        else:
            slot = "ambiguous"
    return shape, slot
