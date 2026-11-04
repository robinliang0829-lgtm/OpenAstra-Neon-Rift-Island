"""NR-M2 bridge slice: open and close the span on the route graph.

One command:

    PYTHONPATH=sim python3 -m steel_tide m2-bridge
    PYTHONPATH=sim python3 -m steel_tide m2-bridge --check

The 4 second warning is NR-03 `schedule_bridge_connect`. Disconnect is the
existing `schedule_bridge_disconnect`. Grab, pass, interrupt, first-to-2,
and the role abilities stay on the earlier decision APIs. This slice does
not add a scorer and does not add an event name.

While the span is open (disconnected) it is not in the walkable graph.
The repair alley still is, and a point can be scored on it. Connecting the
span puts those edges back and recomputes paths that use them. Opening it
again drops the edges, rejects a step onto the span, and moves anyone
standing on `center` to a faction bridgehead. That move does not score and
does not down them.
"""

from __future__ import annotations

from .config import CONFIG_PATH, SteelTideConfig, load_config
from .dual_log import compare_dual_logs, diff_against_evidence, render_dual_logs, write_evidence
from .match import SERVER_CLIENT, SteelTideMatch
from .nr_m2_resident import _extra, _fingerprint, _issue, _open
from .resident_port import POST_WALL_KEYS, DigitalResidentPort
from .routes import authoritative_edges, is_span_edge, span_edge_token

SCHEMA = "nr-m2-bridge-dual-end-v1"
EVIDENCE_DIR = CONFIG_PATH.parents[1] / "docs" / "evidence" / "nr-m2-bridge"
CONNECT_AT_S = 7.5
DISCONNECT_AT_S = 12.0
# b2 walks the elevated deck and has to wait at the bridgehead until the span exists.
ELEVATED = {"b2": "elevated"}


def run_m2_bridge_match(config: SteelTideConfig | None = None) -> SteelTideMatch:
    config = config or load_config()
    port = DigitalResidentPort()
    match = _open(config, port, ELEVATED)
    match.resident_port = port
    match.role_abilities_enabled = True
    match.ability_progress = {}
    # NR-03 warning, then the same match clock opens the span again.
    match.schedule_bridge_connect(CONNECT_AT_S)
    match.schedule_bridge_disconnect(DISCONNECT_AT_S)
    horizon = match.config.match_ms
    for _ in range(100000):
        if match.phase == "settled" or match.t_ms >= horizon:
            break
        before = _fingerprint(match)
        _issue(match, port)
        match.advance_to_ms(match.peek_next_ms(horizon))
        if _fingerprint(match) == before:
            break
    return match


def _bridge_clock(match: SteelTideMatch) -> dict[int, str]:
    """Bridge state after each event, starting from disconnected."""
    state = "disconnected"
    states: dict[int, str] = {}
    for event in match.events:
        if event.name == "BridgeStateChanged":
            reported = event.payload.get("state")
            if reported in ("connected", "disconnected"):
                state = reported
        states[event.t_ms] = state
    return states


def _state_at(clock: dict[int, str], t_ms: int) -> str:
    known = [stamp for stamp in clock if stamp <= t_ms]
    if not known:
        return "disconnected"
    return clock[max(known)]


def _safety_errors(match: SteelTideMatch, involved: set[str], t_ms: int, label: str) -> list[str]:
    """A bridge teleport or reject must not score, drop the core, or down a body.

    A channel that already started for someone else can still complete on
    this millisecond. That point is the score clock, not the span move.
    """
    errors = []
    for event in match.events:
        if event.t_ms != t_ms:
            continue
        if event.name in ("CoreDropped", "CoreReset", "ActorDowned"):
            errors.append(f"{label} at {t_ms} changed the core or the body: {event.name}")
        elif event.name == "PointScored" and event.payload.get("combatant_id") in involved:
            errors.append(f"{label} scored for {event.payload.get('combatant_id')}")
        elif event.name == "PointScored":
            started = [
                item
                for item in match.named("ScoreChannelStarted")
                if item.t_ms < t_ms and item.payload.get("combatant_id") == event.payload.get("combatant_id")
            ]
            if not started:
                errors.append(f"{label} at {t_ms} produced a point without a channel")
    return errors


def _bridge_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    connect_ms = config.seconds_to_ms(CONNECT_AT_S)
    disconnect_ms = config.seconds_to_ms(DISCONNECT_AT_S)
    start_ms = connect_ms - config.bridge_warning_ms
    started = match.named("BridgeWarningStarted")
    completed = match.named("BridgeWarningCompleted")
    changed = match.named("BridgeStateChanged")
    connected = [event for event in changed if event.payload.get("state") == "connected"]
    disconnected = [event for event in changed if event.payload.get("state") == "disconnected"]
    if len(started) != 1 or started[0].t_ms != start_ms or started[0].payload.get("lead_ms") != config.bridge_warning_ms:
        errors.append("bridge warning did not reuse the configured 4 second lead")
    elif started[0].payload.get("readable_without_reflection") is not True:
        errors.append("bridge warning dropped readable_without_reflection")
    if not match.named("BridgeLightStripAdvanced"):
        errors.append("bridge warning did not reuse BridgeLightStripAdvanced")
    elif any(not start_ms < event.t_ms < connect_ms for event in match.named("BridgeLightStripAdvanced")):
        errors.append("a light strip step fell outside the warning window")
    if len(completed) != 1 or completed[0].t_ms != connect_ms:
        errors.append("bridge warning did not complete on the connect timestamp")
    elif completed[0].payload.get("elapsed_ms") != config.bridge_warning_ms:
        errors.append("bridge warning elapsed was not the configured lead")
    if len(connected) != 1 or connected[0].t_ms != connect_ms:
        errors.append("BridgeStateChanged connected was not on the warning-complete timestamp")
    if len(disconnected) != 1 or disconnected[0].t_ms != disconnect_ms:
        errors.append("BridgeStateChanged disconnected was not on the scheduled open")
    elif not connected or disconnected[0].t_ms <= connected[0].t_ms:
        errors.append("the span opened before it had connected")
    open_edges = [edge for edge in authoritative_edges(config, "disconnected") if edge.bridge]
    shut_edges = [edge for edge in authoritative_edges(config, "connected") if edge.bridge]
    if open_edges or len(shut_edges) != 2:
        errors.append("the authoritative graph did not drop the span while it is open")
    if any(edge.bridge for edge in match.route_graph):
        errors.append("the match left a span edge in the route graph after the open")
    elif span_edge_token(config, "disconnected") != "":
        errors.append("an open span still published walkable span edges")
    if span_edge_token(config, "connected") == "":
        errors.append("a connected span published no span edges")
    return errors


def _recompute_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    connect_ms = config.seconds_to_ms(CONNECT_AT_S)
    disconnect_ms = config.seconds_to_ms(DISCONNECT_AT_S)
    recomputes = []
    for name in ("BotDecision", "ResidentDecision"):
        for event in match.named(name):
            if event.payload.get("reason") == "path_recompute":
                recomputes.append(event)
    if not recomputes:
        errors.append("bridge toggles did not recompute a path")
        return errors
    for event in recomputes:
        payload = event.payload
        if payload.get("action") != "request_move":
            errors.append(f"path recompute was not a move intent: {payload}")
        for key in POST_WALL_KEYS:
            if key in payload:
                errors.append(f"path recompute carries coordinates: {payload}")
        if payload.get("route") not in ("elevated", "repair_alley", "walkable"):
            errors.append(f"path recompute route is not on the route graph: {payload}")
    crossed = [
        event
        for event in recomputes
        if event.t_ms == connect_ms and event.payload.get("bridge_state") == "connected" and event.payload.get("span_walkable") is True
    ]
    opened = [
        event
        for event in recomputes
        if event.t_ms == disconnect_ms
        and event.payload.get("bridge_state") == "disconnected"
        and event.payload.get("span_walkable") is False
        and event.payload.get("span_edges") == ""
    ]
    if not crossed:
        errors.append("connecting the span did not recompute a walkable-span path")
    else:
        saw_span = False
        for event in crossed:
            anchor = event.payload.get("anchor")
            hops = [hop for hop in str(event.payload.get("path") or "").split(">") if hop]
            if hops and isinstance(anchor, str) and is_span_edge(config, anchor, hops[0]):
                saw_span = True
            if event.payload.get("span_edges") != span_edge_token(config, "connected"):
                errors.append("the connected recompute did not publish the span edges")
        if not saw_span:
            errors.append("the connected recompute did not step onto a span edge")
    if not opened:
        errors.append("opening the span did not recompute a path with the span removed")
    else:
        for event in opened:
            anchor = event.payload.get("anchor")
            hops = [hop for hop in str(event.payload.get("path") or "").split(">") if hop]
            node = anchor if isinstance(anchor, str) else ""
            for hop in hops:
                if node and is_span_edge(config, node, hop):
                    errors.append(f"an open-span recompute still crosses the span: {event.payload}")
                    break
                node = hop
    return errors


def _safety_story_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    connect_ms = config.seconds_to_ms(CONNECT_AT_S)
    disconnect_ms = config.seconds_to_ms(DISCONNECT_AT_S)
    nudged = match.named("BridgeOccupantNudged")
    if not nudged:
        errors.append("nobody on the span was moved to a safe bridgehead")
    else:
        if any(event.t_ms != disconnect_ms for event in nudged):
            errors.append("a span nudge happened at a time other than the open")
        for event in nudged:
            payload = event.payload
            if payload.get("reason") != "span_not_embedded":
                errors.append(f"span nudge reason drifted: {payload}")
            dest = payload.get("to")
            if dest not in ("bridgehead_a", "bridgehead_b"):
                errors.append(f"span nudge did not land on a bridgehead: {payload}")
            errors.extend(_safety_errors(match, {str(payload.get("combatant_id"))}, event.t_ms, "span nudge"))
        if match.named("ActorDowned"):
            errors.append("a body was downed; the span must not crush")
    blocked = [
        event
        for event in match.named("MoveRejected")
        if event.payload.get("reason") == "bridge_blocked" and event.payload.get("dest") == "center"
    ]
    if not blocked:
        errors.append("a step onto the open span was not rejected at the edge")
    else:
        for event in blocked:
            errors.extend(_safety_errors(match, {str(event.payload.get("combatant_id"))}, event.t_ms, "span reject"))
            if _state_at(_bridge_clock(match), event.t_ms) == "connected" and event.t_ms != disconnect_ms:
                errors.append("the span rejected a crossing while it was connected")
    clock = _bridge_clock(match)
    alley = [
        event
        for event in match.named("MoveCompleted")
        if event.payload.get("route") == "repair_alley" and event.t_ms < connect_ms
    ]
    if not alley:
        errors.append("the repair alley was not walked while the span was open")
    crossed = []
    for event in match.named("MoveCompleted"):
        if not is_span_edge(config, event.payload.get("from", ""), event.payload.get("to", "")):
            continue
        state = _state_at(clock, event.t_ms)
        if state != "connected":
            errors.append(f"a span step completed while the bridge was {state}: {event.payload}")
        elif connect_ms <= event.t_ms < disconnect_ms:
            crossed.append(event)
    if not crossed:
        errors.append("nobody crossed the span after it connected and before it opened again")
    scored_open = [
        event
        for event in match.named("PointScored")
        if _state_at(clock, event.t_ms) == "disconnected"
    ]
    if not scored_open:
        errors.append("the repair alley did not score while the span was open")
    for event in match.named("MoveCompleted"):
        if _state_at(clock, event.t_ms) != "disconnected":
            continue
        if is_span_edge(config, event.payload.get("from", ""), event.payload.get("to", "")):
            errors.append(f"a disconnected move used the span: {event.payload}")
    return errors


def _play_errors(match: SteelTideMatch) -> list[str]:
    """Grab, pass, interrupt, and first-to-2, through the existing match APIs."""
    errors: list[str] = []
    config = match.config
    picked = match.named("CorePicked")
    if not picked:
        errors.append("nobody grabbed the core")
    else:
        opening = picked[0]
        rejected = [
            event
            for event in match.named("CorePickRejected")
            if event.t_ms == opening.t_ms and event.payload.get("reason") == "already_held"
        ]
        if not rejected:
            errors.append("the grab did not reject a second holder in the same frame")
        if opening.payload.get("anchor") != "center":
            errors.append("the grab was not at center")
    passed = match.named("CorePassed")
    if len(passed) != 1:
        errors.append(f"expected one close-range pass, got {len(passed)}")
    else:
        decided = [
            event
            for event in match.named("ResidentDecision") + match.named("BotDecision")
            if event.payload.get("action") == "pass_core" and event.payload.get("reason") == "close_range_pass"
        ]
        if len(decided) != 1 or decided[0].t_ms != passed[0].t_ms:
            errors.append("the pass was not one existing close_range_pass decision")
        else:
            distance = decided[0].payload.get("distance_m")
            if not isinstance(distance, (int, float)) or isinstance(distance, bool) or distance > config.pass_range_m:
                errors.append("the pass was outside pass_range_m")
            if decided[0].payload.get("combatant_id") != passed[0].payload.get("from_id"):
                errors.append("the pass decision was not the holder")
            if decided[0].payload.get("target_id") != passed[0].payload.get("to_id"):
                errors.append("the pass decision did not name the receiver")
    interrupted = match.named("ScoreChannelInterrupted")
    if len(interrupted) != 1 or interrupted[0].payload.get("reason") != "hit":
        errors.append("expected one hit interrupt of a score channel")
    elif any(event.name == "PointScored" and event.t_ms == interrupted[0].t_ms for event in match.events):
        errors.append("the interrupted channel scored")
    else:
        hits = [cmd for cmd in match.inbox if cmd.kind == "hit" and cmd.t_ms == interrupted[0].t_ms]
        if len(hits) != 1 or hits[0].client_id != SERVER_CLIENT or hits[0].payload.get("down") is not False:
            errors.append("the interrupt was not one server hit with down false")
    scored = match.named("PointScored")
    if len(scored) != 2:
        errors.append(f"expected first-to-2, got {len(scored)} points")
        return errors
    if interrupted and scored[0].t_ms <= interrupted[0].t_ms:
        errors.append("a point landed at or before the interrupt")
    settled = match.named("MatchSettled")
    if len(settled) != 1 or settled[0].t_ms != scored[1].t_ms:
        errors.append("first-to-2 did not settle on the second point")
    elif settled[0].payload.get("kind") != "points" or settled[0].payload.get("score") != {"A": 2, "B": 0}:
        errors.append(f"settlement was not a 2-0 points win: {settled[0].payload if settled else None}")
    if match.named("OvertimeStarted") or match.named("MatchClockExpired"):
        errors.append("regulation first-to-2 opened overtime or waited for the clock")
    if match.phase != "settled" or match.settled_kind != "points" or match.score != {"A": 2, "B": 0}:
        errors.append(f"slice ended phase={match.phase} kind={match.settled_kind} score={match.score}")
    if match.core.holder_id is not None or match.core.anchor != "center":
        errors.append("the scoring core did not return to center")
    if len(match.named("CoreReturnedToCenter")) != 2:
        errors.append("each clean channel should return the core once")
    abilities = {event.payload.get("ability") for event in match.named("AbilityUsed") + match.named("AbilityRejected")}
    abilities.discard(None)
    if abilities - {"dash", "shield", "mark"}:
        errors.append(f"a role ability left the existing set: {sorted(abilities)}")
    if not match.role_abilities_enabled:
        errors.append("role abilities were not left on the existing API")
    return errors


def _roster_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    if len(match.combatants) != 6:
        errors.append(f"expected 6 combatants, got {len(match.combatants)}")
    if sorted(combatant.faction for combatant in match.combatants.values()) != ["A", "A", "A", "B", "B", "B"]:
        errors.append("roster is not 3v3")
    humans = [combatant for combatant in match.combatants.values() if combatant.controller == "human"]
    if sorted((combatant.id, combatant.client_id) for combatant in humans) != [("a1", "client-a"), ("b1", "client-b")]:
        errors.append("viewpoints are not client-a/a1 and client-b/b1")
    if match.combatants["a1"].anchor != "spawn_a" or match.combatants["b1"].anchor != "spawn_b":
        errors.append("a human viewpoint left spawn")
    if match.combatants["b2"].preferred_route != "elevated":
        errors.append("the elevated walker did not prefer the span deck")
    for combatant_id, combatant in match.combatants.items():
        if combatant_id == "b2":
            continue
        if combatant.preferred_route != "repair_alley":
            errors.append(f"{combatant_id} left the repair alley preference")
    resident = match.combatants.get("a2")
    if resident is None or resident.controller != "digital_resident":
        errors.append("a2 is not the digital resident")
    port = getattr(match, "resident_port", None)
    if port is None or port.select_calls != 1 or port.decide_calls < 1:
        errors.append("digital_resident did not use select_match and decide")
    return errors


def acceptance_errors(match: SteelTideMatch) -> list[str]:
    errors = match.holder_errors()
    errors.extend(_roster_errors(match))
    errors.extend(_play_errors(match))
    errors.extend(_bridge_errors(match))
    errors.extend(_recompute_errors(match))
    errors.extend(_safety_story_errors(match))
    return errors


def render_slice_logs(match: SteelTideMatch) -> dict[str, str]:
    return render_dual_logs(match, schema=SCHEMA, extra_headers=_extra(match))


def evaluate_slice(match: SteelTideMatch | None = None) -> tuple[dict[str, str], list[str]]:
    match = match or run_m2_bridge_match()
    logs = render_slice_logs(match)
    errors = acceptance_errors(match)
    errors.extend(compare_dual_logs(match, logs, schema=SCHEMA, extra_headers=_extra(match)))
    return logs, errors


def main(argv: list[str] | None = None) -> int:
    args = [] if argv is None else list(argv)
    if args not in ([], ["--check"]):
        print("usage: PYTHONPATH=sim python3 -m steel_tide m2-bridge [--check]")
        return 2
    match = run_m2_bridge_match()
    logs, errors = evaluate_slice(match)
    if args == ["--check"]:
        errors.extend(diff_against_evidence(logs, EVIDENCE_DIR))
    else:
        write_evidence(logs, EVIDENCE_DIR)
    if errors:
        print("NR-M2 bridge FAIL")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("NR-M2 bridge PASS")
    print(
        "roster=6 viewpoints=2 local_bots=3 digital_residents=1 "
        f"score=A:{match.score['A']},B:{match.score['B']} settled={match.settled_kind} "
        f"events={len(match.events)} holder={match.core.holder_id} "
        f"bridge={match.bridge_state}"
    )
    print("rules=contest_core,interrupt_channel,close_range_pass,score_path,path_recompute")
    for end in ("server", "client-a", "client-b"):
        print(f"{end}={(EVIDENCE_DIR / f'{end}.log').as_posix()}")
    if args == ["--check"]:
        print("checked sample logs")
    return 0
