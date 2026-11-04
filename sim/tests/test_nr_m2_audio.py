import json
import unittest

from steel_tide.__main__ import main as cli_main
from steel_tide.audio import catalog_ids, team_cue_id_for
from steel_tide.config import CONFIG_PATH
from steel_tide.events import EVENT_NAMES
from steel_tide.nr03 import run_nr03_bridge
from steel_tide.nr_m2_audio import acceptance_errors, diff_committed, main, run_m2_audio
from steel_tide.nr_m2_pack import STEPS
from steel_tide.palette import BADGES

ROOT = CONFIG_PATH.parents[1]


class AudioCueTests(unittest.TestCase):
    def test_slice_locks_cues_to_source_events(self):
        match = run_m2_audio()
        self.assertEqual(acceptance_errors(match), [])
        self.assertEqual(diff_committed(match), [])
        self.assertNotIn("AudioCue", EVENT_NAMES)
        self.assertFalse(any(event.name == "AudioCue" for event in match.events))
        self.assertEqual(match.score, {"A": 1, "B": 0})
        self.assertEqual(team_cue_id_for("A"), "sfx.team.A.open_chevron.mouth.shoulder_left")
        self.assertEqual(team_cue_id_for("B"), "sfx.team.B.closed_ring.mouth.shoulder_right")
        self.assertEqual(BADGES["A"]["light_slot"], "shoulder_left")
        self.assertEqual(BADGES["B"]["light_slot"], "shoulder_right")
        contested = [cue for cue in match.audio_cues if cue.t_ms == 500 and cue.payload["family"] == "core"]
        self.assertEqual([cue.payload["cue_id"] for cue in contested], ["sfx.core.pickup"])
        self.assertTrue(any(event.name == "CorePickRejected" and event.t_ms == 500 for event in match.events))

    def test_nr03_warning_is_the_bridge_clock(self):
        match = run_nr03_bridge()
        bridge = [cue.payload["cue_id"] for cue in match.audio_cues if cue.payload["family"] == "bridge"]
        self.assertEqual(
            bridge,
            [
                "sfx.bridge.warn",
                "sfx.bridge.light_strip",
                "sfx.bridge.light_strip",
                "sfx.bridge.light_strip",
                "sfx.bridge.connect",
            ],
        )
        started = match.named("BridgeWarningStarted")[0]
        connected = [event for event in match.named("BridgeStateChanged") if event.payload["state"] == "connected"][0]
        warn = [cue for cue in match.audio_cues if cue.payload["cue_id"] == "sfx.bridge.warn"][0]
        connect = [cue for cue in match.audio_cues if cue.payload["cue_id"] == "sfx.bridge.connect"][0]
        self.assertEqual(warn.t_ms, started.t_ms)
        self.assertEqual(connect.t_ms, connected.t_ms)
        self.assertEqual(connect.t_ms - warn.t_ms, match.config.bridge_warning_ms)
        self.assertNotIn("AudioCue", {event.name for event in match.events})

    def test_pack_steps_stay_the_rules_chain(self):
        self.assertNotIn("m2-audio", [step[0] for step in STEPS])
        card = (ROOT / "docs" / "NR-M2-pack.md").read_text(encoding="utf-8")
        self.assertIn("m2-audio", card)
        self.assertIn("不在这张表里", card)

    def test_usage_and_docs(self):
        self.assertEqual(main(["--cook"]), 2)
        self.assertEqual(cli_main(["m2-audio", "--cook"]), 2)
        card = (ROOT / "docs" / "NR-M2-audio.md").read_text(encoding="utf-8")
        handoff = (ROOT / "docs" / "HANDOFF.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("PYTHONPATH=sim python3 -m steel_tide m2-audio --check", card)
        self.assertIn("docs/evidence/nr-m2-audio/audio.log", card)
        self.assertIn("schedule_bridge_connect", card)
        self.assertIn("wired_into_m2_pack false", card)
        self.assertIn("NR-M2-audio", handoff)
        self.assertIn("m2-audio --check", readme)
        for cue_id in catalog_ids():
            self.assertIn(cue_id, card)
        runner = (ROOT / "sim" / "steel_tide" / "nr_m2_audio.py").read_text(encoding="utf-8")
        projector = (ROOT / "sim" / "steel_tide" / "audio.py").read_text(encoding="utf-8")
        self.assertIn("schedule_bridge_connect(CONNECT_AT_S)", runner)
        self.assertIn("schedule_bridge_disconnect(DISCONNECT_AT_S)", runner)
        self.assertNotIn("schedule_bridge", projector)
        project = json.loads((ROOT / "NeonRift.uproject").read_text(encoding="utf-8"))
        self.assertEqual(project["EngineAssociation"], "5.4")
        self.assertFalse(list(ROOT.rglob("*.wav")))
        self.assertFalse(list(ROOT.rglob("*.uasset")))
        self.assertFalse(list((ROOT / "Content").rglob("*.umap")))


if __name__ == "__main__":
    unittest.main()
