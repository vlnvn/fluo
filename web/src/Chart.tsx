import { useLayoutEffect, useRef, useState } from 'react';
import type { Frame } from './contracts';
import { reading, timeLabel } from './api';

export function seriesPath(frames: Frame[], key: 'steam_kg_h' | 'return_kg_h', width: number, height: number, low: number, high: number): string {
  const left = 42, right = 14, top = 10, bottom = 44;
  const usable = width - left - right;
  let open = false;
  return frames.map((frame, i) => {
    const value = frame.readings[key];
    if (value === null) { open = false; return ''; }
    const x = left + (frames.length === 1 ? 0 : i / (frames.length - 1)) * usable;
    const y = top + (1 - (value - low) / (high - low)) * (height - top - bottom);
    const command = open ? 'L' : 'M'; open = true;
    return `${command}${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(' ');
}

export default function Chart({ frames, height = 231, eventTime }: { frames: Frame[]; height?: number; eventTime?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(700);
  const [hover, setHover] = useState<number | null>(null);
  useLayoutEffect(() => {
    const element = ref.current!;
    const observer = new ResizeObserver(entries => setWidth(Math.round(entries[0].contentRect.width)));
    observer.observe(element); return () => observer.disconnect();
  }, []);
  const values = frames.flatMap(f => [f.readings.steam_kg_h, f.readings.return_kg_h]).filter((n): n is number => n !== null);
  const low = values.length ? Math.max(0, Math.floor(Math.min(...values) / 20) * 20 - 20) : 0;
  const high = values.length ? Math.ceil(Math.max(...values) / 20) * 20 + 20 : 100;
  const usable = width - 56;
  const first = frames[0], last = frames.at(-1), middle = frames[Math.floor((frames.length - 1) / 2)];
  const marker = eventTime ? frames.findIndex(f => f.timestamp === eventTime) : -1;
  return <div ref={ref} className="chart" style={{ height }} data-testid="telemetry-chart">
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Steam and condensate measurements" onMouseMove={e => { const x = e.clientX - e.currentTarget.getBoundingClientRect().left; setHover(Math.max(0, Math.min(frames.length - 1, Math.round((x - 42) / usable * (frames.length - 1))))); }} onMouseLeave={() => setHover(null)}>
      <title>Observed steam feed and condensate return, kg/h; missing measurements remain gaps</title>
      {[0, 1, 2, 3].map(i => { const y = 10 + i / 3 * (height - 54); return <g key={i}><line x1="42" x2={width - 14} y1={y} y2={y} stroke="#e1ecf7" /><text x="4" y={y + 2} className="axis-y">{Math.round(high - (high - low) * i / 3)}</text></g>; })}
      <path data-series="steam" d={seriesPath(frames, 'steam_kg_h', width, height, low, high)} fill="none" stroke="#245fc7" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
      <path data-series="return" d={seriesPath(frames, 'return_kg_h', width, height, low, high)} fill="none" stroke="#008ba1" strokeWidth="2.3" strokeDasharray="5 4" strokeLinejoin="round" strokeLinecap="round" />
      {marker >= 0 && <line x1={42 + marker / Math.max(1, frames.length - 1) * usable} x2={42 + marker / Math.max(1, frames.length - 1) * usable} y1="6" y2={height - 39} stroke="#e79933" strokeDasharray="3 4" />}
      {first && <text x="42" y={height - 17} className="axis-x">{timeLabel(first.timestamp)}</text>}
      {middle && width > 420 && <text x={42 + usable / 2} y={height - 17} textAnchor="middle" className="axis-x">{timeLabel(middle.timestamp)}</text>}
      {last && frames.length > 1 && <text x={width - 14} y={height - 17} textAnchor="end" className="axis-x">{timeLabel(last.timestamp)}</text>}
    </svg>
    {hover !== null && frames[hover] && <div className="chart-tooltip" style={{ left: Math.min(width - 177, Math.max(35, 42 + hover / Math.max(1, frames.length - 1) * usable)) }}><strong>{timeLabel(frames[hover].timestamp)} WIB</strong><span>Steam {reading(frames[hover].readings.steam_kg_h)} kg/h</span><span>Return {reading(frames[hover].readings.return_kg_h)} kg/h</span></div>}
  </div>;
}
