"""Mission-level objective selection, sequencing, and feasibility."""
from __future__ import annotations

from ..models import (
    MissionConfig,
    MissionPlan,
    Route,
    RouteStatus,
    SafetyClassification,
    ScientificObjective,
    TerrainGrid,
    TraversabilityResult,
)
from .mobility import estimate_route_mobility
from .objective_manager import sort_objectives
from .resource_eva import compute_resource_consumption
from .route_planner import plan_route
from .safety import assess_mission_safety


def _concat_routes(routes: list[Route]) -> Route:
    if not routes:
        return Route([], 0.0, status=RouteStatus.NO_PATH, message="empty route list")
    waypoints = []
    total_dist = 0.0
    total_cost = 0.0
    uses_unknown = False
    for i, r in enumerate(routes):
        if r.status != RouteStatus.OK:
            return Route([], 0.0, status=RouteStatus.NO_PATH, message=r.message)
        wps = r.waypoints[1:] if i > 0 else r.waypoints
        waypoints.extend(wps)
        total_dist += r.distance_m
        total_cost += r.terrain_cost
        uses_unknown = uses_unknown or r.uses_unknown_terrain
    return Route(
        waypoints=waypoints,
        distance_m=total_dist,
        terrain_cost=total_cost,
        status=RouteStatus.OK,
        uses_unknown_terrain=uses_unknown,
    )


def _plan_legs(
    start_cell: tuple[int, int],
    habitat_cell: tuple[int, int],
    objectives: list[ScientificObjective],
    terrain: TerrainGrid,
    traversability: TraversabilityResult,
    connectivity: int,
) -> Route | None:
    legs: list[Route] = []
    current = start_cell
    for obj in objectives:
        leg = plan_route(terrain, traversability, current, obj.cell, connectivity)
        if leg.status != RouteStatus.OK:
            return None
        leg.waypoints[-1].kind = "target"
        leg.waypoints[-1].objective_id = obj.id
        legs.append(leg)
        current = obj.cell
    ret = plan_route(terrain, traversability, current, habitat_cell, connectivity)
    if ret.status != RouteStatus.OK:
        return None
    ret.waypoints[-1].kind = "habitat"
    legs.append(ret)
    return _concat_routes(legs)


def _evaluate(
    route: Route,
    objectives: list[ScientificObjective],
    terrain: TerrainGrid,
    traversability: TraversabilityResult,
    config: MissionConfig,
    remaining_budget=None,
    remaining_time_h=None,
):
    mobility = estimate_route_mobility(route, terrain, config.mobility_params)
    route.travel_duration_h = mobility.total_duration_h
    activity_h = sum(o.activity_duration_h for o in objectives)
    rc = compute_resource_consumption(
        mobility.total_duration_h, activity_h, mobility.total_distance_m, config
    )
    safety = assess_mission_safety(
        config, route, rc, traversability,
        remaining_budget=remaining_budget,
        remaining_time_h=remaining_time_h,
    )
    return route, rc, safety


def _infeasible_plan(config: MissionConfig, warnings: list[str]) -> MissionPlan:
    return MissionPlan(
        ordered_objective_ids=[],
        route=Route([], 0.0, status=RouteStatus.NO_PATH, message="infeasible"),
        travel_h=0.0,
        activity_h=0.0,
        resource_consumption=compute_resource_consumption(0.0, 0.0, 0.0, config),
        feasible=False,
        warnings=warnings,
    )


def plan_mission(
    terrain: TerrainGrid,
    traversability: TraversabilityResult,
    config: MissionConfig,
    objectives: list[ScientificObjective],
    connectivity: int = 8,
    remaining_budget=None,
    remaining_time_h=None,
) -> MissionPlan:
    if not objectives:
        raise ValueError("plan_mission requires at least one objective")

    warnings: list[str] = []
    sorted_objs = sort_objectives(objectives)
    habitat_cell = config.habitat_cell
    accepted: list[ScientificObjective] = []

    for obj in sorted_objs:
        if not terrain.contains(obj.cell):
            warnings.append(f"Objective {obj.id} at {obj.cell} outside terrain grid.")
            if obj.mandatory:
                warnings.append(f"Mandatory objective {obj.id} unreachable; infeasible.")
                return _infeasible_plan(config, warnings)
            continue
        if not obj.mandatory:
            continue

        candidate = accepted + [obj]
        route = _plan_legs(habitat_cell, habitat_cell, candidate,
                           terrain, traversability, connectivity)
        if route is None:
            warnings.append(f"Mandatory objective {obj.id}: no route; infeasible.")
            return _infeasible_plan(config, warnings)
        _, _rc, safety = _evaluate(route, candidate, terrain, traversability,
                                   config, remaining_budget, remaining_time_h)
        if safety.classification == SafetyClassification.DO_NOT_RECOMMEND:
            warnings.append(
                f"Mandatory objective {obj.id} infeasible: "
                + "; ".join(safety.reasons)
            )
            return _infeasible_plan(config, warnings)
        accepted = candidate

    for obj in sorted_objs:
        if obj.mandatory or not terrain.contains(obj.cell):
            continue
        candidate = accepted + [obj]
        route = _plan_legs(habitat_cell, habitat_cell, candidate,
                           terrain, traversability, connectivity)
        if route is None:
            warnings.append(f"Optional objective {obj.id} skipped: no route.")
            continue
        _, _rc, safety = _evaluate(route, candidate, terrain, traversability,
                                   config, remaining_budget, remaining_time_h)
        if safety.classification == SafetyClassification.DO_NOT_RECOMMEND:
            warnings.append(
                f"Optional objective {obj.id} skipped: "
                + "; ".join(safety.reasons)
            )
            continue
        accepted = candidate

    if not accepted:
        warnings.append("No objectives could be included in the mission.")
        return _infeasible_plan(config, warnings)

    final_route = _plan_legs(habitat_cell, habitat_cell, accepted,
                             terrain, traversability, connectivity)
    if final_route is None:
        warnings.append("Final route assembly failed unexpectedly.")
        return _infeasible_plan(config, warnings)
    final_route, final_rc, final_safety = _evaluate(
        final_route, accepted, terrain, traversability,
        config, remaining_budget, remaining_time_h,
    )
    feasible = final_safety.classification != SafetyClassification.DO_NOT_RECOMMEND
    if final_safety.classification == SafetyClassification.CAUTION:
        warnings.append("Mission requires caution: " + "; ".join(final_safety.reasons))
    return MissionPlan(
        ordered_objective_ids=[o.id for o in accepted],
        route=final_route,
        travel_h=final_rc.travel_h,
        activity_h=final_rc.activity_h,
        resource_consumption=final_rc,
        feasible=feasible,
        warnings=warnings,
    )