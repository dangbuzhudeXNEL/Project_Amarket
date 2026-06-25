"""API endpoints: /api/news/* + /api/dashboard/* 集成测试。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session

from amarket.domain.enums import SourcePriority
from amarket.domain.schemas import IndexSnapshot, RawNewsItem
from amarket.repositories.market_snapshot_repo import MarketSnapshotRepo
from amarket.repositories.news_repo import NewsRepo
from amarket.repositories.news_source_repo import NewsSourceRepo


@pytest.fixture
def seed_news(patched_engine: Engine) -> dict[str, int]:
    """seed 2 个 source + 3 条新闻（用于 /api/news 测试）。"""
    with Session(patched_engine) as session:
        src_repo = NewsSourceRepo(session)
        a = src_repo.upsert(code="src_a", name="Source A", priority=SourcePriority.HIGH)
        b = src_repo.upsert(code="src_b", name="Source B", priority=SourcePriority.MEDIUM)
        a_id = a.id
        b_id = b.id
        assert a_id is not None
        assert b_id is not None

        news_repo = NewsRepo(session)
        news_repo.save_batch(
            [
                RawNewsItem(
                    source_code="src_a",
                    source_msg_id="a1",
                    title="A 第一条",
                    published_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
                ),
                RawNewsItem(
                    source_code="src_a",
                    source_msg_id="a2",
                    title="A 第二条",
                    published_at=datetime(2026, 6, 19, 9, 0, tzinfo=UTC),
                ),
            ],
            source_id=a_id,
        )
        news_repo.save_batch(
            [
                RawNewsItem(
                    source_code="src_b",
                    source_msg_id="b1",
                    title="B 唯一",
                    summary="摘要",
                    url="https://example.com/b1",
                    published_at=datetime(2026, 6, 19, 14, 0, tzinfo=UTC),
                ),
            ],
            source_id=b_id,
        )
    return {"a": a_id, "b": b_id}


def test_api_news_list_returns_all(api_client: TestClient, seed_news: dict[str, int]) -> None:
    resp = api_client.get("/api/news")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    # 按 published_at desc 排序，最新在前
    titles = [item["title"] for item in data["items"]]
    assert titles[0] == "B 唯一"


def test_api_news_filter_by_source(api_client: TestClient, seed_news: dict[str, int]) -> None:
    resp = api_client.get("/api/news?source=src_a")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    for item in data["items"]:
        assert item["source"] == "Source A"


def test_api_news_pagination(api_client: TestClient, seed_news: dict[str, int]) -> None:
    resp = api_client.get("/api/news?limit=1&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["total"] == 3
    assert data["limit"] == 1
    assert data["offset"] == 0


def test_api_news_get_by_id(api_client: TestClient, seed_news: dict[str, int]) -> None:
    list_resp = api_client.get("/api/news?limit=1")
    news_id = list_resp.json()["items"][0]["news_id"]
    resp = api_client.get(f"/api/news/{news_id}")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["news_id"] == news_id


def test_api_news_get_by_id_returns_detail_fields(
    api_client: TestClient, seed_news: dict[str, int]
) -> None:
    """GET /api/news/{id} 必须返回 NewsDetailDTO（含完整 AI 分析字段 + related_news）。

    M3b post-merge polish：列表用 NewsCardDTO 轻量；详情扩为 NewsDetailDTO 含全部字段。
    """
    list_resp = api_client.get("/api/news?limit=1")
    news_id = list_resp.json()["items"][0]["news_id"]
    resp = api_client.get(f"/api/news/{news_id}")
    assert resp.status_code == 200
    detail = resp.json()

    # NewsDetailDTO 独有字段（NewsCardDTO 没有的）必须都出现在响应里
    detail_only_fields = {
        "content",
        "confidence",
        "impact_horizon",
        "action_hint",
        "related_sectors",
        "related_symbols",
        "ai_reasoning",
        "risk_notes",
        "processed_by",
        "pushed",
        "related_news",
    }
    missing = detail_only_fields - set(detail.keys())
    assert not missing, f"NewsDetailDTO 缺字段：{missing}"

    # 默认值检查（无 analysis 时这些字段是 None / []）
    assert detail["related_sectors"] == []
    assert detail["related_symbols"] == []
    assert detail["related_news"] == []
    assert detail["pushed"] is False


def test_api_news_get_404(api_client: TestClient, seed_news: dict[str, int]) -> None:
    resp = api_client.get("/api/news/99999")
    assert resp.status_code == 404


def test_api_dashboard_market_status_empty(
    api_client: TestClient,
    patched_engine: Engine,
) -> None:
    """没数据时返回空 indexes 数组（不 500）。"""
    resp = api_client.get("/api/dashboard/market-status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["indexes"] == []


def test_api_dashboard_market_status_with_data(
    api_client: TestClient,
    patched_engine: Engine,
) -> None:
    with Session(patched_engine) as session:
        repo = MarketSnapshotRepo(session)
        repo.bulk_insert_index_snapshots(
            [
                IndexSnapshot(code="sh000001", name="上证指数", price=4090.5, change_pct=-0.43),
                IndexSnapshot(code="sz399001", name="深证成指", price=16030.7, change_pct=0.94),
            ]
        )

    resp = api_client.get("/api/dashboard/market-status")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["indexes"]) == 2
    codes = [idx["code"] for idx in data["indexes"]]
    assert "sh000001" in codes


def test_api_dashboard_news_sources(
    api_client: TestClient,
    seed_news: dict[str, int],
) -> None:
    resp = api_client.get("/api/dashboard/news-sources")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    codes = [s["code"] for s in data]
    assert "src_a" in codes
    assert "src_b" in codes
