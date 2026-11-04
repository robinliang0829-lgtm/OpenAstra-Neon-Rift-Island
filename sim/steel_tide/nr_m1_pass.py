"""NR-M1 pass slice: near pass, dash lock, channel interrupts, regulation points.

One command:

    PYTHONPATH=sim python3 -m steel_tide m1-pass
    PYTHONPATH=sim python3 -m steel_tide m1-pass --check

The match object is the only scorer. This slice does not add a second
warning clock: the 4 second bridge lead is `schedule_bridge_connect`.
`place_for_test` is not an event.
"""

from __future__ import annotations

from .config import CONFIG_PATH, SteelTideConfig, load_config
from .dual_log import compare_dual_logs, diff_against_evidence, render_dual_logs, write_evidence
from .match import SERVER_CLIENT, SteelTideMatch

SCHEMA = "nr-m1-pass-dual-end-v1"
EVIDENCE_DIR = CONFIG_PATH.parents[1] / "docs" / "evidence" / "nr-m1-pass"

PICK_S = 1.0
DASH_HELD_S = 1.5
PASS_ENEMY_S = 2.0
PASS_FAR_S = 2.4
PASS_OK_S = 2.8
DASH_FREE_S = 3.2
DOWN_S = 4.0
REPICK_S = 4.5
BRIDGE_AT_S = 12.0
HIT_CHANNEL_S = 13.0
HIT_INTERRUPT_S = 14.0
LEAVE_CHANNEL_S = 14.5
LEAVE_INTERRUPT_S = 15.5
SCORE1_S = 16.0
PICK2_S = 19.5
SCORE2_S = 20.0

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
            preferred_route="elevated",
        )
        match.choose_faction(combatant_id, faction)
        match.choose_role(combatant_id, role)
    match.start()
    return match


def _score_terminal(match: SteelTideMatch, combatant_id: str) -> str:
    faction = match.combatants[combatant_id].faction or ""
    return match.config.score_terminal[faction]


def run_m1_pass_match(config: SteelTideConfig | None = None) -> SteelTideMatch:
    config = config or load_config()
    match = _open(config)
    # NR-03 warning. This does not reimplement the 4 second lead.
    match.schedule_bridge_connect(BRIDGE_AT_S)

    match.place_for_test("a1", "center")
    match.enqueue("client-a", "pick_core", PICK_S, combatant_id="a1")
    match.advance_to(PICK_S)

    match.place_for_test("a1", "terminal_a")
    match.enqueue(
        "client-a",
        "use_ability",
        DASH_HELD_S,
        combatant_id="a1",
        ability="dash",
        dest="bridgehead_a",
    )
    match.advance_to(DASH_HELD_S)

    match.place_for_test("b1", "terminal_a")
    match.enqueue("client-a", "pass_core", PASS_ENEMY_S, from_id="a1", to_id="b1")
    match.advance_to(PASS_ENEMY_S)

    origin = config.anchors["terminal_a"]
    match.place_for_test("a2", "terminal_a", pos=(origin[0], origin[1] + config.pass_range_m + 1.0))
    match.enqueue("client-a", "pass_core", PASS_FAR_S, from_id="a1", to_id="a2")
    match.advance_to(PASS_FAR_S)

    match.place_for_test("a2", "terminal_a")
    match.enqueue("client-a", "pass_core", PASS_OK_S, from_id="a1", to_id="a2")
    match.advance_to(PASS_OK_S)

    match.enqueue(
        "client-a",
        "use_ability",
        DASH_FREE_S,
        combatant_id="a1",
        ability="dash",
        dest="bridgehead_a",
    )
    match.advance_to(DASH_FREE_S)

    match.enqueue(SERVER_CLIENT, "hit", DOWN_S, target_id="a2", down=True)
    match.advance_to(DOWN_S)
    match.place_for_test("b2", "terminal_a")
    match.enqueue("bot-b2", "pick_core", REPICK_S, combatant_id="b2")
    match.advance_to(BRIDGE_AT_S)

    terminal = _score_terminal(match, "b2")
    match.place_for_test("b2", terminal)
    match.enqueue("bot-b2", "begin_score", HIT_CHANNEL_S, combatant_id="b2")
    match.enqueue(SERVER_CLIENT, "hit", HIT_INTERRUPT_S, target_id="b2", down=False)
    match.advance_to(HIT_INTERRUPT_S)

    match.enqueue("bot-b2", "begin_score", LEAVE_CHANNEL_S, combatant_id="b2")
    match.enqueue(SERVER_CLIENT, "leave_terminal", LEAVE_INTERRUPT_S, combatant_id="b2")
    match.advance_to(LEAVE_INTERRUPT_S)

    match.enqueue("bot-b2", "begin_score", SCORE1_S, combatant_id="b2")
    match.advance_to(SCORE1_S + config.score_channel_seconds)

    match.place_for_test("b2", "center")
    match.enqueue("bot-b2", "pick_core", PICK2_S, combatant_id="b2")
    match.advance_to(PICK2_S)
    match.place_for_test("b2", terminal)
    match.enqueue("bot-b2", "begin_score", SCORE2_S, combatant_id="b2")
    match.advance_to(SCORE2_S + config.score_channel_seconds)
    return match


def _at(match: SteelTideMatch, name: str, t_ms: int, **payload) -> list:
    found = []
    for event in match.named(name):
        if event.t_ms != t_ms:
            continue
        if all(event.payload.get(key) == value for key, value in payload.items()):
            found.append(event)
    return found


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
        errors.append("a local bot was labeled as a production resident")
    if match.combatants["a1"].role != "assault" or match.combatants["b2"].role != "assault":
        errors.append("the pass slice needs an assault on each side")
    return errors


def _pass_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    pick_ms = config.seconds_to_ms(PICK_S)
    enemy_ms = config.seconds_to_ms(PASS_ENEMY_S)
    far_ms = config.seconds_to_ms(PASS_FAR_S)
    ok_ms = config.seconds_to_ms(PASS_OK_S)
    picked = _at(match, "CorePicked", pick_ms, combatant_id="a1", anchor="center")
    if len(picked) != 1:
        errors.append("a1 did not pick the core at center")
    enemy = _at(match, "CorePassRejected", enemy_ms, from_id="a1", to_id="b1", reason="wrong_faction")
    if len(enemy) != 1:
        errors.append("a pass to the other team was not rejected")
    far = _at(match, "CorePassRejected", far_ms, from_id="a1", to_id="a2", reason="out_of_range")
    if len(far) != 1:
        errors.append("a pass beyond pass_range_m was not rejected")
    if config.pass_range_m <= 0:
        errors.append("pass_range_m is not a near-range limit")
    passed = _at(match, "CorePassed", ok_ms, from_id="a1", to_id="a2")
    if len(passed) != 1:
        errors.append("the in-range teammate pass did not land")
    elif not (pick_ms < enemy_ms < far_ms < ok_ms):
        errors.append("pass checks were not ordered reject-then-success")
    if len(match.named("CorePassed")) != 1 or len(match.named("CorePassRejected")) != 2:
        errors.append("pass events drifted from one success and two rejects")
    return errors


def _dash_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    held_ms = config.seconds_to_ms(DASH_HELD_S)
    free_ms = config.seconds_to_ms(DASH_FREE_S)
    blocked = _at(
        match,
        "AbilityRejected",
        held_ms,
        ability="dash",
        combatant_id="a1",
        reason="holding_core",
        dest="bridgehead_a",
    )
    if len(blocked) != 1:
        errors.append("holding the core did not reject the assault dash")
    freed = _at(match, "AbilityUsed", free_ms, ability="dash", combatant_id="a1")
    if len(freed) != 1:
        errors.append("the assault could not dash after releasing the core")
    elif freed[0].payload.get("from") != "terminal_a" or freed[0].payload.get("dest") != "bridgehead_a":
        errors.append("the dash after the pass did not stay the short elevated hop")
    else:
        cooldown_ms = config.seconds_to_ms(config.role_abilities["assault"]["cooldown_seconds"])
        if freed[0].payload.get("ready_ms") != free_ms + cooldown_ms:
            errors.append("the rejected dash consumed the assault cooldown")
    if len(match.named("AbilityUsed")) != 1:
        errors.append("a dash landed while the core was still held")
    if match.combatants["a1"].anchor != "bridgehead_a":
        errors.append("the freed dash did not move the assault")
    return errors


def _drop_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    down_ms = config.seconds_to_ms(DOWN_S)
    repick_ms = config.seconds_to_ms(REPICK_S)
    respawn_ms = down_ms + config.down_ms
    drops = [event for event in match.named("CoreDropped") if event.payload.get("reason") == "downed"]
    if len(drops) != 1 or drops[0].t_ms != down_ms or drops[0].payload.get("combatant_id") != "a2":
        errors.append("the downed carrier did not drop the core")
    elif drops[0].payload.get("anchor") != "terminal_a":
        errors.append("the dropped core did not stay at the down site")
    else:
        down_index = next(
            index
            for index, event in enumerate(match.events)
            if event.name == "ActorDowned" and event.payload.get("combatant_id") == "a2"
        )
        if match.events.index(drops[0]) > down_index:
            errors.append("ActorDowned was emitted before the core drop")
    if any(event.name == "PointScored" and event.t_ms == down_ms for event in match.events):
        errors.append("downing the carrier scored")
    again = _at(match, "CorePicked", repick_ms, combatant_id="b2", anchor="terminal_a")
    if len(again) != 1 or again[0].t_ms <= down_ms:
        errors.append("the grounded core was not picked up again")
    respawned = _at(match, "ActorRespawned", respawn_ms, combatant_id="a2", anchor="spawn_a")
    if len(respawned) != 1:
        errors.append("the downed carrier did not respawn at the faction spawn")
    elif respawned[0].payload.get("protection_until_ms") != respawn_ms + config.spawn_protection_ms:
        errors.append("respawn did not start spawn protection")
    if len(match.named("CoreDropped")) != 1:
        errors.append("a later hit or the respawn dropped another core")
    return errors


def _channel_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    hit_ms = config.seconds_to_ms(HIT_INTERRUPT_S)
    leave_ms = config.seconds_to_ms(LEAVE_INTERRUPT_S)
    score1_ms = config.seconds_to_ms(SCORE1_S + config.score_channel_seconds)
    hit = _at(match, "ScoreChannelInterrupted", hit_ms, combatant_id="b2", reason="hit")
    left = _at(match, "ScoreChannelInterrupted", leave_ms, combatant_id="b2", reason="left_terminal")
    if len(hit) != 1:
        errors.append("the channel was not interrupted by the hit")
    elif hit[0].payload.get("elapsed_ms") != config.seconds_to_ms(HIT_INTERRUPT_S - HIT_CHANNEL_S):
        errors.append("the hit interrupt did not keep the partial channel")
    if len(left) != 1:
        errors.append("the channel was not interrupted by leaving the terminal")
    elif left[0].payload.get("elapsed_ms") != config.seconds_to_ms(LEAVE_INTERRUPT_S - LEAVE_CHANNEL_S):
        errors.append("the leave interrupt did not keep the partial channel")
    reasons = [event.payload.get("reason") for event in match.named("ScoreChannelInterrupted")]
    if reasons != ["hit", "left_terminal"]:
        errors.append(f"interrupt reasons drifted: {reasons}")
    for stamp in (hit_ms, leave_ms):
        if any(event.name == "PointScored" and event.t_ms == stamp for event in match.events):
            errors.append(f"an interrupted channel scored at {stamp}")
    if any(event.name == "PointScored" and event.t_ms <= leave_ms for event in match.events):
        errors.append("a point landed before a full channel")
    scored = _at(match, "PointScored", score1_ms, combatant_id="b2", faction="B")
    if len(scored) != 1 or scored[0].payload.get("score") != {"A": 0, "B": 1}:
        errors.append("the full 3s channel did not score once")
    elif score1_ms - config.seconds_to_ms(SCORE1_S) != config.score_channel_ms:
        errors.append("the clean channel was not score_channel_seconds")
    returned = _at(match, "CoreReturnedToCenter", score1_ms, anchor="center", scoring_faction="B")
    if len(returned) != 1:
        errors.append("the clean channel did not return the core to center")
    if _at(match, "MatchSettled", score1_ms):
        errors.append("the first regulation point settled the match")
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


def _points_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    score2_ms = config.seconds_to_ms(SCORE2_S + config.score_channel_seconds)
    scored = match.named("PointScored")
    if len(scored) != 2:
        errors.append(f"expected two regulation points, got {len(scored)}")
    elif scored[1].t_ms != score2_ms or scored[1].payload.get("score") != {"A": 0, "B": 2}:
        errors.append(f"the second point drifted: {scored[1].to_dict()}")
    elif scored[1].payload.get("points") != config.points_to_win or scored[1].payload.get("faction") != "B":
        errors.append("the second point did not reach points_to_win for B")
    returned = [event for event in match.named("CoreReturnedToCenter") if event.t_ms == score2_ms]
    if len(returned) != 1:
        errors.append("the winning channel did not return the core")
    settled = match.named("MatchSettled")
    if len(settled) != 1 or settled[0].t_ms != score2_ms:
        errors.append("first-to-2 did not settle on the scoring timestamp")
    elif settled[0].payload.get("kind") != "points" or settled[0].payload.get("winner") != "B":
        errors.append(f"regulation cap should settle as points winner B: {settled[0].payload if settled else None}")
    elif settled[0].payload.get("score") != {"A": 0, "B": 2}:
        errors.append("settlement score drifted")
    if match.named("OvertimeStarted") or match.named("MatchClockExpired"):
        errors.append("regulation first-to-2 opened overtime or waited for the clock")
    if match.phase != "settled" or match.settled_kind != "points" or match.score != {"A": 0, "B": 2}:
        errors.append(f"slice ended phase={match.phase} kind={match.settled_kind} score={match.score}")
    if match.t_ms != score2_ms or match.t_ms >= config.match_ms:
        errors.append(f"match kept running to {match.t_ms} after regulation points")
    if match.core.holder_id is not None or match.core.anchor != "center":
        errors.append("the scoring core did not return to center")
    if len(match.named("CoreReturnedToCenter")) != 2:
        errors.append("each clean channel should return the core once")
    return errors


def acceptance_errors(match: SteelTideMatch) -> list[str]:
    errors = match.holder_errors()
    errors.extend(_roster_errors(match))
    errors.extend(_pass_errors(match))
    errors.extend(_dash_errors(match))
    errors.extend(_drop_errors(match))
    errors.extend(_channel_errors(match))
    errors.extend(_bridge_errors(match))
    errors.extend(_points_errors(match))
    return errors


def render_slice_logs(match: SteelTideMatch) -> dict[str, str]:
    return render_dual_logs(match, schema=SCHEMA, extra_headers=_extra(match))


def evaluate_slice(match: SteelTideMatch | None = None) -> tuple[dict[str, str], list[str]]:
    match = match or run_m1_pass_match()
    logs = render_slice_logs(match)
    errors = acceptance_errors(match)
    errors.extend(compare_dual_logs(match, logs, schema=SCHEMA, extra_headers=_extra(match)))
    return logs, errors


def main(argv: list[str] | None = None) -> int:
    args = [] if argv is None else list(argv)
    if args not in ([], ["--check"]):
        print("usage: PYTHONPATH=sim python3 -m steel_tide m1-pass [--check]")
        return 2
    match = run_m1_pass_match()
    logs, errors = evaluate_slice(match)
    if args == ["--check"]:
        errors.extend(diff_against_evidence(logs, EVIDENCE_DIR))
    else:
        write_evidence(logs, EVIDENCE_DIR)
    if errors:
        print("NR-M1 pass FAIL")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("NR-M1 pass PASS")
    print(
        "roster=6 viewpoints=2 local_bots=4 "
        f"score=A:{match.score['A']},B:{match.score['B']} settled={match.settled_kind} "
        f"events={len(match.events)} holder={match.core.holder_id}"
    )
    print("rules=pass,dash_lock,interrupt_hit,interrupt_leave,regulation_points")
    for end in ("server", "client-a", "client-b"):
        print(f"{end}={(EVIDENCE_DIR / f'{end}.log').as_posix()}")
    if args == ["--check"]:
        print("checked sample logs")
    return 0
