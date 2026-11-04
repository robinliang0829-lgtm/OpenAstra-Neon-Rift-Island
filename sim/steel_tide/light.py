"""Event-side light cue contract. No texture, Lumen scene, or cooked asset.

`SteelTideMatch._emit` asks this module for cue rows after it appends the
authoritative event. The cue copies that event's timestamp. It is not
appended to `match.events`, so it is not a new scoring name and it does
not change holder, score, or interrupt replay.

Shoulder ids come from the NR-03 badge: shape plus lamp slot. Auxiliary
color may tint the lamp and is not part of the id. Day-port and night-port
intensities are the config values. Bridge rows are timestamps of
`BridgeWarning*` / `BridgeLightStripAdvanced` / `BridgeStateChanged`.
This module does not schedule a warning.
"""

from __future__ import annotations

import json

from .model import Event
from .palette import BADGES, PALETTE

ASSET_NONE = "none"
CLOCK = "source_event"
RULES_EFFECT = "none"
TEXTURE_NONE = "none"

READ_BAR = "light.terminal.read_bar"
SCORE = "light.score"
SPAWN_PROTECTION = "light.spawn_protection"
BRIDGE_RAMP = "light.bridge.ramp"
BRIDGE_CONNECT = "light.bridge.connect"
BRIDGE_DISCONNECT = "light.bridge.disconnect"


def shoulder_cue_id(faction: str, shape: str, slot: str) -> str:
    """Id from faction, badge shape, and shoulder slot. Color is not an argument."""
    return f"light.shoulder.{faction}.{shape}.{slot}"


def shoulder_cue_id_for(faction: str) -> str:
    badge = BADGES[faction]
    return shoulder_cue_id(faction, badge["shape"], badge["light_slot"])


def catalog_ids() -> tuple[str, ...]:
    return (
        shoulder_cue_id_for("A"),
        shoulder_cue_id_for("B"),
        BRIDGE_RAMP,
        BRIDGE_CONNECT,
        BRIDGE_DISCONNECT,
        READ_BAR,
        SCORE,
        SPAWN_PROTECTION,
    )


def _payload_copy(payload: dict) -> dict:
    return json.loads(json.dumps(payload))


def _port_fields(lighting, intensity: float) -> dict:
    day = intensity / lighting.day_port_intensity
    night = intensity / lighting.night_port_intensity
    minimum = lighting.min_readable_contrast
    return {
        "contrast_day": day,
        "contrast_night": night,
        "day_port_intensity": lighting.day_port_intensity,
        "intensity": intensity,
        "min_readable_contrast": minimum,
        "night_port_intensity": lighting.night_port_intensity,
        "readable_day": day >= minimum,
        "readable_night": night >= minimum,
    }


def _row(match, event: Event, index: int, cue_id: str, family: str, intensity: float, fields: dict) -> Event:
    lighting = match.config.lighting
    payload = {
        "asset": ASSET_NONE,
        "clock": CLOCK,
        "color_assist": lighting.color_assist,
        "color_is_identity": False,
        "color_role": "none",
        "cue_id": cue_id,
        "family": family,
        "rules_effect": RULES_EFFECT,
        "source_event": event.name,
        "source_index": index,
        "texture": TEXTURE_NONE,
    }
    payload.update(_port_fields(lighting, intensity))
    payload.update(fields)
    return Event(event.t_ms, "LightCue", payload)


def _shoulder_cues(match, event: Event, index: int) -> list[Event]:
    rows: list[Event] = []
    lighting = match.config.lighting
    for combatant in sorted(match.combatants.values(), key=lambda item: item.id):
        faction = combatant.faction
        if faction not in BADGES:
            continue
        badge = BADGES[faction]
        config_badge = match.config.badges[faction]
        shape = config_badge["shape"]
        slot = config_badge["light_slot"]
        aux = PALETTE[badge["aux"]]
        rows.append(
            _row(
                match,
                event,
                index,
                shoulder_cue_id(faction, shape, slot),
                "shoulder",
                lighting.shoulder_intensity,
                {
                    "aux": badge["aux"],
                    "aux_hex": aux["hex"],
                    "aux_role": aux["role"],
                    "body": combatant.body,
                    "color_role": "auxiliary",
                    "combatant_id": combatant.id,
                    "faction": faction,
                    "light_slot": slot,
                    "ruleset": "nr03",
                    "shape": shape,
                },
            )
        )
    return rows


def _spawn_row(match, event: Event, index: int, fields: dict) -> Event:
    return _row(
        match,
        event,
        index,
        SPAWN_PROTECTION,
        "spawn",
        match.config.lighting.spawn_protection_intensity,
        fields,
    )


def _spawn_cues(match, event: Event, index: int) -> list[Event]:
    if event.name == "MatchStarted":
        rows: list[Event] = []
        for combatant in sorted(match.combatants.values(), key=lambda item: item.id):
            rows.append(
                _spawn_row(
                    match,
                    event,
                    index,
                    {
                        "anchor": combatant.anchor,
                        "combatant_id": combatant.id,
                        "faction": combatant.faction,
                        "protection_until_ms": combatant.protection_until_ms,
                        "ruleset": "greybox",
                    },
                )
            )
        return rows
    if event.name == "HitIgnored" and event.payload.get("reason") == "spawn_protection":
        target = match.combatants[event.payload["target_id"]]
        return [
            _spawn_row(
                match,
                event,
                index,
                {
                    "combatant_id": target.id,
                    "protection_until_ms": target.protection_until_ms,
                    "reason": "spawn_protection",
                    "ruleset": "greybox",
                    "source": _payload_copy(event.payload),
                },
            )
        ]
    if event.name == "ActorRespawned":
        return [
            _spawn_row(
                match,
                event,
                index,
                {
                    "combatant_id": event.payload.get("combatant_id"),
                    "protection_until_ms": event.payload.get("protection_until_ms"),
                    "ruleset": "greybox",
                    "source": _payload_copy(event.payload),
                },
            )
        ]
    return []


def _strip_index(event: Event) -> int | None:
    if event.name == "BridgeLightStripAdvanced":
        return event.payload.get("index")
    return event.payload.get("light_strip_index")


def _strip_offset(event: Event) -> int | None:
    if event.name == "BridgeWarningCompleted":
        return event.payload.get("elapsed_ms")
    return event.payload.get("offset_ms")


def _bridge_cues(match, event: Event, index: int) -> list[Event]:
    lighting = match.config.lighting
    if event.name in ("BridgeWarningStarted", "BridgeLightStripAdvanced", "BridgeWarningCompleted"):
        return [
            _row(
                match,
                event,
                index,
                BRIDGE_RAMP,
                "bridge",
                lighting.strip_intensity,
                {
                    "offset_ms": _strip_offset(event),
                    "ruleset": "nr03",
                    "source": _payload_copy(event.payload),
                    "strip_index": _strip_index(event),
                },
            )
        ]
    if event.name != "BridgeStateChanged":
        return []
    state = event.payload.get("state")
    if state == "connected":
        cue_id = BRIDGE_CONNECT
    elif state == "disconnected":
        cue_id = BRIDGE_DISCONNECT
    else:
        return []
    fields: dict = {"ruleset": "nr03", "source": _payload_copy(event.payload), "state": state}
    if state == "connected" and index > 0:
        previous = match.events[index - 1]
        if previous.name == "BridgeWarningCompleted" and previous.t_ms == event.t_ms:
            fields["paired_event"] = previous.name
            fields["paired_index"] = index - 1
    return [_row(match, event, index, cue_id, "bridge", lighting.strip_intensity, fields)]


def cues_for(match, event: Event, index: int) -> list[Event]:
    """Cue rows for one authoritative event. Empty when the event stays dark."""
    if event.name == "FactionsLocked":
        return _shoulder_cues(match, event, index)
    if event.name in ("MatchStarted", "HitIgnored", "ActorRespawned"):
        return _spawn_cues(match, event, index)
    if event.name == "ScoreChannelStarted":
        return [
            _row(
                match,
                event,
                index,
                READ_BAR,
                "terminal",
                match.config.lighting.read_bar_intensity,
                {
                    "duration_ms": event.payload.get("ends_ms", event.t_ms) - event.t_ms,
                    "ruleset": "greybox",
                    "source": _payload_copy(event.payload),
                    "terminal": event.payload.get("terminal"),
                },
            )
        ]
    if event.name == "PointScored":
        return [
            _row(
                match,
                event,
                index,
                SCORE,
                "score",
                match.config.lighting.score_intensity,
                {"ruleset": "greybox", "source": _payload_copy(event.payload)},
            )
        ]
    return _bridge_cues(match, event, index)
