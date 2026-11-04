import json
import unittest
from pathlib import Path

from steel_tide.config import CONFIG_PATH, load_config
from steel_tide.events import EVENT_NAMES
from steel_tide.nr03 import acceptance_errors, diff_committed, run_nr03_bridge
from steel_tide.palette import badge_identity, badge_svg, geometry_signature, greyscale_badge

ROOT = CONFIG_PATH.parents[1]


class ReadabilitySliceTests(unittest.TestCase):
    def test_proxies_badges_and_bridge_sequence(self):
        match = run_nr03_bridge()
        self.assertEqual(acceptance_errors(match), [])
        self.assertEqual(diff_committed(match), [])
        self.assertEqual(load_config().light_strip_lamps(), 5)
        self.assertIn("BridgeLightStripAdvanced", EVENT_NAMES)
        self.assertIn("BridgeWarningCompleted", EVENT_NAMES)
        self.assertIn("BridgeWarningStarted", EVENT_NAMES)

    def test_color_mask_keeps_shape_and_shoulder_slot(self):
        chevron = badge_svg("A")
        ring = badge_svg("B")
        self.assertNotEqual(geometry_signature(chevron), geometry_signature(ring))
        self.assertEqual(geometry_signature(greyscale_badge(chevron)), geometry_signature(chevron))
        self.assertEqual(badge_identity(greyscale_badge(chevron)), ("open_chevron", "shoulder_left"))
        self.assertEqual(badge_identity(greyscale_badge(ring)), ("closed_ring", "shoulder_right"))
        self.assertLess(float(chevron.split('rect x="', 1)[1].split('"', 1)[0]), 32)
        self.assertGreater(float(ring.split('rect x="', 1)[1].split('"', 1)[0]), 32)

    def test_docs_name_the_head_inputs_and_the_gaps(self):
        card = (ROOT / "docs" / "NR-03.md").read_text(encoding="utf-8")
        handoff = (ROOT / "docs" / "HANDOFF.md").read_text(encoding="utf-8")
        gaps = (ROOT / "docs" / "art" / "NR03_GAPS.md").read_text(encoding="utf-8")
        self.assertIn("本 PR HEAD", card)
        self.assertIn("docs/art/NR03_PROXIES.json", card)
        self.assertIn("docs/art/PALETTE_AND_IDS.md", card)
        self.assertIn("badge_A_open_chevron.svg", card)
        self.assertIn("badge_B_closed_ring.svg", card)
        self.assertIn("docs/art/NR03_GAPS.md", card)
        self.assertIn("readable_without_reflection", card)
        self.assertIn("python3 -m steel_tide nr03", card)
        self.assertIn("BridgeWarningStarted", card)
        self.assertIn("BridgeWarningCompleted", card)
        self.assertIn("实机录像仍等 UE", card)
        for name in (
            "NR_Proxy_Humanoid_A",
            "NR_Proxy_Humanoid_B",
            "NR_Proxy_Beast",
            "NR_Proxy_Quadruped",
            "NR_Proxy_EngineeringMachine",
            "NR_Proxy_WetConcrete",
        ):
            self.assertIn(name, card)
            self.assertIn(name, gaps)
        self.assertIn("NR-03 规格已入库、实机录像仍等 UE", handoff)
        self.assertIn("Only local UE is missing.", handoff)

    def test_cpp_is_data_and_subscribe_only(self):
        header = (ROOT / "Source" / "NeonRift" / "Public" / "NeonRiftReadability.h").read_text(encoding="utf-8")
        source = (ROOT / "Source" / "NeonRift" / "Private" / "NeonRiftReadability.cpp").read_text(encoding="utf-8")
        names = (ROOT / "Source" / "NeonRift" / "Public" / "NeonRiftEventNames.h").read_text(encoding="utf-8")
        bridge = (ROOT / "Source" / "NeonRift" / "Private" / "NeonRiftBridgeWarn.cpp").read_text(encoding="utf-8")
        state = (ROOT / "Source" / "NeonRift" / "Private" / "NeonRiftGameState.cpp").read_text(encoding="utf-8")
        project = json.loads((ROOT / "NeonRift.uproject").read_text(encoding="utf-8"))
        blob = header + source
        for token in (
            "UDataAsset",
            "open_chevron",
            "closed_ring",
            "shoulder_left",
            "shoulder_right",
            "NR_Proxy_Humanoid_A",
            "NR_Proxy_Humanoid_B",
            "NR_Proxy_Beast",
            "NR_Proxy_Quadruped",
            "NR_Proxy_EngineeringMachine",
            "NR_Proxy_WetConcrete",
            "organic_beast",
            "hydraulic_quadruped",
            "NR_Body_Humanoid",
            "mat.worn_yellow",
            "mat.wet_concrete",
            "BridgeWarningSeconds = 4.f",
        ):
            self.assertIn(token, blob)
        self.assertIn("BridgeWarningStarted", names)
        self.assertIn("BridgeWarningCompleted", names)
        self.assertIn("BridgeLightStripAdvanced", names)
        self.assertIn("NeonRiftEvents::BridgeWarningCompleted", bridge)
        self.assertIn("NeonRiftEvents::BridgeLightStripAdvanced", bridge)
        self.assertIn("NeonRiftEvents::BridgeWarningCompleted", state)
        self.assertIn("NeonRiftEvents::BridgeLightStripAdvanced", state)
        self.assertNotIn("NeonRiftEmit", source)
        self.assertNotIn("PointScored", blob)
        self.assertNotIn("+=", source)
        self.assertEqual(project["EngineAssociation"], "5.4")
        self.assertFalse(list(ROOT.rglob("*.umap")))
        self.assertFalse(list(ROOT.rglob("*.uasset")))
        evidence = ROOT / "docs" / "evidence" / "nr03"
        self.assertFalse(list(evidence.rglob("*.png")))
        self.assertFalse(list(evidence.rglob("*.mp4")))
        self.assertFalse(list(evidence.rglob("*.webm")))


if __name__ == "__main__":
    unittest.main()
