import type { EventDetail, PreferencesUpdate, ReplayCommand, Review, ReviewUpdate, Scenario, SessionState } from './contracts';

export class ApiError extends Error {
  constructor(public code: string, message: string, public status: number) { super(message); }
}

let csrfToken = '';
export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try { response = await fetch(`/api/v1${path}`, { ...options, headers: { 'Content-Type': 'application/json', ...(csrfToken && options?.method && options.method !== 'GET' ? {'X-CSRF-Token':csrfToken} : {}), ...options?.headers } }); }
  catch { throw new ApiError('CONNECTION_UNAVAILABLE', 'The local API is unavailable. Check that the Python service is running.', 0); }
  if (!response.ok) {
    if(response.status === 401 && path !== '/auth/session')window.dispatchEvent(new Event('fluo-auth-required'));
    const data = await response.json().catch(() => null);
    throw new ApiError(data?.error?.code ?? 'REQUEST_FAILED', data?.error?.message ?? `Request failed (${response.status})`, response.status);
  }
  if(response.status === 204)return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  authSession: async () => {const value=await request<{csrf_token:string;expires_at:string}>('/auth/session');csrfToken=value.csrf_token;return value;},
  startGuest: async () => {const value=await request<{csrf_token:string;expires_at:string}>('/auth/guest',{method:'POST',headers:{'Content-Type':'application/json','X-Fluo-Intent':'guest'},body:'{}'});csrfToken=value.csrf_token;return value;},
  logout: () => request<void>('/auth/logout',{method:'POST'}),
  scenarios: () => request<Scenario[]>('/scenarios'),
  create: () => request<SessionState>('/sessions', { method: 'POST', body: '{}' }),
  state: (id: string) => request<SessionState>(`/sessions/${encodeURIComponent(id)}`),
  command: (id: string, command: ReplayCommand) => request<SessionState>(`/sessions/${id}/replay`, { method: 'POST', body: JSON.stringify(command) }),
  preview: (id: string, cursor: number, signal: AbortSignal) => request<SessionState>(`/sessions/${id}/preview?cursor=${cursor}`, {signal}),
  detail: (id: string, event: string) => request<EventDetail>(`/sessions/${id}/events/${encodeURIComponent(event)}`),
  review: (id: string, event: string, data: ReviewUpdate, submit = false) => request<Review>(`/sessions/${id}/events/${encodeURIComponent(event)}/review${submit ? '/submit' : ''}`, { method: submit ? 'POST' : 'PUT', body: JSON.stringify(data) }),
  preferences: (id: string) => request<PreferencesUpdate>(`/sessions/${id}/preferences`),
  savePreferences: (id: string, data: PreferencesUpdate) => request<PreferencesUpdate>(`/sessions/${id}/preferences`, { method: 'PUT', body: JSON.stringify(data) }),
  reportUrl: (id: string, event: string, format: 'print' | 'report.pdf') => `/api/v1/sessions/${id}/events/${encodeURIComponent(event)}/${format}`,
};

export const timeLabel = (timestamp: string) => new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Jakarta', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(timestamp));
export const reading = (value: number | null, digits = 1) => value === null ? '—' : value.toFixed(digits);

export const modeLabel = (value: string) => value.charAt(0).toUpperCase() + value.slice(1);
