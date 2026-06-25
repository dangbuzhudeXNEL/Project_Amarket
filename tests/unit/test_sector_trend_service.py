"""SectorTrendService 单测（M3b）— 关注 news_heat 计算 + stub 数据回退。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlmodel import Session

from amarket.domain.enums import (
    ActionHint,
    ImpactHorizon,
    NewsCategory,
    Sentiment,
    SourcePriority,
)
from amarket.domain.models import NewsAnalysis, NewsItem, NewsSource, SectorTrend
from amarket.services.dashboard.sector_trend import (
    DEFAULT_SECTOR_NAMES,
    SectorTrendService,
)


@pytest.fixture
def seed_news_analyses(session: Session) -> None:
    """seed 1 source + 3 news + 3 analyses 关联到 '券商' / '银行' 板块。"""
    src = NewsSource(code="t", name="测试源", priority=SourcePriority.HIGH)
    session.add(src)
    session.commit()
    session.refresh(src)
    assert src.id is not None
    sid = src.id

    now = datetime.now(UTC)
    items = [
        NewsItem(
            source_id=sid,
            source_msg_id=f"m{i}",
            title=f"新闻{i}",
            published_at=now - timedelta(minutes=10 * i),
        )
        for i in range(3)
    ]
    session.add_all(items)
    session.commit()
    for it in items:
        session.refresh(it)
    iids = [it.id for it in items]
    assert all(x is not None for x in iids)

    # 2 个分析关联券商，1 个关联银行
    analyses = [
        NewsAnalysis(
            news_id=iids[0],
            primary_category=NewsCategory.MARKET,
            related_sectors=[{"name": "券商", "weight": 0.9}],
            sentiment=Sentiment.POSITIVE,
            importance_score=4,
            urgency_score=3,
            confidence_score=4,
            impact_horizon=ImpactHorizon.INTRADAY,
            action_hint=ActionHint.WATCH,
            processed_by="rule",
        ),
        NewsAnalysis(
            news_id=iids[1],
            primary_category=NewsCategory.MARKET,
            related_sectors=[{"name": "券商", "weight": 0.7}, {"name": "银行", "weight": 0.5}],
            sentiment=Sentiment.NEUTRAL,
            importance_score=3,
            urgency_score=2,
            confidence_score=3,
            impact_horizon=ImpactHorizon.INTRADAY,
            action_hint=ActionHint.WATCH,
            processed_by="rule",
        ),
        NewsAnalysis(
            news_id=iids[2],
            primary_category=NewsCategory.MARKET,
            related_sectors=[{"name": "保险", "weight": 0.6}],
            sentiment=Sentiment.NEGATIVE,
            importance_score=2,
            urgency_score=1,
            confidence_score=3,
            impact_horizon=ImpactHorizon.INTRADAY,
            action_hint=ActionHint.WATCH,
            processed_by="rule",
        ),
    ]
    session.add_all(analyses)
    session.commit()


def test_default_sector_names_has_14(session: Session) -> None:
    assert len(DEFAULT_SECTOR_NAMES) == 14
    assert "券商" in DEFAULT_SECTOR_NAMES


def test_list_sectors_empty_db_returns_14_with_zeros(session: Session) -> None:
    """空 DB（无 news + 无 SectorTrend）→ 返回 14 个板块，全 0 news_heat。"""
    svc = SectorTrendService(session)
    result = svc.list_sectors(window=timedelta(days=1))
    assert len(result) == 14
    for s in result:
        assert s.news_count_24h == 0
        assert s.change_pct is None  # M3b 默认 None
        # market_cap_weight stub 应有值
        assert s.market_cap_weight is not None
        assert s.top_symbols == []


def test_list_sectors_news_heat_from_analysis(
    session: Session, seed_news_analyses: None
) -> None:
    """有 news + analysis → 券商 heat=2，银行 heat=1，保险 heat=1。"""
    svc = SectorTrendService(session)
    result = svc.list_sectors(window=timedelta(days=1))
    by_name = {s.name: s for s in result}
    assert by_name["券商"].news_count_24h == 2
    assert by_name["银行"].news_count_24h == 1
    assert by_name["保险"].news_count_24h == 1
    # 没新闻的板块 = 0
    assert by_name["半导体"].news_count_24h == 0


def test_list_sectors_uses_sector_trend_change_pct_when_present(
    session: Session, seed_news_analyses: None
) -> None:
    """SectorTrend 表里有最近数据 → change_pct 用表里的。"""
    now = datetime.now(UTC)
    session.add(SectorTrend(ts=now, sector_name="券商", change_pct=2.5, news_heat=99))
    session.commit()

    svc = SectorTrendService(session)
    result = svc.list_sectors(window=timedelta(days=1))
    by_name = {s.name: s for s in result}
    # change_pct 用表里的（2.5），但 news_count_24h 用 NewsAnalysis 反查（实时更准）
    assert by_name["券商"].change_pct == 2.5
    assert by_name["券商"].news_count_24h == 2


def test_top_n_by_news_heat(session: Session, seed_news_analyses: None) -> None:
    svc = SectorTrendService(session)
    top3 = svc.top_n(by="news_heat", n=3, window=timedelta(days=1))
    assert len(top3) == 3
    # 第一名是 news_count_24h 最高（券商=2）
    assert top3[0].name == "券商"
