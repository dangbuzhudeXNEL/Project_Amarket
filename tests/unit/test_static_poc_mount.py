"""FastAPI mount poc/ 静态目录测试（M3b）。"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_poc_index_html_served(api_client: TestClient) -> None:
    resp = api_client.get("/poc/index.html")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Amarket" in resp.text


def test_poc_shared_js_served(api_client: TestClient) -> None:
    resp = api_client.get("/poc/assets/js/shared.js")
    assert resp.status_code == 200
    # MIME 可能是 text/javascript 或 application/javascript
    ct = resp.headers["content-type"]
    assert "javascript" in ct or "text/plain" in ct
    assert "fetchJSON" in resp.text


def test_poc_unknown_404(api_client: TestClient) -> None:
    resp = api_client.get("/poc/does_not_exist.html")
    assert resp.status_code == 404
