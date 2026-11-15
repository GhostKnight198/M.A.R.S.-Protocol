"""Independent resource accounting for a proposed mission."""
from __future__ import annotations

from ..models import MissionConfig, ResourceConsumptionResult


def compute_resource_consumption(
    travel_h: float,
    activity_h: float,
    distance_m: float,
    config: MissionConfig,
) -> ResourceConsumptionResult:
    if travel_h < 0 or activity_h < 0 or distance_m < 0:
        raise ValueError("travel_h, activity_h, distance_m must be >= 0")

    r = config.resource_rates
    cf = config.contingency_fraction

    oxygen = r.oxygen_kg_per_hour_walking * travel_h \
        + r.oxygen_kg_per_hour_activity * activity_h
    water = r.water_l_per_hour_walking * travel_h \
        + r.water_l_per_hour_activity * activity_h
    energy = r.energy_wh_per_km * (distance_m / 1000.0) \
        + r.energy_wh_per_hour_activity * activity_h
    other = r.other_units_per_hour_walking * travel_h \
        + r.other_units_per_hour_activity * activity_h

    return ResourceConsumptionResult(
        oxygen_kg_used=oxygen,
        water_l_used=water,
        energy_wh_used=energy,
        other_units_used=other,
        travel_h=travel_h,
        activity_h=activity_h,
        contingency_oxygen_kg=oxygen * cf,
        contingency_water_l=water * cf,
        contingency_energy_wh=energy * cf,
        contingency_other_units=other * cf,
        contingency_time_h=(travel_h + activity_h) * cf,
    )