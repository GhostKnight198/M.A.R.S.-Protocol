"""Single source of truth for the Gale Crater demonstration mission."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class GaleCraterConfig:
    region_name: str = "Gale Crater, Northwestern Crater Floor"
    habitat_id: str = "MARS-HAB-01"
    habitat_lat: float = -4.59310427
    habitat_lon: float = 137.42009295

    operational_radius_m: float = 25_000.0
    extended_radius_m: float = 25_000.0

    mars_radius_m: float = 3_396_190.0

    mola_img_path: Path = REPO_ROOT / "data" / "raw" / "MOLA" / "topography" / "MEGT00N090HB.IMG"

    eva_time_limit_h: float = 8.0
    nominal_walking_speed_kmh: float = 1.0
    contingency_fraction: float = 0.10

    targets: list[dict] = field(default_factory=lambda: [
        {"id": "T01", "name": "Yellowknife Bay", "lat": -4.5950, "lon": 137.4417,
         "priority": "critical", "mandatory": True, "activity_h": 1.00,
         "rationale": "Fluvio-lacustrine mudstones; past aqueous activity (Grotzinger et al. 2014)."},
        {"id": "T02", "name": "Glenelg", "lat": -4.5800, "lon": 137.4020,
         "priority": "high", "mandatory": False, "activity_h": 0.75,
         "rationale": "Contact between striated Unit and hummocky plains; regional unconformity."},
        {"id": "T03", "name": "Kimberley", "lat": -4.6100, "lon": 137.4300,
         "priority": "medium", "mandatory": False, "activity_h": 0.75,
         "rationale": "Diverse sedimentary facies exposed on Gale floor."},
        {"id": "T04", "name": "Darwin", "lat": -4.5600, "lon": 137.4450,
         "priority": "medium", "mandatory": False, "activity_h": 0.50,
         "rationale": "Conglomerate outcrops indicative of fluvial transport."},
        {"id": "T05", "name": "Pahrump Hills", "lat": -4.6000, "lon": 137.4500,
         "priority": "low", "mandatory": False, "activity_h": 0.50,
         "rationale": "Murray formation base; fine-laminated mudstones."},
    ])


GALE_CRATER_CONFIG = GaleCraterConfig()