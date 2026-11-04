import json
import unittest

from steel_tide.__main__ import main as cli_main
from steel_tide.config import CONFIG_PATH
from steel_tide.events import EVENT_NAMES
from steel_tide.hud import catalog_ids, cues_for
from steel_tide.model import Event
from steel_tide.nr_m2_hud import PATH_TEXT, WIRED_INTO_M2_PACK, acceptance_errors, diff_committed, main, run_m2_hud
from steel_tide.nr_m2_pack import STEPS
from steel_tide.palette import BADGES

ROOT = CONFIG_PATH.parents[1]


class HudCueTests(unittest.TestCase):
    def test_slice_locks_lines_to_source_events(self):
        match = run_m2_hud()
        self.assertEqual(acceptance_errors(match), [])
        self.assertEqual(diff_committed(match), [])
        self.assertNotIn("HudCue", EVENT_NAMES)
        self.assertFalse(any(event.name == "HudCue" for event in match.events))
        self.assertEqual(match.score, {"A": 2, "B": 0})
        self.assertEqual(match.settled_kind, "points")
        self.assertFalse(WIRED_INTO_M2_PACK)
        families = {cue.payload["family"] for cue in match.hud_cues}
        self.assertEqual(families, {"scoreboard", "read_bar", "spawn_shield", "role_lock", "side_lock"})

    def test_color_is_not_the_faction_id(self):
        match = run_m2_hud()
        self.assertEqual(BADGES["A"]["shape"], "open_chevron")
        self.assertEqual(BADGES["A"]["light_slot"], "shoulder_left")
        self.assertEqual(BADGES["B"]["shape"], "closed_ring")
        self.assertEqual(BADGES["B"]["light_slot"], "shoulder_right")
        point = [cue for cue in match.hud_cues if cue.payload.get("state") == "point"][0]
        self.assertIn("open_chevron", point.payload["line"])
        self.assertIn("shoulder_left", point.payload["line"])
        self.assertNotIn(point.payload["aux_hex"], point.payload["line"])
        self.assertEqual(point.payload["color_role"], "auxiliary")
        self.assertFalse(point.payload["color_is_identity"])
        side = [cue for cue in match.hud_cues if cue.payload.get("cue_id") == "hud.side_lock"][0]
        self.assertIn(side.payload["shape"], side.payload["line"])
        self.assertIn(side.payload["light_slot"], side.payload["line"])
        self.assertNotIn("role", side.payload["source"])

    def test_silent_rejections_draw_no_line(self):
        self.assertEqual(cues_for(None, Event(0, "HitIgnored", {"reason": "shield", "target_id": "a1"}), 0), [])
        self.assertEqual(
            cues_for(
                None,
                Event(0, "RoleRejected", {"combatant_id": "a1", "reason": "unknown_role", "role": "scout"}),
                0,
            ),
            [],
        )
        self.assertEqual(
            cues_for(
                None,
                Event(0, "FactionRejected", {"combatant_id": "a1", "reason": "illegal_faction", "faction": "B"}),
                0,
            ),
            [],
        )

    def test_pack_steps_omit_m2_hud(self):
        self.assertNotIn("m2-hud", [step[0] for step in STEPS])
        self.assertFalse(WIRED_INTO_M2_PACK)
        card = (ROOT / "docs" / "NR-M2-pack.md").read_text(encoding="utf-8")
        self.assertIn("m2-hud", card)
        self.assertIn("不在这张表里", card)

    def test_usage_and_docs(self):
        self.assertEqual(main(["--cook"]), 2)
        self.assertEqual(cli_main(["m2-hud", "--cook"]), 2)
        card = (ROOT / "docs" / "NR-M2-hud.md").read_text(encoding="utf-8")
        handoff = (ROOT / "docs" / "HANDOFF.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("PYTHONPATH=sim python3 -m steel_tide m2-hud --check", card)
        self.assertIn("docs/evidence/nr-m2-hud/hud.log", card)
        self.assertIn("wired_into_m2_pack false", card)
        self.assertIn(PATH_TEXT.split(",")[0], card)
        self.assertIn("NR-M2-hud", handoff)
        self.assertIn("m2-hud --check", readme)
        for cue_id in catalog_ids():
            self.assertIn(cue_id, card)
        project = json.loads((ROOT / "NeonRift.uproject").read_text(encoding="utf-8"))
        self.assertEqual(project["EngineAssociation"], "5.4")
        self.assertFalse(list(ROOT.rglob("*.uasset")))
        self.assertFalse(list((ROOT / "Content").rglob("*.umap")))
        greybox = (ROOT / "config" / "steel_tide_greybox.json").read_text(encoding="utf-8")
        self.assertIn('"points_to_win": 2', greybox)
        self.assertNotIn("HudCue", greybox)


if __name__ == "__main__":
    unittest.main()
