import pytest

from backend.auth import GuestSettings
from backend.store import open_store


def test_vercel_never_creates_authoritative_sqlite(monkeypatch, tmp_path):
    monkeypatch.setenv('VERCEL', '1')
    monkeypatch.delenv('FLUO_DATABASE_URL', raising=False)
    path = tmp_path / 'forbidden.sqlite3'
    with pytest.raises(RuntimeError, match='DURABLE_DATABASE_REQUIRED'):
        open_store(path)
    assert not path.exists()


def test_vercel_requires_public_mode_and_exact_https_origin(monkeypatch):
    monkeypatch.setenv('VERCEL', '1')
    monkeypatch.setenv('FLUO_DATABASE_URL', 'configuration-only; no connection in this test')
    monkeypatch.delenv('FLUO_PUBLIC_ORIGIN', raising=False)
    monkeypatch.delenv('RENDER_EXTERNAL_URL', raising=False)
    monkeypatch.setenv('FLUO_RELEASE_MODE', 'local')
    with pytest.raises(RuntimeError, match='VERCEL_PUBLIC_DATABASE_REQUIRED'):
        GuestSettings.from_env()
    monkeypatch.setenv('FLUO_RELEASE_MODE', 'public')
    monkeypatch.setenv('VERCEL_URL', '')
    with pytest.raises(RuntimeError, match='PUBLIC_ORIGIN_REQUIRED'):
        GuestSettings.from_env()
    monkeypatch.setenv('VERCEL_URL', 'deployment.example')
    settings = GuestSettings.from_env()
    assert settings.public_origin == 'https://deployment.example'
    assert settings.cookie_name == '__Host-fluo_guest'
    assert (settings.max_guests, settings.sessions_per_guest, settings.mutations_per_guest) == (50, 2, 200)
