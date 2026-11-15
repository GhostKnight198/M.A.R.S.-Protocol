import { useEffect, useState, type ReactNode } from 'react';
import { Activity, AlertTriangle, ArrowDownRight, ArrowUpRight, Check, ChevronDown, Compass, Crosshair, Layers3, LocateFixed, MapPin, Mountain, Pause, Play, Radio, RotateCcw, Signal, Snowflake, Wind } from 'lucide-react';
import MarsMap from './components/MarsMap';
import type { TerrainMode } from './data/demoMission';

const missions = ['Gale Crater Traverse', 'North Polar Survey', 'Olympus Foothills Recon'];
function formatElapsed(seconds: number) {
  const hours = Math.floor(seconds / 3600).toString().padStart(2, '0');
  const minutes = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
  return `${hours}:${minutes}:${(seconds % 60).toString().padStart(2, '0')}`;
}

export default function App() {
  const [mission, setMission] = useState(missions[0]);
  const [terrainMode, setTerrainMode] = useState<TerrainMode>('rough');
  const [showRoute, setShowRoute] = useState(true);
  const [showObstacles, setShowObstacles] = useState(true);
  const [showWaypoints, setShowWaypoints] = useState(true);
  const [demoMode, setDemoMode] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const oxygen = Math.max(0, 100 - Math.floor(elapsed / 110));
  const progress = Math.min(100, Math.floor((elapsed / 5400) * 100));

  useEffect(() => {
    if (!demoMode) return;
    const timer = window.setInterval(() => setElapsed((seconds) => seconds + 1), 1000);
    return () => window.clearInterval(timer);
  }, [demoMode]);

  const toggleDemo = () => {
    if (!demoMode) setElapsed(0);
    setDemoMode((active) => !active);
  };
  const resetDemo = () => { setDemoMode(false); setElapsed(0); };

  return <main className="min-h-screen bg-mars-950 px-3 py-3 text-mars-300 sm:px-5 sm:py-5">
    <div className="mx-auto flex min-h-[calc(100vh-1.5rem)] max-w-[1680px] flex-col gap-3 sm:min-h-[calc(100vh-2.5rem)] sm:gap-4">
      <header className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-white/[0.07] bg-mars-900 px-4 py-3 shadow-panel sm:px-6">
        <div className="flex min-w-0 items-center gap-3"><div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-ember/15 text-ember"><Crosshair size={21} /></div><div><p className="truncate text-sm font-semibold tracking-[0.16em] text-white">M.A.R.S. PROTOCOL</p><p className="mt-0.5 text-[11px] uppercase tracking-[0.18em] text-mars-500">Surface operations · demo console</p></div></div>
        <div className="flex items-center gap-3"><div className="hidden items-center gap-2 rounded-full border border-safe/20 bg-safe/[0.07] px-3 py-1.5 text-[11px] font-medium text-safe sm:flex"><span className="h-1.5 w-1.5 rounded-full bg-safe" /> SYSTEM NOMINAL</div><button type="button" onClick={toggleDemo} className={`inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-semibold transition ${demoMode ? 'bg-ember text-white hover:bg-ember/90' : 'bg-white text-mars-950 hover:bg-mars-300'}`}>{demoMode ? <Pause size={15} /> : <Play size={15} fill="currentColor" />}{demoMode ? 'Pause demo' : 'Start demo'}</button></div>
      </header>

      <section className="grid flex-1 grid-cols-1 gap-3 lg:grid-cols-[250px_minmax(0,1fr)_250px] lg:gap-4">
        <aside className="order-2 flex flex-col gap-3 rounded-2xl border border-white/[0.07] bg-mars-900 p-4 shadow-panel lg:order-1">
          <div className="flex items-center justify-between"><div><p className="eyebrow">Mission control</p><h1 className="mt-1 text-lg font-semibold text-white">Terrain planner</h1></div><div className="rounded-lg bg-mars-800 p-2 text-mars-400"><Compass size={17} /></div></div>
          <label className="mt-2 block"><span className="eyebrow mb-2 block">Active mission</span><span className="relative block"><select value={mission} onChange={(event) => setMission(event.target.value)} className="w-full appearance-none rounded-xl border border-white/[0.08] bg-mars-850 px-3 py-3 pr-9 text-xs font-medium text-mars-300 outline-none focus:border-ember/60">{missions.map((item) => <option key={item}>{item}</option>)}</select><ChevronDown size={15} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-mars-500" /></span></label>
          <div className="mt-2"><div className="mb-2 flex items-center justify-between"><span className="eyebrow">Terrain mode</span><Layers3 size={14} className="text-mars-500" /></div><div className="grid grid-cols-2 gap-2"><button type="button" onClick={() => setTerrainMode('rough')} className={`terrain-button ${terrainMode === 'rough' ? 'terrain-button-active' : ''}`}><Mountain size={16} /><span>Rough terrain</span></button><button type="button" onClick={() => setTerrainMode('ice')} className={`terrain-button ${terrainMode === 'ice' ? 'terrain-button-active terrain-button-ice' : ''}`}><Snowflake size={16} /><span>Ice cap</span></button></div><p className="mt-2.5 text-[11px] leading-relaxed text-mars-500">{terrainMode === 'rough' ? 'Illustrative rocky ridges and uneven ground overlays.' : 'Illustrative ice-field overlays for demo mode.'}</p></div>
          <div className="mt-2 border-t border-white/[0.07] pt-4"><p className="eyebrow mb-3">Map layers</p><LayerToggle label="Planned route" color="bg-ember" checked={showRoute} onChange={setShowRoute} /><LayerToggle label="Waypoints" color="bg-signal" checked={showWaypoints} onChange={setShowWaypoints} /><LayerToggle label="Obstacle zones" color="bg-rose-400" checked={showObstacles} onChange={setShowObstacles} /></div>
          <div className="mt-auto rounded-xl border border-signal/15 bg-signal/[0.06] p-3"><div className="flex items-center gap-2 text-signal"><AlertTriangle size={15} /><span className="text-[10px] font-semibold uppercase tracking-[0.14em]">Demo data notice</span></div><p className="mt-2 text-[11px] leading-relaxed text-mars-500">Map overlays and life-support readings are simulated placeholders, not mission-ready measurements.</p></div>
        </aside>

        <section className="order-1 flex min-h-[430px] flex-col overflow-hidden rounded-2xl border border-white/[0.07] bg-mars-900 shadow-panel lg:order-2 lg:min-h-[620px]">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.07] px-4 py-3.5 sm:px-5"><div className="flex min-w-0 items-center gap-3"><div className="rounded-lg bg-ember/10 p-2 text-ember"><MapPin size={16} /></div><div className="min-w-0"><h2 className="truncate text-sm font-semibold text-white">{mission}</h2><p className="mt-0.5 text-[10px] uppercase tracking-[0.13em] text-mars-500">Mars local grid · illustrative scene</p></div></div><span className="flex items-center gap-1.5 rounded-full border border-signal/20 bg-signal/[0.06] px-2.5 py-1.5 text-[10px] font-medium text-signal"><Activity size={12} /> TERRAIN DEMO</span></div>
          <div className="relative min-h-[330px] flex-1"><MarsMap terrainMode={terrainMode} showRoute={showRoute} showObstacles={showObstacles} showWaypoints={showWaypoints} demoProgress={progress} /><div className="pointer-events-none absolute left-3 top-3 z-[500] rounded-lg border border-white/10 bg-mars-950/85 px-3 py-2 backdrop-blur-md sm:left-4 sm:top-4"><p className="text-[9px] uppercase tracking-[0.16em] text-mars-500">Surface status</p><p className="mt-1 flex items-center gap-1.5 text-[11px] font-medium text-mars-300"><span className="h-1.5 w-1.5 rounded-full bg-safe" /> TERRAIN MODEL ACTIVE</p></div><div className="pointer-events-none absolute bottom-3 left-3 z-[500] rounded-lg border border-white/10 bg-mars-950/85 px-3 py-2 backdrop-blur-md sm:bottom-4 sm:left-4"><p className="text-[9px] uppercase tracking-[0.15em] text-mars-500">Map coordinates</p><p className="mt-1 font-mono text-[11px] text-mars-300">LOCAL GRID · {terrainMode === 'rough' ? 'RG-04' : 'IC-02'}</p></div><div className="pointer-events-none absolute bottom-3 right-3 z-[500] flex items-center gap-2 rounded-lg border border-white/10 bg-mars-950/85 px-3 py-2 text-[10px] text-mars-400 backdrop-blur-md sm:bottom-4 sm:right-4"><span className="h-2 w-2 rounded-full bg-ember" /> ROUTE <span className="mx-1 text-mars-700">|</span><span className="h-2 w-2 rounded-full bg-rose-400" /> HAZARD</div></div>
        </section>

        <aside className="order-3 flex flex-col gap-3 rounded-2xl border border-white/[0.07] bg-mars-900 p-4 shadow-panel">
          <div className="flex items-center justify-between"><div><p className="eyebrow">Life support</p><h2 className="mt-1 text-lg font-semibold text-white">O₂ telemetry</h2></div><div className="rounded-lg bg-safe/[0.1] p-2 text-safe"><Wind size={17} /></div></div>
          <div className="flex items-center gap-4 rounded-xl border border-white/[0.06] bg-mars-850 p-4"><div className="relative h-[154px] w-7 overflow-hidden rounded-full border border-white/10 bg-mars-950 p-1"><div className="absolute inset-x-1 bottom-1 rounded-full bg-gradient-to-t from-safe to-[#b4e7ca] transition-all duration-700" style={{ height: `${Math.max(3, oxygen - 4)}%` }} /><div className="gauge-ticks absolute inset-0 z-10 rounded-full" /></div><div><p className="text-3xl font-semibold tracking-tight text-white">{oxygen}<span className="ml-1 text-base text-mars-500">%</span></p><p className="mt-1 text-[10px] uppercase tracking-[0.15em] text-mars-500">Simulated reserve</p><div className="mt-4 flex items-center gap-1.5 text-[10px] font-medium text-safe"><Check size={13} /> WITHIN DEMO LIMITS</div><p className="mt-1.5 text-[10px] text-mars-500">Illustrative only · no validated threshold</p></div></div>
          <div className="grid grid-cols-2 gap-2"><TelemetryStat label="Pressure" value="—" unit="kPa" icon={<Signal size={13} />} /><TelemetryStat label="Power" value="—" unit="%" icon={<Activity size={13} />} /></div>
          <div className="mt-auto rounded-xl border border-white/[0.06] bg-mars-850 p-3.5"><div className="flex items-center justify-between"><span className="text-[11px] font-medium text-mars-400">Route progress</span><span className="font-mono text-xs text-white">{progress}%</span></div><div className="mt-3 h-1.5 overflow-hidden rounded-full bg-mars-700"><div className="h-full rounded-full bg-ember transition-all duration-700" style={{ width: `${progress}%` }} /></div><div className="mt-2.5 flex items-center justify-between text-[10px] text-mars-500"><span>START</span><span>SCIENCE TARGET</span></div></div>
          <div className="flex items-center justify-between rounded-lg px-1 text-[10px] text-mars-500"><span className="flex items-center gap-1.5"><Radio size={12} /> Telemetry source</span><span className="text-signal">SIMULATED</span></div>
        </aside>
      </section>

      <footer className="grid grid-cols-2 gap-2 rounded-2xl border border-white/[0.07] bg-mars-900 p-3 shadow-panel sm:grid-cols-4 sm:gap-0 sm:px-5 sm:py-4"><Metric label="Mission elapsed" value={formatElapsed(elapsed)} icon={<Activity size={15} />} accent="text-ember" /><Metric label="Est. mission time" value="01h 30m" icon={<ArrowUpRight size={15} />} accent="text-mars-300" /><Metric label="Est. route distance" value="12.4 km" icon={<ArrowDownRight size={15} />} accent="text-mars-300" /><div className="flex items-center justify-between border-t border-white/[0.07] px-2 pt-3 sm:border-l sm:border-t-0 sm:px-5 sm:pt-0"><div><p className="eyebrow">Demo mode</p><p className="mt-1 text-[11px] text-mars-400">Simulated traversal</p></div><button type="button" role="switch" aria-checked={demoMode} aria-label="Toggle demo mode" onClick={toggleDemo} className={`relative h-6 w-11 rounded-full transition ${demoMode ? 'bg-ember' : 'bg-mars-700'}`}><span className={`absolute top-1 h-4 w-4 rounded-full bg-white transition-all ${demoMode ? 'left-6' : 'left-1'}`} /></button><button type="button" onClick={resetDemo} aria-label="Reset demo" className="ml-2 rounded-lg p-2 text-mars-500 transition hover:bg-mars-800 hover:text-white"><RotateCcw size={14} /></button></div></footer>
      <div className="flex items-center justify-center gap-2 pb-1 text-center text-[9px] uppercase tracking-[0.14em] text-mars-700"><LocateFixed size={11} /> Planning visualization only · Not for operational use</div>
    </div>
  </main>;
}

function LayerToggle({ label, color, checked, onChange }: { label: string; color: string; checked: boolean; onChange: (value: boolean) => void }) {
  return <label className="flex cursor-pointer items-center justify-between py-2 text-xs text-mars-400"><span className="flex items-center gap-2.5"><span className={`h-2 w-2 rounded-full ${color}`} />{label}</span><input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} className="h-3.5 w-3.5 accent-[#ed7549]" /></label>;
}
function TelemetryStat({ label, value, unit, icon }: { label: string; value: string; unit: string; icon: ReactNode }) {
  return <div className="rounded-xl border border-white/[0.06] bg-mars-850 p-3"><div className="flex items-center gap-1.5 text-mars-500">{icon}<span className="text-[10px]">{label}</span></div><p className="mt-2 text-sm font-semibold text-mars-300">{value}<span className="ml-1 text-[10px] font-normal text-mars-500">{unit}</span></p></div>;
}
function Metric({ label, value, icon, accent }: { label: string; value: string; icon: ReactNode; accent: string }) {
  return <div className="flex items-center gap-3 px-2 py-1 sm:border-r sm:border-white/[0.07] sm:px-5 sm:first:pl-0"><div className={`rounded-lg bg-mars-800 p-2 ${accent}`}>{icon}</div><div><p className="eyebrow">{label}</p><p className="mt-1 font-mono text-sm font-medium text-white sm:text-base">{value}</p></div></div>;
}
