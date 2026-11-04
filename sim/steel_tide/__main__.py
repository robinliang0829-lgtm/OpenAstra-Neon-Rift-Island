"""Run the dev pack, a slice, or the scripted reproductions."""

from __future__ import annotations

import sys

from .bots import run_bot_slice
from .model import badge_for
from .nr_m1 import main as m1_main
from .nr_m1_bot import main as m1_bot_main
from .nr_m2_audio import main as m2_audio_main
from .nr_m2_bridge import main as m2_bridge_main
from .nr_m2_pack import main as m2_pack_main
from .nr_m2_resident import main as m2_resident_main
from .nr_m2_roles import main as m2_roles_main
from .nr_m1_pass import main as m1_pass_main
from .nr02 import main as nr02_main
from .nr03 import main as nr03_main
from .repro import run_repro_report


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["m2-pack"]:
        return m2_pack_main(args[1:])
    if args[:1] == ["m2-audio"]:
        return m2_audio_main(args[1:])
    if args[:1] == ["m2-bridge"]:
        return m2_bridge_main(args[1:])
    if args[:1] == ["m2-roles"]:
        return m2_roles_main(args[1:])
    if args[:1] == ["m2-resident"]:
        return m2_resident_main(args[1:])
    if args[:1] == ["m1-bot"]:
        return m1_bot_main(args[1:])
    if args[:1] == ["m1-pass"]:
        return m1_pass_main(args[1:])
    if args[:1] == ["m1"]:
        return m1_main(args[1:])
    if args[:1] == ["nr02"]:
        return nr02_main(args[1:])
    if args[:1] == ["nr03"]:
        return nr03_main(args[1:])
    if args[:1] == ["repro"]:
        return 0 if run_repro_report() else 1
    match = run_bot_slice()
    print("Steel Tide local-bot slice (not production residents)")
    print(f"phase={match.phase} score={match.score} holder={match.core.holder_id} t={match.t_seconds:.3f}s")
    for combatant in match.combatants.values():
        badge = badge_for(combatant.faction, match.config.badges, combatant.face_variant)
        print(
            f"  {combatant.id} client={combatant.client_id} body={combatant.body} "
            f"controller={combatant.controller} faction={combatant.faction} badge={badge['shape']}"
        )
    print("--- events ---")
    for event in match.events:
        print(event.format())
    errors = match.holder_errors()
    if errors:
        print("HOLDER AUDIT FAIL")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("HOLDER AUDIT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
