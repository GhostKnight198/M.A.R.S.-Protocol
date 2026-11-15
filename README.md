# M.A.R.S. Protocol


**Mars Surface Mission Intelligence — NASA Space Apps Challenge 2026**

*Interplanetary Survival Guide: Martian Map*

---

## What we built for the hackathon

M.A.R.S. Protocol is an astronaut-centred mission intelligence system. It does not
display a Mars map or compute a shortest path. It answers a harder operational
question:

> Given a habitat, a scientific objective, real Martian terrain, and a finite EVA
> budget — is the excursion actually feasible, and how should the plan adapt when
> conditions change?

The system is built to **reject an infeasible mission rather than manufacture a
solution**.

### Implemented and tested end-to-end on real NASA MOLA topography

- **Terrain ingestion** — MOLA MEGDR at native ~463 m/px, cropped to a Gale Crater
  study area. No upsampling; resampling cannot create spatial information.
- **Derived layers** — slope (Horn 3×3 gradient) and surface roughness (local
  variance) computed from elevation.
- **Traversability engine** — terrain cost surface with hard exclusions (steep
  slope, hazards) kept architecturally separate from soft difficulty costs. Cells
  with no valid observation are carried through as unknown and penalised, never
  silently treated as safe.
- **A\* and weighted A\* route planner** — 4/8-connectivity, diagonal corner-cut
  prevention, admissible heuristic, explicit no-path detection. Returns structured
  route objects, not bare coordinate lists.
- **Human mobility model** — configurable slope and roughness speed penalties;
  segment-level and total travel time.
- **Resource and EVA accounting** — oxygen, water, electrical energy, and other
  consumables tracked independently, each with reserve and contingency
  requirements. Never collapsed into a single score.
- **Objective manager** — priority ranking, mandatory/optional split, target
  validation.
- **Mission planner** — mandatory-first selection, greedy optional insertion,
  full-mission feasibility including the return leg.
- **Safety and feasibility engine** — three-tier classification
  (`acceptable` / `caution` / `do_not_recommend`) with a specific reason attached
  to every warning and every rejection.
- **Dynamic replanning** — an astronaut obstacle report mutates the planning
  environment and triggers a full reassessment of the remaining mission,
  including return feasibility. Replanning is scoped to the mission, not the
  route: dropping an optional objective to preserve a safe return is a
  first-class outcome.
- **Mission report generator** — structured dictionary and human-readable text,
  including provenance and limitations.

### System's Architecture
================================================================================
                          M.A.R.S. PROTOCOL
                 Mars Surface Mission Intelligence
================================================================================

                    MISSION CONFIGURATION
        habitat · targets · EVA budget · resources · reserves
                              |
                              v
                    TERRAIN INGESTION
        MOLA MEGDR · native ~463 m/px · Gale Crater crop
        valid_mask marks no-data cells explicitly
                              |
                              v
                     DERIVED LAYERS
             slope (Horn 3×3) · roughness (local variance)
                              |
                              v
                  TRAVERSABILITY ENGINE
        soft cost grid · hard-exclusion mask · unknown mask
        hard and soft kept architecturally separate
                              |
              +---------------+---------------+
              |                               |
              v                               v
        ROUTE PLANNER                   MOBILITY MODEL
        A* / weighted A*                effective speed
        corner-cut prevention           segment + total time
        no-path detection
              |                               |
              +---------------+---------------+
                              |
                              v
                  RESOURCE & EVA ACCOUNTING
        O2 · H2O · energy · other  (tracked independently)
        contingency fraction applied per resource
                              |
                              v
                    OBJECTIVE MANAGER
             priority ranking · target validation
             mandatory / optional split
                              |
                              v
                     MISSION PLANNER
        mandatory first · greedy optional insertion
        full round-trip feasibility including return
        optional objectives rejected when infeasible
                              |
                              v
                SAFETY & FEASIBILITY ENGINE
        per-resource checks · return feasibility · time
        3-tier: acceptable · caution · do-not-recommend
        every warning and rejection carries a reason
                              |
                              v
                       MISSION STATE
        position · objectives · route · resources
        obstacles · status · version · history
                              |
                              v
                DYNAMIC REPLANNING ENGINE
        obstacle -> terrain update -> full reassessment
        continue · modify · skip-optional · return · abort
        scoped to mission, not to route
                              |
                              v
                  MISSION REPORT GENERATOR
        plan · consumption · safety · provenance · limits
        structured dict + human-readable text
                              |
                              v
                         OUTPUT
================================================================================
SEPARATION OF CONCERNS (enforced structurally)
--------------------------------------------------------------------------------
  Traversability  ≠  route planning
  Mobility        ≠  resource accounting
  Resource model  ≠  safety assessment
  Route feasibility  ≠  mission feasibility
  Replanning      ≠  merely finding another path

  Each engine is independently testable, shares state only through the
  documented TerrainGrid / TraversabilityResult / Route / MissionState
  contracts, and can be replaced without reworking the others.

DATA CONTRACTS
--------------------------------------------------------------------------------
  TerrainGrid          elevation · slope · roughness · hazard_mask
                       valid_mask · resolution_m · origin_lat/lon
  TraversabilityResult cost_grid · hard_exclusion_mask · unknown_mask
                       slope_penalty · roughness_penalty · params
  Route                waypoints · distance_m · travel_duration_h
                       terrain_cost · status · uses_unknown_terrain
  MissionState         current_position · habitat · objectives
                       route · elapsed_h · remaining_resources
                       obstacles · observations · status · version

PROVENANCE AND INTEGRITY (enforced throughout)
--------------------------------------------------------------------------------
  · Every dataset recorded with source, native resolution, observation date
  · Every scenario parameter labelled as scenario-defined, not observed
  · Every derived layer traceable to its source elevation
  · Every warning and rejection carries a specific numerical reason
  · No upsampling — native MOLA resolution preserved
  · No fabricated data — unknown terrain carried through as unknown
  · No silent assumptions — provenance surfaced in every mission report
================================================================================
  

### Scaffolded but not integrated end-to-end within the hackathon window

- **FastAPI surface** — endpoints defined (`/health`, `/pipeline/run`,
  `/mission/plan`, `/mission/report`, `/mission/provenance`); frontend
  integration in progress.
- **CTX imagery ingest** — regional geological context.
- **HiRISE DTM ingest** — high-resolution local terrain refinement.
- **CRISM spectral observations** — mineralogical justification for target sites.

These were scoped out under time constraints. The architecture is deliberately
dataset-agnostic: the traversability, mobility, and planning engines consume a
documented terrain contract, so higher-resolution data and additional datasets
can be substituted without reworking the intelligence layer.

---


### Future R&D direction

What we intend to develop independently beyond the hackathon — this is the
roadmap, not a claim about the current build:

- **Full dataset integration.** CTX, HiRISE DTM, and CRISM ingest into the
  existing pipeline, giving the intelligence layer access to regional geological
  context, sub-metre local terrain, and mineralogical target justification.
  MOLA supplies the broad-scale elevation baseline; HiRISE refines it in patch
  form where coverage exists; CTX and CRISM feed scientific target selection
  rather than terrain cost.
- **Multi-astronaut and multi-mission operations.** The current build models one
  astronaut, one habitat, one mission. The next architectural step generalises
  this to crews, shared resources, and concurrent excursions with conflict
  resolution.
- **Unified tabbed astronaut interface.** One application, five tabs (mission
  setup, Mars explorer, route & traversability, EVA operations, mission report)
  sharing a single mission state.
- **Live environmental modelling.** Atmospheric conditions and radiation budget
  integrated into the feasibility engine, with forecast-driven replanning.
- **Higher-fidelity mobility model.** Field-validated EVA suit performance data
  replacing the current scenario-based mathematical approximation.
- **Alternative-route comparison.** Presenting a small set of Pareto-optimal
  routes by safety, distance, and resource margin, rather than a single
  recommendation.

---



