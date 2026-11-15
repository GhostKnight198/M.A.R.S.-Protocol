"""End-to-end pipeline: MOLA → Traversability → Route → Feasibility → Report."""
from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

from mars_protocol.engines.mission_planner import plan_mission
from mars_protocol.engines.safety import assess_mission_safety
from mars_protocol.engines.traversability import compute_traversability
from mars_protocol.models import (
    MissionConfig, MissionState, MissionStatus, MobilityParams,
    ObjectivePriority, ReserveRequirements, ResourceBudget, ResourceRates,
    ScientificObjective, TraversabilityParams, Waypoint,
)
from mars_protocol.reporting.report_generator import generate_report

from .config import GALE_CRATER_CONFIG, GaleCraterConfig
from .data.data_loader import load_mola_megdr
from .data.preprocessing import build_derived_layers

log = logging.getLogger(__name__)


def _build_mission_config(grid, cfg: GaleCraterConfig):
    r, c = grid.latlon_to_cell(cfg.habitat_lat, cfg.habitat_lon)
    r = max(0, min(grid.shape[0] - 1, r))
    c = max(0, min(grid.shape[1] - 1, c))
    return MissionConfig(
        habitat_id=cfg.habitat_id,
        habitat_lat=cfg.habitat_lat,
        habitat_lon=cfg.habitat_lon,
        habitat_cell=(r, c),
        eva_time_limit_h=cfg.eva_time_limit_h,
        resource_budget=ResourceBudget(1.6, 2.5, 900.0, 60.0),
        resource_rates=ResourceRates(0.05, 0.08, 0.10, 0.25, 40.0, 60.0, 2.0, 4.0),
        reserves=ReserveRequirements(0.30, 0.50, 150.0, 10.0, 0.5),
        traversability_params=TraversabilityParams(),
        mobility_params=MobilityParams(base_walking_speed_kmh=cfg.nominal_walking_speed_kmh),
        contingency_fraction=cfg.contingency_fraction,
        metadata={"region": cfg.region_name},
    )


def _build_objectives(grid, cfg: GaleCraterConfig):
    objs = []
    for t in cfg.targets:
        r, c = grid.latlon_to_cell(t["lat"], t["lon"])
        r = max(0, min(grid.shape[0] - 1, r))
        c = max(0, min(grid.shape[1] - 1, c))
        objs.append(ScientificObjective(
            id=t["id"], name=t["name"], description=t["rationale"],
            cell=(r, c), lat=t["lat"], lon=t["lon"],
            priority=ObjectivePriority(t["priority"]),
            mandatory=t["mandatory"],
            activity_duration_h=t["activity_h"],
            equipment_required=["sample_kit", "spectrometer"],
        ))
    return objs


def run_pipeline() -> dict[str, Any]:
    cfg = GALE_CRATER_CONFIG
    grid_raw, provenance = load_mola_megdr(
        cfg.mola_img_path, cfg.habitat_lat, cfg.habitat_lon, cfg.operational_radius_m,
    )
    grid = build_derived_layers(grid_raw)
    mission_cfg = _build_mission_config(grid, cfg)
    traversability = compute_traversability(grid, mission_cfg.traversability_params)
    objectives = _build_objectives(grid, cfg)
    plan = plan_mission(grid, traversability, mission_cfg, objectives)
    safety = assess_mission_safety(
        mission_cfg, plan.route, plan.resource_consumption, traversability,
    )

    r, c = mission_cfg.habitat_cell
    wp = Waypoint(row=r, col=c, lat=cfg.habitat_lat, lon=cfg.habitat_lon, kind="habitat")
    state = MissionState(
        current_position=wp, habitat=wp,
        remaining_objectives=list(plan.ordered_objective_ids),
        completed_objectives=[],
        route=plan.route, elapsed_h=0.0,
        remaining_resources=mission_cfg.resource_budget.copy(),
        reported_obstacles=[], reported_observations=[],
        status=MissionStatus.ACTIVE if plan.feasible else MissionStatus.INFEASIBLE,
        version=0, history=[f"Pipeline run: feasible={plan.feasible}"],
    )

    report = generate_report(mission_cfg, state, plan=plan, safety=safety, objectives=objectives)
    report["provenance"] = asdict(provenance)
    return {
        "report": report,
        "plan": {
            "ordered_objectives": plan.ordered_objective_ids,
            "feasible": plan.feasible,
            "route_waypoints": [(w.row, w.col) for w in plan.route.waypoints],
            "distance_m": plan.route.distance_m,
            "travel_h": plan.travel_h,
            "warnings": plan.warnings,
        },
        "safety": {
            "classification": safety.classification.value,
            "reasons": safety.reasons,
        },
        "provenance": asdict(provenance),
    }