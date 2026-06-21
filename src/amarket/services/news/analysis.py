"""NewsAnalysisService — 编排 Classifier + AIProvider + Scorer，写 news_analysis 表（M2-e）。

工作流（Spec v3 §6.1.4 + §9.1）：
    NewsItem
      ↓
    NewsClassifier (规则一级 / 二级标签 / 板块 / 标的)
      ↓
    AIProvider.analyze_news() (FallbackChain: Brainmaster → Anthropic → DeepSeek)
      ↓ 全部失败
    SimpleRuleScorer (importance / urgency / sentiment 规则兜底)
      ↓
    NewsAnalysis row (按 processed_by 区分版本，写入 news_analysis 表)

幂等性：同一 (news_id, processed_by) 的分析会 upsert（不重复创建行）。
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlmodel import Session

from amarket.adapters.ai.base import AIProvider, NewsAnalysisRequest, NewsAnalysisResult
from amarket.adapters.ai.factory import build_default_ai_provider
from amarket.core.exceptions import AIError
from amarket.core.logging import get_logger
from amarket.domain.enums import (
    ActionHint,
    ImpactHorizon,
    NewsCategory,
    ProcessingProvider,
    Sentiment,
    SourcePriority,
)
from amarket.domain.models import NewsAnalysis, NewsItem, NewsSource
from amarket.repositories.news_analysis_repo import NewsAnalysisRepo
from amarket.services.news.classifier import (
    ClassificationResult,
    NewsClassifier,
    SectorMatch,
    SymbolMatch,
)
from amarket.services.news.scorer import ScoringResult, SimpleRuleScorer

log = get_logger(__name__)


# --------------------------------------------------------------------------- #
# 结果 DTO（批处理统计）
# --------------------------------------------------------------------------- #


@dataclass
class AnalysisBatchResult:
    total: int = 0
    ai_success: int = 0  # AI 路径成功
    rule_fallback: int = 0  # 兜底到规则
    skipped: int = 0  # 跳过已分析
    failed: int = 0  # 异常（既非 AIError 又非可恢复）
    analyses: list[NewsAnalysis] | None = None


# 规则路径默认值映射（一级分类 → action_hint）
_CATEGORY_DEFAULT_ACTION: dict[NewsCategory, ActionHint] = {
    NewsCategory.RISK_EVENT: ActionHint.AVOID,
    NewsCategory.MACRO_POLICY: ActionHint.FOLLOW,
    NewsCategory.OVERSEAS: ActionHint.FOLLOW,
    NewsCategory.COMPANY_ANNOUNCEMENT: ActionHint.WATCH,
    NewsCategory.MARKET: ActionHint.WATCH,
    NewsCategory.FUND_FLOW: ActionHint.WATCH,
    NewsCategory.COMMODITY: ActionHint.WATCH,
    NewsCategory.TRADE_HINT: ActionHint.WATCH,
}


# --------------------------------------------------------------------------- #
# Service
# --------------------------------------------------------------------------- #


class NewsAnalysisService:
    """新闻深度分析编排服务。"""

    def __init__(
        self,
        session: Session,
        *,
        classifier: NewsClassifier,
        scorer: SimpleRuleScorer,
        ai_provider: AIProvider | None = None,
    ) -> None:
        self._session = session
        self._classifier = classifier
        self._scorer = scorer
        self._ai = ai_provider
        self._repo = NewsAnalysisRepo(session)
        self._source_cache: dict[int, NewsSource | None] = {}

    @classmethod
    def from_config(
        cls,
        session: Session,
        *,
        use_ai: bool = True,
    ) -> NewsAnalysisService:
        """便捷构造：从默认 config/ 加载规则 + 默认 AI fallback chain。"""
        return cls(
            session,
            classifier=NewsClassifier.from_config(),
            scorer=SimpleRuleScorer.from_config(),
            ai_provider=build_default_ai_provider() if use_ai else None,
        )

    # ---------------- 公共入口 ---------------- #

    async def analyze_one(self, item: NewsItem) -> NewsAnalysis:
        """完整分析一条新闻 — 跑分类 + AI 或兜底 + 写库。"""
        if item.id is None:
            raise ValueError("NewsItem must be persisted (id required) before analysis")

        src = self._get_source(item.source_id)
        src_priority = src.priority if src else SourcePriority.MEDIUM

        # 1. 规则分类（永远跑 — 给 AI 上下文，也是兜底用）
        classification = self._classifier.classify(title=item.title, summary=item.summary)

        # 2. 尝试 AI（如果 enabled）
        ai_result: NewsAnalysisResult | None = None
        if self._ai is not None and self._ai.enabled:
            try:
                ai_result = await self._ai.analyze_news(
                    self._build_ai_request(item, classification)
                )
            except AIError as exc:
                log.warning(
                    "analysis.ai_failed_fallback_to_rule",
                    news_id=item.id,
                    error=str(exc)[:160],
                )

        # 3. 构造 NewsAnalysis
        if ai_result is not None:
            analysis = self._build_from_ai(item, ai_result)
        else:
            score = self._scorer.score(
                title=item.title,
                summary=item.summary,
                classification=classification,
                source_priority=src_priority,
                published_at=item.published_at,
            )
            analysis = self._build_from_rule(item, classification, score)

        # 4. 写库（upsert by news_id + processed_by）
        analysis, _created = self._repo.upsert(analysis)
        return analysis

    async def analyze_batch(
        self,
        items: Sequence[NewsItem],
        *,
        concurrency: int = 5,
        skip_existing: bool = True,
    ) -> AnalysisBatchResult:
        """批量分析。AI 路径并发受 concurrency 控制；规则路径串行（快，无需并发）。

        skip_existing=True：已有任意 processed_by 分析过的 news_id 跳过。
        """
        result = AnalysisBatchResult(total=len(items), analyses=[])

        # 过滤已分析的
        to_process: list[NewsItem] = []
        for it in items:
            if it.id is None:
                continue
            if skip_existing and self._has_any_analysis(it.id):
                result.skipped += 1
                continue
            to_process.append(it)

        if not to_process:
            log.info(
                "analysis.batch_done",
                total=result.total,
                skipped=result.skipped,
                processed=0,
            )
            return result

        sem = asyncio.Semaphore(concurrency)

        async def _run_one(it: NewsItem) -> NewsAnalysis | None:
            async with sem:
                try:
                    return await self.analyze_one(it)
                except Exception as exc:  # 兜底：单条失败不拖垮 batch
                    log.error(
                        "analysis.unexpected_error",
                        news_id=it.id,
                        error=str(exc)[:200],
                    )
                    return None

        analyses = await asyncio.gather(*(_run_one(it) for it in to_process))

        assert result.analyses is not None
        for ana in analyses:
            if ana is None:
                result.failed += 1
                continue
            result.analyses.append(ana)
            if ana.processed_by == ProcessingProvider.RULE.value:
                result.rule_fallback += 1
            else:
                result.ai_success += 1

        log.info(
            "analysis.batch_done",
            total=result.total,
            skipped=result.skipped,
            ai_success=result.ai_success,
            rule_fallback=result.rule_fallback,
            failed=result.failed,
        )
        return result

    # ---------------- 内部辅助 ---------------- #

    def _get_source(self, source_id: int) -> NewsSource | None:
        if source_id not in self._source_cache:
            self._source_cache[source_id] = self._session.get(NewsSource, source_id)
        return self._source_cache[source_id]

    def _has_any_analysis(self, news_id: int) -> bool:
        return len(self._repo.list_for_news(news_id=news_id)) > 0

    def _build_ai_request(
        self, item: NewsItem, classification: ClassificationResult
    ) -> NewsAnalysisRequest:
        src = self._get_source(item.source_id)
        return NewsAnalysisRequest(
            news_id=item.id or 0,
            title=item.title,
            summary=item.summary,
            content=item.content,
            source=src.code if src else "unknown",
            published_at=item.published_at,
            rule_primary_category=classification.primary_category,
            rule_tags=classification.tags,
            rule_importance=None,  # M2-e 不传规则分（避免锚定 bias）
            similar_news_titles=[],  # M2+ 可填入近 24h 同类 top 3
        )

    def _build_from_ai(
        self,
        item: NewsItem,
        ai_result: NewsAnalysisResult,
    ) -> NewsAnalysis:
        """AI 路径 → NewsAnalysis ORM。"""
        assert item.id is not None
        return NewsAnalysis(
            news_id=item.id,
            event_id=item.event_id,
            primary_category=ai_result.primary_category,
            tags=list(ai_result.tags),
            related_markets=[],  # AI 当前 schema 不强制 markets，留空
            related_sectors=list(ai_result.related_sectors),
            related_symbols=list(ai_result.related_symbols),
            sentiment=ai_result.sentiment,
            importance_score=ai_result.importance_score,
            urgency_score=ai_result.urgency_score,
            confidence_score=ai_result.confidence_score,
            impact_horizon=ai_result.impact_horizon,
            action_hint=ai_result.action_hint,
            ai_reasoning=ai_result.ai_reasoning,
            risk_notes=ai_result.risk_notes,
            processed_by=ai_result.processed_by,
            processed_at=ai_result.finished_at,
            duration_ms=ai_result.duration_ms,
        )

    def _build_from_rule(
        self,
        item: NewsItem,
        classification: ClassificationResult,
        score: ScoringResult,
    ) -> NewsAnalysis:
        """规则路径兜底 → NewsAnalysis ORM。"""
        assert item.id is not None
        return NewsAnalysis(
            news_id=item.id,
            event_id=item.event_id,
            primary_category=classification.primary_category,
            tags=list(classification.tags),
            related_markets=[],
            related_sectors=[_sector_to_dict(s) for s in classification.related_sectors],
            related_symbols=[_symbol_to_dict(s) for s in classification.related_symbols],
            sentiment=score.sentiment,
            importance_score=score.importance,
            urgency_score=score.urgency,
            confidence_score=score.confidence,
            impact_horizon=ImpactHorizon.INTRADAY,
            action_hint=_CATEGORY_DEFAULT_ACTION.get(
                classification.primary_category, ActionHint.WATCH
            ),
            ai_reasoning=None,
            risk_notes=(
                "规则路径兜底（AI 全部不可用 / 失败）"
                if classification.is_blacklisted is False
                else "规则路径兜底；命中黑名单关键词"
            ),
            processed_by=ProcessingProvider.RULE.value,
            processed_at=datetime.now(UTC),
            duration_ms=None,
        )


def _sector_to_dict(s: SectorMatch) -> dict[str, object]:
    return {"name": s.name, "weight": s.weight}


def _symbol_to_dict(s: SymbolMatch) -> dict[str, object]:
    return {"name": s.name, "weight": s.weight}


__all__ = [
    "AnalysisBatchResult",
    "NewsAnalysisService",
]


# 抑制未使用 import 提示（Sentiment 通过 typing 间接用到）
_ = Sentiment
