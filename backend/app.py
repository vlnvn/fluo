"""Local-only Fluo API and optional built frontend, using frozen ML inference."""
import json
import logging
import uuid
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

LOG = logging.getLogger('fluo.api')


def create_app(service=None):
    @asynccontextmanager
    async def lifespan(application):
        application.state.service = service or ReplayService()
        yield

    api = FastAPI(title='Fluo research replay API', version='1.0.0', lifespan=lifespan,
                  description='Read-only simulated research telemetry; no equipment controls or verified operator authentication.')
    if service is not None:
        api.state.service = service

    @api.middleware('http')
    async def correlation(request: Request, call_next):
        request.state.correlation_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers['X-Correlation-ID'] = request.state.correlation_id
        response.headers['X-Content-Type-Options'] = 'nosniff'
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
        session = s.create(body.scenario_id)
        return s.snapshot(session['id'])

    @api.get('/api/v1/sessions/{session_id}', response_model=SessionState)
    def snapshot(session_id: str, request: Request):
        return current(request).snapshot(session_id)

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
    def print_report(session_id: str, event_id: str, request: Request):
        return HTMLResponse(html_report(current(request).detail(session_id, event_id), session_id))

    dist = ROOT / 'web/dist'
    if dist.exists():
        api.mount('/', StaticFiles(directory=dist, html=True), name='web')
    return api


app = create_app()
