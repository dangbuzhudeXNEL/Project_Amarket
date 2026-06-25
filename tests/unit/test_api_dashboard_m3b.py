"""M3b 新增的 dashboard endpoints 测试：sectors / movers / summary。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session

from amarket.domain.enums import (
    ActionHint,
    ImpactHorizon,
    NewsCategory,
    Sentiment,
    SourcePriority,
)
from amarket.domain.models import NewsAnalysis, NewsItem, NewsSource

# --------------------------------------------------------------------------- #
# /api/dashboard/sectors
# --------------------------------------------------------------------------- #


def test_sectors_empty_db_returns_14_with_zeros(api_client: TestClient) -> None:
    resp = api_client.get("/api/dashboard/sectors")
    assert resp.status_code == 200
    data = resp.json()
    assert "sectors" in data
    assert len(data["sectors"]) == 14
    assert all(s["news_count_24h"] == 0 for s in data["sectors"])
    assert all(s["change_pct"] is None for s in data["sectors"])
    # window 默认 1d
    assert data["window"] == "1d"


@pytest.fixture
def seed_sectors_data(patched_engine: Engine) -> None:
    with Session(patched_engine) as session:
        src = NewsSource(code="t", name="测试", priority=SourcePriority.HIGH)
        session.add(src)
        session.commit()
        session.refresh(src)
        assert src.id is not None
        sid = src.id

        item = NewsItem(
            source_id=sid,
            source_msg_id="m1",
            title="券商利好",
            published_at=datetime.now(UTC),
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        assert item.id is not None

        ana = NewsAnalysis(
            news_id=item.id,
            primary_category=NewsCategory.MARKET,
            related_sectors=[{"name": "券商", "weight": 0.9}],
            sentiment=Sentiment.POSITIVE,
            importance_score=4,
            urgency_score=3,
            confidence_score=4,
            impact_horizon=ImpactHorizon.INTRADAY,
            action_hint=ActionHint.WATCH,
            processed_by="rule",
        )
        session.add(ana)
        session.commit()


def test_sectors_news_heat_counted(
    api_client: TestClient, seed_sectors_data: None
) -> None:
    resp = api_client.get("/api/dashboard/sectors")
    assert resp.status_code == 200
    by_name = {s["name"]: s for s in resp.json()["sectors"]}
    assert by_name["券商"]["news_count_24h"] == 1
    assert by_name["银行"]["news_count_24h"] == 0


def test_sectors_window_param_accepts_short_windows(
    api_client: TestClient, seed_sectors_data: None
) -> None:
    """1h 窗口仍能拿到刚 seed 的（now-1min）那条。"""
    resp = api_client.get("/api/dashboard/sectors?window=1h")
    assert resp.status_code == 200
    data = resp.json()
    assert data["window"] == "1h"
    by_name = {s["name"]: s for s in data["sectors"]}
    assert by_name["券商"]["news_count_24h"] == 1


def test_sectors_invalid_window_falls_back_to_1d(
    api_client: TestClient, seed_sectors_data: None
) -> None:
    resp = api_client.get("/api/dashboard/sectors?window=bogus")
    assert resp.status_code == 200
    assert resp.json()["window"] == "1d"
