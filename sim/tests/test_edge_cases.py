import unittest

from steel_tide.config import load_config
from steel_tide.match import SERVER_CLIENT, SteelTideMatch


def _pair(role_a: str = "assault", role_b: str = "recon") -> SteelTideMatch:
    match = SteelTideMatch(load_config())
    match.add_combatant("a1", "client-a", "humanoid_robot", "human", face_variant="plate-7")
    match.add_combatant("b1", "client-b", "humanoid_robot", "human", face_variant="plate-7")
    match.choose_faction("a1", "A")
    match.choose_faction("b1", "B")
    match.choose_role("a1", role_a)
    match.choose_role("b1", role_b)
    match.start()
    return match


class DoubleSubmitInterruptTests(unittest.TestCase):
    def test_two_hits_interrupt_the_channel_once(self):
        match = _pair()
        match.combatants["a1"].protection_until_ms = 0
        match.place_for_test("a1", "center")
        match.enqueue("client-a", "pick_core", 0.5, combatant_id="a1")
        match.advance_to(0.5)
        match.place_for_test("a1", "terminal_b")
        match.enqueue("client-a", "begin_score", 1.0, combatant_id="a1")
        match.enqueue(SERVER_CLIENT, "hit", 1.5, target_id="a1", down=True)
        match.enqueue(SERVER_CLIENT, "hit", 1.5, target_id="a1", down=True)
        match.advance_to(8)
        self.assertEqual(len(match.named("ScoreChannelInterrupted")), 1)
        self.assertEqual(len(match.named("ActorDowned")), 1)
        self.assertFalse(match.named("PointScored"))
        self.assertEqual(match.holder_errors(), [])

    def test_same_frame_score_submit_and_hit_never_opens_a_channel(self):
        match = _pair()
        match.combatants["a1"].protection_until_ms = 0
        match.place_for_test("a1", "center")
        match.enqueue("client-a", "pick_core", 0.5, combatant_id="a1")
        match.advance_to(0.5)
        match.place_for_test("a1", "terminal_b")
        match.enqueue("client-a", "begin_score", 1.0, combatant_id="a1")
        match.enqueue(SERVER_CLIENT, "hit", 1.0, target_id="a1", down=True)
        match.advance_to(6)
        self.assertFalse(match.named("ScoreChannelStarted"))
        self.assertFalse(match.named("PointScored"))
        self.assertEqual(match.named("ScoreChannelRejected")[-1].payload["reason"], "not_holder")
        self.assertEqual(match.core.status, "ground")


class HumanoidLockTests(unittest.TestCase):
    def test_humanoid_can_switch_before_start_and_not_after(self):
        match = SteelTideMatch(load_config())
        match.add_combatant("a1", "client-a", "humanoid_robot", "human", face_variant="plate-7")
        match.add_combatant("b1", "client-b", "human", "human", face_variant="other")
        match.choose_faction("a1", "A")
        match.choose_faction("a1", "B")
        match.choose_faction("b1", "A")
        match.choose_role("a1", "assault")
        match.choose_role("b1", "recon")
        self.assertEqual(match.combatants["a1"].faction, "B")
        match.start()
        self.assertEqual(match.named("FactionsLocked")[0].payload["assignments"]["a1"], "B")
        match.choose_faction("a1", "A")
        match.advance_to(30)
        match.choose_faction("a1", "A")
        match.choose_role("a1", "recon")
        self.assertEqual(match.combatants["a1"].faction, "B")
        self.assertEqual(match.combatants["a1"].role, "assault")
        self.assertGreaterEqual(len(match.named("FactionRejected")), 2)
        self.assertEqual(match.named("RoleRejected")[-1].payload["reason"], "locked")
        match.enqueue("client-a", "use_ability", 31, combatant_id="a1", ability="mark", target_id="b1")
        match.advance_to(31)
        self.assertEqual(match.named("AbilityRejected")[-1].payload["reason"], "wrong_role")


class BridgeWarningTimelineTests(unittest.TestCase):
    def _open(self) -> SteelTideMatch:
        match = _pair()
        return match

    def test_warning_is_exactly_four_seconds_before_connect(self):
        match = self._open()
        match.schedule_bridge_connect(10)
        match.advance_to_ms(5999)
        self.assertEqual(match.bridge_state, "disconnected")
        self.assertFalse(match.named("BridgeWarningStarted"))
        match.advance_to(6)
        warning = match.named("BridgeWarningStarted")
        self.assertEqual(len(warning), 1)
        self.assertEqual(warning[0].t_ms, 6000)
        self.assertEqual(warning[0].payload["lead_ms"], 4000)
        self.assertTrue(warning[0].payload["readable_without_reflection"])
        self.assertIn("span_light_strip", warning[0].payload["cues"])
        self.assertIn("alarm", warning[0].payload["cues"])
        self.assertEqual(match.bridge_state, "warning")
        match.advance_to_ms(9999)
        self.assertFalse(match.named("BridgeStateChanged"))
        match.advance_to(10)
        self.assertEqual(match.named("BridgeStateChanged")[0].payload["state"], "connected")
        self.assertEqual(match.named("BridgeStateChanged")[0].t_ms, 10000)
        match.advance_to(20)
        self.assertEqual(len(match.named("BridgeWarningStarted")), 1)
        self.assertEqual(len([e for e in match.named("BridgeStateChanged") if e.payload["state"] == "connected"]), 1)

    def test_reschedule_replaces_the_warning_instead_of_stacking(self):
        match = self._open()
        match.schedule_bridge_connect(10)
        match.schedule_bridge_connect(14)
        match.advance_to(6)
        self.assertFalse(match.named("BridgeWarningStarted"))
        match.advance_to(10)
        self.assertEqual(match.bridge_state, "warning")
        self.assertFalse(match.named("BridgeStateChanged"))
        match.advance_to(14)
        self.assertEqual(match.bridge_state, "connected")
        self.assertEqual(len(match.named("BridgeWarningStarted")), 1)
        self.assertEqual(match.named("BridgeWarningStarted")[0].t_ms, 10000)


class RoleCooldownTests(unittest.TestCase):
    def test_role_ids_are_the_three_greybox_jobs(self):
        config = load_config()
        self.assertEqual(
            {role: spec["label_zh"] for role, spec in config.role_abilities.items()},
            {"assault": "突进", "support": "支援", "recon": "侦察"},
        )
        self.assertEqual(set(config.role_abilities), set(config.roles))

    def test_dash_cooldown_and_bridge_block(self):
        match = _pair("assault", "assault")
        for combatant in match.combatants.values():
            combatant.preferred_route = "elevated"
        match.place_for_test("a1", "terminal_a")
        match.place_for_test("b1", "terminal_b")
        match.enqueue("client-a", "use_ability", 1, combatant_id="a1", ability="dash", dest="bridgehead_a")
        match.enqueue("client-b", "use_ability", 1, combatant_id="b1", ability="dash", dest="bridgehead_b")
        match.enqueue("client-a", "use_ability", 1, combatant_id="a1", ability="dash", dest="center")
        match.advance_to(1)
        self.assertEqual(match.combatants["a1"].anchor, "bridgehead_a")
        self.assertEqual(match.combatants["b1"].anchor, "bridgehead_b")
        self.assertEqual(len(match.named("AbilityUsed")), 2)
        self.assertEqual(match.named("AbilityRejected")[-1].payload["reason"], "cooldown")
        match.enqueue("client-a", "use_ability", 9, combatant_id="a1", ability="dash", dest="center")
        match.advance_to(9)
        self.assertEqual(match.named("AbilityRejected")[-1].payload["reason"], "bridge_blocked")
        self.assertEqual(match.combatants["a1"].anchor, "bridgehead_a")
        self.assertEqual(match.combatants["a1"].ability_ready_ms, 9000)
        match.schedule_bridge_connect(14)
        match.advance_to(14)
        match.enqueue("client-a", "use_ability", 14, combatant_id="a1", ability="dash", dest="center")
        match.advance_to(14)
        self.assertEqual(match.named("AbilityRejected")[-1].payload["reason"], "out_of_range")

    def test_shield_swallows_one_hit_and_then_cools_down(self):
        match = _pair("support", "assault")
        match.combatants["a1"].protection_until_ms = 0
        match.place_for_test("a1", "center")
        match.enqueue("client-a", "pick_core", 0.4, combatant_id="a1")
        match.advance_to(0.4)
        match.place_for_test("a1", "terminal_b")
        match.enqueue("client-a", "begin_score", 1, combatant_id="a1")
        match.enqueue("client-a", "use_ability", 1.2, combatant_id="a1", ability="shield")
        match.enqueue(SERVER_CLIENT, "hit", 1.2, target_id="a1", down=True)
        match.advance_to(1.2)
        self.assertEqual(match.named("HitIgnored")[-1].payload["reason"], "shield")
        self.assertTrue(match.channel is not None)
        match.enqueue(SERVER_CLIENT, "hit", 1.4, target_id="a1", down=True)
        match.advance_to(8)
        self.assertTrue(match.named("ScoreChannelInterrupted"))
        self.assertFalse(match.named("PointScored"))
        match.enqueue("client-a", "use_ability", 8, combatant_id="a1", ability="shield")
        match.advance_to(8)
        self.assertEqual(match.named("AbilityRejected")[-1].payload["reason"], "cooldown")

    def test_recon_mark_does_not_reveal_a_covered_target(self):
        match = _pair("recon", "assault")
        match.place_for_test("a1", "center")
        match.place_for_test("b1", "alley_mid")
        match.enqueue("client-a", "use_ability", 1, combatant_id="a1", ability="mark", target_id="b1")
        match.advance_to(1)
        rejected = match.named("AbilityRejected")[-1].payload
        self.assertEqual(rejected["reason"], "not_visible")
        self.assertNotIn("pos", rejected)
        self.assertNotIn("x_m", rejected)
        match.place_for_test("b1", "center")
        match.enqueue("client-a", "use_ability", 1, combatant_id="a1", ability="mark", target_id="b1")
        match.advance_to(1)
        used = match.named("AbilityUsed")[-1]
        self.assertEqual(used.payload["target_id"], "b1")
        self.assertNotIn("pos", used.payload)
        self.assertEqual(used.payload["faction"], "A")
        match.enqueue("client-b", "use_ability", 2, combatant_id="b1", ability="mark", target_id="a1")
        match.advance_to(2)
        self.assertEqual(match.named("AbilityRejected")[-1].payload["reason"], "wrong_role")


if __name__ == "__main__":
    unittest.main()
