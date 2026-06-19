"""API endpoint smoke tests: /healthz, /metrics, /docs。"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_healthz_returns_200_when_healthy(api_client: TestClient) -> None:
    resp = api_client.get("/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert "db" in body["checks"]
    assert body["checks"]["db"]["status"] == "ok"
    assert body["project_meta"]["current_phase"] == "Phase1"


def test_metrics_returns_prometheus_text(api_client: TestClient) -> None:
    resp = api_client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    body = resp.text
    assert "amarket_uptime_seconds" in body
    # Info metric exposes labels including spec_version
    assert "v3.0" in body


def test_openapi_schema_available(api_client: TestClient) -> None:
    resp = api_client.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    assert spec["info"]["title"] == "Project_Amarket"
    paths = spec["paths"]
    assert "/healthz" in paths
    # metrics 不在 schema（include_in_schema=False）
    assert "/metrics" not in paths
