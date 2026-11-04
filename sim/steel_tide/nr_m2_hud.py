"""NR-M2 HUD cue slice. Headless contract, not a widget.

One command:

    PYTHONPATH=sim python3 -m steel_tide m2-hud
    PYTHONPATH=sim python3 -m steel_tide m2-hud --check

The match object remains the only scorer. `HudCue` rows are a side log
written on the same millisecond as the authoritative event. They are not
in `EVENT_NAMES` and they are not in `match.events`.

Not a step of `m2-pack`. The pack's unittest step still imports the tests
for this module. Pack evidence stays the rules chain. `wired_into_m2_pack`
stays false unless `STEPS` grows an `m2-hud` row and this constant is
flipped with it.
"""

from __future__ import annotations

import json

from .config import CONFIG_PATH, load_config
from .events import EVENT_NAMES
from .hud import PATHS, catalog_ids
from .match import SERVER_CLIENT, SteelTideMatch
from .model import Event
from .nr_m2_pack import STEPS
from .palette import BADGES, PALETTE, badge_identity, badge_svg, colorblind_badge, greyscale_badge

ROOT = CONFIG_PATH.parents[1]
EVIDENCE_PATH = ROOT / "docs" / "evidence" / "nr-m2-hud" / "hud.log"
HEADER_PATH = ROOT / "Source" / "NeonRift" / "Public" / "NeonRiftHudCues.h"
SCHEMA = "nr-m2-hud-cues-v1"

# Declared pack wiring. `--check` fails if this disagrees with STEPS.
WIRED_INTO_M2_PACK = False

PATH_TEXT = (
    "scoreboard:PointScored+MatchSettled,"
    "read_bar:ScoreChannelStarted+ScoreChannelInterrupted,"
    "spawn_shield:MatchStarted+HitIgnored.spawn_protection+ActorRespawned,"
    "role_side_lock:RoleRejected.locked+FactionRejected.locked"
)

PROTECT_HIT_S = 1.0
DOWN_S = 3.5
PICK_S = 4.0
CHANNEL_S = 4.5
INTERRUPT_S = 5.5
CHANNEL_AGAIN_S = 6.0
SECOND_PICK_S = 10.0
SECOND_CHANNEL_S = 10.5
RESPAWN_HIT_S = 11.0
COLORBLIND_MODES = ("protanopia", "deuteranopia", "tritanopia")


def _offer_locked(match: SteelTideMatch) -> None:
    """Ask for every configured role and the other side. A closed lobby rejects both."""
    for combatant_id in ("a1", "b1"):
        for role in match.config.roles:
            match.choose_role(combatant_id, role)
        other = "B" if match.combatants[combatant_id].faction == "A" else "A"
        match.choose_faction(combatant_id, other)


def run_m2_hud(config=None) -> SteelTideMatch:
    """Same-body A and B. Scoreboard, read bar, spawn shield, and the locked menu."""
    match = SteelTideMatch(config or load_config())
    for combatant_id, client_id, faction, role in (
        ("a1", "client-a", "A", "assault"),
        ("b1", "client-b", "B", "support"),
    ):
        match.add_combatant(
            combatant_id,
            client_id,
            "humanoid_robot",
            "human",
            face_variant="plate-7",
        )
        match.choose_faction(combatant_id, faction)
    match.choose_role("a1", "scout")
    match.choose_role("a1", "assault")
    match.choose_role("b1", "support")
    match.start()
    _offer_locked(match)

    match.enqueue(SERVER_CLIENT, "hit", PROTECT_HIT_S, target_id="a1", down=True)
    match.advance_to(PROTECT_HIT_S)
    match.enqueue(SERVER_CLIENT, "hit", DOWN_S, target_id="b1", down=True)
    match.place_for_test("a1", "center")
    match.enqueue("client-a", "pick_core", PICK_S, combatant_id="a1")
    match.advance_to(PICK_S)
    match.place_for_test("a1", "terminal_b")
    match.enqueue("client-a", "begin_score", CHANNEL_S, combatant_id="a1")
    match.enqueue(SERVER_CLIENT, "hit", INTERRUPT_S, target_id="a1", down=False)
    match.advance_to(INTERRUPT_S)
    match.enqueue("client-a", "begin_score", CHANNEL_AGAIN_S, combatant_id="a1")
    match.advance_to(CHANNEL_AGAIN_S + match.config.score_channel_seconds)
    match.place_for_test("a1", "center")
    match.enqueue("client-a", "pick_core", SECOND_PICK_S, combatant_id="a1")
    match.advance_to(SECOND_PICK_S)
    match.place_for_test("a1", "terminal_b")
    match.enqueue("client-a", "begin_score", SECOND_CHANNEL_S, combatant_id="a1")
    match.enqueue(SERVER_CLIENT, "hit", RESPAWN_HIT_S, target_id="b1", down=True)
    match.advance_to(SECOND_CHANNEL_S + match.config.score_channel_seconds)
    _offer_locked(match)
    return match


def render_hud_log(match: SteelTideMatch) -> str:
    holder = "-" if match.core.holder_id is None else match.core.holder_id
    flag = "true" if WIRED_INTO_M2_PACK else "false"
    lines = [
        f"# schema {SCHEMA}",
        "# authority sim/steel_tide",
        "# kind hud-cue-contract",
        "# asset none",
        "# umg false",
        "# texture none",
        "# uasset false",
        "# color_is_identity false",
        "# identity shoulder_badge",
        f"# wired_into_m2_pack {flag}",
        f"# paths {PATH_TEXT}",
        "# scoreboard PointScored MatchSettled",
        "# read_bar ScoreChannelStarted ScoreChannelInterrupted",
        "# spawn_shield MatchStarted HitIgnored:spawn_protection ActorRespawned",
        "# role_side_lock RoleRejected:locked FactionRejected:locked",
        f"# score A={match.score['A']} B={match.score['B']}",
        f"# holder {holder}",
        f"# phase {match.phase}",
        f"# settled {match.settled_kind}",
    ]
    for cue in match.hud_cues:
        lines.append(cue.format())
    return "\n".join(lines) + "\n"


def _cues(match: SteelTideMatch, cue_id: str) -> list[Event]:
    return [cue for cue in match.hud_cues if cue.payload.get("cue_id") == cue_id]


def _source(match: SteelTideMatch, cue: Event) -> Event:
    return match.events[cue.payload["source_index"]]


def _wiring_errors() -> list[str]:
    listed = any(name == "m2-hud" for name, _module, _args in STEPS)
    if listed != WIRED_INTO_M2_PACK:
        state = "lists" if listed else "does not list"
        flag = "true" if WIRED_INTO_M2_PACK else "false"
        return [f"wired_into_m2_pack={flag} but m2-pack {state} an m2-hud step"]
    return []


def _geometry_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    a1 = match.combatants["a1"]
    b1 = match.combatants["b1"]
    if a1.body != b1.body or a1.face_variant != b1.face_variant:
        errors.append("A and B humanoids were split by body or face")
    for faction in ("A", "B"):
        badge = BADGES[faction]
        config_badge = match.config.badges[faction]
        if config_badge["shape"] != badge["shape"] or config_badge["light_slot"] != badge["light_slot"]:
            errors.append(f"{faction} config badge drifted from the NR-03 geometry")
        painted = badge_svg(faction).replace(PALETTE[badge["aux"]]["hex"], "#808080")
        if badge_identity(painted) != (badge["shape"], badge["light_slot"]):
            errors.append(f"painting {faction} changed the shoulder identity")
        masked = [greyscale_badge(badge_svg(faction))]
        masked.extend(colorblind_badge(badge_svg(faction), mode) for mode in COLORBLIND_MODES)
        for variant in masked:
            if badge_identity(variant) != (badge["shape"], badge["light_slot"]):
                errors.append(f"color mask changed {faction} shape or shoulder slot")
    return errors


def _scoreboard_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    scored = match.named("PointScored")
    settled = match.named("MatchSettled")
    rows = _cues(match, "hud.scoreboard")
    points = [cue for cue in rows if cue.payload.get("state") == "point"]
    finals = [cue for cue in rows if cue.payload.get("state") == "settled"]
    if len(scored) != 2 or len(points) != 2:
        errors.append(f"scoreboard points {len(points)} != PointScored {len(scored)}")
    if len(settled) != 1 or len(finals) != 1:
        errors.append("scoreboard did not settle once")
        return errors
    for cue, event in zip(points, scored):
        if cue.t_ms != event.t_ms or _source(match, cue) is not event:
            errors.append("a point line is not on its PointScored millisecond")
        if cue.payload.get("score") != event.payload.get("score"):
            errors.append("a point line recomputed the score")
        if cue.payload.get("faction") != event.payload.get("faction"):
            errors.append("a point line lost the scoring faction")
    final = finals[0]
    event = settled[0]
    if final.t_ms != event.t_ms or _source(match, final) is not event:
        errors.append("the settled line is not on MatchSettled")
    if event.t_ms != scored[-1].t_ms:
        errors.append("MatchSettled is not the same millisecond as the winning point")
    if event.payload.get("kind") != "points" or event.payload.get("winner") != "A":
        errors.append(f"settlement was not a points win for A: {event.payload}")
    if event.payload.get("score") != {"A": 2, "B": 0} or match.score != {"A": 2, "B": 0}:
        errors.append(f"scoreboard score drifted: {match.score}")
    if any(item.name == "MatchSettled" and item.t_ms == scored[0].t_ms for item in match.events):
        errors.append("the first point settled the match")
    if match.named("OvertimeStarted"):
        errors.append("regulation points_to_win opened overtime")
    sides = final.payload.get("sides")
    if sides != [
        {"faction": "A", "light_slot": "shoulder_left", "points": 2, "shape": "open_chevron"},
        {"faction": "B", "light_slot": "shoulder_right", "points": 0, "shape": "closed_ring"},
    ]:
        errors.append(f"settled board lost a shoulder badge: {sides}")
    return errors


def _read_bar_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    started = match.named("ScoreChannelStarted")
    interrupted = match.named("ScoreChannelInterrupted")
    opened = [cue for cue in _cues(match, "hud.terminal.read_bar") if cue.payload.get("state") == "open"]
    cleared = [cue for cue in _cues(match, "hud.terminal.read_bar") if cue.payload.get("state") == "cleared"]
    if len(started) != 3 or len(opened) != 3:
        errors.append(f"read bar opened {len(opened)} times for {len(started)} starts")
    if len(interrupted) != 1 or len(cleared) != 1:
        errors.append("read bar did not clear on the one interrupt")
        return errors
    for cue, event in zip(opened, started):
        if cue.t_ms != event.t_ms or _source(match, cue) is not event:
            errors.append("an open read bar is not on ScoreChannelStarted")
        if cue.payload.get("duration_ms") != config.score_channel_ms or cue.payload.get("filled_ms") != 0:
            errors.append("an open read bar is not the configured empty channel")
        if cue.payload.get("terminal") != "terminal_b":
            errors.append("the read bar left the enemy terminal")
    cue = cleared[0]
    event = interrupted[0]
    if cue.t_ms != event.t_ms or _source(match, cue) is not event:
        errors.append("the cleared read bar is not on ScoreChannelInterrupted")
    elapsed = config.seconds_to_ms(INTERRUPT_S) - config.seconds_to_ms(CHANNEL_S)
    if event.payload.get("reason") != "hit" or event.payload.get("elapsed_ms") != elapsed:
        errors.append(f"interrupt payload drifted: {event.payload}")
    if cue.payload.get("scored") is not False or cue.payload.get("filled_ms") != elapsed:
        errors.append("the cleared read bar claims a fill that scored")
    if any(item.name == "PointScored" and item.t_ms == event.t_ms for item in match.events):
        errors.append("the interrupted channel scored on the same millisecond")
    if any(cue.payload.get("source_event") == "PointScored" for cue in _cues(match, "hud.terminal.read_bar")):
        errors.append("a completed channel cleared the read bar as an interrupt")
    return errors


def _spawn_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    started = match.named("MatchStarted")
    ignored = [event for event in match.named("HitIgnored") if event.payload.get("reason") == "spawn_protection"]
    respawned = match.named("ActorRespawned")
    rows = _cues(match, "hud.spawn_shield")
    opening = [cue for cue in rows if _source(match, cue).name == "MatchStarted"]
    holds = [cue for cue in rows if cue.payload.get("state") == "hold"]
    returns = [cue for cue in rows if _source(match, cue).name == "ActorRespawned"]
    if len(started) != 1 or [cue.payload.get("combatant_id") for cue in opening] != ["a1", "b1"]:
        errors.append("match start did not raise one shield per combatant")
    elif any(cue.t_ms != started[0].t_ms or _source(match, cue) is not started[0] for cue in opening):
        errors.append("opening shields are not on the MatchStarted millisecond")
    else:
        for cue, combatant_id, anchor in zip(opening, ("a1", "b1"), ("spawn_a", "spawn_b")):
            if cue.payload.get("anchor") != anchor or cue.payload.get("protection_until_ms") != config.spawn_protection_ms:
                errors.append(f"opening shield for {combatant_id} left spawn or the 3 second window")
    protect_ms = config.seconds_to_ms(PROTECT_HIT_S)
    if not any(event.t_ms == protect_ms and event.payload.get("target_id") == "a1" for event in ignored):
        errors.append("the opening hit was not ignored under spawn protection")
    if any(event.name == "ActorDowned" and event.t_ms == protect_ms for event in match.events):
        errors.append("spawn protection downed a1")
    down_ms = config.seconds_to_ms(DOWN_S)
    respawn_ms = down_ms + config.down_ms
    if len(respawned) != 1 or respawned[0].t_ms != respawn_ms or respawned[0].payload.get("combatant_id") != "b1":
        errors.append("b1 did not respawn on the down clock")
    elif respawned[0].payload.get("anchor") != "spawn_b":
        errors.append("b1 did not respawn at spawn_b")
    elif respawned[0].payload.get("protection_until_ms") != respawn_ms + config.spawn_protection_ms:
        errors.append("respawn did not restart the shield window")
    if len(holds) != 2 or len(ignored) != 2:
        errors.append(f"spawn shield holds {len(holds)} != ignored hits {len(ignored)}")
    else:
        for cue, event in zip(holds, ignored):
            if cue.t_ms != event.t_ms or _source(match, cue) is not event:
                errors.append("a shield hold is not on its HitIgnored millisecond")
            if cue.t_ms >= cue.payload.get("protection_until_ms", 0):
                errors.append("a shield hold is outside its protection window")
            if cue.payload.get("reason") != "spawn_protection":
                errors.append("a shield hold lost spawn_protection")
    if (
        len(returns) != 1
        or not respawned
        or returns[0].t_ms != respawned[0].t_ms
        or _source(match, returns[0]) is not respawned[0]
    ):
        errors.append("the respawn shield is not on ActorRespawned")
    later_ms = config.seconds_to_ms(RESPAWN_HIT_S)
    later = [event for event in ignored if event.t_ms == later_ms and event.payload.get("target_id") == "b1"]
    if len(later) != 1:
        errors.append("the post-respawn hit was not ignored")
    if any(event.name == "ActorDowned" and event.payload.get("combatant_id") == "b1" and event.t_ms == later_ms for event in match.events):
        errors.append("the respawn shield did not hold")
    return errors


def _lock_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    if tuple(config.roles) != ("assault", "support", "recon"):
        errors.append(f"role menu is not the three configured choices: {config.roles}")
    unknown = [event for event in match.named("RoleRejected") if event.payload.get("reason") == "unknown_role"]
    locked_roles = [event for event in match.named("RoleRejected") if event.payload.get("reason") == "locked"]
    locked_sides = [event for event in match.named("FactionRejected") if event.payload.get("reason") == "locked"]
    role_rows = _cues(match, "hud.role_lock")
    side_rows = _cues(match, "hud.side_lock")
    if len(unknown) != 1 or unknown[0].payload.get("role") != "scout":
        errors.append("the pre-lock scout ask was not an unknown_role rejection")
    if any(cue.payload.get("source_event") == "RoleRejected" and cue.payload.get("source", {}).get("reason") == "unknown_role" for cue in match.hud_cues):
        errors.append("an unknown role painted a lock line")
    expected_ids = [combatant_id for combatant_id in ("a1", "b1") for _role in config.roles]
    settle_ms = match.named("MatchSettled")[0].t_ms if match.named("MatchSettled") else None
    for t_ms, label in ((0, "start"), (settle_ms, "settlement")):
        found = [event.payload.get("combatant_id") for event in locked_roles if event.t_ms == t_ms]
        if found != expected_ids:
            errors.append(f"{label} did not reject the three-choice menu for both ends: {found}")
        if any("role" in event.payload for event in locked_roles if event.t_ms == t_ms):
            errors.append(f"{label} wrote a role field onto locked RoleRejected")
        sides = [event.payload.get("combatant_id") for event in locked_sides if event.t_ms == t_ms]
        if sides != ["a1", "b1"]:
            errors.append(f"{label} did not keep both sides locked: {sides}")
    if len(role_rows) != len(locked_roles) or len(side_rows) != len(locked_sides):
        errors.append("lock lines are not one per locked rejection")
    else:
        for cue, event in zip(role_rows, locked_roles):
            if cue.t_ms != event.t_ms or _source(match, cue) is not event or cue.payload.get("reason") != "locked":
                errors.append("a role lock line left its RoleRejected")
            if "role" in cue.payload.get("source", {}):
                errors.append("a role lock line copied a role name the event does not have")
        for cue, event in zip(side_rows, locked_sides):
            if cue.t_ms != event.t_ms or _source(match, cue) is not event:
                errors.append("a side lock line left its FactionRejected")
    if match.combatants["a1"].role != "assault" or match.combatants["b1"].role != "support":
        errors.append("the locked menu rewrote roles")
    if match.combatants["a1"].faction != "A" or match.combatants["b1"].faction != "B":
        errors.append("the locked menu rewrote factions")
    if match.lobby_open or match.phase != "settled":
        errors.append("settlement reopened the lobby")
    return errors


def _contract_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    if "HudCue" in EVENT_NAMES:
        errors.append("HudCue was added to the scoring event names")
    if any(event.name == "HudCue" for event in match.events):
        errors.append("HudCue was written into match.events")
    unknown = sorted({event.name for event in match.events if event.name not in EVENT_NAMES})
    if unknown:
        errors.append(f"slice emitted names outside EVENT_NAMES: {unknown}")
    ids = catalog_ids()
    if len(set(ids)) != len(ids):
        errors.append("catalog cue ids are not unique")
    seen = {cue.payload.get("cue_id") for cue in match.hud_cues}
    missing = [cue_id for cue_id in ids if cue_id not in seen]
    if missing:
        errors.append(f"slice log missed {missing}")
    banned_line = ("tide_cyan", "hazard_amber", "#", "plate-7", "face", "UMG", ".uasset", "Widget")
    for cue in match.hud_cues:
        payload = cue.payload
        if cue.name != "HudCue":
            errors.append("side log row is not named HudCue")
        if payload.get("asset") != "none" or payload.get("texture") != "none" or payload.get("umg") is not False:
            errors.append("a HUD row claims a widget, texture, or asset")
        if payload.get("rules_effect") != "none" or payload.get("clock") != "source_event":
            errors.append("a HUD row uses its own clock or a rules effect")
        if payload.get("color_is_identity") is not False:
            errors.append("a HUD row treats color as identity")
        source = match.events[payload["source_index"]]
        if source.name != payload.get("source_event") or source.t_ms != cue.t_ms:
            errors.append("a HUD row timestamp or source event drifted")
        if payload.get("source") != source.payload:
            errors.append("a HUD row did not copy the source payload")
        line = payload.get("line") or ""
        for banned in banned_line:
            if banned.lower() in line.lower():
                errors.append(f"HUD line contains {banned}")
        if payload.get("state") == "settled":
            for side in payload.get("sides") or []:
                if side.get("shape") not in line or side.get("light_slot") not in line:
                    errors.append("settled line dropped a shoulder badge")
        elif payload.get("identity") == "shoulder_badge":
            shape = payload.get("shape")
            slot = payload.get("light_slot")
            if not isinstance(shape, str) or not isinstance(slot, str) or shape not in line or slot not in line:
                errors.append("HUD line dropped shoulder geometry")
            if payload.get("aux_hex") and str(payload["aux_hex"]).lower() in line.lower():
                errors.append("HUD line contains the auxiliary hex")
        blob = json.dumps(payload)
        for banned in (".uasset", "UMG", "WidgetBlueprint", "Texture2D"):
            if banned in blob:
                errors.append(f"HUD payload mentions {banned}")
    if match.holder_errors():
        errors.append("holder audit failed")
    if match.core.holder_id is not None or match.core.anchor != "center":
        errors.append("core did not finish at center with no holder")
    return errors


def acceptance_errors(match: SteelTideMatch | None = None) -> list[str]:
    match = match or run_m2_hud()
    errors = _wiring_errors()
    errors.extend(_geometry_errors(match))
    errors.extend(_scoreboard_errors(match))
    errors.extend(_read_bar_errors(match))
    errors.extend(_spawn_errors(match))
    errors.extend(_lock_errors(match))
    errors.extend(_contract_errors(match))
    return errors


def diff_committed(match: SteelTideMatch | None = None) -> list[str]:
    errors: list[str] = []
    match = match or run_m2_hud()
    if not EVIDENCE_PATH.is_file():
        errors.append("missing docs/evidence/nr-m2-hud/hud.log")
    elif EVIDENCE_PATH.read_text(encoding="utf-8") != render_hud_log(match):
        errors.append("docs/evidence/nr-m2-hud/hud.log drifted")
    if not HEADER_PATH.is_file():
        errors.append("missing NeonRiftHudCues.h")
    else:
        header = HEADER_PATH.read_text(encoding="utf-8")
        for cue_id in catalog_ids():
            if f'TEXT("{cue_id}")' not in header:
                errors.append(f"{cue_id} missing from NeonRiftHudCues.h")
        for banned in (".uasset", "UMG", "WidgetBlueprint", "Texture2D"):
            if banned in header:
                errors.append(f"HUD header mentions {banned}")
    return errors


def write_outputs(match: SteelTideMatch | None = None) -> None:
    match = match or run_m2_hud()
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(render_hud_log(match), encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    args = [] if argv is None else list(argv)
    if args not in ([], ["--check"]):
        print("usage: PYTHONPATH=sim python3 -m steel_tide m2-hud [--check]", flush=True)
        return 2
    match = run_m2_hud()
    errors = acceptance_errors(match)
    if args == ["--check"]:
        errors.extend(diff_committed(match))
    else:
        write_outputs(match)
    flag = "true" if WIRED_INTO_M2_PACK else "false"
    print(f"wired_into_m2_pack={flag}", flush=True)
    if errors:
        print("NR-M2 hud FAIL", flush=True)
        for error in errors:
            print(f"  - {error}", flush=True)
        return 1
    print("NR-M2 hud PASS", flush=True)
    print(
        f"paths={PATH_TEXT} hud_rows={len(match.hud_cues)} events={len(match.events)} "
        f"score=A:{match.score['A']},B:{match.score['B']} settled={match.settled_kind} "
        f"asset=none umg=false texture=none wired_into_m2_pack={flag}",
        flush=True,
    )
    print(f"log={EVIDENCE_PATH.as_posix()}", flush=True)
    if args == ["--check"]:
        print("checked hud log and cue header", flush=True)
    return 0
