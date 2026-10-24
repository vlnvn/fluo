import { useCallback, useEffect, useRef, useState } from 'react';
import type { EventDetail, PreferencesUpdate, ReplayCommand, Scenario, SessionState } from './contracts';
import { api, ApiError, timeLabel, modeLabel } from './api';
import { Dialog, Icon } from './components';
import { EventCenter, EventDetails, Overview, ScenarioReview, updateReview } from './Views';

type Overlay = 'filter'|'notifications'|'help'|'preferences'|'profile'|'summary'|'preview'|null;
type Route = 'overview'|'scenarios'|'events'|'details';
const SESSION_KEY = 'fluo.session.v1';
const COMPACT_KEY = 'fluo.compact.v1';

function safeDecode(value: string) { try { return decodeURIComponent(value); } catch { return value; } }

function parseRoute(): { page: Route; eventId: string | null } {
  const segments = window.location.hash.replace(/^#\/?/, '').split('/');
  if (segments[0] === 'events' && segments[1]) return { page: 'details', eventId: safeDecode(segments[1]) };
  return { page: segments[0] === 'scenarios' ? 'scenarios' : segments[0] === 'events' ? 'events' : 'overview', eventId: null };
}

function readSeen(): string[] {
    try { const value: unknown = JSON.parse(localStorage.getItem('fluo.seen') ?? '[]'); return Array.isArray(value) ? value.filter((id): id is string => typeof id === 'string') : []; }
    catch { return []; }
}

export default function App() {
  const [authNeeded,setAuthNeeded]=useState(false);
  const [entryBusy,setEntryBusy]=useState(false);
  const [guestExpiry,setGuestExpiry]=useState('');
  const [state, setState] = useState<SessionState | null>(null);
  const [preview, setPreview] = useState<SessionState | null>(null);
  const [scrubbing, setScrubbing] = useState(false);
  const scrubActive = useRef(false);
  const previewRequest = useRef<AbortController | null>(null);
  const previewGeneration = useRef(0);
  const naturalTick = useRef(false);
  const reviewLock = useRef(false);
  const [warningEvent, setWarningEvent] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [route, setRoute] = useState(parseRoute);
  const [compact, setCompact] = useState(() => localStorage.getItem(COMPACT_KEY) === 'true');
  const [overlay, setOverlay] = useState<Overlay>(null);
  const [detail, setDetail] = useState<EventDetail | null>(null);
  const [filter, setFilter] = useState(() => localStorage.getItem('fluo.filter') ?? 'all');
  const [filterDraft, setFilterDraft] = useState(filter);
  const [preferences, setPreferences] = useState<PreferencesUpdate>({ warning_sound: false });
  const [soundDraft, setSoundDraft] = useState(false);
  const [busy, setBusy] = useState(false);
  const [savingReview, setSavingReview] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState('');
  const [downloadBusy, setDownloadBusy] = useState(false);
  const [seen, setSeen] = useState<string[]>(readSeen);
  const note = useRef('');
  const generation = useRef(0);
  const lock = useRef(false);
  const main = useRef<HTMLElement>(null);
  const scrolls = useRef<Record<string, number>>({});
  const currentRoute = useRef(route.page);
  const notificationHistory = useRef<{session:string;scenario:string;cursor:number;ids:Set<string>} | null>(null);

  useEffect(()=>{const expired=()=>{setAuthNeeded(true);setState(null);};window.addEventListener('fluo-auth-required',expired);return()=>window.removeEventListener('fluo-auth-required',expired);},[]);

  useEffect(() => {
    const sync = (event: StorageEvent) => { if (event.key === 'fluo.seen' || event.key === null) setSeen(readSeen()); };
    window.addEventListener('storage', sync);
    return () => window.removeEventListener('storage', sync);
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function bootstrap() {
      try {
        const identity=await api.authSession();if(!cancelled)setGuestExpiry(identity.expires_at);
        const library = await api.scenarios();
        const existing = localStorage.getItem(SESSION_KEY);
        let initial: SessionState;
        if (existing) {
          try { initial = await api.state(existing); }
          catch (e) { if (e instanceof ApiError && e.status === 404) initial = await api.create(); else throw e; }
        } else initial = await api.create();
        const prefs = await api.preferences(initial.session_id);
        if (!cancelled) { localStorage.setItem(SESSION_KEY, initial.session_id); setScenarios(library); setState(initial); setPreferences(prefs); setSoundDraft(prefs.warning_sound); }
      } catch (e) { if (!cancelled) {if(e instanceof ApiError && e.status === 401){setAuthNeeded(true);setError(null);}else setError((e as Error).message);} }
    }
    void bootstrap(); return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    const handler = () => { const next = parseRoute(); if (currentRoute.current !== next.page && main.current) scrolls.current[currentRoute.current] = window.scrollY; currentRoute.current = next.page; setRoute(next); requestAnimationFrame(() => window.scrollTo(0,scrolls.current[next.page] ?? 0)); };
    window.addEventListener('hashchange', handler); return () => window.removeEventListener('hashchange', handler);
  }, []);

  const sessionId = state?.session_id;
  const isPlaying = state?.playback === 'PLAYING';
  useEffect(() => {
    if (!sessionId || !isPlaying) return;
    let cancelled = false, inflight = false;
    const tick = async () => {
      if (inflight || lock.current || scrubActive.current) return;
      inflight = true; const stamp = generation.current;
      try { const next = await api.state(sessionId); if (!cancelled && stamp === generation.current) { naturalTick.current=true;setState(next); setError(null); } }
      catch (e) { if (!cancelled) setError((e as Error).message); }
      finally { inflight = false; }
    };
    const timer = setInterval(() => void tick(), 450);
    return () => { cancelled = true; clearInterval(timer); };
  }, [sessionId, isPlaying]);

  useEffect(() => {

  if (!state) return;
    const previous = notificationHistory.current;
    const ids = new Set(state.events.map(e=>e.id));
    if (naturalTick.current && previous && previous.session === state.session_id && previous.scenario === state.scenario.id && state.cursor > previous.cursor && state.playback !== 'PAUSED') {
      const freshWarning = state.events.some(e => e.category === 'return' && !previous.ids.has(e.id));
      if (freshWarning) { const event = state.events.find(e => e.category === 'return' && !previous.ids.has(e.id))!; setWarningEvent(event.id);setToast(`New return-flow warning / ${event.id}. Verify the measurements before classifying the cause.`); }
      if (freshWarning && preferences.warning_sound) { const audio = new Audio('/assets/notification-chime.mp3'); audio.volume = .4; void audio.play().catch(()=>setToast('New warning received. Your browser blocked the audio cue.')); }
    }
    naturalTick.current = false;
    notificationHistory.current = {session:state.session_id, scenario:state.scenario.id, cursor:state.cursor, ids};
  }, [state, preferences.warning_sound]);

  useEffect(() => {
    if (route.page !== 'details' || !route.eventId || !sessionId) return;
    let cancelled = false;
    setDetail(null);
    api.detail(sessionId, route.eventId).then(value=>{if (!cancelled) {setDetail(value);note.current=value.review.note;}}).catch(e=>{if(!cancelled)setError((e as Error).message);});
    return ()=>{cancelled=true;};
  }, [sessionId, route.page, route.eventId]);

  useEffect(()=>{ if (!toast) return; const timer=setTimeout(()=>setToast(''),4500);return()=>clearTimeout(timer);},[toast]);
  const closeOverlay = useCallback(()=>setOverlay(null),[]);
  const navigate = (page: Route) => { window.location.hash = page === 'overview' ? '#/' : `#/${page}`; };
  const openEvent = (id: string) => { setOverlay(null); window.location.hash=`#/events/${encodeURIComponent(id)}`; };
  const toggleSidebar = () => { setCompact(value=>{localStorage.setItem(COMPACT_KEY,String(!value));return !value;}); };

  const beginScrub = () => { if (!scrubActive.current) {scrubActive.current=true;generation.current++;naturalTick.current=false;setScrubbing(true);} };
  const cancelScrub = useCallback(() => {scrubActive.current=false;previewGeneration.current++;previewRequest.current?.abort();setScrubbing(false);setPreview(null);}, []);
  const previewCursor = async (cursor: number) => {
    if (!state || !scrubActive.current) return;
    previewRequest.current?.abort(); const controller=new AbortController();previewRequest.current=controller;const stamp=++previewGeneration.current;
    try {const next=await api.preview(state.session_id,cursor,controller.signal);if(scrubActive.current&&stamp===previewGeneration.current)setPreview(next);}
    catch(error){if(!controller.signal.aborted){setToast(`Cursor preview unavailable: ${(error as Error).message}`);}}
  };

  const command = async (data: ReplayCommand) => {
    if (!state || lock.current) return;
    lock.current=true;generation.current++;naturalTick.current=false;scrubActive.current=false;previewGeneration.current++;previewRequest.current?.abort();setBusy(true);
    try { const next=await api.command(state.session_id,data);setState(next);setError(null);if(data.action==='scenario') {setDetail(null);if(route.page==='details')navigate('scenarios');} }
    catch(e){setError((e as Error).message);}finally{lock.current=false;setBusy(false);setPreview(null);setScrubbing(false);}
  };

  const saveReview = async (stepId?: string, checked?: boolean, submit=false) => {
    if (!state || !detail || reviewLock.current) return;
    reviewLock.current=true;setSavingReview(true);
    try {
      const checkedSteps=detail.review.steps.filter(step=>step.step_id===stepId?checked:step.checked).map(step=>step.step_id);
      const updated=await api.review(state.session_id,detail.event.id,{checked_steps:checkedSteps,note:note.current,revision:detail.review.revision},submit);
      setDetail(value=>value ? updateReview(value,updated):value);
      if(!submit)setToast('Inspection draft saved to this workspace.');
      if(submit)setToast('Operator review saved to this workspace. Warning and recovery status are unchanged.');
    }catch(e){setError((e as Error).message);}finally{reviewLock.current=false;setSavingReview(false);}
  };

  const savePreferences=async()=>{
    if (!state) return;setBusy(true);
    try{const value=await api.savePreferences(state.session_id,{warning_sound:soundDraft});setPreferences(value);setOverlay(null);setToast('Preferences saved locally.');}catch(e){setError((e as Error).message);}finally{setBusy(false);}
  };

  const downloadReport=async()=>{
    if(!state||!detail||downloadBusy)return;setDownloadBusy(true);
    try{
      const response=await fetch(api.reportUrl(state.session_id,detail.event.id,'report.pdf'));
      if(!response.ok)throw new Error('Could not generate the inspection PDF. Please retry.');
      const blob=await response.blob();if(blob.type!=='application/pdf')throw new Error('The server returned an invalid report format.');
      const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`Fluo-${detail.event.id}-inspection.pdf`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);setToast('Inspection PDF generated from the selected event.');
    }catch(e){setError((e as Error).message);}finally{setDownloadBusy(false);}
  };

  if(authNeeded)return <main className="guest-entry"><section><img src="/assets/BrandOriginalRoundedVectorLogo.svg" alt="Fluo"/><h1>Your private guest workspace</h1><p>Explore recorded steam and condensate telemetry, review signals, and save inspection notes in an isolated guest sandbox.</p><p className="guest-note">Fictional facility · Simulated research telemetry · No equipment controls</p><p className="guest-note">Access expires after two hours. Notes are private to this guest. Expired records are cleaned up when new workspaces open. Human operator identity is not verified.</p>{error&&<p role="alert">{error}</p>}<button className="primary" disabled={entryBusy} onClick={()=>{setEntryBusy(true);void api.startGuest().then(()=>{localStorage.removeItem(SESSION_KEY);window.location.reload();}).catch(e=>{setError((e as Error).message);setEntryBusy(false);});}}>{entryBusy?'Opening workspace…':'Start guest workspace'}</button></section></main>;
  if (!state) return <div className="boot-screen"><img src="/assets/BrandOriginalRoundedVectorLogo.svg" alt="Fluo"/><h1>{error ? 'Local service unavailable' : 'Opening your monitoring workspace'}</h1><p>{error ?? 'Loading verified model and recorded telemetry…'}</p>{error&&<button className="primary" onClick={()=>window.location.reload()}>Retry connection</button>}</div>;
  const notificationKey=(id:string)=>`${state.session_id}:${state.current.site_id}:${id}`;
  const viewState=preview ?? state;
  const unread=viewState.events.filter(e=>!seen.includes(notificationKey(e.id))).length;
  const openNotifications=()=>setOverlay('notifications');
  const markNotificationsRead=()=>{const next=[...new Set([...seen,...state.events.map(e=>notificationKey(e.id))])];setSeen(next);localStorage.setItem('fluo.seen',JSON.stringify(next));};
  const openPreferences=()=>{setSoundDraft(preferences.warning_sound);setOverlay('preferences');};
  const routes=[{page:'overview',label:'Overview',icon:'IconOverview'},{page:'scenarios',label:'Scenario Review',icon:'IconLab'},{page:'events',label:'Event Center',icon:'IconEvents'}] as const;
  return <div className={`app ${compact?'is-compact':''}`}>
    <a href="#main-content" className="skip-link">Skip to content</a>
    <aside className="sidebar" aria-label="Primary navigation">
      <a href="#/" className="brand" aria-label="Fluo Overview"><img src={compact?'/assets/BrandCompact.svg':'/assets/BrandOriginalRoundedVectorLogo.svg'} alt="Fluo"/></a>
      {!compact&&<p className="brand-caption">STEAM &amp; CONDENSATE</p>}
      <nav>{routes.map(item=><a key={item.page} href={item.page==='overview'?'#/':`#/${item.page}`} className={`nav-row ${route.page===item.page||(route.page==='details'&&item.page==='events')?'active':''}`} aria-current={route.page===item.page||(route.page==='details'&&item.page==='events')?'page':undefined} aria-label={item.label} title={compact?item.label:undefined}><Icon name={item.icon}/>{!compact&&<span>{item.label}</span>}</a>)}</nav>
      <button className="sidebar-toggle" onClick={toggleSidebar} aria-label={compact?'Expand sidebar':'Collapse sidebar'} title={compact?'Expand sidebar':'Collapse sidebar'}><Icon name="IconSidebarToggle" className={compact?'expand-icon':''}/></button>
      <div className="sidebar-utilities"><button className="nav-row" onClick={()=>setOverlay('help')} aria-label="Help center" title={compact?'Help center':undefined}><Icon name="IconHelp"/>{!compact&&<span>Help center</span>}</button><button className="nav-row" onClick={openPreferences} aria-label="Preferences" title={compact?'Preferences':undefined}><Icon name="IconPreferences"/>{!compact&&<span>Preferences</span>}</button></div>
    </aside>
    <header className="header"><div className="header-context"><strong>Pabrik Bandung</strong><span>Unit Sizing A</span></div><div className="header-actions"><button className="notification-button" aria-label={`Notifications${unread?`, ${unread} unread`:''}`} title="Notifications" onClick={openNotifications}><Icon name="IconBell"/>{unread>0&&<span className="notification-badge" data-testid="notification-count">{unread}</span>}</button><button className="avatar" onClick={()=>setOverlay('profile')} aria-label="Open workspace profile">AT</button><button className="workspace-profile" onClick={()=>setOverlay('profile')}><strong>PT Arunika Tekstil</strong><span>Pabrik Bandung</span></button></div></header>
    <main id="main-content" ref={main} className={`main-content page-${route.page}`} tabIndex={-1}>
      {error&&<div role="alert" className="error-banner"><span>{error}</span><button onClick={()=>setError(null)} aria-label="Dismiss error">×</button></div>}
      {route.page==='overview'&&<Overview state={viewState} openEvent={openEvent}/>}
      {route.page==='scenarios'&&<ScenarioReview state={viewState} scenarios={scenarios} busy={busy} scrubbing={scrubbing} onScrubStart={beginScrub} onScrubCancel={cancelScrub} onPreview={previewCursor} command={command}/>}
      {route.page==='events'&&<EventCenter key={filter} state={viewState} filter={filter} openFilter={()=>{setFilterDraft(filter);setOverlay('filter');}} openEvent={openEvent}/>}
      {route.page==='details'&&(detail?<EventDetails key={detail.event.id} detail={detail} saving={savingReview} onCheck={(step,checked)=>void saveReview(step,checked)} onNote={value=>{note.current=value;}} onSaveDraft={()=>void saveReview()} onSubmit={()=>void saveReview(undefined,undefined,true)} onSummary={()=>setOverlay('summary')} onBack={()=>navigate('events')}/>:<div className="loading-state" role="status">{error?'Event unavailable. Return to Event Center to choose a recorded interval.':'Loading event evidence…'}{error&&<button className="secondary" onClick={()=>navigate('events')}>Event Center</button>}</div>)}
    </main>
    <div className="data-provenance" title={`Model SHA-256 ${state.lineage.model_sha256}; dataset SHA-256 ${state.lineage.dataset_sha256}`}>Simulated research telemetry <span aria-hidden="true">·</span> {viewState.is_preview ? 'cursor preview' : state.playback.toLowerCase()} <span aria-hidden="true">·</span> {timeLabel(viewState.current.timestamp)} WIB</div>
    {toast&&<div className="toast" role="status">{toast}{warningEvent&&toast.startsWith('New return-flow warning')&&<button className="text-button" onClick={()=>openEvent(warningEvent)}>Review warning</button>}</div>}

    {overlay==='filter'&&<Dialog kind="filter" title="Filter events" onClose={closeOverlay}><h2>Filter events</h2><p className="dialog-subtitle">Choose a category for the event history.</p><fieldset className="filter-options"><legend>Event category</legend>{[['all','All events','Warning and sensor-status changes'],['return','Return deficit','Events requiring verification'],['quality','Data quality','Unavailable or invalid readings']].map(([value,label,description])=><label key={value} className={filterDraft===value?'selected':''}><input type="radio" name="event-category" value={value} checked={filterDraft===value} onChange={()=>setFilterDraft(value)}/><span><strong>{label}</strong><small>{description}</small></span></label>)}</fieldset><div className="filter-context"><div><span>Time window</span><strong>History through {timeLabel(state.current.timestamp)} WIB</strong></div><div><span>Equipment</span><strong>Sizing unit A / {state.current.site_id}</strong></div></div><div className="filter-actions"><button className="secondary" onClick={closeOverlay}>Cancel</button><button className="secondary reset-filter" disabled={filterDraft==='all'} onClick={()=>setFilterDraft('all')}>Reset</button><button className="primary" onClick={()=>{setFilter(filterDraft);localStorage.setItem('fluo.filter',filterDraft);setOverlay(null);}}>Apply filters</button></div></Dialog>}

    {overlay==='notifications'&&<Dialog kind="notifications" title="Notifications" onClose={closeOverlay}><h2>Notifications</h2><button className="mark-notifications-read text-button" disabled={unread===0} onClick={markNotificationsRead}>Mark all as read</button><p className="dialog-subtitle">Recent activity · {unread} unread / {viewState.events.length} recorded</p><div className="notification-items">{viewState.events.slice(0,3).map(event=><button className={`notice-item ${event.category==='return'?'notice-warning':''}`} key={event.id} onClick={()=>openEvent(event.id)}><span className="notice-dot"/><strong>{event.title}</strong><small>{event.category==='return'?'Verify the return-flow meter and operating state':'Review data availability and process context'}</small><time>{timeLabel(event.timestamp)}</time></button>)}{!state.events.length&&<p className="empty-state">No recorded activity yet.</p>}</div><button className="primary notification-history" onClick={()=>{setOverlay(null);navigate('events');}}>Open event history</button></Dialog>}

    {overlay==='help'&&<Dialog kind="help" title="Help center" onClose={closeOverlay}><h2>Help center</h2><p className="dialog-subtitle">How to use Fluo’s monitoring and review tools</p><div className="help-content"><section><h3>Overview</h3><p>Review steam feed, return flow, process state and warning indicators.</p></section><section><h3>Scenario Review</h3><p>Examine recorded process conditions and warning responses. At 1×, one minute of recorded telemetry advances each second.</p></section><section><h3>Event Center</h3><p>Open past warnings, inspect sensor evidence, and record a local operator review. New warnings show a brief notice; the bell opens recorded activity.</p></section><section><h3>Safety and provenance</h3><p>Simulated research telemetry; fictional facility. Physical verification and condensate recovery require authorized site personnel. Scores are not cause probabilities.</p></section></div></Dialog>}

    {overlay==='preferences'&&<Dialog kind="preferences" title="Preferences" onClose={closeOverlay}><h2>Preferences</h2><p className="dialog-subtitle">Workspace and notification settings</p><div className="facility-card"><div><small>FACILITY</small><strong>Pabrik Bandung</strong></div><div><small>PROCESS SCOPE</small><strong>Unit Sizing A</strong></div></div><div className="preferences-section"><h3>Notification preferences</h3><p>Configure how non-critical audible alerts are presented.</p></div><div className="sound-row"><div><strong>Warning sound</strong><p>{soundDraft?'Audio cue is enabled for new warnings':'Audio cue is disabled for new warnings'}</p></div><button className={`sound-toggle ${soundDraft?'on':''}`} role="switch" aria-checked={soundDraft} aria-label="Warning sound" onClick={()=>setSoundDraft(!soundDraft)}>{soundDraft?'On':'Off'}</button></div><button className="primary save-preferences" disabled={busy} onClick={()=>void savePreferences()}>{busy?'Saving…':'Save preferences'}</button></Dialog>}

    {overlay==='profile'&&<Dialog kind="profile" title="Workspace profile" onClose={closeOverlay}><h2>PT Arunika Tekstil</h2><p className="dialog-subtitle">Pabrik Bandung / Unit Sizing A</p><div className="profile-content"><h3>Utility operations</h3><p>Fictional facility. Guest access is isolated; human operator identity is unverified.</p><p>Guest access expires {guestExpiry ? new Date(guestExpiry).toLocaleTimeString('en-GB',{timeZone:'Asia/Jakarta',hour:'2-digit',minute:'2-digit'}) : 'after two hours'} WIB.</p></div><button className="secondary profile-preferences" onClick={openPreferences}>Preferences</button><button className="secondary profile-logout" onClick={()=>void api.logout().then(()=>{localStorage.removeItem(SESSION_KEY);window.location.reload();}).catch(e=>setError((e as Error).message))}>End guest session</button></Dialog>}

    {overlay==='summary'&&detail&&<Dialog kind="summary" title={`Inspection summary ${detail.event.id}`} onClose={closeOverlay} hideClose><h2>Inspection summary — {detail.event.id}</h2><p className="dialog-subtitle">PT Arunika Tekstil / Pabrik Bandung / Unit Sizing A</p><button className="close-summary secondary" onClick={closeOverlay}>Close</button><div className="summary-status">{detail.event.title} / {detail.event.category==='return'?'Cause not confirmed':'Data / mode check'}</div><div className="summary-grid"><section><h3>Observation</h3><p>{detail.event.category==='return'?'Steam and return meters require independent verification.':'Check data availability and process context before interpreting measurements.'}</p><h4>Recommended check</h4><p>Confirm timestamps and mode; compare meter calibration; inspect return routing.</p></section><section><h3>Event evidence</h3><p>Operating mode: {modeLabel(detail.frame.operating_mode)}</p><p>{detail.frame.quality_action === 'SCORE_ALLOWED'?'Return meter: check bias':detail.frame.quality_action}</p><p>Persistence: {detail.frame.inference.persistence_hits} of 10 min</p></section></div><div className="summary-actions"><button className="primary" disabled={downloadBusy} onClick={()=>void downloadReport()}>{downloadBusy?'Generating…':'Download PDF'}</button><button className="secondary" onClick={()=>setOverlay('preview')}>Print</button></div><p className="summary-provenance">Simulated research telemetry · Review: {detail.review.status} · Guest operator (unverified)</p></Dialog>}

    {overlay==='preview'&&detail&&<Dialog kind="preview" title={`A4 inspection preview ${detail.event.id}`} onClose={closeOverlay} hideClose><div className="preview-toolbar"><strong>A4 inspection / {detail.event.id}</strong><button className="secondary" onClick={()=>setOverlay('summary')}>Back to summary</button><button className="primary" onClick={()=>{const frame=document.getElementById('report-preview') as HTMLIFrameElement;frame.contentWindow?.focus();frame.contentWindow?.print();}}>Print A4</button><button className="secondary" onClick={closeOverlay}>Close</button></div><iframe id="report-preview" title={`Printable inspection ${detail.event.id}`} src={`${api.reportUrl(state.session_id,detail.event.id,'print')}?embedded=true`} onLoad={()=>{const frame=document.getElementById('report-preview') as HTMLIFrameElement;frame.contentWindow?.focus();frame.contentWindow?.print();}} /></Dialog>}
  </div>;
}
