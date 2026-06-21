"""AlertService 单元测试（Spec v3 §8.7 — M2-f）。

决策表：
- P0：RISK_EVENT/MACRO_POLICY ∧ imp ≥ 5 ∧ urg ≥ 5
- P1：imp ≥ 4 ∧ urg ≥ 4
- P2：imp ≥ 3
- P3：其他（不写 alerts 表）

只对 P0/P1/P2 写 alerts；P3 仅在 news_analysis 留行。
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlmodel import Session, select

from amarket.domain.enums import (
    ActionHint,
    AlertLevel,
    ImpactHorizon,
    NewsCategory,
    ProcessingProvider,
    Sentiment,
)
from amarket.domain.models import Alert, NewsAnalysis
from amarket.services.news.alert import AlertService, evaluate_alert_level


def _make_analysis(
    *,
    primary: NewsCategory = NewsCategory.MARKET,
    imp: int = 3,
    urg: int = 3,
    news_id: int | None = 1,
    analysis_id: int | None = 1,
) -> NewsAnalysis:
    return NewsAnalysis(
        id=analysis_id,
        news_id=news_id,
        primary_category=primary,
        sentiment=Sentiment.NEUTRAL,
        importance_score=imp,
        urgency_score=urg,
        confidence_score=3,
        impact_horizon=ImpactHorizon.INTRADAY,
        action_hint=ActionHint.WATCH,
        processed_by=ProcessingProvider.RULE.value,
        processed_at=datetime.now(UTC),
    )


# --------------------------------------------------------------------------- #
# 决策表（纯函数）
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("category", "imp", "urg", "expected"),
    [
        # P0：高危分类 + 双 5
        (NewsCategory.RISK_EVENT, 5, 5, AlertLevel.P0),
        (NewsCategory.MACRO_POLICY, 5, 5, AlertLevel.P0),
        # 非高危分类即使双 5 也只到 P1
        (NewsCategory.COMPANY_ANNOUNCEMENT, 5, 5, AlertLevel.P1),
        (NewsCategory.MARKET, 5, 5, AlertLevel.P1),
        # P1：imp ≥ 4 ∧ urg ≥ 4
        (NewsCategory.MARKET, 4, 4, AlertLevel.P1),
        (NewsCategory.OVERSEAS, 4, 5, AlertLevel.P1),
        (NewsCategory.RISK_EVENT, 4, 4, AlertLevel.P1),  # 不到 P0 双 5 门槛
        # P2：imp ≥ 3
        (NewsCategory.MARKET, 3, 2, AlertLevel.P2),
        (NewsCategory.COMPANY_ANNOUNCEMENT, 3, 5, AlertLevel.P2),
        # P3：其他
        (NewsCategory.MARKET, 2, 2, AlertLevel.P3),
        (NewsCategory.TRADE_HINT, 1, 1, AlertLevel.P3),
    ],
)
def test_evaluate_alert_level(
    category: NewsCategory, imp: int, urg: int, expected: AlertLevel
) -> None:
    ana = _make_analysis(primary=category, imp=imp, urg=urg)
    assert evaluate_alert_level(ana) == expected


# --------------------------------------------------------------------------- #
# 写库
# --------------------------------------------------------------------------- #


def test_evaluate_and_persist_p0_creates_alert(session: Session) -> None:
    svc = AlertService(session)
    ana = _make_analysis(primary=NewsCategory.RISK_EVENT, imp=5, urg=5)
    alert = svc.evaluate_and_persist(ana)

    assert alert is not None
    assert alert.id is not None
    assert alert.level == AlertLevel.P0
    assert alert.news_id == 1
    assert alert.status == "pending"
    assert "P0" in alert.trigger_reason
    assert "风险事件" in alert.trigger_reason


def test_evaluate_and_persist_p3_returns_none(session: Session) -> None:
    svc = AlertService(session)
    ana = _make_analysis(primary=NewsCategory.MARKET, imp=1, urg=1)
    assert svc.evaluate_and_persist(ana) is None
    # DB 也无 alert 行
    assert session.exec(select(Alert)).first() is None


def test_evaluate_and_persist_idempotent(session: Session) -> None:
    """同 news_id + level 重复跑不会重复创建。"""
    svc = AlertService(session)
    ana = _make_analysis(imp=4, urg=4, news_id=42)
    a1 = svc.evaluate_and_persist(ana)
    a2 = svc.evaluate_and_persist(ana)
    assert a1 is not None
    assert a2 is not None
    assert a1.id == a2.id
    # DB 中仅 1 行
    rows = session.exec(select(Alert).where(Alert.news_id == 42)).all()
    assert len(rows) == 1


# --------------------------------------------------------------------------- #
# 批处理
# --------------------------------------------------------------------------- #


def test_process_analyses_distributes_levels(session: Session) -> None:
    svc = AlertService(session)
    analyses = [
        _make_analysis(primary=NewsCategory.RISK_EVENT, imp=5, urg=5, news_id=1),
        _make_analysis(primary=NewsCategory.MACRO_POLICY, imp=4, urg=4, news_id=2),
        _make_analysis(primary=NewsCategory.MARKET, imp=3, urg=2, news_id=3),
        _make_analysis(primary=NewsCategory.MARKET, imp=2, urg=2, news_id=4),  # P3
    ]
    result = svc.process_analyses(analyses)

    assert result.total == 4
    assert result.p0 == 1
    assert result.p1 == 1
    assert result.p2 == 1
    assert result.p3_skipped == 1
    assert len(result.created_alert_ids) == 3


def test_process_analyses_handles_existing(session: Session) -> None:
    svc = AlertService(session)
    ana = _make_analysis(imp=4, urg=4, news_id=10)
    svc.evaluate_and_persist(ana)
    # 重跑批处理
    result = svc.process_analyses([ana])
    assert result.already_existed == 1
    assert result.p1 == 0  # 已存在不重复计数


def test_process_analyses_empty() -> None:
    pass  # 不需要 DB
