"""Human mobility model: effective walking speed per terrain cell."""
from __future__ import annotations

import numpy as np

from ..models import (
    MobilityEstimate,
    MobilityParams,
    Route,
    SegmentMobility,
    TerrainGrid,
)


def effective_speed_kmh(
    terrain: TerrainGrid, cell: tuple[int, int], params: MobilityParams
) -> float:
    slope = float(terrain.slope_deg[cell])
    rough = max(0.0, float(terrain.roughness_m[cell]))
    slope_loss = min(0.9, params.slope_speed_penalty_per_deg * abs(slope))
    rough_loss = min(0.9, params.roughness_speed_penalty_per_m * rough)
    speed = params.base_walking_speed_kmh * (1.0 - slope_loss) * (1.0 - rough_loss)
    return max(speed, params.min_effective_speed_kmh)


def _step_distance_m(a: tuple[int, int], b: tuple[int, int], res: float) -> float:
    return float(np.hypot(a[0] - b[0], a[1] - b[1]) * res)


def estimate_route_mobility(
    route: Route, terrain: TerrainGrid, params: MobilityParams
) -> MobilityEstimate:
    if len(route.waypoints) < 2:
        return MobilityEstimate(segments=[], total_distance_m=0.0, total_duration_h=0.0)

    segments: list[SegmentMobility] = []
    total_d = 0.0
    total_t = 0.0
    for a, b in zip(route.waypoints[:-1], route.waypoints[1:]):
        ca = (a.row, a.col)
        cb = (b.row, b.col)
        speed = 0.5 * (effective_speed_kmh(terrain, ca, params)
                       + effective_speed_kmh(terrain, cb, params))
        speed = max(speed, params.min_effective_speed_kmh)
        dist_m = _step_distance_m(ca, cb, terrain.resolution_m)
        dur_h = (dist_m / 1000.0) / speed
        segments.append(SegmentMobility(ca, cb, dist_m, speed, dur_h))
        total_d += dist_m
        total_t += dur_h
    return MobilityEstimate(segments, total_d, total_t)