import json
import unittest

from steel_tide.__main__ import main as cli_main
from steel_tide.config import CONFIG_PATH
from steel_tide.nr_m2_pack import (
    STEPS,
    command_line,
    diff_evidence,
    evidence_paths,
    main,
    render_commands,
    zero_results,
)

ROOT = CONFIG_PATH.parents[1]


class PackRecordTests(unittest.TestCase):
    def test_steps_are_the_shipped_chain(self):
        self.assertEqual(
            [step[0] for step in STEPS],
            [
                "repro",
                "nr02",
                "nr03",
                "m1",
                "m1-pass",
                "m1-bot",
                "m2-resident",
                "m2-roles",
                "m2-bridge",
                "unittest",
            ],
        )
        commands = [command_line(module, args) for _name, module, args in STEPS]
        self.assertEqual(
            commands,
            [
                "PYTHONPATH=sim python3 -m steel_tide repro",
                "PYTHONPATH=sim python3 -m steel_tide nr02 --check",
                "PYTHONPATH=sim python3 -m steel_tide nr03 --check",
                "PYTHONPATH=sim python3 -m steel_tide m1 --check",
                "PYTHONPATH=sim python3 -m steel_tide m1-pass --check",
                "PYTHONPATH=sim python3 -m steel_tide m1-bot --check",
                "PYTHONPATH=sim python3 -m steel_tide m2-resident --check",
                "PYTHONPATH=sim python3 -m steel_tide m2-roles --check",
                "PYTHONPATH=sim python3 -m steel_tide m2-bridge --check",
                "PYTHONPATH=sim python3 -m unittest discover -s sim/tests -v",
            ],
        )
        text = render_commands()
        self.assertIn("# schema nr-m2-pack-dev-v1\n", text)
        self.assertIn("# ue_pack false\n", text)
        self.assertIn("# cook false\n", text)
        self.assertIn("# binary_package false\n", text)
        for command in commands:
            self.assertIn(command + "\n", text)

    def test_committed_record_is_all_zero_for_that_chain(self):
        results = zero_results()
        self.assertEqual(diff_evidence(results), [])
        commands = evidence_paths()["commands"].read_text(encoding="utf-8")
        exits = evidence_paths()["exit-codes"].read_text(encoding="utf-8")
        self.assertEqual(commands, render_commands())
        for result in results:
            self.assertIn(f"{result.name}\t0\t{result.command}\n", exits)
        self.assertNotIn("\t1\t", exits)

    def test_usage_and_dispatch_do_not_start_the_chain(self):
        self.assertEqual(main(["--cook"]), 2)
        self.assertEqual(cli_main(["m2-pack", "--cook"]), 2)


class ContractTests(unittest.TestCase):
    def test_card_readme_and_handoff_point_at_the_headless_pack(self):
        card = (ROOT / "docs" / "NR-M2-pack.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        handoff = (ROOT / "docs" / "HANDOFF.md").read_text(encoding="utf-8")
        source = (ROOT / "sim" / "steel_tide" / "nr_m2_pack.py").read_text(encoding="utf-8")
        entry = "python3 -m steel_tide m2-pack --check"
        self.assertIn(entry, card)
        self.assertIn(entry, readme)
        self.assertIn(entry, handoff)
        self.assertIn("无头", card)
        self.assertIn("不是 UE 包", card)
        self.assertIn("UE 仍挂", card)
        self.assertIn("UE 仍挂", handoff)
        for needle in (
            "docs/evidence/nr-m2-pack/commands.txt",
            "docs/evidence/nr-m2-pack/exit-codes.txt",
            "PYTHONPATH=sim",
            "NR-01",
            "NR-02",
            "NR-03",
            "NR-M1",
            "NR-M1-pass",
            "NR-M1-bot",
            "NR-M2-resident",
            "NR-M2-roles",
            "NR-M2-bridge",
            "repro",
            "unittest",
        ):
            self.assertIn(needle, card)
        self.assertIn("subprocess.run", source)
        self.assertNotIn("SteelTideMatch", source)
        project = json.loads((ROOT / "NeonRift.uproject").read_text(encoding="utf-8"))
        self.assertEqual(project["EngineAssociation"], "5.4")
        self.assertFalse(list((ROOT / "Content").rglob("*.umap")))
        self.assertFalse(list(ROOT.rglob("*.uasset")))


if __name__ == "__main__":
    unittest.main()
