"""Load the greybox proposal shared with the UE operator cards."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config" / "steel_tide_greybox.json"


@dataclass(frozen=True)
class Edge:
    a: str
    b: str
    length_m: float
    bridge: bool
    route: str


@dataclass
class SteelTideConfig:
    walk_speed_mps: float
    sprint_speed_mps: float
    carrier_can_sprint: bool
    team_size: int
    match_seconds: float
    points_to_win: int
    overtime_seconds: float
    down_seconds: float
    spawn_protection_seconds: float
    score_channel_seconds: float
    bridge_warning_seconds: float
    pass_range_m: float
    pickup_radius_m: float
    terminal_half_extent_m: float
    core_reset_timeout_seconds: float
    ue_units_per_meter: int
    roles: tuple[str, ...]
    role_abilities: dict[str, dict]
    faction_rule: dict[str, tuple[str, ...]]
    badges: dict[str, dict[str, str]]
    score_terminal: dict[str, str]
    anchors: dict[str, tuple[float, float]]
    edges: tuple[Edge, ...]

    def seconds_to_ms(self, seconds: float) -> int:
        return int(round(float(seconds) * 1000))

    @property
    def match_ms(self) -> int:
        return self.seconds_to_ms(self.match_seconds)

    @property
    def overtime_ms(self) -> int:
        return self.seconds_to_ms(self.overtime_seconds)

    @property
    def down_ms(self) -> int:
        return self.seconds_to_ms(self.down_seconds)

    @property
    def spawn_protection_ms(self) -> int:
        return self.seconds_to_ms(self.spawn_protection_seconds)

    @property
    def score_channel_ms(self) -> int:
        return self.seconds_to_ms(self.score_channel_seconds)

    @property
    def bridge_warning_ms(self) -> int:
        return self.seconds_to_ms(self.bridge_warning_seconds)

    @property
    def core_reset_timeout_ms(self) -> int:
        return self.seconds_to_ms(self.core_reset_timeout_seconds)


def load_config(path: Path | None = None) -> SteelTideConfig:
    raw = json.loads((path or CONFIG_PATH).read_text(encoding="utf-8"))
    anchors = {key: (float(value[0]), float(value[1])) for key, value in raw["anchors"].items()}
    edges = tuple(
        Edge(
            a=item["a"],
            b=item["b"],
            length_m=float(item["length_m"]),
            bridge=bool(item["bridge"]),
            route=item["route"],
        )
        for item in raw["edges"]
    )
    faction_rule = {body: tuple(sides) for body, sides in raw["faction_rule"].items()}
    return SteelTideConfig(
        walk_speed_mps=float(raw["walk_speed_mps"]),
        sprint_speed_mps=float(raw["sprint_speed_mps"]),
        carrier_can_sprint=bool(raw["carrier_can_sprint"]),
        team_size=int(raw["team_size"]),
        match_seconds=float(raw["match_seconds"]),
        points_to_win=int(raw["points_to_win"]),
        overtime_seconds=float(raw["overtime_seconds"]),
        down_seconds=float(raw["down_seconds"]),
        spawn_protection_seconds=float(raw["spawn_protection_seconds"]),
        score_channel_seconds=float(raw["score_channel_seconds"]),
        bridge_warning_seconds=float(raw["bridge_warning_seconds"]),
        pass_range_m=float(raw["pass_range_m"]),
        pickup_radius_m=float(raw["pickup_radius_m"]),
        terminal_half_extent_m=float(raw["terminal_half_extent_m"]),
        core_reset_timeout_seconds=float(raw["core_reset_timeout_seconds"]),
        ue_units_per_meter=int(raw["ue_units_per_meter"]),
        roles=tuple(raw["roles"]),
        role_abilities=raw["role_abilities"],
        faction_rule=faction_rule,
        badges=raw["badges"],
        score_terminal=dict(raw["terminals"]["scores_at"]),
        anchors=anchors,
        edges=edges,
    )
