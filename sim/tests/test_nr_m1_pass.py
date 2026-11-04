import json
import unittest

from steel_tide.config import CONFIG_PATH, load_config
from steel_tide.dual_log import diff_against_evidence
from steel_tide.match import SteelTideMatch
from steel_tide.nr_m1_pass import (
    EVIDENCE_DIR,
    acceptance_errors,
    evaluate_slice,
    run_m1_pass_match,
)

ROOT = CONFIG_PATH.parents[1]


class SliceTests(unittest.TestCase):
    def test_pass_slice_matches_the_sample_logs(self):
        match = run_m1_pass_match()
        self.assertEqual(acceptance_errors(match), [])
        logs, errors = evaluate_slice(match)
        self.assertEqual(errors, [])
        self.assertEqual(diff_against_evidence(logs, EVIDENCE_DIR), [])
        bodies = []
        for end in ("server", "client-a", "client-b"):
            text = logs[end]
            self.assertIn("# schema nr-m1-pass-dual-end-v1\n", text)
            self.assertIn("# identities ", text)
            body = text.split("# comparable event_body_identical\n", 1)[1]
            bodies.append(body)
            self.assertIn("CorePassed", body)
            self.assertIn("holding_core", body)
            self.assertIn("left_terminal", body)
            self.assertIn('"kind": "points"', body)
        self.assertEqual(bodies[0], bodies[1])
        self.assertEqual(bodies[1], bodies[2])
        self.assertNotIn("OvertimeStarted", bodies[0])

    def test_drop_clears_the_dash_block(self):
        match = SteelTideMatch(load_config())
        match.add_combatant("a1", "client-a", "humanoid_robot", "human", preferred_route="elevated")
        match.add_combatant("b1", "client-b", "humanoid_robot", "human", preferred_route="elevated")
        match.choose_faction("a1", "A")
        match.choose_faction("b1", "B")
        match.choose_role("a1", "assault")
        match.choose_role("b1", "recon")
        match.start()
        match.place_for_test("a1", "center")
        match.enqueue("client-a", "pick_core", 1.0, combatant_id="a1")
        match.advance_to(1.0)
        match.place_for_test("a1", "terminal_a")
        match.enqueue("client-a", "use_ability", 1.2, combatant_id="a1", ability="dash", dest="bridgehead_a")
        match.advance_to(1.2)
        self.assertEqual(match.named("AbilityRejected")[-1].payload["reason"], "holding_core")
        self.assertEqual(match.combatants["a1"].anchor, "terminal_a")
        self.assertEqual(match.core.holder_id, "a1")
        self.assertEqual(match.core.anchor, "terminal_a")
        self.assertEqual(match.combatants["a1"].ability_ready_ms, 0)
        match.enqueue("client-a", "drop_core", 1.4, combatant_id="a1")
        match.advance_to(1.4)
        self.assertIsNone(match.core.holder_id)
        self.assertEqual(match.core.status, "ground")
        match.enqueue("client-a", "use_ability", 1.6, combatant_id="a1", ability="dash", dest="bridgehead_a")
        match.advance_to(1.6)
        used = match.named("AbilityUsed")[-1]
        self.assertEqual(used.payload["ability"], "dash")
        self.assertEqual(used.payload["from"], "terminal_a")
        self.assertEqual(match.combatants["a1"].anchor, "bridgehead_a")
        self.assertEqual(match.core.anchor, "terminal_a")
        self.assertEqual(match.holder_errors(), [])


class ContractTests(unittest.TestCase):
    def test_card_leaves_ue_hanging_and_names_the_command(self):
        card = (ROOT / "docs" / "NR-M1-pass.md").read_text(encoding="utf-8")
        handoff = (ROOT / "docs" / "HANDOFF.md").read_text(encoding="utf-8")
        source = (ROOT / "sim" / "steel_tide" / "nr_m1_pass.py").read_text(encoding="utf-8")
        self.assertIn("UE 仍挂", card)
        self.assertIn("python3 -m steel_tide m1-pass", card)
        self.assertIn("python3 -m steel_tide m1-pass", handoff)
        self.assertIn("schedule_bridge_connect(BRIDGE_AT_S)", source)
        self.assertNotIn("_begin_bridge_warning", source)
        self.assertNotIn("_strip_offsets", source)
        for needle in (
            "wrong_faction",
            "out_of_range",
            "holding_core",
            "left_terminal",
            "CoreReturnedToCenter",
            "kind=points",
            "pass_range_m",
            "points_to_win",
            "docs/evidence/nr-m1-pass/server.log",
        ):
            self.assertIn(needle, card)
        project = json.loads((ROOT / "NeonRift.uproject").read_text(encoding="utf-8"))
        self.assertEqual(project["EngineAssociation"], "5.4")
        self.assertFalse(list((ROOT / "Content").rglob("*.umap")))
        self.assertFalse(list(ROOT.rglob("*.uasset")))


if __name__ == "__main__":
    unittest.main()
