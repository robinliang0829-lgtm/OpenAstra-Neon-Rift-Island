import json
import unittest

from steel_tide.__main__ import main as cli_main
from steel_tide.config import CONFIG_PATH
from steel_tide.events import EVENT_NAMES
from steel_tide.nr_m2_art import (
    CHECKLIST_IDS,
    EVIDENCE_PATH,
    EXPECTED_GEOMETRY,
    IDENTITY_PATH,
    SPEC_PATH,
    TOKEN_ORDER,
    acceptance_errors,
    build_identity,
    diff_committed,
    invariants,
    main,
    wired_into_m2_pack,
)
from steel_tide.nr_m2_pack import STEPS
from steel_tide.palette import BADGES, PALETTE, badge_identity, badge_svg, greyscale_badge

ROOT = CONFIG_PATH.parents[1]
ART_SOURCE = ROOT / "sim" / "steel_tide" / "nr_m2_art.py"
CARD = ROOT / "docs" / "NR-M2-art.md"


class ArtIdentityTests(unittest.TestCase):
    def test_harbor_tokens_match_palette_and_are_not_team_ids(self):
        doc = build_identity()
        self.assertEqual([item["token"] for item in doc["harbor_tokens"]], list(TOKEN_ORDER))
        self.assertEqual(invariants(doc), [])
        families = [item["family"] for item in doc["harbor_tokens"]]
        self.assertEqual(families, ["harbor"] * 5 + ["auxiliary"] * 2)
        hexes = []
        for item in doc["harbor_tokens"]:
            src = PALETTE[item["token"]]
            self.assertEqual(item["id"], src["id"])
            self.assertEqual(item["hex"], src["hex"])
            self.assertEqual(item["role"], src["role"])
            self.assertIs(item["team_identity"], False)
            self.assertEqual(item["texture"], "none")
            hexes.append(item["hex"])
        self.assertEqual(len(hexes), len(set(hexes)))
        concrete = doc["harbor_tokens"][0]
        self.assertEqual(concrete["token"], "wet_concrete")
        self.assertEqual(concrete["roughness"], "high")
        self.assertIs(concrete["reflection_required_for_readability"], False)
        self.assertEqual(doc["harbor_tokens"][5]["aux_for"], "A")
        self.assertEqual(doc["harbor_tokens"][6]["aux_for"], "B")

    def test_badge_geometry_matches_svg_and_survives_grey(self):
        doc = build_identity()
        badge_a = doc["badges"]["A"]
        badge_b = doc["badges"]["B"]
        self.assertEqual(badge_a["shape"], "open_chevron")
        self.assertEqual(badge_a["light_slot"], "shoulder_left")
        self.assertEqual(badge_a["points"], "16,44 32,20 48,44")
        self.assertIsNone(badge_a["circle"])
        self.assertIs(badge_a["closed"], False)
        self.assertEqual(badge_a["light_rect"], {"x": 4, "y": 28, "width": 6, "height": 8})
        self.assertLess(badge_a["light_rect"]["x"], doc["light_midline_x"])
        self.assertEqual(badge_b["shape"], "closed_ring")
        self.assertEqual(badge_b["light_slot"], "shoulder_right")
        self.assertEqual(badge_b["circle"], {"cx": 32, "cy": 32, "r": 16})
        self.assertIsNone(badge_b["points"])
        self.assertIs(badge_b["closed"], True)
        self.assertEqual(badge_b["light_rect"], {"x": 54, "y": 28, "width": 6, "height": 8})
        self.assertGreater(badge_b["light_rect"]["x"], doc["light_midline_x"])
        self.assertEqual(badge_a["body_id"], badge_b["body_id"])
        self.assertEqual(badge_a["socket"], "socket.shoulder_left")
        self.assertEqual(badge_b["socket"], "socket.shoulder_right")
        self.assertIs(badge_a["color_is_identity"], False)
        self.assertIs(badge_b["color_is_identity"], False)
        for faction, spec in EXPECTED_GEOMETRY.items():
            svg = badge_svg(faction)
            self.assertEqual(badge_identity(svg), (spec["shape"], spec["light_slot"]))
            self.assertEqual(badge_identity(greyscale_badge(svg)), (spec["shape"], spec["light_slot"]))
            self.assertNotIn("face", svg.lower())
            self.assertEqual(BADGES[faction]["shape"], spec["shape"])

    def test_naming_table_has_materials_and_colorless_decals(self):
        doc = build_identity()
        materials = [row for row in doc["naming"] if row["kind"] == "material"]
        decals = [row for row in doc["naming"] if row["kind"] == "decal"]
        self.assertEqual([row["id"] for row in materials], [PALETTE[token]["id"] for token in TOKEN_ORDER])
        self.assertEqual([row["id"] for row in decals], ["badge.A.open_chevron", "badge.B.closed_ring"])
        names = [row["blender"] for row in doc["naming"]] + [row["ue"] for row in doc["naming"]]
        self.assertEqual(len(names), len(set(names)))
        for row in doc["naming"]:
            self.assertEqual(row["texture"], "none")
            self.assertIs(row["binary"], False)
            self.assertIs(row["color_is_identity"], False)
        self.assertEqual(decals[0]["ue"], "D_NR_BadgeA_OpenChevron")
        self.assertEqual(decals[1]["blender"], "NR_Decal_BadgeB_ClosedRing")
        for row in decals:
            blob = f"{row['blender']} {row['ue']}".lower()
            for word in ("cyan", "amber", "magenta", "yellow", "#"):
                self.assertNotIn(word, blob)
            self.assertIs(row["team_identity"], True)
            self.assertEqual(row["body_id"], "NR_Body_Humanoid")
        self.assertTrue(materials[5]["ue"].startswith("MI_NR_Aux"))
        self.assertTrue(materials[6]["ue"].startswith("MI_NR_Aux"))

    def test_checklist_and_card_name_the_four_deliverables(self):
        doc = build_identity()
        self.assertEqual([item["id"] for item in doc["checklist"]], list(CHECKLIST_IDS))
        self.assertEqual(doc["checklist"][-1]["status"], "unwired")
        self.assertEqual(doc["checklist"][-2]["status"], "repo_holds_5.4")
        spec = SPEC_PATH.read_text(encoding="utf-8") if SPEC_PATH.is_file() else ""
        card = CARD.read_text(encoding="utf-8")
        for needle in (
            "PYTHONPATH=sim python3 -m steel_tide m2-art --check",
            "wired_into_m2_pack",
            "open_chevron",
            "closed_ring",
            "shoulder_left",
            "shoulder_right",
            "EVENT_NAMES",
            "5.4",
            "config/m2_art_identity.json",
            "docs/art/M2_ASSET_SPEC.md",
            "docs/evidence/nr-m2-art/identity.log",
            "NR_Decal_BadgeA_OpenChevron",
            "D_NR_BadgeB_ClosedRing",
            "NR_Body_Humanoid",
        ):
            self.assertIn(needle, card)
        self.assertIn("原画", card)
        self.assertIn("港区色板", spec)
        self.assertIn("肩章几何", spec)
        self.assertIn("贴花与材质命名", spec)
        self.assertIn("核对清单", spec)

    def test_committed_contract_matches_the_builder(self):
        doc = build_identity()
        self.assertEqual(diff_committed(doc), [])
        self.assertEqual(acceptance_errors(doc), [])
        identity = json.loads(IDENTITY_PATH.read_text(encoding="utf-8"))
        self.assertIs(identity["wired_into_m2_pack"], False)
        self.assertIs(identity["event_names_changed"], False)
        self.assertIs(identity["scoring_changed"], False)
        self.assertIs(identity["match"], False)
        self.assertEqual(identity["engine_association"], "5.4")
        evidence = EVIDENCE_PATH.read_text(encoding="utf-8")
        self.assertIn("# wired_into_m2_pack false\n", evidence)
        self.assertIn("# event_names_changed false\n", evidence)
        self.assertIn("# scoring_changed false\n", evidence)
        self.assertIn("# match false\n", evidence)
        self.assertIn("A\topen_chevron\tshoulder_left\t", evidence)
        self.assertIn("B\tclosed_ring\tshoulder_right\t", evidence)
        self.assertIn("16,44 32,20 48,44", evidence)
        self.assertIn("32,32,16", evidence)

    def test_check_leaves_events_scoring_and_pack_alone(self):
        events_before = EVENT_NAMES
        events_bytes = (ROOT / "sim" / "steel_tide" / "events.py").read_bytes()
        match_bytes = (ROOT / "sim" / "steel_tide" / "match.py").read_bytes()
        greybox_bytes = CONFIG_PATH.read_bytes()
        pack_source = (ROOT / "sim" / "steel_tide" / "nr_m2_pack.py").read_text(encoding="utf-8")
        self.assertIs(wired_into_m2_pack(), False)
        self.assertNotIn("m2-art", [step[0] for step in STEPS])
        self.assertFalse(any("m2-art" in args for _name, _module, args in STEPS))
        self.assertNotIn("m2-art", pack_source)
        source = ART_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("SteelTideMatch", source)
        self.assertNotIn("EVENT_NAMES =", source)
        self.assertEqual(main(["--check"]), 0)
        self.assertEqual(cli_main(["m2-art", "--check"]), 0)
        self.assertEqual(EVENT_NAMES, events_before)
        self.assertEqual((ROOT / "sim" / "steel_tide" / "events.py").read_bytes(), events_bytes)
        self.assertEqual((ROOT / "sim" / "steel_tide" / "match.py").read_bytes(), match_bytes)
        self.assertEqual(CONFIG_PATH.read_bytes(), greybox_bytes)
        project = json.loads((ROOT / "NeonRift.uproject").read_text(encoding="utf-8"))
        self.assertEqual(project["EngineAssociation"], "5.4")
        self.assertFalse(list(ROOT.rglob("*.uasset")))
        self.assertFalse(list(ROOT.rglob("*.umap")))
        self.assertFalse(list((ROOT / "Source").rglob("NeonRift*Cues.h")))
        greybox = json.loads(greybox_bytes.decode("utf-8"))
        self.assertEqual(greybox["points_to_win"], 2)

    def test_usage_and_a_bad_token_fail(self):
        self.assertEqual(main(["--cook"]), 2)
        self.assertEqual(cli_main(["m2-art", "--cook"]), 2)
        doc = build_identity()
        doc["harbor_tokens"][0]["hex"] = "#000000"
        self.assertTrue(invariants(doc))
        doc = build_identity()
        doc["wired_into_m2_pack"] = True
        self.assertTrue(any("wired_into_m2_pack" in error for error in invariants(doc)))
        doc = build_identity()
        doc["badges"]["A"]["points"] = "0,0 1,1 2,2"
        self.assertTrue(invariants(doc))


if __name__ == "__main__":
    unittest.main()
