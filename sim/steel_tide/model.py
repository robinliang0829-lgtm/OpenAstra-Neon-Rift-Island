"""State objects and the event-log audit shared with the UE wiring contract."""

from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class Event:
    t_ms: int
    name: str
    payload: dict

    def to_dict(self) -> dict:
        return {"t_ms": self.t_ms, "t_s": self.t_ms / 1000, "name": self.name, "payload": self.payload}

    def format(self) -> str:
        body = json.dumps(self.payload, ensure_ascii=False, sort_keys=True)
        return f"{self.t_ms / 1000:8.3f}  {self.name}  {body}"


@dataclass
class Core:
    anchor: str
    pos: tuple[float, float]
    status: str
    holder_id: str | None = None
    since_ms: int = 0

    @property
    def pickable(self) -> bool:
        return self.holder_id is None and self.status in ("spawn", "ground")


@dataclass
class Combatant:
    id: str
    client_id: str
    body: str
    controller: str
    face_variant: str | None = None
    faction: str | None = None
    role: str | None = None
    anchor: str | None = None
    pos: tuple[float, float] = (0.0, 0.0)
    anchor_since_ms: int = 0
    downed: bool = False
    respawn_ms: int | None = None
    protection_until_ms: int = 0
    preferred_route: str = "repair_alley"


@dataclass
class Channel:
    combatant_id: str
    terminal: str
    started_ms: int
    ends_ms: int


@dataclass
class Command:
    t_ms: int
    client_id: str
    seq: int
    kind: str
    payload: dict
    applied: bool = False


def badge_for(faction: str | None, badges: dict[str, dict[str, str]], face_variant: str | None = None) -> dict[str, str]:
    """Team identity is the match faction. `face_variant` is accepted and ignored."""
    del face_variant
    if faction not in badges:
        raise ValueError("unchosen combatants have no team badge")
    return dict(badges[faction])


def audit_holder_log(events: list[Event], final_holder: str | None) -> list[str]:
    """Replay holder changes. Two holders at once, or a second pick, is an error."""
    errors: list[str] = []
    holder: str | None = None
    for event in events:
        name = event.name
        if name == "CorePicked":
            if holder is not None:
                errors.append(f"{event.t_ms}: CorePicked while {holder} still held")
            holder = event.payload["combatant_id"]
        elif name == "CorePassed":
            if holder != event.payload["from_id"]:
                errors.append(f"{event.t_ms}: CorePassed from {event.payload['from_id']} but holder was {holder}")
            holder = event.payload["to_id"]
        elif name in ("CoreDropped", "CoreReset", "CoreReturnedToCenter"):
            holder = None
    if holder != final_holder:
        errors.append(f"log holder {holder} != state holder {final_holder}")
    return errors
