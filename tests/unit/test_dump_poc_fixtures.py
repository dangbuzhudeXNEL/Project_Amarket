"""dump_poc_fixtures 单元测试 — 用 tmp SQLite + 种子数据。"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine

# 把 scripts/ 加入 sys.path 以便 import dump_poc_fixtures
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import dump_poc_fixtures as dpf  # noqa: E402

from amarket.domain.enums import (  # noqa: E402
    ActionHint,
    AlertLevel,
    ImpactHorizon,
    NewsCategory,
    Sentiment,
    SourcePriority,
)
from amarket.domain.models import (  # noqa: E402
    Alert,
    MarketSnapshot,
    NewsAnalysis,
    NewsItem,
    NewsSource,
)


@pytest.fixture
def tmp_engine(tmp_path: Path):
    """tmp SQLite + 全表创建。"""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def seeded_session(tmp_engine):
    """种入：1 source + 3 news + 2 analysis + 1 alert + 2 market_snapshot。"""
    with Session(tmp_engine) as s:
        src = NewsSource(
            code="ths", name="同花顺", priority=SourcePriority.HIGH, enabled=True
        )
        s.add(src)
        s.commit()
        s.refresh(src)

        n1 = NewsItem(
            source_id=src.id,
            source_msg_id="msg-1",
            title="央行降准 0.25%",
            summary="央行宣布降准...",
            url="https://example.com/n1",
            published_at=datetime(2026, 6, 24, 8, 30, tzinfo=UTC),
        )
        n2 = NewsItem(
            source_id=src.id,
            source_msg_id="msg-2",
            title="某公司发布业绩预告",
            summary="预增 50%",
            url="https://example.com/n2",
            published_at=datetime(2026, 6, 24, 9, 0, tzinfo=UTC),
        )
        n3 = NewsItem(
            source_id=src.id,
            source_msg_id="msg-3",
            title="盘后新闻 3",
            summary=None,
            url=None,
            published_at=datetime(2026, 6, 24, 15, 30, tzinfo=UTC),
        )
        s.add_all([n1, n2, n3])
        s.commit()
        for n in (n1, n2, n3):
            s.refresh(n)

        a1 = NewsAnalysis(
            news_id=n1.id,
            primary_category=NewsCategory.MACRO_POLICY,
            tags=["货币政策"],
            related_sectors=[{"name": "券商", "weight": 0.9}],
            related_symbols=[{"code": "601318", "name": "中国平安"}],
            sentiment=Sentiment.STRONG_POSITIVE,
            importance_score=5,
            urgency_score=5,
            confidence_score=5,
            impact_horizon=ImpactHorizon.IMMEDIATE,
            action_hint=ActionHint.FOLLOW,
            ai_reasoning="降准利好金融板块",
            processed_by="agent:news-classifier-realtime",
        )
        a2 = NewsAnalysis(
            news_id=n2.id,
            primary_category=NewsCategory.COMPANY_ANNOUNCEMENT,
            tags=["业绩预告"],
            sentiment=Sentiment.POSITIVE,
            importance_score=3,
            urgency_score=3,
            confidence_score=4,
            processed_by="rule",
        )
        s.add_all([a1, a2])
        s.commit()
        s.refresh(a1)

        alert = Alert(
            news_id=n1.id,
            level=AlertLevel.P0,
            trigger_reason="importance=5 + sentiment=strong_bull",
            analysis_id=a1.id,
            status="pushed",
            created_at=datetime(2026, 6, 24, 8, 31, tzinfo=UTC),
            pushed_at=datetime(2026, 6, 24, 8, 31, 5, tzinfo=UTC),
        )
        s.add(alert)

        ms1 = MarketSnapshot(
            ts=datetime(2026, 6, 24, 10, 0, tzinfo=UTC),
            asset_kind="index",
            code="sh000001",
            name="上证指数",
            price=3200.5,
            change_pct=0.5,
            change_abs=15.9,
            extra_json={"source": "akshare"},
        )
        ms2 = MarketSnapshot(
            ts=datetime(2026, 6, 24, 10, 0, tzinfo=UTC),
            asset_kind="index",
            code="sz399001",
            name="深证成指",
            price=10500.0,
            change_pct=-0.3,
            change_abs=-31.5,
            extra_json={"source": "akshare"},
        )
        s.add_all([ms1, ms2])
        s.commit()

        yield s, {
            "src_id": src.id,
            "news_ids": [n1.id, n2.id, n3.id],
            "alert_id": alert.id,
        }


# ===== Task 5 测试 — 骨架可调用 =====


def test_main_creates_empty_jsons(tmp_path, monkeypatch, tmp_engine):
    """空 DB 也能跑完不崩，输出 7 类 JSON 文件。"""
    out = tmp_path / "data"
    monkeypatch.setattr(
        "sys.argv",
        ["dump_poc_fixtures.py", "--db", str(tmp_engine.url), "--out", str(out)],
    )
    rc = dpf.main()
    assert rc == 0
    for name in ("dashboard", "news", "alerts", "sectors", "reports", "params"):
        assert (out / f"{name}.json").exists(), f"{name}.json missing"


# ===== Task 6 测试 =====


def test_dump_news_returns_enriched_dto(seeded_session):
    session, ids = seeded_session
    result = dpf.dump_news(session, limit=10)
    assert len(result) == 3, "should dump all 3 seeded news"
    # 按 published_at 倒序：n3 最新
    titles = [r["title"] for r in result]
    assert titles[0] == "盘后新闻 3"
    # 第一个 news (n1) 是降准，有完整 AI 分析
    rec = next(r for r in result if r["title"] == "央行降准 0.25%")
    assert rec["primary_category"] == "宏观政策"
    assert rec["sentiment"] == "强利多"
    assert rec["importance"] == 5
    assert rec["urgency"] == 5
    assert rec["confidence"] == 5
    assert rec["impact_horizon"] == "即时"
    assert rec["action_hint"] == "关注"
    assert rec["alert_level"] == "P0"
    assert rec["pushed"] is True
    assert rec["related_sectors"] == [{"name": "券商", "weight": 0.9}]
    assert rec["related_symbols"] == [{"code": "601318", "name": "中国平安"}]
    assert rec["source"] == "同花顺"


def test_dump_news_handles_no_analysis(seeded_session):
    """没分析的 news（n3）应该字段为 None / [] 但不崩。"""
    session, _ = seeded_session
    result = dpf.dump_news(session, limit=10)
    rec = next(r for r in result if r["title"] == "盘后新闻 3")
    assert rec["primary_category"] is None
    assert rec["sentiment"] is None
    assert rec["importance"] is None
    assert rec["alert_level"] is None
    assert rec["related_sectors"] == []


def test_dump_dashboard_aggregates(seeded_session):
    session, _ = seeded_session
    result = dpf.dump_dashboard(session, news_limit=10)
    assert "market_status" in result
    assert "latest_news" in result
    assert "p0_alerts" in result
    assert "p1_alerts" in result
    assert "today_conclusion" in result
    assert "today_reports" in result
    # market_status.indexes 至少包含 sh000001 / sz399001
    codes = [idx["code"] for idx in result["market_status"]["indexes"]]
    assert "sh000001" in codes
    assert "sz399001" in codes
    # P0 alerts 至少有种子的 1 条
    assert len(result["p0_alerts"]) >= 1


def test_dump_news_details_writes_per_id_files(seeded_session, tmp_path):
    session, ids = seeded_session
    ids_written = dpf.dump_news_details(session, tmp_path, limit=2, pretty=False)
    assert len(ids_written) == 2
    for nid in ids_written:
        f = tmp_path / f"news-detail-{nid}.json"
        assert f.exists()
        data = json.loads(f.read_text(encoding="utf-8"))
        assert data["news_id"] == nid
        assert "related_news" in data  # 详情比列表多 related_news
