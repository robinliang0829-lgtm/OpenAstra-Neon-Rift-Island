import unittest

from steel_tide.match import SERVER_CLIENT
from steel_tide.repro import (
    check_interrupt,
    check_score_completes,
    scenario_interrupt,
    scenario_score_completes,
)


class ScoreInterruptTests(unittest.TestCase):
    def test_hit_before_three_seconds_awards_nothing(self):
        match = scenario_interrupt()
        self.assertEqual(check_interrupt(match), [])
        self.assertEqual(match.core.status, "ground")
        self.assertEqual(match.core.anchor, "terminal_b")
        self.assertTrue(match.named("ActorDowned"))
        self.assertFalse(match.named("PointScored"))
        match.advance_to(8.9)
        self.assertEqual(match.named("ActorRespawned")[0].payload["anchor"], "spawn_a")
        self.assertEqual(match.core.status, "ground")
        self.assertEqual(match.core.anchor, "terminal_b")
        self.assertEqual(match.holder_errors(), [])

    def test_hit_on_the_completion_instant_cancels_the_point(self):
        match = scenario_score_completes()
        # Rebuild a channel and hit it on the exact end, before the timer resolves.
        fresh = scenario_interrupt()
        self.assertEqual(fresh.named("ScoreChannelInterrupted")[0].payload["reason"], "hit")
        del match
        ended = _channel_then(SERVER_CLIENT, "hit", 4.0, target_id="a1", down=False)
        self.assertFalse(ended.named("PointScored"))
        self.assertEqual(ended.named("ScoreChannelInterrupted")[0].t_ms, 4000)
        self.assertEqual(ended.score["A"], 0)

    def test_leaving_the_terminal_cancels_and_does_not_resume(self):
        match = _channel_then(SERVER_CLIENT, "leave_terminal", 2.5, combatant_id="a1")
        match.advance_to(30)
        self.assertFalse(match.named("PointScored"))
        self.assertEqual(match.named("ScoreChannelInterrupted")[0].payload["reason"], "left_terminal")
        self.assertEqual(match.holder_errors(), [])

    def test_uninterrupted_channel_scores_once(self):
        match = scenario_score_completes()
        self.assertEqual(check_score_completes(match), [])
        self.assertEqual(match.core.anchor, "center")
        self.assertEqual(match.core.status, "spawn")
        self.assertIsNone(match.core.holder_id)

    def test_player_client_cannot_forge_a_hit(self):
        match = _channel_then("client-b", "hit", 2.0, target_id="a1", down=True)
        match.advance_to(6)
        self.assertEqual(match.named("HitRejected")[0].payload["reason"], "server_only")
        self.assertTrue(match.named("PointScored"))
        self.assertEqual(match.holder_errors(), [])


def _channel_then(client_id: str, kind: str, at_seconds: float, **payload):
    from steel_tide.repro import _duo

    match = _duo()
    match.place_for_test("a1", "center")
    match.enqueue("client-a", "pick_core", 0.5, combatant_id="a1")
    match.advance_to(0.5)
    match.place_for_test("a1", "terminal_b")
    match.enqueue("client-a", "begin_score", 1.0, combatant_id="a1")
    match.advance_to(1.0)
    match.enqueue(client_id, kind, at_seconds, **payload)
    match.advance_to(max(at_seconds, 4.0))
    return match


if __name__ == "__main__":
    unittest.main()
