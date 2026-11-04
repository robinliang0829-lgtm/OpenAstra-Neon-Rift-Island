"""Event-side audio cue contract. No wave, MetaSound, or cooked asset.

`SteelTideMatch._emit` asks this module for cue rows after it appends the
authoritative event. The cue copies that event's timestamp. It is not
appended to `match.events`, so it is not a new scoring name and it does
not change holder, score, or interrupt replay.

Team ids come from the NR-03 badge: shape plus shoulder-lamp mouth.
Auxiliary color is recorded and is not part of the id. Bridge cues are
rows on `BridgeWarning*` / `BridgeStateChanged`. They do not schedule a
second warning. Core cues are one row on each link of the chain.
"""

from __future__ import annotations

import json

from .model import Event
from .palette import BADGES, PALETTE

ASSET_NONE = "none"
CLOCK = "source_event"
RULES_EFFECT = "none"

CORE_CUES: tuple[tuple[str, str], ...] = (
    ("CorePicked", "sfx.core.pickup"),
    ("CorePassed", "sfx.core.pass"),
    ("CoreDropped", "sfx.core.drop"),
    ("ScoreChannelStarted", "sfx.core.channel_start"),
    ("ScoreChannelInterrupted", "sfx.core.interrupt"),
    ("PointScored", "sfx.core.score"),
    ("CoreReturnedToCenter", "sfx.core.return_to_center"),
    ("CoreReset", "sfx.core.reset"),
)
CORE_CUE_IDS = {name: cue_id for name, cue_id in CORE_CUES}

BRIDGE_WARN = "sfx.bridge.warn"
BRIDGE_LIGHT_STRIP = "sfx.bridge.light_strip"
BRIDGE_CONNECT = "sfx.bridge.connect"
BRIDGE_DISCONNECT = "sfx.bridge.disconnect"
BRIDGE_CUES: tuple[tuple[str, str], ...] = (
    ("BridgeWarningStarted", BRIDGE_WARN),
    ("BridgeLightStripAdvanced", BRIDGE_LIGHT_STRIP),
    ("BridgeStateChanged:connected", BRIDGE_CONNECT),
    ("BridgeStateChanged:disconnected", BRIDGE_DISCONNECT),
)

# Rejection names stay silent. The successful event is the cue.
SILENT_EVENTS = frozenset(
    {
        "AbilityRejected",
        "BridgeWarningCompleted",
        "CoreDropRejected",
        "CoreMarkRejected",
        "CoreMarkedUnpickable",
        "CorePassRejected",
        "CorePickRejected",
        "FactionRejected",
        "HitRejected",
        "MoveRejected",
        "RoleRejected",
        "RouteRejected",
        "ScoreChannelRejected",
    }
)


def team_cue_id(faction: str, shape: str, mouth: str) -> str:
    """Id from faction, badge shape, and lamp-side mouth. Color is not an argument."""
    return f"sfx.team.{faction}.{shape}.mouth.{mouth}"


def team_cue_id_for(faction: str) -> str:
    badge = BADGES[faction]
    return team_cue_id(faction, badge["shape"], badge["light_slot"])


def catalog_ids() -> tuple[str, ...]:
    return (
        team_cue_id_for("A"),
        team_cue_id_for("B"),
        *(cue_id for _name, cue_id in BRIDGE_CUES),
        *(cue_id for _name, cue_id in CORE_CUES),
    )


def _payload_copy(payload: dict) -> dict:
    return json.loads(json.dumps(payload))


def _row(event: Event, index: int, cue_id: str, family: str, fields: dict) -> Event:
    payload = {
        "asset": ASSET_NONE,
        "clock": CLOCK,
        "color_is_identity": False,
        "color_role": "none",
        "cue_id": cue_id,
        "family": family,
        "rules_effect": RULES_EFFECT,
        "source_event": event.name,
        "source_index": index,
    }
    payload.update(fields)
    return Event(event.t_ms, "AudioCue", payload)


def _team_cues(match, event: Event, index: int) -> list[Event]:
    rows: list[Event] = []
    for combatant in sorted(match.combatants.values(), key=lambda item: item.id):
        faction = combatant.faction
        if faction not in BADGES:
            continue
        badge = BADGES[faction]
        config_badge = match.config.badges[faction]
        shape = config_badge["shape"]
        mouth = config_badge["light_slot"]
        aux = PALETTE[badge["aux"]]
        rows.append(
            _row(
                event,
                index,
                team_cue_id(faction, shape, mouth),
                "team",
                {
                    "aux": badge["aux"],
                    "aux_hex": aux["hex"],
                    "aux_role": aux["role"],
                    "body": combatant.body,
                    "color_role": "auxiliary",
                    "combatant_id": combatant.id,
                    "faction": faction,
                    "light_slot": mouth,
                    "mouth": mouth,
                    "shape": shape,
                },
            )
        )
    return rows


def _bridge_fields(match, event: Event, index: int) -> dict | None:
    if event.name == "BridgeWarningStarted":
        return {"cue_id": BRIDGE_WARN, "ruleset": "nr03", "source": _payload_copy(event.payload)}
    if event.name == "BridgeLightStripAdvanced":
        return {"cue_id": BRIDGE_LIGHT_STRIP, "ruleset": "nr03", "source": _payload_copy(event.payload)}
    if event.name != "BridgeStateChanged":
        return None
    state = event.payload.get("state")
    if state == "connected":
        fields: dict = {
            "cue_id": BRIDGE_CONNECT,
            "ruleset": "nr03",
            "source": _payload_copy(event.payload),
        }
        if index > 0:
            previous = match.events[index - 1]
            if previous.name == "BridgeWarningCompleted" and previous.t_ms == event.t_ms:
                fields["paired_event"] = previous.name
                fields["paired_index"] = index - 1
        return fields
    if state == "disconnected":
        return {"cue_id": BRIDGE_DISCONNECT, "ruleset": "nr03", "source": _payload_copy(event.payload)}
    return None


def cues_for(match, event: Event, index: int) -> list[Event]:
    """Cue rows for one authoritative event. Empty when the event is silent."""
    if event.name in SILENT_EVENTS:
        return []
    if event.name == "FactionsLocked":
        return _team_cues(match, event, index)
    cue_id = CORE_CUE_IDS.get(event.name)
    if cue_id is not None:
        return [_row(event, index, cue_id, "core", {"source": _payload_copy(event.payload)})]
    bridge = _bridge_fields(match, event, index)
    if bridge is None:
        return []
    cue_id = bridge.pop("cue_id")
    return [_row(event, index, cue_id, "bridge", bridge)]
