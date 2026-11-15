# M.A.R.S. Protocol

Astronaut-centred Mars surface mission intelligence system. The first frontend milestone is a terrain-focused, responsive command-center demo built with React, Tailwind CSS, and Leaflet.

## Frontend demo

```bash
cd frontend
npm install
npm run dev
```

The dashboard includes mission selection, rough-terrain / ice-cap visualization modes, route and waypoint overlays, demo obstacle zones, simulated rover progress, and a responsive life-support/mission metrics panel.

**Demo limitations:** The map uses an illustrative local grid; it is not georeferenced Mars terrain data. Route, obstacle, terrain overlays, O₂ readings, and rover progress are simulated placeholders—not NASA-derived analysis, live telemetry, or operational safety guidance. They are intended to be replaced or driven by real data and the FastAPI service in later implementation work.
