"""API /api/reports/* 集成测试（M3b）。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session

from amarket.domain.enums import ReportKind
from amarket.domain.models import Report


@pytest.fixture
def seed_today_reports(patched_engine: Engine) -> None:
    with Session(patched_engine) as session:
        today = datetime.now(UTC).date()
        session.add(
            Report(
                date=today,
                kind=ReportKind.PREMARKET,
                status="completed",
                markdown="## 盘前\n- A",
                content_json={"sections": []},
                generated_by="agent:daily-report-writer",
                generated_at=datetime.now(UTC),
            )
        )
        session.add(
            Report(
                date=today,
                kind=ReportKind.MORNING,
                status="completed",
                markdown="## 早盘",
                generated_by="agent:daily-report-writer",
                generated_at=datetime.now(UTC),
            )
        )
        session.commit()


def test_reports_list_empty_db(api_client: TestClient) -> None:
    resp = api_client.get("/api/reports")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_reports_list_returns_items(
    api_client: TestClient, seed_today_reports: None
) -> None:
    resp = api_client.get("/api/reports")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    kinds = {it["kind"] for it in data["items"]}
    assert kinds == {"premarket", "morning"}
    # list view 不含 markdown（不污染列表）
    assert "markdown" not in data["items"][0]


def test_reports_list_filter_by_kind(
    api_client: TestClient, seed_today_reports: None
) -> None:
    resp = api_client.get("/api/reports?kind=premarket")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_reports_get_detail_includes_markdown(
    api_client: TestClient, seed_today_reports: None
) -> None:
    list_resp = api_client.get("/api/reports?kind=premarket")
    rid = list_resp.json()["items"][0]["report_id"]
    resp = api_client.get(f"/api/reports/{rid}")
    assert resp.status_code == 200
    data = resp.json()
    assert "## 盘前" in data["markdown"]
    assert data["content_json"] == {"sections": []}


def test_reports_get_detail_404(api_client: TestClient) -> None:
    resp = api_client.get("/api/reports/999999")
    assert resp.status_code == 404


def test_reports_today_returns_6_kinds(
    api_client: TestClient, seed_today_reports: None
) -> None:
    resp = api_client.get("/api/reports/today")
    assert resp.status_code == 200
    data = resp.json()
    assert set(data["reports_by_kind"].keys()) == {
        "premarket",
        "morning",
        "noon",
        "afternoon",
        "close",
        "evening",
    }
    assert data["reports_by_kind"]["premarket"]["status"] == "completed"
    assert data["reports_by_kind"]["evening"] is None


def test_reports_today_specific_kind(
    api_client: TestClient, seed_today_reports: None
) -> None:
    resp = api_client.get("/api/reports/today/premarket")
    assert resp.status_code == 200
    assert resp.json()["kind"] == "premarket"
    assert "## 盘前" in resp.json()["markdown"]


def test_reports_today_specific_kind_missing_returns_404(
    api_client: TestClient, seed_today_reports: None
) -> None:
    resp = api_client.get("/api/reports/today/evening")
    assert resp.status_code == 404
