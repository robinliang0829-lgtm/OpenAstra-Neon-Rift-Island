import json
import unittest

from steel_tide.config import CONFIG_PATH, load_config
from steel_tide.dual_log import diff_against_evidence
from steel_tide.match import SERVER_CLIENT, SteelTideMatch
from steel_tide.nr_m1 import (
    EVIDENCE_DIR,
    acceptance_errors,
    acceptance_retie,
    diff_retie,
    evaluate_slice,
    render_retie,
    rule_errors,
    run_m1_match,
    run_m1_retie,
)

ROOT = CONFIG_PATH.parents[1]
CPP = (
    ROOT / "Source" / "NeonRift" / "Private" / "NeonRiftGameMode.cpp",
    ROOT / "Source" / "NeonRift" / "Private" / "NeonRiftGameState.cpp",
    ROOT / "Source" / "NeonRift" / "Private" / "NeonRiftPlayerState.cpp",
)


class SliceTests(unittest.TestCase):
    def test_prep_slice_matches_the_sample_logs(self):
        match = run_m1_match()
        self.assertEqual(acceptance_errors(match), [])
        logs, errors = evaluate_slice(match)
        self.assertEqual(errors, [])
        self.assertEqual(diff_against_evidence(logs, EVIDENCE_DIR), [])
        bodies = []
        for end in ("server", "client-a", "client-b"):
            text = logs[end]
            self.assertIn("# schema nr-m1-dual-end-v1\n", text)
            self.assertIn("# identities ", text)
            body = text.split("# comparable event_body_identical\n", 1)[1]
            bodies.append(body)
            self.assertIn("ActorRespawned", body)
            self.assertIn("spawn_protection", body)
            self.assertIn("OvertimeStarted", body)
            self.assertIn("MatchSettled", body)
        self.assertEqual(bodies[0], bodies[1])
        self.assertEqual(bodies[1], bodies[2])
        retie = run_m1_retie()
        self.assertEqual(acceptance_retie(retie), [])
        self.assertEqual(diff_retie(render_retie(retie)), [])
        self.assertEqual(rule_errors(), [])

    def test_spawn_protection_does_not_spend_a_directed_shield(self):
        match = SteelTideMatch(load_config())
        match.add_combatant("a1", "client-a", "humanoid_robot", "human")
        match.add_combatant("a2", "bot-a2", "humanoid_robot", "local_bot")
        match.add_combatant("b1", "client-b", "humanoid_robot", "human")
        match.choose_faction("a1", "A")
        match.choose_faction("a2", "A")
        match.choose_faction("b1", "B")
        match.choose_role("a1", "assault")
        match.choose_role("a2", "support")
        match.choose_role("b1", "recon")
        match.start()
        match.place_for_test("a1", "spawn_a")
        match.place_for_test("a2", "spawn_a")
        match.enqueue("bot-a2", "use_ability", 0.2, combatant_id="a2", ability="shield", target_id="a1")
        match.enqueue(SERVER_CLIENT, "hit", 0.2, target_id="a1", down=True)
        match.advance_to(0.2)
        self.assertEqual(match.named("HitIgnored")[-1].payload["reason"], "spawn_protection")
        self.assertEqual(match.combatants["a1"].shield_charges, 1)
        self.assertFalse(match.combatants["a1"].downed)
        self.assertEqual(match.holder_errors(), [])


class ContractTests(unittest.TestCase):
    def test_docs_leave_ue_hanging_and_name_the_command(self):
        card = (ROOT / "docs" / "NR-M1-prep.md").read_text(encoding="utf-8")
        handoff = (ROOT / "docs" / "HANDOFF.md").read_text(encoding="utf-8")
        self.assertIn("UE 仍挂", card)
        self.assertIn("UE 仍挂", handoff)
        self.assertIn("Only local UE is missing.", handoff)
        self.assertIn("NR-03 规格已入库、实机录像仍等 UE", handoff)
        for needle in (
            "python3 -m steel_tide m1",
            "docs/evidence/nr-m1/server.log",
            "docs/evidence/nr-m1/retie.log",
            "down_seconds",
            "spawn_protection_seconds",
            "overtime_seconds",
            "kind=score",
            "kind=draw",
            "kind=points",
            "humanoid_robot",
            "open_chevron",
            "closed_ring",
            "BodyType",
            "MatchFaction",
            "ControllerKind",
        ):
            self.assertIn(needle, card)
        self.assertIn("python3 -m steel_tide m1", handoff)
        project = json.loads((ROOT / "NeonRift.uproject").read_text(encoding="utf-8"))
        self.assertEqual(project["EngineAssociation"], "5.4")
        self.assertFalse(list((ROOT / "Content").rglob("*.umap")))
        self.assertFalse(list(ROOT.rglob("*.uasset")))

    def test_framework_stores_three_labels_and_does_not_score(self):
        player_h = (ROOT / "Source" / "NeonRift" / "Public" / "NeonRiftPlayerState.h").read_text(encoding="utf-8")
        state_h = (ROOT / "Source" / "NeonRift" / "Public" / "NeonRiftGameState.h").read_text(encoding="utf-8")
        self.assertIn("BodyType", player_h)
        self.assertIn("MatchFaction", player_h)
        self.assertIn("ControllerKind", player_h)
        self.assertIn("SetIdentityLabels", player_h)
        self.assertIn("MirroredIdentityPayload", state_h)
        for path in CPP:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("points_to_win", text)
            self.assertNotIn("+=", text)
            self.assertNotIn("++", text)
            self.assertNotIn("NeonRiftEmit", text)
        mode = (ROOT / "Source" / "NeonRift" / "Private" / "NeonRiftGameMode.cpp").read_text(encoding="utf-8")
        self.assertIn("AddDynamic", mode)
        self.assertIn("Broadcast", mode)


if __name__ == "__main__":
    unittest.main()
