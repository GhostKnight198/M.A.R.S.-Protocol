# M.A.R.S. Protocol

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

## Future R&D direction

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



