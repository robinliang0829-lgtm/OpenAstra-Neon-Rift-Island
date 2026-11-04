"""Local strategy bots. They are not production digital residents."""

from __future__ import annotations

from .config import SteelTideConfig, load_config
from .match import SteelTideMatch
from .routes import shortest_path, step_edge


def run_bot_slice(horizon_s: float = 36.0, config: SteelTideConfig | None = None) -> SteelTideMatch:
    """Two local bots, opposite factions, same humanoid body, repair-alley route.

    The bridge stays down, so both walk the alley, reach the core together, and
    the server grants it to one client.
    """
    match = SteelTideMatch(config or load_config())
    match.add_combatant(
        "a1",
        "client-a",
        "humanoid_robot",
        "local_bot",
        face_variant="same-face",
        preferred_route="repair_alley",
    )
    match.add_combatant(
        "b1",
        "client-b",
        "humanoid_robot",
        "local_bot",
        face_variant="same-face",
        preferred_route="repair_alley",
    )
    match.choose_faction("a1", "A")
    match.choose_faction("b1", "B")
    match.choose_role("a1", "assault")
    match.choose_role("b1", "recon")
    match.start()
    horizon = match.config.seconds_to_ms(horizon_s)
    for _ in range(10000):
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
    return (match.t_ms, pending, len(match.events), match.core.holder_id, match.phase)


def _issue(match: SteelTideMatch) -> None:
    for combatant in match.combatants.values():
        if combatant.downed or match.phase not in ("live", "overtime"):
            continue
        action, dest = _decide(match, combatant)
        if action == "pick" and not match.has_pending(combatant.id, "pick_core"):
            match.enqueue(combatant.client_id, "pick_core", match.t_seconds, combatant_id=combatant.id)
        elif action == "score" and match.channel is None and not match.has_pending(combatant.id, "begin_score"):
            match.enqueue(combatant.client_id, "begin_score", match.t_seconds, combatant_id=combatant.id)
        elif action == "move" and dest and not match.has_pending(combatant.id, "request_move"):
            edge = step_edge(match.config, combatant.anchor or "", dest, combatant.preferred_route, match.bridge_state)
            if edge is None:
                continue
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


def _decide(match: SteelTideMatch, combatant) -> tuple[str, str | None]:
    if combatant.faction is None or combatant.anchor is None:
        return "idle", None
    enemy_terminal = match.config.score_terminal[combatant.faction]
    if match.core.holder_id == combatant.id:
        if combatant.anchor == enemy_terminal:
            return "score", None
        return _move_toward(match, combatant, enemy_terminal)
    if match.core.pickable:
        if combatant.anchor == match.core.anchor:
            return "pick", None
        return _move_toward(match, combatant, match.core.anchor)
    return "idle", None


def _move_toward(match: SteelTideMatch, combatant, goal: str) -> tuple[str, str | None]:
    path = shortest_path(match.config, combatant.anchor, goal, combatant.preferred_route, match.bridge_state)
    if not path:
        return "idle", None
    return "move", path[0]
