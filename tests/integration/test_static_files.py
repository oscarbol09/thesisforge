"""Integration tests for SPA static files serving and CORS configuration."""

import pytest
from httpx import ASGITransport, AsyncClient

from thesisforge.api.app import create_app


@pytest.mark.asyncio
async def test_serve_spa_root_index_html() -> None:
    """Verify that root GET / serves the SPA index.html."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "ThesisForge" in response.text
        assert "alpinejs" in response.text or "Alpine" in response.text


@pytest.mark.asyncio
async def test_serve_spa_static_assets() -> None:
    """Verify that CSS tokens and JS files are served correctly with proper MIME types."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # CSS Tokens
        css_resp = await client.get("/css/tokens.css")
        assert css_resp.status_code == 200
        assert "text/css" in css_resp.headers.get("content-type", "")
        assert "--accent-primary" in css_resp.text

        # JS App Store
        js_resp = await client.get("/js/app.js")
        assert js_resp.status_code == 200
        assert "javascript" in js_resp.headers.get("content-type", "")
        assert "Alpine.store" in js_resp.text


@pytest.mark.asyncio
async def test_serve_favicon_endpoint() -> None:
    """Verify that GET /favicon.ico serves the favicon if present."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/favicon.ico")
        assert response.status_code == 200
        assert (
            "image" in response.headers.get("content-type", "").lower()
            or response.headers.get("content-type") == "application/octet-stream"
        )


@pytest.mark.asyncio
async def test_serve_static_assets_directory() -> None:
    """Verify that mounted /assets/ directory serves repository static brand assets."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/assets/logo.png")
        assert response.status_code == 200
        assert "image/png" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_api_routes_precedence_over_static_files() -> None:
    """Verify that API routes take priority over the mounted root static files."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Health check
        health_resp = await client.get("/health")
        assert health_resp.status_code == 200
        data = health_resp.json()
        assert data["status"] == "ok"
        assert "version" in data

        # API projects listing
        proj_resp = await client.get("/api/projects")
        assert proj_resp.status_code == 200
        assert isinstance(proj_resp.json(), list)


@pytest.mark.asyncio
async def test_security_csp_headers_contain_spa_allowlists() -> None:
    """Verify that SecurityHeadersMiddleware includes CDN allowances for Tailwind and Alpine."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health")
        csp = response.headers.get("Content-Security-Policy", "")
        assert "cdn.tailwindcss.com" in csp
        assert "cdn.jsdelivr.net" in csp
        assert "cdnjs.cloudflare.com" in csp
        assert "connect-src" in csp


@pytest.mark.asyncio
async def test_index_html_meta_csp_matches_headers() -> None:
    """Verify that gui/index.html's meta CSP tag explicitly includes required CDN domains."""
    import re
    from pathlib import Path

    index_path = Path("gui/index.html")
    assert index_path.is_file()
    content = index_path.read_text(encoding="utf-8")

    # Match content attribute of Content-Security-Policy meta tag
    match = re.search(
        r'<meta\s+http-equiv=["\']Content-Security-Policy["\']\s+content="([^"]+)"',
        content,
        re.IGNORECASE,
    )
    assert match is not None, "Content-Security-Policy meta tag not found in gui/index.html"
    csp_meta = match.group(1)

    # Required CDNs must be permitted in the meta CSP script-src
    assert "https://cdn.tailwindcss.com" in csp_meta
    assert "https://cdn.jsdelivr.net" in csp_meta
    assert "https://cdnjs.cloudflare.com" in csp_meta
