import unittest

from steel_tide.repro import (
    check_match_timeout,
    check_timeout_pending,
    check_timeout_reset,
    finish_timeout_reset,
    scenario_match_timeout,
    scenario_timeout_reset,
)


class TimeoutResetTests(unittest.TestCase):
    def test_overboard_timeout_resets_core_to_center(self):
        pending = scenario_timeout_reset("overboard")
        self.assertEqual(check_timeout_pending(pending, "overboard"), [])
        self.assertEqual(pending.core.anchor, "sea")
        finished = finish_timeout_reset(pending)
        self.assertEqual(check_timeout_reset(finished, "overboard"), [])
        self.assertEqual(finished.named("CorePicked")[-1].payload["combatant_id"], "b1")

    def test_stuck_timeout_resets_core_to_center(self):
        pending = scenario_timeout_reset("stuck")
        self.assertEqual(check_timeout_pending(pending, "stuck"), [])
        self.assertEqual(pending.core.anchor, "stuck")
        finished = finish_timeout_reset(pending)
        self.assertEqual(check_timeout_reset(finished, "stuck"), [])

    def test_match_clock_settles_once_and_does_not_reopen_roles(self):
        match = scenario_match_timeout()
        self.assertEqual(check_match_timeout(match), [])
        self.assertEqual(len(match.named("OvertimeStarted")), 1)
        self.assertEqual(len(match.named("MatchClockExpired")), 1)
        self.assertFalse(any(event.name == "RoleChosen" and event.t_ms > 0 for event in match.events))


if __name__ == "__main__":
    unittest.main()
