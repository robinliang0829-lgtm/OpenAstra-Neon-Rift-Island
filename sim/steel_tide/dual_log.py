"""Dual-end event log. Viewpoints copy sim lines. They do not score.

`docs/rules/DUAL_END_EVENT_LOG.md` is the operator schema. Header keys and the
event table are generated from `EVENT_NAMES` so the three ends stay 1:1 with
`sim/steel_tide`.
"""

from __future__ import annotations

from pathlib import Path

from .events import EVENT_NAMES
from .model import Event
from .match import SteelTideMatch

SCHEMA_ID = "nr02-dual-end-v1"
AUTHORITY = "sim/steel_tide"
EVIDENCE_DIR = Path(__file__).resolve().parents[2] / "docs" / "evidence" / "nr02"
SCHEMA_DOC = Path(__file__).resolve().parents[2] / "docs" / "rules" / "DUAL_END_EVENT_LOG.md"
ENDS = ("server", "client-a", "client-b")
HEADER_KEYS = (
    "schema",
    "authority",
    "end",
    "viewpoint_client",
    "controlled",
    "local_bots",
    "roster",
    "mirrored_holder",
    "mirrored_score",
    "event_lines",
    "comparable",
)
HEADER_KEYS_THAT_MAY_DIFFER = ("end", "viewpoint_client", "controlled")

# Replay categories. Anything not listed does not change that mirror.
HOLDER_EFFECT = {
    "CorePicked": "set",
    "CorePassed": "transfer",
    "CoreDropped": "clear",
    "CoreReset": "clear",
    "CoreReturnedToCenter": "clear",
}
SCORE_EFFECT = {
    "PointScored": "copy",
    "ScoreChannelInterrupted": "must_not_score",
    "ScoreChannelRejected": "must_not_score",
    "CoreReset": "must_not_score",
}
INTERRUPT_EVENTS = frozenset({"ScoreChannelInterrupted"})

HOLDER_ZH = {
    "set": "写入持有者（`combatant_id`）",
    "transfer": "持有者改为 `to_id`",
    "clear": "清空持有者",
    "unchanged": "不改变持有者",
}
SCORE_ZH = {
    "copy": "用 `payload.score` 覆盖镜像比分",
    "must_not_score": "不得记分",
    "unchanged": "不改变比分",
}
INTERRUPT_ZH = {"yes": "是打断", "no": "不是打断"}


def schema_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for name in EVENT_NAMES:
        rows.append(
            {
                "name": name,
                "holder": HOLDER_EFFECT.get(name, "unchanged"),
                "score": SCORE_EFFECT.get(name, "unchanged"),
                "interrupt": "yes" if name in INTERRUPT_EVENTS else "no",
            }
        )
    return rows


def schema_table_markdown() -> str:
    lines = [
        "| 事件 | 持有者 | 比分 | 打断 |",
        "| --- | --- | --- | --- |",
    ]
    for row in schema_rows():
        lines.append(
            "| `{name}` | {holder} | {score} | {interrupt} |".format(
                name=row["name"],
                holder=HOLDER_ZH[row["holder"]],
                score=SCORE_ZH[row["score"]],
                interrupt=INTERRUPT_ZH[row["interrupt"]],
            )
        )
    return "\n".join(lines)


def replay_holder(events: list[Event]) -> str | None:
    """Same transitions as `audit_holder_log`. A copy, not a second grant."""
    holder: str | None = None
    for event in events:
        effect = HOLDER_EFFECT.get(event.name, "unchanged")
        if effect == "set":
            holder = event.payload["combatant_id"]
        elif effect == "transfer":
            holder = event.payload["to_id"]
        elif effect == "clear":
            holder = None
    return holder


def replay_score(events: list[Event]) -> dict[str, int]:
    """Copy `payload.score` from PointScored. Interrupts do not add a point."""
    score = {"A": 0, "B": 0}
    for event in events:
        if SCORE_EFFECT.get(event.name, "unchanged") == "copy":
            reported = event.payload["score"]
            score = {"A": int(reported["A"]), "B": int(reported["B"])}
    return score


def format_score(score: dict[str, int]) -> str:
    return f"A={score['A']} B={score['B']}"


def format_holder(holder: str | None) -> str:
    return "-" if holder is None else holder


def event_body(match: SteelTideMatch) -> str:
    if not match.events:
        return ""
    return "\n".join(event.format() for event in match.events) + "\n"


def _ids(match: SteelTideMatch, controller: str | None = None) -> list[str]:
    combatants = match.combatants.values()
    if controller is not None:
        combatants = [combatant for combatant in combatants if combatant.controller == controller]
    return [combatant.id for combatant in sorted(combatants, key=lambda item: item.id)]


def roster_token(match: SteelTideMatch) -> str:
    parts = []
    for combatant in sorted(match.combatants.values(), key=lambda item: item.id):
        parts.append(f"{combatant.id}:{combatant.controller}:{combatant.faction}:{combatant.client_id}")
    return ",".join(parts)


def render_log(
    match: SteelTideMatch,
    end: str,
    *,
    schema: str = SCHEMA_ID,
    extra_headers: tuple[tuple[str, str], ...] = (),
) -> str:
    if end not in ENDS:
        raise ValueError(f"unknown end {end}")
    holder = format_holder(replay_holder(match.events))
    score = format_score(replay_score(match.events))
    body = event_body(match)
    event_lines = 0 if not body else body.count("\n")
    if end == "server":
        viewpoint = "-"
        controlled = ",".join(_ids(match))
    elif end == "client-a":
        viewpoint = "client-a"
        controlled = "a1"
    else:
        viewpoint = "client-b"
        controlled = "b1"
    fields = {
        "schema": schema,
        "authority": AUTHORITY,
        "end": end,
        "viewpoint_client": viewpoint,
        "controlled": controlled,
        "local_bots": ",".join(_ids(match, "local_bot")),
        "roster": roster_token(match),
        "mirrored_holder": holder,
        "mirrored_score": score,
        "event_lines": str(event_lines),
        "comparable": "event_body_identical",
    }
    lines: list[str] = []
    for key in HEADER_KEYS:
        if key == "comparable":
            for extra_key, value in extra_headers:
                lines.append(f"# {extra_key} {value}")
        lines.append(f"# {key} {fields[key]}")
    return "\n".join(lines) + "\n" + body


def render_dual_logs(
    match: SteelTideMatch,
    *,
    schema: str = SCHEMA_ID,
    extra_headers: tuple[tuple[str, str], ...] = (),
) -> dict[str, str]:
    return {
        end: render_log(match, end, schema=schema, extra_headers=extra_headers)
        for end in ENDS
    }


def parse_log(text: str) -> tuple[dict[str, str], str]:
    headers: dict[str, str] = {}
    body_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("# "):
            key, value = line[2:].split(" ", 1)
            headers[key] = value
        elif line:
            body_lines.append(line)
    body = "\n".join(body_lines) + ("\n" if body_lines else "")
    return headers, body


def compare_dual_logs(
    match: SteelTideMatch,
    logs: dict[str, str],
    *,
    schema: str = SCHEMA_ID,
    extra_headers: tuple[tuple[str, str], ...] = (),
) -> list[str]:
    errors: list[str] = []
    if tuple(logs) != ENDS:
        errors.append(f"ends {tuple(logs)} != {ENDS}")
        return errors
    bodies = {end: parse_log(text)[1] for end, text in logs.items()}
    expected_body = event_body(match)
    headers = {end: parse_log(text)[0] for end, text in logs.items()}
    if len(set(bodies.values())) != 1:
        errors.append("event bodies differ across ends")
    for end, body in bodies.items():
        if body != expected_body:
            errors.append(f"{end} event body is not the sim log")
    expected_holder = format_holder(replay_holder(match.events))
    expected_score = format_score(replay_score(match.events))
    if replay_holder(match.events) != match.core.holder_id:
        errors.append("replayed holder != match.core.holder_id")
    if replay_score(match.events) != match.score:
        errors.append(f"replayed score {replay_score(match.events)} != match.score {match.score}")
    shared: dict[str, str] | None = None
    for end, header in headers.items():
        missing = [key for key in HEADER_KEYS if key not in header]
        if missing:
            errors.append(f"{end} missing header {missing}")
            continue
        if header["schema"] != schema or header["authority"] != AUTHORITY:
            errors.append(f"{end} schema/authority drifted")
        for extra_key, value in extra_headers:
            if header.get(extra_key) != value:
                errors.append(f"{end} {extra_key} drifted")
        if header["end"] != end:
            errors.append(f"{end} header end is {header['end']}")
        if header["comparable"] != "event_body_identical":
            errors.append(f"{end} is not marked comparable")
        if header["mirrored_holder"] != expected_holder:
            errors.append(f"{end} holder mirror {header['mirrored_holder']} != {expected_holder}")
        if header["mirrored_score"] != expected_score:
            errors.append(f"{end} score mirror {header['mirrored_score']} != {expected_score}")
        body_count = 0 if not bodies[end] else bodies[end].count("\n")
        if header["event_lines"] != str(body_count):
            errors.append(f"{end} event_lines {header['event_lines']} != {body_count}")
        if header["roster"] != roster_token(match):
            errors.append(f"{end} roster drifted")
        if header["local_bots"] != ",".join(_ids(match, "local_bot")):
            errors.append(f"{end} local_bots drifted")
        comparable = {key: value for key, value in header.items() if key not in HEADER_KEYS_THAT_MAY_DIFFER}
        if shared is None:
            shared = comparable
        elif comparable != shared:
            errors.append(f"{end} shared header fields differ")
    server = headers.get("server", {})
    if server.get("viewpoint_client") != "-" or server.get("controlled") != ",".join(_ids(match)):
        errors.append("server viewpoint header is wrong")
    if headers.get("client-a", {}).get("viewpoint_client") != "client-a":
        errors.append("client-a viewpoint missing")
    if headers.get("client-a", {}).get("controlled") != "a1":
        errors.append("client-a does not control a1")
    if headers.get("client-b", {}).get("viewpoint_client") != "client-b":
        errors.append("client-b viewpoint missing")
    if headers.get("client-b", {}).get("controlled") != "b1":
        errors.append("client-b does not control b1")
    return errors


def evidence_paths(directory: Path | None = None) -> dict[str, Path]:
    root = EVIDENCE_DIR if directory is None else directory
    return {end: root / f"{end}.log" for end in ENDS}


def write_evidence(logs: dict[str, str], directory: Path | None = None) -> None:
    root = EVIDENCE_DIR if directory is None else directory
    root.mkdir(parents=True, exist_ok=True)
    for end, path in evidence_paths(root).items():
        path.write_text(logs[end], encoding="utf-8", newline="\n")


def diff_against_evidence(logs: dict[str, str], directory: Path | None = None) -> list[str]:
    errors: list[str] = []
    for end, path in evidence_paths(directory).items():
        if not path.is_file():
            errors.append(f"missing sample log {path}")
            continue
        on_disk = path.read_text(encoding="utf-8")
        if on_disk != logs[end]:
            errors.append(f"sample log drifted: {path}")
    return errors
