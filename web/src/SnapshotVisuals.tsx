import type { Event, Frame, SessionState } from './contracts';

export const isInterruption = (event: Event) => event.category === 'quality' && ['GATEWAY_OFFLINE','VERIFY_RETURN_METER'].includes(event.quality_action ?? '');

export function eventBins(events: Event[], category: 'return' | 'quality', now: string, count = 13): number[] {
  const end = Date.parse(now);
  const start = Math.min(end, ...events.map(event => Date.parse(event.timestamp)));
  const span = Math.max(60000, end - start + 1);
  const bins = Array<number>(count).fill(0);
  for (const event of events) {
    if (event.category !== category || Date.parse(event.timestamp) > end) continue;
    if (category === 'quality' && !isInterruption(event)) continue;
    const index = Math.min(count - 1, Math.floor((Date.parse(event.timestamp) - start) / span * count));
    bins[index]++;
  }
  return bins;
}

export function EventHistogram({ state, category }: { state: SessionState; category: 'return' | 'quality' }) {
  const bins = eventBins(state.events, category, state.current.timestamp);
  const maximum = Math.max(1, ...bins);
  const label = `${category === 'return' ? 'Return review' : 'Data interruption'} events across 13 equal time bins in recorded history; oldest to newest. Counts: ${bins.join(', ')}`;
  return <svg className={`event-histogram histogram-${category}`} viewBox="0 0 169 36" role="img" aria-label={label}>
    <title>{label}</title>
    {bins.map((value, index) => {
      const height = value ? 6 + value / maximum * 25 : 2;
      return <rect key={index} data-count={value} x={index * 13} y={35 - height} width="10" height={height} rx="2.5" className={value ? 'bin-populated' : 'bin-empty'}><title>{value} events</title></rect>;
    })}
  </svg>;
}

export function WindowProgress({ state }: { state: SessionState }) {
  const fraction = state.cursor / Math.max(1, state.scenario.total_frames - 1);
  const percent = Math.round(fraction * 100);
  return <svg className="window-progress" viewBox="0 0 54 54" role="img" aria-label={`Replay window ${percent}% elapsed; sample ${state.cursor + 1} of ${state.scenario.total_frames}`}>
    <circle cx="27" cy="27" r="21" className="progress-track"/>
    <circle cx="27" cy="27" r="21" className="progress-value" pathLength="100" strokeDasharray={`${fraction * 100} 100`} transform="rotate(-90 27 27)"/>
    <text x="27" y="30" textAnchor="middle">{percent}%</text>
  </svg>;
}

export function ReadingTrend({ frames, field }: { frames: Frame[]; field: 'steam_kg_h' | 'return_kg_h' | 'pressure_barg' }) {
  const values = frames.map(frame => frame.readings[field]);
  const valid = values.filter((value): value is number => value !== null);
  if (!valid.length) return null;
  const low = Math.min(...valid), high = Math.max(...valid);
  let connected = false;
  const path = values.map((value, index) => {
    if (value === null) { connected = false; return ''; }
    const x = 3 + index / Math.max(1, values.length - 1) * 58;
    const y = high === low ? 16 : 28 - (value - low) / (high - low) * 24;
    const command = connected ? 'L' : 'M'; connected = true;
    return `${command}${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(' ');
  return <svg className="reading-trend" viewBox="0 0 64 32" role="img" aria-label={`Recent ${field.replaceAll('_', ' ')} trend, ${valid.length} available samples; independently scaled`}>
    <path d={path} fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    {valid.length === 1 && <circle cx="3" cy="16" r="2" fill="currentColor"/>}
  </svg>;
}
