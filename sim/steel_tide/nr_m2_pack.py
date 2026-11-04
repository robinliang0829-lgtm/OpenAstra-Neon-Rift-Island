"""NR-M2 dev pack: one headless command chains the shipped checks.

Others clone the repo, set PYTHONPATH, and run this. It is a Python
acceptance pack. It does not cook, package a binary, or launch UE.

    PYTHONPATH=sim python3 -m steel_tide m2-pack
    PYTHONPATH=sim python3 -m steel_tide m2-pack --check
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .config import REPO_ROOT

SCHEMA = "nr-m2-pack-dev-v1"
EVIDENCE_DIR = REPO_ROOT / "docs" / "evidence" / "nr-m2-pack"

# name, module, arguments after `python3 -m <module>`
# m2-audio is a separate --check. It is not a step here. See docs/NR-M2-audio.md.
STEPS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("repro", "steel_tide", ("repro",)),
    ("nr02", "steel_tide", ("nr02", "--check")),
    ("nr03", "steel_tide", ("nr03", "--check")),
    ("m1", "steel_tide", ("m1", "--check")),
    ("m1-pass", "steel_tide", ("m1-pass", "--check")),
    ("m1-bot", "steel_tide", ("m1-bot", "--check")),
    ("m2-resident", "steel_tide", ("m2-resident", "--check")),
    ("m2-roles", "steel_tide", ("m2-roles", "--check")),
    ("m2-bridge", "steel_tide", ("m2-bridge", "--check")),
    ("unittest", "unittest", ("discover", "-s", "sim/tests", "-v")),
)


def command_line(module: str, args: tuple[str, ...]) -> str:
    return f"PYTHONPATH=sim python3 -m {module} " + " ".join(args)


def _header() -> str:
    return (
        f"# schema {SCHEMA}\n"
        "# kind headless-python-dev-pack\n"
        "# ue_pack false\n"
        "# cook false\n"
        "# binary_package false\n"
    )


def render_commands() -> str:
    lines = [_header().rstrip("\n")]
    for _name, module, args in STEPS:
        lines.append(command_line(module, args))
    return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class StepResult:
    name: str
    command: str
    exit_code: int


def render_exit_codes(results: list[StepResult]) -> str:
    lines = [_header().rstrip("\n"), "# columns name exit_code command"]
    for result in results:
        lines.append(f"{result.name}\t{result.exit_code}\t{result.command}")
    return "\n".join(lines) + "\n"


def zero_results() -> list[StepResult]:
    return [StepResult(name, command_line(module, args), 0) for name, module, args in STEPS]


def evidence_paths() -> dict[str, Path]:
    return {
        "commands": EVIDENCE_DIR / "commands.txt",
        "exit-codes": EVIDENCE_DIR / "exit-codes.txt",
    }


def evidence_texts(results: list[StepResult]) -> dict[str, str]:
    return {
        "commands": render_commands(),
        "exit-codes": render_exit_codes(results),
    }


def _child_env() -> dict[str, str]:
    env = os.environ.copy()
    sim = str(REPO_ROOT / "sim")
    prior = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = sim if not prior else sim + os.pathsep + prior
    return env


def run_pack() -> list[StepResult]:
    """Run each shipped check in its own process and keep the exit code."""
    results: list[StepResult] = []
    env = _child_env()
    for name, module, args in STEPS:
        command = command_line(module, args)
        print(f"--- {name} ---", flush=True)
        print(command, flush=True)
        completed = subprocess.run(
            [sys.executable, "-m", module, *args],
            cwd=REPO_ROOT,
            env=env,
            check=False,
        )
        code = completed.returncode
        print(f"exit {name} {code}", flush=True)
        results.append(StepResult(name, command, code))
    return results


def write_evidence(results: list[StepResult]) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    for key, text in evidence_texts(results).items():
        evidence_paths()[key].write_text(text, encoding="utf-8", newline="\n")


def diff_evidence(results: list[StepResult]) -> list[str]:
    errors: list[str] = []
    for key, text in evidence_texts(results).items():
        path = evidence_paths()[key]
        if not path.is_file():
            errors.append(f"missing pack record {path}")
            continue
        on_disk = path.read_text(encoding="utf-8")
        if on_disk != text:
            errors.append(f"pack record drifted: {path}")
    return errors


def acceptance_errors(results: list[StepResult]) -> list[str]:
    errors: list[str] = []
    names = [step[0] for step in STEPS]
    if [item.name for item in results] != names:
        errors.append("pack did not run the required steps in order")
    for result in results:
        if result.exit_code != 0:
            errors.append(f"{result.name} exit {result.exit_code}")
    return errors


def main(argv: list[str] | None = None) -> int:
    args = [] if argv is None else list(argv)
    if args not in ([], ["--check"]):
        print("usage: PYTHONPATH=sim python3 -m steel_tide m2-pack [--check]", flush=True)
        return 2
    print("NR-M2 pack: headless Python dev pack. Not a UE pack. No cook. No binary package.", flush=True)
    results = run_pack()
    errors = acceptance_errors(results)
    if args == ["--check"]:
        errors.extend(diff_evidence(results))
    else:
        write_evidence(results)
    if errors:
        print("NR-M2 pack FAIL", flush=True)
        for error in errors:
            print(f"  - {error}", flush=True)
        return 1
    print("NR-M2 pack PASS", flush=True)
    print(f"steps={len(results)} failed=0 ue_pack=false", flush=True)
    for key, path in evidence_paths().items():
        print(f"{key}={path.as_posix()}", flush=True)
    if args == ["--check"]:
        print("checked command list and exit codes", flush=True)
    return 0
