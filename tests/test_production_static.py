import os
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api import app, setup_static_routes


def test_production_static_serving(tmp_path):
    """
    Test static file serving and SPA fallback using an isolated temporary static directory.
    """
    # Create isolated mock static directory
    static_dir = tmp_path / "mock_static"
    static_dir.mkdir()
    assets_dir = static_dir / "assets"
    assets_dir.mkdir()

    # Create mock index.html
    index_file = static_dir / "index.html"
    index_content = "<!DOCTYPE html><html><head><title>GeneDxplorer</title></head><body><div id='root'></div></body></html>"
    index_file.write_text(index_content, encoding="utf-8")

    # Create mock asset
    asset_file = assets_dir / "main-test123.js"
    asset_file.write_text("console.log('genedxplorer asset');", encoding="utf-8")

    # Create mock root image asset
    bg_file = static_dir / "background.png"
    bg_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

    # Create a fresh isolated test FastAPI app
    test_app = FastAPI()

    # Register an API route first
    @test_app.get("/api/health")
    def health():
        return {"status": "ok"}

    # Attach static routes with the mock directory
    resolved = setup_static_routes(test_app, static_dir=str(static_dir))
    assert resolved == str(static_dir)

    client = TestClient(test_app)

    # 1. Homepage returns index.html
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "text/html" in res_root.headers.get("content-type", "")
    assert "GeneDxplorer" in res_root.text

    # 2. Valid client-side SPA routes fall back to index.html
    spa_routes = [
        "/about",
        "/discover",
        "/compare",
        "/workspace",
        "/disease/Alzheimer%27s%20disease",
        "/gene/APOE",
        "/graph",
        "/similarity",
        "/evidence",
        "/reproducibility/SNAP-123456"
    ]
    for route in spa_routes:
        res_spa = client.get(route)
        assert res_spa.status_code == 200, f"Route {route} failed with {res_spa.status_code}"
        assert "text/html" in res_spa.headers.get("content-type", "")
        assert "GeneDxplorer" in res_spa.text

    # 3. Existing static asset in /assets/ is served directly
    res_asset = client.get("/assets/main-test123.js")
    assert res_asset.status_code == 200
    assert "console.log('genedxplorer asset');" in res_asset.text

    # 4. Existing root static asset (/background.png) is served directly
    res_bg = client.get("/background.png")
    assert res_bg.status_code == 200

    # 5. Missing asset with file extension returns 404, NOT index.html
    res_missing_asset = client.get("/assets/nonexistent.js")
    assert res_missing_asset.status_code == 404
    assert "GeneDxplorer" not in res_missing_asset.text

    res_missing_root_asset = client.get("/missing_image.png")
    assert res_missing_root_asset.status_code == 404
    assert "GeneDxplorer" not in res_missing_root_asset.text

    # 6. Unknown API route returns 404, NOT index.html
    res_unknown_api = client.get("/api/unknown/endpoint")
    assert res_unknown_api.status_code == 404
    assert "GeneDxplorer" not in res_unknown_api.text

    # 7. Known API route works normally
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.json() == {"status": "ok"}


def test_backend_only_mode_when_static_dir_absent(tmp_path):
    """
    Test that API functions normally in pure backend mode when no frontend build exists.
    """
    test_app = FastAPI()

    @test_app.get("/api/health")
    def health():
        return {"status": "ok"}

    nonexistent_dir = str(tmp_path / "nonexistent_static_dir")
    resolved = setup_static_routes(test_app, static_dir=nonexistent_dir)
    assert resolved is None

    client = TestClient(test_app)

    # API works
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"

    # Root returns 404 (no frontend attached)
    res_root = client.get("/")
    assert res_root.status_code == 404


def test_primary_app_endpoints_and_docs():
    """
    Verify the primary production app instance still serves docs and API endpoints.
    """
    client = TestClient(app)

    # API health check
    res_h = client.get("/api/health")
    assert res_h.status_code == 200
    assert res_h.json()["status"] == "ok"

    # API ready check
    res_r = client.get("/api/ready")
    assert res_r.status_code == 200
    assert res_r.json()["status"] == "ready"

    # Unknown API path returns 404
    res_un = client.get("/api/nonexistent_subsystem")
    assert res_un.status_code == 404
    assert "GeneDxplorer" not in res_un.text

    # OpenAPI JSON schema
    res_openapi = client.get("/openapi.json")
    assert res_openapi.status_code == 200
    assert "openapi" in res_openapi.json()

