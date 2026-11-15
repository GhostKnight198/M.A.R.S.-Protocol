"""Dynamic feedback and mission-level replanning."""
from __future__ import annotations

from ..models import (
    MissionConfig,
    MissionState,
    MissionStatus,
    ReportedObstacle,
    ReplanAction,
    ReplanningResult,
    Route,
    RouteStatus,
    SafetyAssessment,
    SafetyClassification,
    ScientificObjective,
    TerrainGrid,
    TraversabilityResult,
)
from .mobility import estimate_route_mobility
from .resource_eva import compute_resource_consumption
from .route_planner import plan_route
from .safety import assess_mission_safety
from .traversability import compute_traversability


def apply_obstacle_to_terrain(
    terrain: TerrainGrid, obstacle: ReportedObstacle
) -> TerrainGrid:
    if not terrain.contains(obstacle.cell):
        raise ValueError(f"obstacle cell {obstacle.cell} outside terrain")
    if obstacle.radius_cells < 0:
        raise ValueError("radius_cells must be >= 0")
    hazard = terrain.hazard_mask.copy()
    rows, cols = terrain.shape
    r, c = obstacle.cell
    rad = obstacle.radius_cells
    for dr in range(-rad, rad + 1):
        for dc in range(-rad, rad + 1):
            if dr * dr + dc * dc > rad * rad:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                hazard[nr, nc] = True
    return TerrainGrid(
        elevation_m=terrain.elevation_m,
        slope_deg=terrain.slope_deg,
        roughness_m=terrain.roughness_m,
        hazard_mask=hazard,
        valid_mask=terrain.valid_mask,
        resolution_m=terrain.resolution_m,
        origin_lat=terrain.origin_lat,
        origin_lon=terrain.origin_lon,
    )


def _empty_safety() -> SafetyAssessment:
    return SafetyAssessment(
        classification=SafetyClassification.DO_NOT_RECOMMEND,
        reasons=["no feasible route"],
        resource_checks=[],
        return_feasible=False,
        time_ok=False,
        uses_unknown_terrain=False,
    )


def _combine_and_assess(
    start_cell: tuple[int, int],
    objectives: list[ScientificObjective],
    habitat_cell: tuple[int, int],
    terrain: TerrainGrid,
    traversability: TraversabilityResult,
    config: MissionConfig,
    state: MissionState,
) -> tuple[Route | None, SafetyAssessment | None]:
    legs: list[Route] = []
    current = start_cell
    for obj in objectives:
        leg = plan_route(terrain, traversability, current, obj.cell)
        if leg.status != RouteStatus.OK:
            return None, None
        leg.waypoints[-1].kind = "target"
        leg.waypoints[-1].objective_id = obj.id
        legs.append(leg)
        current = obj.cell
    ret = plan_route(terrain, traversability, current, habitat_cell)
    if ret.status != RouteStatus.OK:
        return None, None
    ret.waypoints[-1].kind = "habitat"
    legs.append(ret)

    waypoints = []
    for i, leg in enumerate(legs):
        wps = leg.waypoints[1:] if i > 0 else leg.waypoints
        waypoints.extend(wps)
    combined = Route(
        waypoints=waypoints,
        distance_m=sum(leg.distance_m for leg in legs),
        terrain_cost=sum(leg.terrain_cost for leg in legs),
        status=RouteStatus.OK,
        uses_unknown_terrain=any(leg.uses_unknown_terrain for leg in legs),
    )
    mobility = estimate_route_mobility(combined, terrain, config.mobility_params)
    combined.travel_duration_h = mobility.total_duration_h
    activity_h = sum(o.activity_duration_h for o in objectives)
    rc = compute_resource_consumption(
        mobility.total_duration_h, activity_h, mobility.total_distance_m, config
    )
    remaining_time_h = max(0.0, config.eva_time_limit_h - state.elapsed_h)
    safety = assess_mission_safety(
        config, combined, rc, traversability,
        remaining_budget=state.remaining_resources,
        remaining_time_h=remaining_time_h,
    )
    return combined, safety


def _update_state(
    state: MissionState,
    route: Route | None,
    status: MissionStatus,
    reasons: list[str],
    new_remaining: list[str] | None = None,
    new_obstacles: list[ReportedObstacle] | None = None,
) -> MissionState:
    return MissionState(
        current_position=state.current_position,
        habitat=state.habitat,
        remaining_objectives=(
            new_remaining if new_remaining is not None
            else list(state.remaining_objectives)
        ),
        completed_objectives=list(state.completed_objectives),
        route=route,
        elapsed_h=state.elapsed_h,
        remaining_resources=state.remaining_resources.copy(),
        reported_obstacles=(
            new_obstacles if new_obstacles is not None
            else list(state.reported_obstacles)
        ),
        reported_observations=list(state.reported_observations),
        status=status,
        version=state.version + 1,
        history=list(state.history) + reasons,
    )


def replan_mission(
    state: MissionState,
    terrain: TerrainGrid,
    traversability: TraversabilityResult,
    config: MissionConfig,
    objectives_by_id: dict[str, ScientificObjective],
    obstacle: ReportedObstacle | None = None,
) -> ReplanningResult:
    reasons: list[str] = []

    if obstacle is not None:
        terrain = apply_obstacle_to_terrain(terrain, obstacle)
        traversability = compute_traversability(terrain, config.traversability_params)
        reasons.append(
            f"Obstacle applied at {obstacle.cell} "
            f"(r={obstacle.radius_cells}): {obstacle.description}"
        )

    current_cell = (state.current_position.row, state.current_position.col)
    habitat_cell = (state.habitat.row, state.habitat.col)
    new_obstacles = list(state.reported_obstacles)
    if obstacle is not None:
        new_obstacles.append(obstacle)

    if traversability.hard_exclusion_mask[current_cell]:
        reasons.append(
            "Astronaut's current cell is hard-excluded after update; ABORT."
        )
        updated = _update_state(state, None, MissionStatus.ABORTED, reasons,
                                new_obstacles=new_obstacles)
        return ReplanningResult(
            ReplanAction.ABORT, updated, None, _empty_safety(), reasons
        )

    remaining_ids = list(state.remaining_objectives)
    remaining_objs = [
        objectives_by_id[oid] for oid in remaining_ids if oid in objectives_by_id
    ]
    mandatory = [o for o in remaining_objs if o.mandatory]
    optional = [o for o in remaining_objs if not o.mandatory]

    if not remaining_objs:
        full_route, full_safety = _combine_and_assess(
            current_cell, [], habitat_cell, terrain, traversability, config, state
        )
        if (full_route is not None and full_safety is not None
                and full_safety.classification != SafetyClassification.DO_NOT_RECOMMEND):
            reasons.append("No remaining objectives; heading home.")
            updated = _update_state(state, full_route, MissionStatus.RETURNING,
                                    reasons, new_remaining=[],
                                    new_obstacles=new_obstacles)
            return ReplanningResult(ReplanAction.RETURN, updated,
                                    full_route, full_safety, reasons)
        reasons.append("No remaining objectives and no feasible return path.")
        updated = _update_state(state, None, MissionStatus.ABORTED, reasons,
                                new_remaining=[], new_obstacles=new_obstacles)
        return ReplanningResult(ReplanAction.ABORT, updated, None,
                                _empty_safety(), reasons)

    full_route, full_safety = _combine_and_assess(
        current_cell, remaining_objs, habitat_cell, terrain, traversability, config, state
    )

    if (full_route is not None and full_safety is not None
            and full_safety.classification == SafetyClassification.ACCEPTABLE):
        reasons.append("Full remaining mission is acceptable.")
        updated = _update_state(state, full_route, MissionStatus.ACTIVE, reasons,
                                new_obstacles=new_obstacles)
        return ReplanningResult(ReplanAction.CONTINUE, updated,
                                full_route, full_safety, reasons)

    if (full_route is not None and full_safety is not None
            and full_safety.classification == SafetyClassification.CAUTION):
        if optional:
            mand_route, mand_safety = _combine_and_assess(
                current_cell, mandatory, habitat_cell,
                terrain, traversability, config, state
            )
            if (mand_route is not None and mand_safety is not None
                    and mand_safety.classification == SafetyClassification.ACCEPTABLE):
                reasons.append("Downgrading to mandatory-only to remove caution.")
                updated = _update_state(
                    state, mand_route, MissionStatus.ACTIVE, reasons,
                    new_remaining=[o.id for o in mandatory],
                    new_obstacles=new_obstacles,
                )
                return ReplanningResult(ReplanAction.SKIP_OPTIONAL, updated,
                                        mand_route, mand_safety, reasons)
        reasons.append(
            "Continuing with CAUTION: " + "; ".join(full_safety.reasons)
        )
        updated = _update_state(state, full_route, MissionStatus.ACTIVE,
                                reasons, new_obstacles=new_obstacles)
        return ReplanningResult(ReplanAction.CONTINUE, updated,
                                full_route, full_safety, reasons)

    if optional:
        mand_route, mand_safety = _combine_and_assess(
            current_cell, mandatory, habitat_cell,
            terrain, traversability, config, state
        )
        if (mand_route is not None and mand_safety is not None
                and mand_safety.classification != SafetyClassification.DO_NOT_RECOMMEND):
            if not mandatory:
                reasons.append("Dropping all remaining objectives; heading home.")
                updated = _update_state(state, mand_route, MissionStatus.RETURNING,
                                        reasons, new_remaining=[],
                                        new_obstacles=new_obstacles)
                return ReplanningResult(ReplanAction.RETURN, updated,
                                        mand_route, mand_safety, reasons)
            reasons.append("Dropping optional objectives to restore feasibility.")
            updated = _update_state(
                state, mand_route, MissionStatus.ACTIVE, reasons,
                new_remaining=[o.id for o in mandatory],
                new_obstacles=new_obstacles,
            )
            return ReplanningResult(ReplanAction.SKIP_OPTIONAL, updated,
                                    mand_route, mand_safety, reasons)

    ret = plan_route(terrain, traversability, current_cell, habitat_cell)
    if ret.status == RouteStatus.OK:
        ret.waypoints[-1].kind = "habitat"
        mobility = estimate_route_mobility(ret, terrain, config.mobility_params)
        ret.travel_duration_h = mobility.total_duration_h
        rc = compute_resource_consumption(
            mobility.total_duration_h, 0.0, mobility.total_distance_m, config
        )
        remaining_time_h = max(0.0, config.eva_time_limit_h - state.elapsed_h)
        ret_safety = assess_mission_safety(
            config, ret, rc, traversability,
            remaining_budget=state.remaining_resources,
            remaining_time_h=remaining_time_h,
        )
        if ret_safety.classification != SafetyClassification.DO_NOT_RECOMMEND:
            reasons.append("Return to habitat feasible; aborting remaining science.")
            updated = _update_state(state, ret, MissionStatus.RETURNING, reasons,
                                    new_remaining=[], new_obstacles=new_obstacles)
            return ReplanningResult(ReplanAction.RETURN, updated, ret,
                                    ret_safety, reasons)
        reasons.append("Return-only infeasible: " + "; ".join(ret_safety.reasons))
        updated = _update_state(state, None, MissionStatus.ABORTED, reasons,
                                new_obstacles=new_obstacles)
        return ReplanningResult(ReplanAction.ABORT, updated, None,
                                ret_safety, reasons)

    reasons.append("No route to habitat; mission ABORTED.")
    updated = _update_state(state, None, MissionStatus.ABORTED, reasons,
                            new_obstacles=new_obstacles)
    return ReplanningResult(ReplanAction.ABORT, updated, None,
                            _empty_safety(), reasons)