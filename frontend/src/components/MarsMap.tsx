import { CRS, divIcon } from 'leaflet';
import type { LatLngExpression } from 'leaflet';
import { useState } from 'react';
import { Circle, CircleMarker, MapContainer, Marker, Polygon, Polyline, Tooltip, useMapEvents } from 'react-leaflet';
import { DEMO_OBSTACLES, DEMO_ROUTE, DEMO_WAYPOINTS } from '../data/demoMission';
import type { TerrainMode } from '../data/demoMission';

type Props = { terrainMode: TerrainMode; showRoute: boolean; showObstacles: boolean; showWaypoints: boolean; demoProgress: number };
const bounds: LatLngExpression[] = [[0, 0], [700, 1000]];

const habitatIcon = divIcon({
  className: 'mars-marker mars-marker-habitat',
  html: '<span class="habitat-marker__glow"></span><span class="habitat-marker__body"><svg viewBox="0 0 32 32" aria-hidden="true"><path d="M4 23h24M7 23V17l9-8 9 8v6M12 23v-5h8v5M16 9V5m-3 0h6"/><path d="M5 26h22"/></svg></span>',
  iconSize: [42, 48],
  iconAnchor: [21, 40],
});
const destinationIcon = divIcon({
  className: 'mars-marker mars-marker-destination',
  html: '<span class="destination-marker__pin"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/></svg></span>',
  iconSize: [38, 46],
  iconAnchor: [19, 42],
});
const astronautIcon = divIcon({
  className: 'mars-marker mars-marker-astronaut',
  html: '<span class="astronaut-marker__pulse"></span><span class="astronaut-marker__body"><svg viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="9" r="5"/><path d="M11 8h10M10 16l-4 5 4 2 3-3v7h6v-7l3 3 4-2-4-5c-1-2-3-3-5-3h-2c-2 0-4 1-5 3Z"/><path d="m14 26-2 3m6-3 2 3"/></svg></span>',
  iconSize: [46, 46],
  iconAnchor: [23, 23],
});

export default function MarsMap({ terrainMode, showRoute, showObstacles, showWaypoints, demoProgress }: Props) {
  const [cursor, setCursor] = useState<{ x: number; y: number } | null>(null);
  const astronautPoint = pointAlongRoute(demoProgress / 100);
  const terrainLabel = terrainMode === 'rough' ? 'Rocky / rough terrain' : 'Icy terrain';
  const rockyRegions: LatLngExpression[][] = [[[470, 120], [600, 220], [560, 370], [430, 330]], [[340, 600], [430, 690], [350, 830], [245, 740]], [[570, 760], [650, 860], [580, 970], [500, 870]]];
  const iceRegions: LatLngExpression[][] = [[[520, 80], [650, 160], [610, 350], [500, 310]], [[260, 420], [360, 500], [300, 650], [190, 590]], [[470, 750], [580, 800], [540, 950], [430, 900]]];

  return <>
    <MapContainer crs={CRS.Simple} center={[350, 500]} zoom={-0.35} minZoom={-2} maxZoom={2} maxBounds={bounds} maxBoundsViscosity={0.9} className={`mars-map ${terrainMode === 'ice' ? 'mars-map-ice' : ''}`}>
      <MapCursor onMove={(x, y) => setCursor({ x, y })} />
      {(terrainMode === 'rough' ? rockyRegions : iceRegions).map((region, index) => <Polygon key={`terrain-${index}`} positions={region} pathOptions={terrainMode === 'rough' ? { color: '#d88755', weight: 1, fillColor: '#d88755', fillOpacity: 0.19 } : { color: '#80bdd0', weight: 1, fillColor: '#80bdd0', fillOpacity: 0.2 }} />)}
      {showObstacles && DEMO_OBSTACLES.map((obstacle) => <Circle key={obstacle.id} center={obstacle.position} radius={obstacle.radius} pathOptions={{ color: '#fb7185', weight: 1.5, fillColor: '#fb7185', fillOpacity: 0.12, dashArray: '5 5' }}><Tooltip>{obstacle.label}</Tooltip></Circle>)}
      {showRoute && <Polyline positions={DEMO_ROUTE} pathOptions={{ color: '#ed7549', weight: 4, opacity: 0.95, lineCap: 'round', lineJoin: 'round' }} />}
      {showWaypoints && DEMO_WAYPOINTS.map((waypoint) => <CircleMarker key={waypoint.id} center={waypoint.position} radius={6} pathOptions={{ color: '#17191c', weight: 2, fillColor: '#e8b65b', fillOpacity: 1 }}><Tooltip direction="top">{waypoint.label}</Tooltip></CircleMarker>)}
      <Marker position={DEMO_ROUTE[0]} icon={habitatIcon} zIndexOffset={500}><Tooltip direction="top" offset={[0, -30]}>MARS-HAB-01 · Home base</Tooltip></Marker>
      <Marker position={DEMO_ROUTE[DEMO_ROUTE.length - 1]} icon={destinationIcon} zIndexOffset={400}><Tooltip direction="top" offset={[0, -32]}>Scientific target · destination</Tooltip></Marker>
      {demoProgress > 0 && <Marker position={astronautPoint} icon={astronautIcon} zIndexOffset={1000}><Tooltip direction="top">Astronaut · simulated EVA location</Tooltip></Marker>}
    </MapContainer>
    <div className="map-terrain-card" aria-live="polite"><span className={`terrain-swatch ${terrainMode === 'ice' ? 'terrain-swatch-ice' : ''}`} /><span><span className="map-terrain-label">Terrain type</span><strong>{terrainLabel}</strong></span></div>
    <div className="map-legend" aria-label="Map marker legend"><span><i className="legend-home" />Home base</span><span><i className="legend-target" />Target</span><span><i className="legend-crew" />Astronaut</span></div>
    <div className="absolute right-3 top-3 z-[500] rounded-lg border border-white/10 bg-mars-950/85 px-2.5 py-2 font-mono text-[9px] text-mars-400 backdrop-blur-md sm:right-4 sm:top-4">{cursor ? `[${cursor.x} m, ${cursor.y} m]` : 'LOCAL GRID · METRES'}</div>
  </>;
}
function MapCursor({ onMove }: { onMove: (x: number, y: number) => void }) {
  useMapEvents({ mousemove: (event) => onMove(Math.round(event.latlng.lng), Math.round(event.latlng.lat)) });
  return null;
}
function pointAlongRoute(progress: number): LatLngExpression {
  const clamped = Math.max(0, Math.min(1, progress));
  const scaled = clamped * (DEMO_ROUTE.length - 1);
  const index = Math.min(Math.floor(scaled), DEMO_ROUTE.length - 2);
  const fraction = scaled - index;
  const from = DEMO_ROUTE[index];
  const to = DEMO_ROUTE[index + 1];
  return [from[0] + (to[0] - from[0]) * fraction, from[1] + (to[1] - from[1]) * fraction];
}
