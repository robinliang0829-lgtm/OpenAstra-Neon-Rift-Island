import json
import unittest

from steel_tide.config import CONFIG_PATH, load_config
from steel_tide.dual_log import diff_against_evidence
from steel_tide.match import SteelTideMatch
from steel_tide.nr_m1_bot import run_m1_bot_match
from steel_tide.nr_m2_resident import EVIDENCE_DIR, acceptance_errors, evaluate_slice, run_m2_resident_match
from steel_tide.resident_port import (
    PRODUCTION_RESIDENT,
    DigitalResidentPort,
    lobby_view,
    perceive,
)

ROOT = CONFIG_PATH.parents[1]
FRAMEWORK = (
    ROOT / "Source" / "NeonRift" / "Private" / "NeonRiftGameMode.cpp",
    ROOT / "Source" / "NeonRift" / "Private" / "NeonRiftGameState.cpp",
    ROOT / "Source" / "NeonRift" / "Private" / "NeonRiftPlayerState.cpp",
)


class SliceTests(unittest.TestCase):
    def test_resident_slice_matches_the_sample_logs(self):
        match = run_m2_resident_match()
        self.assertEqual(acceptance_errors(match), [])
        logs, errors = evaluate_slice(match)
        self.assertEqual(errors, [])
        self.assertEqual(diff_against_evidence(logs, EVIDENCE_DIR), [])
        bodies = []
        for end in ("server", "client-a", "client-b"):
            text = logs[end]
            self.assertIn("# schema nr-m2-resident-dual-end-v1\n", text)
            self.assertIn("# identities ", text)
            self.assertIn("# digital_residents a2\n", text)
            self.assertIn("# local_bots a3,b2,b3\n", text)
            body = text.split("# comparable event_body_identical\n", 1)[1]
            bodies.append(body)
            self.assertIn("select_match", body)
            self.assertIn("contest_core", body)
            self.assertIn("close_range_pass", body)
            self.assertIn("contest_channel", body)
            self.assertIn("score_path", body)
            self.assertIn('"controller": "digital_resident"', body)
            self.assertIn('"controller": "local_bot"', body)
            self.assertIn('"kind": "points"', body)
            self.assertNotIn('"x_m"', body)
            self.assertNotIn('"y_m"', body)
            self.assertNotIn('"pos"', body)
        self.assertEqual(bodies[0], bodies[1])
        self.assertEqual(bodies[1], bodies[2])
        self.assertNotIn("OvertimeStarted", bodies[0])
        self.assertNotIn("place_for_test", bodies[0])

    def test_policy_is_repeatable_and_leaves_m1_alone(self):
        first = [event.format() for event in run_m2_resident_match().events]
        second = [event.format() for event in run_m2_resident_match().events]
        self.assertEqual(first, second)
        older = run_m1_bot_match()
        self.assertEqual(older.named("ResidentDecision"), [])
        self.assertFalse(any(combatant.controller == "digital_resident" for combatant in older.combatants.values()))


class PerceptionTests(unittest.TestCase):
    def test_select_match_accepts_a_legal_seat_and_refuses_an_illegal_one(self):
        self.assertIs(PRODUCTION_RESIDENT, False)
        port = DigitalResidentPort()
        chosen = port.select_match(
            {
                "legal_factions": ["A", "B"],
                "offered_faction": "A",
                "offered_role": "support",
                "roles": ["assault", "support", "recon"],
            }
        )
        self.assertEqual(chosen, {"faction": "A", "join": True, "role": "support"})
        self.assertEqual(port.select_calls, 1)
        fallback = DigitalResidentPort().select_match(
            {"legal_factions": ["A", "B"], "roles": ["assault", "support", "recon"]}
        )
        self.assertEqual(fallback, {"faction": "A", "join": True, "role": "assault"})
        refused = DigitalResidentPort().select_match(
            {
                "legal_factions": ["B"],
                "offered_faction": "A",
                "offered_role": "support",
                "roles": ["assault", "support", "recon"],
            }
        )
        self.assertEqual(refused, {"faction": None, "join": False, "role": None})

    def test_covered_enemy_is_an_id_and_poisoned_views_are_refused(self):
        match = SteelTideMatch(load_config())
        match.add_combatant("a2", "bot-a2", "humanoid_robot", "digital_resident")
        match.add_combatant("a3", "bot-a3", "human", "local_bot")
        match.add_combatant("b2", "bot-b2", "humanoid_robot", "local_bot")
        match.choose_faction("a2", "A")
        match.choose_role("a2", "support")
        match.choose_faction("a3", "A")
        match.choose_role("a3", "recon")
        match.choose_faction("b2", "B")
        match.choose_role("b2", "assault")
        match.start()
        match.place_for_test("a2", "alley_a")
        match.place_for_test("a3", "alley_a")
        match.place_for_test("b2", "alley_mid")
        view = perceive(match, match.combatants["a2"])
        self.assertEqual(view["hidden_targets"], [{"id": "b2"}])
        self.assertNotIn("holder_anchor", view)
        self.assertNotIn("core_anchor", view)
        self.assertEqual(view["core_home"], "center")
        self.assertNotIn("pos", json.dumps(view))
        self.assertNotIn("x_m", json.dumps(view))
        mate = next(item for item in view["teammates"] if item["id"] == "a3")
        self.assertEqual(mate["distance_m"], 0.0)
        self.assertNotIn("pos", mate)
        port = DigitalResidentPort()
        seat = lobby_view(match, match.combatants["a2"], "A", "support")
        self.assertNotIn("self_anchor", seat)
        self.assertEqual(port.select_match(seat)["join"], True)
        decision = port.decide(view)
        self.assertEqual(decision.action, "request_move")
        self.assertEqual(decision.reason, "contest_core")
        self.assertEqual(decision.goal, "center")
        poisoned = {"hidden_targets": [{"id": "b2", "x_m": 48, "y_m": 18}]}
        with self.assertRaises(ValueError) as raised:
            port.decide(poisoned)
        self.assertIn("post-wall", str(raised.exception))
        with self.assertRaises(ValueError):
            port.select_match({"hidden_targets": [{"id": "b2", "anchor": "alley_mid"}], "legal_factions": ["A"]})

    def test_decision_log_keeps_the_controllers_apart(self):
        match = SteelTideMatch(load_config())
        match.add_combatant("r1", "resident-1", "humanoid_robot", "digital_resident")
        match.add_combatant("b1", "bot-1", "humanoid_robot", "local_bot")
        with self.assertRaises(RuntimeError):
            match.note_bot_decision("r1", "pick_core", "contest_core", "core")
        with self.assertRaises(RuntimeError):
            match.note_resident_decision("b1", "pick_core", "contest_core", "core")
        match.note_resident_decision("r1", "pick_core", "contest_core", "core")
        payload = match.named("ResidentDecision")[0].payload
        self.assertEqual(payload["controller"], "digital_resident")
        self.assertEqual(match.named("BotDecision"), [])


class ContractTests(unittest.TestCase):
    def test_card_leaves_ue_hanging_and_names_the_command(self):
        card = (ROOT / "docs" / "NR-M2-resident.md").read_text(encoding="utf-8")
        handoff = (ROOT / "docs" / "HANDOFF.md").read_text(encoding="utf-8")
        source = (ROOT / "sim" / "steel_tide" / "nr_m2_resident.py").read_text(encoding="utf-8")
        port = (ROOT / "sim" / "steel_tide" / "resident_port.py").read_text(encoding="utf-8")
        header = (ROOT / "Source" / "NeonRift" / "Public" / "NeonRiftResidentPort.h").read_text(encoding="utf-8")
        cpp = (ROOT / "Source" / "NeonRift" / "Private" / "NeonRiftResidentPort.cpp").read_text(encoding="utf-8")
        self.assertIn("UE 仍挂", card)
        self.assertIn("不是生产数字居民", card)
        self.assertIn("不喂墙后坐标", card)
        self.assertIn("python3 -m steel_tide m2-resident", card)
        self.assertIn("python3 -m steel_tide m2-resident", handoff)
        self.assertIn("port.select_match(", source)
        self.assertIn("port.decide(", source)
        self.assertIn("schedule_bridge_connect(BRIDGE_AT_S)", source)
        self.assertNotIn("place_for_test", source)
        self.assertNotIn("_begin_bridge_warning", source)
        self.assertIn("PRODUCTION_RESIDENT = False", port)
        self.assertIn("not a production resident", header.lower())
        self.assertNotIn("FVector", header)
        self.assertNotIn("x_m", header)
        for needle in ("contest_core", "close_range_pass", "contest_channel", "score_path", "select_match", "legal_faction"):
            self.assertIn(needle, cpp)
        self.assertIn("NeonRiftEvents::ResidentDecision", cpp)
        self.assertIn("humanoid_robot", cpp)
        self.assertNotIn("PointScored", cpp)
        self.assertNotIn("FVector", cpp)
        self.assertNotIn("x_m", cpp)
        for path in FRAMEWORK:
            self.assertNotIn("UNeonRiftResidentPort", path.read_text(encoding="utf-8"))
        for needle in (
            "contest_core",
            "close_range_pass",
            "contest_channel",
            "score_path",
            "pass_range_m",
            "kind=points",
            "ResidentDecision",
            "BotDecision",
            "select_match",
            "digital_resident",
            "local_bot",
            "docs/evidence/nr-m2-resident/server.log",
        ):
            self.assertIn(needle, card)
        project = json.loads((ROOT / "NeonRift.uproject").read_text(encoding="utf-8"))
        self.assertEqual(project["EngineAssociation"], "5.4")
        self.assertFalse(list((ROOT / "Content").rglob("*.umap")))
        self.assertFalse(list(ROOT.rglob("*.uasset")))


if __name__ == "__main__":
    unittest.main()
