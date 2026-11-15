"""Structured and text mission report generation."""
from __future__ import annotations

from typing import Any

from ..models import (
    MissionConfig,
    MissionPlan,
    MissionState,
    SafetyAssessment,
    ScientificObjective,
)


def generate_report(
    config: MissionConfig,
    state: MissionState,
    plan: MissionPlan | None = None,
    safety: SafetyAssessment | None = None,
    objectives: list[ScientificObjective] | None = None,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "mission": {
            "habitat_id": config.habitat_id,
            "habitat_lat": config.habitat_lat,
            "habitat_lon": config.habitat_lon,
            "habitat_cell": list(config.habitat_cell),
            "eva_time_limit_h": config.eva_time_limit_h,
            "contingency_fraction": config.contingency_fraction,
            "region": config.metadata.get("region", ""),
        },
        "resource_budget": {
            "oxygen_kg": config.resource_budget.oxygen_kg,
            "water_l": config.resource_budget.water_l,
            "energy_wh": config.resource_budget.energy_wh,
            "other_units": config.resource_budget.other_units,
        },
        "reserves": {
            "oxygen_kg": config.reserves.oxygen_kg_reserve,
            "water_l": config.reserves.water_l_reserve,
            "energy_wh": config.reserves.energy_wh_reserve,
            "other_units": config.reserves.other_units_reserve,
            "time_h": config.reserves.time_reserve_h,
        },
        "state": {
            "status": state.status.value,
            "version": state.version,
            "elapsed_h": state.elapsed_h,
            "current_position": [state.current_position.row, state.current_position.col],
            "habitat_cell": [state.habitat.row, state.habitat.col],
            "remaining_resources": {
                "oxygen_kg": state.remaining_resources.oxygen_kg,
                "water_l": state.remaining_resources.water_l,
                "energy_wh": state.remaining_resources.energy_wh,
                "other_units": state.remaining_resources.other_units,
            },
            "remaining_objectives": list(state.remaining_objectives),
            "completed_objectives": list(state.completed_objectives),
            "reported_obstacles": [
                {"cell": list(o.cell), "radius": o.radius_cells,
                 "severity": o.severity, "description": o.description}
                for o in state.reported_obstacles
            ],
            "reported_observations": [
                {"description": o.description,
                 "cell": list(o.cell) if o.cell else None}
                for o in state.reported_observations
            ],
            "history": list(state.history),
        },
        "objectives": [
            {"id": o.id, "name": o.name, "cell": list(o.cell),
             "mandatory": o.mandatory, "priority": o.priority.value,
             "activity_duration_h": o.activity_duration_h}
            for o in (objectives or [])
        ],
    }
    if plan is not None:
        rc = plan.resource_consumption
        report["plan"] = {
            "ordered_objective_ids": list(plan.ordered_objective_ids),
            "feasible": plan.feasible,
            "travel_h": plan.travel_h,
            "activity_h": plan.activity_h,
            "route_distance_m": plan.route.distance_m,
            "route_status": plan.route.status.value,
            "uses_unknown_terrain": plan.route.uses_unknown_terrain,
            "resource_consumption": {
                "oxygen_kg": rc.oxygen_kg_used,
                "water_l": rc.water_l_used,
                "energy_wh": rc.energy_wh_used,
                "other_units": rc.other_units_used,
                "contingency_oxygen_kg": rc.contingency_oxygen_kg,
                "contingency_water_l": rc.contingency_water_l,
                "contingency_energy_wh": rc.contingency_energy_wh,
                "contingency_other_units": rc.contingency_other_units,
                "contingency_time_h": rc.contingency_time_h,
            },
            "warnings": list(plan.warnings),
        }
    if safety is not None:
        report["safety"] = {
            "classification": safety.classification.value,
            "reasons": list(safety.reasons),
            "return_feasible": safety.return_feasible,
            "time_ok": safety.time_ok,
            "uses_unknown_terrain": safety.uses_unknown_terrain,
            "resource_checks": [
                {"resource": c.resource, "required": c.required,
                 "available": c.available, "reserve": c.reserve, "ok": c.ok}
                for c in safety.resource_checks
            ],
        }
    return report


def format_report_text(report: dict[str, Any]) -> str:
    lines: list[str] = []
    m = report["mission"]
    lines.append("=" * 70)
    lines.append("M.A.R.S. PROTOCOL — MISSION REPORT")
    lines.append("=" * 70)
    lines.append(f"Region: {m['region']}")
    lines.append(f"Habitat: {m['habitat_id']}  lat={m['habitat_lat']:.6f}  lon={m['habitat_lon']:.6f}")
    lines.append(f"Habitat cell: {m['habitat_cell']}")
    lines.append(f"EVA time limit: {m['eva_time_limit_h']} h   Contingency: {m['contingency_fraction']:.0%}")

    b = report["resource_budget"]
    lines.append(
        f"Budget:   O2={b['oxygen_kg']}kg  H2O={b['water_l']}L  "
        f"E={b['energy_wh']}Wh  Other={b['other_units']}"
    )
    r = report["reserves"]
    lines.append(
        f"Reserves: O2={r['oxygen_kg']}kg  H2O={r['water_l']}L  "
        f"E={r['energy_wh']}Wh  Other={r['other_units']}  Time={r['time_h']}h"
    )

    s = report["state"]
    lines.append("")
    lines.append(f"State: {s['status'].upper()}  v={s['version']}  elapsed={s['elapsed_h']:.2f} h")
    lines.append(f"Current position: {s['current_position']}  Habitat: {s['habitat_cell']}")
    lines.append(f"Remaining objectives: {s['remaining_objectives']}")
    lines.append(f"Completed objectives: {s['completed_objectives']}")
    rr = s["remaining_resources"]
    lines.append(
        f"Remaining resources: O2={rr['oxygen_kg']:.3f}  H2O={rr['water_l']:.3f}  "
        f"E={rr['energy_wh']:.1f}  Other={rr['other_units']:.2f}"
    )

    if s["reported_obstacles"]:
        lines.append("")
        lines.append("Reported obstacles:")
        for o in s["reported_obstacles"]:
            lines.append(
                f"  - {o['description']}  cell={o['cell']}  r={o['radius']}  ({o['severity']})"
            )

    if "plan" in report:
        p = report["plan"]
        lines.append("")
        lines.append(f"Plan: {'FEASIBLE' if p['feasible'] else 'INFEASIBLE'}")
        lines.append(f"  Ordered objectives: {p['ordered_objective_ids']}")
        lines.append(
            f"  Route: status={p['route_status']}  distance={p['route_distance_m']:.1f} m  "
            f"travel={p['travel_h']:.2f} h  activity={p['activity_h']:.2f} h"
        )
        lines.append(f"  Uses unknown terrain: {p['uses_unknown_terrain']}")
        rc = p["resource_consumption"]
        lines.append(
            f"  Consumption: O2={rc['oxygen_kg']:.3f}+{rc['contingency_oxygen_kg']:.3f}  "
            f"H2O={rc['water_l']:.3f}+{rc['contingency_water_l']:.3f}  "
            f"E={rc['energy_wh']:.1f}+{rc['contingency_energy_wh']:.1f}  "
            f"Other={rc['other_units']:.2f}+{rc['contingency_other_units']:.2f}"
        )
        for w in p["warnings"]:
            lines.append(f"  ! {w}")

    if "safety" in report:
        sf = report["safety"]
        lines.append("")
        lines.append(f"Safety: {sf['classification'].upper()}")
        lines.append(
            f"  Return feasible: {sf['return_feasible']}   "
            f"Time OK: {sf['time_ok']}   "
            f"Unknown terrain: {sf['uses_unknown_terrain']}"
        )
        for c in sf["resource_checks"]:
            mark = "OK   " if c["ok"] else "SHORT"
            lines.append(
                f"  [{mark}] {c['resource']:<12s} required={c['required']:.3f}  "
                f"available={c['available']:.3f}  reserve={c['reserve']:.3f}"
            )
        for reason in sf["reasons"]:
            lines.append(f"  ! {reason}")

    if s["history"]:
        lines.append("")
        lines.append("History:")
        for h in s["history"]:
            lines.append(f"  - {h}")

    lines.append("=" * 70)
    return "\n".join(lines)