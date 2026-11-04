"""Authoritative Steel Tide match. One core, server-resolved intents, no second scorer."""

from __future__ import annotations

import math

from .config import SteelTideConfig, load_config
from .model import Channel, Combatant, Command, Core, Event, audit_holder_log
from .routes import shortest_path, step_edge


PICK_PRIORITY = 40
SERVER_CLIENT = "server"


class SteelTideMatch:
    def __init__(self, config: SteelTideConfig | None = None):
        self.config = config or load_config()
        self.t_ms = 0
        self.phase = "lobby"
        self.lobby_open = True
        self.combatants: dict[str, Combatant] = {}
        self.events: list[Event] = []
        self.score = {"A": 0, "B": 0}
        self.bridge_state = "disconnected"
        self.channel: Channel | None = None
        self.inbox: list[Command] = []
        self._seq = 0
        self._client_of: dict[str, str] = {}
        center = self.config.anchors["center"]
        self.core = Core(anchor="center", pos=center, status="spawn", holder_id=None, since_ms=0)
        self.match_deadline_ms: int | None = None
        self.ot_deadline_ms: int | None = None
        self.bridge_warning_ms: int | None = None
        self.bridge_connect_ms: int | None = None
        self.bridge_connected_ms: int | None = None
        self.disconnect_at_ms: int | None = None
        self.settled_kind: str | None = None

    @property
    def t_seconds(self) -> float:
        return self.t_ms / 1000

    def _emit(self, name: str, payload: dict | None = None) -> None:
        self.events.append(Event(self.t_ms, name, payload or {}))

    def add_combatant(
        self,
        combatant_id: str,
        client_id: str,
        body: str,
        controller: str,
        face_variant: str | None = None,
        preferred_route: str = "repair_alley",
    ) -> None:
        if self.phase != "lobby":
            raise RuntimeError("roster is locked")
        if body not in self.config.faction_rule:
            raise ValueError(f"unknown body {body}")
        if controller not in ("human", "digital_resident", "local_bot"):
            raise ValueError(f"unknown controller {controller}")
        if combatant_id in self.combatants:
            raise ValueError(f"duplicate combatant {combatant_id}")
        self.combatants[combatant_id] = Combatant(
            id=combatant_id,
            client_id=client_id,
            body=body,
            controller=controller,
            face_variant=face_variant,
            preferred_route=preferred_route,
        )
        self._client_of[combatant_id] = client_id
        self._emit(
            "CombatantJoined",
            {
                "combatant_id": combatant_id,
                "client_id": client_id,
                "body": body,
                "controller": controller,
            },
        )

    def choose_faction(self, combatant_id: str, faction: str) -> None:
        combatant = self.combatants[combatant_id]
        if not self.lobby_open:
            self._emit("FactionRejected", {"combatant_id": combatant_id, "reason": "locked"})
            return
        allowed = self.config.faction_rule[combatant.body]
        if faction not in allowed:
            self._emit(
                "FactionRejected",
                {"combatant_id": combatant_id, "reason": "illegal_faction", "faction": faction, "body": combatant.body},
            )
            return
        combatant.faction = faction
        self._emit("FactionChosen", {"combatant_id": combatant_id, "faction": faction, "body": combatant.body})

    def choose_role(self, combatant_id: str, role: str) -> None:
        if not self.lobby_open:
            self._emit("RoleRejected", {"combatant_id": combatant_id, "reason": "locked"})
            return
        if role not in self.config.roles:
            self._emit("RoleRejected", {"combatant_id": combatant_id, "reason": "unknown_role", "role": role})
            return
        self.combatants[combatant_id].role = role
        self._emit("RoleChosen", {"combatant_id": combatant_id, "role": role})

    def start(self) -> None:
        if self.phase != "lobby":
            raise RuntimeError("match already started")
        missing = [c.id for c in self.combatants.values() if c.faction is None or c.role is None]
        if missing:
            raise RuntimeError(f"unchosen roster: {', '.join(missing)}")
        sides = {c.faction for c in self.combatants.values()}
        if sides != {"A", "B"}:
            raise RuntimeError(f"both factions are required, have {sorted(sides)}")
        self.lobby_open = False
        self.phase = "live"
        self.match_deadline_ms = self.t_ms + self.config.match_ms
        for combatant in self.combatants.values():
            self._place_at_spawn(combatant, protect=True)
        self._emit("FactionsLocked", {"assignments": {c.id: c.faction for c in self.combatants.values()}})
        self._emit("RolesLocked", {"assignments": {c.id: c.role for c in self.combatants.values()}})
        self._emit(
            "MatchStarted",
            {
                "deadline_ms": self.match_deadline_ms,
                "role_select_open": False,
                "points_to_win": self.config.points_to_win,
            },
        )

    def enqueue(self, client_id: str, kind: str, t_seconds: float, **payload) -> None:
        t_ms = self.config.seconds_to_ms(t_seconds)
        if t_ms < self.t_ms:
            raise RuntimeError("command is in the past")
        self._seq += 1
        self.inbox.append(Command(t_ms, client_id, self._seq, kind, payload))

    def advance_to(self, t_seconds: float) -> None:
        self.advance_to_ms(self.config.seconds_to_ms(t_seconds))

    def advance_to_ms(self, target_ms: int) -> None:
        if target_ms < self.t_ms:
            raise RuntimeError("time goes backwards")
        steps = 0
        while self.phase != "settled":
            steps += 1
            if steps > 100000:
                raise RuntimeError("match clock did not advance")
            pending = [cmd.t_ms for cmd in self.inbox if not cmd.applied and cmd.t_ms <= target_ms]
            timers = [when for when in self._timer_times() if self.t_ms <= when <= target_ms]
            if not pending and not timers:
                self.t_ms = target_ms
                break
            nxt = min(pending + timers)
            self.t_ms = nxt
            self._apply_commands(nxt)
            self._apply_timers(nxt)
            if self.t_ms >= target_ms and not any(not cmd.applied and cmd.t_ms <= target_ms for cmd in self.inbox):
                if not any(self.t_ms <= when <= target_ms for when in self._timer_times()):
                    break

    def peek_next_ms(self, horizon_ms: int) -> int:
        pending = [cmd.t_ms for cmd in self.inbox if not cmd.applied and cmd.t_ms <= horizon_ms]
        timers = [when for when in self._timer_times() if self.t_ms <= when <= horizon_ms]
        if not pending and not timers:
            return horizon_ms
        return min(pending + timers)

    def has_pending(self, combatant_id: str, kind: str) -> bool:
        return any(
            not cmd.applied and cmd.kind == kind and cmd.payload.get("combatant_id") == combatant_id
            for cmd in self.inbox
        )

    def place_for_test(
        self,
        combatant_id: str,
        anchor: str,
        pos: tuple[float, float] | None = None,
    ) -> None:
        """Harness placement. Not a client intent and not a UE event."""
        combatant = self.combatants[combatant_id]
        combatant.anchor = anchor
        combatant.pos = self.config.anchors[anchor] if pos is None else pos
        combatant.anchor_since_ms = self.t_ms
        if self.core.holder_id == combatant_id:
            self.core.anchor = anchor
            self.core.pos = combatant.pos

    def schedule_bridge_connect(self, connect_at_seconds: float) -> None:
        connect_ms = self.config.seconds_to_ms(connect_at_seconds)
        self.bridge_connect_ms = connect_ms
        warning = connect_ms - self.config.bridge_warning_ms
        self.bridge_warning_ms = max(warning, self.t_ms)

    def schedule_bridge_disconnect(self, at_seconds: float) -> None:
        self.disconnect_at_ms = self.config.seconds_to_ms(at_seconds)

    def holder_errors(self) -> list[str]:
        return audit_holder_log(self.events, self.core.holder_id)

    def named(self, name: str) -> list[Event]:
        return [event for event in self.events if event.name == name]

    def _timer_times(self) -> list[int]:
        times: list[int] = []
        if self.channel is not None:
            times.append(self.channel.ends_ms)
        if self.core.status in ("stuck", "overboard"):
            times.append(self.core.since_ms + self.config.core_reset_timeout_ms)
        for combatant in self.combatants.values():
            if combatant.downed and combatant.respawn_ms is not None:
                times.append(combatant.respawn_ms)
        if self.bridge_warning_ms is not None:
            times.append(self.bridge_warning_ms)
        if self.bridge_connect_ms is not None:
            times.append(self.bridge_connect_ms)
        if self.disconnect_at_ms is not None:
            times.append(self.disconnect_at_ms)
        if self.phase == "live" and self.match_deadline_ms is not None:
            times.append(self.match_deadline_ms)
        if self.phase == "overtime" and self.ot_deadline_ms is not None:
            times.append(self.ot_deadline_ms)
        return times

    def _apply_commands(self, t_ms: int) -> None:
        due = [cmd for cmd in self.inbox if not cmd.applied and cmd.t_ms == t_ms]
        due.sort(key=lambda cmd: (self._kind_priority(cmd.kind), cmd.client_id, cmd.seq))
        picks = [cmd for cmd in due if cmd.kind == "pick_core"]
        for cmd in due:
            if cmd.kind == "pick_core":
                continue
            cmd.applied = True
            self._apply_one(cmd)
        if picks:
            for cmd in picks:
                cmd.applied = True
            self._resolve_pick_batch(picks)

    def _kind_priority(self, kind: str) -> int:
        order = {
            "request_move": 10,
            "use_ability": 15,
            "hit": 20,
            "leave_terminal": 20,
            "drop_core": 20,
            "pass_core": 30,
            "mark_core_overboard": 35,
            "mark_core_stuck": 35,
            "pick_core": PICK_PRIORITY,
            "begin_score": 50,
            "set_route": 60,
        }
        return order.get(kind, 100)

    def _apply_one(self, cmd: Command) -> None:
        kind = cmd.kind
        if kind == "request_move":
            self._request_move(cmd)
        elif kind == "hit":
            self._hit(cmd)
        elif kind == "leave_terminal":
            self._leave_terminal(cmd)
        elif kind == "drop_core":
            self._drop(cmd.payload["combatant_id"], "voluntary", cmd.client_id)
        elif kind == "pass_core":
            self._pass(cmd)
        elif kind == "mark_core_overboard":
            self._mark_core_command(cmd, "overboard")
        elif kind == "mark_core_stuck":
            self._mark_core_command(cmd, "stuck")
        elif kind == "begin_score":
            self._begin_score(cmd)
        elif kind == "set_route":
            self._set_route(cmd)
        elif kind == "use_ability":
            self._use_ability(cmd)
        else:
            raise ValueError(f"unknown command {kind}")

    def _owns(self, cmd: Command, combatant_id: str) -> bool:
        return self._client_of.get(combatant_id) == cmd.client_id

    def _request_move(self, cmd: Command) -> None:
        combatant_id = cmd.payload["combatant_id"]
        if not self._owns(cmd, combatant_id):
            self._emit("MoveRejected", {"combatant_id": combatant_id, "reason": "wrong_client"})
            return
        combatant = self.combatants[combatant_id]
        dest = cmd.payload["dest"]
        route = cmd.payload["route"]
        if combatant.downed:
            self._emit("MoveRejected", {"combatant_id": combatant_id, "reason": "downed"})
            return
        edge = step_edge(self.config, combatant.anchor or "", dest, route, self.bridge_state)
        if edge is None:
            reason = "bridge_blocked" if self._bridge_blocks(combatant.anchor or "", dest) else "no_edge"
            self._emit("MoveRejected", {"combatant_id": combatant_id, "reason": reason, "dest": dest})
            return
        travel_ms = self._travel_ms(edge.length_m, combatant_id)
        ready_at = combatant.anchor_since_ms
        if edge.bridge:
            ready_at = max(ready_at, self.bridge_connected_ms or 0)
        if cmd.t_ms < ready_at + travel_ms:
            self._emit("MoveRejected", {"combatant_id": combatant_id, "reason": "too_soon", "dest": dest})
            return
        origin = combatant.anchor
        combatant.anchor = dest
        combatant.pos = self.config.anchors[dest]
        combatant.anchor_since_ms = cmd.t_ms
        if self.core.holder_id == combatant_id:
            self.core.anchor = dest
            self.core.pos = combatant.pos
        self._emit(
            "MoveCompleted",
            {"combatant_id": combatant_id, "from": origin, "to": dest, "route": route, "travel_ms": travel_ms},
        )

    def _bridge_blocks(self, start: str, dest: str) -> bool:
        for edge in self.config.edges:
            if {edge.a, edge.b} == {start, dest} and edge.bridge and self.bridge_state != "connected":
                return True
        return False

    def _speed(self, combatant_id: str) -> float:
        if self.core.holder_id == combatant_id and not self.config.carrier_can_sprint:
            return self.config.walk_speed_mps
        return self.config.sprint_speed_mps

    def _travel_ms(self, length_m: float, combatant_id: str) -> int:
        return int(round(length_m / self._speed(combatant_id) * 1000))

    def _hit(self, cmd: Command) -> None:
        if not self._server_only(cmd, "HitRejected"):
            return
        target_id = cmd.payload["target_id"]
        target = self.combatants[target_id]
        if self.t_ms < target.protection_until_ms:
            self._emit("HitIgnored", {"target_id": target_id, "reason": "spawn_protection"})
            return
        if target.shield_charges > 0:
            target.shield_charges -= 1
            self._emit("HitIgnored", {"target_id": target_id, "reason": "shield"})
            return
        if self.channel and self.channel.combatant_id == target_id:
            self._interrupt(target_id, "hit")
        if cmd.payload.get("down", True) and not target.downed:
            if self.core.holder_id == target_id:
                self._release_core(target_id, "downed")
            target.downed = True
            target.respawn_ms = self.t_ms + self.config.down_ms
            self._emit("ActorDowned", {"combatant_id": target_id, "respawn_ms": target.respawn_ms})

    def _leave_terminal(self, cmd: Command) -> None:
        if not self._server_only(cmd, "ScoreChannelRejected"):
            return
        combatant_id = cmd.payload["combatant_id"]
        if self.channel and self.channel.combatant_id == combatant_id:
            self._interrupt(combatant_id, "left_terminal")

    def _drop(self, combatant_id: str, reason: str, client_id: str | None) -> None:
        if client_id is not None and self._client_of.get(combatant_id) != client_id:
            self._emit("CoreDropRejected", {"combatant_id": combatant_id, "reason": "wrong_client"})
            return
        if self.core.holder_id != combatant_id:
            self._emit("CoreDropRejected", {"combatant_id": combatant_id, "reason": "not_holder"})
            return
        if self.channel and self.channel.combatant_id == combatant_id:
            self._interrupt(combatant_id, "dropped")
        self._release_core(combatant_id, reason)

    def _release_core(self, combatant_id: str, reason: str) -> None:
        if self.core.holder_id != combatant_id:
            return
        self.core.holder_id = None
        self.core.status = "ground"
        self.core.since_ms = self.t_ms
        self._emit(
            "CoreDropped",
            {
                "combatant_id": combatant_id,
                "reason": reason,
                "anchor": self.core.anchor,
                "status": "ground",
            },
        )

    def _pass(self, cmd: Command) -> None:
        from_id = cmd.payload["from_id"]
        to_id = cmd.payload["to_id"]
        if not self._owns(cmd, from_id):
            self._emit("CorePassRejected", {"from_id": from_id, "to_id": to_id, "reason": "wrong_client"})
            return
        if self.core.holder_id != from_id:
            self._emit("CorePassRejected", {"from_id": from_id, "to_id": to_id, "reason": "not_holder"})
            return
        target = self.combatants[to_id]
        passer = self.combatants[from_id]
        if target.faction != passer.faction:
            self._emit("CorePassRejected", {"from_id": from_id, "to_id": to_id, "reason": "wrong_faction"})
            return
        if target.downed or passer.downed:
            self._emit("CorePassRejected", {"from_id": from_id, "to_id": to_id, "reason": "downed"})
            return
        if math.hypot(passer.pos[0] - target.pos[0], passer.pos[1] - target.pos[1]) > self.config.pass_range_m:
            self._emit("CorePassRejected", {"from_id": from_id, "to_id": to_id, "reason": "out_of_range"})
            return
        if self.channel and self.channel.combatant_id == from_id:
            self._interrupt(from_id, "passed")
        self.core.holder_id = to_id
        self.core.status = "held"
        self.core.anchor = target.anchor or self.core.anchor
        self.core.pos = target.pos
        self.core.since_ms = self.t_ms
        self._emit("CorePassed", {"from_id": from_id, "to_id": to_id})

    def _server_only(self, cmd: Command, event_name: str) -> bool:
        if cmd.client_id == SERVER_CLIENT:
            return True
        self._emit(event_name, {"reason": "server_only", "client_id": cmd.client_id})
        return False

    def _mark_core_command(self, cmd: Command, status: str) -> None:
        if not self._server_only(cmd, "CoreMarkRejected"):
            return
        self._mark_core(status)

    def _mark_core(self, status: str) -> None:
        holder = self.core.holder_id
        if self.channel is not None:
            self._interrupt(self.channel.combatant_id, status)
        if holder is not None:
            self.core.holder_id = None
            self._emit("CoreDropped", {"combatant_id": holder, "reason": status, "anchor": status, "status": status})
        anchor = "sea" if status == "overboard" else "stuck"
        self.core.holder_id = None
        self.core.status = status
        self.core.anchor = anchor
        self.core.pos = self.config.anchors[anchor]
        self.core.since_ms = self.t_ms
        self._emit("CoreMarkedUnpickable", {"status": status, "anchor": anchor})

    def _begin_score(self, cmd: Command) -> None:
        combatant_id = cmd.payload["combatant_id"]
        if not self._owns(cmd, combatant_id):
            self._emit("ScoreChannelRejected", {"combatant_id": combatant_id, "reason": "wrong_client"})
            return
        combatant = self.combatants[combatant_id]
        terminal = self.config.score_terminal[combatant.faction or ""]
        if self.core.holder_id != combatant_id:
            self._emit("ScoreChannelRejected", {"combatant_id": combatant_id, "reason": "not_holder"})
            return
        if combatant.downed or combatant.anchor != terminal:
            self._emit("ScoreChannelRejected", {"combatant_id": combatant_id, "reason": "not_at_terminal"})
            return
        if self.channel and self.channel.combatant_id == combatant_id:
            return
        self.channel = Channel(
            combatant_id=combatant_id,
            terminal=terminal,
            started_ms=self.t_ms,
            ends_ms=self.t_ms + self.config.score_channel_ms,
        )
        self._emit(
            "ScoreChannelStarted",
            {"combatant_id": combatant_id, "terminal": terminal, "ends_ms": self.channel.ends_ms},
        )

    def _use_ability(self, cmd: Command) -> None:
        combatant_id = cmd.payload["combatant_id"]
        if not self._owns(cmd, combatant_id):
            self._emit("AbilityRejected", {"combatant_id": combatant_id, "reason": "wrong_client"})
            return
        combatant = self.combatants[combatant_id]
        if self.phase not in ("live", "overtime"):
            self._emit("AbilityRejected", {"combatant_id": combatant_id, "reason": "not_live"})
            return
        if combatant.downed or combatant.role is None:
            self._emit("AbilityRejected", {"combatant_id": combatant_id, "reason": "downed"})
            return
        spec = self.config.role_abilities[combatant.role]
        requested = cmd.payload.get("ability")
        if requested != spec["id"]:
            self._emit(
                "AbilityRejected",
                {"combatant_id": combatant_id, "reason": "wrong_role", "ability": requested, "role": combatant.role},
            )
            return
        if self.t_ms < combatant.ability_ready_ms:
            self._emit(
                "AbilityRejected",
                {"combatant_id": combatant_id, "reason": "cooldown", "ready_ms": combatant.ability_ready_ms},
            )
            return
        reason = self._apply_ability(combatant, spec, cmd)
        if reason is not None:
            payload = {"combatant_id": combatant_id, "reason": reason, "ability": spec["id"]}
            self._emit("AbilityRejected", payload)
            return
        combatant.ability_ready_ms = self.t_ms + self.config.seconds_to_ms(spec["cooldown_seconds"])
        self._emit(
            "AbilityUsed",
            {
                "combatant_id": combatant_id,
                "ability": spec["id"],
                "role": combatant.role,
                "faction": combatant.faction,
                "ready_ms": combatant.ability_ready_ms,
                "target_id": cmd.payload.get("target_id"),
            },
        )

    def _apply_ability(self, combatant: Combatant, spec: dict, cmd: Command) -> str | None:
        ability = spec["id"]
        if ability == "dash":
            return self._dash(combatant, cmd.payload.get("dest"), float(spec["range_m"]))
        if ability == "shield":
            combatant.shield_charges = 1
            return None
        if ability == "mark":
            return self._mark(combatant, cmd.payload.get("target_id"))
        return "unknown_ability"

    def _dash(self, combatant: Combatant, dest: str | None, max_range_m: float) -> str | None:
        if not dest or not combatant.anchor:
            return "no_edge"
        edge = step_edge(self.config, combatant.anchor, dest, combatant.preferred_route, self.bridge_state)
        if edge is None:
            if self._bridge_blocks(combatant.anchor, dest):
                return "bridge_blocked"
            return "no_edge"
        if edge.length_m > max_range_m:
            return "out_of_range"
        combatant.anchor = dest
        combatant.pos = self.config.anchors[dest]
        combatant.anchor_since_ms = self.t_ms
        if self.core.holder_id == combatant.id:
            self.core.anchor = dest
            self.core.pos = combatant.pos
        return None

    def _mark(self, combatant: Combatant, target_id: str | None) -> str | None:
        target = self.combatants.get(target_id or "")
        if target is None:
            return "no_target"
        if not self._target_visible(combatant, target):
            return "not_visible"
        return None

    def _target_visible(self, observer: Combatant, target: Combatant) -> bool:
        if observer.anchor is not None and observer.anchor == target.anchor:
            return True
        alley = {"alley_a", "alley_mid", "alley_b"}
        if observer.anchor in alley or target.anchor in alley:
            return False
        return observer.anchor is not None and target.anchor is not None

    def _set_route(self, cmd: Command) -> None:
        combatant_id = cmd.payload["combatant_id"]
        route = cmd.payload["route"]
        if route not in ("elevated", "repair_alley"):
            self._emit("RouteRejected", {"combatant_id": combatant_id, "reason": "unknown_route"})
            return
        self.combatants[combatant_id].preferred_route = route
        self._emit("RouteSelected", {"combatant_id": combatant_id, "route": route})

    def _resolve_pick_batch(self, picks: list[Command]) -> None:
        ordered = sorted(picks, key=lambda cmd: (cmd.client_id, cmd.payload["combatant_id"], cmd.seq))
        eligible: list[Command] = []
        for cmd in ordered:
            reason = self._pick_block(cmd)
            if reason is None:
                eligible.append(cmd)
            else:
                self._emit(
                    "CorePickRejected",
                    {
                        "combatant_id": cmd.payload["combatant_id"],
                        "client_id": cmd.client_id,
                        "reason": reason,
                    },
                )
        if not eligible:
            return
        winner = eligible[0]
        self._grant_pick(winner)
        for cmd in eligible[1:]:
            self._emit(
                "CorePickRejected",
                {
                    "combatant_id": cmd.payload["combatant_id"],
                    "client_id": cmd.client_id,
                    "reason": "already_held",
                },
            )

    def _pick_block(self, cmd: Command) -> str | None:
        combatant_id = cmd.payload["combatant_id"]
        if not self._owns(cmd, combatant_id):
            return "wrong_client"
        if self.phase not in ("live", "overtime"):
            return "not_live"
        combatant = self.combatants[combatant_id]
        if combatant.downed:
            return "downed"
        if not self.core.pickable:
            return "already_held" if self.core.holder_id else "not_pickable"
        if combatant.anchor != self.core.anchor:
            return "not_at_core"
        distance = math.hypot(combatant.pos[0] - self.core.pos[0], combatant.pos[1] - self.core.pos[1])
        if distance > self.config.pickup_radius_m:
            return "not_at_core"
        return None

    def _grant_pick(self, cmd: Command) -> None:
        if self.core.holder_id is not None or self.core.status == "held":
            raise RuntimeError("double hold")
        combatant_id = cmd.payload["combatant_id"]
        self.core.holder_id = combatant_id
        self.core.status = "held"
        self.core.since_ms = self.t_ms
        self._emit(
            "CorePicked",
            {
                "combatant_id": combatant_id,
                "client_id": cmd.client_id,
                "anchor": self.core.anchor,
            },
        )

    def _interrupt(self, combatant_id: str, reason: str) -> None:
        if self.channel is None or self.channel.combatant_id != combatant_id:
            return
        elapsed = self.t_ms - self.channel.started_ms
        self.channel = None
        self._emit("ScoreChannelInterrupted", {"combatant_id": combatant_id, "reason": reason, "elapsed_ms": elapsed})

    def _apply_timers(self, t_ms: int) -> None:
        if self.bridge_warning_ms is not None and t_ms >= self.bridge_warning_ms:
            self.bridge_warning_ms = None
            if self.bridge_state != "connected":
                self.bridge_state = "warning"
            self._emit(
                "BridgeWarningStarted",
                {
                    "lead_ms": self.config.bridge_warning_ms,
                    "cues": ["water_reflection", "span_light_strip", "alarm"],
                    "readable_without_reflection": True,
                },
            )
        if self.bridge_connect_ms is not None and t_ms >= self.bridge_connect_ms:
            self.bridge_connect_ms = None
            self.bridge_state = "connected"
            self.bridge_connected_ms = t_ms
            self._emit("BridgeStateChanged", {"state": "connected"})
        if self.disconnect_at_ms is not None and t_ms >= self.disconnect_at_ms:
            self.disconnect_at_ms = None
            self._disconnect_bridge()
        for combatant in list(self.combatants.values()):
            if combatant.downed and combatant.respawn_ms is not None and t_ms >= combatant.respawn_ms:
                combatant.respawn_ms = None
                combatant.downed = False
                self._place_at_spawn(combatant, protect=True)
                self._emit("ActorRespawned", {"combatant_id": combatant.id, "anchor": combatant.anchor})
        if self.core.status in ("stuck", "overboard") and t_ms >= self.core.since_ms + self.config.core_reset_timeout_ms:
            reason = self.core.status
            self.core.holder_id = None
            self.core.status = "spawn"
            self.core.anchor = "center"
            self.core.pos = self.config.anchors["center"]
            self.core.since_ms = t_ms
            self._emit("CoreReset", {"reason": reason, "anchor": "center"})
        if self.channel is not None and t_ms >= self.channel.ends_ms:
            self._complete_score()
        self._expire_clock()

    def _disconnect_bridge(self) -> None:
        self.bridge_state = "disconnected"
        for combatant in list(self.combatants.values()):
            if combatant.anchor != "center":
                continue
            dest = "bridgehead_a" if combatant.faction == "A" else "bridgehead_b"
            combatant.anchor = dest
            combatant.pos = self.config.anchors[dest]
            combatant.anchor_since_ms = self.t_ms
            if self.core.holder_id == combatant.id:
                self.core.anchor = dest
                self.core.pos = combatant.pos
            if self.channel and self.channel.combatant_id == combatant.id:
                self._interrupt(combatant.id, "bridge_nudge")
            self._emit(
                "BridgeOccupantNudged",
                {"combatant_id": combatant.id, "to": dest, "reason": "span_not_embedded"},
            )
        self._emit("BridgeStateChanged", {"state": "disconnected"})

    def _complete_score(self) -> None:
        if self.channel is None:
            return
        combatant = self.combatants[self.channel.combatant_id]
        faction = combatant.faction or ""
        self.channel = None
        self.score[faction] += 1
        self.core.holder_id = None
        self.core.status = "spawn"
        self.core.anchor = "center"
        self.core.pos = self.config.anchors["center"]
        self.core.since_ms = self.t_ms
        self._emit(
            "PointScored",
            {
                "faction": faction,
                "combatant_id": combatant.id,
                "points": self.score[faction],
                "score": dict(self.score),
            },
        )
        self._emit("CoreReturnedToCenter", {"anchor": "center", "scoring_faction": faction})
        if self.score[faction] >= self.config.points_to_win and self.phase != "settled":
            self._settle("points")

    def _expire_clock(self) -> None:
        if self.phase == "live" and self.match_deadline_ms is not None and self.t_ms >= self.match_deadline_ms:
            self.match_deadline_ms = None
            self._emit("MatchClockExpired", {"score": dict(self.score), "role_select_open": False})
            if self.score["A"] != self.score["B"]:
                self._settle("score")
            else:
                self.phase = "overtime"
                self.ot_deadline_ms = self.t_ms + self.config.overtime_ms
                self._emit(
                    "OvertimeStarted",
                    {"deadline_ms": self.ot_deadline_ms, "role_select_open": False},
                )
        if self.phase == "overtime" and self.ot_deadline_ms is not None and self.t_ms >= self.ot_deadline_ms:
            self.ot_deadline_ms = None
            if self.score["A"] != self.score["B"]:
                self._settle("score")
            else:
                self._settle("draw")

    def _settle(self, kind: str) -> None:
        if self.phase == "settled":
            return
        self.lobby_open = False
        if self.score["A"] > self.score["B"]:
            winner: str | None = "A"
        elif self.score["B"] > self.score["A"]:
            winner = "B"
        else:
            winner = None
        self.phase = "settled"
        self.settled_kind = kind
        self.channel = None
        self._emit(
            "MatchSettled",
            {
                "kind": kind,
                "winner": winner,
                "score": dict(self.score),
                "role_select_open": False,
            },
        )

    def _place_at_spawn(self, combatant: Combatant, protect: bool) -> None:
        anchor = "spawn_a" if combatant.faction == "A" else "spawn_b"
        combatant.anchor = anchor
        combatant.pos = self.config.anchors[anchor]
        combatant.anchor_since_ms = self.t_ms
        if protect:
            combatant.protection_until_ms = self.t_ms + self.config.spawn_protection_ms


def path_between(match: SteelTideMatch, start: str, goal: str, preferred: str) -> list[str] | None:
    return shortest_path(match.config, start, goal, preferred, match.bridge_state)
