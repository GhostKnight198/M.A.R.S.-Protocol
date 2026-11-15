"""Load real NASA terrain datasets into the TerrainGrid contract."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio

from mars_protocol.models import TerrainGrid

log = logging.getLogger(__name__)


@dataclass
class ProvenanceRecord:
    dataset: str
    source_path: str
    native_resolution_m: float
    native_crs: str
    observation_note: str = ""
    limitations: str = ""


_TILE_MIN_LAT = -44.0
_TILE_MAX_LAT = 0.0
_TILE_MIN_LON = 90.0
_TILE_MAX_LON = 180.0
_TILE_PX_PER_DEG = 128.0
_TILE_ROWS = 5632
_TILE_COLS = 11520
_TILE_RES_M = 463.14


def _latlon_to_pixel(lat: float, lon: float) -> tuple[float, float]:
    row = (_TILE_MAX_LAT - lat) * _TILE_PX_PER_DEG
    col = (lon - _TILE_MIN_LON) * _TILE_PX_PER_DEG
    return row, col


def _read_tile_robustly(img_path: Path) -> np.ndarray:
    """Read entire MOLA tile, handling PDS MSB_INTEGER endianness explicitly."""
    try:
        with rasterio.open(img_path) as src:
            arr = src.read(1)
            if arr.shape != (_TILE_ROWS, _TILE_COLS):
                log.warning(
                    "Rasterio read shape %s != expected (%d, %d)",
                    arr.shape, _TILE_ROWS, _TILE_COLS,
                )
    except Exception as e:
        log.warning("Rasterio read failed (%s), trying raw binary parse", e)
        arr = None

    if arr is None or arr.max() > 30000 or arr.min() < -30000:
        # Rasterio likely misread. Parse raw .img binary: 16-bit big-endian signed.
        log.info("Falling back to raw binary parse (MSB int16).")
        with open(img_path, "rb") as f:
            raw = f.read()
        expected_bytes = _TILE_ROWS * _TILE_COLS * 2
        if len(raw) < expected_bytes:
            raise ValueError(
                f"MOLA .img too small: {len(raw)} bytes < {expected_bytes} expected"
            )
        arr = np.frombuffer(
            raw[:expected_bytes], dtype=">i2"
        ).astype(np.int32).reshape(_TILE_ROWS, _TILE_COLS)

    return arr.astype(np.float64)


def load_mola_megdr(
    img_path: Path,
    study_lat: float,
    study_lon: float,
    operational_radius_m: float,
) -> tuple[TerrainGrid, ProvenanceRecord]:
    img_path = Path(img_path)
    if not img_path.exists():
        raise FileNotFoundError(f"MOLA file not found: {img_path}")

    log.info("Loading MOLA: %s", img_path)
    full_tile = _read_tile_robustly(img_path)
    log.info(
        "Full tile loaded: shape=%s range=%.1f..%.1f",
        full_tile.shape, float(full_tile.min()), float(full_tile.max()),
    )

    radius_px = max(5, int(round(operational_radius_m / _TILE_RES_M)))
    c_row, c_col = _latlon_to_pixel(study_lat, study_lon)

    row_off = max(0, int(round(c_row - radius_px)))
    col_off = max(0, int(round(c_col - radius_px)))
    height = min(int(round(2 * radius_px)), _TILE_ROWS - row_off)
    width = min(int(round(2 * radius_px)), _TILE_COLS - col_off)

    data = full_tile[row_off:row_off + height, col_off:col_off + width]

    valid = (data > -32000.0) & (data < 30000.0)
    elevation = np.where(valid, data, np.nan)

    slope = np.zeros_like(elevation, dtype=np.float64)
    roughness = np.zeros_like(elevation, dtype=np.float64)
    hazard = np.zeros_like(elevation, dtype=bool)

    origin_lat = _TILE_MAX_LAT - row_off / _TILE_PX_PER_DEG
    origin_lon = _TILE_MIN_LON + col_off / _TILE_PX_PER_DEG

    grid = TerrainGrid(
        elevation_m=np.nan_to_num(elevation, nan=0.0),
        slope_deg=slope,
        roughness_m=roughness,
        hazard_mask=hazard,
        valid_mask=valid,
        resolution_m=_TILE_RES_M,
        origin_lat=origin_lat,
        origin_lon=origin_lon,
    )
    provenance = ProvenanceRecord(
        dataset="MOLA MEGDR",
        source_path=str(img_path),
        native_resolution_m=_TILE_RES_M,
        native_crs="simple_cylindrical planetographic (degrees)",
        observation_note="Mars Global Surveyor MOLA — 1997-2006 observations.",
        limitations=(
            f"Native resolution ~463 m/px. Grid cropped to "
            f"{2*operational_radius_m/1000:.0f} km x "
            f"{2*operational_radius_m/1000:.0f} km "
            f"study area ({grid.shape[0]}x{grid.shape[1]} px). "
            f"No upsampling performed."
        ),
    )
    log.info(
        "MOLA grid loaded: shape=%s valid=%d/%d elev=%.1f..%.1f",
        grid.shape, int(valid.sum()), valid.size,
        float(elevation[valid].min()) if valid.any() else 0.0,
        float(elevation[valid].max()) if valid.any() else 0.0,
    )
    return grid, provenance