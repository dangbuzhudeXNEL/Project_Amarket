"""NewsAnalysisService 集成测试（Spec v3 §6.1.4 — M2-e）。

覆盖：
- AI 路径成功 → 写 AI 结果
- AI 全失败 → 兜底规则路径
- ai_provider=None → 直接规则路径
- 幂等（同 news_id + processed_by upsert）
- 批处理 + 并发 + skip_existing
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from sqlmodel import Session, select

from amarket.adapters.ai.base import (
    NewsAnalysisRequest,
    NewsAnalysisResult,
    ProviderHealth,
)
from amarket.core.exceptions import AIError
from amarket.domain.enums import (
    ActionHint,
    ImpactHorizon,
    NewsCategory,
    ProcessingProvider,
    Sentiment,
)
from amarket.domain.models import NewsAnalysis, NewsItem
from amarket.domain.schemas import RawNewsItem
from amarket.repositories.news_repo import NewsRepo
from amarket.repositories.news_source_repo import NewsSourceRepo
from amarket.services.news.analysis import NewsAnalysisService
from amarket.services.news.classifier import NewsClassifier
from amarket.services.news.scorer import SimpleRuleScorer

# --------------------------------------------------------------------------- #
# Fake AI Providers
# --------------------------------------------------------------------------- #


class _FakeSuccessAIProvider:
    code = "agent:fake-success"
    enabled = True

    async def analyze_news(self, request: NewsAnalysisRequest) -> NewsAnalysisResult:
        return NewsAnalysisResult(
            primary_category=NewsCategory.MACRO_POLICY,
            tags=["AI算力", "半导体"],
            related_sectors=[{"name": "AI算力", "weight": 0.8}],
            related_symbols=[{"code": "688256", "name": "寒武纪", "weight": 1}],
            sentiment=Sentiment.POSITIVE,
            importance_score=4,
            urgency_score=3,
            confidence_score=4,
            impact_horizon=ImpactHorizon.SHORT_TERM,
            action_hint=ActionHint.FOLLOW,
            ai_reasoning="AI 测试输出 reasoning",
            risk_notes=None,
            processed_by=self.code,
            duration_ms=42,
            finished_at=datetime.now(UTC),
        )

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(code=self.code, enabled=True, configured=True, status="ok")


class _FakeFailingAIProvider:
    code = "agent:fake-fail"
    enabled = True

    async def analyze_news(self, request: NewsAnalysisRequest) -> NewsAnalysisResult:
        raise AIError("fake AI failure")

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(code=self.code, enabled=True, configured=True, status="degraded")


class _FakeDisabledAIProvider:
    code = "agent:fake-disabled"
    enabled = False

    async def analyze_news(self, request: NewsAnalysisRequest) -> NewsAnalysisResult:
        raise AIError("disabled")

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(code=self.code, enabled=False, configured=False, status="disabled")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _seed_source(session: Session, code: str = "src1") -> int:
    src = NewsSourceRepo(session).upsert(code=code, name=code.upper())
    assert src.id is not None
    return src.id


def _insert_item(
    session: Session,
    source_id: int,
    *,
    msg_id: str,
    title: str,
    summary: str | None = None,
) -> NewsItem:
    raw = RawNewsItem(
        source_code="src1",
        source_msg_id=msg_id,
        title=title,
        summary=summary,
        published_at=datetime.now(UTC),
    )
    item, _ = NewsRepo(session).upsert_from_raw(raw, source_id=source_id)
    return item


def _build_service(
    session: Session,
    *,
    ai_provider: Any | None = None,
) -> NewsAnalysisService:
    return NewsAnalysisService(
        session,
        classifier=NewsClassifier.from_config(),
        scorer=SimpleRuleScorer.from_config(),
        ai_provider=ai_provider,
    )


# --------------------------------------------------------------------------- #
# AI 成功路径
# --------------------------------------------------------------------------- #


async def test_analyze_one_ai_success(session: Session) -> None:
    src_id = _seed_source(session)
    item = _insert_item(session, src_id, msg_id="1", title="央行宣布降准")
    svc = _build_service(session, ai_provider=_FakeSuccessAIProvider())

    analysis = await svc.analyze_one(item)

    assert analysis.id is not None
    assert analysis.news_id == item.id
    assert analysis.primary_category == NewsCategory.MACRO_POLICY
    assert analysis.importance_score == 4
    assert analysis.processed_by == "agent:fake-success"
    assert analysis.duration_ms == 42
    assert analysis.ai_reasoning == "AI 测试输出 reasoning"
    # 行已落库
    in_db = session.exec(select(NewsAnalysis).where(NewsAnalysis.news_id == item.id)).first()
    assert in_db is not None
    assert in_db.processed_by == "agent:fake-success"


# --------------------------------------------------------------------------- #
# AI 失败 → 规则兜底
# --------------------------------------------------------------------------- #


async def test_analyze_one_ai_failure_falls_back_to_rule(session: Session) -> None:
    src_id = _seed_source(session)
    item = _insert_item(session, src_id, msg_id="1", title="央行宣布降准")
    svc = _build_service(session, ai_provider=_FakeFailingAIProvider())

    analysis = await svc.analyze_one(item)

    assert analysis.processed_by == ProcessingProvider.RULE.value
    # 规则路径用 classifier + scorer，应得出宏观政策分类
    assert analysis.primary_category == NewsCategory.MACRO_POLICY
    # confidence 应为 3（规则路径固定）
    assert analysis.confidence_score == 3
    assert analysis.ai_reasoning is None
    assert analysis.risk_notes is not None and "规则路径兜底" in analysis.risk_notes


# --------------------------------------------------------------------------- #
# AI provider = None → 强制规则路径
# --------------------------------------------------------------------------- #


async def test_analyze_one_no_ai_provider_uses_rule(session: Session) -> None:
    src_id = _seed_source(session)
    item = _insert_item(session, src_id, msg_id="1", title="央行降准")
    svc = _build_service(session, ai_provider=None)

    analysis = await svc.analyze_one(item)

    assert analysis.processed_by == ProcessingProvider.RULE.value


async def test_analyze_one_disabled_ai_provider_uses_rule(session: Session) -> None:
    src_id = _seed_source(session)
    item = _insert_item(session, src_id, msg_id="1", title="央行降准")
    svc = _build_service(session, ai_provider=_FakeDisabledAIProvider())

    analysis = await svc.analyze_one(item)

    assert analysis.processed_by == ProcessingProvider.RULE.value


# --------------------------------------------------------------------------- #
# 幂等
# --------------------------------------------------------------------------- #


async def test_analyze_one_is_idempotent_upsert(session: Session) -> None:
    """同一 news_id + processed_by 二次跑应是 upsert，不创建新行。"""
    src_id = _seed_source(session)
    item = _insert_item(session, src_id, msg_id="1", title="央行降准")
    svc = _build_service(session, ai_provider=_FakeSuccessAIProvider())

    a1 = await svc.analyze_one(item)
    a2 = await svc.analyze_one(item)

    assert a1.id == a2.id  # 同一行（upsert，不是 insert）
    # DB 中确实只有 1 行
    rows = session.exec(select(NewsAnalysis).where(NewsAnalysis.news_id == item.id)).all()
    assert len(rows) == 1


# --------------------------------------------------------------------------- #
# Batch
# --------------------------------------------------------------------------- #


async def test_analyze_batch_processes_all_items(session: Session) -> None:
    src_id = _seed_source(session)
    items = [
        _insert_item(session, src_id, msg_id=str(i), title=f"新闻 {i} 央行降准") for i in range(5)
    ]
    svc = _build_service(session, ai_provider=_FakeSuccessAIProvider())

    result = await svc.analyze_batch(items, concurrency=3)

    assert result.total == 5
    assert result.ai_success == 5
    assert result.rule_fallback == 0
    assert result.failed == 0
    assert result.analyses is not None
    assert len(result.analyses) == 5


async def test_analyze_batch_skip_existing(session: Session) -> None:
    """已分析过的 news_id 应跳过。"""
    src_id = _seed_source(session)
    items = [_insert_item(session, src_id, msg_id=str(i), title=f"新闻 {i}") for i in range(3)]
    svc = _build_service(session, ai_provider=_FakeSuccessAIProvider())

    # 首次分析全部
    first = await svc.analyze_batch(items, concurrency=2)
    assert first.ai_success == 3

    # 重跑 — 全部应被 skip
    second = await svc.analyze_batch(items, concurrency=2, skip_existing=True)
    assert second.skipped == 3
    assert second.ai_success == 0


async def test_analyze_batch_skip_provider_aware_rule_then_ai(session: Session) -> None:
    """Regression P1-1：rule 跑过的不该锁死 AI 路径。

    场景：用户先 --no-ai 跑 rule，后配 API key 想升级到 AI。AI 路径应该
    照常分析（不被 rule 行错跳）。
    """
    src_id = _seed_source(session)
    items = [
        _insert_item(session, src_id, msg_id=str(i), title=f"新闻 {i} 央行降准") for i in range(3)
    ]

    # Step 1: 先用规则路径（无 AI）跑一遍
    svc_rule = _build_service(session, ai_provider=None)
    first = await svc_rule.analyze_batch(items, concurrency=2)
    assert first.rule_fallback == 3

    # Step 2: 切到 AI 路径重跑（默认 skip_existing=True）— 不应被 rule 行锁死
    svc_ai = _build_service(session, ai_provider=_FakeSuccessAIProvider())
    second = await svc_ai.analyze_batch(items, concurrency=2)
    assert second.ai_success == 3  # AI 真的跑了
    assert second.skipped == 0


async def test_analyze_batch_skip_provider_aware_ai_then_rule(session: Session) -> None:
    """Regression P1-1（反方向）：AI 跑过的不该锁死 rule 重分析。"""
    src_id = _seed_source(session)
    items = [_insert_item(session, src_id, msg_id="1", title="新闻 央行降准")]

    # AI 先跑
    svc_ai = _build_service(session, ai_provider=_FakeSuccessAIProvider())
    first = await svc_ai.analyze_batch(items, concurrency=1)
    assert first.ai_success == 1

    # 切 rule 路径重跑 — 应正常跑（rule 行还没存在）
    svc_rule = _build_service(session, ai_provider=None)
    second = await svc_rule.analyze_batch(items, concurrency=1)
    assert second.rule_fallback == 1
    assert second.skipped == 0


async def test_analyze_batch_skip_same_path_twice(session: Session) -> None:
    """同 provider 路径重跑应正确跳过。"""
    src_id = _seed_source(session)
    items = [_insert_item(session, src_id, msg_id="1", title="新闻 央行降准")]

    svc = _build_service(session, ai_provider=_FakeSuccessAIProvider())
    first = await svc.analyze_batch(items, concurrency=1)
    assert first.ai_success == 1

    # 同样 AI 配置重跑 — 该跳过
    second = await svc.analyze_batch(items, concurrency=1)
    assert second.skipped == 1
    assert second.ai_success == 0


async def test_analyze_batch_mixed_failure_fallback(session: Session) -> None:
    """AI 失败的 item 自动走规则路径，统计为 rule_fallback。"""
    src_id = _seed_source(session)
    items = [
        _insert_item(session, src_id, msg_id=str(i), title=f"新闻 {i} 央行降准") for i in range(3)
    ]
    svc = _build_service(session, ai_provider=_FakeFailingAIProvider())

    result = await svc.analyze_batch(items, concurrency=2)
    assert result.total == 3
    assert result.ai_success == 0
    assert result.rule_fallback == 3
    assert result.failed == 0


async def test_analyze_batch_empty_input(session: Session) -> None:
    svc = _build_service(session)
    result = await svc.analyze_batch([], concurrency=2)
    assert result.total == 0
    assert result.analyses == []


async def test_analyze_batch_each_task_uses_independent_session(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression P1-5：analyze_batch 内每个 task 应创建独立 Session。

    防止未来加 async DB driver / await injection 时的 race。
    """
    from amarket.services.news import analysis as analysis_module

    src_id = _seed_source(session)
    items = [_insert_item(session, src_id, msg_id=str(i), title=f"新闻 {i}") for i in range(3)]

    # 计数 Session 构造调用
    session_count = 0
    original_session_cls = analysis_module.Session

    def counting_session(*args: Any, **kwargs: Any) -> Session:
        nonlocal session_count
        session_count += 1
        return original_session_cls(*args, **kwargs)

    monkeypatch.setattr(analysis_module, "Session", counting_session)

    svc = _build_service(session, ai_provider=_FakeSuccessAIProvider())
    result = await svc.analyze_batch(items, concurrency=2)

    assert result.ai_success == 3
    # 至少 3 次 Session 构造（每 task 一个独立 session）
    assert session_count >= 3


# --------------------------------------------------------------------------- #
# 边界 & 异常
# --------------------------------------------------------------------------- #


async def test_analyze_one_rejects_unsaved_item(session: Session) -> None:
    svc = _build_service(session)
    item = NewsItem(
        source_id=1,
        source_msg_id="x",
        title="尚未入库的 item",
        published_at=datetime.now(UTC),
    )  # id is None
    with pytest.raises(ValueError):
        await svc.analyze_one(item)
