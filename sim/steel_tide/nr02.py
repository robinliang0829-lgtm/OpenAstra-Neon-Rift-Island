"""NR-02 headless slice: 3v3, two human viewpoints, four local bots.

One command:

    PYTHONPATH=sim python3 -m steel_tide nr02
    PYTHONPATH=sim python3 -m steel_tide nr02 --check

The match object in `sim/steel_tide/match.py` is the only scorer. `place_for_test`
stands in for "this body is inside the volume" when UE is not installed. It is
not an event. Volume walks on the real greybox will not share these timestamps.
"""

from __future__ import annotations

from .dual_log import (
    compare_dual_logs,
    diff_against_evidence,
    evidence_paths,
    render_dual_logs,
    replay_holder,
    replay_score,
    write_evidence,
)
from .match import SERVER_CLIENT, SteelTideMatch
from .config import load_config

CONTEST_S = 1.0
CHANNEL_S = 2.0
HIT_S = 3.5
MOVE_S = 2.25
GROUND_PICK_S = 4.0
GROUND_SCORE_S = 4.1
MARK_S = 7.6
UNPICKABLE_S = 10.0
POST_RESET_DELAY_S = 0.1

ROSTER = (
    ("a1", "client-a", "humanoid_robot", "human", "A", "assault", "same-face"),
    ("a2", "bot-a2", "humanoid_robot", "local_bot", "A", "support", "same-face"),
    ("a3", "bot-a3", "human", "local_bot", "A", "recon", None),
    ("b1", "client-b", "humanoid_robot", "human", "B", "assault", "same-face"),
    ("b2", "bot-b2", "humanoid_robot", "local_bot", "B", "support", "same-face"),
    ("b3", "bot-b3", "beast", "local_bot", "B", "recon", None),
)


def run_nr02_match(config=None) -> SteelTideMatch:
    match = SteelTideMatch(config or load_config())
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
    for combatant_id, client_id, *_rest in ROSTER:
        match.enqueue(client_id, "set_route", 0.5, combatant_id=combatant_id, route="repair_alley")
        match.enqueue(client_id, "pick_core", CONTEST_S, combatant_id=combatant_id)
    # Two human clients occupy the core. Bots are still at their spawns.
    match.place_for_test("a1", "center")
    match.place_for_test("b1", "center")
    match.advance_to(CONTEST_S)
    match.place_for_test("a1", "terminal_b")
    match.enqueue("client-a", "begin_score", CHANNEL_S, combatant_id="a1")
    match.enqueue(SERVER_CLIENT, "hit", HIT_S, target_id="a1", down=True)
    for combatant_id, client_id, dest in (
        ("a3", "bot-a3", "alley_a"),
        ("b2", "bot-b2", "alley_b"),
        ("b3", "bot-b3", "alley_b"),
    ):
        match.enqueue(
            client_id,
            "request_move",
            MOVE_S,
            combatant_id=combatant_id,
            dest=dest,
            route="repair_alley",
        )
    match.advance_to(MOVE_S)
    match.place_for_test("a2", "terminal_b")
    match.enqueue("bot-a2", "pick_core", GROUND_PICK_S, combatant_id="a2")
    # begin_score is applied before picks on the same timestamp, so it waits one step.
    match.enqueue("bot-a2", "begin_score", GROUND_SCORE_S, combatant_id="a2")
    match.advance_to(GROUND_SCORE_S + match.config.score_channel_seconds)
    match.enqueue(SERVER_CLIENT, "mark_core_overboard", MARK_S)
    match.advance_to(MARK_S)
    match.place_for_test("b1", "sea")
    match.enqueue("client-b", "pick_core", UNPICKABLE_S, combatant_id="b1")
    reset_s = MARK_S + match.config.core_reset_timeout_seconds
    match.advance_to(reset_s)
    match.place_for_test("a3", "center")
    match.enqueue("bot-a3", "pick_core", reset_s + POST_RESET_DELAY_S, combatant_id="a3")
    match.advance_to(reset_s + POST_RESET_DELAY_S)
    return match


def acceptance_errors(match: SteelTideMatch) -> list[str]:
    errors = match.holder_errors()
    config = match.config
    contest_ms = config.seconds_to_ms(CONTEST_S)
    hit_ms = config.seconds_to_ms(HIT_S)
    score_ms = config.seconds_to_ms(GROUND_SCORE_S + config.score_channel_seconds)
    mark_ms = config.seconds_to_ms(MARK_S)
    reset_ms = mark_ms + config.core_reset_timeout_ms
    post_ms = config.seconds_to_ms(MARK_S + config.core_reset_timeout_seconds + POST_RESET_DELAY_S)
    humans = [combatant for combatant in match.combatants.values() if combatant.controller == "human"]
    bots = [combatant for combatant in match.combatants.values() if combatant.controller == "local_bot"]
    if len(match.combatants) != 6:
        errors.append(f"expected 6 combatants, got {len(match.combatants)}")
    if config.team_size != 3:
        errors.append(f"greybox team_size is {config.team_size}, NR-02 slice is 3v3")
    if sorted(combatant.faction for combatant in match.combatants.values()) != ["A", "A", "A", "B", "B", "B"]:
        errors.append("roster is not 3v3")
    if sorted((combatant.id, combatant.client_id) for combatant in humans) != [("a1", "client-a"), ("b1", "client-b")]:
        errors.append(f"viewpoints drifted: {humans}")
    if sorted(combatant.id for combatant in bots) != ["a2", "a3", "b2", "b3"]:
        errors.append("expected four local bots a2,a3,b2,b3")
    if any(combatant.controller == "digital_resident" for combatant in match.combatants.values()):
        errors.append("a local bot was labeled as a production resident")
    for combatant_id in ("a1", "a2", "b1", "b2"):
        combatant = match.combatants[combatant_id]
        if combatant.body != "humanoid_robot" or combatant.face_variant != "same-face":
            errors.append(f"{combatant_id} is not the shared humanoid body")
    if match.combatants["a1"].body != match.combatants["b1"].body:
        errors.append("the two viewpoints do not share a body")
    if match.combatants["a1"].faction == match.combatants["b1"].faction:
        errors.append("viewpoints picked the same faction")
    picked = [event for event in match.named("CorePicked") if event.t_ms == contest_ms]
    rejected = [
        event
        for event in match.named("CorePickRejected")
        if event.t_ms == contest_ms and event.payload.get("reason") == "already_held"
    ]
    away = [
        event
        for event in match.named("CorePickRejected")
        if event.t_ms == contest_ms and event.payload.get("reason") == "not_at_core"
    ]
    if len(picked) != 1 or picked[0].payload.get("combatant_id") != "a1":
        errors.append("same-frame contest did not grant the core to client-a / a1")
    if len(rejected) != 1 or rejected[0].payload.get("combatant_id") != "b1":
        errors.append("client-b did not receive already_held on the contest frame")
    if len(away) != 4:
        errors.append(f"expected 4 bot not_at_core rejections, got {len(away)}")
    if picked and rejected and picked[0].t_ms != rejected[0].t_ms:
        errors.append("pick and already_held were not the same frame")
    interrupted = match.named("ScoreChannelInterrupted")
    if len(interrupted) != 1 or interrupted[0].payload.get("reason") != "hit":
        errors.append("expected one hit interrupt")
    elif interrupted[0].t_ms != hit_ms or interrupted[0].payload.get("combatant_id") != "a1":
        errors.append(f"interrupt payload {interrupted[0].to_dict()}")
    if any(event.name == "PointScored" and event.t_ms == hit_ms for event in match.events):
        errors.append("the interrupted channel scored")
    through_interrupt = [event for event in match.events if event.t_ms <= hit_ms]
    if replay_score(through_interrupt) != {"A": 0, "B": 0}:
        errors.append("score changed on the interrupt")
    scored = match.named("PointScored")
    if len(scored) != 1:
        errors.append(f"expected one PointScored, got {len(scored)}")
    elif scored[0].t_ms != score_ms or scored[0].payload.get("faction") != "A" or scored[0].payload.get("combatant_id") != "a2":
        errors.append(f"clean point landed wrong: {scored[0].to_dict()}")
    elif scored[0].t_ms <= hit_ms:
        errors.append("clean point was not after the interrupt")
    returned = match.named("CoreReturnedToCenter")
    if len(returned) != 1 or returned[0].t_ms != score_ms:
        errors.append("missing CoreReturnedToCenter on the clean score")
    resets = match.named("CoreReset")
    if len(resets) != 1:
        errors.append(f"expected one CoreReset, got {len(resets)}")
    elif resets[0].t_ms != reset_ms or resets[0].payload.get("reason") != "overboard" or resets[0].payload.get("anchor") != "center":
        errors.append(f"reset payload {resets[0].to_dict()}")
    elif scored and resets[0].t_ms <= scored[0].t_ms:
        errors.append("reset happened before the clean score")
    blocked = [
        event
        for event in match.named("CorePickRejected")
        if event.payload.get("reason") == "not_pickable" and event.payload.get("combatant_id") == "b1"
    ]
    if not blocked:
        errors.append("sea window did not reject the viewpoint pickup")
    post = [event for event in match.named("CorePicked") if event.t_ms == post_ms]
    if len(post) != 1 or post[0].payload.get("combatant_id") != "a3":
        errors.append("core was not pickable at center after reset")
    if match.score != {"A": 1, "B": 0}:
        errors.append(f"score {match.score}")
    if replay_score(match.events) != match.score:
        errors.append("log score does not match match.score")
    if match.core.holder_id != "a3" or replay_holder(match.events) != "a3":
        errors.append(f"final holder {match.core.holder_id}")
    if match.phase == "settled" or match.named("MatchSettled"):
        errors.append("slice settled the match; NR-02 only checks the core beats")
    if not match.named("ActorDowned") or not match.named("ActorRespawned"):
        errors.append("down/respawn missing after the interrupt")
    if not any(event.payload.get("reason") == "downed" for event in match.named("CoreDropped")):
        errors.append("interrupt did not drop the core")
    if len(match.named("RouteSelected")) != 6:
        errors.append("roster did not all select a route")
    if len(match.named("MoveCompleted")) < 3:
        errors.append("local bots did not complete a move")
    bot_ids = {combatant.id for combatant in bots}
    seen = {event.payload.get("combatant_id") for event in match.events if event.payload.get("combatant_id") in bot_ids}
    if seen != bot_ids:
        errors.append(f"bots missing from the log: {bot_ids - seen}")
    return errors


def evaluate(match: SteelTideMatch | None = None) -> tuple[dict[str, str], list[str]]:
    match = match or run_nr02_match()
    logs = render_dual_logs(match)
    errors = acceptance_errors(match)
    errors.extend(compare_dual_logs(match, logs))
    return logs, errors


def main(argv: list[str] | None = None) -> int:
    args = [] if argv is None else list(argv)
    if args not in ([], ["--check"]):
        print("usage: PYTHONPATH=sim python3 -m steel_tide nr02 [--check]")
        return 2
    match = run_nr02_match()
    logs, errors = evaluate(match)
    if args == ["--check"]:
        errors.extend(diff_against_evidence(logs))
    else:
        write_evidence(logs)
    if errors:
        print("NR-02 3v3 dual-end FAIL")
        for error in errors:
            print(f"  - {error}")
        return 1
    paths = evidence_paths()
    print("NR-02 3v3 dual-end PASS")
    print(
        "roster=6 viewpoints=2 local_bots=4 "
        f"score=A:{match.score['A']},B:{match.score['B']} holder={match.core.holder_id} "
        f"events={len(match.events)}"
    )
    for end in ("server", "client-a", "client-b"):
        print(f"{end}={paths[end].as_posix()}")
    if args == ["--check"]:
        print("checked sample logs")
    return 0
