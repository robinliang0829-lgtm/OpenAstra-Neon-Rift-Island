import unittest

from steel_tide.bots import run_bot_slice
from steel_tide.config import load_config
from steel_tide.match import SteelTideMatch
from steel_tide.model import badge_for
from steel_tide.routes import path_length_m

ROBIN_FACTION_RULE = {
    "human": ("A",),
    "celestial": ("A",),
    "humanoid_robot": ("A", "B"),
    "robot": ("B",),
    "beast": ("B",),
}


class FactionTests(unittest.TestCase):
    def test_config_matches_robin_faction_law(self):
        config = load_config()
        self.assertEqual(config.faction_rule, ROBIN_FACTION_RULE)
        self.assertEqual(config.score_channel_seconds, 3)
        self.assertEqual(config.terminal_half_extent_m, 2)
        self.assertFalse(config.carrier_can_sprint)
        self.assertEqual(config.badges["A"]["shape"], "open_chevron")
        self.assertEqual(config.badges["B"]["shape"], "closed_ring")

    def test_body_does_not_secretly_assign_a_side(self):
        match = SteelTideMatch(load_config())
        match.add_combatant("humanoid", "client-h", "humanoid_robot", "human", face_variant="plate-7")
        match.add_combatant("person", "client-p", "human", "human")
        match.add_combatant("quad", "client-q", "robot", "local_bot")
        match.add_combatant("beast", "client-b", "beast", "digital_resident")
        match.choose_faction("humanoid", "A")
        match.choose_faction("quad", "A")
        match.choose_faction("beast", "A")
        match.choose_faction("person", "B")
        self.assertIsNone(match.combatants["quad"].faction)
        self.assertIsNone(match.combatants["beast"].faction)
        self.assertIsNone(match.combatants["person"].faction)
        self.assertEqual(match.combatants["humanoid"].faction, "A")
        with self.assertRaises(RuntimeError):
            match.start()

    def test_same_face_humanoids_badge_by_faction_only(self):
        config = load_config()
        match = SteelTideMatch(config)
        match.add_combatant("a1", "client-a", "humanoid_robot", "human", face_variant="plate-7")
        match.add_combatant("b1", "client-b", "humanoid_robot", "digital_resident", face_variant="plate-7")
        match.choose_faction("a1", "A")
        match.choose_faction("b1", "B")
        match.choose_role("a1", "assault")
        match.choose_role("b1", "assault")
        match.start()
        badge_a = badge_for("A", config.badges, "other-face")
        badge_b = badge_for("B", config.badges, "plate-7")
        self.assertNotEqual(badge_a["shape"], badge_b["shape"])
        self.assertEqual(badge_for(match.combatants["a1"].faction, config.badges, "plate-7")["shape"], "open_chevron")
        self.assertEqual(match.combatants["a1"].controller, "human")
        self.assertEqual(match.combatants["b1"].controller, "digital_resident")
        match.choose_faction("a1", "B")
        self.assertEqual(match.named("FactionRejected")[-1].payload["reason"], "locked")
        self.assertEqual(match.combatants["a1"].faction, "A")


class RouteTests(unittest.TestCase):
    def test_alley_is_longer_and_open_while_the_span_is_down(self):
        config = load_config()
        self.assertEqual(path_length_m(config, "spawn_a", "center", "elevated", "connected"), 48)
        self.assertEqual(path_length_m(config, "spawn_b", "center", "elevated", "connected"), 48)
        self.assertEqual(path_length_m(config, "spawn_a", "center", "repair_alley", "disconnected"), 84)
        self.assertEqual(path_length_m(config, "spawn_b", "center", "repair_alley", "disconnected"), 84)
        self.assertIsNone(path_length_m(config, "spawn_a", "center", "elevated", "disconnected"))
        self.assertEqual(path_length_m(config, "center", "terminal_b", "repair_alley", "disconnected"), 96)

    def test_warning_leads_the_span_and_crossing_starts_when_it_connects(self):
        match = SteelTideMatch(load_config())
        match.add_combatant("a1", "client-a", "celestial", "human")
        match.add_combatant("b1", "client-b", "robot", "local_bot")
        match.choose_faction("a1", "A")
        match.choose_faction("b1", "B")
        match.choose_role("a1", "recon")
        match.choose_role("b1", "support")
        match.start()
        match.schedule_bridge_connect(10)
        match.advance_to(6)
        self.assertEqual(match.bridge_state, "warning")
        self.assertTrue(match.named("BridgeWarningStarted")[0].payload["readable_without_reflection"])
        self.assertFalse(match.named("BridgeStateChanged"))
        match.place_for_test("a1", "bridgehead_a")
        match.enqueue(
            "client-a",
            "request_move",
            6,
            combatant_id="a1",
            dest="center",
            route="elevated",
        )
        match.advance_to(6)
        self.assertEqual(match.named("MoveRejected")[-1].payload["reason"], "bridge_blocked")
        match.advance_to(10)
        self.assertEqual(match.bridge_state, "connected")
        match.enqueue(
            "client-a",
            "request_move",
            10,
            combatant_id="a1",
            dest="center",
            route="elevated",
        )
        match.advance_to(10)
        self.assertEqual(match.named("MoveRejected")[-1].payload["reason"], "too_soon")
        self.assertEqual(match.combatants["a1"].anchor, "bridgehead_a")
        match.enqueue(
            "client-a",
            "request_move",
            13,
            combatant_id="a1",
            dest="center",
            route="elevated",
        )
        match.advance_to(13)
        self.assertEqual(match.combatants["a1"].anchor, "center")

    def test_disconnect_nudges_span_occupants_and_leaves_the_alley(self):
        match = SteelTideMatch(load_config())
        match.add_combatant("a1", "client-a", "human", "human")
        match.add_combatant("b1", "client-b", "beast", "human")
        match.choose_faction("a1", "A")
        match.choose_faction("b1", "B")
        match.choose_role("a1", "assault")
        match.choose_role("b1", "assault")
        match.start()
        match.schedule_bridge_connect(1)
        match.advance_to(1)
        match.place_for_test("a1", "center")
        match.place_for_test("b1", "alley_mid")
        match.schedule_bridge_disconnect(3)
        match.advance_to(3)
        self.assertEqual(match.combatants["a1"].anchor, "bridgehead_a")
        self.assertEqual(match.combatants["b1"].anchor, "alley_mid")
        self.assertEqual(match.named("BridgeOccupantNudged")[0].payload["reason"], "span_not_embedded")
        self.assertEqual(match.bridge_state, "disconnected")

    def test_carrier_walks_and_does_not_sprint(self):
        match = SteelTideMatch(load_config())
        match.add_combatant("a1", "client-a", "humanoid_robot", "human")
        match.add_combatant("b1", "client-b", "humanoid_robot", "local_bot")
        match.choose_faction("a1", "A")
        match.choose_faction("b1", "B")
        match.choose_role("a1", "support")
        match.choose_role("b1", "support")
        match.start()
        match.place_for_test("a1", "center")
        match.enqueue("client-a", "pick_core", 0.2, combatant_id="a1")
        match.advance_to(0.2)
        match.place_for_test("a1", "spawn_a")
        departed = match.t_ms
        match.enqueue(
            "client-a",
            "request_move",
            (departed + 2250) / 1000,
            combatant_id="a1",
            dest="alley_a",
            route="repair_alley",
        )
        match.advance_to_ms(departed + 2250)
        self.assertEqual(match.named("MoveRejected")[-1].payload["reason"], "too_soon")
        match.enqueue(
            "client-a",
            "request_move",
            (departed + 3000) / 1000,
            combatant_id="a1",
            dest="alley_a",
            route="repair_alley",
        )
        match.advance_to_ms(departed + 3000)
        self.assertEqual(match.combatants["a1"].anchor, "alley_a")
        self.assertEqual(match.core.holder_id, "a1")
        self.assertEqual(match.core.anchor, "alley_a")


class BotSliceTests(unittest.TestCase):
    def test_bot_vs_bot_scores_once_without_a_double_hold(self):
        match = run_bot_slice()
        self.assertEqual(match.holder_errors(), [])
        scored = match.named("PointScored")
        self.assertEqual(len(scored), 1)
        self.assertEqual(scored[0].payload["faction"], "A")
        self.assertEqual(scored[0].t_ms, 29500)
        self.assertEqual(match.score, {"A": 1, "B": 0})
        contest = [event for event in match.events if event.t_ms == 10500 and event.name == "CorePickRejected"]
        self.assertEqual(len(contest), 1)
        self.assertEqual(contest[0].payload["reason"], "already_held")
        self.assertEqual(match.combatants["a1"].body, match.combatants["b1"].body)
        self.assertNotEqual(match.combatants["a1"].faction, match.combatants["b1"].faction)


if __name__ == "__main__":
    unittest.main()
