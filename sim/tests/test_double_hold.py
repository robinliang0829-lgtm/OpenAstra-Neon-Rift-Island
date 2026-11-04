import unittest

from steel_tide.config import load_config
from steel_tide.match import SteelTideMatch
from steel_tide.repro import check_no_double_hold, scenario_no_double_hold


class DoubleHoldTests(unittest.TestCase):
    def test_same_frame_pick_grants_one_holder(self):
        match = scenario_no_double_hold()
        self.assertEqual(check_no_double_hold(match), [])
        self.assertEqual(match.core.holder_id, "a1")
        self.assertEqual(match.named("CorePickRejected")[0].payload["combatant_id"], "b1")

    def test_later_pick_while_held_is_rejected(self):
        match = scenario_no_double_hold()
        match.enqueue("client-b", "pick_core", 2.0, combatant_id="b1")
        match.advance_to(2.0)
        self.assertEqual(match.core.holder_id, "a1")
        self.assertEqual(match.holder_errors(), [])
        reasons = [event.payload["reason"] for event in match.named("CorePickRejected")]
        self.assertEqual(reasons, ["already_held", "already_held"])

    def test_ineligible_client_does_not_block_the_one_on_the_core(self):
        match = SteelTideMatch(load_config())
        match.add_combatant("a1", "client-z", "human", "human")
        match.add_combatant("b1", "client-a", "robot", "local_bot")
        match.choose_faction("a1", "A")
        match.choose_faction("b1", "B")
        match.choose_role("a1", "recon")
        match.choose_role("b1", "assault")
        match.start()
        match.place_for_test("a1", "center")
        match.place_for_test("b1", "spawn_b")
        match.enqueue("client-a", "pick_core", 1.0, combatant_id="b1")
        match.enqueue("client-z", "pick_core", 1.0, combatant_id="a1")
        match.advance_to(1.0)
        self.assertEqual(match.core.holder_id, "a1")
        rejected = match.named("CorePickRejected")
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0].payload["reason"], "not_at_core")
        self.assertEqual(match.holder_errors(), [])

    def test_pass_and_drop_keep_a_single_holder(self):
        match = SteelTideMatch(load_config())
        match.add_combatant("a1", "client-a", "humanoid_robot", "human", face_variant="same-face")
        match.add_combatant("a2", "client-a2", "humanoid_robot", "digital_resident", face_variant="same-face")
        match.add_combatant("b1", "client-b", "beast", "local_bot")
        match.choose_faction("a1", "A")
        match.choose_faction("a2", "A")
        match.choose_faction("b1", "B")
        match.choose_role("a1", "assault")
        match.choose_role("a2", "support")
        match.choose_role("b1", "recon")
        match.start()
        match.place_for_test("a1", "center")
        match.enqueue("client-a", "pick_core", 1.0, combatant_id="a1")
        match.advance_to(1.0)
        match.place_for_test("b1", "center", pos=(50.0, 0.0))
        match.enqueue("client-a", "pass_core", 1.5, from_id="a1", to_id="b1")
        match.advance_to(1.5)
        self.assertEqual(match.named("CorePassRejected")[0].payload["reason"], "wrong_faction")
        self.assertEqual(match.core.holder_id, "a1")

        match.place_for_test("a2", "center", pos=(48.0, 10.0))
        match.enqueue("client-a", "pass_core", 2.0, from_id="a1", to_id="a2")
        match.advance_to(2.0)
        self.assertEqual(match.named("CorePassRejected")[-1].payload["reason"], "out_of_range")

        match.place_for_test("a2", "center")
        match.enqueue("client-a", "pass_core", 2.5, from_id="a1", to_id="a2")
        match.advance_to(2.5)
        self.assertEqual(match.core.holder_id, "a2")
        self.assertEqual(match.named("CorePassed")[-1].payload["to_id"], "a2")

        match.enqueue("client-a2", "drop_core", 3.0, combatant_id="a2")
        match.advance_to(3.0)
        self.assertIsNone(match.core.holder_id)
        self.assertEqual(match.core.status, "ground")
        match.place_for_test("b1", "center")
        match.place_for_test("a1", "center")
        match.enqueue("client-a", "pick_core", 3.5, combatant_id="a1")
        match.enqueue("client-b", "pick_core", 3.5, combatant_id="b1")
        match.advance_to(3.5)
        self.assertEqual(match.core.holder_id, "a1")
        self.assertEqual(match.holder_errors(), [])


if __name__ == "__main__":
    unittest.main()
