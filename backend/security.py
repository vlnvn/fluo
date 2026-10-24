"""Defence in depth for a loopback demo; this does not provide authentication."""
import asyncio
import time
from collections import defaultdict, deque
from urllib.parse import urlsplit

from starlette.responses import JSONResponse

MAX_BODY = 4 * 1024 * 1024
LOCAL_HOSTS = {'localhost', '127.0.0.1', '::1'}
LOCAL_ORIGINS = {f'http://{host}:{port}' for host in ('localhost', '127.0.0.1') for port in (5173, 8000)}


class LocalBoundary:
    """Bound request memory and rates before JSON parsing, including chunked bodies."""

    def __init__(self, app, max_body=MAX_BODY, rate_limit=600, allow_test_host=False, public_origin=''):
        self.app, self.max_body, self.rate_limit = app, max_body, rate_limit
        self.hosts = LOCAL_HOSTS | ({'testserver'} if allow_test_host else set())
        self.origins = LOCAL_ORIGINS | ({public_origin} if public_origin else set())
        if public_origin:
            self.hosts = {urlsplit(public_origin).hostname} | ({'testserver'} if allow_test_host else set())
            self.origins = {public_origin}
        self.windows = defaultdict(deque)

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        headers = dict(scope.get('headers', []))
        host = headers.get(b'host', b'').decode('latin1')
        try:
            hostname = urlsplit('http://' + host).hostname
        except ValueError:
            hostname = None
        if hostname not in self.hosts:
            return await self.reject(scope, receive, send, 400, 'UNTRUSTED_HOST')
        origin = headers.get(b'origin', b'').decode('latin1')
        if scope['method'] not in ('GET', 'HEAD', 'OPTIONS') and origin and origin not in self.origins:
            return await self.reject(scope, receive, send, 403, 'UNTRUSTED_ORIGIN')
        if len(scope.get('query_string', b'')) > 8192:
            return await self.reject(scope, receive, send, 414, 'QUERY_TOO_LONG')
        if scope['path'].startswith('/api/'):
            # One process, bounded map; reads and expensive/writing requests have separate budgets.
            now = time.monotonic()
            key = (scope.get('client', ('local', 0))[0], scope['method'] not in ('GET', 'HEAD') or scope['path'].endswith(('/report.pdf', '/inference')))
            if len(self.windows) > 2048:
                self.windows.clear()
            window = self.windows[key]
            while window and window[0] < now - 60:
                window.popleft()
            limit = self.rate_limit if key[1] else self.rate_limit * 4
            if scope['path'] == '/api/v1/auth/guest':
                key = (scope.get('client', ('local', 0))[0], 'guest-entry')
                window = self.windows[key]
                while window and window[0] < now - 60:
                    window.popleft()
                limit = 60
            if len(window) >= limit:
                return await self.reject(scope, receive, send, 429, 'RATE_LIMITED')
            window.append(now)
        try:
            length = int(headers.get(b'content-length', b'0'))
        except ValueError:
            return await self.reject(scope, receive, send, 400, 'INVALID_LENGTH')
        if length < 0 or length > self.max_body:
            return await self.reject(scope, receive, send, 413, 'BODY_TOO_LARGE')
        if scope['method'] in ('POST', 'PUT', 'PATCH'):
            messages, total = [], 0
            while True:
                try:
                    message = await asyncio.wait_for(receive(), timeout=10)
                except TimeoutError:
                    return await self.reject(scope, receive, send, 408, 'BODY_TIMEOUT')
                if message['type'] == 'http.disconnect':
                    return
                total += len(message.get('body', b''))
                if total > self.max_body:
                    return await self.reject(scope, receive, send, 413, 'BODY_TOO_LARGE')
                messages.append(message)
                if not message.get('more_body', False):
                    break
            iterator = iter(messages)

            async def buffered():
                message = next(iterator, None)
                return message if message is not None else await receive()

            return await self.app(scope, buffered, send)
        await self.app(scope, receive, send)

    @staticmethod
    async def reject(scope, receive, send, status, code):
        response = JSONResponse({'error': {'code': code, 'message': 'Request rejected by local demo boundary.'}}, status_code=status, headers={'Cache-Control': 'no-store', 'Retry-After': '60'} if status == 429 else {'Cache-Control': 'no-store'})
        await response(scope, receive, send)


def assert_local_release():
    from .auth import GuestSettings
    GuestSettings.from_env()
