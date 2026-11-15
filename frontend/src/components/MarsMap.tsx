import { CRS } from 'leaflet';
import type { LatLngExpression } from 'leaflet';
import { useState } from 'react';
import { Circle, CircleMarker, MapContainer, Polygon, Polyline, Tooltip, useMapEvents } from 'react-leaflet';
import { DEMO_OBSTACLES, DEMO_ROUTE, DEMO_WAYPOINTS } from '../data/demoMission';
import type { TerrainMode } from '../data/demoMission';

type Props = { terrainMode: TerrainMode; showRoute: boolean; showObstacles: boolean; showWaypoints: boolean; demoProgress: number };
const bounds: LatLngExpression[] = [[0, 0], [700, 1000]];

export default function MarsMap({ terrainMode, showRoute, showObstacles, showWaypoints, demoProgress }: Props) {
  const [cursor, setCursor] = useState<{ x: number; y: number } | null>(null);
  const roverPoint = pointAlongRoute(demoProgress / 100);
  const rockyRegions: LatLngExpression[][] = [[[470, 120], [600, 220], [560, 370], [430, 330]], [[340, 600], [430, 690], [350, 830], [245, 740]], [[570, 760], [650, 860], [580, 970], [500, 870]]];
  const iceRegions: LatLngExpression[][] = [[[520, 80], [650, 160], [610, 350], [500, 310]], [[260, 420], [360, 500], [300, 650], [190, 590]], [[470, 750], [580, 800], [540, 950], [430, 900]]];

  return <>
    <MapContainer crs={CRS.Simple} center={[350, 500]} zoom={-0.35} minZoom={-2} maxZoom={2} maxBounds={bounds} maxBoundsViscosity={0.9} className={`mars-map ${terrainMode === 'ice' ? 'mars-map-ice' : ''}`} zoomControl attributionControl={false}>
      <MapCursor onMove={(x, y) => setCursor({ x, y })} />
      {(terrainMode === 'rough' ? rockyRegions : iceRegions).map((region, index) => <Polygon key={`terrain-${index}`} positions={region} pathOptions={terrainMode === 'rough' ? { color: '#d88755', weight: 1.5, fillColor: '#d88755', fillOpacity: 0.23, dashArray: '5 5' } : { color: '#80bdd0', weight: 1.5, fillColor: '#79b5ca', fillOpacity: 0.25, dashArray: '5 5' }} />)}
      {showObstacles && DEMO_OBSTACLES.map((obstacle) => <Circle key={obstacle.id} center={obstacle.position} radius={obstacle.radius} pathOptions={{ color: '#fb7185', weight: 1.5, fillColor: '#fb7185', fillOpacity: 0.16, dashArray: '4 5' }}><Tooltip sticky>{obstacle.label} · demo obstacle zone</Tooltip></Circle>)}
      {showRoute && <Polyline positions={DEMO_ROUTE} pathOptions={{ color: '#ed7549', weight: 4, opacity: 0.95, lineCap: 'round', lineJoin: 'round' }} />}
      {showWaypoints && DEMO_WAYPOINTS.map((waypoint) => <CircleMarker key={waypoint.id} center={waypoint.position} radius={6} pathOptions={{ color: '#17191c', weight: 2, fillColor: '#e8b65b', fillOpacity: 1 }}><Tooltip direction="top" offset={[0, -7]}>{waypoint.label}</Tooltip></CircleMarker>)}
      <CircleMarker center={DEMO_ROUTE[0]} radius={7} pathOptions={{ color: '#17191c', weight: 2, fillColor: '#76c7a2', fillOpacity: 1 }}><Tooltip direction="top">Habitat · demo start</Tooltip></CircleMarker>
      <CircleMarker center={DEMO_ROUTE[DEMO_ROUTE.length - 1]} radius={8} pathOptions={{ color: '#17191c', weight: 2, fillColor: '#ed7549', fillOpacity: 1 }}><Tooltip direction="top">Science target · demo</Tooltip></CircleMarker>
      {demoProgress > 0 && <CircleMarker center={roverPoint} radius={8} pathOptions={{ color: '#ffffff', weight: 2, fillColor: '#ffffff', fillOpacity: 1 }}><Tooltip direction="top">Simulated rover position</Tooltip></CircleMarker>}
    </MapContainer>
    <div className="absolute right-3 top-3 z-[500] rounded-lg border border-white/10 bg-mars-950/85 px-2.5 py-2 font-mono text-[9px] text-mars-400 backdrop-blur-md sm:right-4 sm:top-4">{cursor ? `X ${cursor.x.toString().padStart(3, '0')} · Y ${cursor.y.toString().padStart(3, '0')}` : 'X 500 · Y 350'}</div>
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
