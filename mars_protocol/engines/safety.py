"""Mission-level safety and feasibility classification."""
from __future__ import annotations

from ..models import (
    MissionConfig,
    ResourceBudget,
    ResourceCheck,
    ResourceConsumptionResult,
    Route,
    RouteStatus,
    SafetyAssessment,
    SafetyClassification,
)


def assess_mission_safety(
    config: MissionConfig,
    route: Route | None,
    resource_consumption: ResourceConsumptionResult,
    traversability=None,
    remaining_budget: ResourceBudget | None = None,
    remaining_time_h: float | None = None,
) -> SafetyAssessment:
    reasons: list[str] = []
    checks: list[ResourceCheck] = []

    budget = remaining_budget if remaining_budget is not None else config.resource_budget
    time_limit = (
        remaining_time_h if remaining_time_h is not None else config.eva_time_limit_h
    )
    reserves = config.reserves
    rc = resource_consumption

    pairs = [
        ("oxygen_kg", rc.oxygen_kg_used + rc.contingency_oxygen_kg,
         budget.oxygen_kg, reserves.oxygen_kg_reserve),
        ("water_l", rc.water_l_used + rc.contingency_water_l,
         budget.water_l, reserves.water_l_reserve),
        ("energy_wh", rc.energy_wh_used + rc.contingency_energy_wh,
         budget.energy_wh, reserves.energy_wh_reserve),
        ("other_units", rc.other_units_used + rc.contingency_other_units,
         budget.other_units, reserves.other_units_reserve),
    ]
    for name, used, avail, reserve in pairs:
        required = used + reserve
        ok = required <= avail
        checks.append(ResourceCheck(name, required, avail, reserve, ok))
        if not ok:
            reasons.append(
                f"{name}: shortfall {required - avail:.3f} "
                f"(need {required:.3f} = used {used:.3f} + reserve {reserve:.3f}; "
                f"available {avail:.3f})"
            )

    total_time = rc.travel_h + rc.activity_h + rc.contingency_time_h
    required_time = total_time + reserves.time_reserve_h
    time_ok = required_time <= time_limit
    if not time_ok:
        reasons.append(
            f"EVA time: need {required_time:.2f} h (travel {rc.travel_h:.2f} "
            f"+ activity {rc.activity_h:.2f} + contingency {rc.contingency_time_h:.2f} "
            f"+ reserve {reserves.time_reserve_h:.2f}); limit {time_limit:.2f} h"
        )

    return_feasible = route is not None and route.status == RouteStatus.OK
    if not return_feasible:
        reasons.append("Return route to habitat cannot be guaranteed.")

    uses_unknown = bool(route.uses_unknown_terrain) if route else False
    if uses_unknown:
        reasons.append("Route crosses cells with no valid terrain data.")

    hard_failure = (
        any(not c.ok for c in checks) or (not time_ok) or (not return_feasible)
    )
    if hard_failure:
        classification = SafetyClassification.DO_NOT_RECOMMEND
    elif uses_unknown:
        classification = SafetyClassification.CAUTION
    else:
        classification = SafetyClassification.ACCEPTABLE

    return SafetyAssessment(
        classification=classification,
        reasons=reasons,
        resource_checks=checks,
        return_feasible=return_feasible,
        time_ok=time_ok,
        uses_unknown_terrain=uses_unknown,
    )