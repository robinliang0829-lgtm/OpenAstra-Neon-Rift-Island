"""Event-side HUD cue contract. No UMG widget, texture, or cooked asset.

`SteelTideMatch._emit` asks this module for cue rows after it appends the
authoritative event. The cue copies that event's timestamp. It is not
appended to `match.events`, so it is not a new scoring name and it does
not change holder, score, or interrupt replay.

Faction text uses the NR-03 badge: shape plus shoulder slot. Auxiliary
color is recorded and is not part of the line or the id.
"""

from __future__ import annotations

import json

from .model import Event
from .palette import BADGES, PALETTE

ASSET_NONE = "none"
CLOCK = "source_event"
RULES_EFFECT = "none"
TEXTURE_NONE = "none"

SCOREBOARD = "hud.scoreboard"
READ_BAR = "hud.terminal.read_bar"
SPAWN_SHIELD = "hud.spawn_shield"
ROLE_LOCK = "hud.role_lock"
SIDE_LOCK = "hud.side_lock"

# family, cue id, authoritative names this row is allowed to mirror
PATHS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("scoreboard", SCOREBOARD, ("PointScored", "MatchSettled")),
    ("read_bar", READ_BAR, ("ScoreChannelStarted", "ScoreChannelInterrupted")),
    ("spawn_shield", SPAWN_SHIELD, ("MatchStarted", "HitIgnored", "ActorRespawned")),
    ("role_lock", ROLE_LOCK, ("RoleRejected",)),
    ("side_lock", SIDE_LOCK, ("FactionRejected",)),
)


def catalog_ids() -> tuple[str, ...]:
    return tuple(cue_id for _family, cue_id, _names in PATHS)


def _payload_copy(payload: dict) -> dict:
    return json.loads(json.dumps(payload))


def _identity(match, faction: str | None) -> dict | None:
    """Shape and shoulder slot. Color is attached as auxiliary and is not an id."""
    if not faction or faction not in BADGES or faction not in match.config.badges:
        return None
    badge = BADGES[faction]
    config_badge = match.config.badges[faction]
    aux = PALETTE[badge["aux"]]
    return {
        "aux": badge["aux"],
        "aux_hex": aux["hex"],
        "aux_role": aux["role"],
        "color_role": "auxiliary",
        "faction": faction,
        "identity": "shoulder_badge",
        "light_slot": config_badge["light_slot"],
        "shape": config_badge["shape"],
    }


def _geom(ident: dict) -> str:
    return f"{ident['shape']} {ident['light_slot']}"


def _combatant(match, combatant_id: str | None):
    if not combatant_id:
        return None
    return match.combatants.get(combatant_id)


def _row(event: Event, index: int, cue_id: str, family: str, line: str, fields: dict) -> Event:
    payload = {
        "asset": ASSET_NONE,
        "clock": CLOCK,
        "color_is_identity": False,
        "color_role": "none",
        "cue_id": cue_id,
        "family": family,
        "line": line,
        "rules_effect": RULES_EFFECT,
        "source": _payload_copy(event.payload),
        "source_event": event.name,
        "source_index": index,
        "texture": TEXTURE_NONE,
        "umg": False,
    }
    payload.update(fields)
    return Event(event.t_ms, "HudCue", payload)


def _score_bits(score: dict) -> str:
    return f"A {score.get('A')} B {score.get('B')}"


def _scoreboard_cues(match, event: Event, index: int) -> list[Event]:
    if event.name == "PointScored":
        faction = event.payload.get("faction")
        ident = _identity(match, faction)
        if ident is None:
            return []
        score = event.payload.get("score") or {}
        points = event.payload.get("points")
        line = (
            f"scoreboard point {faction} {_geom(ident)} points {points} score {_score_bits(score)}"
        )
        return [
            _row(
                event,
                index,
                SCOREBOARD,
                "scoreboard",
                line,
                {"points": points, "score": dict(score), "state": "point", **ident},
            )
        ]
    if event.name != "MatchSettled":
        return []
    score = event.payload.get("score") or {}
    sides = []
    tokens = []
    for faction in ("A", "B"):
        ident = _identity(match, faction)
        if ident is None:
            return []
        points = score.get(faction)
        sides.append({"faction": faction, "light_slot": ident["light_slot"], "points": points, "shape": ident["shape"]})
        tokens.append(f"{faction} {_geom(ident)} {points}")
    winner = event.payload.get("winner")
    winner_token = "none" if winner is None else winner
    kind = event.payload.get("kind")
    line = f"scoreboard settled {kind} winner {winner_token} score {' '.join(tokens)}"
    return [
        _row(
            event,
            index,
            SCOREBOARD,
            "scoreboard",
            line,
            {
                "color_role": "auxiliary",
                "identity": "shoulder_badge",
                "kind": kind,
                "score": dict(score),
                "sides": sides,
                "state": "settled",
                "winner": winner,
            },
        )
    ]


def _read_bar_cues(match, event: Event, index: int) -> list[Event]:
    combatant = _combatant(match, event.payload.get("combatant_id"))
    faction = combatant.faction if combatant is not None else None
    ident = _identity(match, faction)
    if ident is None or combatant is None:
        return []
    geom = _geom(ident)
    if event.name == "ScoreChannelStarted":
        ends_ms = event.payload.get("ends_ms")
        duration_ms = None if ends_ms is None else ends_ms - event.t_ms
        terminal = event.payload.get("terminal")
        line = (
            f"read_bar open {terminal} {combatant.id} {geom} filled 0 duration_ms {duration_ms}"
        )
        return [
            _row(
                event,
                index,
                READ_BAR,
                "read_bar",
                line,
                {
                    "combatant_id": combatant.id,
                    "duration_ms": duration_ms,
                    "filled_ms": 0,
                    "state": "open",
                    "terminal": terminal,
                    **ident,
                },
            )
        ]
    if event.name != "ScoreChannelInterrupted":
        return []
    elapsed = event.payload.get("elapsed_ms")
    reason = event.payload.get("reason")
    duration_ms = match.config.score_channel_ms
    line = (
        f"read_bar cleared {combatant.id} {geom} {reason} filled {elapsed} "
        f"duration_ms {duration_ms} scored false"
    )
    return [
        _row(
            event,
            index,
            READ_BAR,
            "read_bar",
            line,
            {
                "combatant_id": combatant.id,
                "duration_ms": duration_ms,
                "elapsed_ms": elapsed,
                "filled_ms": elapsed,
                "reason": reason,
                "scored": False,
                "state": "cleared",
                **ident,
            },
        )
    ]


def _spawn_row(match, event: Event, index: int, combatant, state: str, reason: str | None) -> Event:
    ident = _identity(match, combatant.faction)
    if ident is None:
        raise RuntimeError(f"spawn shield row missing badge for {combatant.id}")
    until_ms = combatant.protection_until_ms
    if event.name == "ActorRespawned" and event.payload.get("protection_until_ms") is not None:
        until_ms = event.payload["protection_until_ms"]
    anchor = event.payload.get("anchor") or combatant.anchor
    geom = _geom(ident)
    if state == "hold":
        line = (
            f"spawn_shield hold {combatant.id} {geom} {anchor} {reason} until_ms {until_ms}"
        )
    else:
        line = f"spawn_shield up {combatant.id} {geom} {anchor} until_ms {until_ms}"
    fields = {
        "anchor": anchor,
        "combatant_id": combatant.id,
        "protection_until_ms": until_ms,
        "state": state,
        **ident,
    }
    if reason is not None:
        fields["reason"] = reason
    return _row(event, index, SPAWN_SHIELD, "spawn_shield", line, fields)


def _spawn_cues(match, event: Event, index: int) -> list[Event]:
    if event.name == "MatchStarted":
        rows = []
        for combatant in sorted(match.combatants.values(), key=lambda item: item.id):
            rows.append(_spawn_row(match, event, index, combatant, "up", None))
        return rows
    if event.name == "HitIgnored" and event.payload.get("reason") == "spawn_protection":
        combatant = _combatant(match, event.payload.get("target_id"))
        if combatant is None:
            return []
        return [_spawn_row(match, event, index, combatant, "hold", "spawn_protection")]
    if event.name == "ActorRespawned":
        combatant = _combatant(match, event.payload.get("combatant_id"))
        if combatant is None:
            return []
        return [_spawn_row(match, event, index, combatant, "up", None)]
    return []


def _lock_cues(match, event: Event, index: int) -> list[Event]:
    if event.payload.get("reason") != "locked":
        return []
    combatant = _combatant(match, event.payload.get("combatant_id"))
    if combatant is None:
        return []
    if event.name == "RoleRejected":
        line = f"role_lock {combatant.id} locked"
        return [
            _row(
                event,
                index,
                ROLE_LOCK,
                "role_lock",
                line,
                {"combatant_id": combatant.id, "menu": "closed", "reason": "locked", "state": "locked"},
            )
        ]
    if event.name != "FactionRejected":
        return []
    ident = _identity(match, combatant.faction)
    if ident is None:
        return []
    line = f"side_lock {combatant.id} locked {_geom(ident)}"
    return [
        _row(
            event,
            index,
            SIDE_LOCK,
            "side_lock",
            line,
            {"combatant_id": combatant.id, "menu": "closed", "reason": "locked", "state": "locked", **ident},
        )
    ]


def cues_for(match, event: Event, index: int) -> list[Event]:
    """HUD rows for one authoritative event. Empty when the event has no line."""
    if event.name in ("PointScored", "MatchSettled"):
        return _scoreboard_cues(match, event, index)
    if event.name in ("ScoreChannelStarted", "ScoreChannelInterrupted"):
        return _read_bar_cues(match, event, index)
    if event.name in ("MatchStarted", "HitIgnored", "ActorRespawned"):
        return _spawn_cues(match, event, index)
    if event.name in ("RoleRejected", "FactionRejected"):
        return _lock_cues(match, event, index)
    return []
