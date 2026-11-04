"""Run the bot slice or the scripted reproductions."""

from __future__ import annotations

import sys

from .bots import run_bot_slice
from .model import badge_for
from .repro import run_repro_report


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
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
