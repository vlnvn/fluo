import { useState } from 'react';
import type { Event, EventDetail, Review, ReplayCommand, Scenario, SessionState } from './contracts';
import { reading, timeLabel, modeLabel } from './api';
import Chart from './Chart';
import ReplaySeek from './ReplaySeek';
import { EventHistogram, ReadingTrend, WindowProgress } from './SnapshotVisuals';
import { Card, Icon, Pill } from './components';

export function PageTitle({ title, subtitle, children }: { title: string; subtitle: string; children?: React.ReactNode }) {
  return <div className="page-title"><h1>{title}</h1><p>{subtitle}</p>{children && <div className="page-title-actions">{children}</div>}</div>;
}

export function Overview({ state, openEvent }: { state: SessionState; openEvent: (id: string) => void }) {
  const { current: current, frames, events } = state;
  const warning = current.inference.warning;
  const valid = current.quality_action === 'SCORE_ALLOWED';
  const target = events.find(e => e.category === 'return') ?? events[0];
  return <>
    <PageTitle title="Condensate return" subtitle="Pabrik Bandung / Steam return line A"><Pill kind={current.operating_mode === 'production' ? 'green' : 'gray'}>{modeLabel(current.operating_mode)}</Pill><Pill>{current.site_id.replace('_', ' ')}</Pill></PageTitle>
    <div className="kpi-grid">
      {[['Steam feed', reading(current.readings.steam_kg_h), 'kg/h', 'steam_kg_h'], ['Condensate return', reading(current.readings.return_kg_h), 'kg/h', 'return_kg_h'], ['Steam pressure', reading(current.readings.pressure_barg), 'bar(g)', 'pressure_barg']].map(([title, value, unit, field]) => <Card title={title} className="kpi" key={title}><strong className="kpi-value" data-testid={`kpi-${title.toLowerCase().replaceAll(' ', '-')}`}>{value}</strong><span className="kpi-unit">{unit}</span><ReadingTrend frames={frames} field={field as 'steam_kg_h' | 'return_kg_h' | 'pressure_barg'}/></Card>)}
      <Card title="Condensate return status" subtitle="Interpretation depends on meter validity" className="monitor-card"><Pill kind={warning ? 'amber' : valid ? 'green' : 'gray'}>{warning ? 'Investigate — unconfirmed' : valid ? 'Monitoring' : 'Insufficient evidence / sensor check'}</Pill></Card>
    </div>
    <div className="overview-grid">
      <Card title="Steam and condensate return" subtitle={`Steam supply and return, ${timeLabel(frames[0].timestamp)}–${timeLabel(current.timestamp)}`} className="overview-graph gradient-card">
        <div className="main-chart-slot"><Chart frames={frames} eventTime={state.active_event_id ? events.find(e => e.id === state.active_event_id)?.timestamp : undefined} /></div>
        <div className="chart-legend"><span className="legend-steam"/>Steam feed <span className="legend-return"/>Condensate return</div>
      </Card>
      <Card title="What needs checking" subtitle="Check the meter before classifying the cause" className="investigate-card">
        <strong className="signature-value" data-testid="signature-score">{reading(current.inference.score, 2)}</strong><span className="signature-label">{valid ? 'Signature score' : 'Score withheld'}</span><div className="card-divider" />
        <h3><Icon name="IconAlert"/>{warning ? 'Return-flow deficit detected' : valid ? 'Read-only monitoring' : 'Check data and operating mode'}</h3>
        <p className="guidance">{warning ? 'Verify return-flow meter and operating mode before inspecting the return path.' : valid ? 'No persistent return-deficit warning in the current interval.' : 'Interpretation is withheld until valid telemetry and history are available.'}</p>
        <button className="primary investigate-button" disabled={!target} onClick={() => target && openEvent(target.id)}>View investigation<Icon name="ActionTrailingArrow"/></button>
      </Card>
      <Card title="Process & data-quality timeline" subtitle="Separate operating mode and sensor availability" className="quality-card">
        <div className="quality-segments" aria-label="Recent process and data quality">{frames.slice(-18).map(f => <span key={f.minute_id} title={`${timeLabel(f.timestamp)} · ${f.quality_action}`} className={f.quality_action === 'SCORE_ALLOWED' ? f.inference.warning ? 'quality-warning' : 'quality-valid' : 'quality-unavailable'} />)}</div>
      </Card>
      <Card title="Latest review note" subtitle={`${timeLabel(current.timestamp)} / current interval`} className="recent-card"><p>{warning ? 'Return ratio decreased during production. A meter check precedes any physical conclusion.' : valid ? 'Measurements are available. Continue monitoring the return path and operating context.' : 'Check telemetry availability and process state before interpreting the return signal.'}</p></Card>
    </div>
  </>;
}

export function ScenarioReview({ state, scenarios, busy, command }: { state: SessionState; scenarios: Scenario[]; busy: boolean; command: (data: ReplayCommand) => Promise<void> }) {
  const { current, frames } = state;
  return <>
    <PageTitle title="Scenario Review" subtitle="Compare operating conditions and review warning responses" />
    <div className="scenario-grid">
      <Card title="Scenario library" subtitle="Choose a scenario to inspect" className="scenario-library"><div className="scenario-list">{scenarios.map(s => <button key={s.id} className={`scenario-option ${s.id === state.scenario.id ? 'selected' : ''}`} aria-pressed={s.id === state.scenario.id} disabled={busy} onClick={() => command({ action: 'scenario', scenario_id: s.id })}><span>{s.name}</span><small>{s.group}</small></button>)}</div></Card>
      <Card title={`${timeLabel(current.timestamp)} / ${timeLabel(state.scenario.end_timestamp)}`} subtitle={`Replay timeline / speed ${state.speed}×`} className="playback-card">
        <div className="playback-controls" role="group" aria-label="Replay controls">
          <button aria-label="Rewind 10 samples" title="Rewind 10 samples" disabled={busy || state.cursor === 0} onClick={() => command({ action: 'rewind' })}><Icon name="IconRewind"/></button>
          <button className="play-button" aria-label="Play replay" title="Play replay" disabled={busy || state.playback !== 'PAUSED'} onClick={() => command({ action: 'play' })}><Icon name="IconPlay"/></button>
          <button aria-label="Pause replay" title="Pause replay" disabled={busy || state.playback !== 'PLAYING'} onClick={() => command({ action: 'pause' })}><Icon name="IconPause"/></button>
          <button aria-label="Forward 10 samples" title="Forward 10 samples" disabled={busy || state.cursor >= state.scenario.total_frames - 1} onClick={() => command({ action: 'forward' })}><Icon name="IconRewind" className="forward-icon"/></button>
          <button aria-label="Reset replay" title="Reset replay" disabled={busy || (state.cursor === 0 && state.playback === 'PAUSED')} onClick={() => command({ action: 'reset' })}><Icon name="IconReset"/></button>
          <button className="speed-button" aria-label={`Playback speed ${state.speed}x`} disabled={busy} onClick={() => command({ action: 'speed', speed: state.speed === 1 ? 2 : 1 })}>{state.speed}×</button>
        </div>
      </Card>
      <Card title="Sizing steam branch" subtitle="Steam distribution and return path" className="process-card gradient-card">
        <div className="process-flow"><div className="process-node steam-node"><h3>Steam supply</h3><p>{reading(current.readings.pressure_barg)} bar(g)</p></div><Icon name="ProcessConnector"/><div className="process-node sizing-node"><h3>Sizing section</h3><p>Indirect heat</p></div><Icon name="ProcessConnector"/><div className={`process-node return-node ${current.inference.warning ? 'process-warning' : ''}`}><h3>Condensate return</h3><p>{reading(current.readings.return_kg_h)} kg/h</p></div></div>
        <span className="process-live-state">{current.quality_action === 'SCORE_ALLOWED' ? current.inference.warning ? 'Investigate — cause unconfirmed' : 'Monitoring' : 'Data / mode check'}</span>
      </Card>
      <Card title="Steam / condensate trends" subtitle="Steam feed and return flow" className="scenario-graph"><div className="scenario-chart-slot"><Chart frames={frames} height={215}/></div></Card>
    </div>
    <ReplaySeek key={state.scenario.id} state={state} busy={busy} command={command}/>
  </>;
}

export function EventCenter({ state, filter, openFilter, openEvent }: { state: SessionState; filter: string; openFilter: () => void; openEvent: (id: string) => void }) {
  const [sort, setSort] = useState<'desc'|'asc'>('desc');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const categoryName = filter === 'return' ? 'Return deficit' : filter === 'quality' ? 'Data quality' : 'All events';
  const filtered = state.events.filter(e => (filter === 'all' || e.category === filter) && `${e.id} ${e.title} ${e.state}`.toLowerCase().includes(search.toLowerCase()));
  const rows = sort === 'desc' ? filtered : [...filtered].reverse();
  const boundedPage = Math.min(page, Math.max(0, Math.ceil(rows.length / 4) - 1));
  return <>
    <PageTitle title="Signal events" subtitle="Review intervals derived from detector state changes" />
    <div className="event-kpis">
      <Card title="Review items" subtitle="Recorded operating history" className="event-summary"><strong>{String(state.events.filter(e => e.category === 'return').length).padStart(2,'0')}</strong><EventHistogram state={state} category="return"/></Card>
      <Card title="Data interruptions" subtitle="Requires attention" className="event-summary"><strong>{String(state.events.filter(e => e.category === 'quality' && e.title !== 'Data connection restored').length).padStart(2,'0')}</strong><EventHistogram state={state} category="quality"/></Card>
      <Card title="Review window" subtitle="Selected replay interval" className="event-range"><strong>{timeLabel(state.scenario.start_timestamp)} — {timeLabel(state.current.timestamp)}</strong><WindowProgress state={state}/></Card>
    </div>
    <div className="filter-toolbar"><Icon name="IconFilter"/><span>{categoryName} / history through {timeLabel(state.current.timestamp)} WIB</span><button className="secondary" onClick={openFilter}>Filters</button></div>
    <Card title="Review queue" subtitle="Most recent warning and quality-check intervals" className="event-table-card">
      <div className="event-search"><label className="sr-only" htmlFor="event-search">Search events</label><input id="event-search" placeholder="Search events" value={search} onChange={e=>{setSearch(e.target.value);setPage(0);}} /></div>
      <table><thead><tr><th><button aria-label={`Sort events ${sort === 'desc' ? 'oldest' : 'newest'} first`} onClick={()=>{setSort(sort === 'desc' ? 'asc' : 'desc');setPage(0);}}>TIME <span className="sort-caret" aria-hidden="true">{sort === 'desc' ? '↓' : '↑'}</span></button></th><th>EVENT</th><th>TYPE</th><th>STATE</th><th>DURATION</th><th><span className="sr-only">Open</span></th></tr></thead>
      <tbody>{rows.slice(boundedPage*4,boundedPage*4+4).map((event: Event)=> <tr key={event.id}><td><time dateTime={event.timestamp} title={event.timestamp}>{timeLabel(event.timestamp)}</time></td><td><button className="event-link" onClick={()=>openEvent(event.id)}>{event.id}</button></td><td className="event-type">{event.title}</td><td className={event.category === 'return' ? 'warning-text' : ''}>{event.state}</td><td>{event.duration_min} min</td><td><button className="open-row" aria-label={`Open ${event.id}`} onClick={()=>openEvent(event.id)}><Icon name="IconRow0"/></button></td></tr>)}</tbody></table>
      {!rows.length && <div className="empty-state">No events match this filter.</div>}
      <div className="table-footer"><span>{rows.length} recorded intervals · {state.current.site_id}</span><div><button className="text-button" disabled={boundedPage === 0} onClick={()=>setPage(boundedPage-1)}>Previous</button><span>{boundedPage+1} / {Math.max(1,Math.ceil(rows.length/4))}</span><button className="text-button" disabled={(boundedPage+1)*4 >= rows.length} onClick={()=>setPage(boundedPage+1)}>Next</button></div></div>
    </Card>
  </>;
}

export function EventDetails({ detail, saving, onCheck, onNote, onSaveDraft, onSubmit, onSummary, onBack }: { detail: EventDetail; saving: boolean; onCheck: (step: string, checked: boolean) => void; onNote: (note: string) => void; onSaveDraft: () => void; onSubmit: () => void; onSummary: () => void; onBack: () => void }) {
  const { event, frame, review } = detail;
  const [note, setNote] = useState(review.note);
  const isReturn = event.category === 'return';
  return <>
    <PageTitle title={`Event review / ${event.id}`} subtitle={`${event.title} — sizing branch`}><button className="back-events secondary" onClick={onBack}>← Event Center</button></PageTitle>
    <div className="event-notice"><Icon name="IconWarn"/><span>{isReturn ? 'Indication only — physical loss and meter under-reading cannot be distinguished from these inputs alone.' : 'Data and mode checks precede interpretation — unavailable readings do not establish physical loss.'}</span></div>
    <div className="details-grid">
      <Card title="Context around the event" subtitle={`${timeLabel(detail.context[0].timestamp)}–${timeLabel(detail.context.at(-1)!.timestamp)} / steam and return measurements`} className="event-context"><div className="event-chart-slot"><Chart frames={detail.context} height={227} eventTime={event.timestamp}/></div></Card>
      <Card title={isReturn ? 'Why this was flagged' : 'Evidence quality'} subtitle="Signal strength does not establish the cause" className="evidence-card"><strong className="signature-value">{reading(frame.inference.score,2)}</strong><span className="signature-label">{frame.inference.score === null ? 'Score withheld' : 'Signature score'}</span><div className="card-divider"/><ul>{event.evidence.map(line=><li key={line}><Icon name="IconEvidence0"/>{line.startsWith('Process: ') ? `Process: ${modeLabel(line.slice(9))}` : line}</li>)}</ul></Card>
      <Card title="Manual verification" subtitle="Verified steps form the operator review record" className="verification-card"><div className="verification-list">{review.steps.map(step=><label key={step.step_id}><input type="checkbox" checked={!!step.checked} disabled={saving} onChange={e=>onCheck(step.step_id,e.target.checked)}/><span>{step.label}</span></label>)}</div><p className="draft-hint">{saving ? 'Saving draft…' : review.status === 'draft' ? 'Draft saved locally. Submit the review explicitly below.' : 'Changes remain a draft until recorded in the application.'}</p></Card>
      <Card title="Action card" subtitle="Read-only field guidance" className="action-card"><div className="action-lines"><p>Assessment: {isReturn ? 'unconfirmed deficit' : 'data / mode check'}</p><p>Next step: {isReturn ? 'verify instruments first' : 'verify data and operating context'}</p><p>Recovery eligibility: site assessment</p><p>Automatic actuation: disabled</p></div><p className="operator-status">Operator review: {review.status === 'submitted' ? 'submitted locally' : 'pending confirmation'}</p><button className="primary summary-button" onClick={onSummary}>View inspection summary</button></Card>
    </div>
    <form className="review-editor" onSubmit={e=>{e.preventDefault();onNote(note);onSubmit();}}><div><label htmlFor="review-evidence">Inspection evidence / note</label><textarea id="review-evidence" maxLength={2000} placeholder="Record observations without assuming a physical cause" value={note} disabled={saving} onChange={e=>{setNote(e.target.value);onNote(e.target.value);}} /></div><div><p>Local operator (unverified). Review records persist in this local installation.</p><div className="review-buttons"><button className="secondary" type="button" disabled={saving} onClick={onSaveDraft}>Save draft</button><button className="primary" type="submit" disabled={saving}>{saving ? 'Saving…' : 'Record operator review'}</button></div><small>{review.submitted_at ? `Submitted ${new Date(review.submitted_at).toLocaleString('en-GB')}` : 'Checking steps does not resolve a warning or authorize recovery.'}</small></div></form>
  </>;
}

export function updateReview(detail: EventDetail, review: Review): EventDetail { return { ...detail, review }; }
