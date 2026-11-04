import json
import re
import unittest
from pathlib import Path

from steel_tide.config import CONFIG_PATH
from steel_tide.events import EVENT_GROUPS, EVENT_NAMES
from steel_tide.layout import LAYOUT_PATH, greybox_layout

ROOT = CONFIG_PATH.parents[1]
MATCH = ROOT / "sim" / "steel_tide" / "match.py"
HEADER = ROOT / "Source" / "NeonRift" / "Public" / "NeonRiftEventNames.h"
WIRING = ROOT / "docs" / "rules" / "UE_EVENT_WIRING.md"
NR01 = ROOT / "docs" / "NR-01.md"


def sim_emit_names() -> set[str]:
    source = MATCH.read_text(encoding="utf-8")
    names = set(re.findall(r'_emit\(\s*"([A-Za-z]+)"', source))
    names.update(re.findall(r'_server_only\(\s*[A-Za-z_]+\s*,\s*"([A-Za-z]+)"', source))
    return names


def header_names() -> set[str]:
    return set(re.findall(r'TEXT\("([A-Za-z]+)"\)', HEADER.read_text(encoding="utf-8")))


def wiring_names() -> set[str]:
    names: set[str] = set()
    in_table = False
    for line in WIRING.read_text(encoding="utf-8").splitlines():
        if line.startswith("| 事件 |"):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            break
        if line.startswith("| ---"):
            continue
        names.update(re.findall(r"`([A-Za-z]+)`", line.split("|")[1]))
    return names


class UEContractTests(unittest.TestCase):
    def test_event_groups_cover_the_sim_once(self):
        self.assertEqual(tuple(sorted(EVENT_NAMES)), tuple(sorted(set(EVENT_NAMES))))
        covered = [name for group in EVENT_GROUPS.values() for name in group]
        self.assertEqual(sorted(covered), sorted(EVENT_NAMES))

    def test_event_names_match_sim_header_and_wiring(self):
        expected = set(EVENT_NAMES)
        self.assertEqual(sim_emit_names(), expected)
        self.assertEqual(header_names(), expected)
        self.assertEqual(wiring_names(), expected)
        for group, names in EVENT_GROUPS.items():
            source = (ROOT / "Source" / "NeonRift" / "Private" / f"NeonRift{group}.cpp").read_text(encoding="utf-8")
            for name in names:
                self.assertIn(f"NeonRiftEvents::{name}", source)

    def test_uproject_is_a_54_placeholder(self):
        project = json.loads((ROOT / "NeonRift.uproject").read_text(encoding="utf-8"))
        self.assertEqual(project["EngineAssociation"], "5.4")
        self.assertEqual(project["Modules"][0]["Name"], "NeonRift")
        self.assertTrue((ROOT / "Source" / "NeonRift" / "NeonRift.Build.cs").is_file())
        self.assertTrue((ROOT / "Source" / "NeonRift.Target.cs").is_file())
        self.assertTrue((ROOT / "Source" / "NeonRiftEditor.Target.cs").is_file())

    def test_nr01_layout_matches_the_sim(self):
        layout = greybox_layout()
        on_disk = json.loads(LAYOUT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(on_disk, layout)
        self.assertEqual(layout["routes"]["elevated_spawn_a_to_center"]["length_m"], 48)
        self.assertEqual(layout["routes"]["repair_alley_spawn_a_to_center"]["length_m"], 84)
        self.assertEqual(layout["routes"]["elevated_spawn_a_to_center"]["walk_seconds_at_walk_speed"], 8)
        self.assertEqual(layout["routes"]["repair_alley_spawn_a_to_center"]["walk_seconds_at_walk_speed"], 14)
        self.assertEqual(layout["status"], "layout_only_no_umap")
        card = NR01.read_text(encoding="utf-8")
        for name, actor in layout["actors"].items():
            self.assertIn(name, card)
            self.assertIn(f"({actor['x_uu']}, {actor['y_uu']}, 0)", card)
        self.assertFalse(list((ROOT / "Content").rglob("*.umap")))
        self.assertFalse(list(ROOT.rglob("*.uasset")))


if __name__ == "__main__":
    unittest.main()
