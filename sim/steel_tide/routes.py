"""Two Steel Tide routes. The repair alley never depends on the bridge span."""

from __future__ import annotations

import heapq

from .config import Edge, SteelTideConfig


def edge_allowed(edge: Edge, preferred: str, bridge_state: str) -> bool:
    if edge.bridge and bridge_state != "connected":
        return False
    if preferred == "repair_alley" and edge.route == "elevated":
        return False
    if preferred == "elevated" and edge.route == "alley":
        return False
    return True


def _graph(config: SteelTideConfig, preferred: str, bridge_state: str) -> dict[str, list[tuple[str, float]]]:
    graph: dict[str, list[tuple[str, float]]] = {name: [] for name in config.anchors}
    for edge in config.edges:
        if not edge_allowed(edge, preferred, bridge_state):
            continue
        graph.setdefault(edge.a, []).append((edge.b, edge.length_m))
        graph.setdefault(edge.b, []).append((edge.a, edge.length_m))
    return graph


def shortest_path(
    config: SteelTideConfig,
    start: str,
    goal: str,
    preferred: str,
    bridge_state: str,
) -> list[str] | None:
    """Return anchors after `start`, ending at `goal`. Empty if already there. None if blocked."""
    if start == goal:
        return []
    graph = _graph(config, preferred, bridge_state)
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
