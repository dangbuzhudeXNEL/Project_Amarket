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
