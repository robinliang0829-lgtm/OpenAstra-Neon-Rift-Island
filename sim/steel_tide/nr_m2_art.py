"""NR-M2 art identity. Harbor palette, badge geometry, decal and material names.

No match is run. EVENT_NAMES and the scorer stay where they are. Nothing
here is a texture binary or a .uasset.

    PYTHONPATH=sim python3 -m steel_tide m2-art
    PYTHONPATH=sim python3 -m steel_tide m2-art --check

wired_into_m2_pack is false: the dev pack does not gain an m2-art step.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as etree
from pathlib import Path

from .config import CONFIG_PATH, REPO_ROOT
from .nr_m2_pack import STEPS
from .palette import (
    BADGES,
    PALETTE,
    badge_identity,
    badge_svg,
    colorblind_badge,
    geometry_signature,
    greyscale_badge,
)

SCHEMA = "nr-m2-art-identity-v1"
IDENTITY_PATH = REPO_ROOT / "config" / "m2_art_identity.json"
SPEC_PATH = REPO_ROOT / "docs" / "art" / "M2_ASSET_SPEC.md"
EVIDENCE_PATH = REPO_ROOT / "docs" / "evidence" / "nr-m2-art" / "identity.log"
PALETTE_DOC = REPO_ROOT / "docs" / "art" / "PALETTE_AND_IDS.md"
UPROJECT_PATH = REPO_ROOT / "NeonRift.uproject"
SHARED_BODY = "NR_Body_Humanoid"
LIGHT_MIDLINE_X = 32
ENGINE_ASSOCIATION = "5.4"
_SVG = "{http://www.w3.org/2000/svg}"
_COLORBLIND = ("protanopia", "deuteranopia", "tritanopia")
_DECAL_COLOR_WORDS = (
    "tide",
    "hazard",
    "cyan",
    "amber",
    "magenta",
    "yellow",
    "concrete",
    "#",
    "3ddfd4",
    "e2a23a",
)

# Harbor environment first, faction auxiliary after. Hex lives in palette.py.
HARBOR_ORDER = (
    "wet_concrete",
    "worn_yellow",
    "sign_cyan",
    "sign_magenta",
    "sea_wall",
)
AUX_ORDER = ("tide_cyan", "hazard_amber")
TOKEN_ORDER = HARBOR_ORDER + AUX_ORDER

USES = {
    "wet_concrete": "deck and street",
    "worn_yellow": "engineering machines",
    "sign_cyan": "environment sign",
    "sign_magenta": "environment sign",
    "sea_wall": "sea wall",
    "tide_cyan": "A auxiliary only",
    "hazard_amber": "B auxiliary only",
}
NOTES = {
    "wet_concrete": "High roughness. A reflection is not required to read the deck.",
    "worn_yellow": "Engineering-machine scale reference. Not a team id.",
    "sign_cyan": "Environment sign. Quieter than a shoulder badge.",
    "sign_magenta": "Environment sign. Quieter than a shoulder badge.",
    "sea_wall": "Shared non-team paint. Beast and quadruped still need different outlines.",
    "tide_cyan": "Auxiliary tint for A. Not the team id.",
    "hazard_amber": "Auxiliary tint for B. Not the team id.",
}
_NOTE_ZH = {
    "wet_concrete": "粗糙度高。倒影不是读甲板的条件。",
    "worn_yellow": "工程机械的比例参照，不是队标。",
    "sign_cyan": "环境招牌，要比肩章安静。",
    "sign_magenta": "环境招牌，要比肩章安静。",
    "sea_wall": "非队标的共用漆。兽和四足机仍要不同轮廓。",
    "tide_cyan": "只给 A 的辅助色，不是队标。",
    "hazard_amber": "只给 B 的辅助色，不是队标。",
}
MATERIAL_NAMES = {
    "wet_concrete": ("NR_Mat_WetConcrete", "MI_NR_WetConcrete"),
    "worn_yellow": ("NR_Mat_WornYellow", "MI_NR_WornYellow"),
    "sign_cyan": ("NR_Mat_SignCyan", "MI_NR_SignCyan"),
    "sign_magenta": ("NR_Mat_SignMagenta", "MI_NR_SignMagenta"),
    "sea_wall": ("NR_Mat_SeaWall", "MI_NR_SeaWall"),
    "tide_cyan": ("NR_Mat_AuxTideCyan", "MI_NR_AuxTideCyan"),
    "hazard_amber": ("NR_Mat_AuxHazardAmber", "MI_NR_AuxHazardAmber"),
}
DECAL_NAMES = {
    "A": ("NR_Decal_BadgeA_OpenChevron", "D_NR_BadgeA_OpenChevron"),
    "B": ("NR_Decal_BadgeB_ClosedRing", "D_NR_BadgeB_ClosedRing"),
}
# Numbers are the badge svg. Color is not part of this table.
EXPECTED_GEOMETRY = {
    "A": {
        "shape": "open_chevron",
        "light_slot": "shoulder_left",
        "primitive": "polyline",
        "points": "16,44 32,20 48,44",
        "circle": None,
        "light_rect": (4, 28, 6, 8),
        "closed": False,
        "stroke_width": 6,
        "stroke_linecap": "square",
        "viewbox": "0 0 64 64",
    },
    "B": {
        "shape": "closed_ring",
        "light_slot": "shoulder_right",
        "primitive": "circle",
        "points": None,
        "circle": (32, 32, 16),
        "light_rect": (54, 28, 6, 8),
        "closed": True,
        "stroke_width": 6,
        "stroke_linecap": None,
        "viewbox": "0 0 64 64",
    },
}
CHECKLIST_IDS = (
    "harbor.tokens",
    "harbor.concrete",
    "harbor.signs",
    "harbor.yellow",
    "harbor.seawall",
    "badge.shape",
    "badge.light",
    "badge.body",
    "badge.noface",
    "naming.decal",
    "naming.material",
    "naming.notexture",
    "scale.units",
    "engine.placeholder",
    "pack.unwired",
)


def wired_into_m2_pack() -> bool:
    """True only when the dev pack's step list actually runs m2-art."""
    for name, _module, args in STEPS:
        if name == "m2-art" or "m2-art" in args:
            return True
    return False


def _engine_association() -> str:
    project = json.loads(UPROJECT_PATH.read_text(encoding="utf-8"))
    return str(project.get("EngineAssociation", ""))


def _greybox() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _rect_dict(rect: tuple[int, int, int, int] | None) -> dict[str, int] | None:
    if rect is None:
        return None
    return {"x": rect[0], "y": rect[1], "width": rect[2], "height": rect[3]}


def _circle_dict(circle: tuple[int, int, int] | None) -> dict[str, int] | None:
    if circle is None:
        return None
    return {"cx": circle[0], "cy": circle[1], "r": circle[2]}


def _int_attr(element: etree.Element, name: str) -> int:
    value = float(element.attrib[name])
    if value != int(value):
        raise ValueError(f"{name} is not an integer: {element.attrib[name]}")
    return int(value)


def parse_badge_svg(svg: str) -> dict:
    """Read shape, lamp rect, and stroke from one badge svg."""
    root = etree.fromstring(svg)
    polys = root.findall(f"{_SVG}polyline")
    circles = root.findall(f"{_SVG}circle")
    rects = root.findall(f"{_SVG}rect")
    if len(polys) == 1 and not circles:
        primitive = "polyline"
        geometry = polys[0]
        points = geometry.attrib.get("points")
        circle = None
        closed = False
    elif len(circles) == 1 and not polys:
        primitive = "circle"
        geometry = circles[0]
        points = None
        circle = (_int_attr(geometry, "cx"), _int_attr(geometry, "cy"), _int_attr(geometry, "r"))
        closed = True
    else:
        primitive = "ambiguous"
        geometry = None
        points = None
        circle = None
        closed = None
    if len(rects) == 1:
        light_rect = (
            _int_attr(rects[0], "x"),
            _int_attr(rects[0], "y"),
            _int_attr(rects[0], "width"),
            _int_attr(rects[0], "height"),
        )
        light_fill = rects[0].attrib.get("fill")
    else:
        light_rect = None
        light_fill = None
    stroke_linecap = None if geometry is None else geometry.attrib.get("stroke-linecap")
    stroke_width = None if geometry is None else _int_attr(geometry, "stroke-width")
    return {
        "viewbox": root.attrib.get("viewBox"),
        "badge_id": root.attrib.get("data-badge-id"),
        "shape": root.attrib.get("data-shape"),
        "light_slot": root.attrib.get("data-light-slot"),
        "color_role": root.attrib.get("data-color-role"),
        "aux": root.attrib.get("data-aux-color"),
        "primitive": primitive,
        "points": points,
        "circle": circle,
        "closed": closed,
        "light_rect": light_rect,
        "light_fill": light_fill,
        "stroke": None if geometry is None else geometry.attrib.get("stroke"),
        "fill": None if geometry is None else geometry.attrib.get("fill"),
        "stroke_width": stroke_width,
        "stroke_linecap": stroke_linecap,
        "title": None if root.find(f"{_SVG}title") is None else root.find(f"{_SVG}title").text,
    }


def _token_row(token: str) -> dict:
    src = PALETTE[token]
    blender, ue = MATERIAL_NAMES[token]
    family = "harbor" if token in HARBOR_ORDER else "auxiliary"
    return {
        "token": token,
        "id": src["id"],
        "hex": src["hex"],
        "role": src["role"],
        "family": family,
        "team_identity": False,
        "use": USES[token],
        "note": NOTES[token],
        "roughness": "high" if token == "wet_concrete" else None,
        "reflection_required_for_readability": False if token == "wet_concrete" else None,
        "aux_for": {"tide_cyan": "A", "hazard_amber": "B"}.get(token),
        "blender": blender,
        "ue": ue,
        "texture": "none",
    }


def _badge_row(faction: str) -> dict:
    spec = EXPECTED_GEOMETRY[faction]
    badge = BADGES[faction]
    aux = PALETTE[badge["aux"]]
    blender, ue = DECAL_NAMES[faction]
    return {
        "faction": faction,
        "id": badge["id"],
        "shape": spec["shape"],
        "light_id": badge["light_id"],
        "light_slot": spec["light_slot"],
        "aux": badge["aux"],
        "aux_id": aux["id"],
        "aux_hex": aux["hex"],
        "aux_role": aux["role"],
        "color_is_identity": False,
        "file": badge["file"],
        "viewbox": spec["viewbox"],
        "primitive": spec["primitive"],
        "points": spec["points"],
        "circle": _circle_dict(spec["circle"]),
        "light_rect": _rect_dict(spec["light_rect"]),
        "closed": spec["closed"],
        "stroke_width": spec["stroke_width"],
        "stroke_linecap": spec["stroke_linecap"],
        "body_id": SHARED_BODY,
        "socket": f"socket.{spec['light_slot']}",
        "blender": blender,
        "ue": ue,
        "texture": "none",
    }


def _naming_rows(tokens: list[dict], badges: dict[str, dict]) -> list[dict]:
    rows: list[dict] = []
    for token in tokens:
        rows.append(
            {
                "kind": "material",
                "id": token["id"],
                "token": token["token"],
                "hex": token["hex"],
                "role": token["role"],
                "family": token["family"],
                "team_identity": False,
                "color_is_identity": False,
                "shape": None,
                "light_id": None,
                "light_slot": None,
                "blender": token["blender"],
                "ue": token["ue"],
                "socket": None,
                "body_id": None,
                "texture": "none",
                "binary": False,
            }
        )
    for faction in ("A", "B"):
        badge = badges[faction]
        rows.append(
            {
                "kind": "decal",
                "id": badge["id"],
                "token": None,
                "hex": None,
                "role": "team_mark",
                "family": "badge",
                "team_identity": True,
                "color_is_identity": False,
                "shape": badge["shape"],
                "light_id": badge["light_id"],
                "light_slot": badge["light_slot"],
                "blender": badge["blender"],
                "ue": badge["ue"],
                "socket": badge["socket"],
                "body_id": badge["body_id"],
                "texture": "none",
                "binary": False,
            }
        )
    return rows


def _checklist(tokens: list[dict], badges: dict[str, dict]) -> list[dict]:
    by = {item["token"]: item for item in tokens}
    concrete = by["wet_concrete"]
    cyan = by["sign_cyan"]
    magenta = by["sign_magenta"]
    yellow = by["worn_yellow"]
    wall = by["sea_wall"]
    tide = by["tide_cyan"]
    amber = by["hazard_amber"]
    badge_a = badges["A"]
    badge_b = badges["B"]
    rows = (
        (
            "harbor.tokens",
            "both",
            "spec_only",
            "五个港区环境色和两个辅助色的 id、十六进制都来自 `palette.py`。"
            "环境色是 "
            + "、".join(f"`{item['id']}`" for item in tokens if item["family"] == "harbor")
            + f"。辅助色是 `{tide['id']}` `{tide['hex']}`、`{amber['id']}` `{amber['hex']}`。"
            "不要在 Blender 或材质实例里另写一版。",
        ),
        (
            "harbor.concrete",
            "both",
            "spec_only",
            f"`{concrete['id']}`（`{concrete['hex']}`）铺甲板和路面。粗糙度高。"
            "验收关高反射，倒影不是读这块材质的条件。",
        ),
        (
            "harbor.signs",
            "both",
            "spec_only",
            f"`{cyan['id']}`（`{cyan['hex']}`）和 `{magenta['id']}`（`{magenta['hex']}`）只做环境招牌。"
            "它们不是队标，不能比肩章更抢。",
        ),
        (
            "harbor.yellow",
            "both",
            "spec_only",
            f"`{yellow['id']}`（`{yellow['hex']}`）只涂港区工程机械，当比例参照。黄漆不是阵营。",
        ),
        (
            "harbor.seawall",
            "both",
            "spec_only",
            f"`{wall['id']}`（`{wall['hex']}`）是海堤色。兽和四足机可以共用这色，轮廓仍必须不同。"
            "不要靠换色把四足机当成兽。",
        ),
        (
            "badge.shape",
            "both",
            "spec_only",
            f"A 是开口人字 `{badge_a['shape']}`，折线 `{badge_a['points']}`，不回到起点。"
            f"B 是闭合环 `{badge_b['shape']}`，圆心 `{badge_b['circle']['cx']},{badge_b['circle']['cy']}`，半径 `{badge_b['circle']['r']}`。"
            f"视框 `{badge_a['viewbox']}`，线宽 {badge_a['stroke_width']}。人字用方头。",
        ),
        (
            "badge.light",
            "both",
            "spec_only",
            f"A 的灯矩形从 `{badge_a['light_rect']['x']},{badge_a['light_rect']['y']}` 起，"
            f"宽 {badge_a['light_rect']['width']} 高 {badge_a['light_rect']['height']}，在中线 x={LIGHT_MIDLINE_X} 的左侧。"
            f"B 从 `{badge_b['light_rect']['x']},{badge_b['light_rect']['y']}` 起，同样大小，在右侧。"
            "遮住颜色以后形状和灯位仍要能分开。",
        ),
        (
            "badge.body",
            "ue",
            "spec_only",
            f"两名人形共用 `{SHARED_BODY}`。A 的贴花插槽是 `{badge_a['socket']}`，B 是 `{badge_b['socket']}`。"
            "不要做第二套身体。",
        ),
        (
            "badge.noface",
            "both",
            "spec_only",
            "不按脸认敌我。肩章里不出现 face。不要交肖像贴图。",
        ),
        (
            "naming.decal",
            "both",
            "spec_only",
            f"A 的贴花：Blender `{badge_a['blender']}`，UE `{badge_a['ue']}`。"
            f"B：`{badge_b['blender']}` / `{badge_b['ue']}`。名字里不写青、琥珀或十六进制。",
        ),
        (
            "naming.material",
            "both",
            "spec_only",
            "材质按命名表。Blender 用 `NR_Mat_*`，UE 实例用 `MI_NR_*`。"
            "辅助色实例名带 Aux，角色仍是 auxiliary。母材质和实例都不要交进这个仓。",
        ),
        (
            "naming.notexture",
            "both",
            "no_binary",
            "命名表里 texture 是 `none`。不要交 png、tga、exr 或 `.uasset`。",
        ),
        (
            "scale.units",
            "blender",
            "spec_only",
            "Blender 的 1 米导出成 UE 100 单位，对齐 `ue_units_per_meter`。不要改灰盒配置来迁就模型。",
        ),
        (
            "engine.placeholder",
            "ue",
            "repo_holds_5.4",
            "`NeonRift.uproject` 的 `EngineAssociation` 保持 `5.4`。这条检查不打开编辑器。",
        ),
        (
            "pack.unwired",
            "both",
            "unwired",
            "`wired_into_m2_pack` 为 false。`m2-pack` 的步骤里没有 `m2-art`。"
            "不改 `EVENT_NAMES`，不计分。",
        ),
    )
    return [
        {"id": item_id, "owner": owner, "status": status, "text": text}
        for item_id, owner, status, text in rows
    ]


def build_identity() -> dict:
    tokens = [_token_row(token) for token in TOKEN_ORDER]
    badges = {faction: _badge_row(faction) for faction in ("A", "B")}
    greybox = _greybox()
    return {
        "schema": SCHEMA,
        "id": "NR-M2-art",
        "title": "钢潮港原画身份契约",
        "status": "spec_only_no_uasset",
        "authority": "sim/steel_tide/nr_m2_art.py",
        "palette_source": "sim/steel_tide/palette.py",
        "palette_doc": "docs/art/PALETTE_AND_IDS.md",
        "wired_into_m2_pack": False,
        "event_names_changed": False,
        "scoring_changed": False,
        "match": False,
        "texture_binaries": False,
        "uasset": False,
        "umap": False,
        "cook": False,
        "engine_association": ENGINE_ASSOCIATION,
        "ue_units_per_meter": int(greybox["ue_units_per_meter"]),
        "map_slice": greybox["map_slice"],
        "color_is_identity": False,
        "face_is_identity": False,
        "light_midline_x": LIGHT_MIDLINE_X,
        "shared_body": SHARED_BODY,
        "harbor_tokens": tokens,
        "badges": badges,
        "naming": _naming_rows(tokens, badges),
        "checklist": _checklist(tokens, badges),
    }


def _binaries_present() -> bool:
    return any(REPO_ROOT.rglob("*.uasset")) or any(REPO_ROOT.rglob("*.umap"))


def invariants(doc: dict) -> list[str]:
    """Fail when the contract drifts from palette.py, the svg, or the repo rules."""
    errors: list[str] = []
    if doc.get("schema") != SCHEMA:
        errors.append("schema drifted")
    if doc.get("wired_into_m2_pack") is not False or wired_into_m2_pack():
        errors.append("wired_into_m2_pack must stay false")
    if doc.get("event_names_changed") is not False:
        errors.append("event_names_changed must stay false")
    if doc.get("scoring_changed") is not False:
        errors.append("scoring_changed must stay false")
    if doc.get("match") is not False:
        errors.append("art identity must not run a match")
    for flag in ("texture_binaries", "uasset", "umap", "cook", "color_is_identity", "face_is_identity"):
        if doc.get(flag) is not False:
            errors.append(f"{flag} must stay false")
    if _engine_association() != ENGINE_ASSOCIATION or doc.get("engine_association") != ENGINE_ASSOCIATION:
        errors.append(f"EngineAssociation is not {ENGINE_ASSOCIATION}")
    greybox = _greybox()
    if greybox.get("ue_units_per_meter") != 100 or doc.get("ue_units_per_meter") != 100:
        errors.append("ue_units_per_meter is not 100")
    if greybox.get("map_slice") != "SteelTidePort" or doc.get("map_slice") != "SteelTidePort":
        errors.append("map slice is not SteelTidePort")
    if doc.get("shared_body") != SHARED_BODY or doc.get("light_midline_x") != LIGHT_MIDLINE_X:
        errors.append("shared body or light midline drifted")

    tokens = doc.get("harbor_tokens")
    if not isinstance(tokens, list) or [item.get("token") for item in tokens] != list(TOKEN_ORDER):
        errors.append("harbor token order drifted")
        tokens = []
    hexes: list[str] = []
    palette_text = PALETTE_DOC.read_text(encoding="utf-8") if PALETTE_DOC.is_file() else ""
    if not palette_text:
        errors.append("palette doc is missing")
    for item in tokens:
        src = PALETTE.get(item.get("token"))
        if src is None:
            errors.append(f"unknown token {item.get('token')}")
            continue
        if item.get("id") != src["id"] or item.get("hex") != src["hex"] or item.get("role") != src["role"]:
            errors.append(f"{item.get('token')} drifted from palette.py")
        if item.get("use") != USES.get(item.get("token")):
            errors.append(f"{item.get('token')} use drifted")
        if item.get("team_identity") is not False or item.get("texture") != "none":
            errors.append(f"{item.get('id')} is marked as a team id or carries a texture")
        family = "harbor" if item.get("token") in HARBOR_ORDER else "auxiliary"
        if item.get("family") != family:
            errors.append(f"{item.get('token')} family drifted")
        if family == "harbor" and item.get("role") != "environment":
            errors.append(f"{item.get('id')} harbor token is not environment")
        if family == "auxiliary" and item.get("role") != "auxiliary":
            errors.append(f"{item.get('id')} auxiliary token is not auxiliary")
        blender, ue = MATERIAL_NAMES[item["token"]]
        if item.get("blender") != blender or item.get("ue") != ue:
            errors.append(f"{item.get('id')} material name drifted")
        if item.get("token") == "wet_concrete":
            if item.get("roughness") != "high" or item.get("reflection_required_for_readability") is not False:
                errors.append("wet concrete no longer reads without a reflection")
        elif item.get("roughness") is not None or item.get("reflection_required_for_readability") is not None:
            errors.append(f"{item.get('token')} grew a roughness rule it does not have")
        if item.get("id") not in palette_text or item.get("hex") not in palette_text:
            errors.append(f"{item.get('id')} is missing from PALETTE_AND_IDS.md")
        if item.get("use") not in palette_text:
            errors.append(f"{item.get('token')} use is missing from PALETTE_AND_IDS.md")
        hexes.append(item.get("hex"))
    if len(hexes) != len(set(hexes)):
        errors.append("palette hex values are not unique")

    badges = doc.get("badges") if isinstance(doc.get("badges"), dict) else {}
    if list(badges) != ["A", "B"]:
        errors.append("badge factions drifted")
    signatures = {}
    for faction in ("A", "B"):
        badge = badges.get(faction)
        if not isinstance(badge, dict):
            errors.append(f"badge {faction} missing")
            continue
        spec = EXPECTED_GEOMETRY[faction]
        src = BADGES[faction]
        parsed = parse_badge_svg(badge_svg(faction))
        if badge.get("shape") != src["shape"] or badge.get("shape") != spec["shape"]:
            errors.append(f"badge {faction} shape drifted")
        if badge.get("light_slot") != src["light_slot"] or badge.get("light_id") != src["light_id"]:
            errors.append(f"badge {faction} light slot drifted")
        if badge.get("points") != spec["points"] or badge.get("closed") is not spec["closed"]:
            errors.append(f"badge {faction} geometry drifted")
        if _circle_dict(spec["circle"]) != badge.get("circle"):
            errors.append(f"badge {faction} circle drifted")
        if _rect_dict(spec["light_rect"]) != badge.get("light_rect"):
            errors.append(f"badge {faction} light rect drifted")
        if parsed["points"] != spec["points"] or parsed["circle"] != spec["circle"]:
            errors.append(f"badge {faction} svg does not match the geometry contract")
        if parsed["light_rect"] != spec["light_rect"] or parsed["primitive"] != spec["primitive"]:
            errors.append(f"badge {faction} svg primitive drifted")
        if parsed["shape"] != spec["shape"] or parsed["light_slot"] != spec["light_slot"]:
            errors.append(f"badge {faction} svg identity attrs drifted")
        if parsed["viewbox"] != spec["viewbox"] or parsed["stroke_width"] != spec["stroke_width"]:
            errors.append(f"badge {faction} viewbox or stroke drifted")
        if parsed["stroke_linecap"] != spec["stroke_linecap"] or parsed["fill"] != "none":
            errors.append(f"badge {faction} stroke style drifted")
        if parsed["closed"] is not spec["closed"]:
            errors.append(f"badge {faction} open/closed flag drifted")
        aux = PALETTE[src["aux"]]
        if parsed["light_fill"] != aux["hex"] or parsed["stroke"] != aux["hex"]:
            errors.append(f"badge {faction} lamp is not the auxiliary tint")
        if parsed["color_role"] != "auxiliary" or parsed["aux"] != src["aux"] or parsed["title"] != src["id"]:
            errors.append(f"badge {faction} color role drifted")
        if badge.get("aux_hex") != aux["hex"] or badge.get("aux_role") != "auxiliary":
            errors.append(f"badge {faction} aux record drifted")
        if badge.get("color_is_identity") is not False or badge.get("texture") != "none":
            errors.append(f"badge {faction} treats color or a texture as identity")
        if badge.get("body_id") != SHARED_BODY:
            errors.append(f"badge {faction} does not use {SHARED_BODY}")
        rect = badge.get("light_rect") or {}
        x = rect.get("x")
        if badge.get("light_slot") == "shoulder_left" and not (isinstance(x, int) and x < LIGHT_MIDLINE_X):
            errors.append("open chevron lamp is not left of the midline")
        if badge.get("light_slot") == "shoulder_right" and not (isinstance(x, int) and x > LIGHT_MIDLINE_X):
            errors.append("closed ring lamp is not right of the midline")
        svg = badge_svg(faction)
        if badge_identity(svg) != (spec["shape"], spec["light_slot"]):
            errors.append(f"badge {faction} identity {badge_identity(svg)}")
        if "face" in svg.lower():
            errors.append("badge svg mentions a face")
        path = REPO_ROOT / src["file"]
        if not path.is_file() or path.read_text(encoding="utf-8") != svg:
            errors.append(f"{src['file']} drifted from palette.badge_svg")
        signatures[faction] = geometry_signature(svg)
        masked = [greyscale_badge(svg)]
        masked.extend(colorblind_badge(svg, mode) for mode in _COLORBLIND)
        for variant in masked:
            if badge_identity(variant) != (spec["shape"], spec["light_slot"]):
                errors.append(f"color-masked {faction} badge changed identity")
            if geometry_signature(variant) != signatures[faction]:
                errors.append(f"color mask changed {faction} geometry")
    if signatures.get("A") and signatures.get("A") == signatures.get("B"):
        errors.append("masked badge geometry does not separate A and B")
    if len(badges) == 2:
        if badges["A"].get("shape") == badges["B"].get("shape") or badges["A"].get("light_slot") == badges["B"].get("light_slot"):
            errors.append("A and B share a shape or a light slot")

    naming = doc.get("naming") if isinstance(doc.get("naming"), list) else []
    material_ids = [row.get("id") for row in naming if row.get("kind") == "material"]
    decal_ids = [row.get("id") for row in naming if row.get("kind") == "decal"]
    expected_materials = [PALETTE[token]["id"] for token in TOKEN_ORDER]
    expected_decals = [BADGES[faction]["id"] for faction in ("A", "B")]
    if material_ids != expected_materials:
        errors.append("material naming table does not cover the palette once")
    if decal_ids != expected_decals:
        errors.append("decal naming table does not cover both badges")
    seen_names: set[str] = set()
    for row in naming:
        if row.get("texture") != "none" or row.get("binary") is not False:
            errors.append(f"{row.get('id')} names a texture binary")
        if row.get("color_is_identity") is not False:
            errors.append(f"{row.get('id')} uses color as identity")
        for label in ("blender", "ue"):
            name = row.get(label)
            if not isinstance(name, str) or name in seen_names:
                errors.append(f"naming collision on {name}")
            else:
                seen_names.add(name)
        if row.get("kind") == "decal":
            blob = f"{row.get('blender')} {row.get('ue')}".lower()
            if any(word in blob for word in _DECAL_COLOR_WORDS):
                errors.append(f"{row.get('id')} decal name carries a color")
            if row.get("team_identity") is not True or row.get("hex") is not None:
                errors.append(f"{row.get('id')} decal row drifted")
            if row.get("body_id") != SHARED_BODY:
                errors.append(f"{row.get('id')} decal is not on {SHARED_BODY}")
        elif row.get("kind") == "material":
            if row.get("team_identity") is not False or row.get("hex") is None:
                errors.append(f"{row.get('id')} material row drifted")
        else:
            errors.append(f"unknown naming kind {row.get('kind')}")

    checklist = doc.get("checklist") if isinstance(doc.get("checklist"), list) else []
    if [item.get("id") for item in checklist] != list(CHECKLIST_IDS):
        errors.append("checklist ids drifted")
    blob = "\n".join(item.get("text", "") for item in checklist if isinstance(item, dict))
    for item in tokens:
        if item.get("id") not in blob or item.get("hex") not in blob:
            errors.append(f"checklist dropped {item.get('id')}")
    for faction, badge in badges.items():
        if badge.get("blender") not in blob or badge.get("ue") not in blob:
            errors.append(f"checklist dropped {faction} decal name")
        if badge.get("shape") not in blob:
            errors.append(f"checklist dropped {faction} shape")
    binaries = _binaries_present()
    if binaries:
        errors.append("repo contains a .uasset or .umap")
    for item in checklist:
        if not isinstance(item, dict):
            errors.append("checklist row is not an object")
            continue
        status = item.get("status")
        if item.get("id") == "naming.notexture" and (status != "no_binary" or binaries):
            errors.append("notexture checklist does not match the repo")
        elif item.get("id") == "engine.placeholder" and status != "repo_holds_5.4":
            errors.append("engine checklist status drifted")
        elif item.get("id") == "pack.unwired" and status != "unwired":
            errors.append("pack checklist status drifted")
        elif item.get("id") not in {"naming.notexture", "engine.placeholder", "pack.unwired"} and status != "spec_only":
            errors.append(f"{item.get('id')} status drifted")
        if "face" in item.get("text", "").lower() and item.get("id") != "badge.noface":
            errors.append("checklist mentions a face outside the no-face row")
    return errors


def render_json(doc: dict) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def _geom_text(badge: dict) -> str:
    if badge["primitive"] == "polyline":
        return badge["points"]
    circle = badge["circle"]
    return f"{circle['cx']},{circle['cy']},{circle['r']}"


def _rect_text(badge: dict) -> str:
    rect = badge["light_rect"]
    return f"{rect['x']},{rect['y']},{rect['width']},{rect['height']}"


def render_evidence(doc: dict) -> str:
    lines = [
        f"# schema {doc['schema']}",
        "# kind art-identity-contract",
        "# match false",
        f"# wired_into_m2_pack {str(doc['wired_into_m2_pack']).lower()}",
        f"# event_names_changed {str(doc['event_names_changed']).lower()}",
        f"# scoring_changed {str(doc['scoring_changed']).lower()}",
        f"# texture_binaries {str(doc['texture_binaries']).lower()}",
        f"# uasset {str(doc['uasset']).lower()}",
        f"# umap {str(doc['umap']).lower()}",
        f"# cook {str(doc['cook']).lower()}",
        f"# engine_association {doc['engine_association']}",
        f"# ue_units_per_meter {doc['ue_units_per_meter']}",
        f"# map_slice {doc['map_slice']}",
        f"# color_is_identity {str(doc['color_is_identity']).lower()}",
        f"# face_is_identity {str(doc['face_is_identity']).lower()}",
        f"# shared_body {doc['shared_body']}",
        f"# light_midline_x {doc['light_midline_x']}",
        "# columns materials: token id hex role family blender ue texture",
    ]
    for row in doc["naming"]:
        if row["kind"] != "material":
            continue
        lines.append(
            "\t".join(
                (
                    row["token"],
                    row["id"],
                    row["hex"],
                    row["role"],
                    row["family"],
                    row["blender"],
                    row["ue"],
                    row["texture"],
                )
            )
        )
    lines.append("# columns decals: faction shape light_slot id light_id primitive geometry light_rect closed blender ue socket texture")
    for faction in ("A", "B"):
        badge = doc["badges"][faction]
        lines.append(
            "\t".join(
                (
                    faction,
                    badge["shape"],
                    badge["light_slot"],
                    badge["id"],
                    badge["light_id"],
                    badge["primitive"],
                    _geom_text(badge),
                    _rect_text(badge),
                    str(badge["closed"]).lower(),
                    badge["blender"],
                    badge["ue"],
                    badge["socket"],
                    badge["texture"],
                )
            )
        )
    lines.append("# columns checklist: id owner status")
    for item in doc["checklist"]:
        lines.append(f"{item['id']}\t{item['owner']}\t{item['status']}")
    lines.append(
        f"# counts materials={sum(row['kind'] == 'material' for row in doc['naming'])} "
        f"decals={sum(row['kind'] == 'decal' for row in doc['naming'])} "
        f"checklist={len(doc['checklist'])}"
    )
    return "\n".join(lines) + "\n"


def render_spec(doc: dict) -> str:
    """Operator checklist. The same rows are in config/m2_art_identity.json."""
    lines = [
        "# M2 原画资产规格",
        "",
        "给 Blender 操作和游戏组-虚幻引擎操作。这一份把港区色板、阵营肩章几何、贴花和材质命名收成一张可核对的身份契约。",
        "",
        "仓内命令：",
        "",
        "```bash",
        "PYTHONPATH=sim python3 -m steel_tide m2-art --check",
        "```",
        "",
        "`wired_into_m2_pack` 为 false。这条不进 `m2-pack` 的步骤表，不跑一局，不改 `EVENT_NAMES`，不计分。"
        f"`EngineAssociation` 仍是 `{doc['engine_association']}`。不交贴图二进制，不交 `.uasset`。",
        "",
        "权威脚本是 `sim/steel_tide/nr_m2_art.py`。色值来自 `sim/steel_tide/palette.py`。"
        "机器可读的同一张表是 `config/m2_art_identity.json`。"
        "肩章文件仍是 `docs/art/badges/badge_A_open_chevron.svg` 和 `docs/art/badges/badge_B_closed_ring.svg`。"
        "环境参考是 `docs/kickoff/refs/01_Neon_Bay.png`，它不是贴图源。",
        "代理轮廓仍以 `docs/art/NR03_PROXIES.json` 为准。这张表不新造兽或四足机的网格。",
        "",
        "UE 仍挂。这条 `--check` 不打开编辑器。",
        "",
        "## 港区色板",
        "",
        "队标是肩章形状和肩灯位置。十六进制只是辅助。五个环境色是港区，两个辅助色只给对应阵营的灯和描边上色。",
        "",
        "| token | id | hex | role | family | use |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in doc["harbor_tokens"]:
        lines.append(
            f"| `{item['token']}` | `{item['id']}` | `{item['hex']}` | {item['role']} | {item['family']} | {item['use']} |"
        )
    lines.extend(
        [
            "",
            "| token | Blender | UE 实例 | 备注 |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in doc["harbor_tokens"]:
        lines.append(
            f"| `{item['token']}` | `{item['blender']}` | `{item['ue']}` | {_NOTE_ZH[item['token']]} |"
        )
    lines.extend(
        [
            "",
            "## 肩章几何",
            "",
            f"视框 `0 0 64 64`。中线 x={doc['light_midline_x']}。"
            "灯矩形的 x 小于中线是左肩，大于中线是右肩。线宽 6，形状不填色。"
            f"两名人形共用 `{doc['shared_body']}`。",
            "",
            "| faction | shape | light | socket | primitive | geometry | light rect | stroke | closed | aux |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for faction in ("A", "B"):
        badge = doc["badges"][faction]
        cap = badge["stroke_linecap"] or "none"
        lines.append(
            f"| {faction} | `{badge['shape']}` | `{badge['light_slot']}` `{badge['light_id']}` | "
            f"`{badge['socket']}` | {badge['primitive']} | `{_geom_text(badge)}` | `{_rect_text(badge)}` | "
            f"{badge['stroke_width']} {cap} | {str(badge['closed']).lower()} | `{badge['aux']}` `{badge['aux_hex']}` |"
        )
    lines.extend(
        [
            "",
            "A 的几何是开口折线，没有圆。B 的几何是圆，没有折线。灰度或色盲模拟只改辅助色，不改这两行。",
            "",
            "## 贴花与材质命名",
            "",
            "贴花这一行的队标是形状和灯位。`color_is_identity` 为 false。名字里不写辅助色，也不写十六进制。`texture` 全部是 `none`。",
            "",
            "| kind | id | Blender | UE | socket | texture |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in doc["naming"]:
        socket = row["socket"] or "none"
        lines.append(
            f"| {row['kind']} | `{row['id']}` | `{row['blender']}` | `{row['ue']}` | `{socket}` | `{row['texture']}` |"
        )
    lines.extend(
        [
            "",
            "## 核对清单",
            "",
            "格子留给 Blender / UE 操作员上机时做。仓内 `--check` 核对这些行还在，不把未做的网格算成已交。",
            "",
            "| id | 交给 | 仓内 | 要做的事 |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in doc["checklist"]:
        lines.append(f"| `{item['id']}` | {item['owner']} | {item['status']} | {item['text']} |")
    lines.extend(
        [
            "",
            "## 不要交进这个仓",
            "",
            "- 贴图二进制（png、tga、exr）和 `.uasset` / `.umap`",
            "- 改过的 `EngineAssociation`",
            "- 新的 `EVENT_NAMES`，或另一套计分",
            "- 把 `m2-art` 写进 `m2-pack` 的步骤表",
            "- 把辅助色或脸当成队标",
            "- 为了让这条 `--check` 通过而去打开本机 UE",
            "",
        ]
    )
    return "\n".join(lines)


def evidence_paths() -> dict[str, Path]:
    return {
        "identity": IDENTITY_PATH,
        "spec": SPEC_PATH,
        "evidence": EVIDENCE_PATH,
    }


def rendered_texts(doc: dict | None = None) -> dict[str, str]:
    doc = build_identity() if doc is None else doc
    return {
        "identity": render_json(doc),
        "spec": render_spec(doc),
        "evidence": render_evidence(doc),
    }


def diff_committed(doc: dict | None = None) -> list[str]:
    doc = build_identity() if doc is None else doc
    errors: list[str] = []
    for key, text in rendered_texts(doc).items():
        path = evidence_paths()[key]
        if not path.is_file():
            errors.append(f"missing {path.relative_to(REPO_ROOT).as_posix()}")
            continue
        if path.read_text(encoding="utf-8") != text:
            errors.append(f"drifted: {path.relative_to(REPO_ROOT).as_posix()}")
    return errors


def write_outputs(doc: dict | None = None) -> None:
    doc = build_identity() if doc is None else doc
    for key, text in rendered_texts(doc).items():
        path = evidence_paths()[key]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")


def _rules_snapshot() -> dict:
    import steel_tide.events as events_mod

    return {
        "events": events_mod.EVENT_NAMES,
        "events_file": (REPO_ROOT / "sim" / "steel_tide" / "events.py").read_bytes(),
        "greybox": CONFIG_PATH.read_bytes(),
        "match": (REPO_ROOT / "sim" / "steel_tide" / "match.py").read_bytes(),
    }


def _snapshot_errors(snapshot: dict) -> list[str]:
    import steel_tide.events as events_mod

    errors: list[str] = []
    if events_mod.EVENT_NAMES != snapshot["events"]:
        errors.append("EVENT_NAMES changed while checking art identity")
    if (REPO_ROOT / "sim" / "steel_tide" / "events.py").read_bytes() != snapshot["events_file"]:
        errors.append("events.py changed while checking art identity")
    if CONFIG_PATH.read_bytes() != snapshot["greybox"]:
        errors.append("greybox config changed while checking art identity")
    if (REPO_ROOT / "sim" / "steel_tide" / "match.py").read_bytes() != snapshot["match"]:
        errors.append("match.py changed while checking art identity")
    return errors


def acceptance_errors(doc: dict | None = None) -> list[str]:
    return invariants(build_identity() if doc is None else doc)


def _pass_line(doc: dict) -> str:
    materials = sum(row["kind"] == "material" for row in doc["naming"])
    decals = sum(row["kind"] == "decal" for row in doc["naming"])
    return (
        "wired_into_m2_pack=false "
        "event_names_changed=false "
        "scoring_changed=false "
        f"harbor_tokens={len(doc['harbor_tokens'])} "
        "badges=A:open_chevron/shoulder_left,B:closed_ring/shoulder_right "
        f"materials={materials} decals={decals} checklist={len(doc['checklist'])} "
        "texture_binaries=false uasset=false "
        f"engine_association={doc['engine_association']}"
    )


def main(argv: list[str] | None = None) -> int:
    args = [] if argv is None else list(argv)
    if args not in ([], ["--check"]):
        print("usage: PYTHONPATH=sim python3 -m steel_tide m2-art [--check]", flush=True)
        return 2
    snapshot = _rules_snapshot()
    doc = build_identity()
    errors = acceptance_errors(doc)
    errors.extend(_snapshot_errors(snapshot))
    if args == ["--check"]:
        errors.extend(diff_committed(doc))
    elif not errors:
        write_outputs(doc)
        errors.extend(_snapshot_errors(snapshot))
    if errors:
        print("NR-M2 art FAIL", flush=True)
        for error in errors:
            print(f"  - {error}", flush=True)
        return 1
    print("NR-M2 art PASS", flush=True)
    print(_pass_line(doc), flush=True)
    for key, path in evidence_paths().items():
        print(f"{key}={path.relative_to(REPO_ROOT).as_posix()}", flush=True)
    if args == ["--check"]:
        print("checked identity, asset spec, and evidence", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
