"""Shared data models for the M.A.R.S. Protocol computational backend."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np


class RouteStatus(str, Enum):
    OK = "ok"
    NO_PATH = "no_path"
    DEGRADED = "degraded"


class MissionStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    RETURNING = "returning"
    COMPLETED = "completed"
    ABORTED = "aborted"
    INFEASIBLE = "infeasible"


class ObjectivePriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


PRIORITY_RANK: dict[ObjectivePriority, int] = {
    ObjectivePriority.CRITICAL: 4,
    ObjectivePriority.HIGH: 3,
    ObjectivePriority.MEDIUM: 2,
    ObjectivePriority.LOW: 1,
}


class SafetyClassification(str, Enum):
    ACCEPTABLE = "acceptable_under_current_assumptions"
    CAUTION = "caution"
    DO_NOT_RECOMMEND = "do_not_recommend"


class ReplanAction(str, Enum):
    CONTINUE = "continue_mission"
    MODIFY = "modify_mission"
    SKIP_OPTIONAL = "skip_optional_objective"
    RETURN = "return_to_habitat"
    ABORT = "abort_mission"


@dataclass
class TerrainGrid:
    elevation_m: np.ndarray
    slope_deg: np.ndarray
    roughness_m: np.ndarray
    hazard_mask: np.ndarray
    valid_mask: np.ndarray
    resolution_m: float
    origin_lat: float
    origin_lon: float

    def __post_init__(self) -> None:
        shape = self.elevation_m.shape
        if len(shape) != 2:
            raise ValueError("elevation_m must be 2D")
        for name, arr in (
            ("slope_deg", self.slope_deg),
            ("roughness_m", self.roughness_m),
            ("hazard_mask", self.hazard_mask),
            ("valid_mask", self.valid_mask),
        ):
            if arr.shape != shape:
                raise ValueError(f"{name} shape {arr.shape} != elevation {shape}")
        if self.resolution_m <= 0:
            raise ValueError("resolution_m must be positive")

    @property
    def shape(self) -> tuple[int, int]:
        return self.elevation_m.shape

    def contains(self, cell: tuple[int, int]) -> bool:
        r, c = cell
        return 0 <= r < self.shape[0] and 0 <= c < self.shape[1]

    def cell_to_latlon(self, cell: tuple[int, int]) -> tuple[float, float]:
        r, c = cell
        deg_lat = 1.0 / 111_320.0
        deg_lon = 1.0 / (111_320.0 * np.cos(np.radians(self.origin_lat)) + 1e-9)
        lat = self.origin_lat - r * self.resolution_m * deg_lat
        lon = self.origin_lon + c * self.resolution_m * deg_lon
        return lat, lon

    def latlon_to_cell(self, lat: float, lon: float) -> tuple[int, int]:
        deg_lat = 1.0 / 111_320.0
        deg_lon = 1.0 / (111_320.0 * np.cos(np.radians(self.origin_lat)) + 1e-9)
        r = int(round((self.origin_lat - lat) / (self.resolution_m * deg_lat)))
        c = int(round((lon - self.origin_lon) / (self.resolution_m * deg_lon)))
        return r, c


@dataclass
class TraversabilityParams:
    max_slope_deg: float = 25.0
    slope_cost_weight: float = 1.5
    roughness_cost_weight: float = 0.8
    roughness_reference_m: float = 0.5
    hazard_cost_multiplier: float = 9_999.0
    unknown_terrain_cost_multiplier: float = 3.0
    base_cost: float = 1.0


@dataclass
class ResourceBudget:
    oxygen_kg: float
    water_l: float
    energy_wh: float
    other_units: float

    def __post_init__(self) -> None:
        for name in ("oxygen_kg", "water_l", "energy_wh", "other_units"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be >= 0")

    def copy(self) -> "ResourceBudget":
        return ResourceBudget(self.oxygen_kg, self.water_l,
                              self.energy_wh, self.other_units)


@dataclass
class ResourceRates:
    oxygen_kg_per_hour_walking: float
    oxygen_kg_per_hour_activity: float
    water_l_per_hour_walking: float
    water_l_per_hour_activity: float
    energy_wh_per_km: float
    energy_wh_per_hour_activity: float
    other_units_per_hour_walking: float
    other_units_per_hour_activity: float


@dataclass
class ReserveRequirements:
    oxygen_kg_reserve: float
    water_l_reserve: float
    energy_wh_reserve: float
    other_units_reserve: float
    time_reserve_h: float


@dataclass
class ScientificObjective:
    id: str
    name: str
    description: str
    cell: tuple[int, int]
    lat: float
    lon: float
    priority: ObjectivePriority
    mandatory: bool
    activity_duration_h: float
    equipment_required: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("objective id must be non-empty")
        if self.activity_duration_h < 0:
            raise ValueError("activity_duration_h must be >= 0")


@dataclass
class Waypoint:
    row: int
    col: int
    lat: Optional[float] = None
    lon: Optional[float] = None
    kind: str = "transit"
    objective_id: Optional[str] = None


@dataclass
class Route:
    waypoints: list[Waypoint]
    distance_m: float
    travel_duration_h: float = 0.0
    terrain_cost: float = 0.0
    status: RouteStatus = RouteStatus.OK
    message: str = ""
    uses_unknown_terrain: bool = False


@dataclass
class MobilityParams:
    base_walking_speed_kmh: float = 1.0
    slope_speed_penalty_per_deg: float = 0.02
    roughness_speed_penalty_per_m: float = 0.20
    min_effective_speed_kmh: float = 0.10


@dataclass
class MissionConfig:
    habitat_id: str
    habitat_lat: float
    habitat_lon: float
    habitat_cell: tuple[int, int]
    eva_time_limit_h: float
    resource_budget: ResourceBudget
    resource_rates: ResourceRates
    reserves: ReserveRequirements
    traversability_params: TraversabilityParams
    mobility_params: MobilityParams
    contingency_fraction: float = 0.10
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.eva_time_limit_h <= 0:
            raise ValueError("eva_time_limit_h must be positive")
        if not (0.0 <= self.contingency_fraction < 1.0):
            raise ValueError("contingency_fraction must be in [0, 1)")


@dataclass
class ReportedObstacle:
    cell: tuple[int, int]
    radius_cells: int
    severity: str = "blocking"
    description: str = ""
    reported_at_elapsed_h: float = 0.0


@dataclass
class ReportedObservation:
    description: str
    cell: Optional[tuple[int, int]] = None
    reported_at_elapsed_h: float = 0.0


@dataclass
class MissionState:
    current_position: Waypoint
    habitat: Waypoint
    remaining_objectives: list[str]
    completed_objectives: list[str]
    route: Optional[Route]
    elapsed_h: float
    remaining_resources: ResourceBudget
    reported_obstacles: list[ReportedObstacle]
    reported_observations: list[ReportedObservation]
    status: MissionStatus
    version: int = 0
    history: list[str] = field(default_factory=list)


@dataclass
class TraversabilityResult:
    cost_grid: np.ndarray
    hard_exclusion_mask: np.ndarray
    unknown_mask: np.ndarray
    slope_penalty: np.ndarray
    roughness_penalty: np.ndarray
    params: TraversabilityParams
    warnings: list[str] = field(default_factory=list)


@dataclass
class SegmentMobility:
    from_cell: tuple[int, int]
    to_cell: tuple[int, int]
    distance_m: float
    effective_speed_kmh: float
    duration_h: float


@dataclass
class MobilityEstimate:
    segments: list[SegmentMobility]
    total_distance_m: float
    total_duration_h: float


@dataclass
class ResourceConsumptionResult:
    oxygen_kg_used: float
    water_l_used: float
    energy_wh_used: float
    other_units_used: float
    travel_h: float
    activity_h: float
    contingency_oxygen_kg: float
    contingency_water_l: float
    contingency_energy_wh: float
    contingency_other_units: float
    contingency_time_h: float


@dataclass
class ResourceCheck:
    resource: str
    required: float
    available: float
    reserve: float
    ok: bool


@dataclass
class SafetyAssessment:
    classification: SafetyClassification
    reasons: list[str]
    resource_checks: list[ResourceCheck]
    return_feasible: bool
    time_ok: bool
    uses_unknown_terrain: bool


@dataclass
class MissionPlan:
    ordered_objective_ids: list[str]
    route: Route
    travel_h: float
    activity_h: float
    resource_consumption: ResourceConsumptionResult
    feasible: bool
    warnings: list[str] = field(default_factory=list)


@dataclass
class ReplanningResult:
    action: ReplanAction
    updated_state: MissionState
    updated_route: Optional[Route]
    safety: SafetyAssessment
    reasons: list[str]