"""Converts raw terrain layers into a traversal cost surface."""
from __future__ import annotations

import numpy as np

from ..models import TerrainGrid, TraversabilityParams, TraversabilityResult


def compute_traversability(
    terrain: TerrainGrid,
    params: TraversabilityParams,
) -> TraversabilityResult:
    if params.max_slope_deg <= 0:
        raise ValueError("max_slope_deg must be positive")
    if params.roughness_reference_m <= 0:
        raise ValueError("roughness_reference_m must be positive")

    shape = terrain.shape
    warnings: list[str] = []

    slope_norm = np.clip(terrain.slope_deg / params.max_slope_deg, 0.0, 1.0)
    slope_penalty = params.slope_cost_weight * slope_norm ** 2

    rough_norm = np.maximum(0.0, terrain.roughness_m) / params.roughness_reference_m
    roughness_penalty = params.roughness_cost_weight * rough_norm

    cost = params.base_cost * (1.0 + slope_penalty + roughness_penalty)

    too_steep = terrain.slope_deg > params.max_slope_deg
    hazard = terrain.hazard_mask.astype(bool)
    hard_exclusion = too_steep | hazard

    unknown_mask = ~terrain.valid_mask.astype(bool)
    cost = np.where(unknown_mask, cost * params.unknown_terrain_cost_multiplier, cost)
    cost = np.where(hazard, cost * params.hazard_cost_multiplier, cost)

    if unknown_mask.any():
        warnings.append(
            f"{int(unknown_mask.sum())} cells have no valid terrain data; "
            f"cost inflated x{params.unknown_terrain_cost_multiplier:.1f}."
        )
    if hard_exclusion.any():
        warnings.append(
            f"{int(hard_exclusion.sum())} cells hard-excluded (slope > "
            f"{params.max_slope_deg:.1f}° or hazard)."
        )

    assert cost.shape == shape
    return TraversabilityResult(
        cost_grid=cost.astype(float),
        hard_exclusion_mask=hard_exclusion,
        unknown_mask=unknown_mask,
        slope_penalty=slope_penalty,
        roughness_penalty=roughness_penalty,
        params=params,
        warnings=warnings,
    )