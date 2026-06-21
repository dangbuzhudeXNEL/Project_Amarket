"""NewsAnalysisRepo — AI / 规则分析结果读写（M2-e）。

按 `(news_id, processed_by)` 唯一约束 — 同一条新闻可被多 provider 多次分析，
但同一 provider 只保留最新一次。
"""

from __future__ import annotations

from datetime import datetime

from sqlmodel import and_, select

from amarket.domain.models import NewsAnalysis
from amarket.repositories.base import BaseRepo


class NewsAnalysisRepo(BaseRepo[NewsAnalysis]):
    model = NewsAnalysis

    # ----------------- 写 ----------------- #

    def upsert(self, analysis: NewsAnalysis) -> tuple[NewsAnalysis, bool]:
        """按 (news_id, processed_by) upsert。

        Returns: (row, created) — created=False 表示更新已有行。
        """
        existing = self.get_for_news(news_id=analysis.news_id, processed_by=analysis.processed_by)
        if existing is not None:
            # 更新所有可变字段
            existing.primary_category = analysis.primary_category
            existing.tags = analysis.tags
            existing.related_markets = analysis.related_markets
            existing.related_sectors = analysis.related_sectors
            existing.related_symbols = analysis.related_symbols
            existing.sentiment = analysis.sentiment
            existing.importance_score = analysis.importance_score
            existing.urgency_score = analysis.urgency_score
            existing.confidence_score = analysis.confidence_score
            existing.impact_horizon = analysis.impact_horizon
            existing.action_hint = analysis.action_hint
            existing.ai_reasoning = analysis.ai_reasoning
            existing.risk_notes = analysis.risk_notes
            existing.duration_ms = analysis.duration_ms
            existing.processed_at = analysis.processed_at
            existing.event_id = analysis.event_id
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing, False

        return self.add(analysis), True

    # ----------------- 读 ----------------- #

    def get_for_news(
        self,
        *,
        news_id: int,
        processed_by: str,
    ) -> NewsAnalysis | None:
        stmt = select(NewsAnalysis).where(
            and_(
                NewsAnalysis.news_id == news_id,
                NewsAnalysis.processed_by == processed_by,
            )
        )
        return self.session.exec(stmt).first()

    def list_for_news(self, *, news_id: int) -> list[NewsAnalysis]:
        """同一条新闻下的所有分析版本（多 provider）。"""
        stmt = (
            select(NewsAnalysis)
            .where(NewsAnalysis.news_id == news_id)
            .order_by(NewsAnalysis.processed_at.desc())  # type: ignore[attr-defined]
        )
        return list(self.session.exec(stmt))

    def list_recent(
        self,
        *,
        since: datetime | None = None,
        min_importance: int | None = None,
        limit: int = 100,
    ) -> list[NewsAnalysis]:
        """按 processed_at 倒序，可选按重要性过滤（M2-f AlertService 用）。"""
        stmt = select(NewsAnalysis).order_by(
            NewsAnalysis.processed_at.desc()  # type: ignore[attr-defined]
        )
        if since:
            stmt = stmt.where(NewsAnalysis.processed_at >= since)
        if min_importance is not None:
            stmt = stmt.where(NewsAnalysis.importance_score >= min_importance)
        stmt = stmt.limit(limit)
        return list(self.session.exec(stmt))


__all__ = ["NewsAnalysisRepo"]
