"""NR-M2 fail slice: three failure paths, one headless check.

Both ends reach for the core on the same timestamp and only one holds it.
A hit during the score channel awards nothing. Timeout settlement does not
re-open the three-role menu.

    PYTHONPATH=sim python3 -m steel_tide m2-fail
    PYTHONPATH=sim python3 -m steel_tide m2-fail --check

This is a parallel knife next to `m2-pack`. It is not a pack step.
`wired_into_m2_pack` stays false unless `STEPS` in `nr_m2_pack` grows an
`m2-fail` row and this constant is flipped with it. The match object is
the only scorer. `EVENT_NAMES` is not extended. `place_for_test` is not
an event. The greybox file is not rewritten; this slice only shortens the
in-memory match and overtime clocks so the draw fits in the sample log.
"""

from __future__ import annotations

from .config import CONFIG_PATH, SteelTideConfig, load_config
from .dual_log import compare_dual_logs, diff_against_evidence, render_dual_logs, write_evidence
from .events import EVENT_NAMES
from .match import SERVER_CLIENT, SteelTideMatch
from .nr_m2_pack import STEPS

SCHEMA = "nr-m2-fail-dual-end-v1"
EVIDENCE_DIR = CONFIG_PATH.parents[1] / "docs" / "evidence" / "nr-m2-fail"
PATHS = "parallel_pick,hit_interrupt,timeout_no_role_redraw"

# Declared pack wiring. `--check` fails if this disagrees with STEPS.
WIRED_INTO_M2_PACK = False

# In-memory clocks only. config/steel_tide_greybox.json stays 360 / 60.
MATCH_SECONDS = 12
OVERTIME_SECONDS = 5
PICK_S = 1.0
CHANNEL_S = 2.0
HIT_S = 4.0


def fail_config() -> SteelTideConfig:
    config = load_config()
    config.match_seconds = MATCH_SECONDS
    config.overtime_seconds = OVERTIME_SECONDS
    return config


def _offer_locked_roles(match: SteelTideMatch) -> None:
    """Ask for every configured role. A closed lobby rejects all three."""
    for combatant_id in ("a1", "b1"):
        for role in match.config.roles:
            match.choose_role(combatant_id, role)


def run_m2_fail_match(config: SteelTideConfig | None = None) -> SteelTideMatch:
    config = config or fail_config()
    match = SteelTideMatch(config)
    match.add_combatant("a1", "client-a", "humanoid_robot", "human", face_variant="same-face")
    match.add_combatant("b1", "client-b", "humanoid_robot", "human", face_variant="same-face")
    match.choose_faction("a1", "A")
    match.choose_faction("b1", "B")
    match.choose_role("a1", "assault")
    match.choose_role("b1", "support")
    match.start()

    # Both ends are on the core. client-b is enqueued first. The batch still
    # sorts by client id, so client-a takes the only hold and b1 stays empty.
    match.place_for_test("a1", "center")
    match.place_for_test("b1", "center")
    match.enqueue("client-b", "pick_core", PICK_S, combatant_id="b1")
    match.enqueue("client-a", "pick_core", PICK_S, combatant_id="a1")
    match.advance_to(PICK_S)

    terminal = config.score_terminal["A"]
    match.place_for_test("a1", terminal)
    match.enqueue("client-a", "begin_score", CHANNEL_S, combatant_id="a1")
    match.enqueue(SERVER_CLIENT, "hit", HIT_S, target_id="a1", down=True)
    match.advance_to(config.match_seconds)
    _offer_locked_roles(match)
    match.advance_to(config.match_seconds + config.overtime_seconds)
    _offer_locked_roles(match)
    match.choose_faction("a1", "B")
    match.choose_faction("b1", "A")
    return match


def _at(match: SteelTideMatch, name: str, t_ms: int, **payload) -> list:
    found = []
    for event in match.named(name):
        if event.t_ms != t_ms:
            continue
        if all(event.payload.get(key) == value for key, value in payload.items()):
            found.append(event)
    return found


def _wiring_errors() -> list[str]:
    listed = any(name == "m2-fail" for name, _module, _args in STEPS)
    if listed != WIRED_INTO_M2_PACK:
        state = "lists" if listed else "does not list"
        flag = "true" if WIRED_INTO_M2_PACK else "false"
        return [f"wired_into_m2_pack={flag} but m2-pack {state} an m2-fail step"]
    return []


def _parallel_pick_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    pick_ms = match.config.seconds_to_ms(PICK_S)
    picked = match.named("CorePicked")
    rejected = [event for event in match.named("CorePickRejected") if event.payload.get("reason") == "already_held"]
    if len(picked) != 1:
        errors.append(f"parallel pick granted {len(picked)} holders")
    elif picked[0].t_ms != pick_ms or picked[0].payload.get("combatant_id") != "a1":
        errors.append("the single hold was not client-a's a1 at the shared timestamp")
    elif picked[0].payload.get("client_id") != "client-a" or picked[0].payload.get("anchor") != "center":
        errors.append("the successful pick left center or the client-a end")
    if len(rejected) != 1:
        errors.append(f"expected one already_held rejection, got {len(rejected)}")
    elif rejected[0].t_ms != pick_ms or rejected[0].payload.get("combatant_id") != "b1":
        errors.append("client-b was not the empty hand on the same timestamp")
    elif rejected[0].payload.get("client_id") != "client-b":
        errors.append("the empty-hand rejection was not client-b")
    if picked and rejected and picked[0].t_ms != rejected[0].t_ms:
        errors.append("pick and empty-hand rejection were not the same frame")
    holders = {event.payload.get("combatant_id") for event in picked}
    if holders != {"a1"}:
        errors.append(f"holder set is not the single winner: {holders}")
    if any(event.payload.get("combatant_id") == "b1" for event in picked):
        errors.append("the empty hand also received CorePicked")
    return errors


def _interrupt_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    channel_ms = config.seconds_to_ms(CHANNEL_S)
    hit_ms = config.seconds_to_ms(HIT_S)
    started = _at(match, "ScoreChannelStarted", channel_ms, combatant_id="a1", terminal="terminal_b")
    if len(started) != 1:
        errors.append("a1 did not start the channel on the enemy terminal")
    elif started[0].payload.get("ends_ms") != channel_ms + config.score_channel_ms:
        errors.append("the channel end was not score_channel_seconds")
    interrupted = _at(match, "ScoreChannelInterrupted", hit_ms, combatant_id="a1", reason="hit")
    if len(interrupted) != 1:
        errors.append("the hit did not interrupt the channel")
    else:
        elapsed = interrupted[0].payload.get("elapsed_ms")
        if elapsed != hit_ms - channel_ms or not isinstance(elapsed, int) or elapsed >= config.score_channel_ms:
            errors.append(f"hit elapsed was not inside the channel: {elapsed}")
    if match.named("PointScored"):
        errors.append("the interrupted channel awarded a point")
    if match.score != {"A": 0, "B": 0}:
        errors.append(f"score changed: {match.score}")
    dropped = _at(match, "CoreDropped", hit_ms, combatant_id="a1", reason="downed", anchor="terminal_b")
    if len(dropped) != 1:
        errors.append("the downed carrier did not drop the core on the terminal")
    if not _at(match, "ActorDowned", hit_ms, combatant_id="a1"):
        errors.append("the interrupting hit did not down a1")
    respawn_ms = hit_ms + config.down_ms
    respawned = _at(match, "ActorRespawned", respawn_ms, combatant_id="a1", anchor="spawn_a")
    if len(respawned) != 1:
        errors.append("a1 did not respawn at spawn_a after down_seconds")
    if match.core.anchor != "terminal_b" or match.core.status != "ground" or match.core.holder_id is not None:
        errors.append("the dropped core left the terminal or gained a holder")
    if match.named("CoreReturnedToCenter") or match.named("CoreReset"):
        errors.append("a failed channel returned or reset the core")
    names = [event.name for event in match.events if event.t_ms == hit_ms]
    if names != ["ScoreChannelInterrupted", "CoreDropped", "ActorDowned"]:
        errors.append(f"hit timestamp order drifted: {names}")
    return errors


def _timeout_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    if tuple(config.roles) != ("assault", "support", "recon"):
        errors.append(f"role menu is not the three configured choices: {config.roles}")
    clock_ms = config.match_ms
    settle_ms = clock_ms + config.overtime_ms
    expired = _at(match, "MatchClockExpired", clock_ms)
    if len(expired) != 1 or expired[0].payload.get("role_select_open") is not False:
        errors.append("the clock reopened role select")
    elif expired[0].payload.get("score") != {"A": 0, "B": 0}:
        errors.append("the clock settled a score that the hit should have denied")
    overtime = _at(match, "OvertimeStarted", clock_ms)
    if len(overtime) != 1 or overtime[0].payload.get("role_select_open") is not False:
        errors.append("overtime reopened role select")
    settled = match.named("MatchSettled")
    if len(settled) != 1 or settled[0].t_ms != settle_ms:
        errors.append("timeout did not settle once at the overtime buzzer")
    elif settled[0].payload.get("kind") != "draw" or settled[0].payload.get("winner") is not None:
        errors.append(f"tied timeout was not a draw: {settled[0].payload}")
    elif settled[0].payload.get("role_select_open") is not False or settled[0].payload.get("score") != {"A": 0, "B": 0}:
        errors.append(f"settlement reopened a choice or invented a score: {settled[0].payload}")
    if match.phase != "settled" or match.settled_kind != "draw" or match.lobby_open:
        errors.append(f"lobby reopened phase={match.phase} kind={match.settled_kind} open={match.lobby_open}")
    role_chosen = match.named("RoleChosen")
    if [(event.t_ms, event.payload.get("combatant_id"), event.payload.get("role")) for event in role_chosen] != [
        (0, "a1", "assault"),
        (0, "b1", "support"),
    ]:
        errors.append("timeout settlement repeated role select")
    if match.named("RolesLocked") and any(event.t_ms > 0 for event in match.named("RolesLocked")):
        errors.append("a second RolesLocked re-offered the menu")
    # Locked RoleRejected keeps the existing payload: combatant_id and reason.
    # The role name is not copied onto that event. Three rejects per end are
    # the three menu entries, in config.roles order, for a1 then b1.
    expected_ids = [combatant_id for combatant_id in ("a1", "b1") for _role in config.roles]
    for t_ms, label in ((clock_ms, "overtime"), (settle_ms, "settlement")):
        locked = [
            event.payload.get("combatant_id") for event in _at(match, "RoleRejected", t_ms, reason="locked")
        ]
        if locked != expected_ids:
            errors.append(f"{label} did not reject the three-choice for both ends: {locked}")
        if any("role" in event.payload for event in _at(match, "RoleRejected", t_ms)):
            errors.append(f"{label} wrote a new role field onto RoleRejected")
    factions = _at(match, "FactionRejected", settle_ms, reason="locked")
    if sorted(event.payload.get("combatant_id") for event in factions) != ["a1", "b1"]:
        errors.append("settlement did not keep factions locked")
    if match.combatants["a1"].role != "assault" or match.combatants["b1"].role != "support":
        errors.append("timeout rewrote the locked roles")
    if match.combatants["a1"].faction != "A" or match.combatants["b1"].faction != "B":
        errors.append("timeout rewrote the locked factions")
    return errors


def _name_errors(match: SteelTideMatch) -> list[str]:
    unknown = sorted({event.name for event in match.events if event.name not in EVENT_NAMES})
    if unknown:
        return [f"slice emitted names outside EVENT_NAMES: {unknown}"]
    return []


def acceptance_errors(match: SteelTideMatch) -> list[str]:
    errors = match.holder_errors()
    errors.extend(_wiring_errors())
    errors.extend(_parallel_pick_errors(match))
    errors.extend(_interrupt_errors(match))
    errors.extend(_timeout_errors(match))
    errors.extend(_name_errors(match))
    return errors


def _extra(match: SteelTideMatch) -> tuple[tuple[str, str], ...]:
    parts = []
    for combatant in sorted(match.combatants.values(), key=lambda item: item.id):
        parts.append(f"{combatant.id}:{combatant.body}:{combatant.faction}:{combatant.controller}")
    flag = "true" if WIRED_INTO_M2_PACK else "false"
    return (
        ("identities", ",".join(parts)),
        ("fail_paths", PATHS),
        ("role_menu", ",".join(match.config.roles)),
        ("wired_into_m2_pack", flag),
    )


def render_slice_logs(match: SteelTideMatch) -> dict[str, str]:
    return render_dual_logs(match, schema=SCHEMA, extra_headers=_extra(match))


def evaluate_slice(match: SteelTideMatch | None = None) -> tuple[dict[str, str], list[str]]:
    match = match or run_m2_fail_match()
    logs = render_slice_logs(match)
    errors = acceptance_errors(match)
    errors.extend(compare_dual_logs(match, logs, schema=SCHEMA, extra_headers=_extra(match)))
    return logs, errors


def main(argv: list[str] | None = None) -> int:
    args = [] if argv is None else list(argv)
    if args not in ([], ["--check"]):
        print("usage: PYTHONPATH=sim python3 -m steel_tide m2-fail [--check]", flush=True)
        return 2
    match = run_m2_fail_match()
    logs, errors = evaluate_slice(match)
    if args == ["--check"]:
        errors.extend(diff_against_evidence(logs, EVIDENCE_DIR))
    else:
        write_evidence(logs, EVIDENCE_DIR)
    flag = "true" if WIRED_INTO_M2_PACK else "false"
    print(f"wired_into_m2_pack={flag}", flush=True)
    if errors:
        print("NR-M2 fail FAIL", flush=True)
        for error in errors:
            print(f"  - {error}", flush=True)
        return 1
    print("NR-M2 fail PASS", flush=True)
    print(
        f"paths={PATHS} holder_at_pick=a1 empty_hand=b1 "
        f"score=A:{match.score['A']},B:{match.score['B']} settled={match.settled_kind} "
        f"events={len(match.events)}",
        flush=True,
    )
    for end in ("server", "client-a", "client-b"):
        print(f"{end}={(EVIDENCE_DIR / f'{end}.log').as_posix()}", flush=True)
    if args == ["--check"]:
        print("checked sample logs", flush=True)
    return 0
