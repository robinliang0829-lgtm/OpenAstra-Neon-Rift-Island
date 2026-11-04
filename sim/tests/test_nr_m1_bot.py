import json
import unittest

from steel_tide.bots import run_bot_slice
from steel_tide.config import CONFIG_PATH, load_config
from steel_tide.dual_log import diff_against_evidence
from steel_tide.match import SteelTideMatch
from steel_tide.nr_m1_bot import EVIDENCE_DIR, acceptance_errors, evaluate_slice, run_m1_bot_match
from steel_tide.repro import scenario_no_double_hold

ROOT = CONFIG_PATH.parents[1]
FRAMEWORK = (
    ROOT / "Source" / "NeonRift" / "Private" / "NeonRiftGameMode.cpp",
    ROOT / "Source" / "NeonRift" / "Private" / "NeonRiftGameState.cpp",
    ROOT / "Source" / "NeonRift" / "Private" / "NeonRiftPlayerState.cpp",
)


class SliceTests(unittest.TestCase):
    def test_bot_slice_matches_the_sample_logs(self):
        match = run_m1_bot_match()
        self.assertEqual(acceptance_errors(match), [])
        logs, errors = evaluate_slice(match)
        self.assertEqual(errors, [])
        self.assertEqual(diff_against_evidence(logs, EVIDENCE_DIR), [])
        bodies = []
        for end in ("server", "client-a", "client-b"):
            text = logs[end]
            self.assertIn("# schema nr-m1-bot-dual-end-v1\n", text)
            self.assertIn("# identities ", text)
            self.assertIn("# local_bots a2,a3,b2,b3\n", text)
            body = text.split("# comparable event_body_identical\n", 1)[1]
            bodies.append(body)
            self.assertIn("contest_core", body)
            self.assertIn("close_range_pass", body)
            self.assertIn("contest_channel", body)
            self.assertIn("score_path", body)
            self.assertIn('"kind": "points"', body)
            self.assertNotIn("digital_resident", body)
        self.assertEqual(bodies[0], bodies[1])
        self.assertEqual(bodies[1], bodies[2])
        self.assertNotIn("OvertimeStarted", bodies[0])
        self.assertNotIn("place_for_test", bodies[0])

    def test_policy_is_repeatable(self):
        first = [event.format() for event in run_m1_bot_match().events]
        second = [event.format() for event in run_m1_bot_match().events]
        self.assertEqual(first, second)

    def test_older_slices_do_not_emit_bot_decisions(self):
        bots = run_bot_slice()
        self.assertEqual(bots.named("BotDecision"), [])
        self.assertEqual(bots.named("PointScored")[0].t_ms, 29500)
        self.assertEqual(scenario_no_double_hold().named("BotDecision"), [])


class PortTests(unittest.TestCase):
    def test_m1_runner_does_not_call_the_resident_port(self):
        policy = (ROOT / "sim" / "steel_tide" / "bot_policy.py").read_text(encoding="utf-8")
        runner = (ROOT / "sim" / "steel_tide" / "nr_m1_bot.py").read_text(encoding="utf-8")
        self.assertNotIn("DigitalResidentPort(", policy)
        self.assertNotIn("DigitalResidentPort(", runner)
        self.assertNotIn("select_match(", runner)
        self.assertNotIn("place_for_test", policy)
        self.assertNotIn("place_for_test", runner)
        for path in FRAMEWORK:
            self.assertNotIn("UNeonRiftResidentPort", path.read_text(encoding="utf-8"))
        port_cpp = (ROOT / "Source" / "NeonRift" / "Private" / "NeonRiftResidentPort.cpp").read_text(encoding="utf-8")
        self.assertNotIn("PointScored", port_cpp)

    def test_decision_log_refuses_a_resident_controller(self):
        match = SteelTideMatch(load_config())
        match.add_combatant("r1", "resident-1", "humanoid_robot", "digital_resident")
        with self.assertRaises(RuntimeError):
            match.note_bot_decision("r1", "pick_core", "contest_core", "core")
        self.assertEqual(match.named("BotDecision"), [])
        self.assertEqual(match.combatants["r1"].controller, "digital_resident")


class ContractTests(unittest.TestCase):
    def test_card_leaves_ue_hanging_and_names_the_command(self):
        card = (ROOT / "docs" / "NR-M1-bot.md").read_text(encoding="utf-8")
        handoff = (ROOT / "docs" / "HANDOFF.md").read_text(encoding="utf-8")
        source = (ROOT / "sim" / "steel_tide" / "nr_m1_bot.py").read_text(encoding="utf-8")
        self.assertIn("UE 仍挂", card)
        self.assertIn("python3 -m steel_tide m1-bot", card)
        self.assertIn("python3 -m steel_tide m1-bot", handoff)
        self.assertIn("schedule_bridge_connect(BRIDGE_AT_S)", source)
        self.assertNotIn("_begin_bridge_warning", source)
        self.assertNotIn("_strip_offsets", source)
        for needle in (
            "contest_core",
            "close_range_pass",
            "contest_channel",
            "score_path",
            "pass_range_m",
            "kind=points",
            "BotDecision",
            "target_id",
            "local_bot",
            "digital_resident",
            "docs/evidence/nr-m1-bot/server.log",
        ):
            self.assertIn(needle, card)
        project = json.loads((ROOT / "NeonRift.uproject").read_text(encoding="utf-8"))
        self.assertEqual(project["EngineAssociation"], "5.4")
        self.assertFalse(list((ROOT / "Content").rglob("*.umap")))
        self.assertFalse(list(ROOT.rglob("*.uasset")))


if __name__ == "__main__":
    unittest.main()
