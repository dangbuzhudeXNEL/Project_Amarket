"""NewsEventRepo — 同事件聚合表（M2 起会大量用）。"""

from __future__ import annotations

from datetime import datetime

from sqlmodel import select

from amarket.domain.models import NewsEvent
from amarket.repositories.base import BaseRepo


class NewsEventRepo(BaseRepo[NewsEvent]):
    model = NewsEvent

    def get_by_signature(self, signature: str) -> NewsEvent | None:
        stmt = select(NewsEvent).where(NewsEvent.signature == signature)
        return self.session.exec(stmt).first()

    def get_by_canonical_title(self, canonical_title: str) -> NewsEvent | None:
        """精确匹配 normalize 后的标题（M2-b L2 去重）。"""
        stmt = select(NewsEvent).where(NewsEvent.canonical_title == canonical_title)
        return self.session.exec(stmt).first()

    def list_recent(
        self,
        *,
        since: datetime,
        limit: int = 200,
    ) -> list[NewsEvent]:
        """最近活跃的 event（last_seen_at >= since），按 last_seen_at 倒序。

        用于 M2-b L3 SimHash 距离匹配 — 候选集不取全表，限近窗口。
        """
        stmt = (
            select(NewsEvent)
            .where(NewsEvent.last_seen_at >= since)
            .order_by(NewsEvent.last_seen_at.desc())  # type: ignore[attr-defined]
            .limit(limit)
        )
        return list(self.session.exec(stmt))


__all__ = ["NewsEventRepo"]
