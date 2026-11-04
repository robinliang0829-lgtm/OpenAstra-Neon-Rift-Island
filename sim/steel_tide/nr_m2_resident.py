"""NR-M2 resident slice: one thin digital resident finishes a 3v3 with local bots.

One command:

    PYTHONPATH=sim python3 -m steel_tide m2-resident
    PYTHONPATH=sim python3 -m steel_tide m2-resident --check

`a2` is `controller=digital_resident` and is the only combatant that calls
`select_match` and `decide`. The other movers stay `local_bot`. Two human
viewpoints stay at spawn. Contest, pass, interrupt, first-to-2, and the
4 second bridge warning are the NR-M1-bot paths. This is not a production
resident, and the perceived dict does not carry post-wall coordinates.
"""

from __future__ import annotations

from .bot_policy import _commit, decide
from .config import CONFIG_PATH, SteelTideConfig, load_config
from .dual_log import compare_dual_logs, diff_against_evidence, render_dual_logs, write_evidence
from .match import SteelTideMatch
from .nr_m1_bot import BRIDGE_AT_S, _bridge_errors, _interrupt_errors
from .resident_port import POST_WALL_KEYS, DigitalResidentPort, lobby_view, perceive

SCHEMA = "nr-m2-resident-dual-end-v1"
EVIDENCE_DIR = CONFIG_PATH.parents[1] / "docs" / "evidence" / "nr-m2-resident"

# client_id stays bot-a2 so the same-frame pick order still elects a2.
# controller is the field that distinguishes the resident from local_bot.
ROSTER = (
    ("a1", "client-a", "humanoid_robot", "human", "A", "assault", "same-face"),
    ("a2", "bot-a2", "humanoid_robot", "digital_resident", "A", "support", "same-face"),
    ("a3", "bot-a3", "human", "local_bot", "A", "recon", None),
    ("b1", "client-b", "humanoid_robot", "human", "B", "recon", "same-face"),
    ("b2", "bot-b2", "humanoid_robot", "local_bot", "B", "assault", "same-face"),
    ("b3", "bot-b3", "beast", "local_bot", "B", "support", None),
)


def _extra(match: SteelTideMatch) -> tuple[tuple[str, str], ...]:
    parts = []
    residents = []
    for combatant in sorted(match.combatants.values(), key=lambda item: item.id):
        parts.append(f"{combatant.id}:{combatant.body}:{combatant.faction}:{combatant.controller}")
        if combatant.controller == "digital_resident":
            residents.append(combatant.id)
    return (("identities", ",".join(parts)), ("digital_residents", ",".join(residents)))


def _open(config: SteelTideConfig, port: DigitalResidentPort) -> SteelTideMatch:
    match = SteelTideMatch(config)
    for combatant_id, client_id, body, controller, faction, role, face in ROSTER:
        match.add_combatant(
            combatant_id,
            client_id,
            body,
            controller,
            face_variant=face,
            preferred_route="repair_alley",
        )
        if controller == "digital_resident":
            combatant = match.combatants[combatant_id]
            choice = port.select_match(lobby_view(match, combatant, faction, role))
            if choice["join"] is not True or choice["faction"] != faction or choice["role"] != role:
                raise RuntimeError("resident refused the legal seat")
            match.note_resident_decision(
                combatant_id,
                "select_match",
                "legal_faction",
                choice["faction"],
                role=choice["role"],
                join=True,
            )
            faction = choice["faction"]
            role = choice["role"]
        match.choose_faction(combatant_id, faction)
        match.choose_role(combatant_id, role)
    match.start()
    return match


def _issue(match: SteelTideMatch, port: DigitalResidentPort) -> None:
    for combatant in match.combatants.values():
        if combatant.controller == "local_bot":
            decision = decide(match, combatant)
        elif combatant.controller == "digital_resident":
            decision = port.decide(perceive(match, combatant))
        else:
            continue
        if decision is None:
            continue
        _commit(match, combatant, decision)


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


def run_m2_resident_match(config: SteelTideConfig | None = None) -> SteelTideMatch:
    config = config or load_config()
    port = DigitalResidentPort()
    match = _open(config, port)
    match.resident_port = port
    # NR-03 warning. This does not reimplement the 4 second lead.
    match.schedule_bridge_connect(BRIDGE_AT_S)
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


def _roster_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    humans = [combatant for combatant in match.combatants.values() if combatant.controller == "human"]
    bots = [combatant for combatant in match.combatants.values() if combatant.controller == "local_bot"]
    residents = [combatant for combatant in match.combatants.values() if combatant.controller == "digital_resident"]
    if len(match.combatants) != 6:
        errors.append(f"expected 6 combatants, got {len(match.combatants)}")
    if sorted(combatant.faction for combatant in match.combatants.values()) != ["A", "A", "A", "B", "B", "B"]:
        errors.append("roster is not 3v3")
    if sorted((combatant.id, combatant.client_id) for combatant in humans) != [("a1", "client-a"), ("b1", "client-b")]:
        errors.append("viewpoints are not client-a/a1 and client-b/b1")
    if sorted(combatant.id for combatant in bots) != ["a3", "b2", "b3"]:
        errors.append("expected three local bots beside the resident")
    if sorted(combatant.id for combatant in residents) != ["a2"]:
        errors.append("expected one digital_resident, a2")
    resident = match.combatants.get("a2")
    if resident is None or resident.faction != "A" or resident.role != "support":
        errors.append("resident select_match did not take the legal A support seat")
    elif resident.body == resident.controller or resident.controller == resident.faction:
        errors.append("a2 collapsed controller into body or faction")
    for combatant in match.combatants.values():
        if combatant.body == combatant.controller or combatant.controller == combatant.faction:
            errors.append(f"{combatant.id} collapsed controller into body or faction")
    if match.combatants["a1"].anchor != "spawn_a" or match.combatants["b1"].anchor != "spawn_b":
        errors.append("a human viewpoint left spawn")
    return errors


def _decision_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    bots = match.named("BotDecision")
    residents = match.named("ResidentDecision")
    if not bots:
        errors.append("local bots recorded no decisions")
    if not residents:
        errors.append("digital_resident recorded no decisions")
    for event in bots:
        payload = event.payload
        if payload.get("controller") != "local_bot":
            errors.append(f"bot decision controller is not local_bot: {payload}")
        if payload.get("combatant_id") not in ("a3", "b2", "b3"):
            errors.append(f"bot decision is not from a local bot: {payload}")
        if "reason" not in payload or "target_id" not in payload or "action" not in payload:
            errors.append(f"bot decision is missing action, reason, or target_id: {payload}")
    for event in residents:
        payload = event.payload
        if payload.get("controller") != "digital_resident":
            errors.append(f"resident decision controller is not digital_resident: {payload}")
        if payload.get("combatant_id") != "a2":
            errors.append(f"resident decision is not from a2: {payload}")
        for key in POST_WALL_KEYS:
            if key in payload:
                errors.append(f"resident decision carries post-wall coordinates: {payload}")
    decided_ids = {event.payload.get("combatant_id") for event in bots + residents}
    if "a1" in decided_ids or "b1" in decided_ids:
        errors.append("a human viewpoint recorded a decision")
    selected = [event for event in residents if event.payload.get("action") == "select_match"]
    if len(selected) != 1:
        errors.append("select_match was not a single resident decision")
    else:
        payload = selected[0].payload
        if payload.get("reason") != "legal_faction" or payload.get("target_id") != "A":
            errors.append("select_match did not take faction A")
        if payload.get("role") != "support" or payload.get("join") is not True:
            errors.append("select_match did not join as support")
        started = match.named("MatchStarted")
        if not started or selected[0].t_ms > started[0].t_ms:
            errors.append("select_match was not recorded before the match started")
        if not any(event.payload.get("action") != "select_match" for event in residents):
            errors.append("decide recorded no intent after select_match")
    port = getattr(match, "resident_port", None)
    if port is None or port.select_calls != 1 or port.decide_calls < 1:
        errors.append("digital_resident did not use select_match and decide")
    elif port.hidden_shapes and any(shape != frozenset({"id"}) for shape in port.hidden_shapes):
        errors.append("a covered enemy was fed coordinates")
    elif not port.hidden_shapes:
        errors.append("the resident never observed a covered enemy")
    return errors


def _picks(match: SteelTideMatch, t_ms: int) -> list:
    found = []
    for name in ("BotDecision", "ResidentDecision"):
        for event in match.named(name):
            if event.t_ms != t_ms:
                continue
            if event.payload.get("action") == "pick_core" and event.payload.get("reason") == "contest_core":
                found.append(event)
    return found


def _contest_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    picked = match.named("CorePicked")
    if not picked:
        errors.append("nobody picked the core")
        return errors
    opening = picked[0]
    rejected = [
        event
        for event in match.named("CorePickRejected")
        if event.t_ms == opening.t_ms and event.payload.get("reason") == "already_held"
    ]
    if opening.payload.get("combatant_id") != "a2" or opening.payload.get("anchor") != "center":
        errors.append("the opening contest was not won by a2 at center")
    elif opening.payload.get("client_id") != "bot-a2":
        errors.append("the opening contest winner was not the resident command channel")
    picks = _picks(match, opening.t_ms)
    if len(picks) != 4 or len(rejected) != 3:
        errors.append("the opening contest was not four combatants on one frame")
    elif any(event.payload.get("target_id") != "core" for event in picks):
        errors.append("a contest decision did not name the core")
    else:
        by_id = {event.payload.get("combatant_id"): event for event in picks}
        if set(by_id) != {"a2", "a3", "b2", "b3"}:
            errors.append("the opening contest roster drifted")
        elif by_id["a2"].name != "ResidentDecision" or by_id["a2"].payload.get("controller") != "digital_resident":
            errors.append("the resident did not contest through ResidentDecision")
        elif any(by_id[bot].name != "BotDecision" or by_id[bot].payload.get("controller") != "local_bot" for bot in ("a3", "b2", "b3")):
            errors.append("a local bot contest was logged as the resident")
    if len(picked) != 2:
        errors.append(f"expected the opening contest and the return contest, got {len(picked)} picks")
    else:
        again = picked[1]
        again_rejected = [
            event
            for event in match.named("CorePickRejected")
            if event.t_ms == again.t_ms and event.payload.get("reason") == "already_held"
        ]
        again_picks = _picks(match, again.t_ms)
        if again.payload.get("combatant_id") != "a2" or again.payload.get("anchor") != "center":
            errors.append("the return contest was not won by a2 at center")
        if len(again_rejected) != 1 or again_rejected[0].payload.get("combatant_id") != "b3":
            errors.append("the return contest was not b3 losing to a2")
        if sorted(event.payload.get("combatant_id") for event in again_picks) != ["a2", "b3"]:
            errors.append("the return contest was not a2 and b3")
        else:
            resident_pick = next(event for event in again_picks if event.payload.get("combatant_id") == "a2")
            bot_pick = next(event for event in again_picks if event.payload.get("combatant_id") == "b3")
            if resident_pick.name != "ResidentDecision" or bot_pick.name != "BotDecision":
                errors.append("the return contest did not keep the controllers apart")
    return errors


def _pass_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    passed = match.named("CorePassed")
    if len(passed) != 1 or passed[0].payload.get("from_id") != "a2" or passed[0].payload.get("to_id") != "a3":
        errors.append("the close-range pass was not a2 to a3")
        return errors
    decided = [
        event
        for event in match.named("ResidentDecision")
        if event.payload.get("reason") == "close_range_pass" and event.payload.get("action") == "pass_core"
    ]
    bot_passes = [
        event
        for event in match.named("BotDecision")
        if event.payload.get("action") == "pass_core"
    ]
    if bot_passes:
        errors.append("a local bot recorded the resident pass")
    if len(decided) != 1:
        errors.append("the close-range pass was not a single resident decision")
        return errors
    decision = decided[0]
    if decision.payload.get("target_id") != "a3" or decision.payload.get("combatant_id") != "a2":
        errors.append("the pass decision did not name a2 to a3")
    if decision.payload.get("controller") != "digital_resident":
        errors.append("the pass decision was not marked digital_resident")
    distance = decision.payload.get("distance_m")
    if not isinstance(distance, (int, float)) or isinstance(distance, bool) or distance > match.config.pass_range_m:
        errors.append("the pass decision was not inside pass_range_m")
    if decision.t_ms != passed[0].t_ms:
        errors.append("the pass decision and CorePassed were not the same timestamp")
    if match.named("CorePassRejected"):
        errors.append("the policy attempted a pass the server rejected")
    return errors


def _score_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    scored = match.named("PointScored")
    if len(scored) != 2:
        errors.append(f"expected two score-path points, got {len(scored)}")
        return errors
    if scored[0].payload.get("combatant_id") != "a3" or scored[0].payload.get("score") != {"A": 1, "B": 0}:
        errors.append("the first clean channel was not a3 making it 1-0")
    if scored[1].payload.get("combatant_id") != "a2" or scored[1].payload.get("score") != {"A": 2, "B": 0}:
        errors.append("the second clean channel was not a2 reaching 2-0")
    elif scored[1].payload.get("points") != config.points_to_win or scored[1].payload.get("faction") != "A":
        errors.append("the second point did not reach points_to_win for A")
    paths = []
    for event in match.events:
        if event.payload.get("reason") == "score_path" and event.payload.get("action") == "begin_score":
            paths.append((event.name, event.payload.get("combatant_id"), event.payload.get("controller")))
    expected = [
        ("BotDecision", "a3", "local_bot"),
        ("BotDecision", "a3", "local_bot"),
        ("ResidentDecision", "a2", "digital_resident"),
    ]
    if paths != expected:
        errors.append("the score path was not a3, the restarted a3 channel, then the resident a2")
    elif any(
        event.payload.get("target_id") != "terminal_b"
        for event in match.events
        if event.payload.get("reason") == "score_path" and event.payload.get("action") == "begin_score"
    ):
        errors.append("a score decision did not name terminal_b")
    settled = match.named("MatchSettled")
    if len(settled) != 1 or settled[0].t_ms != scored[1].t_ms:
        errors.append("first-to-2 did not settle on the second point")
    elif settled[0].payload.get("kind") != "points" or settled[0].payload.get("winner") != "A":
        errors.append("regulation cap should settle as points winner A")
    elif settled[0].payload.get("score") != {"A": 2, "B": 0}:
        errors.append("settlement score drifted")
    if match.named("OvertimeStarted") or match.named("MatchClockExpired"):
        errors.append("regulation first-to-2 opened overtime or waited for the clock")
    if match.phase != "settled" or match.settled_kind != "points" or match.score != {"A": 2, "B": 0}:
        errors.append(f"slice ended phase={match.phase} kind={match.settled_kind} score={match.score}")
    if match.t_ms >= config.match_ms:
        errors.append("the policy did not finish inside regulation")
    if match.core.holder_id is not None or match.core.anchor != "center":
        errors.append("the scoring core did not return to center")
    if len(match.named("CoreReturnedToCenter")) != 2:
        errors.append("each clean channel should return the core once")
    interrupted = match.named("ScoreChannelInterrupted")
    if not interrupted or scored[0].t_ms <= interrupted[0].t_ms:
        errors.append("the score path did not come after the interrupt")
    return errors


def acceptance_errors(match: SteelTideMatch) -> list[str]:
    errors = match.holder_errors()
    errors.extend(_roster_errors(match))
    errors.extend(_decision_errors(match))
    errors.extend(_contest_errors(match))
    errors.extend(_pass_errors(match))
    errors.extend(_interrupt_errors(match))
    errors.extend(_score_errors(match))
    errors.extend(_bridge_errors(match))
    return errors


def render_slice_logs(match: SteelTideMatch) -> dict[str, str]:
    return render_dual_logs(match, schema=SCHEMA, extra_headers=_extra(match))


def evaluate_slice(match: SteelTideMatch | None = None) -> tuple[dict[str, str], list[str]]:
    match = match or run_m2_resident_match()
    logs = render_slice_logs(match)
    errors = acceptance_errors(match)
    errors.extend(compare_dual_logs(match, logs, schema=SCHEMA, extra_headers=_extra(match)))
    return logs, errors


def main(argv: list[str] | None = None) -> int:
    args = [] if argv is None else list(argv)
    if args not in ([], ["--check"]):
        print("usage: PYTHONPATH=sim python3 -m steel_tide m2-resident [--check]")
        return 2
    match = run_m2_resident_match()
    logs, errors = evaluate_slice(match)
    if args == ["--check"]:
        errors.extend(diff_against_evidence(logs, EVIDENCE_DIR))
    else:
        write_evidence(logs, EVIDENCE_DIR)
    if errors:
        print("NR-M2 resident FAIL")
        for error in errors:
            print(f"  - {error}")
        return 1
    port = match.resident_port
    print("NR-M2 resident PASS")
    print(
        "roster=6 viewpoints=2 local_bots=3 digital_residents=1 "
        f"score=A:{match.score['A']},B:{match.score['B']} settled={match.settled_kind} "
        f"events={len(match.events)} holder={match.core.holder_id} "
        f"select_match={port.select_calls} decide={port.decide_calls}"
    )
    print("rules=contest_core,interrupt_channel,close_range_pass,score_path")
    print("controller=digital_resident")
    for end in ("server", "client-a", "client-b"):
        print(f"{end}={(EVIDENCE_DIR / f'{end}.log').as_posix()}")
    if args == ["--check"]:
        print("checked sample logs")
    return 0
