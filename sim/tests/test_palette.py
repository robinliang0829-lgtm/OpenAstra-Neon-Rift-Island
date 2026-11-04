import unittest
import xml.etree.ElementTree as etree
from pathlib import Path

from steel_tide.config import CONFIG_PATH, load_config
from steel_tide.palette import BADGES, PALETTE, badge_svg

ROOT = CONFIG_PATH.parents[1]
SPEC = ROOT / "docs" / "art" / "PALETTE_AND_IDS.md"


class PaletteTests(unittest.TestCase):
    def test_ids_are_in_the_spec_and_match_faction_badges(self):
        text = SPEC.read_text(encoding="utf-8")
        config = load_config()
        for token in (*PALETTE.values(), *BADGES.values()):
            self.assertIn(token["id"] if "id" in token else token, text)
        for faction, badge in BADGES.items():
            self.assertIn(badge["id"], text)
            self.assertIn(badge["light_id"], text)
            self.assertEqual(config.badges[faction]["shape"], badge["shape"])
            self.assertEqual(config.badges[faction]["light_slot"], badge["light_slot"])
            self.assertEqual(PALETTE[badge["aux"]]["role"], "auxiliary")
        for token in PALETTE.values():
            self.assertIn(token["hex"], text)
        self.assertNotIn("face", text.lower())

    def test_badge_svgs_keep_shape_identity_without_a_face(self):
        for faction, badge in BADGES.items():
            path = ROOT / badge["file"]
            rendered = badge_svg(faction)
            self.assertEqual(path.read_text(encoding="utf-8"), rendered)
            root = etree.fromstring(rendered)
            self.assertEqual(root.attrib["viewBox"], "0 0 64 64")
            self.assertEqual(root.attrib["data-badge-id"], badge["id"])
            self.assertEqual(root.attrib["data-shape"], badge["shape"])
            self.assertEqual(root.attrib["data-light-slot"], badge["light_slot"])
            self.assertEqual(root.attrib["data-color-role"], "auxiliary")
            self.assertNotIn("face", rendered.lower())
        chevron = etree.fromstring(badge_svg("A"))
        ring = etree.fromstring(badge_svg("B"))
        self.assertEqual(chevron.find("{http://www.w3.org/2000/svg}polyline").attrib["points"], "16,44 32,20 48,44")
        self.assertIsNone(chevron.find("{http://www.w3.org/2000/svg}circle"))
        self.assertIsNotNone(ring.find("{http://www.w3.org/2000/svg}circle"))
        self.assertIsNone(ring.find("{http://www.w3.org/2000/svg}polyline"))
        self.assertFalse(list(ROOT.rglob("*.umap")))


if __name__ == "__main__":
    unittest.main()