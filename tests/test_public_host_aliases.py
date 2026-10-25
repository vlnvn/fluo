"""Exact public-host allowlist for verified Vercel deployment aliases."""
import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from backend.security import LocalBoundary


def app_with_hosts(primary="https://fluo-original.vercel.app"):
    app = Starlette(routes=[Route("/", lambda request: PlainTextResponse("ok"), methods=["GET", "POST"])])
    app.add_middleware(LocalBoundary, public_origin=primary)
    return app


def test_exact_origin_and_vercel_aliases(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VERCEL_URL", "fluo-deployment.vercel.app")
    monkeypatch.setenv("VERCEL_PROJECT_PRODUCTION_URL", "fluo-prod.vercel.app")
    monkeypatch.setenv("FLUO_EXTRA_PUBLIC_ORIGINS", "https://fluo-review.vercel.app")
    app = app_with_hosts()
    for host in ("fluo-original.vercel.app", "fluo-deployment.vercel.app", "fluo-prod.vercel.app", "fluo-review.vercel.app"):
        with TestClient(app, base_url=f"https://{host}") as client:
            assert client.get("/").status_code == 200
            assert client.post("/", headers={"Origin": f"https://{host}"}).status_code == 200
    with TestClient(app, base_url="https://unknown.vercel.app") as client:
        assert client.get("/").json()["error"]["code"] == "UNTRUSTED_HOST"


def test_reject_cross_alias_origin_and_host_spoof(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VERCEL_URL", "fluo-deployment.vercel.app")
    monkeypatch.delenv("VERCEL_PROJECT_PRODUCTION_URL", raising=False)
    monkeypatch.setenv("FLUO_EXTRA_PUBLIC_ORIGINS", "https://fluo-review.vercel.app")
    with TestClient(app_with_hosts(), base_url="https://fluo-deployment.vercel.app") as client:
        assert client.post("/", headers={"Origin": "https://fluo-review.vercel.app"}).json()["error"]["code"] == "UNTRUSTED_ORIGIN"
        assert client.get("/", headers={"Host": "attacker.invalid"}).status_code == 400
        assert client.get("/", headers={"Host": "fluo-deployment.vercel.app:8443"}).status_code == 400


def test_reject_wildcard_and_non_https_alias(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("FLUO_EXTRA_PUBLIC_ORIGINS", "https://*.vercel.app")
    with pytest.raises(RuntimeError, match="INVALID_PUBLIC_HOST_ORIGIN"):
        with TestClient(app_with_hosts()):
            pass
    monkeypatch.setenv("FLUO_EXTRA_PUBLIC_ORIGINS", "http://fluo-review.vercel.app")
    with pytest.raises(RuntimeError, match="INVALID_PUBLIC_HOST_ORIGIN"):
        with TestClient(app_with_hosts()):
            pass


def test_local_demo_hosts_remain_unchanged(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("FLUO_EXTRA_PUBLIC_ORIGINS", raising=False)
    app = Starlette(routes=[Route("/", lambda request: PlainTextResponse("ok"))])
    app.add_middleware(LocalBoundary)
    with TestClient(app, base_url="http://localhost:8000") as client:
        assert client.get("/").status_code == 200
    with TestClient(app, base_url="http://foreign.invalid") as client:
        assert client.get("/").status_code == 400
