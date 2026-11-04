import json
import unittest

from steel_tide.bot_policy import decide
from steel_tide.config import CONFIG_PATH, load_config
from steel_tide.dual_log import diff_against_evidence
from steel_tide.match import SteelTideMatch
from steel_tide.nr_m1_bot import run_m1_bot_match
from steel_tide.nr_m2_resident import run_m2_resident_match
from steel_tide.nr_m2_roles import EVIDENCE_DIR, acceptance_errors, evaluate_slice, run_m2_roles_match
from steel_tide.resident_port import DigitalResidentPort

ROOT = CONFIG_PATH.parents[1]
ROLES = ["assault", "support", "recon"]


def _join(role: str) -> DigitalResidentPort:
    port = DigitalResidentPort()
    port.select_match(
        {
            "legal_factions": ["A", "B"],
            "offered_faction": "A",
            "offered_role": role,
            "roles": ROLES,
        }
    )
    return port


class SliceTests(unittest.TestCase):
    def test_roles_slice_matches_the_sample_logs(self):
        match = run_m2_roles_match()
        self.assertEqual(acceptance_errors(match), [])
        logs, errors = evaluate_slice(match)
        self.assertEqual(errors, [])
        self.assertEqual(diff_against_evidence(logs, EVIDENCE_DIR), [])
        bodies = []
        for end in ("server", "client-a", "client-b"):
            text = logs[end]
            self.assertIn("# schema nr-m2-roles-dual-end-v1\n", text)
            self.assertIn("# digital_residents a2\n", text)
            self.assertIn("# local_bots a3,b2,b3\n", text)
            body = text.split("# comparable event_body_identical\n", 1)[1]
            bodies.append(body)
            for ability in ("dash", "shield", "mark"):
                self.assertIn(f'"ability": "{ability}"', body)
            for reason in ROLES:
                self.assertIn(f'"reason": "{reason}"', body)
            self.assertIn('"directed_by": "a2"', body)
            self.assertIn('"reason": "out_of_range"', body)
            self.assertIn('"reason": "cooldown"', body)
            self.assertIn('"reason": "not_visible"', body)
            self.assertIn('"kind": "points"', body)
            self.assertNotIn('"x_m"', body)
            self.assertNotIn('"y_m"', body)
            self.assertNotIn('"pos"', body)
        self.assertEqual(bodies[0], bodies[1])
        self.assertEqual(bodies[1], bodies[2])
        self.assertNotIn("OvertimeStarted", bodies[0])
        self.assertNotIn("place_for_test", bodies[0])

    def test_earlier_cards_do_not_grow_ability_lines(self):
        self.assertEqual(run_m1_bot_match().named("AbilityUsed"), [])
        self.assertEqual(run_m2_resident_match().named("AbilityUsed"), [])
        first = [event.format() for event in run_m2_roles_match().events]
        second = [event.format() for event in run_m2_roles_match().events]
        self.assertEqual(first, second)


class DecisionTests(unittest.TestCase):
    def _pair(self) -> SteelTideMatch:
        match = SteelTideMatch(load_config())
        match.add_combatant("a2", "bot-a2", "humanoid_robot", "local_bot", preferred_route="repair_alley")
        match.add_combatant("a3", "bot-a3", "human", "local_bot", preferred_route="repair_alley")
        match.add_combatant("b2", "bot-b2", "humanoid_robot", "local_bot", preferred_route="repair_alley")
        match.choose_faction("a2", "A")
        match.choose_role("a2", "support")
        match.choose_faction("a3", "A")
        match.choose_role("a3", "recon")
        match.choose_faction("b2", "B")
        match.choose_role("b2", "assault")
        match.start()
        match.role_abilities_enabled = True
        match.ability_progress = {}
        return match

    def test_local_bot_reasons_match_each_role(self):
        match = self._pair()
        # The flag is what turns the rush on. Without it the assault still walks.
        match.role_abilities_enabled = False
        walked = decide(match, match.combatants["b2"])
        self.assertEqual(walked.action, "request_move")
        self.assertEqual(walked.reason, "contest_core")
        match.role_abilities_enabled = True
        rushed = decide(match, match.combatants["b2"])
        self.assertEqual(rushed.action, "use_ability")
        self.assertEqual(rushed.reason, "assault")
        self.assertEqual(rushed.ability, "dash")
        self.assertEqual(rushed.target_id, "alley_b")
        self.assertGreater(rushed.distance_m, 12)

        match.place_for_test("a2", "center")
        match.place_for_test("a3", "center")
        match.core.holder_id = "a3"
        match.core.status = "held"
        shield = decide(match, match.combatants["a2"])
        self.assertEqual(shield.reason, "support")
        self.assertEqual(shield.ability, "shield")
        self.assertEqual(shield.target_id, "a3")
        self.assertEqual(shield.distance_m, 0.0)

        match.core.holder_id = None
        match.core.status = "spawn"
        match.place_for_test("a3", "alley_a")
        match.place_for_test("b2", "alley_mid")
        marked = decide(match, match.combatants["a3"])
        self.assertEqual(marked.reason, "recon")
        self.assertEqual(marked.ability, "mark")
        self.assertEqual(marked.target_id, "b2")
        self.assertIsNone(marked.distance_m)

    def test_resident_reasons_match_each_role_without_coordinates(self):
        assault = _join("assault")
        over = assault.decide(
            {
                "ability_id": "dash",
                "ability_progress": "",
                "ability_range_m": 12,
                "ability_ready": True,
                "core_anchor": "center",
                "core_home": "center",
                "core_pickable": True,
                "downed": False,
                "faction": "A",
                "hidden_targets": [],
                "holding_core": False,
                "hops": {"center": {"dest": "alley_b", "distance_m": 18.0}},
                "in_alley": False,
                "interrupt_open": True,
                "pass_open": True,
                "pass_range_m": 4,
                "phase": "live",
                "role": "assault",
                "role_abilities": True,
                "roles": ROLES,
                "self_anchor": "spawn_b",
                "teammates": [],
                "visible_targets": [],
            }
        )
        self.assertEqual(over.reason, "assault")
        self.assertEqual(over.ability, "dash")
        self.assertEqual(over.distance_m, 18.0)
        short = assault.decide(
            {
                "ability_id": "dash",
                "ability_progress": "ranged",
                "ability_range_m": 12,
                "ability_ready": True,
                "core_pickable": False,
                "downed": False,
                "faction": "A",
                "hidden_targets": [{"id": "b2"}],
                "holder_faction": "B",
                "holder_id": "b2",
                "holder_score_terminal": "terminal_b",
                "holding_core": False,
                "hops": {"terminal_b": {"dest": "terminal_b", "distance_m": 12.0}},
                "in_alley": False,
                "interrupt_open": True,
                "pass_open": False,
                "pass_range_m": 4,
                "phase": "live",
                "role": "assault",
                "role_abilities": True,
                "roles": ROLES,
                "self_anchor": "spawn_b",
                "teammates": [],
                "visible_targets": [],
            }
        )
        self.assertEqual(short.reason, "assault")
        self.assertEqual(short.target_id, "terminal_b")
        self.assertLessEqual(short.distance_m, 12)
        cooled = assault.decide(
            {
                "ability_id": "dash",
                "ability_progress": "dashed",
                "ability_range_m": 12,
                "ability_ready": False,
                "core_pickable": False,
                "downed": False,
                "faction": "A",
                "hidden_targets": [],
                "holder_faction": "B",
                "holder_score_terminal": "terminal_b",
                "holding_core": False,
                "in_alley": False,
                "interrupt_open": True,
                "pass_range_m": 4,
                "phase": "live",
                "role": "assault",
                "role_abilities": True,
                "roles": ROLES,
                "self_anchor": "terminal_b",
                "teammates": [],
                "visible_targets": [],
            }
        )
        self.assertEqual(cooled.reason, "assault")
        self.assertEqual(cooled.progress, "cooled")
        self.assertIsNone(cooled.distance_m)

        support = _join("support")
        shield = support.decide(
            {
                "ability_id": "shield",
                "ability_progress": "",
                "ability_range_m": 0,
                "ability_ready": True,
                "core_pickable": False,
                "downed": False,
                "faction": "A",
                "hidden_targets": [{"id": "b2"}],
                "holder_faction": "A",
                "holder_id": "a3",
                "holding_core": False,
                "in_alley": False,
                "interrupt_open": True,
                "pass_range_m": 4,
                "phase": "live",
                "role": "support",
                "role_abilities": True,
                "roles": ROLES,
                "self_anchor": "center",
                "teammates": [
                    {"anchor": "center", "distance_m": 0.0, "downed": False, "id": "a3", "role": "recon"}
                ],
                "visible_targets": [],
            }
        )
        self.assertEqual(shield.reason, "support")
        self.assertEqual(shield.ability, "shield")
        self.assertEqual(shield.target_id, "a3")
        self.assertEqual(shield.distance_m, 0.0)
        self.assertEqual(support.hidden_shapes[-1], frozenset({"id"}))

        recon = _join("recon")
        hidden = recon.decide(
            {
                "ability_id": "mark",
                "ability_progress": "",
                "ability_range_m": 0,
                "ability_ready": True,
                "core_home": "center",
                "core_pickable": True,
                "downed": False,
                "faction": "A",
                "hidden_targets": [{"id": "b1"}],
                "holding_core": False,
                "hops": {"center": {"dest": "alley_mid", "distance_m": 48.0}},
                "in_alley": True,
                "interrupt_open": True,
                "pass_open": True,
                "pass_range_m": 4,
                "phase": "live",
                "role": "recon",
                "role_abilities": True,
                "roles": ROLES,
                "self_anchor": "alley_a",
                "teammates": [],
                "visible_targets": [],
            }
        )
        self.assertEqual(hidden.reason, "recon")
        self.assertEqual(hidden.ability, "mark")
        self.assertEqual(hidden.target_id, "b1")
        self.assertIsNone(hidden.distance_m)
        self.assertNotIn("x_m", json.dumps(hidden.__dict__))
        visible = recon.decide(
            {
                "ability_id": "mark",
                "ability_progress": "hidden",
                "ability_range_m": 0,
                "ability_ready": True,
                "core_pickable": False,
                "downed": False,
                "faction": "A",
                "hidden_targets": [],
                "holder_faction": "A",
                "holder_id": "a2",
                "holding_core": False,
                "in_alley": False,
                "interrupt_open": True,
                "pass_range_m": 4,
                "phase": "live",
                "role": "recon",
                "role_abilities": True,
                "roles": ROLES,
                "self_anchor": "center",
                "teammates": [],
                "visible_targets": [{"anchor": "spawn_b", "faction": "B", "id": "b1"}],
            }
        )
        self.assertEqual(visible.reason, "recon")
        self.assertEqual(visible.target_id, "b1")
        poisoned = {"hops": {"center": {"dest": "alley_b", "x_m": 1}}, "hidden_targets": []}
        with self.assertRaises(ValueError) as raised:
            recon.decide(poisoned)
        self.assertIn("post-wall", str(raised.exception))


class ContractTests(unittest.TestCase):
    def test_card_leaves_ue_hanging_and_names_the_command(self):
        card = (ROOT / "docs" / "NR-M2-roles.md").read_text(encoding="utf-8")
        handoff = (ROOT / "docs" / "HANDOFF.md").read_text(encoding="utf-8")
        source = (ROOT / "sim" / "steel_tide" / "nr_m2_roles.py").read_text(encoding="utf-8")
        resident = (ROOT / "sim" / "steel_tide" / "nr_m2_resident.py").read_text(encoding="utf-8")
        self.assertIn("UE 仍挂", card)
        self.assertIn("python3 -m steel_tide m2-roles", card)
        self.assertIn("python3 -m steel_tide m2-roles", handoff)
        self.assertIn("_issue(match, port)", source)
        self.assertIn("port.decide(", resident)
        self.assertIn("schedule_bridge_connect(BRIDGE_AT_S)", source)
        self.assertNotIn("place_for_test", source)
        self.assertNotIn("_begin_bridge_warning", source)
        for needle in (
            "contest_core",
            "close_range_pass",
            "contest_channel",
            "score_path",
            "dash",
            "shield",
            "mark",
            "assault",
            "support",
            "recon",
            "out_of_range",
            "not_visible",
            "directed_by",
            "kind=points",
            "docs/evidence/nr-m2-roles/server.log",
            "select_match",
            "digital_resident",
            "local_bot",
        ):
            self.assertIn(needle, card)
        project = json.loads((ROOT / "NeonRift.uproject").read_text(encoding="utf-8"))
        self.assertEqual(project["EngineAssociation"], "5.4")
        self.assertFalse(list((ROOT / "Content").rglob("*.umap")))
        self.assertFalse(list(ROOT.rglob("*.uasset")))


if __name__ == "__main__":
    unittest.main()
