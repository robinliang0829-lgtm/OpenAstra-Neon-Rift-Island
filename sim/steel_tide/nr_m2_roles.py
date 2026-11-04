"""NR-M2 roles slice: rush, shield, and scout inside one 3v3.

One command:

    PYTHONPATH=sim python3 -m steel_tide m2-roles
    PYTHONPATH=sim python3 -m steel_tide m2-roles --check

`a2` is the thin digital resident. The other movers stay `local_bot`.
Both decision paths can choose the role ability. This match logs all three
`AbilityUsed` kinds: assault dash (突进 / rush), support shield (支援),
and recon mark (侦察 / scout). Contest, pass, interrupt, first-to-2, and
the 4 second bridge warning are the earlier cards. Decision reasons are
the role ids.
"""

from __future__ import annotations

import math

from .config import CONFIG_PATH, SteelTideConfig, load_config
from .dual_log import compare_dual_logs, diff_against_evidence, render_dual_logs, write_evidence
from .match import SERVER_CLIENT, SteelTideMatch
from .resident_port import DigitalResidentPort
from .nr_m1_bot import BRIDGE_AT_S, INTERRUPT_AFTER_S, _bridge_errors
from .nr_m2_resident import (
    ROSTER,
    _contest_errors,
    _decision_errors,
    _extra,
    _fingerprint,
    _issue,
    _open,
    _pass_errors,
    _roster_errors,
    _score_errors,
)
from .role_ability import COORD_KEYS

SCHEMA = "nr-m2-roles-dual-end-v1"
EVIDENCE_DIR = CONFIG_PATH.parents[1] / "docs" / "evidence" / "nr-m2-roles"
ROLE_ABILITY = {"assault": "dash", "support": "shield", "recon": "mark"}


def run_m2_roles_match(config: SteelTideConfig | None = None) -> SteelTideMatch:
    config = config or load_config()
    port = DigitalResidentPort()
    match = _open(config, port)
    match.resident_port = port
    match.role_abilities_enabled = True
    match.ability_progress = {}
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


def _ability_decisions(match: SteelTideMatch) -> list:
    found = []
    for name in ("BotDecision", "ResidentDecision"):
        for event in match.named(name):
            if event.payload.get("action") == "use_ability":
                found.append(event)
    return found


def _anchors_before(match: SteelTideMatch, event) -> dict[str, str]:
    """Anchors after every earlier event. The event itself has not been applied."""
    anchors = {
        combatant.id: "spawn_a" if combatant.faction == "A" else "spawn_b"
        for combatant in match.combatants.values()
    }
    for item in match.events:
        if item is event:
            break
        if item.name == "MoveCompleted":
            anchors[item.payload["combatant_id"]] = item.payload["to"]
        elif item.name == "AbilityUsed" and item.payload.get("ability") == "dash":
            anchors[item.payload["combatant_id"]] = item.payload["dest"]
    return anchors


def _no_coords(payload: dict) -> bool:
    return COORD_KEYS.isdisjoint(payload)


def _interrupt_errors(match: SteelTideMatch) -> list[str]:
    """The resident card's one interrupt, plus the shield proof hits."""
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
    contest = [cmd for cmd in hits if cmd.t_ms == event.t_ms]
    if len(contest) != 1 or contest[0].client_id != SERVER_CLIENT or contest[0].payload.get("down") is not False:
        errors.append("the channel hit was not one server contact with down false")
    elif contest[0].payload.get("target_id") != "a3":
        errors.append("the channel hit was not aimed at a3")
    if any(cmd.client_id != SERVER_CLIENT or cmd.payload.get("down") is not False for cmd in hits):
        errors.append("a hit was not a server contact with down false")
    if match.named("ActorDowned") or match.named("CoreDropped"):
        errors.append("a hit downed a combatant or dropped the core")
    return errors


def _reason_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    decisions = _ability_decisions(match)
    if not decisions:
        errors.append("no role ability was decided")
        return errors
    kinds = {event.payload.get("ability") for event in match.named("AbilityUsed")}
    if kinds != {"dash", "shield", "mark"}:
        errors.append(f"AbilityUsed kinds {sorted(kinds)} are not dash, shield, and mark")
    controllers = {event.name for event in decisions}
    if controllers != {"BotDecision", "ResidentDecision"}:
        errors.append(f"ability decisions did not come from both controllers: {controllers}")
    reasons = set()
    for event in decisions:
        payload = event.payload
        combatant_id = payload.get("combatant_id")
        role = match.combatants[combatant_id].role if combatant_id in match.combatants else None
        reasons.add(payload.get("reason"))
        if payload.get("reason") != role or payload.get("role") != role:
            errors.append(f"ability reason does not match the role: {payload}")
        elif ROLE_ABILITY.get(role) != payload.get("ability"):
            errors.append(f"ability id does not match the role: {payload}")
        if not _no_coords(payload):
            errors.append(f"ability decision carries coordinates: {payload}")
    if reasons != {"assault", "support", "recon"}:
        errors.append(f"ability reasons were not the three roles: {sorted(reasons)}")
    return errors


def _rush_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    limit = float(config.role_abilities["assault"]["range_m"])
    cooldown_ms = config.seconds_to_ms(config.role_abilities["assault"]["cooldown_seconds"])
    used = [event for event in match.named("AbilityUsed") if event.payload.get("ability") == "dash"]
    if len(used) != 1:
        errors.append(f"expected one short rush, got {len(used)}")
        return errors
    dash = used[0]
    payload = dash.payload
    if payload.get("combatant_id") != "b2" or payload.get("role") != "assault":
        errors.append(f"the rush was not b2's assault dash: {payload}")
    origin = payload.get("from")
    dest = payload.get("dest")
    if origin not in config.anchors or dest not in config.anchors:
        errors.append("the rush did not name two anchors")
    else:
        start = config.anchors[origin]
        end = config.anchors[dest]
        distance = math.hypot(start[0] - end[0], start[1] - end[1])
        if distance > limit or payload.get("range_m") != config.role_abilities["assault"]["range_m"]:
            errors.append(f"the rush was not a hop inside {limit}m")
        if any(
            event.name == "MoveCompleted"
            and event.payload.get("combatant_id") == "b2"
            and event.payload.get("from") == origin
            and event.payload.get("to") == dest
            for event in match.events
        ):
            errors.append("the short hop was walked instead of dashed")
    if payload.get("ready_ms") != dash.t_ms + cooldown_ms:
        errors.append("the rush cooldown was not the configured assault cooldown")
    decided = [
        event
        for event in match.named("BotDecision")
        if event.payload.get("action") == "use_ability"
        and event.payload.get("ability") == "dash"
        and event.payload.get("combatant_id") == "b2"
        and event.t_ms == dash.t_ms
        and event.payload.get("distance_m") is not None
    ]
    if len(decided) != 1 or decided[0].payload.get("reason") != "assault":
        errors.append("the short rush was not one assault BotDecision")
    elif not isinstance(decided[0].payload.get("distance_m"), (int, float)) or decided[0].payload["distance_m"] > limit:
        errors.append("the rush decision distance was over the assault range")
    rejected = [
        event
        for event in match.named("AbilityRejected")
        if event.payload.get("ability") == "dash" and event.payload.get("combatant_id") == "b2"
    ]
    over = [event for event in rejected if event.payload.get("reason") == "out_of_range"]
    cooled = [event for event in rejected if event.payload.get("reason") == "cooldown"]
    if len(over) != 1 or over[0].t_ms >= dash.t_ms:
        errors.append("the over-range rush was not rejected before the short hop")
    elif over[0].payload.get("dest") == dest:
        errors.append("the over-range reject used the short destination")
    else:
        walked = [
            event
            for event in match.named("MoveCompleted")
            if event.payload.get("combatant_id") == "b2" and event.t_ms > over[0].t_ms
        ]
        if not walked or walked[0].payload.get("from") != "spawn_b":
            errors.append("the rejected rush still moved the assault")
    ready_ms = payload.get("ready_ms", 0)
    if len(cooled) != 1 or cooled[0].t_ms < dash.t_ms or cooled[0].t_ms >= ready_ms:
        errors.append("a second rush inside the cooldown was not rejected")
    elif match.events.index(cooled[0]) < match.events.index(dash):
        errors.append("the cooldown reject was logged before the short rush")
    elif cooled[0].payload.get("ready_ms") != ready_ms:
        errors.append("the cooldown reject did not keep the rush ready time")
    if any(event.payload.get("reason") == "holding_core" for event in rejected):
        errors.append("the assault dashed while holding the core, or was rejected for it")
    return errors


def _shield_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    used = [event for event in match.named("AbilityUsed") if event.payload.get("ability") == "shield"]
    if len(used) < 1:
        errors.append("support did not place a shield")
        return errors
    expected = {("a2", "a3", "ResidentDecision"), ("b3", "b2", "BotDecision")}
    seen = set()
    for event in used:
        payload = event.payload
        caster = payload.get("combatant_id")
        target = payload.get("target_id")
        if payload.get("directed_by") != caster or payload.get("role") != "support":
            errors.append(f"shield was not directed by the support: {payload}")
            continue
        caster_faction = match.combatants[caster].faction
        target_faction = match.combatants[target].faction if target in match.combatants else None
        if caster_faction != target_faction:
            errors.append(f"shield covered the other team: {payload}")
        anchors = _anchors_before(match, event)
        caster_anchor = anchors.get(caster)
        target_anchor = anchors.get(target)
        if caster_anchor != target_anchor:
            errors.append(f"shield was not on the same anchor: {caster_anchor} -> {target_anchor}")
        blocked = [
            item
            for item in match.named("HitIgnored")
            if item.t_ms == event.t_ms
            and item.payload.get("reason") == "shield"
            and item.payload.get("target_id") == target
            and item.payload.get("directed_by") == caster
        ]
        if len(blocked) != 1:
            errors.append(f"the directed shield did not block the next hit on {target}")
        source = "ResidentDecision" if caster == "a2" else "BotDecision"
        seen.add((caster, target, source))
        decided = [
            item
            for item in match.named(source)
            if item.payload.get("action") == "use_ability"
            and item.payload.get("ability") == "shield"
            and item.payload.get("combatant_id") == caster
            and item.payload.get("target_id") == target
        ]
        if len(decided) != 1 or decided[0].payload.get("reason") != "support":
            errors.append(f"{caster} did not decide the shield as support")
        elif decided[0].payload.get("distance_m") != 0.0:
            errors.append(f"{caster} shield decision was not range 0")
    if seen != expected:
        errors.append(f"shield pairs drifted: {sorted(seen)}")
    if any(event.payload.get("reason") == "wrong_faction" for event in match.named("AbilityRejected") if event.payload.get("ability") == "shield"):
        errors.append("support attempted a shield on the other team")
    return errors


def _scout_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    rejected = [
        event
        for event in match.named("AbilityRejected")
        if event.payload.get("ability") == "mark" and event.payload.get("reason") == "not_visible"
    ]
    used = [event for event in match.named("AbilityUsed") if event.payload.get("ability") == "mark"]
    if len(rejected) != 1 or len(used) != 1:
        errors.append(f"expected one hidden reject and one visible mark, got {len(rejected)} and {len(used)}")
        return errors
    hidden = rejected[0]
    visible = used[0]
    if hidden.payload.get("combatant_id") != "a3" or visible.payload.get("combatant_id") != "a3":
        errors.append("the scout marks were not a3's recon ability")
    if hidden.payload.get("target_id") != visible.payload.get("target_id"):
        errors.append("the hidden reject and the visible mark were not the same target")
    for event, should_see in ((hidden, False), (visible, True)):
        if not _no_coords(event.payload):
            errors.append(f"mark result carries coordinates: {event.payload}")
        anchors = _anchors_before(match, event)
        observer = anchors.get(event.payload["combatant_id"])
        target = anchors.get(event.payload["target_id"])
        seen = match.anchor_visible(observer, target)
        if seen != should_see:
            errors.append(
                f"mark visibility at {event.t_ms} {event.name} was {seen} for {observer} -> {target}"
            )
    decisions = [
        event
        for event in match.named("BotDecision")
        if event.payload.get("action") == "use_ability"
        and event.payload.get("ability") == "mark"
        and event.payload.get("combatant_id") == "a3"
    ]
    if len(decisions) != 2:
        errors.append("recon did not decide both the hidden mark and the visible mark")
    elif any(event.payload.get("reason") != "recon" or not _no_coords(event.payload) for event in decisions):
        errors.append("a scout decision reason mismatched recon or carried coordinates")
    elif any(event.payload.get("distance_m") is not None for event in decisions):
        errors.append("a scout decision included a distance")
    if hidden.t_ms >= visible.t_ms:
        errors.append("the scout marked a hidden target successfully, or marked before the reject")
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
    errors.extend(_reason_errors(match))
    errors.extend(_rush_errors(match))
    errors.extend(_shield_errors(match))
    errors.extend(_scout_errors(match))
    return errors


def render_slice_logs(match: SteelTideMatch) -> dict[str, str]:
    return render_dual_logs(match, schema=SCHEMA, extra_headers=_extra(match))


def evaluate_slice(match: SteelTideMatch | None = None) -> tuple[dict[str, str], list[str]]:
    match = match or run_m2_roles_match()
    logs = render_slice_logs(match)
    errors = acceptance_errors(match)
    errors.extend(compare_dual_logs(match, logs, schema=SCHEMA, extra_headers=_extra(match)))
    return logs, errors


def main(argv: list[str] | None = None) -> int:
    args = [] if argv is None else list(argv)
    if args not in ([], ["--check"]):
        print("usage: PYTHONPATH=sim python3 -m steel_tide m2-roles [--check]")
        return 2
    match = run_m2_roles_match()
    logs, errors = evaluate_slice(match)
    if args == ["--check"]:
        errors.extend(diff_against_evidence(logs, EVIDENCE_DIR))
    else:
        write_evidence(logs, EVIDENCE_DIR)
    if errors:
        print("NR-M2 roles FAIL")
        for error in errors:
            print(f"  - {error}")
        return 1
    port = match.resident_port
    print("NR-M2 roles PASS")
    print(
        "roster=6 viewpoints=2 local_bots=3 digital_residents=1 "
        f"score=A:{match.score['A']},B:{match.score['B']} settled={match.settled_kind} "
        f"events={len(match.events)} holder={match.core.holder_id} "
        f"select_match={port.select_calls} decide={port.decide_calls}"
    )
    print("rules=contest_core,interrupt_channel,close_range_pass,score_path,assault,support,recon")
    print("abilities=dash,shield,mark")
    for end in ("server", "client-a", "client-b"):
        print(f"{end}={(EVIDENCE_DIR / f'{end}.log').as_posix()}")
    if args == ["--check"]:
        print("checked sample logs")
    return 0
