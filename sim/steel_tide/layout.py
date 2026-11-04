"""NR-01 greybox coordinates exported from the Steel Tide config."""

from __future__ import annotations

import json
from pathlib import Path

from .config import CONFIG_PATH, SteelTideConfig, load_config
from .routes import path_length_m, shortest_path

LAYOUT_PATH = CONFIG_PATH.parents[1] / "Content" / "Greybox" / "NR01_SteelTide.layout.json"

ACTORS = {
    "NR_Spawn_A": ("spawn_a", 0, "A spawn, face +X"),
    "NR_Terminal_A": ("terminal_a", 0, "B scores here"),
    "NR_BridgeHead_A": ("bridgehead_a", 0, "Safe deck when the span drops"),
    "NR_CoreSpawn": ("center", 0, "Single phase-core spawn"),
    "NR_BridgeHead_B": ("bridgehead_b", 180, "Safe deck when the span drops"),
    "NR_Terminal_B": ("terminal_b", 180, "A scores here"),
    "NR_Spawn_B": ("spawn_b", 180, "B spawn, face -X"),
    "NR_Alley_A": ("alley_a", 0, "Repair-alley node"),
    "NR_Alley_Mid": ("alley_mid", 0, "Repair-alley node"),
    "NR_Alley_B": ("alley_b", 180, "Repair-alley node"),
}

DECKS = (
    ("NR_Deck_A", "spawn_a", "bridgehead_a", 0.0),
    ("NR_BridgeSpan", "bridgehead_a", "bridgehead_b", 0.0),
    ("NR_Deck_B", "bridgehead_b", "spawn_b", 0.0),
    ("NR_AlleyDeck", "alley_a", "alley_b", 18.0),
)


def _point(config: SteelTideConfig, anchor: str, yaw: float = 0.0) -> dict:
    x_m, y_m = config.anchors[anchor]
    uu = config.ue_units_per_meter
    return {
        "anchor": anchor,
        "x_m": x_m,
        "y_m": y_m,
        "x_uu": int(round(x_m * uu)),
        "y_uu": int(round(y_m * uu)),
        "z_uu": 0,
        "yaw": yaw,
    }


def _polyline(config: SteelTideConfig, start: str, goal: str, route: str, bridge_state: str) -> dict:
    path = shortest_path(config, start, goal, route, bridge_state)
    if path is None:
        raise RuntimeError(f"no {route} path {start} -> {goal} while bridge is {bridge_state}")
    anchors = [start, *path]
    length_m = path_length_m(config, start, goal, route, bridge_state)
    return {
        "route": route,
        "bridge_state": bridge_state,
        "length_m": length_m,
        "walk_seconds_at_walk_speed": length_m / config.walk_speed_mps,
        "anchors": anchors,
        "points": [_point(config, anchor) for anchor in anchors],
    }


def _deck(config: SteelTideConfig, name: str, start: str, end: str, y_m: float) -> dict:
    uu = config.ue_units_per_meter
    x0 = config.anchors[start][0]
    x1 = config.anchors[end][0]
    length_m = abs(x1 - x0)
    return {
        "name": name,
        "x_min_uu": int(round(min(x0, x1) * uu)),
        "x_max_uu": int(round(max(x0, x1) * uu)),
        "y_uu": int(round(y_m * uu)),
        "width_uu": int(round(4 * uu)),
        "thickness_uu": int(round(0.4 * uu)),
        "length_m": length_m,
    }


def greybox_layout(config: SteelTideConfig | None = None) -> dict:
    config = config or load_config()
    return {
        "id": "NR01_SteelTide",
        "level": "NR_SteelTide_Greybox",
        "status": "layout_only_no_umap",
        "source": "sim/steel_tide/layout.py",
        "rules": "config/steel_tide_greybox.json",
        "ue_units_per_meter": config.ue_units_per_meter,
        "ue_axes": "sim x -> UE X, sim y -> UE Y, Z up, deck Z = 0",
        "walk_speed_uu_s": int(round(config.walk_speed_mps * config.ue_units_per_meter)),
        "actors": {
            name: {**_point(config, anchor, yaw), "note": note}
            for name, (anchor, yaw, note) in ACTORS.items()
        },
        "routes": {
            "elevated_spawn_a_to_center": _polyline(config, "spawn_a", "center", "elevated", "connected"),
            "elevated_spawn_b_to_center": _polyline(config, "spawn_b", "center", "elevated", "connected"),
            "repair_alley_spawn_a_to_center": _polyline(config, "spawn_a", "center", "repair_alley", "disconnected"),
            "repair_alley_spawn_b_to_center": _polyline(config, "spawn_b", "center", "repair_alley", "disconnected"),
        },
        "decks": [_deck(config, name, start, end, y_m) for name, start, end, y_m in DECKS],
        "alley_links": [
            {
                "name": "NR_AlleyLink_A",
                "x_uu": _point(config, "spawn_a")["x_uu"],
                "y_min_uu": 0,
                "y_max_uu": _point(config, "alley_a")["y_uu"],
            },
            {
                "name": "NR_AlleyLink_Mid",
                "x_uu": _point(config, "center")["x_uu"],
                "y_min_uu": 0,
                "y_max_uu": _point(config, "alley_mid")["y_uu"],
            },
            {
                "name": "NR_AlleyLink_B",
                "x_uu": _point(config, "spawn_b")["x_uu"],
                "y_min_uu": 0,
                "y_max_uu": _point(config, "alley_b")["y_uu"],
            },
        ],
    }


def export_layout(path: Path | None = None) -> Path:
    target = path or LAYOUT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(greybox_layout(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return target
