import { useEffect, useRef, useState } from 'react';
import { timeLabel } from './api';
import type { ReplayCommand, SessionState } from './contracts';

export default function ReplaySeek({ state, busy, command, onStart, onCancel, onPreview }: { onStart: () => void; onCancel: () => void; onPreview: (cursor: number) => Promise<void>; state: SessionState; busy: boolean; command: (value: ReplayCommand) => Promise<void> }) {
  const [draft, setDraft] = useState<number | null>(null);
  const pending = useRef<number | null>(null);
  const dragging = useRef(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const previewTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cancel = useRef(onCancel); cancel.current=onCancel;
  useEffect(() => () => { if(timer.current) clearTimeout(timer.current);if(previewTimer.current)clearTimeout(previewTimer.current);cancel.current(); }, []);
  const commit = async () => {
    if (timer.current) clearTimeout(timer.current);
    if (previewTimer.current) {clearTimeout(previewTimer.current);previewTimer.current=null;}
    const cursor = pending.current;
    if (cursor === null) { if(!busy)onCancel();return; }
    if(busy)return;
    pending.current = null;
    try { await command({ action: 'seek', cursor }); }
    finally { setDraft(null); }
  };
  return <div className="replay-seek"><label htmlFor="replay-position">Replay position <span>{(draft ?? state.cursor) + 1} / {state.scenario.total_frames} samples · 1× = one minute of recorded data per second</span></label>
    <input style={{'--replay-progress': `${(draft ?? state.cursor) / Math.max(1,state.scenario.total_frames-1) * 100}%` } as React.CSSProperties} aria-valuetext={`${(draft ?? state.cursor)+1} of ${state.scenario.total_frames} samples; ${timeLabel(new Date(Date.parse(state.scenario.start_timestamp)+(draft ?? state.cursor)*60000).toISOString())} WIB`} id="replay-position" aria-label="Replay position" type="range" min="0" max={state.scenario.total_frames - 1} value={draft ?? state.cursor} disabled={busy}
      onPointerDown={event => { onStart();dragging.current = true; event.currentTarget.setPointerCapture(event.pointerId); }}
      onChange={event => {
        onStart();const value = Number(event.target.value); pending.current = value; setDraft(value);
        if (timer.current) clearTimeout(timer.current);
        if (!previewTimer.current) previewTimer.current=setTimeout(()=>{previewTimer.current=null;if(pending.current!==null)void onPreview(pending.current);},80);
        if (!dragging.current) timer.current = setTimeout(() => void commit(), 120);
      }}
      onPointerUp={() => { dragging.current = false; void commit(); }}
      onPointerCancel={() => { dragging.current=false;pending.current=null;if(previewTimer.current)clearTimeout(previewTimer.current);previewTimer.current=null;setDraft(null);onCancel(); }}
      onKeyUp={event => { if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End', 'PageUp', 'PageDown'].includes(event.key)) void commit(); }}
      onBlur={() => { dragging.current = false; void commit(); }} />
    <p>Scenario names describe the simulator setup. They are not diagnoses made by the model.</p>
  </div>;
}
