"""NR-03 readability slice: proxy spec, badge geometry, 4s bridge warning.

One command:

    PYTHONPATH=sim python3 -m steel_tide nr03
    PYTHONPATH=sim python3 -m steel_tide nr03 --check

The match object remains the only scorer. This slice checks that a bridge
warning can be read from the light strip and the alarm, and that faction
badges still differ after color is masked. It does not record a device.
"""

from __future__ import annotations

import json
from pathlib import Path

from .config import CONFIG_PATH, load_config
from .match import SteelTideMatch
from .model import badge_for
from .palette import BADGES, PALETTE, badge_identity, badge_svg, colorblind_badge, geometry_signature, greyscale_badge

ROOT = CONFIG_PATH.parents[1]
SPEC_PATH = ROOT / "docs" / "art" / "NR03_PROXIES.json"
EVIDENCE_PATH = ROOT / "docs" / "evidence" / "nr03" / "bridge.log"
PALETTE_DOC = ROOT / "docs" / "art" / "PALETTE_AND_IDS.md"

HUMANOID_BODY = (
    "00100",
    "01110",
    "00100",
    "01110",
    "01010",
)
BEAST_SILHOUETTE = (
    "00111100",
    "01111100",
    "01110010",
    "00100010",
    "00100000",
    "01100000",
)
QUADRUPED_SILHOUETTE = (
    "01111110",
    "01111110",
    "01000010",
    "01000010",
    "01000010",
    "01000010",
)
SHARED_BODY = "NR_Body_Humanoid"
CONNECT_AT_S = 10.0
COLORBLIND_MODES = ("protanopia", "deuteranopia", "tritanopia")


def _cells(rows: tuple[str, ...]) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for y, row in enumerate(rows):
        for x, mark in enumerate(row):
            if mark == "1":
                cells.add((x, y))
    return cells


def _badge_record(faction: str) -> dict:
    badge = BADGES[faction]
    aux = PALETTE[badge["aux"]]
    return {
        "faction": faction,
        "id": badge["id"],
        "shape": badge["shape"],
        "light_id": badge["light_id"],
        "light_slot": badge["light_slot"],
        "aux": badge["aux"],
        "aux_id": aux["id"],
        "aux_hex": aux["hex"],
        "aux_role": aux["role"],
        "file": badge["file"],
        "color_is_identity": False,
    }


def proxy_spec(config=None) -> dict:
    config = config or load_config()
    shared_paint = PALETTE["sea_wall"]["hex"]
    return {
        "id": "NR03_readability",
        "status": "spec_only_no_umap",
        "authority": "sim/steel_tide",
        "source": "sim/steel_tide/nr03.py",
        "palette": "docs/art/PALETTE_AND_IDS.md",
        "level": "NR_SteelTide_Greybox",
        "badges": {"A": _badge_record("A"), "B": _badge_record("B")},
        "bridge_warning": {
            "event_started": "BridgeWarningStarted",
            "event_advance": "BridgeLightStripAdvanced",
            "event_completed": "BridgeWarningCompleted",
            "event_connect": "BridgeStateChanged",
            "connect_state": "connected",
            "bridge_warning_seconds": config.bridge_warning_seconds,
            "readable_without_reflection": config.readable_without_reflection,
            "alarm_starts_with": "span_light_strip",
            "optional_cue": "water_reflection",
            "required_cues": ["span_light_strip", "alarm"],
            "lamps": config.light_strip_lamps(),
            "span_actor": "NR_BridgeSpan",
        },
        "proxies": [
            {
                "id": "NR_Proxy_Humanoid_A",
                "kind": "humanoid",
                "body_id": SHARED_BODY,
                "same_body_as": "NR_Proxy_Humanoid_B",
                "faction": "A",
                "badge_id": BADGES["A"]["id"],
                "shape": BADGES["A"]["shape"],
                "light_id": BADGES["A"]["light_id"],
                "light_slot": BADGES["A"]["light_slot"],
                "aux": BADGES["A"]["aux"],
                "body_silhouette": list(HUMANOID_BODY),
            },
            {
                "id": "NR_Proxy_Humanoid_B",
                "kind": "humanoid",
                "body_id": SHARED_BODY,
                "same_body_as": "NR_Proxy_Humanoid_A",
                "faction": "B",
                "badge_id": BADGES["B"]["id"],
                "shape": BADGES["B"]["shape"],
                "light_id": BADGES["B"]["light_id"],
                "light_slot": BADGES["B"]["light_slot"],
                "aux": BADGES["B"]["aux"],
                "body_silhouette": list(HUMANOID_BODY),
            },
            {
                "id": "NR_Proxy_Beast",
                "kind": "beast",
                "body_id": "NR_Body_Beast",
                "silhouette_id": "organic_beast",
                "paint_hex": shared_paint,
                "silhouette": list(BEAST_SILHOUETTE),
                "note": "Organic stance. A recolor of the quadruped is not this proxy.",
            },
            {
                "id": "NR_Proxy_Quadruped",
                "kind": "robot",
                "body_id": "NR_Body_Quadruped",
                "silhouette_id": "hydraulic_quadruped",
                "paint_hex": shared_paint,
                "silhouette": list(QUADRUPED_SILHOUETTE),
                "note": "Machine stance. Paint matches the beast so the outline has to differ.",
            },
            {
                "id": "NR_Proxy_EngineeringMachine",
                "kind": "prop",
                "material_id": PALETTE["worn_yellow"]["id"],
                "paint": "worn_yellow",
                "hex": PALETTE["worn_yellow"]["hex"],
                "role": "scale_reference",
            },
            {
                "id": "NR_Proxy_WetConcrete",
                "kind": "material",
                "material_id": PALETTE["wet_concrete"]["id"],
                "token": "wet_concrete",
                "hex": PALETTE["wet_concrete"]["hex"],
                "roughness": "high",
                "reflection_required_for_readability": False,
            },
        ],
    }


def spec_text(config=None) -> str:
    return json.dumps(proxy_spec(config), indent=2, ensure_ascii=False) + "\n"


def run_nr03_bridge(config=None) -> SteelTideMatch:
    """Two same-body humanoids, then one 4 second warning through connect."""
    match = SteelTideMatch(config or load_config())
    for combatant_id, client_id, faction in (
        ("a1", "client-a", "A"),
        ("b1", "client-b", "B"),
    ):
        match.add_combatant(
            combatant_id,
            client_id,
            "humanoid_robot",
            "human",
            face_variant="plate-7",
        )
        match.choose_faction(combatant_id, faction)
        match.choose_role(combatant_id, "assault")
    match.start()
    match.schedule_bridge_connect(CONNECT_AT_S)
    match.advance_to(CONNECT_AT_S)
    return match


def render_bridge_log(match: SteelTideMatch) -> str:
    names = {
        "BridgeWarningStarted",
        "BridgeLightStripAdvanced",
        "BridgeWarningCompleted",
        "BridgeStateChanged",
    }
    lines = [
        "# schema nr03-bridge-v1",
        "# authority sim/steel_tide",
        f"# bridge_warning_seconds {match.config.bridge_warning_seconds:g}",
        f"# readable_without_reflection {str(match.config.readable_without_reflection).lower()}",
        "# note event timing only; no audio file and no device recording",
    ]
    for event in match.events:
        if event.name in names:
            lines.append(event.format())
    return "\n".join(lines) + "\n"


def _proxy_errors(config=None) -> list[str]:
    errors: list[str] = []
    config = config or load_config()
    spec = proxy_spec(config)
    by_id = {item["id"]: item for item in spec["proxies"]}
    human_a = by_id["NR_Proxy_Humanoid_A"]
    human_b = by_id["NR_Proxy_Humanoid_B"]
    beast = by_id["NR_Proxy_Beast"]
    quadruped = by_id["NR_Proxy_Quadruped"]
    machine = by_id["NR_Proxy_EngineeringMachine"]
    concrete = by_id["NR_Proxy_WetConcrete"]
    if human_a["body_id"] != human_b["body_id"] or human_a["body_id"] != SHARED_BODY:
        errors.append("humanoid proxies do not share one body")
    if human_a["body_silhouette"] != human_b["body_silhouette"]:
        errors.append("humanoid proxies use different body silhouettes")
    if human_a["shape"] == human_b["shape"] or human_a["light_slot"] == human_b["light_slot"]:
        errors.append("humanoid proxies do not separate faction by shape and light slot")
    if human_a["shape"] != "open_chevron" or human_a["light_slot"] != "shoulder_left":
        errors.append("humanoid A is not open_chevron on the left shoulder")
    if human_b["shape"] != "closed_ring" or human_b["light_slot"] != "shoulder_right":
        errors.append("humanoid B is not closed_ring on the right shoulder")
    if beast["paint_hex"] != quadruped["paint_hex"]:
        errors.append("beast and quadruped differ by paint instead of silhouette")
    if beast["silhouette_id"] == quadruped["silhouette_id"]:
        errors.append("beast and quadruped share a silhouette id")
    beast_cells = _cells(tuple(beast["silhouette"]))
    quad_cells = _cells(tuple(quadruped["silhouette"]))
    if beast_cells == quad_cells or len(beast_cells.symmetric_difference(quad_cells)) < 4:
        errors.append("beast and quadruped silhouettes are not distinct")
    if machine["material_id"] != "mat.worn_yellow" or machine["hex"] != PALETTE["worn_yellow"]["hex"]:
        errors.append("engineering machine is not the worn yellow proxy")
    if concrete["material_id"] != "mat.wet_concrete" or concrete["hex"] != PALETTE["wet_concrete"]["hex"]:
        errors.append("wet concrete proxy drifted from the palette")
    if concrete["roughness"] != "high" or concrete["reflection_required_for_readability"] is not False:
        errors.append("wet concrete still requires a reflection to be readable")
    warning = spec["bridge_warning"]
    if warning["bridge_warning_seconds"] != 4 or warning["readable_without_reflection"] is not True:
        errors.append("bridge warning spec is not 4s and readable without reflection")
    if warning["event_started"] != "BridgeWarningStarted":
        errors.append("warning start event drifted")
    if warning["event_completed"] != "BridgeWarningCompleted" or warning["event_connect"] != "BridgeStateChanged":
        errors.append("warning complete/connect events are not the header names")
    if not PALETTE_DOC.is_file():
        errors.append("palette doc is missing")
    else:
        text = PALETTE_DOC.read_text(encoding="utf-8")
        for proxy_id in by_id:
            if proxy_id not in text:
                errors.append(f"{proxy_id} is missing from PALETTE_AND_IDS.md")
    return errors


def _badge_errors() -> list[str]:
    errors: list[str] = []
    rendered = {faction: badge_svg(faction) for faction in ("A", "B")}
    if badge_identity(rendered["A"]) != ("open_chevron", "shoulder_left"):
        errors.append(f"badge A identity {badge_identity(rendered['A'])}")
    if badge_identity(rendered["B"]) != ("closed_ring", "shoulder_right"):
        errors.append(f"badge B identity {badge_identity(rendered['B'])}")
    signature_a = geometry_signature(rendered["A"])
    signature_b = geometry_signature(rendered["B"])
    if signature_a == signature_b:
        errors.append("masked badge geometry does not separate A and B")
    grey_a = greyscale_badge(rendered["A"])
    grey_b = greyscale_badge(rendered["B"])
    if geometry_signature(grey_a) == geometry_signature(grey_b):
        errors.append("greyscale badge geometry does not separate A and B")
    if geometry_signature(grey_a) != signature_a or geometry_signature(grey_b) != signature_b:
        errors.append("greyscale changed badge geometry")
    for faction, svg in rendered.items():
        expected = badge_identity(svg)
        variants = [greyscale_badge(svg)]
        variants.extend(colorblind_badge(svg, mode) for mode in COLORBLIND_MODES)
        for variant in variants:
            if badge_identity(variant) != expected:
                errors.append(f"color-masked {faction} badge changed identity")
            if "face" in variant.lower():
                errors.append("badge markup mentions a face")
    amber = PALETTE["hazard_amber"]["hex"]
    cyan_grey = greyscale_badge(PALETTE["tide_cyan"]["hex"])
    painted = rendered["B"].replace(amber, cyan_grey)
    if badge_identity(painted) != ("closed_ring", "shoulder_right"):
        errors.append("painting B with A's grey made the ring read as a chevron")
    return errors


def _bridge_errors(match: SteelTideMatch) -> list[str]:
    errors: list[str] = []
    config = match.config
    raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if raw.get("bridge_warning_seconds") != 4 or raw.get("readable_without_reflection") is not True:
        errors.append("config is missing bridge_warning_seconds=4 or readable_without_reflection")
    if config.bridge_warning_seconds != 4 or config.readable_without_reflection is not True:
        errors.append("loaded config does not keep the 4s readable warning")
    if match.combatants["a1"].body != match.combatants["b1"].body:
        errors.append("bridge slice humanoids do not share a body")
    if match.combatants["a1"].face_variant != match.combatants["b1"].face_variant:
        errors.append("bridge slice humanoids were split into different bodies")
    badge_a = badge_for(match.combatants["a1"].faction, config.badges, match.combatants["a1"].face_variant)
    badge_b = badge_for(match.combatants["b1"].faction, config.badges, match.combatants["b1"].face_variant)
    if badge_a["shape"] == badge_b["shape"] or badge_a["light_slot"] == badge_b["light_slot"]:
        errors.append("same-body humanoids are not separated by badge shape and light slot")
    started = match.named("BridgeWarningStarted")
    advances = match.named("BridgeLightStripAdvanced")
    completed = match.named("BridgeWarningCompleted")
    connected = [event for event in match.named("BridgeStateChanged") if event.payload.get("state") == "connected"]
    if len(started) != 1 or len(completed) != 1 or len(connected) != 1:
        errors.append(
            f"expected one start, one complete, one connect; got {len(started)}/{len(completed)}/{len(connected)}"
        )
        return errors
    start = started[0]
    done = completed[0]
    connect = connected[0]
    lead = config.bridge_warning_ms
    if start.payload.get("lead_ms") != lead or start.payload.get("sequence_ms") != lead:
        errors.append("warning sequence is not the configured lead")
    if start.payload.get("alarm_started") is not True or start.payload.get("alarm_with") != "span_light_strip":
        errors.append("alarm did not start with the light strip")
    if start.payload.get("light_strip_index") != 0 or start.payload.get("offset_ms") != 0:
        errors.append("light strip did not start on the warning event")
    if start.payload.get("readable_without_reflection") is not True:
        errors.append("warning payload dropped readable_without_reflection")
    for cue in ("span_light_strip", "alarm"):
        if cue not in start.payload.get("cues", []):
            errors.append(f"warning is missing {cue}")
    if [event.payload.get("index") for event in advances] != [1, 2, 3]:
        errors.append(f"light strip indexes {[event.payload.get('index') for event in advances]}")
    if [event.t_ms - start.t_ms for event in advances] != [1000, 2000, 3000]:
        errors.append("light strip is not a 1 second cadence across the 4 second lead")
    if any(event.payload.get("cue") != "span_light_strip" for event in advances):
        errors.append("a light-strip step lost its cue")
    if done.t_ms - start.t_ms != lead or done.payload.get("elapsed_ms") != lead:
        errors.append("warning did not complete 4 seconds after it started")
    if done.payload.get("alarm_started_with") != "span_light_strip":
        errors.append("completion detached the alarm from the light strip")
    if done.payload.get("light_strip_index") != config.light_strip_lamps() - 1:
        errors.append("completion is not the last lamp")
    if connect.t_ms != done.t_ms:
        errors.append("bridge connect is not on the warning-complete timestamp")
    if match.events.index(connect) != match.events.index(done) + 1:
        errors.append("connect event is not the next line after warning complete")
    if start.t_ms != config.seconds_to_ms(CONNECT_AT_S) - lead:
        errors.append("warning did not lead the connect by 4 seconds")
    if match.score != {"A": 0, "B": 0} or match.core.holder_id is not None:
        errors.append("bridge warning changed holder or score")
    if match.named("PointScored") or match.phase == "settled":
        errors.append("readability slice settled a match")
    return errors


def acceptance_errors(match: SteelTideMatch | None = None) -> list[str]:
    match = match or run_nr03_bridge()
    errors = _proxy_errors(match.config)
    errors.extend(_badge_errors())
    errors.extend(_bridge_errors(match))
    return errors


def diff_committed(match: SteelTideMatch | None = None) -> list[str]:
    errors: list[str] = []
    match = match or run_nr03_bridge()
    if not SPEC_PATH.is_file():
        errors.append("missing docs/art/NR03_PROXIES.json")
    elif SPEC_PATH.read_text(encoding="utf-8") != spec_text(match.config):
        errors.append("docs/art/NR03_PROXIES.json drifted from sim/steel_tide/nr03.py")
    if not EVIDENCE_PATH.is_file():
        errors.append("missing docs/evidence/nr03/bridge.log")
    elif EVIDENCE_PATH.read_text(encoding="utf-8") != render_bridge_log(match):
        errors.append("docs/evidence/nr03/bridge.log drifted")
    for faction, badge in BADGES.items():
        path = ROOT / badge["file"]
        if not path.is_file() or path.read_text(encoding="utf-8") != badge_svg(faction):
            errors.append(f"{badge['file']} drifted from palette.badge_svg")
    return errors


def write_outputs(match: SteelTideMatch | None = None) -> None:
    match = match or run_nr03_bridge()
    SPEC_PATH.parent.mkdir(parents=True, exist_ok=True)
    SPEC_PATH.write_text(spec_text(match.config), encoding="utf-8")
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(render_bridge_log(match), encoding="utf-8")
    for faction, badge in BADGES.items():
        path = ROOT / badge["file"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(badge_svg(faction), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = [] if argv is None else list(argv)
    if args not in ([], ["--check"]):
        print("usage: PYTHONPATH=sim python3 -m steel_tide nr03 [--check]")
        return 2
    match = run_nr03_bridge()
    errors = acceptance_errors(match)
    if args == ["--check"]:
        errors.extend(diff_committed(match))
    else:
        write_outputs(match)
    if errors:
        print("NR-03 readability FAIL")
        for error in errors:
            print(f"  - {error}")
        return 1
    started = match.named("BridgeWarningStarted")[0]
    completed = match.named("BridgeWarningCompleted")[0]
    print("NR-03 readability PASS")
    print(
        "proxies=6 badges=A:open_chevron/shoulder_left,B:closed_ring/shoulder_right "
        f"bridge_warning_seconds={match.config.bridge_warning_seconds:g} "
        f"readable_without_reflection={str(match.config.readable_without_reflection).lower()} "
        f"sequence_ms={completed.t_ms - started.t_ms} "
        f"alarm_with={started.payload['alarm_with']}"
    )
    print(f"spec={SPEC_PATH.as_posix()}")
    print(f"log={EVIDENCE_PATH.as_posix()}")
    if args == ["--check"]:
        print("checked spec, badges, and bridge log")
    return 0
