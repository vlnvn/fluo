"""Local-only Fluo API and optional built frontend, using frozen ML inference."""
import json
import logging
import uuid
import secrets
import re
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .inference_adapter import ROOT, score_telemetry
from .reporting import html_report, pdf_report
from .schemas import CreateSession, Event, EventDetail, InferenceRequest, PreferencesUpdate, ReplayCommand, Review, ReviewUpdate, Scenario, SessionState
from .service import DomainError, ReplayService
from .security import LocalBoundary
from .auth import GuestAccess, GuestSettings

LOG = logging.getLogger('fluo.api')


def create_app(service=None, guest_settings=None):
    settings = guest_settings or GuestSettings.from_env()
    @asynccontextmanager
    async def lifespan(application):
        application.state.service = service or ReplayService()
        application.state.access = GuestAccess(application.state.service.store, settings)
        yield
        if service is None:
            application.state.service.store.close()

    api = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, title='Fluo research replay API', version='1.0.0', lifespan=lifespan,
                  description='Read-only simulated research telemetry; no equipment controls or verified operator authentication.')
    if service is not None:
        api.state.service = service

    api.add_middleware(LocalBoundary, allow_test_host=service is not None, public_origin=settings.public_origin)

    @api.middleware('http')
    async def correlation(request: Request, call_next):
        request.state.correlation_id = str(uuid.uuid4())
        request.state.csp_nonce = secrets.token_urlsafe(24)
        try:
            path = request.url.path
            if path.startswith('/api/v1/') and path != '/api/v1/auth/guest':
                owner = request.app.state.access.authorize(request)
                request.state.guest = owner
                match = re.match(r'^/api/v1/sessions/([^/]+)', path)
                if match and not request.app.state.service.store.owns_session(owner['digest'], match.group(1)):
                    raise DomainError('UNKNOWN_SESSION', 'This replay session is unavailable.', 404)
                if settings.public and path == '/api/v1/inference':
                    raise DomainError('GUEST_CAPABILITY_DENIED', 'Guest access is limited to the audited recorded scenarios.', 403)
            response = await call_next(request)
        except DomainError as error:
            response = JSONResponse({'error': {'code': error.code, 'message': error.message, 'correlation_id': request.state.correlation_id}}, status_code=error.status)
        except Exception:
            LOG.exception('Unhandled request failure correlation=%s', request.state.correlation_id)
            response = JSONResponse({'error': {'code': 'INTERNAL_ERROR', 'message': 'The local service could not complete this request.', 'correlation_id': request.state.correlation_id}}, status_code=500)
        if settings.public:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        response.headers['X-Correlation-ID'] = request.state.correlation_id
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        response.headers['Content-Security-Policy'] = f"default-src 'self'; script-src 'self' 'nonce-{request.state.csp_nonce}'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; media-src 'self'; connect-src 'self'; frame-src 'self'; frame-ancestors 'self'; object-src 'none'; base-uri 'none'; form-action 'self'"
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Cache-Control'] = 'no-store' if request.url.path.startswith('/api/') else 'no-cache'
        return response

    @api.exception_handler(DomainError)
    async def domain_error(request, error):
        return JSONResponse(status_code=error.status, content={'error': {'code': error.code, 'message': error.message, 'correlation_id': request.state.correlation_id}})

    @api.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        return JSONResponse(status_code=422, content={'error': {'code': 'INVALID_SCHEMA', 'message': 'Request does not match the versioned API schema.', 'details': [{'field': '.'.join(map(str, e['loc'])), 'message': e['msg']} for e in error.errors()], 'correlation_id': request.state.correlation_id}})

    def current(request):
        return request.app.state.service

    @api.post('/api/v1/auth/guest')
    def guest_entry(request: Request, response: Response):
        if request.headers.get('x-fluo-intent') != 'guest':
            raise DomainError('GUEST_INTENT_REQUIRED', 'Use the guest workspace entry.', 403)
        access = request.app.state.access
        try:
            owner = access.principal(request)
            return access.public_state(owner)
        except DomainError:
            token, owner = access.create()
        response.set_cookie(settings.cookie_name, token, max_age=settings.ttl_seconds, httponly=True, secure=settings.public, samesite='strict', path='/')
        return access.public_state(owner)

    @api.get('/api/v1/auth/session')
    def guest_session(request: Request):
        return request.app.state.access.public_state(request.state.guest)

    @api.post('/api/v1/auth/logout', status_code=204)
    def guest_logout(request: Request):
        request.app.state.service.store.revoke_guest(request.state.guest['digest'])
        response = Response(status_code=204)
        response.delete_cookie(settings.cookie_name, path='/', httponly=True, secure=settings.public, samesite='strict')
        return response

    @api.get('/health/live')
    def liveness():
        return {'status': 'alive'}

    @api.get('/health/ready')
    def readiness(request: Request):
        return {'status': 'ready', 'model_loaded': current(request).model is not None}

    @api.get('/api/v1/health')
    def health(request: Request):
        s = current(request)
        return {'status': 'ok', 'schema_version': '1.0', 'model_loaded': True, 'training_performed': False, 'read_only': True, 'lineage': s.lineage}

    @api.get('/api/v1/scenarios', response_model=list[Scenario])
    def scenarios(request: Request):
        s = current(request)
        return [s.public(v) for v in s.scenarios.values()]

    @api.post('/api/v1/sessions', response_model=SessionState, status_code=201)
    def create_session(body: CreateSession, request: Request):
        s = current(request)
        with s.store.lock:
            session = s.create(body.scenario_id, request.state.guest['digest'], settings.sessions_per_guest)
        return s.snapshot(session['id'])

    @api.get('/api/v1/sessions/{session_id}', response_model=SessionState)
    def snapshot(session_id: str, request: Request):
        return current(request).snapshot(session_id)

    @api.get('/api/v1/sessions/{session_id}/preview', response_model=SessionState)
    def preview(session_id: str, request: Request, cursor: int = Query(ge=0)):
        return current(request).snapshot(session_id, preview_cursor=cursor)

    @api.post('/api/v1/sessions/{session_id}/replay', response_model=SessionState)
    def command(session_id: str, body: ReplayCommand, request: Request):
        return current(request).command(session_id, body)

    @api.get('/api/v1/sessions/{session_id}/events', response_model=list[Event])
    def events(session_id: str, request: Request, category: str = Query('all', pattern='^(all|return|quality)$'), search: str = Query('', max_length=100), order: str = Query('desc', pattern='^(asc|desc)$')):
        rows = current(request).snapshot(session_id)['events']
        rows = [r for r in rows if (category == 'all' or r['category'] == category) and search.lower() in f"{r['id']} {r['title']} {r['state']}".lower()]
        return rows if order == 'desc' else list(reversed(rows))

    @api.get('/api/v1/sessions/{session_id}/events/{event_id}', response_model=EventDetail)
    def detail(session_id: str, event_id: str, request: Request):
        return current(request).detail(session_id, event_id)

    @api.put('/api/v1/sessions/{session_id}/events/{event_id}/review', response_model=Review)
    def save_review(session_id: str, event_id: str, body: ReviewUpdate, request: Request):
        return current(request).update_review(session_id, event_id, body)

    @api.post('/api/v1/sessions/{session_id}/events/{event_id}/review/submit', response_model=Review)
    def submit_review(session_id: str, event_id: str, body: ReviewUpdate, request: Request):
        return current(request).update_review(session_id, event_id, body, submit=True)

    @api.get('/api/v1/sessions/{session_id}/preferences')
    def preferences(session_id: str, request: Request):
        s = current(request)
        s.session(session_id)
        return s.store.preferences(session_id)

    @api.put('/api/v1/sessions/{session_id}/preferences', response_model=PreferencesUpdate)
    def save_preferences(session_id: str, body: PreferencesUpdate, request: Request):
        s = current(request)
        s.session(session_id)
        s.store.save_preferences(session_id, body.model_dump())
        return body

    @api.post('/api/v1/inference', response_model=list[dict])
    def infer(body: InferenceRequest, request: Request):
        data = pd.DataFrame([r.model_dump(mode='json') for r in body.rows])
        try:
            result = score_telemetry(data, current(request).model)
        except ValueError as error:
            raise DomainError('INVALID_TELEMETRY', str(error), 422) from error
        return json.loads(result.to_json(orient='records'))

    @api.get('/api/v1/sessions/{session_id}/events/{event_id}/report.pdf')
    def report(session_id: str, event_id: str, request: Request):
        detail = current(request).detail(session_id, event_id)
        return Response(pdf_report(detail), media_type='application/pdf', headers={'Content-Disposition': f'attachment; filename="Fluo-{detail["event"]["id"]}-inspection.pdf"'})

    @api.get('/api/v1/sessions/{session_id}/events/{event_id}/print', response_class=HTMLResponse)
    def print_report(session_id: str, event_id: str, request: Request, embedded: bool = False):
        return HTMLResponse(html_report(current(request).detail(session_id, event_id), session_id, embedded=embedded, nonce=request.state.csp_nonce))

    dist = ROOT / 'web/dist'
    if dist.exists():
        api.mount('/', StaticFiles(directory=dist, html=True), name='web')
    return api


app = create_app()
