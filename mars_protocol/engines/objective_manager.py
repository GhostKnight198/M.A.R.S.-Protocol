"""Objective prioritisation and validation helpers."""
from __future__ import annotations

from ..models import (
    PRIORITY_RANK,
    ScientificObjective,
    TerrainGrid,
    TraversabilityResult,
)


def sort_objectives(objectives: list[ScientificObjective]) -> list[ScientificObjective]:
    return sorted(
        objectives,
        key=lambda o: (not o.mandatory, -PRIORITY_RANK[o.priority], o.id),
    )


def validate_objective(
    objective: ScientificObjective,
    terrain: TerrainGrid,
    traversability: TraversabilityResult | None = None,
) -> list[str]:
    issues: list[str] = []
    if not terrain.contains(objective.cell):
        issues.append(
            f"Objective {objective.id}: target {objective.cell} outside terrain."
        )
        return issues
    if traversability is not None and traversability.hard_exclusion_mask[objective.cell]:
        issues.append(
            f"Objective {objective.id}: target cell is hard-excluded."
        )
    if objective.activity_duration_h < 0:
        issues.append(f"Objective {objective.id}: negative duration.")
    return issues


def mandatory_objectives(objs: list[ScientificObjective]) -> list[ScientificObjective]:
    return [o for o in objs if o.mandatory]


def optional_objectives(objs: list[ScientificObjective]) -> list[ScientificObjective]:
    return [o for o in objs if not o.mandatory]