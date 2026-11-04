import json
import unittest

from steel_tide.__main__ import main as cli_main
from steel_tide.config import CONFIG_PATH
from steel_tide.dual_log import diff_against_evidence, parse_log
from steel_tide.events import EVENT_NAMES
from steel_tide.nr_m2_fail import (
    EVIDENCE_DIR,
    PATHS,
    WIRED_INTO_M2_PACK,
    acceptance_errors,
    evaluate_slice,
    main,
    run_m2_fail_match,
)
from steel_tide.nr_m2_pack import STEPS

ROOT = CONFIG_PATH.parents[1]


class SliceTests(unittest.TestCase):
    def test_three_failure_paths_match_the_sample_logs(self):
        match = run_m2_fail_match()
        self.assertEqual(acceptance_errors(match), [])
        logs, errors = evaluate_slice(match)
        self.assertEqual(errors, [])
        self.assertEqual(diff_against_evidence(logs, EVIDENCE_DIR), [])
        bodies = []
        for end in ("server", "client-a", "client-b"):
            text = logs[end]
            self.assertIn("# schema nr-m2-fail-dual-end-v1\n", text)
            self.assertIn("# authority sim/steel_tide\n", text)
            self.assertIn("# fail_paths parallel_pick,hit_interrupt,timeout_no_role_redraw\n", text)
            self.assertIn("# role_menu assault,support,recon\n", text)
            self.assertIn("# wired_into_m2_pack false\n", text)
            header, body = parse_log(text)
            bodies.append(body)
            self.assertEqual(header["wired_into_m2_pack"], "false")
            self.assertEqual(header["fail_paths"], PATHS)
            self.assertEqual(header["mirrored_score"], "A=0 B=0")
            self.assertEqual(header["mirrored_holder"], "-")
            self.assertNotIn("PointScored", body)
            self.assertNotIn("CoreReturnedToCenter", body)
            self.assertNotIn("CoreReset", body)
            self.assertIn('"reason": "already_held"', body)
            self.assertIn('"reason": "hit"', body)
            self.assertIn('"kind": "draw"', body)
            self.assertIn('"role_select_open": false', body)
            self.assertNotIn('"role_select_open": true', body)
        self.assertEqual(bodies[0], bodies[1])
        self.assertEqual(bodies[1], bodies[2])
        self.assertEqual(logs["server"].split("# comparable event_body_identical\n", 1)[1].count("RoleChosen"), 2)
        self.assertEqual(match.core.holder_id, None)
        self.assertEqual(match.score, {"A": 0, "B": 0})
        self.assertFalse(match.lobby_open)
        self.assertEqual(match.combatants["a1"].role, "assault")
        self.assertEqual(match.combatants["b1"].role, "support")
        picked = match.named("CorePicked")
        self.assertEqual(len(picked), 1)
        self.assertEqual(picked[0].payload["combatant_id"], "a1")
        self.assertEqual(match.named("CorePickRejected")[0].payload["combatant_id"], "b1")
        self.assertEqual(picked[0].t_ms, match.named("CorePickRejected")[0].t_ms)

    def test_pack_step_list_matches_the_declared_flag(self):
        self.assertFalse(WIRED_INTO_M2_PACK)
        self.assertNotIn("m2-fail", [step[0] for step in STEPS])
        commands = (ROOT / "docs" / "evidence" / "nr-m2-pack" / "commands.txt").read_text(encoding="utf-8")
        exits = (ROOT / "docs" / "evidence" / "nr-m2-pack" / "exit-codes.txt").read_text(encoding="utf-8")
        self.assertNotIn("m2-fail", commands)
        self.assertNotIn("m2-fail", exits)
        source = (ROOT / "sim" / "steel_tide" / "nr_m2_fail.py").read_text(encoding="utf-8")
        self.assertNotIn("_emit(", source)
        self.assertNotIn("_complete_score", source)
        self.assertNotIn("_grant_pick", source)
        self.assertNotIn("EVENT_NAMES =", source)
        for event in run_m2_fail_match().events:
            self.assertIn(event.name, EVENT_NAMES)


class ContractTests(unittest.TestCase):
    def test_card_names_the_parallel_check_and_leaves_ue_hanging(self):
        card = (ROOT / "docs" / "NR-M2-fail.md").read_text(encoding="utf-8")
        handoff = (ROOT / "docs" / "HANDOFF.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        pack = (ROOT / "docs" / "NR-M2-pack.md").read_text(encoding="utf-8")
        dual = (ROOT / "docs" / "rules" / "DUAL_END_EVENT_LOG.md").read_text(encoding="utf-8")
        wiring = (ROOT / "docs" / "rules" / "UE_EVENT_WIRING.md").read_text(encoding="utf-8")
        entry = "python3 -m steel_tide m2-fail --check"
        for text in (card, handoff, readme, pack, dual, wiring):
            self.assertIn(entry, text)
        self.assertIn("UE 仍挂", card)
        self.assertIn("wired_into_m2_pack", card)
        self.assertIn("false", card)
        for needle in (
            "already_held",
            "ScoreChannelInterrupted",
            "PointScored",
            "role_select_open",
            "assault",
            "support",
            "recon",
            "docs/evidence/nr-m2-fail/server.log",
            "不进",
        ):
            self.assertIn(needle, card)
        self.assertIn("wired_into_m2_pack", pack)
        greybox = json.loads((ROOT / "config" / "steel_tide_greybox.json").read_text(encoding="utf-8"))
        self.assertEqual(greybox["match_seconds"], 360)
        self.assertEqual(greybox["overtime_seconds"], 60)
        self.assertEqual(greybox["score_channel_seconds"], 3)
        self.assertEqual(greybox["roles"], ["assault", "support", "recon"])
        project = json.loads((ROOT / "NeonRift.uproject").read_text(encoding="utf-8"))
        self.assertEqual(project["EngineAssociation"], "5.4")
        self.assertFalse(list((ROOT / "Content").rglob("*.umap")))
        self.assertFalse(list(ROOT.rglob("*.uasset")))

    def test_usage_and_check_dispatch(self):
        self.assertEqual(main(["--cook"]), 2)
        self.assertEqual(cli_main(["m2-fail", "--cook"]), 2)
        self.assertEqual(main(["--check"]), 0)
        self.assertEqual(cli_main(["m2-fail", "--check"]), 0)


if __name__ == "__main__":
    unittest.main()
