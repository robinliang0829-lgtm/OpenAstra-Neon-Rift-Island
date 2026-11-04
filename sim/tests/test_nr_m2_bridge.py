import json
import unittest

from steel_tide.config import CONFIG_PATH, load_config
from steel_tide.dual_log import diff_against_evidence
from steel_tide.match import SteelTideMatch
from steel_tide.nr_m1_bot import run_m1_bot_match
from steel_tide.nr_m2_bridge import EVIDENCE_DIR, acceptance_errors, evaluate_slice, run_m2_bridge_match
from steel_tide.nr_m2_resident import run_m2_resident_match
from steel_tide.nr_m2_roles import run_m2_roles_match
from steel_tide.routes import authoritative_edges, plan_route, shortest_path, span_hops

ROOT = CONFIG_PATH.parents[1]


class GraphTests(unittest.TestCase):
    def test_open_span_leaves_the_graph_and_the_alley_scores_a_path(self):
        config = load_config()
        opened = authoritative_edges(config, "disconnected")
        closed = authoritative_edges(config, "connected")
        self.assertFalse(any(edge.bridge for edge in opened))
        self.assertEqual(sum(1 for edge in closed if edge.bridge), 2)
        self.assertIsNone(shortest_path(config, "spawn_a", "center", "elevated", "disconnected"))
        self.assertEqual(
            shortest_path(config, "spawn_a", "center", "repair_alley", "disconnected"),
            ["alley_a", "alley_mid", "center"],
        )
        approach, route = plan_route(config, "spawn_b", "center", "elevated", "disconnected")
        self.assertEqual(approach, ["terminal_b", "bridgehead_b"])
        self.assertEqual(route, "elevated")
        waiting, waiting_route = plan_route(config, "bridgehead_b", "center", "elevated", "disconnected")
        self.assertEqual(waiting, [])
        self.assertEqual(waiting_route, "elevated")
        crossing, crossing_route = plan_route(config, "bridgehead_b", "center", "elevated", "connected")
        self.assertEqual(crossing, ["center"])
        self.assertEqual(crossing_route, "elevated")
        escape, escape_route = plan_route(config, "bridgehead_a", "terminal_b", "repair_alley", "disconnected")
        self.assertEqual(escape_route, "walkable")
        self.assertEqual(span_hops(config, "bridgehead_a", escape or ()), ())
        self.assertIn("terminal_b", escape or [])

    def test_nudge_and_edge_reject_do_not_score_or_down(self):
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
        match.enqueue("client-a", "pick_core", 1.2, combatant_id="a1")
        match.advance_to(1.2)
        self.assertEqual(match.core.holder_id, "a1")
        held_score = dict(match.score)
        match.schedule_bridge_disconnect(2)
        match.advance_to(2)
        self.assertEqual(match.combatants["a1"].anchor, "bridgehead_a")
        self.assertEqual(match.combatants["b1"].anchor, "alley_mid")
        self.assertEqual(match.core.holder_id, "a1")
        self.assertEqual(match.core.anchor, "bridgehead_a")
        self.assertEqual(match.score, held_score)
        self.assertFalse(match.combatants["a1"].downed)
        self.assertFalse(match.named("PointScored"))
        self.assertFalse(match.named("CoreDropped"))
        self.assertFalse(match.named("ActorDowned"))
        self.assertFalse(any(edge.bridge for edge in match.route_graph))
        match.enqueue("client-a", "request_move", 2, combatant_id="a1", dest="center", route="elevated")
        match.advance_to(2)
        self.assertEqual(match.named("MoveRejected")[-1].payload["reason"], "bridge_blocked")
        self.assertEqual(match.combatants["a1"].anchor, "bridgehead_a")
        self.assertEqual(match.score, held_score)
        self.assertEqual(match.core.holder_id, "a1")


class SliceTests(unittest.TestCase):
    def test_bridge_slice_matches_the_sample_logs(self):
        match = run_m2_bridge_match()
        self.assertEqual(acceptance_errors(match), [])
        logs, errors = evaluate_slice(match)
        self.assertEqual(errors, [])
        self.assertEqual(diff_against_evidence(logs, EVIDENCE_DIR), [])
        bodies = []
        for end in ("server", "client-a", "client-b"):
            text = logs[end]
            self.assertIn("# schema nr-m2-bridge-dual-end-v1\n", text)
            self.assertIn("# digital_residents a2\n", text)
            body = text.split("# comparable event_body_identical\n", 1)[1]
            bodies.append(body)
            self.assertIn('"state": "connected"', body)
            self.assertIn('"state": "disconnected"', body)
            self.assertIn('"reason": "path_recompute"', body)
            self.assertIn('"reason": "bridge_blocked"', body)
            self.assertIn('"reason": "span_not_embedded"', body)
            self.assertIn('"route": "repair_alley"', body)
            self.assertIn('"span_walkable": true', body)
            self.assertIn('"span_walkable": false', body)
            self.assertIn('"kind": "points"', body)
            self.assertNotIn('"x_m"', body)
            self.assertNotIn('"y_m"', body)
            self.assertNotIn('"pos"', body)
        self.assertEqual(bodies[0], bodies[1])
        self.assertEqual(bodies[1], bodies[2])
        self.assertNotIn("OvertimeStarted", bodies[0])
        self.assertNotIn("ActorDowned", bodies[0])
        self.assertNotIn("place_for_test", bodies[0])
        connected = bodies[0].index('"state": "connected"')
        disconnected = bodies[0].index('"state": "disconnected"')
        self.assertLess(connected, disconnected)

    def test_earlier_cards_do_not_recompute_on_their_alley_plans(self):
        for match in (run_m1_bot_match(), run_m2_resident_match(), run_m2_roles_match()):
            reasons = [
                event.payload.get("reason")
                for event in match.named("BotDecision") + match.named("ResidentDecision")
            ]
            self.assertNotIn("path_recompute", reasons)
            self.assertFalse(match.named("BridgeOccupantNudged"))


class ContractTests(unittest.TestCase):
    def test_card_leaves_ue_hanging_and_names_the_command(self):
        card = (ROOT / "docs" / "NR-M2-bridge.md").read_text(encoding="utf-8")
        handoff = (ROOT / "docs" / "HANDOFF.md").read_text(encoding="utf-8")
        source = (ROOT / "sim" / "steel_tide" / "nr_m2_bridge.py").read_text(encoding="utf-8")
        self.assertIn("UE 仍挂", card)
        self.assertIn("python3 -m steel_tide m2-bridge", card)
        self.assertIn("python3 -m steel_tide m2-bridge", handoff)
        self.assertIn("schedule_bridge_connect(CONNECT_AT_S)", source)
        self.assertIn("schedule_bridge_disconnect(DISCONNECT_AT_S)", source)
        self.assertNotIn("_begin_bridge_warning", source)
        self.assertNotIn("place_for_test", source)
        for needle in (
            "path_recompute",
            "bridge_blocked",
            "span_not_embedded",
            "connected",
            "disconnected",
            "repair_alley",
            "contest_core",
            "close_range_pass",
            "kind=points",
            "docs/evidence/nr-m2-bridge/server.log",
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
