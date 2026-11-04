"""NR-M1 prep slice: two viewpoints, four local bots, one authoritative sim.

One command:

    PYTHONPATH=sim python3 -m steel_tide m1
    PYTHONPATH=sim python3 -m steel_tide m1 --check

The match object is the only scorer. Respawn, spawn protection, overtime,
side lock, and the three role deltas run here. The 4 second bridge warning
is the NR-03 scheduler (`schedule_bridge_connect`); this slice only aligns
to it. `place_for_test` is not an event.
"""

from __future__ import annotations

import json

from .config import CONFIG_PATH, SteelTideConfig, load_config
from .dual_log import compare_dual_logs, diff_against_evidence, render_dual_logs, render_log, write_evidence
from .match import SERVER_CLIENT, SteelTideMatch
from .model import badge_for
from .palette import BADGES

SCHEMA = "nr-m1-dual-end-v1"
RETIE_SCHEMA = "nr-m1-retie-v1"
EVIDENCE_DIR = CONFIG_PATH.parents[1] / "docs" / "evidence" / "nr-m1"
RETIE_PATH = EVIDENCE_DIR / "retie.log"
SECRET_MARK_KEYS = ("anchor", "location", "pos", "x", "x_m", "y", "y_m")

PROTECT_HIT_S = 1.0
ROUTE_S = 0.4
DASH_S = 4.0
MARK_HIDDEN_S = 5.0
MARK_VISIBLE_S = 5.5
SHIELD_FAR_S = 6.0
SHIELD_S = 6.2
SHIELD_OTHER_HIT_S = 6.4
CONTEST_S = 8.0
CHANNEL_S = 8.2
DROP_S = 9.0
REPICK_S = 9.5
SHIELD_ENEMY_S = 19.0
BRIDGE_AT_S = 20.0
LONG_DASH_S = 21.0
WRONG_ROLE_S = 22.0
OT_BEGIN_S = 361.0

ROSTER = (
    ("a1", "client-a", "humanoid_robot", "human", "A", "assault", "same-face"),
    ("a2", "bot-a2", "humanoid_robot", "local_bot", "A", "support", "same-face"),
    ("a3", "bot-a3", "human", "local_bot", "A", "recon", None),
    ("b1", "client-b", "humanoid_robot", "human", "B", "recon", "same-face"),
    ("b2", "bot-b2", "humanoid_robot", "local_bot", "B", "assault", "same-face"),
    ("b3", "bot-b3", "beast", "local_bot", "B", "support", None),
)


def _respawn_hit_s(config: SteelTideConfig) -> float:
    return DROP_S + config.down_seconds + 0.5


def _extra(match: SteelTideMatch) -> tuple[tuple[str, str], ...]:
    parts = []
    for combatant in sorted(match.combatants.values(), key=lambda item: item.id):
        parts.append(f"{combatant.id}:{combatant.body}:{combatant.faction}:{combatant.controller}")
    return (("identities", ",".join(parts)),)


def _open(config: SteelTideConfig, probe: bool) -> SteelTideMatch:
    match = SteelTideMatch(config)
    for combatant_id, client_id, body, controller, _faction, _role, face in ROSTER:
        match.add_combatant(
            combatant_id,
            client_id,
            body,
            controller,
            face_variant=face,
            preferred_route="repair_alley",
        )
    if probe:
        # Humanoids may take either badge before the lock. Other bodies may not.
        # "scout" is the card name for recon; it is not a second role id.
        match.choose_faction("a1", "B")
        match.choose_faction("a1", "A")
        match.choose_faction("a3", "B")
        match.choose_faction("b3", "A")
        match.choose_faction("b1", "A")
        match.choose_faction("b1", "B")
        match.choose_role("a1", "scout")
    for combatant_id, _client_id, _body, _controller, faction, role, _face in ROSTER:
        match.choose_faction(combatant_id, faction)
        match.choose_role(combatant_id, role)
    match.start()
    if probe:
        match.choose_faction("a1", "B")
        match.choose_role("b1", "assault")
    return match


def run_m1_match(config: SteelTideConfig | None = None) -> SteelTideMatch:
    config = config or load_config()
    match = _open(config, probe=True)
    # NR-03 warning. This does not reimplement the 4 second lead.
    match.schedule_bridge_connect(BRIDGE_AT_S)
    match.enqueue(SERVER_CLIENT, "hit", PROTECT_HIT_S, target_id="a1", down=True)
    match.enqueue("client-a", "set_route", ROUTE_S, combatant_id="a1", route="elevated")
    match.enqueue("bot-b2", "set_route", ROUTE_S, combatant_id="b2", route="elevated")
    match.enqueue("client-a", "use_ability", DASH_S, combatant_id="a1", ability="dash", dest="terminal_a")
    match.enqueue("client-a", "use_ability", DASH_S, combatant_id="a1", ability="dash", dest="bridgehead_a")
    match.enqueue("bot-b2", "use_ability", DASH_S, combatant_id="b2", ability="dash", dest="terminal_b")
    match.advance_to(DASH_S)

    match.place_for_test("b1", "center")
    match.place_for_test("a3", "alley_mid")
    match.enqueue("client-b", "use_ability", MARK_HIDDEN_S, combatant_id="b1", ability="mark", target_id="a3")
    match.advance_to(MARK_HIDDEN_S)
    match.place_for_test("a3", "center")
    match.enqueue("client-b", "use_ability", MARK_VISIBLE_S, combatant_id="b1", ability="mark", target_id="a3")
    match.advance_to(MARK_VISIBLE_S)

    match.enqueue("bot-a2", "use_ability", SHIELD_FAR_S, combatant_id="a2", ability="shield", target_id="a1")
    match.advance_to(SHIELD_FAR_S)
    match.place_for_test("a1", "terminal_a")
    match.place_for_test("a2", "terminal_a")
    match.enqueue("bot-a2", "use_ability", SHIELD_S, combatant_id="a2", ability="shield", target_id="a1")
    match.enqueue(SERVER_CLIENT, "hit", SHIELD_S, target_id="a1", down=True)
    match.enqueue(SERVER_CLIENT, "hit", SHIELD_OTHER_HIT_S, target_id="a2", down=True)
    match.advance_to(SHIELD_OTHER_HIT_S)

    match.place_for_test("a1", "center")
    match.place_for_test("b1", "center")
    match.enqueue("client-a", "pick_core", CONTEST_S, combatant_id="a1")
    match.enqueue("client-b", "pick_core", CONTEST_S, combatant_id="b1")
    match.advance_to(CONTEST_S)
    match.place_for_test("a1", "terminal_b")
    match.enqueue("client-a", "begin_score", CHANNEL_S, combatant_id="a1")
    match.enqueue(SERVER_CLIENT, "hit", DROP_S, target_id="a1", down=True)
    match.advance_to(DROP_S)
    match.place_for_test("b2", "terminal_b")
    match.enqueue("bot-b2", "pick_core", REPICK_S, combatant_id="b2")
    match.advance_to(REPICK_S)

    respawn_hit_s = _respawn_hit_s(config)
    match.enqueue(SERVER_CLIENT, "hit", respawn_hit_s, target_id="a1", down=True)
    match.advance_to(respawn_hit_s)
    match.place_for_test("a2", "center")
    match.enqueue("bot-a2", "use_ability", SHIELD_ENEMY_S, combatant_id="a2", ability="shield", target_id="b1")
    match.advance_to(SHIELD_ENEMY_S)
    match.advance_to(BRIDGE_AT_S)
    match.place_for_test("a1", "bridgehead_a")
    match.enqueue("client-a", "use_ability", LONG_DASH_S, combatant_id="a1", ability="dash", dest="center")
    match.advance_to(LONG_DASH_S)
    match.enqueue("client-a", "use_ability", WRONG_ROLE_S, combatant_id="a1", ability="mark", target_id="b1")
    match.advance_to(WRONG_ROLE_S)

    match.advance_to(config.match_seconds)
    match.choose_faction("a1", "B")
    match.choose_role("a1", "support")
    match.place_for_test("b2", "terminal_a")
    match.enqueue("bot-b2", "begin_score", OT_BEGIN_S, combatant_id="b2")
    match.advance_to(OT_BEGIN_S + config.score_channel_seconds)
    return match


def run_m1_retie(config: SteelTideConfig | None = None) -> SteelTideMatch:
    """Same roster, no point. Overtime expires still tied and draws."""
    config = config or load_config()
    match = _open(config, probe=True)
    match.advance_to(config.match_seconds)
    match.advance_to(config.match_seconds + config.overtime_seconds)
    match.choose_faction("a1", "B")
    match.choose_role("a1", "support")
    return match


def _proposal_errors(config: SteelTideConfig) -> list[str]:
    errors: list[str] = []
    expected = {
        "down_seconds": 5,
        "spawn_protection_seconds": 3,
        "overtime_seconds": 60,
        "bridge_warning_seconds": 4,
        "match_seconds": 360,
        "points_to_win": 2,
        "score_channel_seconds": 3,
        "team_size": 3,
    }
    for key, value in expected.items():
        if getattr(config, key) != value:
            errors.append(f"greybox {key} is {getattr(config, key)}, M1 prep expects {value}")
    abilities = config.role_abilities
    if set(abilities) != {"assault", "support", "recon"}:
        errors.append(f"roles drifted: {sorted(abilities)}")
    else:
        if abilities["assault"]["id"] != "dash" or abilities["assault"]["range_m"] != 12:
            errors.append("assault is not the 12m dash")
        if abilities["assault"]["cooldown_seconds"] != 8:
            errors.append("assault cooldown drifted")
        if abilities["support"]["id"] != "shield" or abilities["support"]["range_m"] != 0:
            errors.append("support shield range drifted")
        if abilities["support"]["cooldown_seconds"] != 12:
            errors.append("support cooldown drifted")
        if abilities["recon"]["id"] != "mark":
            errors.append("recon mark id drifted")
        labels = {role: spec["label_zh"] for role, spec in abilities.items()}
        if labels != {"assault": "突进", "support": "支援", "recon": "侦察"}:
            errors.append(f"role labels drifted: {labels}")
    raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if raw.get("controllers") != ["human", "digital_resident", "local_bot"]:
        errors.append("controllers are not the three stored kinds")
    return errors


def _roster_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
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
    for combatant_id in ("a1", "a2", "b1", "b2"):
        combatant = match.combatants[combatant_id]
        if combatant.body != "humanoid_robot" or combatant.face_variant != "same-face":
            errors.append(f"{combatant_id} is not the shared humanoid body")
    if match.combatants["a1"].faction == match.combatants["b1"].faction:
        errors.append("the two humanoids picked the same faction")
    roles = {
        "A": sorted(c.role for c in match.combatants.values() if c.faction == "A"),
        "B": sorted(c.role for c in match.combatants.values() if c.faction == "B"),
    }
    if roles["A"] != ["assault", "recon", "support"] or roles["B"] != ["assault", "recon", "support"]:
        errors.append(f"each side needs assault, support, and recon: {roles}")
    badge_a = badge_for("A", config.badges, "other-face")
    badge_b = badge_for("B", config.badges, "same-face")
    if badge_a["shape"] != BADGES["A"]["shape"] or badge_b["shape"] != BADGES["B"]["shape"]:
        errors.append("match badges drifted from the NR-03 palette")
    if badge_a["shape"] == badge_b["shape"] or badge_a["light_slot"] == badge_b["light_slot"]:
        errors.append("A and B badges are not distinct once color is ignored")
    if badge_a["shape"] != "open_chevron" or badge_b["shape"] != "closed_ring":
        errors.append("humanoid badges are not the NR-03 chevron and ring")
    return errors


def _identity_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    locked = match.named("FactionsLocked")
    if len(locked) != 1:
        errors.append(f"expected one FactionsLocked, got {len(locked)}")
        return errors
    identities = locked[0].payload.get("identities")
    if not isinstance(identities, dict):
        errors.append("FactionsLocked has no identities")
        return errors
    for combatant in match.combatants.values():
        stored = identities.get(combatant.id)
        if stored != {"body": combatant.body, "controller": combatant.controller, "faction": combatant.faction}:
            errors.append(f"{combatant.id} identity was not stored as body, faction, controller")
        if combatant.body == combatant.controller or combatant.body == combatant.faction:
            errors.append(f"{combatant.id} collapsed body into faction or controller")
        if not combatant.body or not combatant.faction or not combatant.controller:
            errors.append(f"{combatant.id} is missing one of the three fields")
    if match.combatants["a3"].body != "human" or match.combatants["a3"].controller != "local_bot":
        errors.append("a3 does not keep a human body on a local-bot controller")
    if match.combatants["b3"].body != "beast" or match.combatants["b3"].faction != "B":
        errors.append("beast was not stored as body B")
    chosen = [event.payload.get("faction") for event in match.named("FactionChosen") if event.payload.get("combatant_id") == "a1"]
    if "A" not in chosen or "B" not in chosen:
        errors.append("humanoid a1 could not choose both badges before the lock")
    illegal = [
        (event.payload.get("combatant_id"), event.payload.get("faction"))
        for event in match.named("FactionRejected")
        if event.payload.get("reason") == "illegal_faction"
    ]
    if sorted(illegal) != [("a3", "B"), ("b3", "A")]:
        errors.append(f"illegal body choices drifted: {illegal}")
    if match.combatants["a1"].faction != "A" or match.combatants["b1"].faction != "B":
        errors.append("lock did not keep the final humanoid sides")
    if not _at(match, "FactionRejected", 0, combatant_id="a1", reason="locked"):
        errors.append("faction was not locked when the match started")
    if not _at(match, "FactionRejected", match.config.match_ms, combatant_id="a1", reason="locked"):
        errors.append("faction was not locked at the overtime clock")
    if match.lobby_open:
        errors.append("lobby stayed open after the lock")
    return errors


def _at(match: SteelTideMatch, name: str, t_ms: int, **payload) -> list:
    found = []
    for event in match.named(name):
        if event.t_ms != t_ms:
            continue
        if all(event.payload.get(key) == value for key, value in payload.items()):
            found.append(event)
    return found


def _mark_leaks(payload: dict) -> list[str]:
    return [key for key in SECRET_MARK_KEYS if key in payload]


def _role_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    dash_ms = config.seconds_to_ms(DASH_S)
    short = _at(match, "AbilityUsed", dash_ms, ability="dash", combatant_id="a1")
    if len(short) != 1 or short[0].payload.get("from") != "spawn_a" or short[0].payload.get("dest") != "terminal_a":
        errors.append("assault did not dash the short spawn_a to terminal_a hop")
    elif short[0].payload.get("range_m") != config.role_abilities["assault"]["range_m"]:
        errors.append("dash did not publish its short range")
    other = _at(match, "AbilityUsed", dash_ms, ability="dash", combatant_id="b2")
    if len(other) != 1 or other[0].payload.get("from") != "spawn_b" or other[0].payload.get("dest") != "terminal_b":
        errors.append("the other side's assault did not dash the short hop")
    cooled = _at(match, "AbilityRejected", dash_ms, ability="dash", combatant_id="a1", reason="cooldown")
    if len(cooled) != 1:
        errors.append("a second dash on the same frame was not cooling down")
    long_ms = config.seconds_to_ms(LONG_DASH_S)
    long = _at(match, "AbilityRejected", long_ms, ability="dash", combatant_id="a1", reason="out_of_range")
    if len(long) != 1 or long[0].payload.get("dest") != "center":
        errors.append("the bridge span was not rejected as longer than the dash")
    elif match.combatants["a1"].anchor != "bridgehead_a":
        errors.append("the rejected long dash still moved the assault")
    hidden_ms = config.seconds_to_ms(MARK_HIDDEN_S)
    hidden = _at(match, "AbilityRejected", hidden_ms, ability="mark", reason="not_visible", target_id="a3")
    if len(hidden) != 1:
        errors.append("scout marked a target standing in the alley")
    elif _mark_leaks(hidden[0].payload):
        errors.append(f"covered mark leaked coordinates: {_mark_leaks(hidden[0].payload)}")
    visible_ms = config.seconds_to_ms(MARK_VISIBLE_S)
    visible = _at(match, "AbilityUsed", visible_ms, ability="mark", combatant_id="b1", target_id="a3")
    if len(visible) != 1:
        errors.append("scout did not mark the visible target")
    elif _mark_leaks(visible[0].payload):
        errors.append(f"visible mark leaked coordinates: {_mark_leaks(visible[0].payload)}")
    if not any(event.payload.get("role") == "scout" and event.payload.get("reason") == "unknown_role" for event in match.named("RoleRejected")):
        errors.append("scout was accepted as a role id; the id is recon")
    far = _at(match, "AbilityRejected", config.seconds_to_ms(SHIELD_FAR_S), ability="shield", reason="out_of_range", target_id="a1")
    if len(far) != 1:
        errors.append("support shield traveled farther than range_m 0")
    shielded = _at(match, "AbilityUsed", config.seconds_to_ms(SHIELD_S), ability="shield", combatant_id="a2", target_id="a1")
    if len(shielded) != 1 or shielded[0].payload.get("directed_by") != "a2":
        errors.append("support did not place a shield on the named teammate")
    blocked = _at(match, "HitIgnored", config.seconds_to_ms(SHIELD_S), reason="shield", target_id="a1", directed_by="a2")
    if len(blocked) != 1:
        errors.append("the directed shield did not stop the named target's hit")
    if _at(match, "ActorDowned", config.seconds_to_ms(SHIELD_S), combatant_id="a1"):
        errors.append("the shielded assault was still downed")
    support_down = _at(match, "ActorDowned", config.seconds_to_ms(SHIELD_OTHER_HIT_S), combatant_id="a2")
    if len(support_down) != 1:
        errors.append("the shield covered the support as well as the named target")
    enemy = _at(
        match,
        "AbilityRejected",
        config.seconds_to_ms(SHIELD_ENEMY_S),
        ability="shield",
        combatant_id="a2",
        reason="wrong_faction",
        target_id="b1",
    )
    if len(enemy) != 1:
        errors.append("support shield was accepted on the other team")
    wrong = _at(match, "AbilityRejected", config.seconds_to_ms(WRONG_ROLE_S), ability="mark", combatant_id="a1", reason="wrong_role")
    if len(wrong) != 1:
        errors.append("assault was allowed to mark")
    return errors


def _core_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    contest_ms = config.seconds_to_ms(CONTEST_S)
    drop_ms = config.seconds_to_ms(DROP_S)
    repick_ms = config.seconds_to_ms(REPICK_S)
    respawn_ms = drop_ms + config.down_ms
    protect_ms = config.seconds_to_ms(_respawn_hit_s(config))
    opening = _at(match, "HitIgnored", config.seconds_to_ms(PROTECT_HIT_S), reason="spawn_protection", target_id="a1")
    if len(opening) != 1:
        errors.append("opening spawn protection did not ignore the hit")
    if _at(match, "ActorDowned", config.seconds_to_ms(PROTECT_HIT_S)):
        errors.append("spawn protection still downed the target")
    picked = _at(match, "CorePicked", contest_ms, combatant_id="a1")
    rejected = _at(match, "CorePickRejected", contest_ms, combatant_id="b1", reason="already_held")
    if len(picked) != 1 or len(rejected) != 1:
        errors.append("same-frame contest did not keep a single holder")
    interrupted = _at(match, "ScoreChannelInterrupted", drop_ms, combatant_id="a1", reason="hit")
    if len(interrupted) != 1:
        errors.append("the channel was not interrupted by the downing hit")
    if any(event.name == "PointScored" and event.t_ms == drop_ms for event in match.events):
        errors.append("the interrupted channel scored")
    drops = [event for event in match.named("CoreDropped") if event.payload.get("reason") == "downed"]
    if len(drops) != 1 or drops[0].t_ms != drop_ms or drops[0].payload.get("combatant_id") != "a1":
        errors.append("the downed carrier did not drop the core")
    elif drops[0].payload.get("anchor") != "terminal_b":
        errors.append("the dropped core did not stay at the down site")
    else:
        down_index = next(
            index
            for index, event in enumerate(match.events)
            if event.name == "ActorDowned" and event.payload.get("combatant_id") == "a1"
        )
        drop_index = match.events.index(drops[0])
        if drop_index > down_index:
            errors.append("ActorDowned was emitted before the core drop")
    downed = _at(match, "ActorDowned", drop_ms, combatant_id="a1")
    if len(downed) != 1 or downed[0].payload.get("respawn_ms") != respawn_ms:
        errors.append("down duration was not down_seconds")
    respawned = _at(match, "ActorRespawned", respawn_ms, combatant_id="a1", anchor="spawn_a")
    if len(respawned) != 1:
        errors.append("carrier did not respawn at the faction spawn")
    elif respawned[0].payload.get("protection_until_ms") != respawn_ms + config.spawn_protection_ms:
        errors.append("respawn did not start spawn protection")
    again = _at(match, "CorePicked", repick_ms, combatant_id="b2", anchor="terminal_b")
    if len(again) != 1 or again[0].t_ms <= drop_ms:
        errors.append("the grounded core was not picked up again")
    later = _at(match, "HitIgnored", protect_ms, reason="spawn_protection", target_id="a1")
    if len(later) != 1:
        errors.append("respawn protection did not ignore the next hit")
    if any(event.name == "CoreDropped" and event.t_ms == protect_ms for event in match.events):
        errors.append("spawn protection dropped the core")
    if len(match.named("CoreDropped")) != 1:
        errors.append("a respawn or a shielded hit dropped another core")
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


def _overtime_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    clock_ms = config.match_ms
    point_ms = config.seconds_to_ms(OT_BEGIN_S + config.score_channel_seconds)
    deadline_ms = clock_ms + config.overtime_ms
    started = match.named("OvertimeStarted")
    if len(started) != 1 or started[0].t_ms != clock_ms:
        errors.append("overtime did not start on the tied regulation clock")
    elif started[0].payload.get("score") != {"A": 0, "B": 0} or started[0].payload.get("deadline_ms") != deadline_ms:
        errors.append(f"overtime payload drifted: {started[0].payload}")
    elif started[0].payload.get("role_select_open") is not False:
        errors.append("overtime reopened role select")
    scored = match.named("PointScored")
    if len(scored) != 1:
        errors.append(f"expected the single overtime point, got {len(scored)}")
    elif scored[0].t_ms != point_ms or scored[0].payload.get("faction") != "B" or scored[0].payload.get("score") != {"A": 0, "B": 1}:
        errors.append(f"overtime point drifted: {scored[0].to_dict() if scored else None}")
    elif scored[0].t_ms >= deadline_ms:
        errors.append("the first overtime point waited for the buzzer")
    settled = match.named("MatchSettled")
    if len(settled) != 1 or settled[0].t_ms != point_ms:
        errors.append("the first lead did not settle on the scoring timestamp")
    elif settled[0].payload.get("kind") != "score" or settled[0].payload.get("winner") != "B":
        errors.append(f"first lead should settle as score winner B: {settled[0].payload if settled else None}")
    elif settled[0].payload.get("role_select_open") is not False:
        errors.append("settlement reopened role select")
    if match.phase != "settled" or match.settled_kind != "score" or match.score != {"A": 0, "B": 1}:
        errors.append(f"slice ended phase={match.phase} kind={match.settled_kind} score={match.score}")
    if match.t_ms != point_ms:
        errors.append(f"match kept running to {match.t_ms} after the first overtime point")
    if match.core.holder_id is not None or match.core.anchor != "center":
        errors.append("the scoring core did not return to center")
    if any(event.payload.get("reason") != "locked" for event in match.named("RoleRejected") if event.t_ms >= clock_ms):
        errors.append("a role change was accepted at the overtime clock")
    if match.combatants["a1"].faction != "A" or match.combatants["a1"].role != "assault":
        errors.append("overtime rewrote the locked loadout")
    early_points = [event for event in scored if event.t_ms <= clock_ms] if scored else []
    if early_points:
        errors.append("a point landed before overtime, so the entry was not a tie")
    return errors


def acceptance_errors(match: SteelTideMatch) -> list[str]:
    errors = match.holder_errors()
    errors.extend(_proposal_errors(match.config))
    errors.extend(_roster_errors(match))
    errors.extend(_identity_errors(match))
    errors.extend(_role_errors(match))
    errors.extend(_core_errors(match))
    errors.extend(_bridge_errors(match))
    errors.extend(_overtime_errors(match))
    return errors


def acceptance_retie(match: SteelTideMatch) -> list[str]:
    errors = match.holder_errors()
    config = match.config
    clock_ms = config.match_ms
    end_ms = clock_ms + config.overtime_ms
    if config.overtime_seconds != 60 or config.match_seconds != 360:
        errors.append("retie did not use the 360s clock and 60s overtime")
    started = match.named("OvertimeStarted")
    if len(started) != 1 or started[0].t_ms != clock_ms or started[0].payload.get("deadline_ms") != end_ms:
        errors.append("retie did not enter one 60s overtime from a tie")
    elif started[0].payload.get("score") != {"A": 0, "B": 0}:
        errors.append("retie overtime did not start from 0-0")
    if match.named("PointScored"):
        errors.append("retie awarded a point")
    settled = match.named("MatchSettled")
    if len(settled) != 1 or settled[0].t_ms != end_ms:
        errors.append("retie did not draw on the overtime buzzer")
    elif settled[0].payload.get("kind") != "draw" or settled[0].payload.get("winner") is not None:
        errors.append(f"buzzer settle drifted: {settled[0].payload}")
    elif settled[0].payload.get("score") != {"A": 0, "B": 0}:
        errors.append("buzzer draw changed the score")
    if match.phase != "settled" or match.settled_kind != "draw" or match.t_ms != end_ms:
        errors.append(f"retie phase={match.phase} kind={match.settled_kind} t={match.t_ms}")
    if len(match.named("OvertimeStarted")) != 1:
        errors.append("a second overtime started")
    if match.combatants["a1"].faction != "A" or match.combatants["a1"].role != "assault":
        errors.append("the draw reopened side or role select")
    if not any(event.t_ms == end_ms and event.payload.get("reason") == "locked" for event in match.named("FactionRejected")):
        errors.append("faction was not locked after the draw")
    identities = match.named("FactionsLocked")[0].payload["identities"]
    for combatant in match.combatants.values():
        if identities[combatant.id]["body"] != combatant.body or identities[combatant.id]["controller"] != combatant.controller:
            errors.append(f"{combatant.id} body or controller changed across the draw")
    return errors


def _pair(config: SteelTideConfig) -> SteelTideMatch:
    match = SteelTideMatch(config)
    match.add_combatant("a1", "client-a", "humanoid_robot", "human", face_variant="same-face")
    match.add_combatant("b1", "client-b", "humanoid_robot", "human", face_variant="same-face")
    match.choose_faction("a1", "A")
    match.choose_faction("b1", "B")
    match.choose_role("a1", "assault")
    match.choose_role("b1", "assault")
    match.start()
    return match


def _score_point(match: SteelTideMatch, combatant_id: str, client_id: str, pick_s: float, begin_s: float) -> None:
    combatant = match.combatants[combatant_id]
    terminal = match.config.score_terminal[combatant.faction or ""]
    match.place_for_test(combatant_id, "center")
    match.enqueue(client_id, "pick_core", pick_s, combatant_id=combatant_id)
    match.advance_to(pick_s)
    match.place_for_test(combatant_id, terminal)
    match.enqueue(client_id, "begin_score", begin_s, combatant_id=combatant_id)
    match.advance_to(begin_s + match.config.score_channel_seconds)


def check_lead_skips_overtime() -> list[str]:
    config = load_config()
    config.match_seconds = 8
    match = _pair(config)
    _score_point(match, "a1", "client-a", 0.5, 1.0)
    match.advance_to(8)
    errors = match.holder_errors()
    if match.named("OvertimeStarted"):
        errors.append("a regulation lead opened overtime")
    settled = match.named("MatchSettled")
    if len(settled) != 1 or settled[0].t_ms != 8000 or settled[0].payload.get("kind") != "score":
        errors.append("regulation lead did not settle as score on the clock")
    elif settled[0].payload.get("winner") != "A" or match.score != {"A": 1, "B": 0}:
        errors.append("regulation lead winner drifted")
    return errors


def check_overtime_points_cap() -> list[str]:
    config = load_config()
    config.match_seconds = 20
    match = _pair(config)
    _score_point(match, "a1", "client-a", 0.5, 1.0)
    _score_point(match, "b1", "client-b", 5.0, 6.0)
    match.advance_to(20)
    errors = match.holder_errors()
    started = match.named("OvertimeStarted")
    if len(started) != 1 or started[0].payload.get("score") != {"A": 1, "B": 1}:
        errors.append("1-1 did not enter overtime")
    elif started[0].payload.get("deadline_ms") != 80000:
        errors.append("points-cap check shortened the 60s overtime")
    _score_point(match, "a1", "client-a", 21.0, 22.0)
    errors.extend(match.holder_errors())
    settled = match.named("MatchSettled")
    if len(settled) != 1 or settled[0].payload.get("kind") != "points" or settled[0].payload.get("winner") != "A":
        errors.append("reaching points_to_win during overtime did not settle as points")
    elif settled[0].t_ms != 25000 or match.score != {"A": 2, "B": 1}:
        errors.append("points cap did not end on that score")
    elif settled[0].t_ms >= 80000:
        errors.append("points cap waited for the overtime buzzer")
    return errors


def check_retie_point_draws() -> list[str]:
    """A point that restores a tie ends overtime immediately as a draw.

    One core cannot do this from a tied entry, because that point always
    creates a lead. The planted score is only here so the branch stays tested.
    """
    config = load_config()
    config.match_seconds = 5
    match = _pair(config)
    match.advance_to(5)
    errors = match.holder_errors()
    if match.phase != "overtime" or match.score != {"A": 0, "B": 0}:
        errors.append("retie-point setup did not enter overtime tied")
        return errors
    match.score["A"] = 1
    _score_point(match, "b1", "client-b", 6.0, 7.0)
    errors.extend(match.holder_errors())
    settled = match.named("MatchSettled")
    if len(settled) != 1 or settled[0].t_ms != 10000 or settled[0].payload.get("kind") != "draw":
        errors.append("a point that restored the tie did not draw immediately")
    elif settled[0].payload.get("winner") is not None or match.score != {"A": 1, "B": 1}:
        errors.append("retie draw named a winner or a different score")
    elif match.t_ms != 10000 or match.t_ms >= 65000:
        errors.append("retie draw waited out the 60s")
    if len(match.named("OvertimeStarted")) != 1:
        errors.append("retie draw opened another overtime")
    match.choose_role("a1", "support")
    if not any(event.payload.get("reason") == "locked" for event in match.named("RoleRejected")):
        errors.append("retie draw reopened roles")
    return errors


def rule_errors() -> list[str]:
    errors = [f"lead: {item}" for item in check_lead_skips_overtime()]
    errors.extend(f"points: {item}" for item in check_overtime_points_cap())
    errors.extend(f"retie-point: {item}" for item in check_retie_point_draws())
    return errors


def render_slice_logs(match: SteelTideMatch) -> dict[str, str]:
    extra = _extra(match)
    return render_dual_logs(match, schema=SCHEMA, extra_headers=extra)


def render_retie(match: SteelTideMatch) -> str:
    return render_log(match, "server", schema=RETIE_SCHEMA, extra_headers=_extra(match))


def evaluate_slice(match: SteelTideMatch | None = None) -> tuple[dict[str, str], list[str]]:
    match = match or run_m1_match()
    logs = render_slice_logs(match)
    errors = acceptance_errors(match)
    errors.extend(compare_dual_logs(match, logs, schema=SCHEMA, extra_headers=_extra(match)))
    return logs, errors


def diff_retie(text: str) -> list[str]:
    if not RETIE_PATH.is_file():
        return [f"missing sample log {RETIE_PATH}"]
    on_disk = RETIE_PATH.read_text(encoding="utf-8")
    if on_disk != text:
        return [f"sample log drifted: {RETIE_PATH}"]
    return []


def write_retie(text: str) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    RETIE_PATH.write_text(text, encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    args = [] if argv is None else list(argv)
    if args not in ([], ["--check"]):
        print("usage: PYTHONPATH=sim python3 -m steel_tide m1 [--check]")
        return 2
    match = run_m1_match()
    logs, errors = evaluate_slice(match)
    retie = run_m1_retie()
    retie_text = render_retie(retie)
    errors.extend(acceptance_retie(retie))
    errors.extend(rule_errors())
    if args == ["--check"]:
        errors.extend(diff_against_evidence(logs, EVIDENCE_DIR))
        errors.extend(diff_retie(retie_text))
    else:
        write_evidence(logs, EVIDENCE_DIR)
        write_retie(retie_text)
    if errors:
        print("NR-M1 prep FAIL")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("NR-M1 prep PASS")
    print(
        "roster=6 viewpoints=2 local_bots=4 "
        f"score=A:{match.score['A']},B:{match.score['B']} settled={match.settled_kind} "
        f"events={len(match.events)} holder={match.core.holder_id}"
    )
    print(f"retie=draw t={retie.t_ms / 1000:.3f}s events={len(retie.events)}")
    print("rules=lead,first_score,points_cap,retie_point,buzzer")
    for end in ("server", "client-a", "client-b"):
        print(f"{end}={(EVIDENCE_DIR / f'{end}.log').as_posix()}")
    print(f"retie={RETIE_PATH.as_posix()}")
    if args == ["--check"]:
        print("checked sample logs")
    return 0
