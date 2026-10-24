import { useEffect, useRef, useState } from 'react';
import type { ReplayCommand, SessionState } from './contracts';

export default function ReplaySeek({ state, busy, command }: { state: SessionState; busy: boolean; command: (value: ReplayCommand) => Promise<void> }) {
  const [draft, setDraft] = useState<number | null>(null);
  const pending = useRef<number | null>(null);
  const dragging = useRef(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);
  const commit = async () => {
    if (timer.current) clearTimeout(timer.current);
    const cursor = pending.current;
    if (cursor === null || busy) return;
    pending.current = null;
    try { await command({ action: 'seek', cursor }); }
    finally { setDraft(null); }
  };
  return <div className="replay-seek"><label htmlFor="replay-position">Replay position <span>{(draft ?? state.cursor) + 1} / {state.scenario.total_frames} samples · 1× = one minute of recorded data per second</span></label>
    <input id="replay-position" aria-label="Replay position" type="range" min="0" max={state.scenario.total_frames - 1} value={draft ?? state.cursor} disabled={busy}
      onPointerDown={event => { dragging.current = true; event.currentTarget.setPointerCapture(event.pointerId); }}
      onChange={event => {
        const value = Number(event.target.value); pending.current = value; setDraft(value);
        if (timer.current) clearTimeout(timer.current);
        if (!dragging.current) timer.current = setTimeout(() => void commit(), 120);
      }}
      onPointerUp={() => { dragging.current = false; void commit(); }}
      onPointerCancel={() => { dragging.current = false; pending.current = null; setDraft(null); }}
      onKeyUp={event => { if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End', 'PageUp', 'PageDown'].includes(event.key)) void commit(); }}
      onBlur={() => { dragging.current = false; void commit(); }} />
    <p>Scenario names describe the simulator setup. They are not diagnoses made by the model.</p>
  </div>;
}
