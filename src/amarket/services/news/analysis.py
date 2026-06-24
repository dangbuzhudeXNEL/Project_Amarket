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
        # 抓 engine 用于 analyze_batch 创建每 task 独立 session（修 P1-5）
        bind = session.get_bind()
        from sqlalchemy.engine import Engine

        self._engine: Engine | None = bind if isinstance(bind, Engine) else None
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

        skip_existing=True：已有"同路径 provider"分析过的 news_id 跳过
        （AI 路径只在已有 AI 分析时跳；规则路径只在已有 rule 时跳）。
        """
        result = AnalysisBatchResult(total=len(items), analyses=[])

        # 过滤已分析的（按当前 provider 路径精确判定）
        to_process: list[NewsItem] = []
        for it in items:
            if it.id is None:
                continue
            if skip_existing and self._has_analysis_for_current_path(it.id):
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
            """每 task 独立 session（修 reviewer P1-5）。

            原方案：所有 coroutine 共享 self._session。当前 DB 操作是同步的、
            不释放 event loop，所以并发协程在 DB 步骤上等效串行 — 没爆。
            但很脆弱：未来如果 (a) 改 async DB driver / (b) 日志切 async sink /
            (c) repo 方法间塞 await，就会出现交叉 commit race。

            新方案：拿 engine 给每 task 起独立 Session(engine)。返回前 expunge
            让 NewsAnalysis 行可在 session 外访问（NewsAnalysis 无 lazy 关系）。
            """
            async with sem:
                # 若没有 engine（in-memory 或外部传入特殊 session），降级用共享 session
                if self._engine is None:
                    try:
                        return await self.analyze_one(it)
                    except Exception as exc:
                        log.error(
                            "analysis.unexpected_error",
                            news_id=it.id,
                            error=str(exc)[:200],
                        )
                        return None

                with Session(self._engine) as task_session:
                    try:
                        local_svc = NewsAnalysisService(
                            task_session,
                            classifier=self._classifier,
                            scorer=self._scorer,
                            ai_provider=self._ai,
                        )
                        # 重新在本 session fetch item（避免跨 session 用 detached 对象）
                        local_item = task_session.get(NewsItem, it.id)
                        if local_item is None:
                            return None
                        ana = await local_svc.analyze_one(local_item)
                        # detach: 让 caller 可在 session 外读 ana 的 scalar 字段
                        task_session.expunge(ana)
                        return ana
                    except Exception as exc:
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

    def _has_analysis_for_current_path(self, news_id: int) -> bool:
        """Provider-aware skip：检查"当前会走的路径"是否已分析过该 news。

        - AI 路径（self._ai enabled）：检查是否有 `agent:*` 或 `sdk:*` 行
        - 规则路径（self._ai disabled 或 None）：检查是否有 `rule` 行

        修 reviewer P1-1：原 `_has_any_analysis` 是 provider-agnostic，造成
        "rule 锁死" footgun — 用户先 `--no-ai` 跑了 rule，后续配 API key 想用 AI
        升级时，老 news 会被错跳过（除非加 --reanalyze）。
        """
        existing = self._repo.list_for_news(news_id=news_id)
        ai_enabled = self._ai is not None and self._ai.enabled
        rule_marker = ProcessingProvider.RULE.value
        for ana in existing:
            if ai_enabled:
                # AI 路径：任何非 rule 的（agent:* / sdk:*）都算"已分析"
                if ana.processed_by != rule_marker:
                    return True
            else:
                # 规则路径：只看 rule 行
                if ana.processed_by == rule_marker:
                    return True
        return False

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
