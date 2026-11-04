"""NR-M2 audio cue slice. Headless contract, not a sound asset.

One command:

    PYTHONPATH=sim python3 -m steel_tide m2-audio
    PYTHONPATH=sim python3 -m steel_tide m2-audio --check

The match object remains the only scorer. This slice places two same-body
humanoids, then runs the existing pick / pass / drop / channel / reset
calls and the NR-03 bridge schedulers. `AudioCue` rows are a side log.
They are not in `EVENT_NAMES` and they are not in `match.events`.

Not a step of `m2-pack`. The pack's unittest step still imports the tests
for this module. Pack evidence stays the rules chain.
"""

from __future__ import annotations

import json

from .audio import (
    BRIDGE_CONNECT,
    BRIDGE_DISCONNECT,
    BRIDGE_LIGHT_STRIP,
    BRIDGE_WARN,
    CORE_CUES,
    catalog_ids,
    team_cue_id_for,
)
from .config import CONFIG_PATH, load_config
from .events import EVENT_NAMES
from .match import SERVER_CLIENT, SteelTideMatch
from .model import Event
from .palette import BADGES, PALETTE, badge_identity, badge_svg, colorblind_badge, greyscale_badge

ROOT = CONFIG_PATH.parents[1]
EVIDENCE_PATH = ROOT / "docs" / "evidence" / "nr-m2-audio" / "audio.log"
HEADER_PATH = ROOT / "Source" / "NeonRift" / "Public" / "NeonRiftAudioCues.h"
SCHEMA = "nr-m2-audio-cues-v1"

# Schedule points only. The 4 second lead stays inside schedule_bridge_connect.
CONNECT_AT_S = 16.0
DISCONNECT_AT_S = 18.0
COLORBLIND_MODES = ("protanopia", "deuteranopia", "tritanopia")


def run_m2_audio(config=None) -> SteelTideMatch:
    """Same-body A and B, one of each core cue, then the NR-03 bridge clock."""
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
    match.start()
    match.schedule_bridge_connect(CONNECT_AT_S)
    match.schedule_bridge_disconnect(DISCONNECT_AT_S)
    match.place_for_test("a1", "center")
    match.place_for_test("a2", "center")
    match.enqueue("client-a", "pick_core", 0.5, combatant_id="a1")
    match.enqueue("client-a2", "pick_core", 0.5, combatant_id="a2")
    match.enqueue("client-a", "pass_core", 1.0, from_id="a1", to_id="a2")
    match.enqueue("client-a2", "drop_core", 1.5, combatant_id="a2")
    match.advance_to(1.5)
    match.place_for_test("a2", "spawn_a")
    match.enqueue("client-a", "pick_core", 3.5, combatant_id="a1")
    match.advance_to(3.5)
    match.place_for_test("a1", "terminal_b")
    match.enqueue("client-a", "begin_score", 4.0, combatant_id="a1")
    match.enqueue(SERVER_CLIENT, "hit", 5.0, target_id="a1", down=False)
    match.advance_to(5.0)
    match.enqueue("client-a", "begin_score", 5.5, combatant_id="a1")
    match.advance_to(DISCONNECT_AT_S)
    match.place_for_test("a1", "center")
    match.enqueue("client-a", "pick_core", 19.0, combatant_id="a1")
    match.enqueue(SERVER_CLIENT, "mark_core_overboard", 19.5)
    match.advance_to(19.5 + match.config.core_reset_timeout_seconds)
    return match


def render_audio_log(match: SteelTideMatch) -> str:
    holder = "-" if match.core.holder_id is None else match.core.holder_id
    lines = [
        f"# schema {SCHEMA}",
        "# authority sim/steel_tide",
        "# kind audio-cue-contract",
        "# asset none",
        "# wav false",
        "# metasound false",
        "# uasset false",
        "# bridge_ruleset nr03",
        "# color_is_identity false",
        "# wired_into_m2_pack false",
        f"# bridge_warning_seconds {match.config.bridge_warning_seconds:g}",
        f"# score A={match.score['A']} B={match.score['B']}",
        f"# holder {holder}",
        f"# phase {match.phase}",
    ]
    for cue in match.audio_cues:
        lines.append(cue.format())
    return "\n".join(lines) + "\n"


def _cues(match: SteelTideMatch, cue_id: str) -> list[Event]:
    return [cue for cue in match.audio_cues if cue.payload.get("cue_id") == cue_id]


def _source(match: SteelTideMatch, cue: Event) -> Event:
    return match.events[cue.payload["source_index"]]


def _team_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    if team_cue_id_for("A") == team_cue_id_for("B"):
        errors.append("team cue ids are not split")
    for faction in ("A", "B"):
        badge = BADGES[faction]
        expected = team_cue_id_for(faction)
        if badge["shape"] not in expected or badge["light_slot"] not in expected:
            errors.append(f"{faction} cue id dropped shape or mouth")
        if PALETTE[badge["aux"]]["hex"].lower() in expected.lower():
            errors.append(f"{faction} cue id contains the auxiliary hex")
        if badge["aux"] in expected:
            errors.append(f"{faction} cue id contains the auxiliary token")
        painted = badge_svg(faction).replace(PALETTE[badge["aux"]]["hex"], "#808080")
        if badge_identity(painted) != (badge["shape"], badge["light_slot"]):
            errors.append(f"painting {faction} changed the mouth identity")
        masked = [greyscale_badge(badge_svg(faction))]
        masked.extend(colorblind_badge(badge_svg(faction), mode) for mode in COLORBLIND_MODES)
        for variant in masked:
            if badge_identity(variant) != (badge["shape"], badge["light_slot"]):
                errors.append(f"color mask changed {faction} shape or mouth")
    a1 = match.combatants["a1"]
    b1 = match.combatants["b1"]
    if a1.body != b1.body or a1.face_variant != b1.face_variant:
        errors.append("A and B humanoids were split by body")
    rows = [cue for cue in match.audio_cues if cue.payload.get("family") == "team"]
    if [cue.payload.get("combatant_id") for cue in rows] != ["a1", "a2", "b1"]:
        errors.append("team cues are not one row per locked combatant")
    seen: dict[str, str] = {}
    for cue in rows:
        faction = cue.payload.get("faction")
        cue_id = cue.payload.get("cue_id")
        if faction not in ("A", "B") or cue_id != team_cue_id_for(faction):
            errors.append(f"team cue {cue_id} is not the NR-03 id for {faction}")
            continue
        if cue.payload.get("mouth") != cue.payload.get("light_slot"):
            errors.append("audio mouth is not the shoulder lamp slot")
        if cue.payload.get("color_role") != "auxiliary" or cue.payload.get("color_is_identity") is not False:
            errors.append("team color is not marked auxiliary")
        if cue.payload.get("shape") != BADGES[faction]["shape"]:
            errors.append("team cue shape drifted from the badge")
        if cue.payload.get("light_slot") != BADGES[faction]["light_slot"]:
            errors.append("team cue mouth drifted from the badge")
        if "face" in json.dumps(cue.payload).lower():
            errors.append("team cue mentions a face")
        seen[faction] = cue_id
    if seen.get("A") == seen.get("B") or set(seen) != {"A", "B"}:
        errors.append("locked roster did not emit both team mouths")
    mouths = {cue.payload.get("mouth") for cue in rows}
    if mouths != {"shoulder_left", "shoulder_right"}:
        errors.append(f"mouths {mouths} are not the two lamp sides")
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
    warns = _cues(match, BRIDGE_WARN)
    strips = _cues(match, BRIDGE_LIGHT_STRIP)
    connects = _cues(match, BRIDGE_CONNECT)
    disconnects = _cues(match, BRIDGE_DISCONNECT)
    if len(started) != 1 or len(completed) != 1 or len(connected) != 1 or len(disconnected) != 1:
        errors.append("bridge slice did not emit one warn, one complete, one connect, one disconnect")
        return errors
    if len(warns) != 1 or len(connects) != 1 or len(disconnects) != 1:
        errors.append("bridge cue counts are not one warn, one connect, one disconnect")
        return errors
    if len(strips) != len(advances) or len(advances) != 3:
        errors.append("light-strip cues are not one per BridgeLightStripAdvanced")
    start = started[0]
    done = completed[0]
    connect = connected[0]
    disconnect = disconnected[0]
    warn = warns[0]
    if warn.t_ms != start.t_ms or _source(match, warn) is not start:
        errors.append("warn cue is not on BridgeWarningStarted")
    if warn.payload.get("source", {}).get("lead_ms") != config.bridge_warning_ms:
        errors.append("warn cue did not copy lead_ms from the warning event")
    if warn.payload.get("source", {}).get("alarm_with") != "span_light_strip":
        errors.append("warn cue detached the alarm from the light strip")
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
    if any(_source(match, cue) is not event or cue.t_ms != event.t_ms for cue, event in zip(strips, advances)):
        errors.append("a light-strip cue missed its BridgeLightStripAdvanced timestamp")
    if [cue.payload.get("source", {}).get("index") for cue in strips] != [1, 2, 3]:
        errors.append("light-strip progress indexes are not 1, 2, 3")
    if _source(match, disconnects[0]) is not disconnect or disconnects[0].t_ms != disconnect.t_ms:
        errors.append("disconnect cue is not on BridgeStateChanged disconnected")
    if any(cue.payload.get("cue_id") == BRIDGE_WARN for cue in match.audio_cues if cue.t_ms == done.t_ms):
        errors.append("warning completion grew a second warn cue")
    completed_cues = [
        cue for cue in match.audio_cues if cue.payload.get("source_event") == "BridgeWarningCompleted"
    ]
    if completed_cues:
        errors.append("BridgeWarningCompleted emitted its own cue beside connect")
    window = [event for event in match.events if start.t_ms <= event.t_ms <= connect.t_ms]
    if any(event.name == "PointScored" for event in window):
        errors.append("the 4 second warning window scored a point")
    if match.events.index(connect) != match.events.index(done) + 1:
        errors.append("connect event is not the next line after warning complete")
    return errors


def _core_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    for name, cue_id in CORE_CUES:
        sources = match.named(name)
        cues = _cues(match, cue_id)
        if not sources or not cues:
            errors.append(f"missing {name} / {cue_id}")
            continue
        if len(cues) != len(sources):
            errors.append(f"{cue_id} count {len(cues)} != {name} count {len(sources)}")
        for cue, event in zip(cues, sources):
            if cue.t_ms != event.t_ms or _source(match, cue) is not event:
                errors.append(f"{cue_id} is not locked to {name}")
            if cue.payload.get("source") != event.payload:
                errors.append(f"{cue_id} did not copy the {name} payload")
    picked = match.named("CorePicked")
    rejected = [event for event in match.named("CorePickRejected") if event.t_ms == picked[0].t_ms]
    if len(picked) < 1 or not rejected:
        errors.append("same-frame contest did not keep one pick and one rejection")
    if any(cue.payload.get("source_event") == "CorePickRejected" for cue in match.audio_cues):
        errors.append("a rejected pick emitted a pickup cue")
    interrupt = match.named("ScoreChannelInterrupted")
    if len(interrupt) != 1 or interrupt[0].payload.get("reason") != "hit":
        errors.append("channel interrupt is not the one server hit")
    elif any(event.name == "PointScored" and event.t_ms == interrupt[0].t_ms for event in match.events):
        errors.append("interrupt millisecond also scored")
    reset = match.named("CoreReset")
    if len(reset) != 1 or reset[0].payload.get("anchor") != "center":
        errors.append("reset did not return the core to center")
    elif any(event.name == "PointScored" and event.t_ms == reset[0].t_ms for event in match.events):
        errors.append("reset millisecond scored")
    if match.score != {"A": 1, "B": 0}:
        errors.append(f"score drifted to {match.score}")
    if match.core.holder_id is not None or match.core.anchor != "center":
        errors.append("core did not finish at center with no holder")
    if match.named("PointScored") and match.named("CoreReturnedToCenter"):
        scored = match.named("PointScored")[0]
        returned = match.named("CoreReturnedToCenter")[0]
        if scored.t_ms != returned.t_ms:
            errors.append("return-to-center is not on the score timestamp")
    if match.holder_errors():
        errors.append("holder audit failed")
    return errors


def _contract_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    if "AudioCue" in EVENT_NAMES:
        errors.append("AudioCue was added to the scoring event names")
    if any(event.name == "AudioCue" for event in match.events):
        errors.append("AudioCue was written into match.events")
    ids = set(catalog_ids())
    if len(ids) != len(catalog_ids()):
        errors.append("catalog cue ids are not unique")
    seen = {cue.payload.get("cue_id") for cue in match.audio_cues}
    missing = [cue_id for cue_id in catalog_ids() if cue_id not in seen]
    if missing:
        errors.append(f"slice log missed {missing}")
    for cue in match.audio_cues:
        payload = cue.payload
        if cue.name != "AudioCue":
            errors.append("side log row is not named AudioCue")
        if payload.get("asset") != "none" or payload.get("rules_effect") != "none":
            errors.append("a cue claims an asset or a rules effect")
        if payload.get("clock") != "source_event":
            errors.append("a cue uses a clock other than the source event")
        if payload.get("color_is_identity") is not False:
            errors.append("a cue treats color as identity")
        source = match.events[payload["source_index"]]
        if source.name != payload.get("source_event") or source.t_ms != cue.t_ms:
            errors.append("a cue timestamp or source event drifted")
        blob = json.dumps(payload)
        for banned in (".wav", ".uasset", "MetaSound", "metasound"):
            if banned in blob:
                errors.append(f"cue payload mentions {banned}")
    return errors


def acceptance_errors(match: SteelTideMatch | None = None) -> list[str]:
    match = match or run_m2_audio()
    errors = _team_errors(match)
    errors.extend(_bridge_errors(match))
    errors.extend(_core_errors(match))
    errors.extend(_contract_errors(match))
    return errors


def diff_committed(match: SteelTideMatch | None = None) -> list[str]:
    errors: list[str] = []
    match = match or run_m2_audio()
    if not EVIDENCE_PATH.is_file():
        errors.append("missing docs/evidence/nr-m2-audio/audio.log")
    elif EVIDENCE_PATH.read_text(encoding="utf-8") != render_audio_log(match):
        errors.append("docs/evidence/nr-m2-audio/audio.log drifted")
    if not HEADER_PATH.is_file():
        errors.append("missing NeonRiftAudioCues.h")
    else:
        header = HEADER_PATH.read_text(encoding="utf-8")
        for cue_id in catalog_ids():
            if f'TEXT("{cue_id}")' not in header:
                errors.append(f"{cue_id} missing from NeonRiftAudioCues.h")
        for banned in (".wav", ".uasset", "MetaSound"):
            if banned in header:
                errors.append(f"audio header mentions {banned}")
    return errors


def write_outputs(match: SteelTideMatch | None = None) -> None:
    match = match or run_m2_audio()
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(render_audio_log(match), encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    args = [] if argv is None else list(argv)
    if args not in ([], ["--check"]):
        print("usage: PYTHONPATH=sim python3 -m steel_tide m2-audio [--check]", flush=True)
        return 2
    match = run_m2_audio()
    errors = acceptance_errors(match)
    if args == ["--check"]:
        errors.extend(diff_committed(match))
    else:
        write_outputs(match)
    if errors:
        print("NR-M2 audio FAIL", flush=True)
        for error in errors:
            print(f"  - {error}", flush=True)
        return 1
    print("NR-M2 audio PASS", flush=True)
    print(
        "cues="
        + ",".join(catalog_ids())
        + f" audio_rows={len(match.audio_cues)} events={len(match.events)} "
        + f"score=A:{match.score['A']},B:{match.score['B']} "
        + f"bridge_warning_seconds={match.config.bridge_warning_seconds:g} "
        + "asset=none wired_into_m2_pack=false",
        flush=True,
    )
    print(f"log={EVIDENCE_PATH.as_posix()}", flush=True)
    if args == ["--check"]:
        print("checked audio log and cue header", flush=True)
    return 0
