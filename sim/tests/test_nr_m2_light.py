import json
import unittest

from steel_tide.__main__ import main as cli_main
from steel_tide.config import CONFIG_PATH, load_config
from steel_tide.events import EVENT_NAMES
from steel_tide.light import catalog_ids, shoulder_cue_id_for
from steel_tide.match import SERVER_CLIENT, SteelTideMatch
from steel_tide.nr03 import run_nr03_bridge
from steel_tide.nr_m2_light import acceptance_errors, diff_committed, main, run_m2_light
from steel_tide.nr_m2_pack import STEPS
from steel_tide.palette import BADGES

ROOT = CONFIG_PATH.parents[1]


class LightCueTests(unittest.TestCase):
    def test_slice_locks_cues_to_source_events(self):
        match = run_m2_light()
        self.assertEqual(acceptance_errors(match), [])
        self.assertEqual(diff_committed(match), [])
        self.assertNotIn("LightCue", EVENT_NAMES)
        self.assertFalse(any(event.name == "LightCue" for event in match.events))
        self.assertEqual(match.score, {"A": 1, "B": 0})
        self.assertEqual(shoulder_cue_id_for("A"), "light.shoulder.A.open_chevron.shoulder_left")
        self.assertEqual(shoulder_cue_id_for("B"), "light.shoulder.B.closed_ring.shoulder_right")
        self.assertEqual(BADGES["A"]["light_slot"], "shoulder_left")
        self.assertEqual(BADGES["B"]["light_slot"], "shoulder_right")
        lighting = load_config().lighting
        self.assertEqual(lighting.day_port_intensity, 1.0)
        self.assertEqual(lighting.night_port_intensity, 0.25)
        self.assertGreater(lighting.shoulder_intensity / lighting.day_port_intensity, lighting.min_readable_contrast)
        bars = [cue for cue in match.light_cues if cue.payload["cue_id"] == "light.terminal.read_bar"]
        scores = [cue for cue in match.light_cues if cue.payload["cue_id"] == "light.score"]
        spawned = [cue for cue in match.light_cues if cue.payload["cue_id"] == "light.spawn_protection"]
        self.assertEqual(len(bars), 1)
        self.assertEqual(len(scores), 1)
        self.assertGreaterEqual(len(spawned), 1)
        self.assertTrue(any(event.name == "ScoreChannelRejected" and event.t_ms == 3200 for event in match.events))
        self.assertFalse(any(cue.t_ms == 3200 for cue in bars))

    def test_nr03_warning_is_the_bridge_clock(self):
        match = run_nr03_bridge()
        bridge = [cue.payload["cue_id"] for cue in match.light_cues if cue.payload["family"] == "bridge"]
        self.assertEqual(
            bridge,
            [
                "light.bridge.ramp",
                "light.bridge.ramp",
                "light.bridge.ramp",
                "light.bridge.ramp",
                "light.bridge.ramp",
                "light.bridge.connect",
            ],
        )
        started = match.named("BridgeWarningStarted")[0]
        completed = match.named("BridgeWarningCompleted")[0]
        connected = [event for event in match.named("BridgeStateChanged") if event.payload["state"] == "connected"][0]
        ramps = [cue for cue in match.light_cues if cue.payload["cue_id"] == "light.bridge.ramp"]
        connect = [cue for cue in match.light_cues if cue.payload["cue_id"] == "light.bridge.connect"][0]
        self.assertEqual(ramps[0].t_ms, started.t_ms)
        self.assertEqual(ramps[-1].t_ms, completed.t_ms)
        self.assertEqual(connect.t_ms, connected.t_ms)
        self.assertEqual(connect.t_ms, completed.t_ms)
        self.assertEqual(connect.t_ms - ramps[0].t_ms, match.config.bridge_warning_ms)
        self.assertEqual([cue.t_ms - started.t_ms for cue in ramps], [0, 1000, 2000, 3000, 4000])
        self.assertNotIn("LightCue", {event.name for event in match.events})
        self.assertEqual(match.score, {"A": 0, "B": 0})

    def test_respawn_protection_uses_the_respawn_event_clock(self):
        config = load_config()
        match = SteelTideMatch(config)
        match.add_combatant("a1", "client-a", "humanoid_robot", "human", face_variant="plate-7")
        match.add_combatant("b1", "client-b", "humanoid_robot", "human", face_variant="plate-7")
        match.choose_faction("a1", "A")
        match.choose_faction("b1", "B")
        match.choose_role("a1", "assault")
        match.choose_role("b1", "assault")
        match.start()
        match.enqueue(SERVER_CLIENT, "hit", 3.0, target_id="a1", down=True)
        match.advance_to(3.0 + config.down_seconds)
        respawned = match.named("ActorRespawned")
        cues = [cue for cue in match.light_cues if cue.payload.get("source_event") == "ActorRespawned"]
        self.assertEqual(len(respawned), 1)
        self.assertEqual(len(cues), 1)
        self.assertEqual(cues[0].t_ms, respawned[0].t_ms)
        self.assertEqual(cues[0].payload["cue_id"], "light.spawn_protection")
        self.assertEqual(cues[0].payload["protection_until_ms"], respawned[0].payload["protection_until_ms"])
        self.assertEqual(cues[0].payload["protection_until_ms"], respawned[0].t_ms + config.spawn_protection_ms)
        self.assertEqual(match.score, {"A": 0, "B": 0})
        self.assertFalse(match.named("PointScored"))

    def test_pack_steps_stay_the_rules_chain(self):
        self.assertNotIn("m2-light", [step[0] for step in STEPS])
        card = (ROOT / "docs" / "NR-M2-pack.md").read_text(encoding="utf-8")
        self.assertIn("m2-light", card)
        self.assertIn("不在这张表里", card)
        self.assertIn("旁路", card)

    def test_usage_and_docs(self):
        self.assertEqual(main(["--cook"]), 2)
        self.assertEqual(cli_main(["m2-light", "--cook"]), 2)
        card = (ROOT / "docs" / "NR-M2-light.md").read_text(encoding="utf-8")
        handoff = (ROOT / "docs" / "HANDOFF.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("PYTHONPATH=sim python3 -m steel_tide m2-light --check", card)
        self.assertIn("docs/evidence/nr-m2-light/light.log", card)
        self.assertIn("schedule_bridge_connect", card)
        self.assertIn("wired_into_m2_pack false", card)
        self.assertIn("day_port_intensity", card)
        self.assertIn("night_port_intensity", card)
        self.assertIn("NR-M2-light", handoff)
        self.assertIn("m2-light --check", readme)
        for cue_id in catalog_ids():
            self.assertIn(cue_id, card)
        runner = (ROOT / "sim" / "steel_tide" / "nr_m2_light.py").read_text(encoding="utf-8")
        projector = (ROOT / "sim" / "steel_tide" / "light.py").read_text(encoding="utf-8")
        self.assertIn("schedule_bridge_connect(CONNECT_AT_S)", runner)
        self.assertIn("schedule_bridge_disconnect(DISCONNECT_AT_S)", runner)
        self.assertNotIn("schedule_bridge", projector)
        self.assertNotIn("bridge_warning", projector)
        self.assertNotIn("score_channel", projector)
        project = json.loads((ROOT / "NeonRift.uproject").read_text(encoding="utf-8"))
        self.assertEqual(project["EngineAssociation"], "5.4")
        self.assertFalse(list(ROOT.rglob("*.uasset")))
        self.assertFalse(list((ROOT / "Content").rglob("*.umap")))
        self.assertFalse(list((ROOT / "docs" / "evidence" / "nr-m2-light").rglob("*.png")))


if __name__ == "__main__":
    unittest.main()
