"""Two Steel Tide routes. The repair alley never depends on the bridge span.

The authoritative route graph is every configured edge, minus the elevated
span while the bridge is open (disconnected). Preference filters that graph.
It does not put the span back, and it does not delete the alley.
"""

from __future__ import annotations

import heapq

from .config import Edge, SteelTideConfig

# Deck edges that are not the moving span. Shared spawn links stay on both preferences.
_DECK_ROUTES = frozenset({"elevated", "shared"})


def edge_allowed(edge: Edge, preferred: str, bridge_state: str) -> bool:
    if edge.bridge and bridge_state != "connected":
        return False
    if preferred == "repair_alley" and edge.route == "elevated":
        return False
    if preferred == "elevated" and edge.route == "alley":
        return False
    return True


def authoritative_edges(config: SteelTideConfig, bridge_state: str) -> tuple[Edge, ...]:
    """Walkable edges. Span edges exist only while the bridge is connected."""
    if bridge_state == "connected":
        return tuple(config.edges)
    return tuple(edge for edge in config.edges if not edge.bridge)


def span_pairs(config: SteelTideConfig) -> tuple[tuple[str, str], ...]:
    pairs = []
    for edge in config.edges:
        if edge.bridge:
            pairs.append(tuple(sorted((edge.a, edge.b))))
    return tuple(sorted(pairs))


def span_edge_token(config: SteelTideConfig, bridge_state: str) -> str:
    """Span edges currently in the route graph. Empty while the span is open."""
    if bridge_state != "connected":
        return ""
    return ",".join(f"{left}-{right}" for left, right in span_pairs(config))


def is_span_edge(config: SteelTideConfig, start: str, dest: str) -> bool:
    ends = {start, dest}
    return any(edge.bridge and {edge.a, edge.b} == ends for edge in config.edges)


def bridgeheads(config: SteelTideConfig) -> tuple[str, ...]:
    """Safe decks at the ends of the span. `center` is on the span, not a refuge."""
    found: list[str] = []
    for edge in config.edges:
        if not edge.bridge:
            continue
        for anchor in (edge.a, edge.b):
            if anchor == "center" or anchor in found:
                continue
            found.append(anchor)
    return tuple(found)


def span_hops(config: SteelTideConfig, anchor: str, path: tuple[str, ...] | list[str]) -> tuple[tuple[str, str], ...]:
    hops: list[tuple[str, str]] = []
    node = anchor
    for nxt in path:
        if is_span_edge(config, node, nxt):
            hops.append((node, nxt))
        node = nxt
    return tuple(hops)


def _adjacency(edges: tuple[Edge, ...] | list[Edge], anchors: tuple[str, ...] | list[str]) -> dict[str, list[tuple[str, float]]]:
    graph: dict[str, list[tuple[str, float]]] = {name: [] for name in anchors}
    for edge in edges:
        graph.setdefault(edge.a, []).append((edge.b, edge.length_m))
        graph.setdefault(edge.b, []).append((edge.a, edge.length_m))
    return graph


def _dijkstra(graph: dict[str, list[tuple[str, float]]], start: str, goal: str) -> list[str] | None:
    """Anchors after `start`, ending at `goal`. Empty if already there. None if blocked."""
    if start == goal:
        return []
    dist = {start: 0.0}
    prev: dict[str, str] = {}
    heap = [(0.0, start)]
    while heap:
        walked, node = heapq.heappop(heap)
        if walked != dist.get(node):
            continue
        if node == goal:
            break
        for nxt, length in graph.get(node, []):
            cand = walked + length
            if cand < dist.get(nxt, float("inf")):
                dist[nxt] = cand
                prev[nxt] = node
                heapq.heappush(heap, (cand, nxt))
    if goal not in dist:
        return None
    chain = [goal]
    while chain[-1] != start:
        chain.append(prev[chain[-1]])
    chain.reverse()
    return chain[1:]


def _graph(config: SteelTideConfig, preferred: str, bridge_state: str) -> dict[str, list[tuple[str, float]]]:
    allowed = [edge for edge in config.edges if edge_allowed(edge, preferred, bridge_state)]
    return _adjacency(allowed, list(config.anchors))


def shortest_path(
    config: SteelTideConfig,
    start: str,
    goal: str,
    preferred: str,
    bridge_state: str,
) -> list[str] | None:
    """Return anchors after `start`, ending at `goal`. Empty if already there. None if blocked."""
    return _dijkstra(_graph(config, preferred, bridge_state), start, goal)


def _approach_bridgehead(config: SteelTideConfig, start: str, goal: str) -> list[str] | None:
    """Walk the fixed deck to a safe bridgehead while the span is open.

    None: `start` is not on that deck, so the alley is the route.
    Empty: already at the safe edge. The span step is not in the graph.
    """
    deck = [edge for edge in config.edges if not edge.bridge and edge.route in _DECK_ROUTES]
    graph = _adjacency(deck, list(config.anchors))
    if _dijkstra(graph, start, goal) is not None:
        return None
    reachable: list[tuple[list[str], str]] = []
    for head in bridgeheads(config):
        path = _dijkstra(graph, start, head)
        if path is not None:
            reachable.append((path, head))
    if not reachable:
        return None
    for path, head in reachable:
        if head == start:
            return []
    reachable.sort(key=lambda item: (sum(1 for _ in item[0]), item[1]))
    return reachable[0][0]


def plan_route(
    config: SteelTideConfig,
    start: str,
    goal: str,
    preferred: str,
    bridge_state: str,
) -> tuple[list[str] | None, str]:
    """Path on the authoritative graph.

    The preferred route wins when it reaches `goal`. An elevated preference
    with the span open approaches the safe bridgehead instead of stepping
    onto a missing edge. Otherwise the repair alley, then any walkable edge
    that is still in the graph, so a character left on a bridgehead can
    leave and still score. None only when the goal is off every walkable edge.
    """
    if start == goal:
        return [], preferred
    direct = shortest_path(config, start, goal, preferred, bridge_state)
    if direct is not None:
        return direct, preferred
    if preferred == "elevated" and bridge_state != "connected":
        approach = _approach_bridgehead(config, start, goal)
        if approach is not None:
            return approach, "elevated"
    alley = shortest_path(config, start, goal, "repair_alley", bridge_state)
    if alley is not None:
        return alley, "repair_alley"
    walkable = _dijkstra(_adjacency(list(authoritative_edges(config, bridge_state)), list(config.anchors)), start, goal)
    if walkable is not None:
        return walkable, "walkable"
    return None, preferred


def path_length_m(
    config: SteelTideConfig,
    start: str,
    goal: str,
    preferred: str,
    bridge_state: str,
) -> float | None:
    path = shortest_path(config, start, goal, preferred, bridge_state)
    if path is None:
        return None
    graph = _graph(config, preferred, bridge_state)
    total = 0.0
    node = start
    for nxt in path:
        length = next(length for dest, length in graph[node] if dest == nxt)
        total += length
        node = nxt
    return total


def step_edge(config: SteelTideConfig, start: str, dest: str, preferred: str, bridge_state: str) -> Edge | None:
    for edge in config.edges:
        if {edge.a, edge.b} != {start, dest}:
            continue
        if edge_allowed(edge, preferred, bridge_state):
            return edge
    return None
