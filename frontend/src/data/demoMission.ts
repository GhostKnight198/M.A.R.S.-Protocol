export type TerrainMode = 'rough' | 'ice';
// Illustrative local-grid coordinates only; these are not georeferenced Mars data.
export const DEMO_ROUTE: [number, number][] = [[520, 110], [535, 260], [470, 385], [420, 525], [320, 635], [285, 790], [220, 885]];
export const DEMO_WAYPOINTS = [
  { id: 'wp-1', label: 'Waypoint 01 · Ridge approach', position: DEMO_ROUTE[1] },
  { id: 'wp-2', label: 'Waypoint 02 · Traverse', position: DEMO_ROUTE[3] },
  { id: 'wp-3', label: 'Waypoint 03 · Science target', position: DEMO_ROUTE[6] },
];
export const DEMO_OBSTACLES = [
  { id: 'hazard-1', label: 'Rough ground', position: [470, 320] as [number, number], radius: 54 },
  { id: 'hazard-2', label: 'Rock field', position: [350, 730] as [number, number], radius: 47 },
  { id: 'hazard-3', label: 'Slope caution', position: [580, 570] as [number, number], radius: 42 },
];
