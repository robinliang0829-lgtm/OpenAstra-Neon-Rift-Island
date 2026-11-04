"""NR-M1 bot slice: a local policy finishes one 3v3.

One command:

    PYTHONPATH=sim python3 -m steel_tide m1-bot
    PYTHONPATH=sim python3 -m steel_tide m1-bot --check

Two human viewpoints and four local bots. The policy walks, contests the
core, passes in range, interrupts one channel, and scores to `points_to_win`.
It does not construct a digital resident. The 4 second bridge lead is
`schedule_bridge_connect`.
"""

from __future__ import annotations

from .bot_policy import INTERRUPT_AFTER_S, run_local_bots
from .config import CONFIG_PATH, SteelTideConfig, load_config
from .dual_log import compare_dual_logs, diff_against_evidence, render_dual_logs, write_evidence
from .match import SERVER_CLIENT, SteelTideMatch

SCHEMA = "nr-m1-bot-dual-end-v1"
EVIDENCE_DIR = CONFIG_PATH.parents[1] / "docs" / "evidence" / "nr-m1-bot"
BRIDGE_AT_S = 12.0

ROSTER = (
    ("a1", "client-a", "humanoid_robot", "human", "A", "assault", "same-face"),
    ("a2", "bot-a2", "humanoid_robot", "local_bot", "A", "support", "same-face"),
    ("a3", "bot-a3", "human", "local_bot", "A", "recon", None),
    ("b1", "client-b", "humanoid_robot", "human", "B", "recon", "same-face"),
    ("b2", "bot-b2", "humanoid_robot", "local_bot", "B", "assault", "same-face"),
    ("b3", "bot-b3", "beast", "local_bot", "B", "support", None),
)


def _extra(match: SteelTideMatch) -> tuple[tuple[str, str], ...]:
    parts = []
    for combatant in sorted(match.combatants.values(), key=lambda item: item.id):
        parts.append(f"{combatant.id}:{combatant.body}:{combatant.faction}:{combatant.controller}")
    return (("identities", ",".join(parts)),)


def _open(config: SteelTideConfig) -> SteelTideMatch:
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
        match.choose_faction(combatant_id, faction)
        match.choose_role(combatant_id, role)
    match.start()
    return match


def run_m1_bot_match(config: SteelTideConfig | None = None) -> SteelTideMatch:
    config = config or load_config()
    match = _open(config)
    # NR-03 warning. This does not reimplement the 4 second lead.
    match.schedule_bridge_connect(BRIDGE_AT_S)
    return run_local_bots(match)


def _roster_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    humans = [combatant for combatant in match.combatants.values() if combatant.controller == "human"]
    bots = [combatant for combatant in match.combatants.values() if combatant.controller == "local_bot"]
    if len(match.combatants) != 6:
        errors.append(f"expected 6 combatants, got {len(match.combatants)}")
    if sorted(combatant.faction for combatant in match.combatants.values()) != ["A", "A", "A", "B", "B", "B"]:
        errors.append("roster is not 3v3")
    if sorted((combatant.id, combatant.client_id) for combatant in humans) != [("a1", "client-a"), ("b1", "client-b")]:
        errors.append("viewpoints are not client-a/a1 and client-b/b1")
    if sorted(combatant.id for combatant in bots) != ["a2", "a3", "b2", "b3"]:
        errors.append("expected four local bots")
    if any(combatant.controller == "digital_resident" for combatant in match.combatants.values()):
        errors.append("a combatant was instantiated as a production resident")
    for combatant in match.combatants.values():
        if combatant.body == combatant.controller or combatant.controller == combatant.faction:
            errors.append(f"{combatant.id} collapsed controller into body or faction")
    if match.combatants["a1"].anchor != "spawn_a" or match.combatants["b1"].anchor != "spawn_b":
        errors.append("a human viewpoint left spawn; the policy only drives local_bot")
    return errors


def _decision_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    decisions = match.named("BotDecision")
    if not decisions:
        errors.append("local bots recorded no decisions")
        return errors
    for event in decisions:
        payload = event.payload
        if payload.get("controller") != "local_bot":
            errors.append(f"decision controller is not local_bot: {payload}")
        if payload.get("combatant_id") not in ("a2", "a3", "b2", "b3"):
            errors.append(f"decision is not from a local bot: {payload}")
        if "reason" not in payload or "target_id" not in payload or "action" not in payload:
            errors.append(f"decision is missing action, reason, or target_id: {payload}")
    humans = {event.payload.get("combatant_id") for event in decisions}
    if "a1" in humans or "b1" in humans:
        errors.append("a human viewpoint recorded a bot decision")
    return errors


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
    picks = [
        event
        for event in match.named("BotDecision")
        if event.t_ms == opening.t_ms
        and event.payload.get("action") == "pick_core"
        and event.payload.get("reason") == "contest_core"
    ]
    if len(picks) != 4 or len(rejected) != 3:
        errors.append("the opening contest was not four local bots on one frame")
    elif any(event.payload.get("target_id") != "core" for event in picks):
        errors.append("a contest decision did not name the core")
    if len(picked) != 2:
        errors.append(f"expected the opening contest and the return contest, got {len(picked)} picks")
    else:
        again = picked[1]
        again_rejected = [
            event
            for event in match.named("CorePickRejected")
            if event.t_ms == again.t_ms and event.payload.get("reason") == "already_held"
        ]
        again_picks = [
            event
            for event in match.named("BotDecision")
            if event.t_ms == again.t_ms
            and event.payload.get("action") == "pick_core"
            and event.payload.get("reason") == "contest_core"
        ]
        if again.payload.get("combatant_id") != "a2" or again.payload.get("anchor") != "center":
            errors.append("the return contest was not won by a2 at center")
        if len(again_rejected) != 1 or again_rejected[0].payload.get("combatant_id") != "b3":
            errors.append("the return contest was not b3 losing to a2")
        if sorted(event.payload.get("combatant_id") for event in again_picks) != ["a2", "b3"]:
            errors.append("the return contest was not a2 and b3")
    return errors


def _pass_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    passed = match.named("CorePassed")
    if len(passed) != 1 or passed[0].payload.get("from_id") != "a2" or passed[0].payload.get("to_id") != "a3":
        errors.append("the close-range pass was not a2 to a3")
        return errors
    decided = [
        event
        for event in match.named("BotDecision")
        if event.payload.get("reason") == "close_range_pass" and event.payload.get("action") == "pass_core"
    ]
    if len(decided) != 1:
        errors.append("the close-range pass was not a single audited decision")
        return errors
    decision = decided[0]
    if decision.payload.get("target_id") != "a3" or decision.payload.get("combatant_id") != "a2":
        errors.append("the pass decision did not name a2 to a3")
    distance = decision.payload.get("distance_m")
    if not isinstance(distance, (int, float)) or distance > match.config.pass_range_m:
        errors.append("the pass decision was not inside pass_range_m")
    if decision.t_ms != passed[0].t_ms:
        errors.append("the pass decision and CorePassed were not the same timestamp")
    if match.named("CorePassRejected"):
        errors.append("the policy attempted a pass the server rejected")
    return errors


def _interrupt_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    interrupted = match.named("ScoreChannelInterrupted")
    if len(interrupted) != 1:
        errors.append(f"expected one channel interrupt, got {len(interrupted)}")
        return errors
    event = interrupted[0]
    if event.payload.get("reason") != "hit" or event.payload.get("combatant_id") != "a3":
        errors.append(f"interrupt was not a hit on a3: {event.payload}")
    elif event.payload.get("elapsed_ms") != match.config.seconds_to_ms(INTERRUPT_AFTER_S):
        errors.append("the hit did not land one second into the channel")
    if any(item.name == "PointScored" and item.t_ms == event.t_ms for item in match.events):
        errors.append("the interrupted channel scored")
    if any(item.name == "PointScored" and item.t_ms <= event.t_ms for item in match.events):
        errors.append("a point landed at or before the interrupt")
    decided = [
        item
        for item in match.named("BotDecision")
        if item.payload.get("action") == "interrupt_channel" and item.payload.get("reason") == "contest_channel"
    ]
    if len(decided) != 1:
        errors.append("the interrupt was not a single audited bot decision")
    elif decided[0].payload.get("combatant_id") != "b2" or decided[0].payload.get("target_id") != "a3":
        errors.append("b2 did not decide to contest a3's channel")
    elif decided[0].t_ms > event.t_ms:
        errors.append("the interrupt decision was recorded after the hit")
    hits = [cmd for cmd in match.inbox if cmd.kind == "hit"]
    if len(hits) != 1 or hits[0].client_id != SERVER_CLIENT or hits[0].payload.get("down") is not False:
        errors.append("the channel hit was not one server contact with down false")
    if match.named("ActorDowned") or match.named("CoreDropped"):
        errors.append("the interrupt downed the carrier or dropped the core")
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
    paths = [
        event
        for event in match.named("BotDecision")
        if event.payload.get("reason") == "score_path" and event.payload.get("action") == "begin_score"
    ]
    if [event.payload.get("combatant_id") for event in paths] != ["a3", "a3", "a2"]:
        errors.append("the score path was not a3, the restarted a3 channel, then a2")
    elif any(event.payload.get("target_id") != "terminal_b" for event in paths):
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


def _bridge_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    start_ms = config.seconds_to_ms(BRIDGE_AT_S) - config.bridge_warning_ms
    connect_ms = config.seconds_to_ms(BRIDGE_AT_S)
    started = match.named("BridgeWarningStarted")
    completed = match.named("BridgeWarningCompleted")
    connected = [event for event in match.named("BridgeStateChanged") if event.payload.get("state") == "connected"]
    if len(started) != 1 or started[0].t_ms != start_ms or started[0].payload.get("lead_ms") != config.bridge_warning_ms:
        errors.append("bridge warning did not reuse the configured 4 second lead")
    elif started[0].payload.get("readable_without_reflection") is not True:
        errors.append("bridge warning dropped readable_without_reflection")
    if len(completed) != 1 or completed[0].t_ms != connect_ms:
        errors.append("bridge warning did not complete on the connect timestamp")
    elif completed[0].payload.get("elapsed_ms") != config.bridge_warning_ms:
        errors.append("bridge warning elapsed was not the configured lead")
    if len(connected) != 1 or connected[0].t_ms != connect_ms:
        errors.append("bridge connect was not aligned with BridgeWarningCompleted")
    advanced = match.named("BridgeLightStripAdvanced")
    expected = config.light_strip_lamps() - 2
    if len(advanced) != expected:
        errors.append(f"light strip count {len(advanced)} != scheduler {expected}")
    elif any(not start_ms < event.t_ms < connect_ms for event in advanced):
        errors.append("a light strip step fell outside the warning window")
    if any(event.name == "PointScored" and event.t_ms <= connect_ms for event in match.events):
        errors.append("the bridge warning scored")
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
    match = match or run_m1_bot_match()
    logs = render_slice_logs(match)
    errors = acceptance_errors(match)
    errors.extend(compare_dual_logs(match, logs, schema=SCHEMA, extra_headers=_extra(match)))
    return logs, errors


def main(argv: list[str] | None = None) -> int:
    args = [] if argv is None else list(argv)
    if args not in ([], ["--check"]):
        print("usage: PYTHONPATH=sim python3 -m steel_tide m1-bot [--check]")
        return 2
    match = run_m1_bot_match()
    logs, errors = evaluate_slice(match)
    if args == ["--check"]:
        errors.extend(diff_against_evidence(logs, EVIDENCE_DIR))
    else:
        write_evidence(logs, EVIDENCE_DIR)
    if errors:
        print("NR-M1 bot FAIL")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("NR-M1 bot PASS")
    print(
        "roster=6 viewpoints=2 local_bots=4 "
        f"score=A:{match.score['A']},B:{match.score['B']} settled={match.settled_kind} "
        f"events={len(match.events)} holder={match.core.holder_id}"
    )
    print("rules=contest_core,interrupt_channel,close_range_pass,score_path")
    for end in ("server", "client-a", "client-b"):
        print(f"{end}={(EVIDENCE_DIR / f'{end}.log').as_posix()}")
    if args == ["--check"]:
        print("checked sample logs")
    return 0
