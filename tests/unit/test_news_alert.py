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


def test_evaluate_and_persist_upgrade_supersedes_old(session: Session) -> None:
    """Regression P1-2：升档时旧低优先级 alert 应被 superseded。

    场景：news_id=100 一开始 imp=3 urg=2 → P2；后重分析升到 imp=5 urg=5 风险事件
    → P0。旧 P2 行应被标 status='superseded'，新 P0 行 pending。M4 pusher
    只会推 P0，不会双推。
    """
    svc = AlertService(session)

    # Step 1: P2 alert（imp=3）
    ana_p2 = _make_analysis(primary=NewsCategory.MARKET, imp=3, urg=2, news_id=100)
    a_p2 = svc.evaluate_and_persist(ana_p2)
    assert a_p2 is not None
    assert a_p2.level == AlertLevel.P2
    assert a_p2.status == "pending"

    # Step 2: 重分析升到 P0（风险事件 imp=5 urg=5）
    ana_p0 = _make_analysis(primary=NewsCategory.RISK_EVENT, imp=5, urg=5, news_id=100)
    a_p0 = svc.evaluate_and_persist(ana_p0)
    assert a_p0 is not None
    assert a_p0.level == AlertLevel.P0
    assert a_p0.status == "pending"

    # P2 行应被 superseded（不删，留审计）
    session.refresh(a_p2)
    assert a_p2.status == "superseded"

    # DB 中 news_id=100 有 2 行 alert：1 个 pending P0 + 1 个 superseded P2
    rows = session.exec(select(Alert).where(Alert.news_id == 100)).all()
    assert len(rows) == 2
    pending = [a for a in rows if a.status == "pending"]
    assert len(pending) == 1
    assert pending[0].level == AlertLevel.P0


def test_evaluate_and_persist_downgrade_keeps_old_pending(session: Session) -> None:
    """降档（P0 → P2）不应 supersede 旧 P0（避免误丢更紧急告警）。

    设计选择：只升档 supersede，降档不动。如果先评 P0 后改 P2，旧 P0 还在
    pending — 假设是分析模型先报 false positive 后修正，但 P0 已发，应留痕。
    """
    svc = AlertService(session)

    # 先 P0
    ana_p0 = _make_analysis(primary=NewsCategory.RISK_EVENT, imp=5, urg=5, news_id=200)
    a_p0 = svc.evaluate_and_persist(ana_p0)
    assert a_p0 is not None and a_p0.status == "pending"

    # 后降到 P2
    ana_p2 = _make_analysis(primary=NewsCategory.MARKET, imp=3, urg=2, news_id=200)
    a_p2 = svc.evaluate_and_persist(ana_p2)
    assert a_p2 is not None and a_p2.level == AlertLevel.P2

    # P0 仍 pending（不应被 supersede）
    session.refresh(a_p0)
    assert a_p0.status == "pending"
    assert a_p2.status == "pending"


def test_process_analyses_batch_supersedes_correctly(session: Session) -> None:
    """process_analyses 批处理 — 同 news 后续高 level 也应 supersede 之前的。"""
    svc = AlertService(session)
    # 同 news_id 的两次分析，第二次升档
    analyses = [
        _make_analysis(primary=NewsCategory.MARKET, imp=3, urg=2, news_id=300),
        _make_analysis(primary=NewsCategory.RISK_EVENT, imp=5, urg=5, news_id=300),
    ]
    result = svc.process_analyses(analyses)
    assert result.p0 == 1
    assert result.p2 == 1

    # P2 应被 superseded
    rows = session.exec(select(Alert).where(Alert.news_id == 300)).all()
    assert len(rows) == 2
    pending = [a for a in rows if a.status == "pending"]
    superseded = [a for a in rows if a.status == "superseded"]
    assert len(pending) == 1 and pending[0].level == AlertLevel.P0
    assert len(superseded) == 1 and superseded[0].level == AlertLevel.P2


# --------------------------------------------------------------------------- #
# 黑名单 → 不生成 alert（P1-3）
# --------------------------------------------------------------------------- #


def test_blacklisted_news_does_not_generate_alert(session: Session) -> None:
    """Regression P1-3：命中黑名单的新闻即使评分高也不应生成 alert。

    场景：标题含"震惊"等黑名单关键词的模板新闻被规则误打高分，AlertService
    应该过滤掉，不写 alerts 表（news_analysis 行仍保留可审计）。
    """
    from amarket.domain.schemas import RawNewsItem
    from amarket.repositories.news_repo import NewsRepo
    from amarket.repositories.news_source_repo import NewsSourceRepo

    # 写一条标题含"震惊"的新闻
    src = NewsSourceRepo(session).upsert(code="test", name="TEST")
    raw = RawNewsItem(
        source_code="test",
        source_msg_id="bl-1",
        title="震惊！央行突发降准重大政策",
        published_at=datetime.now(UTC),
    )
    item, _ = NewsRepo(session).upsert_from_raw(raw, source_id=src.id or 1)

    # P0 级别的 analysis
    ana = _make_analysis(primary=NewsCategory.MACRO_POLICY, imp=5, urg=5, news_id=item.id or 1)

    # 不传 blacklist → 正常生成
    svc_no_filter = AlertService(session)
    alert1 = svc_no_filter.evaluate_and_persist(ana)
    assert alert1 is not None
    assert alert1.level == AlertLevel.P0

    # 把生成的 alert 撤掉，再用带黑名单的 service 跑
    session.delete(alert1)
    session.commit()

    svc_with_blacklist = AlertService(session, blacklist_keywords=["震惊", "速看"])
    alert2 = svc_with_blacklist.evaluate_and_persist(ana)
    assert alert2 is None  # 不生成
    # DB 中 alerts 表无对应行
    rows = session.exec(select(Alert).where(Alert.news_id == item.id)).all()
    assert len(rows) == 0


def test_blacklist_from_config_loads_keywords(session: Session) -> None:
    """AlertService.from_config 从真实 keywords.yml 加载黑名单。"""
    svc = AlertService.from_config(session)
    # 真实 config/keywords.yml 应有"震惊"等
    assert len(svc._blacklist) > 0
    assert "震惊" in svc._blacklist or "速看" in svc._blacklist


def test_process_analyses_skips_blacklisted_as_p3(session: Session) -> None:
    """批处理：黑名单新闻应被计入 p3_skipped 而非 p0/p1/p2。"""
    from amarket.domain.schemas import RawNewsItem
    from amarket.repositories.news_repo import NewsRepo
    from amarket.repositories.news_source_repo import NewsSourceRepo

    src = NewsSourceRepo(session).upsert(code="test", name="TEST")
    # 1 条黑名单 + 1 条正常
    raw1 = RawNewsItem(
        source_code="test",
        source_msg_id="bl-2",
        title="速看！央行降准",
        published_at=datetime.now(UTC),
    )
    raw2 = RawNewsItem(
        source_code="test",
        source_msg_id="normal-1",
        title="正常的高分新闻",
        published_at=datetime.now(UTC),
    )
    item_bl, _ = NewsRepo(session).upsert_from_raw(raw1, source_id=src.id or 1)
    item_ok, _ = NewsRepo(session).upsert_from_raw(raw2, source_id=src.id or 1)

    analyses = [
        _make_analysis(primary=NewsCategory.MACRO_POLICY, imp=5, urg=5, news_id=item_bl.id or 1),
        _make_analysis(primary=NewsCategory.MACRO_POLICY, imp=5, urg=5, news_id=item_ok.id or 2),
    ]
    svc = AlertService(session, blacklist_keywords=["速看"])
    result = svc.process_analyses(analyses)

    # 1 个 P0（正常）+ 1 个 p3_skipped（黑名单）
    assert result.p0 == 1
    assert result.p3_skipped == 1
    assert len(result.created_alert_ids) == 1


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
