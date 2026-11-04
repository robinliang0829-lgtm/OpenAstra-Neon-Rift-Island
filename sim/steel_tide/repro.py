"""Scripted two-client reproductions the UE operator diffs against PIE logs."""

from __future__ import annotations

from .config import load_config
from .match import SERVER_CLIENT, SteelTideMatch


def _duo() -> SteelTideMatch:
    match = SteelTideMatch(load_config())
    match.add_combatant("a1", "client-a", "humanoid_robot", "human", face_variant="same-face")
    match.add_combatant("b1", "client-b", "humanoid_robot", "human", face_variant="same-face")
    match.choose_faction("a1", "A")
    match.choose_faction("b1", "B")
    match.choose_role("a1", "assault")
    match.choose_role("b1", "support")
    match.start()
    return match


def scenario_no_double_hold() -> SteelTideMatch:
    match = _duo()
    match.place_for_test("a1", "center")
    match.place_for_test("b1", "center")
    match.enqueue("client-a", "pick_core", 1.0, combatant_id="a1")
    match.enqueue("client-b", "pick_core", 1.0, combatant_id="b1")
    match.advance_to(1.0)
    return match


def check_no_double_hold(match: SteelTideMatch) -> list[str]:
    errors = match.holder_errors()
    picked = match.named("CorePicked")
    rejected = [event for event in match.named("CorePickRejected") if event.payload.get("reason") == "already_held"]
    if len(picked) != 1:
        errors.append(f"expected 1 CorePicked, got {len(picked)}")
    if len(rejected) != 1:
        errors.append(f"expected 1 already_held rejection, got {len(rejected)}")
    if picked and rejected and picked[0].t_ms != rejected[0].t_ms:
        errors.append("pick and rejection were not the same frame")
    if match.core.holder_id is None:
        errors.append("core has no holder after a successful pick")
    holders = {match.core.holder_id}
    if len(holders) != 1:
        errors.append("holder set is not a single id")
    return errors


def scenario_interrupt() -> SteelTideMatch:
    match = _duo()
    match.place_for_test("a1", "center")
    match.enqueue("client-a", "pick_core", 0.5, combatant_id="a1")
    match.advance_to(0.5)
    match.place_for_test("a1", "terminal_b")
    match.enqueue("client-a", "begin_score", 1.0, combatant_id="a1")
    match.advance_to(1.0)
    match.enqueue(SERVER_CLIENT, "hit", 3.9, target_id="a1", down=True)
    match.advance_to(8.0)
    return match


def check_interrupt(match: SteelTideMatch) -> list[str]:
    errors = match.holder_errors()
    if match.named("PointScored"):
        errors.append("interrupted channel awarded a point")
    interrupted = match.named("ScoreChannelInterrupted")
    if len(interrupted) != 1 or interrupted[0].payload.get("reason") != "hit":
        errors.append("expected one hit interrupt")
    if match.score != {"A": 0, "B": 0}:
        errors.append(f"score changed: {match.score}")
    if match.core.status == "held":
        errors.append("downed carrier still holds the core")
    return errors


def scenario_score_completes() -> SteelTideMatch:
    match = _duo()
    match.place_for_test("a1", "center")
    match.enqueue("client-a", "pick_core", 0.5, combatant_id="a1")
    match.advance_to(0.5)
    match.place_for_test("a1", "terminal_b")
    match.enqueue("client-a", "begin_score", 1.0, combatant_id="a1")
    match.enqueue("client-a", "begin_score", 2.0, combatant_id="a1")
    match.advance_to(20.0)
    return match


def check_score_completes(match: SteelTideMatch) -> list[str]:
    errors = match.holder_errors()
    scored = match.named("PointScored")
    if len(scored) != 1:
        errors.append(f"expected exactly one PointScored, got {len(scored)}")
    elif scored[0].t_ms != 4000 or scored[0].payload.get("faction") != "A":
        errors.append(f"point landed at the wrong time or side: {scored[0].to_dict()}")
    if match.score != {"A": 1, "B": 0}:
        errors.append(f"score {match.score}")
    if match.named("CoreReset"):
        errors.append("a clean score must return the core, not timeout-reset it")
    if not match.named("CoreReturnedToCenter"):
        errors.append("missing CoreReturnedToCenter")
    return errors


def scenario_timeout_reset(kind: str = "overboard") -> SteelTideMatch:
    match = _duo()
    match.place_for_test("a1", "center")
    match.enqueue("client-a", "pick_core", 0.5, combatant_id="a1")
    match.advance_to(0.5)
    mark = "mark_core_overboard" if kind == "overboard" else "mark_core_stuck"
    match.enqueue(SERVER_CLIENT, mark, 2.0)
    match.enqueue("client-b", "pick_core", 5.0, combatant_id="b1")
    match.advance_to_ms(9999)
    return match


def finish_timeout_reset(match: SteelTideMatch) -> SteelTideMatch:
    match.advance_to(10.0)
    match.place_for_test("b1", "center")
    match.enqueue("client-b", "pick_core", 10.0, combatant_id="b1")
    match.advance_to(10.0)
    return match


def check_timeout_pending(match: SteelTideMatch, kind: str) -> list[str]:
    errors = match.holder_errors()
    if match.named("CoreReset"):
        errors.append("core reset before the timeout")
    if match.named("PointScored"):
        errors.append("timeout path awarded a point")
    if match.core.status != kind:
        errors.append(f"core status {match.core.status}, expected {kind}")
    if match.core.holder_id is not None:
        errors.append("unpickable core still has a holder")
    rejected = match.named("CorePickRejected")
    if not any(event.payload.get("reason") == "not_pickable" for event in rejected):
        errors.append("pickup during timeout was not rejected")
    return errors


def check_timeout_reset(match: SteelTideMatch, kind: str) -> list[str]:
    errors = match.holder_errors()
    resets = match.named("CoreReset")
    if len(resets) != 1:
        errors.append(f"expected 1 CoreReset, got {len(resets)}")
    elif resets[0].t_ms != 10000 or resets[0].payload.get("reason") != kind:
        errors.append(f"reset payload {resets[0].to_dict()}")
    elif resets[0].payload.get("anchor") != "center":
        errors.append("reset did not return the core to center")
    if match.named("PointScored"):
        errors.append("timeout reset awarded a point")
    if match.core.anchor != "center" or match.core.status != "held" or match.core.holder_id != "b1":
        errors.append("core was not pickable at center after reset")
    return errors


def scenario_match_timeout() -> SteelTideMatch:
    config = load_config()
    config.match_seconds = 12
    config.overtime_seconds = 5
    match = SteelTideMatch(config)
    match.add_combatant("a1", "client-a", "human", "human")
    match.add_combatant("b1", "client-b", "beast", "digital_resident")
    match.choose_faction("a1", "A")
    match.choose_faction("b1", "B")
    match.choose_role("a1", "assault")
    match.choose_role("b1", "recon")
    match.start()
    match.advance_to(12)
    match.choose_role("a1", "support")
    match.choose_role("b1", "assault")
    match.choose_faction("a1", "B")
    match.advance_to(17)
    match.choose_role("a1", "recon")
    match.advance_to(40)
    return match


def check_match_timeout(match: SteelTideMatch) -> list[str]:
    errors = match.holder_errors()
    if match.phase != "settled" or match.settled_kind != "draw":
        errors.append(f"expected a draw settle, phase={match.phase} kind={match.settled_kind}")
    settled = match.named("MatchSettled")
    if len(settled) != 1:
        errors.append(f"expected one MatchSettled, got {len(settled)}")
    elif settled[0].payload.get("role_select_open") is not False or settled[0].payload.get("winner") is not None:
        errors.append(f"settle reopened a choice or named a winner: {settled[0].payload}")
    if match.lobby_open:
        errors.append("role select reopened")
    role_chosen = match.named("RoleChosen")
    if len(role_chosen) != 2:
        errors.append("timeout settlement repeated role select")
    if not match.named("RoleRejected"):
        errors.append("locked role select did not reject")
    if not any(event.payload.get("reason") == "locked" for event in match.named("FactionRejected")):
        errors.append("faction was not locked at the clock")
    if match.combatants["a1"].role != "assault" or match.combatants["a1"].faction != "A":
        errors.append("timeout rewrote the locked loadout")
    return errors


def run_repro_report() -> bool:
    checks = [
        ("no_double_hold", check_no_double_hold(scenario_no_double_hold())),
        ("interrupt_cancels_score", check_interrupt(scenario_interrupt())),
        ("timeout_reset", check_timeout_reset(finish_timeout_reset(scenario_timeout_reset()), "overboard")),
        ("match_timeout_no_role_redraw", check_match_timeout(scenario_match_timeout())),
    ]
    ok = True
    for name, errors in checks:
        if errors:
            ok = False
            print(f"REPRO {name} FAIL")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"REPRO {name} PASS")
    return ok
