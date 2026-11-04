"""NR-M2 light cue slice. Headless contract, not a lit level.

One command:

    PYTHONPATH=sim python3 -m steel_tide m2-light
    PYTHONPATH=sim python3 -m steel_tide m2-light --check

The match object remains the only scorer. This slice places same-body
humanoids, then runs one protected hit, one terminal read-bar, one score,
and the NR-03 bridge schedulers. `LightCue` rows are a side log. They are
not in `EVENT_NAMES` and they are not in `match.events`.

Not a step of `m2-pack`. The pack's unittest step still imports the tests
for this module. Pack evidence stays the rules chain. Lighting parameters
live in `config/steel_tide_greybox.json` and this check reads them. The
pack command does not rewrite that file.
"""

from __future__ import annotations

import json

from .config import CONFIG_PATH, load_config
from .events import EVENT_NAMES
from .light import (
    BRIDGE_CONNECT,
    BRIDGE_DISCONNECT,
    BRIDGE_RAMP,
    READ_BAR,
    SCORE,
    SPAWN_PROTECTION,
    catalog_ids,
    shoulder_cue_id_for,
)
from .match import SERVER_CLIENT, SteelTideMatch
from .model import Event
from .palette import BADGES, PALETTE, badge_identity, badge_svg, colorblind_badge, greyscale_badge

ROOT = CONFIG_PATH.parents[1]
EVIDENCE_PATH = ROOT / "docs" / "evidence" / "nr-m2-light" / "light.log"
HEADER_PATH = ROOT / "Source" / "NeonRift" / "Public" / "NeonRiftLightCues.h"
SCHEMA = "nr-m2-light-cues-v1"

# Schedule points only. The 4 second lead stays inside schedule_bridge_connect.
CONNECT_AT_S = 16.0
DISCONNECT_AT_S = 18.0
COLORBLIND_MODES = ("protanopia", "deuteranopia", "tritanopia")


def run_m2_light(config=None) -> SteelTideMatch:
    """Same-body A and B, one of each required cue, on the NR-03 bridge clock."""
    match = SteelTideMatch(config or load_config())
    for combatant_id, client_id, faction, role in (
        ("a1", "client-a", "A", "assault"),
        ("a2", "client-a2", "A", "support"),
        ("b1", "client-b", "B", "assault"),
    ):
        match.add_combatant(
            combatant_id,
            client_id,
            "humanoid_robot",
            "human",
            face_variant="plate-7",
        )
        match.choose_faction(combatant_id, faction)
        match.choose_role(combatant_id, role)
    match.schedule_bridge_connect(CONNECT_AT_S)
    match.schedule_bridge_disconnect(DISCONNECT_AT_S)
    match.start()
    match.enqueue(SERVER_CLIENT, "hit", 0.5, target_id="a1", down=True)
    match.advance_to(0.5)
    match.place_for_test("a1", "terminal_b")
    match.enqueue("client-a", "begin_score", 3.2, combatant_id="a1")
    match.advance_to(3.2)
    match.place_for_test("a1", "center")
    match.enqueue("client-a", "pick_core", 3.5, combatant_id="a1")
    match.advance_to(3.5)
    match.place_for_test("a1", "terminal_b")
    match.enqueue("client-a", "begin_score", 4.0, combatant_id="a1")
    match.advance_to(DISCONNECT_AT_S)
    return match


def render_light_log(match: SteelTideMatch) -> str:
    lighting = match.config.lighting
    holder = "-" if match.core.holder_id is None else match.core.holder_id
    lines = [
        f"# schema {SCHEMA}",
        "# authority sim/steel_tide",
        "# kind light-cue-contract",
        "# asset none",
        "# texture none",
        "# lumen false",
        "# uasset false",
        "# bridge_ruleset nr03",
        "# color_is_identity false",
        "# wired_into_m2_pack false",
        "# pack_wiring side-log-only; unittest still runs test_nr_m2_light.py",
        f"# bridge_warning_seconds {match.config.bridge_warning_seconds:g}",
        f"# day_port_intensity {lighting.day_port_intensity:g}",
        f"# night_port_intensity {lighting.night_port_intensity:g}",
        f"# shoulder_intensity {lighting.shoulder_intensity:g}",
        f"# min_readable_contrast {lighting.min_readable_contrast:g}",
        f"# color_assist {str(lighting.color_assist).lower()}",
        f"# score A={match.score['A']} B={match.score['B']}",
        f"# holder {holder}",
        f"# phase {match.phase}",
    ]
    for cue in match.light_cues:
        lines.append(cue.format())
    return "\n".join(lines) + "\n"


def _cues(match: SteelTideMatch, cue_id: str) -> list[Event]:
    return [cue for cue in match.light_cues if cue.payload.get("cue_id") == cue_id]


def _source(match: SteelTideMatch, cue: Event) -> Event:
    return match.events[cue.payload["source_index"]]


def _shoulder_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    lighting = match.config.lighting
    raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    block = raw.get("lighting")
    if not isinstance(block, dict):
        errors.append("config is missing the lighting block")
        return errors
    if block.get("day_port_intensity") != lighting.day_port_intensity:
        errors.append("day_port_intensity drifted from the config file")
    if block.get("night_port_intensity") != lighting.night_port_intensity:
        errors.append("night_port_intensity drifted from the config file")
    if lighting.day_port_intensity <= lighting.night_port_intensity:
        errors.append("day port is not brighter than night port")
    if shoulder_cue_id_for("A") == shoulder_cue_id_for("B"):
        errors.append("shoulder cue ids are not split")
    for faction, slot in (("A", "shoulder_left"), ("B", "shoulder_right")):
        badge = BADGES[faction]
        config_badge = match.config.badges[faction]
        if config_badge["light_slot"] != slot or badge["light_slot"] != slot:
            errors.append(f"{faction} lamp is not {slot}")
        expected = shoulder_cue_id_for(faction)
        if badge["shape"] not in expected or slot not in expected:
            errors.append(f"{faction} cue id dropped shape or slot")
        if PALETTE[badge["aux"]]["hex"].lower() in expected.lower():
            errors.append(f"{faction} cue id contains the auxiliary hex")
        if badge["aux"] in expected:
            errors.append(f"{faction} cue id contains the auxiliary token")
        painted = badge_svg(faction).replace(PALETTE[badge["aux"]]["hex"], "#808080")
        if badge_identity(painted) != (badge["shape"], badge["light_slot"]):
            errors.append(f"painting {faction} changed the lamp slot")
        masked = [greyscale_badge(badge_svg(faction))]
        masked.extend(colorblind_badge(badge_svg(faction), mode) for mode in COLORBLIND_MODES)
        for variant in masked:
            if badge_identity(variant) != (badge["shape"], badge["light_slot"]):
                errors.append(f"color mask changed {faction} shape or lamp slot")
    a1 = match.combatants["a1"]
    b1 = match.combatants["b1"]
    if a1.body != b1.body or a1.face_variant != b1.face_variant:
        errors.append("A and B humanoids were split by body")
    rows = [cue for cue in match.light_cues if cue.payload.get("family") == "shoulder"]
    if [cue.payload.get("combatant_id") for cue in rows] != ["a1", "a2", "b1"]:
        errors.append("shoulder cues are not one row per locked combatant")
    seen: dict[str, str] = {}
    for cue in rows:
        faction = cue.payload.get("faction")
        cue_id = cue.payload.get("cue_id")
        if faction not in ("A", "B") or cue_id != shoulder_cue_id_for(faction):
            errors.append(f"shoulder cue {cue_id} is not the NR-03 id for {faction}")
            continue
        if cue.payload.get("light_slot") != BADGES[faction]["light_slot"]:
            errors.append("shoulder cue slot drifted from the badge")
        if cue.payload.get("shape") != BADGES[faction]["shape"]:
            errors.append("shoulder cue shape drifted from the badge")
        if cue.payload.get("color_role") != "auxiliary" or cue.payload.get("color_is_identity") is not False:
            errors.append("shoulder color is not marked auxiliary")
        if cue.payload.get("color_assist") is not True:
            errors.append("color assist flag was dropped")
        if cue.payload.get("intensity") != lighting.shoulder_intensity:
            errors.append("shoulder intensity is not the config value")
        if cue.payload.get("readable_day") is not True or cue.payload.get("readable_night") is not True:
            errors.append(f"{faction} shoulder lamp is not readable in day port and night port")
        if "face" in json.dumps(cue.payload).lower():
            errors.append("shoulder cue mentions a face")
        seen[faction] = cue_id
        if _source(match, cue).name != "FactionsLocked" or cue.t_ms != 0:
            errors.append("shoulder cue is not on the faction lock")
    if seen.get("A") == seen.get("B") or set(seen) != {"A", "B"}:
        errors.append("locked roster did not emit both shoulder slots")
    slots = {cue.payload.get("light_slot") for cue in rows}
    if slots != {"shoulder_left", "shoulder_right"}:
        errors.append(f"slots {slots} are not the two lamp sides")
    return errors


def _bridge_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    if config.bridge_warning_seconds != 4 or config.bridge_warning_ms != 4000:
        errors.append("bridge warning is not the configured 4 seconds")
    started = match.named("BridgeWarningStarted")
    advances = match.named("BridgeLightStripAdvanced")
    completed = match.named("BridgeWarningCompleted")
    connected = [event for event in match.named("BridgeStateChanged") if event.payload.get("state") == "connected"]
    disconnected = [
        event for event in match.named("BridgeStateChanged") if event.payload.get("state") == "disconnected"
    ]
    ramps = _cues(match, BRIDGE_RAMP)
    connects = _cues(match, BRIDGE_CONNECT)
    disconnects = _cues(match, BRIDGE_DISCONNECT)
    if len(started) != 1 or len(completed) != 1 or len(connected) != 1 or len(disconnected) != 1:
        errors.append("bridge slice did not emit one warn, one complete, one connect, one disconnect")
        return errors
    if len(connects) != 1 or len(disconnects) != 1:
        errors.append("bridge cue counts are not one connect and one disconnect")
        return errors
    start = started[0]
    done = completed[0]
    connect = connected[0]
    disconnect = disconnected[0]
    expected_rows = [start, *advances, done]
    if len(ramps) != len(expected_rows) or len(advances) != 3:
        errors.append("light-strip ramp is not one cue per strip event")
        return errors
    if any(_source(match, cue) is not event or cue.t_ms != event.t_ms for cue, event in zip(ramps, expected_rows)):
        errors.append("a ramp cue missed its BridgeLightStrip timestamp")
    if [cue.payload.get("strip_index") for cue in ramps] != [0, 1, 2, 3, 4]:
        errors.append("ramp indexes are not the five NR-03 lamps")
    if [cue.t_ms - start.t_ms for cue in ramps] != [0, 1000, 2000, 3000, 4000]:
        errors.append("ramp is not the 4 second NR-03 cadence")
    if any(cue.payload.get("offset_ms") != cue.t_ms - start.t_ms for cue in ramps):
        errors.append("ramp offset is not the source event clock")
    if ramps[0].payload.get("source", {}).get("lead_ms") != config.bridge_warning_ms:
        errors.append("ramp start did not copy lead_ms from BridgeWarningStarted")
    if ramps[0].payload.get("source", {}).get("alarm_with") != "span_light_strip":
        errors.append("ramp start detached the alarm from the light strip")
    if done.t_ms - start.t_ms != config.bridge_warning_ms:
        errors.append("warning complete is not 4 seconds after the warning start")
    if connect.t_ms != done.t_ms or connects[0].t_ms != connect.t_ms:
        errors.append("connect cue is not on the warning-complete timestamp")
    if _source(match, connects[0]) is not connect:
        errors.append("connect cue is not sourced from BridgeStateChanged")
    if connects[0].payload.get("paired_event") != "BridgeWarningCompleted":
        errors.append("connect cue lost the same-millisecond BridgeWarningCompleted")
    if connects[0].payload.get("paired_index") != match.events.index(done):
        errors.append("connect cue paired index is not BridgeWarningCompleted")
    if _source(match, disconnects[0]) is not disconnect or disconnects[0].t_ms != disconnect.t_ms:
        errors.append("disconnect cue is not on BridgeStateChanged disconnected")
    if any(cue.payload.get("cue_id") == BRIDGE_CONNECT and cue.t_ms == start.t_ms for cue in match.light_cues):
        errors.append("the warning start grew a second connect cue")
    window = [event for event in match.events if start.t_ms <= event.t_ms <= connect.t_ms]
    if any(event.name == "PointScored" for event in window):
        errors.append("the 4 second warning window scored a point")
    if match.events.index(connect) != match.events.index(done) + 1:
        errors.append("connect event is not the next line after warning complete")
    if any(cue.payload.get("ruleset") != "nr03" for cue in ramps + connects + disconnects):
        errors.append("a bridge cue left the NR-03 ruleset")
    return errors


def _gameplay_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    bars = _cues(match, READ_BAR)
    scores = _cues(match, SCORE)
    spawned = _cues(match, SPAWN_PROTECTION)
    started = match.named("ScoreChannelStarted")
    rejected = match.named("ScoreChannelRejected")
    scored = match.named("PointScored")
    if len(started) != 1 or len(bars) != 1:
        errors.append("terminal read-bar is not one cue on one ScoreChannelStarted")
    else:
        bar = bars[0]
        channel = started[0]
        if bar.t_ms != channel.t_ms or _source(match, bar) is not channel:
            errors.append("read-bar cue is not locked to ScoreChannelStarted")
        if bar.payload.get("terminal") != "terminal_b":
            errors.append("read-bar is not on the enemy terminal")
        if bar.payload.get("duration_ms") != config.score_channel_ms:
            errors.append("read-bar duration is not the configured channel")
        if bar.payload.get("source", {}).get("ends_ms") != channel.t_ms + config.score_channel_ms:
            errors.append("read-bar did not copy the channel end from the event")
        if bar.payload.get("intensity") != config.lighting.read_bar_intensity:
            errors.append("read-bar intensity is not the config value")
    if len(rejected) != 1 or rejected[0].payload.get("reason") != "not_holder":
        errors.append("the early channel attempt was not rejected")
    elif any(cue.payload.get("source_event") == "ScoreChannelRejected" for cue in match.light_cues):
        errors.append("a rejected channel lit the read-bar")
    if len(scored) != 1 or len(scores) != 1:
        errors.append("score light is not one cue on one PointScored")
    else:
        cue = scores[0]
        event = scored[0]
        if cue.t_ms != event.t_ms or _source(match, cue) is not event:
            errors.append("score cue is not locked to PointScored")
        if cue.payload.get("source") != event.payload:
            errors.append("score cue did not copy the PointScored payload")
        if cue.payload.get("intensity") != config.lighting.score_intensity:
            errors.append("score intensity is not the config value")
        if any(other.payload.get("source_event") == "CoreReturnedToCenter" for other in match.light_cues):
            errors.append("return-to-center grew a second score light")
    opened = [cue for cue in spawned if cue.payload.get("source_event") == "MatchStarted"]
    ignored = [cue for cue in spawned if cue.payload.get("source_event") == "HitIgnored"]
    if [cue.payload.get("combatant_id") for cue in opened] != ["a1", "a2", "b1"]:
        errors.append("spawn protection did not open once per combatant at match start")
    else:
        for cue in opened:
            if cue.t_ms != 0 or cue.payload.get("protection_until_ms") != config.spawn_protection_ms:
                errors.append("spawn window is not the configured protection on MatchStarted")
            if cue.payload.get("intensity") != config.lighting.spawn_protection_intensity:
                errors.append("spawn protection intensity is not the config value")
    hits = [event for event in match.named("HitIgnored") if event.payload.get("reason") == "spawn_protection"]
    if len(hits) != 1 or len(ignored) != 1:
        errors.append("protected hit did not emit one spawn-protection cue")
    else:
        cue = ignored[0]
        if cue.t_ms != hits[0].t_ms or _source(match, cue) is not hits[0]:
            errors.append("spawn-protection cue is not locked to HitIgnored")
        if cue.payload.get("reason") != "spawn_protection":
            errors.append("spawn-protection cue lost its reason")
        if cue.payload.get("protection_until_ms") != config.spawn_protection_ms:
            errors.append("protected hit started a second protection window")
        if not cue.t_ms < cue.payload.get("protection_until_ms"):
            errors.append("protected hit is not inside the open window")
        if match.combatants["a1"].downed:
            errors.append("spawn protection still downed the target")
    if any(cue.payload.get("source_event") == "HitIgnored" and cue.payload.get("reason") == "shield" for cue in spawned):
        errors.append("a shield ignore was labeled spawn protection")
    if match.score != {"A": 1, "B": 0}:
        errors.append(f"score drifted to {match.score}")
    if match.phase != "live":
        errors.append("one point settled the match")
    if match.core.holder_id is not None or match.core.anchor != "center":
        errors.append("core did not finish at center with no holder")
    if match.holder_errors():
        errors.append("holder audit failed")
    return errors


def _contract_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    if "LightCue" in EVENT_NAMES:
        errors.append("LightCue was added to the scoring event names")
    if any(event.name == "LightCue" for event in match.events):
        errors.append("LightCue was written into match.events")
    ids = set(catalog_ids())
    if len(ids) != len(catalog_ids()):
        errors.append("catalog cue ids are not unique")
    seen = {cue.payload.get("cue_id") for cue in match.light_cues}
    missing = [cue_id for cue_id in catalog_ids() if cue_id not in seen]
    if missing:
        errors.append(f"slice log missed {missing}")
    for cue in match.light_cues:
        payload = cue.payload
        if cue.name != "LightCue":
            errors.append("side log row is not named LightCue")
        if payload.get("asset") != "none" or payload.get("texture") != "none":
            errors.append("a cue claims an asset or a texture")
        if payload.get("rules_effect") != "none":
            errors.append("a cue claims a rules effect")
        if payload.get("clock") != "source_event":
            errors.append("a cue uses a clock other than the source event")
        if payload.get("color_is_identity") is not False:
            errors.append("a cue treats color as identity")
        if payload.get("readable_day") is not True or payload.get("readable_night") is not True:
            errors.append("a cue is not readable against day port and night port")
        if payload.get("day_port_intensity") != match.config.lighting.day_port_intensity:
            errors.append("a cue dropped day_port_intensity")
        if payload.get("night_port_intensity") != match.config.lighting.night_port_intensity:
            errors.append("a cue dropped night_port_intensity")
        source = match.events[payload["source_index"]]
        if source.name != payload.get("source_event") or source.t_ms != cue.t_ms:
            errors.append("a cue timestamp or source event drifted")
        blob = json.dumps(payload)
        for banned in (".uasset", ".png", "Lumen", "lumen"):
            if banned in blob:
                errors.append(f"cue payload mentions {banned}")
    return errors


def acceptance_errors(match: SteelTideMatch | None = None) -> list[str]:
    match = match or run_m2_light()
    errors = _shoulder_errors(match)
    errors.extend(_bridge_errors(match))
    errors.extend(_gameplay_errors(match))
    errors.extend(_contract_errors(match))
    return errors


def diff_committed(match: SteelTideMatch | None = None) -> list[str]:
    errors: list[str] = []
    match = match or run_m2_light()
    if not EVIDENCE_PATH.is_file():
        errors.append("missing docs/evidence/nr-m2-light/light.log")
    elif EVIDENCE_PATH.read_text(encoding="utf-8") != render_light_log(match):
        errors.append("docs/evidence/nr-m2-light/light.log drifted")
    if not HEADER_PATH.is_file():
        errors.append("missing NeonRiftLightCues.h")
    else:
        header = HEADER_PATH.read_text(encoding="utf-8")
        for cue_id in catalog_ids():
            if f'TEXT("{cue_id}")' not in header:
                errors.append(f"{cue_id} missing from NeonRiftLightCues.h")
        for banned in (".uasset", "Lumen", "lumen"):
            if banned in header:
                errors.append(f"light header mentions {banned}")
    return errors


def write_outputs(match: SteelTideMatch | None = None) -> None:
    match = match or run_m2_light()
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(render_light_log(match), encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    args = [] if argv is None else list(argv)
    if args not in ([], ["--check"]):
        print("usage: PYTHONPATH=sim python3 -m steel_tide m2-light [--check]", flush=True)
        return 2
    match = run_m2_light()
    errors = acceptance_errors(match)
    if args == ["--check"]:
        errors.extend(diff_committed(match))
    else:
        write_outputs(match)
    if errors:
        print("NR-M2 light FAIL", flush=True)
        for error in errors:
            print(f"  - {error}", flush=True)
        return 1
    print("NR-M2 light PASS", flush=True)
    print(
        "cues="
        + ",".join(catalog_ids())
        + f" light_rows={len(match.light_cues)} events={len(match.events)} "
        + f"score=A:{match.score['A']},B:{match.score['B']} "
        + f"bridge_warning_seconds={match.config.bridge_warning_seconds:g} "
        + f"day_port_intensity={match.config.lighting.day_port_intensity:g} "
        + f"night_port_intensity={match.config.lighting.night_port_intensity:g} "
        + "asset=none texture=none wired_into_m2_pack=false",
        flush=True,
    )
    print(f"log={EVIDENCE_PATH.as_posix()}", flush=True)
    if args == ["--check"]:
        print("checked light log and cue header", flush=True)
    return 0
