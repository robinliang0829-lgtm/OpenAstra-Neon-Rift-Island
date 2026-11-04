"""Thin digital-resident policy. Not a production resident.

`select_match` accepts a legal offered seat, or the first legal faction and
role when no seat is offered, and refuses an illegal one. `decide` returns
the same contest, pass, interrupt, and score intents as the local bot, using
only the perceived dict.

Enemy coordinates behind the repair alley are not in that dict. A covered
enemy is an id. Teammate signals may carry an anchor name and `distance_m`.
No `pos`, `x_m`, or `y_m` is fed in.

When the match sets `role_abilities_enabled`, `decide` may also return the
role ability: assault dash, support shield, or recon mark. The reason is the
role id. A covered target is still only an id.
"""

from __future__ import annotations

import math

from .bot_policy import Decision
from .match import SteelTideMatch
from .role_ability import attach_resident_ability, choose_role_ability, view_from_resident

# Not a production resident. The sim match is the only scorer.
PRODUCTION_RESIDENT = False

POST_WALL_KEYS = ("location", "pos", "x", "x_m", "y", "y_m")
_HIDDEN_KEYS = frozenset({"id"})
_VISIBLE_KEYS = frozenset({"anchor", "faction", "id"})
_TEAM_KEYS = frozenset({"anchor", "distance_m", "downed", "id", "role"})
_NAME_KEYS = (
    "channel_reader_anchor",
    "core_anchor",
    "core_home",
    "holder_anchor",
    "holder_score_terminal",
    "score_terminal",
    "self_anchor",
)


class DigitalResidentPort:
    """Runnable thin policy. Join a legal seat, then intent from perception."""

    def __init__(self) -> None:
        self.joined = False
        self.faction: str | None = None
        self.role: str | None = None
        self.select_calls = 0
        self.decide_calls = 0
        self.hidden_shapes: list[frozenset[str]] = []

    def select_match(self, perceived: dict) -> dict:
        """Choose whether to join and which legal faction and role to take."""
        self.select_calls += 1
        assert_no_post_wall(perceived)
        legal = perceived.get("legal_factions") or []
        roles = perceived.get("roles") or []
        if not isinstance(legal, (list, tuple)) or not isinstance(roles, (list, tuple)):
            return self._refuse()
        if "offered_faction" in perceived:
            offered = perceived.get("offered_faction")
        elif legal:
            offered = legal[0]
        else:
            offered = None
        if "offered_role" in perceived:
            role = perceived.get("offered_role")
        elif roles:
            role = roles[0]
        else:
            role = None
        if offered not in legal or role not in roles:
            return self._refuse()
        self.joined = True
        self.faction = offered
        self.role = role
        return {"faction": offered, "join": True, "role": role}

    def decide(self, perceived: dict) -> Decision | None:
        """One intent from perception. Humans are not decided here."""
        self.decide_calls += 1
        assert_no_post_wall(perceived)
        for item in perceived.get("hidden_targets") or []:
            self.hidden_shapes.append(frozenset(item))
        if not self.joined:
            return None
        base = _decide_thin(perceived)
        if not perceived.get("role_abilities"):
            return base
        return choose_role_ability(view_from_resident(perceived, base), base)

    def _refuse(self) -> dict:
        self.joined = False
        self.faction = None
        self.role = None
        return {"faction": None, "join": False, "role": None}


def lobby_view(match: SteelTideMatch, combatant, offered_faction: str, offered_role: str) -> dict:
    """Seat offer. No anchors and no enemy coordinates."""
    view = {
        "body": combatant.body,
        "combatant_id": combatant.id,
        "controller": combatant.controller,
        "legal_factions": list(match.config.faction_rule[combatant.body]),
        "offered_faction": offered_faction,
        "offered_role": offered_role,
        "phase": match.phase,
        "roles": list(match.config.roles),
    }
    assert_no_post_wall(view)
    return view


def perceive(match: SteelTideMatch, combatant) -> dict:
    """What a human in this volume can use. Covered enemies are ids only."""
    config = match.config
    view: dict = {
        "body": combatant.body,
        "channel_active": match.channel is not None,
        "combatant_id": combatant.id,
        "controller": combatant.controller,
        "core_home": "center",
        "core_pickable": match.core.pickable,
        "downed": combatant.downed,
        "faction": combatant.faction,
        "holding_core": match.core.holder_id == combatant.id,
        "interrupt_open": not match.named("ScoreChannelInterrupted"),
        "legal_factions": list(config.faction_rule[combatant.body]),
        "pass_open": not match.named("CorePassed"),
        "pass_range_m": config.pass_range_m,
        "phase": match.phase,
        "role": combatant.role,
        "roles": list(config.roles),
        "self_anchor": combatant.anchor,
    }
    if combatant.faction:
        view["score_terminal"] = config.score_terminal[combatant.faction]
    if match.core.holder_id is None and match.anchor_visible(combatant.anchor, match.core.anchor):
        view["core_anchor"] = match.core.anchor
    teammates = []
    visible = []
    hidden = []
    for other in match.combatants.values():
        if other.id == combatant.id:
            continue
        if combatant.faction is not None and other.faction == combatant.faction:
            teammates.append(
                {
                    "anchor": other.anchor,
                    "distance_m": round(_distance(combatant, other), 3),
                    "downed": other.downed,
                    "id": other.id,
                    "role": other.role,
                }
            )
            continue
        if match.anchor_visible(combatant.anchor, other.anchor):
            visible.append({"anchor": other.anchor, "faction": other.faction, "id": other.id})
        else:
            hidden.append({"id": other.id})
    view["hidden_targets"] = hidden
    view["teammates"] = teammates
    view["visible_targets"] = visible
    holder_id = match.core.holder_id
    if holder_id and holder_id != combatant.id:
        holder = match.combatants[holder_id]
        view["holder_faction"] = holder.faction
        view["holder_id"] = holder_id
        if holder.faction:
            # Public score terminal for that faction, not the holder's live coordinates.
            view["holder_score_terminal"] = config.score_terminal[holder.faction]
        if holder.faction == combatant.faction or match.anchor_visible(combatant.anchor, holder.anchor):
            view["holder_anchor"] = holder.anchor
    channel = match.channel
    if channel is not None:
        reader = match.combatants[channel.combatant_id]
        if reader.faction == combatant.faction or match.anchor_visible(combatant.anchor, reader.anchor):
            view["channel_reader_anchor"] = reader.anchor
            view["channel_reader_faction"] = reader.faction
            view["channel_reader_id"] = reader.id
    attach_resident_ability(match, combatant, view)
    assert_no_post_wall(view)
    return view


def assert_no_post_wall(perceived: dict) -> None:
    """Refuse a view that carries enemy coordinates from behind cover."""
    if not isinstance(perceived, dict):
        raise ValueError("post-wall coordinates")
    if "anchors" in perceived or any(key in perceived for key in POST_WALL_KEYS):
        raise ValueError("post-wall coordinates")
    for key in _NAME_KEYS:
        if isinstance(perceived.get(key), (list, tuple, dict)):
            raise ValueError("post-wall coordinates")
    hidden_ids = set()
    for item in perceived.get("hidden_targets") or []:
        if not isinstance(item, dict) or set(item) != _HIDDEN_KEYS:
            raise ValueError("post-wall coordinates")
        hidden_ids.add(item.get("id"))
    for item in perceived.get("visible_targets") or []:
        if not isinstance(item, dict) or not set(item) <= _VISIBLE_KEYS or "id" not in item:
            raise ValueError("post-wall coordinates")
    for item in perceived.get("teammates") or []:
        if not isinstance(item, dict) or not set(item) <= _TEAM_KEYS or "id" not in item:
            raise ValueError("post-wall coordinates")
        if isinstance(item.get("distance_m"), (list, tuple, dict)):
            raise ValueError("post-wall coordinates")
    if perceived.get("holder_id") in hidden_ids and ("holder_anchor" in perceived or "core_anchor" in perceived):
        raise ValueError("post-wall coordinates")
    reader_id = perceived.get("channel_reader_id")
    if reader_id in hidden_ids:
        raise ValueError("post-wall coordinates")
    hops = perceived.get("hops")
    if hops is not None:
        if not isinstance(hops, dict):
            raise ValueError("post-wall coordinates")
        for goal, hop in hops.items():
            if not isinstance(goal, str) or not isinstance(hop, dict):
                raise ValueError("post-wall coordinates")
            if set(hop) - {"dest", "distance_m"}:
                raise ValueError("post-wall coordinates")
            if not isinstance(hop.get("dest"), str):
                raise ValueError("post-wall coordinates")
            distance = hop.get("distance_m")
            if not isinstance(distance, (int, float)) or isinstance(distance, bool):
                raise ValueError("post-wall coordinates")


def _decide_thin(perceived: dict) -> Decision | None:
    if perceived.get("downed") or perceived.get("faction") is None or perceived.get("self_anchor") is None:
        return None
    if perceived.get("phase") not in ("live", "overtime"):
        return None
    if _should_interrupt(perceived):
        return Decision("interrupt_channel", "contest_channel", perceived["channel_reader_id"])
    if perceived.get("holding_core"):
        return _decide_holder(perceived)
    if perceived.get("core_pickable"):
        core_anchor = perceived.get("core_anchor")
        if core_anchor is not None and perceived.get("self_anchor") == core_anchor:
            return Decision("pick_core", "contest_core", "core")
        goal = core_anchor or perceived.get("core_home")
        if not goal:
            return None
        return Decision("request_move", "contest_core", "core", goal=goal)
    holder_faction = perceived.get("holder_faction")
    if holder_faction is not None and holder_faction == perceived.get("faction"):
        return None
    if perceived.get("interrupt_open") and perceived.get("role") == "assault" and holder_faction:
        terminal = perceived.get("holder_score_terminal")
        if terminal and perceived.get("self_anchor") != terminal:
            return Decision(
                "request_move",
                "interrupt_channel",
                perceived.get("holder_id") or terminal,
                goal=terminal,
            )
        return None
    return None


def _should_interrupt(perceived: dict) -> bool:
    if not perceived.get("channel_active") or not perceived.get("interrupt_open"):
        return False
    if perceived.get("role") != "assault":
        return False
    reader = perceived.get("channel_reader_id")
    if not reader:
        return False
    if perceived.get("channel_reader_faction") == perceived.get("faction"):
        return False
    return perceived.get("channel_reader_anchor") == perceived.get("self_anchor")


def _decide_holder(perceived: dict) -> Decision | None:
    terminal = perceived.get("score_terminal")
    if perceived.get("pass_open"):
        mates = []
        for mate in perceived.get("teammates") or []:
            if mate.get("downed"):
                continue
            distance = mate.get("distance_m")
            if isinstance(distance, (int, float)) and not isinstance(distance, bool):
                if distance <= perceived.get("pass_range_m", 0):
                    mates.append(mate)
        if mates:
            mates.sort(key=lambda item: item["id"])
            chosen = mates[0]
            return Decision(
                "pass_core",
                "close_range_pass",
                chosen["id"],
                distance_m=chosen["distance_m"],
            )
    if terminal and perceived.get("self_anchor") == terminal and not perceived.get("channel_active"):
        return Decision("begin_score", "score_path", terminal)
    if terminal and perceived.get("self_anchor") != terminal:
        return Decision("request_move", "score_path", terminal, goal=terminal)
    return None


def _distance(left, right) -> float:
    return math.hypot(left.pos[0] - right.pos[0], left.pos[1] - right.pos[1])
