"""Role-ability intents shared by the local bot and the thin resident.

The reason on the decision is the role id: `assault` (突进 / rush),
`support` (支援), `recon` (侦察 / scout). `scout` is not a second role id.

This stays dormant unless the match sets `role_abilities_enabled` and, for
the resident, the perceived dict carries `role_abilities`. The view has
anchor names and distances. It does not carry enemy coordinates.
"""

from __future__ import annotations

from .bot_policy import Decision
from .routes import shortest_path, step_edge

ALLEY_ANCHORS = frozenset({"alley_a", "alley_mid", "alley_b"})
COORD_KEYS = frozenset({"location", "pos", "x", "x_m", "y", "y_m"})


def next_hop(match, combatant, goal: str) -> dict | None:
    """The next anchor name and its length. Not a coordinate."""
    if not combatant.anchor or not goal:
        return None
    path = shortest_path(
        match.config,
        combatant.anchor,
        goal,
        combatant.preferred_route,
        match.bridge_state,
    )
    if not path:
        return None
    edge = step_edge(
        match.config,
        combatant.anchor,
        path[0],
        combatant.preferred_route,
        match.bridge_state,
    )
    if edge is None:
        return None
    return {"dest": path[0], "distance_m": float(edge.length_m)}


def view_for_bot(match, combatant, base: Decision | None) -> dict:
    """Coordinate-free ability view for one local bot."""
    spec = match.config.role_abilities[combatant.role]
    shield = None
    visible: list[str] = []
    hidden: list[str] = []
    for other in sorted(match.combatants.values(), key=lambda item: item.id):
        if other.id == combatant.id or other.downed:
            continue
        if other.faction == combatant.faction:
            if shield is None and other.anchor == combatant.anchor:
                shield = other.id
            continue
        if match.anchor_visible(combatant.anchor, other.anchor):
            visible.append(other.id)
        else:
            hidden.append(other.id)
    hop_dest = None
    hop_m = None
    if base is not None and base.action == "request_move" and base.goal:
        hop = next_hop(match, combatant, base.goal)
        if hop is not None:
            hop_dest = hop["dest"]
            hop_m = hop["distance_m"]
    progress = getattr(match, "ability_progress", None) or {}
    return {
        "ability_id": spec["id"],
        "ability_progress": progress.get(combatant.id, ""),
        "ability_range_m": float(spec["range_m"]),
        "ability_ready": match.t_ms >= combatant.ability_ready_ms,
        "base_action": None if base is None else base.action,
        "holding_core": match.core.holder_id == combatant.id,
        "in_alley": combatant.anchor in ALLEY_ANCHORS,
        "mark_hidden": hidden[0] if hidden else None,
        "mark_visible": visible[0] if visible else None,
        "next_hop": hop_dest,
        "next_hop_m": hop_m,
        "role": combatant.role,
        "role_abilities": True,
        "self_anchor": combatant.anchor,
        "shield_target": shield,
    }


def view_from_resident(perceived: dict, base: Decision | None) -> dict:
    """Same shape as the bot view, read only from perception."""
    hop_dest = None
    hop_m = None
    if base is not None and base.goal:
        hop = (perceived.get("hops") or {}).get(base.goal)
        if isinstance(hop, dict):
            hop_dest = hop.get("dest")
            hop_m = hop.get("distance_m")
    shield = None
    mates = [item for item in perceived.get("teammates") or [] if isinstance(item, dict)]
    mates.sort(key=lambda item: item.get("id") or "")
    for mate in mates:
        if mate.get("downed"):
            continue
        distance = mate.get("distance_m")
        if isinstance(distance, (int, float)) and not isinstance(distance, bool) and distance == 0:
            shield = mate.get("id")
            break
    visible = sorted(
        item.get("id")
        for item in perceived.get("visible_targets") or []
        if isinstance(item, dict) and item.get("id")
    )
    hidden = sorted(
        item.get("id")
        for item in perceived.get("hidden_targets") or []
        if isinstance(item, dict) and item.get("id")
    )
    return {
        "ability_id": perceived.get("ability_id"),
        "ability_progress": perceived.get("ability_progress") or "",
        "ability_range_m": perceived.get("ability_range_m"),
        "ability_ready": bool(perceived.get("ability_ready")),
        "base_action": None if base is None else base.action,
        "holding_core": bool(perceived.get("holding_core")),
        "in_alley": bool(perceived.get("in_alley")),
        "mark_hidden": hidden[0] if hidden else None,
        "mark_visible": visible[0] if visible else None,
        "next_hop": hop_dest,
        "next_hop_m": hop_m,
        "role": perceived.get("role"),
        "role_abilities": True,
        "self_anchor": perceived.get("self_anchor"),
        "shield_target": shield,
    }


def choose_role_ability(view: dict, base: Decision | None) -> Decision | None:
    """Return a role ability, or the contest decision already chosen."""
    if not view.get("role_abilities"):
        return base
    role = view.get("role")
    progress = view.get("ability_progress") or ""
    ready = bool(view.get("ability_ready"))
    ability = view.get("ability_id")
    limit = view.get("ability_range_m")
    limit_m = float(limit) if isinstance(limit, (int, float)) and not isinstance(limit, bool) else 0.0

    if role == "assault" and ability == "dash" and not view.get("holding_core"):
        hop = view.get("next_hop")
        distance = view.get("next_hop_m")
        measured = isinstance(distance, (int, float)) and not isinstance(distance, bool)
        if progress == "" and view.get("base_action") == "request_move" and hop and measured and distance > limit_m:
            return Decision(
                "use_ability",
                "assault",
                hop,
                distance_m=float(distance),
                ability="dash",
                progress="ranged",
            )
        if (
            progress == "ranged"
            and ready
            and view.get("base_action") == "request_move"
            and hop
            and measured
            and distance <= limit_m
        ):
            return Decision(
                "use_ability",
                "assault",
                hop,
                distance_m=float(distance),
                ability="dash",
                progress="dashed",
            )
        if progress == "dashed" and not ready:
            dest = view.get("self_anchor") or hop or "cooldown"
            return Decision("use_ability", "assault", dest, ability="dash", progress="cooled")

    if role == "support" and ability == "shield":
        target = view.get("shield_target")
        if progress == "" and view.get("base_action") is None and target and ready:
            return Decision(
                "use_ability",
                "support",
                target,
                distance_m=0.0,
                ability="shield",
                progress="shielded",
            )

    if role == "recon" and ability == "mark":
        if (
            progress == ""
            and view.get("in_alley")
            and view.get("mark_hidden")
            and view.get("base_action") == "request_move"
        ):
            return Decision(
                "use_ability",
                "recon",
                view["mark_hidden"],
                ability="mark",
                progress="hidden",
            )
        if progress == "hidden" and ready and view.get("base_action") is None and view.get("mark_visible"):
            return Decision(
                "use_ability",
                "recon",
                view["mark_visible"],
                ability="mark",
                progress="marked",
            )

    return base


def attach_resident_ability(match, combatant, view: dict) -> None:
    """Add the ability offer to a perceived dict. No enemy coordinates."""
    if not getattr(match, "role_abilities_enabled", False):
        return
    if combatant.role not in match.config.role_abilities:
        return
    spec = match.config.role_abilities[combatant.role]
    progress = getattr(match, "ability_progress", None) or {}
    view["ability_id"] = spec["id"]
    view["ability_progress"] = progress.get(combatant.id, "")
    view["ability_range_m"] = float(spec["range_m"])
    view["ability_ready"] = match.t_ms >= combatant.ability_ready_ms
    view["in_alley"] = combatant.anchor in ALLEY_ANCHORS
    view["role_abilities"] = True
    hops: dict[str, dict] = {}
    for key in ("core_anchor", "core_home", "holder_score_terminal", "score_terminal"):
        goal = view.get(key)
        if not isinstance(goal, str):
            continue
        hop = next_hop(match, combatant, goal)
        if hop is not None:
            hops[goal] = hop
    if hops:
        view["hops"] = hops
