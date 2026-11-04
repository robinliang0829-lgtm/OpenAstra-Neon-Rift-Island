"""Local bot policy for one 3v3. Not a production digital resident.

Decisions are `BotDecision` events: action, reason, target_id. The resident
adapter is `resident_port.DigitalResidentPort`. This module does not construct
it and does not call it. NR-M2-resident is the card that does. `controller=local_bot`
is not rewritten into `digital_resident`.

Hit stays server-only. When an assault shares the reader's anchor, the policy
records `interrupt_channel` and the sim enqueues the server `hit`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .match import SERVER_CLIENT, SteelTideMatch
from .routes import shortest_path, step_edge

# The assault contests the channel one second after it starts, inside the 3s read.
INTERRUPT_AFTER_S = 1.0


@dataclass(frozen=True)
class Decision:
    action: str
    reason: str
    target_id: str
    goal: str | None = None
    distance_m: float | None = None


def run_local_bots(match: SteelTideMatch, horizon_s: float | None = None) -> SteelTideMatch:
    """Step local_bot intents until the match settles or the horizon."""
    horizon = match.config.match_ms if horizon_s is None else match.config.seconds_to_ms(horizon_s)
    for _ in range(100000):
        if match.phase == "settled" or match.t_ms >= horizon:
            break
        before = _fingerprint(match)
        _issue(match)
        match.advance_to_ms(match.peek_next_ms(horizon))
        if _fingerprint(match) == before:
            break
    return match


def _fingerprint(match: SteelTideMatch) -> tuple:
    pending = sum(1 for cmd in match.inbox if not cmd.applied)
    return (
        match.t_ms,
        pending,
        len(match.events),
        match.core.holder_id,
        match.phase,
        match.score["A"],
        match.score["B"],
    )


def _issue(match: SteelTideMatch) -> None:
    for combatant in match.combatants.values():
        if combatant.controller != "local_bot":
            continue
        decision = decide(match, combatant)
        if decision is None:
            continue
        _commit(match, combatant, decision)


def decide(match: SteelTideMatch, combatant) -> Decision | None:
    """One intent for a local bot. Humans and residents are not decided here."""
    if combatant.controller != "local_bot":
        return None
    if combatant.downed or combatant.faction is None or combatant.anchor is None:
        return None
    if match.phase not in ("live", "overtime"):
        return None
    if _should_interrupt(match, combatant):
        return Decision("interrupt_channel", "contest_channel", match.channel.combatant_id)
    if match.core.holder_id == combatant.id:
        return _decide_holder(match, combatant)
    if match.core.pickable:
        if combatant.anchor == match.core.anchor:
            return Decision("pick_core", "contest_core", "core")
        return Decision("request_move", "contest_core", "core", goal=match.core.anchor)
    holder = match.combatants[match.core.holder_id]
    if holder.faction == combatant.faction:
        # In-range teammate waits for the pass. The passer stays for the return.
        return None
    if _interrupt_open(match) and combatant.role == "assault":
        terminal = match.config.score_terminal[holder.faction]
        if combatant.anchor != terminal:
            return Decision("request_move", "interrupt_channel", holder.id, goal=terminal)
        return None
    # Other enemies hold. The alley does not reach terminal_a, so they stay on
    # the core and contest it again when a point sends it back.
    return None


def _decide_holder(match: SteelTideMatch, combatant) -> Decision | None:
    terminal = match.config.score_terminal[combatant.faction or ""]
    if not match.named("CorePassed"):
        mate = _pass_target(match, combatant)
        if mate is not None:
            return Decision(
                "pass_core",
                "close_range_pass",
                mate.id,
                distance_m=round(_distance(combatant, mate), 3),
            )
    if combatant.anchor == terminal and match.channel is None:
        return Decision("begin_score", "score_path", terminal)
    if combatant.anchor != terminal:
        return Decision("request_move", "score_path", terminal, goal=terminal)
    return None


def _should_interrupt(match: SteelTideMatch, combatant) -> bool:
    channel = match.channel
    if channel is None or not _interrupt_open(match) or combatant.role != "assault":
        return False
    reader = match.combatants[channel.combatant_id]
    if reader.faction == combatant.faction or reader.anchor != combatant.anchor:
        return False
    return not _pending_hit(match, reader.id)


def _interrupt_open(match: SteelTideMatch) -> bool:
    return not match.named("ScoreChannelInterrupted")


def _pass_target(match: SteelTideMatch, combatant):
    found = []
    for other in match.combatants.values():
        if other.id == combatant.id or other.faction != combatant.faction or other.downed:
            continue
        if other.anchor is None:
            continue
        if _distance(combatant, other) <= match.config.pass_range_m:
            found.append(other)
    if not found:
        return None
    found.sort(key=lambda item: item.id)
    return found[0]


def _distance(left, right) -> float:
    return math.hypot(left.pos[0] - right.pos[0], left.pos[1] - right.pos[1])


def _pending_hit(match: SteelTideMatch, target_id: str) -> bool:
    return any(
        not cmd.applied and cmd.kind == "hit" and cmd.payload.get("target_id") == target_id for cmd in match.inbox
    )


def _pending_pass(match: SteelTideMatch, combatant_id: str) -> bool:
    return any(
        not cmd.applied and cmd.kind == "pass_core" and cmd.payload.get("from_id") == combatant_id
        for cmd in match.inbox
    )


def _commit(match: SteelTideMatch, combatant, decision: Decision) -> None:
    if combatant.controller not in ("local_bot", "digital_resident"):
        return
    action = decision.action
    if action == "request_move":
        if not _enqueue_move(match, combatant, decision.goal or ""):
            return
    elif action == "pick_core":
        if match.has_pending(combatant.id, "pick_core"):
            return
        match.enqueue(combatant.client_id, "pick_core", match.t_seconds, combatant_id=combatant.id)
    elif action == "pass_core":
        if _pending_pass(match, combatant.id):
            return
        match.enqueue(
            combatant.client_id,
            "pass_core",
            match.t_seconds,
            from_id=combatant.id,
            to_id=decision.target_id,
        )
    elif action == "begin_score":
        if match.channel is not None or match.has_pending(combatant.id, "begin_score"):
            return
        match.enqueue(combatant.client_id, "begin_score", match.t_seconds, combatant_id=combatant.id)
    elif action == "interrupt_channel":
        if _pending_hit(match, decision.target_id):
            return
        # Server resolves contact. The bot client does not send hit.
        match.enqueue(
            SERVER_CLIENT,
            "hit",
            match.t_seconds + INTERRUPT_AFTER_S,
            target_id=decision.target_id,
            down=False,
        )
    else:
        return
    if combatant.controller == "local_bot":
        match.note_bot_decision(
            combatant.id,
            action,
            decision.reason,
            decision.target_id,
            distance_m=decision.distance_m,
        )
    elif combatant.controller == "digital_resident":
        match.note_resident_decision(
            combatant.id,
            action,
            decision.reason,
            decision.target_id,
            distance_m=decision.distance_m,
        )


def _enqueue_move(match: SteelTideMatch, combatant, goal: str) -> bool:
    if not goal or match.has_pending(combatant.id, "request_move"):
        return False
    path = shortest_path(match.config, combatant.anchor or "", goal, combatant.preferred_route, match.bridge_state)
    if not path:
        return False
    dest = path[0]
    edge = step_edge(match.config, combatant.anchor or "", dest, combatant.preferred_route, match.bridge_state)
    if edge is None:
        return False
    travel_ms = match._travel_ms(edge.length_m, combatant.id)
    earliest = combatant.anchor_since_ms + travel_ms
    eta_ms = earliest if earliest >= match.t_ms else match.t_ms
    match.enqueue(
        combatant.client_id,
        "request_move",
        eta_ms / 1000,
        combatant_id=combatant.id,
        dest=dest,
        route=combatant.preferred_route,
    )
    return True
