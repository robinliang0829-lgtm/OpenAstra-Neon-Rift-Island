import unittest
from pathlib import Path

from steel_tide.config import CONFIG_PATH
from steel_tide.dual_log import (
    HEADER_KEYS,
    SCHEMA_DOC,
    compare_dual_logs,
    diff_against_evidence,
    schema_rows,
    schema_table_markdown,
)
from steel_tide.events import EVENT_NAMES
from steel_tide.model import Event
from steel_tide.nr02 import acceptance_errors, evaluate, run_nr02_match

ROOT = CONFIG_PATH.parents[1]
CPP = (
    ROOT / "Source" / "NeonRift" / "Private" / "NeonRiftGameMode.cpp",
    ROOT / "Source" / "NeonRift" / "Private" / "NeonRiftGameState.cpp",
    ROOT / "Source" / "NeonRift" / "Private" / "NeonRiftPlayerState.cpp",
)
HEADERS = (
    ROOT / "Source" / "NeonRift" / "Public" / "NeonRiftGameMode.h",
    ROOT / "Source" / "NeonRift" / "Public" / "NeonRiftGameState.h",
    ROOT / "Source" / "NeonRift" / "Public" / "NeonRiftPlayerState.h",
)


class SchemaTests(unittest.TestCase):
    def test_rows_cover_each_sim_event_once(self):
        rows = schema_rows()
        names = [row["name"] for row in rows]
        self.assertEqual(names, list(EVENT_NAMES))
        self.assertEqual(len(names), len(set(names)))

    def test_schema_doc_table_matches_the_rows(self):
        doc = SCHEMA_DOC.read_text(encoding="utf-8")
        start = doc.index("<!-- nr02-event-schema -->")
        end = doc.index("<!-- /nr02-event-schema -->")
        section = doc[start:end]
        self.assertIn(schema_table_markdown(), section)
        for name in EVENT_NAMES:
            self.assertEqual(section.count(f"`{name}`"), 1)
        for key in HEADER_KEYS:
            self.assertIn(f"`{key}`", doc)

    def test_replay_follows_holder_and_score_categories(self):
        from steel_tide.dual_log import replay_holder, replay_score

        events: list[Event] = []

        def add(name: str, payload: dict) -> None:
            events.append(Event(len(events) + 1, name, payload))

        add("CorePicked", {"combatant_id": "a1"})
        self.assertEqual(replay_holder(events), "a1")
        add("CorePassed", {"from_id": "a1", "to_id": "a2"})
        self.assertEqual(replay_holder(events), "a2")
        add("ScoreChannelInterrupted", {"combatant_id": "a2", "reason": "hit"})
        add("CorePickRejected", {"combatant_id": "b1", "reason": "already_held"})
        self.assertEqual(replay_holder(events), "a2")
        self.assertEqual(replay_score(events), {"A": 0, "B": 0})
        add("CoreDropped", {"combatant_id": "a2", "reason": "downed"})
        self.assertIsNone(replay_holder(events))
        add("PointScored", {"faction": "A", "combatant_id": "a2", "points": 1, "score": {"A": 1, "B": 0}})
        self.assertEqual(replay_score(events), {"A": 1, "B": 0})
        self.assertIsNone(replay_holder(events))
        add("CoreReturnedToCenter", {"anchor": "center"})
        add("CoreReset", {"reason": "overboard", "anchor": "center"})
        self.assertIsNone(replay_holder(events))
        self.assertEqual(replay_score(events), {"A": 1, "B": 0})


class SliceTests(unittest.TestCase):
    def test_3v3_two_viewpoints_and_four_bots(self):
        match = run_nr02_match()
        self.assertEqual(acceptance_errors(match), [])
        logs, errors = evaluate(match)
        self.assertEqual(errors, [])
        self.assertEqual(diff_against_evidence(logs), [])
        self.assertEqual(compare_dual_logs(match, logs), [])
        bodies = []
        for end in ("server", "client-a", "client-b"):
            text = logs[end]
            self.assertIn(f"# end {end}\n", text)
            body = text.split("# comparable event_body_identical\n", 1)[1]
            bodies.append(body)
            self.assertIn("CorePicked", body)
            self.assertIn("already_held", body)
            self.assertIn("ScoreChannelInterrupted", body)
            self.assertIn("PointScored", body)
            self.assertIn("CoreReturnedToCenter", body)
            self.assertIn("CoreReset", body)
        self.assertEqual(bodies[0], bodies[1])
        self.assertEqual(bodies[1], bodies[2])
        self.assertLess(len(bodies[0].encode("utf-8")), 64_000)


class StubTests(unittest.TestCase):
    def test_game_framework_only_subscribes(self):
        for path in CPP + HEADERS:
            self.assertTrue(path.is_file(), path)
        state = (ROOT / "Source" / "NeonRift" / "Private" / "NeonRiftGameState.cpp").read_text(encoding="utf-8")
        for name in EVENT_NAMES:
            self.assertIn(f"NeonRiftEvents::{name}", state)
        for path in CPP:
            text = path.read_text(encoding="utf-8")
            self.assertIn("AddDynamic", text)
            self.assertIn("Broadcast", text)
            self.assertNotIn("NeonRiftEmit", text)
            self.assertNotIn("points_to_win", text)
            self.assertNotIn("+=", text)
            self.assertNotIn("++", text)
        mode = (ROOT / "Source" / "NeonRift" / "Private" / "NeonRiftGameMode.cpp").read_text(encoding="utf-8")
        self.assertIn("ANeonRiftGameState::StaticClass()", mode)
        self.assertIn("ANeonRiftPlayerState::StaticClass()", mode)

    def test_handoff_says_only_local_ue_is_missing(self):
        handoff = (ROOT / "docs" / "HANDOFF.md").read_text(encoding="utf-8")
        card = (ROOT / "docs" / "NR-02.md").read_text(encoding="utf-8")
        self.assertIn("Only local UE is missing.", handoff)
        self.assertIn("还缺的只有本机 UE", handoff)
        self.assertIn("Only local UE is missing.", card)
        self.assertIn("docs/evidence/nr02/server.log", card)
        self.assertIn("python3 -m steel_tide nr02", handoff)
        self.assertIn("5.4", handoff)
        self.assertFalse(list((ROOT / "Content").rglob("*.umap")))
        self.assertFalse(list(ROOT.rglob("*.uasset")))


if __name__ == "__main__":
    unittest.main()
