"""Opaque, expiring guest capabilities. Human/operator identity is not verified."""
import hashlib
import os
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlsplit

from .service_errors import DomainError


@dataclass(frozen=True)
class GuestSettings:
    public_origin: str = ''
    public: bool = False
    ttl_seconds: int = 7200
    max_guests: int = 200
    sessions_per_guest: int = 5
    mutations_per_guest: int = 500

    @classmethod
    def from_env(cls):
        mode = os.environ.get('FLUO_RELEASE_MODE', 'local')
        if mode not in ('local', 'public'):
            raise RuntimeError('INVALID_RELEASE_MODE')
        origin = os.environ.get('FLUO_PUBLIC_ORIGIN', os.environ.get('RENDER_EXTERNAL_URL', '')).rstrip('/')
        if mode == 'public':
            parsed = urlsplit(origin)
            if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment or parsed.hostname in ('localhost', '127.0.0.1'):
                raise RuntimeError('PUBLIC_ORIGIN_REQUIRED: provide the exact approved HTTPS origin')
            if not os.environ.get('FLUO_DB_PATH'):
                raise RuntimeError('PUBLIC_STATE_PATH_REQUIRED: configure the verified persistent volume')
        return cls(public=mode == 'public', public_origin=origin)

    @property
    def cookie_name(self):
        return '__Host-fluo_guest' if self.public else 'fluo_guest'


def token_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


class GuestAccess:
    def __init__(self, store, settings):
        self.store, self.settings = store, settings

    def principal(self, request):
        token = request.cookies.get(self.settings.cookie_name, '')
        if len(token) != 43:
            raise DomainError('AUTH_REQUIRED', 'Start a private guest workspace to continue.', 401)
        owner = self.store.guest(token_digest(token))
        if not owner or owner['revoked'] or owner['expires'] <= time.time():
            raise DomainError('AUTH_EXPIRED', 'This guest workspace has expired. Start a new workspace.', 401)
        return owner

    def check_csrf(self, request, owner):
        supplied = request.headers.get('x-csrf-token', '')
        if not secrets.compare_digest(supplied, owner['csrf']):
            raise DomainError('CSRF_REJECTED', 'The request could not be verified. Reload the workspace.', 403)

    def authorize(self, request):
        owner = self.principal(request)
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            self.check_csrf(request, owner)
            self.store.consume_guest_mutation(owner['digest'], self.settings.mutations_per_guest)
        return owner

    def create(self):
        token = secrets.token_urlsafe(32)
        owner = {'digest': token_digest(token), 'csrf': secrets.token_urlsafe(32),
                 'expires': time.time() + self.settings.ttl_seconds, 'revoked': 0, 'mutations': 0}
        self.store.create_guest(owner, self.settings.max_guests)
        return token, owner

    @staticmethod
    def public_state(owner):
        return {'guest': True, 'operator_verified': False, 'csrf_token': owner['csrf'],
                'expires_at': datetime.fromtimestamp(owner['expires'], timezone.utc).isoformat(),
                'capabilities': ['owned-replay', 'owned-reviews', 'owned-reports']}
