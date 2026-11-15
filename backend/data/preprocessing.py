"""Derive slope and roughness from elevation, preserving validity."""
from __future__ import annotations

import numpy as np

from mars_protocol.models import TerrainGrid


def derive_slope_deg(elevation_m: np.ndarray, resolution_m: float) -> np.ndarray:
    e = elevation_m.astype(np.float64)
    padded = np.pad(e, 1, mode="edge")
    a = padded[:-2, :-2]; b = padded[:-2, 1:-1]; c = padded[:-2, 2:]
    d = padded[1:-1, :-2];                      f = padded[1:-1, 2:]
    g = padded[2:, :-2];  h = padded[2:, 1:-1]; i = padded[2:, 2:]
    dzdx = ((c + 2*f + i) - (a + 2*d + g)) / (8.0 * resolution_m)
    dzdy = ((g + 2*h + i) - (a + 2*b + c)) / (8.0 * resolution_m)
    slope_rad = np.arctan(np.hypot(dzdx, dzdy))
    return np.degrees(slope_rad)


def derive_roughness_m(elevation_m: np.ndarray) -> np.ndarray:
    e = elevation_m.astype(np.float64)
    from scipy.ndimage import uniform_filter
    mean = uniform_filter(e, size=3)
    mean_sq = uniform_filter(e * e, size=3)
    var = np.maximum(mean_sq - mean * mean, 0.0)
    return np.sqrt(var)


def build_derived_layers(grid: TerrainGrid) -> TerrainGrid:
    slope = derive_slope_deg(grid.elevation_m, grid.resolution_m)
    rough = derive_roughness_m(grid.elevation_m)
    slope = np.where(grid.valid_mask, slope, 0.0)
    rough = np.where(grid.valid_mask, rough, 0.0)
    return TerrainGrid(
        elevation_m=grid.elevation_m,
        slope_deg=slope,
        roughness_m=rough,
        hazard_mask=grid.hazard_mask,
        valid_mask=grid.valid_mask,
        resolution_m=grid.resolution_m,
        origin_lat=grid.origin_lat,
        origin_lon=grid.origin_lon,
    )