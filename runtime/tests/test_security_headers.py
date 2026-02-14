"""Tests for SecurityHeadersMiddleware — verifies all security headers are set."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from ailine_runtime.api.middleware.security_headers import SecurityHeadersMiddleware


def _hello(request: Request) -> PlainTextResponse:
    return PlainTextResponse("ok")


@pytest.fixture()
def app():
    """Minimal Starlette app with SecurityHeadersMiddleware."""
    a = Starlette(routes=[Route("/", _hello)])
    a.add_middleware(SecurityHeadersMiddleware)
    return a


@pytest.fixture()
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestSecurityHeaders:
    async def test_x_content_type_options(self, client: AsyncClient) -> None:
        resp = await client.get("/")
        assert resp.headers["X-Content-Type-Options"] == "nosniff"

    async def test_x_frame_options(self, client: AsyncClient) -> None:
        resp = await client.get("/")
        assert resp.headers["X-Frame-Options"] == "DENY"

    async def test_referrer_policy(self, client: AsyncClient) -> None:
        resp = await client.get("/")
        assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    async def test_permissions_policy(self, client: AsyncClient) -> None:
        resp = await client.get("/")
        pp = resp.headers["Permissions-Policy"]
        assert "camera=(self)" in pp
        assert "microphone=()" in pp
        assert "geolocation=()" in pp

    async def test_hsts(self, client: AsyncClient) -> None:
        resp = await client.get("/")
        hsts = resp.headers["Strict-Transport-Security"]
        assert "max-age=63072000" in hsts
        assert "includeSubDomains" in hsts

    async def test_csp(self, client: AsyncClient) -> None:
        resp = await client.get("/")
        csp = resp.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "script-src 'self' https://vlibras.gov.br" in csp
        assert "object-src 'none'" in csp
        assert "base-uri 'self'" in csp

    async def test_all_headers_present(self, client: AsyncClient) -> None:
        resp = await client.get("/")
        expected = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "Referrer-Policy",
            "Permissions-Policy",
            "Strict-Transport-Security",
            "Content-Security-Policy",
        ]
        for header in expected:
            assert header in resp.headers, f"Missing header: {header}"
