"""A* / Weighted A* on a terrain cost grid with hard-exclusion handling."""
from __future__ import annotations

import heapq

import numpy as np

from ..models import Route, RouteStatus, TerrainGrid, TraversabilityResult, Waypoint

_NBRS_8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
_NBRS_4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _neighbours(connectivity: int):
    if connectivity == 4:
        return _NBRS_4
    if connectivity == 8:
        return _NBRS_8
    raise ValueError("connectivity must be 4 or 8")


def _step_cost(cost_grid: np.ndarray, a, b, res: float) -> float:
    ca = float(cost_grid[a])
    cb = float(cost_grid[b])
    dist = float(np.hypot(a[0] - b[0], a[1] - b[1]) * res)
    return 0.5 * (ca + cb) * dist


def plan_route(
    terrain: TerrainGrid,
    traversability: TraversabilityResult,
    start: tuple[int, int],
    goal: tuple[int, int],
    connectivity: int = 8,
    weight: float = 1.0,
) -> Route:
    if not terrain.contains(start):
        raise ValueError(f"start {start} outside terrain")
    if not terrain.contains(goal):
        raise ValueError(f"goal {goal} outside terrain")
    if weight < 1.0:
        raise ValueError("weight must be >= 1.0")

    hard = traversability.hard_exclusion_mask
    if hard[start]:
        return Route([], 0.0, status=RouteStatus.NO_PATH,
                     message=f"start {start} is hard-excluded")
    if hard[goal]:
        return Route([], 0.0, status=RouteStatus.NO_PATH,
                     message=f"goal {goal} is hard-excluded")

    rows, cols = terrain.shape
    cost_grid = traversability.cost_grid
    min_cost = float(np.min(cost_grid[~hard])) if (~hard).any() else 1.0
    min_cost = max(min_cost, 1e-6)

    def h(a, b):
        dr = abs(a[0] - b[0])
        dc = abs(a[1] - b[1])
        if connectivity == 8:
            diag = min(dr, dc)
            straight = max(dr, dc) - diag
            cells = diag * np.sqrt(2.0) + straight
        else:
            cells = dr + dc
        return cells * terrain.resolution_m * min_cost

    g_score: dict[tuple[int, int], float] = {start: 0.0}
    prev: dict[tuple[int, int], tuple[int, int]] = {}
    open_heap = [(h(start, goal), 0.0, start)]
    visited: set[tuple[int, int]] = set()

    while open_heap:
        _, g, cell = heapq.heappop(open_heap)
        if cell in visited:
            continue
        visited.add(cell)
        if cell == goal:
            return _reconstruct(terrain, traversability, prev, start, goal, connectivity)
        r, c = cell
        for dr, dc in _neighbours(connectivity):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            nbr = (nr, nc)
            if hard[nbr]:
                continue
            if dr != 0 and dc != 0:
                if hard[(r + dr, c)] or hard[(r, c + dc)]:
                    continue
            tentative = g + _step_cost(cost_grid, cell, nbr, terrain.resolution_m)
            if tentative < g_score.get(nbr, float("inf")):
                g_score[nbr] = tentative
                prev[nbr] = cell
                heapq.heappush(open_heap, (tentative + weight * h(nbr, goal), tentative, nbr))

    return Route([], 0.0, status=RouteStatus.NO_PATH,
                 message=f"no path from {start} to {goal}")


def _reconstruct(
    terrain: TerrainGrid,
    traversability: TraversabilityResult,
    prev: dict,
    start: tuple[int, int],
    goal: tuple[int, int],
    connectivity: int,
) -> Route:
    path = [goal]
    while path[-1] != start:
        path.append(prev[path[-1]])
    path.reverse()

    waypoints: list[Waypoint] = []
    for cell in path:
        lat, lon = terrain.cell_to_latlon(cell)
        waypoints.append(Waypoint(row=cell[0], col=cell[1], lat=lat, lon=lon))

    total_dist = 0.0
    total_cost = 0.0
    uses_unknown = False
    for a, b in zip(path[:-1], path[1:]):
        total_dist += float(np.hypot(a[0] - b[0], a[1] - b[1]) * terrain.resolution_m)
        total_cost += _step_cost(traversability.cost_grid, a, b, terrain.resolution_m)
        if traversability.unknown_mask[a] or traversability.unknown_mask[b]:
            uses_unknown = True

    return Route(
        waypoints=waypoints,
        distance_m=total_dist,
        travel_duration_h=0.0,
        terrain_cost=total_cost,
        status=RouteStatus.OK,
        message="",
        uses_unknown_terrain=uses_unknown,
    )