"""M3b 新增的 dashboard endpoints 测试：sectors / movers / summary。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session

from amarket.domain.enums import (
    ActionHint,
    AlertLevel,
    ImpactHorizon,
    NewsCategory,
    Sentiment,
    SourcePriority,
)
from amarket.domain.models import Alert, MarketSnapshot, NewsAnalysis, NewsItem, NewsSource

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


# --------------------------------------------------------------------------- #
# /api/dashboard/movers
# --------------------------------------------------------------------------- #


def test_movers_empty_db_returns_empty_lists(api_client: TestClient) -> None:
    resp = api_client.get("/api/dashboard/movers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["top_gainers"] == []
    assert data["top_losers"] == []


@pytest.fixture
def seed_market_snapshots(patched_engine: Engine) -> None:
    with Session(patched_engine) as session:
        rows = [
            MarketSnapshot(
                ts=datetime.now(UTC),
                asset_kind="stock",
                code="600000",
                name="浦发银行",
                price=10.5,
                change_pct=5.2,  # gainer
            ),
            MarketSnapshot(
                ts=datetime.now(UTC),
                asset_kind="stock",
                code="600519",
                name="贵州茅台",
                price=1700.0,
                change_pct=1.1,
            ),
            MarketSnapshot(
                ts=datetime.now(UTC),
                asset_kind="stock",
                code="000001",
                name="平安银行",
                price=11.2,
                change_pct=-3.8,  # loser
            ),
            MarketSnapshot(
                ts=datetime.now(UTC),
                asset_kind="stock",
                code="000333",
                name="美的集团",
                price=70.0,
                change_pct=-1.5,
            ),
            MarketSnapshot(
                ts=datetime.now(UTC),
                asset_kind="index",  # index 应该被过滤
                code="sh000001",
                name="上证",
                price=3200.0,
                change_pct=10.0,
            ),
        ]
        session.add_all(rows)
        session.commit()


def test_movers_returns_top_gainers_and_losers(
    api_client: TestClient, seed_market_snapshots: None
) -> None:
    resp = api_client.get("/api/dashboard/movers?n=2")
    assert resp.status_code == 200
    data = resp.json()
    # gainers desc by change_pct，过滤 asset_kind='stock'
    assert len(data["top_gainers"]) == 2
    assert data["top_gainers"][0]["code"] == "600000"
    assert data["top_gainers"][0]["change_pct"] == 5.2
    # losers asc by change_pct
    assert len(data["top_losers"]) == 2
    assert data["top_losers"][0]["code"] == "000001"
    assert data["top_losers"][0]["change_pct"] == -3.8
    # 不含 index
    all_codes = {m["code"] for m in data["top_gainers"] + data["top_losers"]}
    assert "sh000001" not in all_codes


def test_movers_n_param_bounded(api_client: TestClient, seed_market_snapshots: None) -> None:
    resp = api_client.get("/api/dashboard/movers?n=50")
    assert resp.status_code == 200
    # 只有 2 个 gainer + 2 个 loser
    assert len(resp.json()["top_gainers"]) == 2


# --------------------------------------------------------------------------- #
# /api/dashboard/summary
# --------------------------------------------------------------------------- #


def test_summary_empty_db_returns_skeleton(api_client: TestClient) -> None:
    resp = api_client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "as_of" in data
    assert "market_status" in data
    assert "latest_news" in data
    assert data["latest_news"] == []
    assert data["p0_alerts"] == []
    assert data["p1_alerts"] == []
    assert len(data["top_sectors"]) == 14  # 14 板块都给出（即使 heat=0）
    assert "today_reports" in data
    # 6 时段 key 都有，但 value 可能 null
    for kind in ("premarket", "morning", "noon", "afternoon", "close", "evening"):
        assert kind in data["today_reports"]


def test_summary_aggregates_alerts_by_level(
    api_client: TestClient, patched_engine: Engine
) -> None:
    """seed 一个 P0 + 一个 P1 + 一个 P2 → summary p0_alerts 1 个，p1_alerts 1 个。"""
    with Session(patched_engine) as session:
        src = NewsSource(code="t", name="测试", priority=SourcePriority.HIGH)
        session.add(src)
        session.commit()
        session.refresh(src)
        assert src.id is not None

        item = NewsItem(
            source_id=src.id,
            source_msg_id="m1",
            title="重大政策",
            published_at=datetime.now(UTC),
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        assert item.id is not None
        nid = item.id

        for lvl in (AlertLevel.P0, AlertLevel.P1, AlertLevel.P2):
            session.add(
                Alert(
                    news_id=nid,
                    level=lvl,
                    trigger_reason="test",
                    status="pending",
                    created_at=datetime.now(UTC),
                )
            )
        session.commit()

    resp = api_client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["p0_alerts"]) == 1
    assert len(data["p1_alerts"]) == 1
    assert data["p0_alerts"][0]["level"] == "P0"


def test_summary_latest_news_limit(api_client: TestClient, patched_engine: Engine) -> None:
    """seed 60 条新闻 → summary.latest_news 默认 30 条上限。"""
    with Session(patched_engine) as session:
        src = NewsSource(code="t", name="测试", priority=SourcePriority.HIGH)
        session.add(src)
        session.commit()
        session.refresh(src)
        assert src.id is not None
        for i in range(60):
            session.add(
                NewsItem(
                    source_id=src.id,
                    source_msg_id=f"m{i}",
                    title=f"新闻{i}",
                    published_at=datetime.now(UTC),
                )
            )
        session.commit()

    resp = api_client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    assert len(resp.json()["latest_news"]) == 30
