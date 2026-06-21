"""NewsRepo — 新闻原文读写。"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlmodel import and_, select

from amarket.domain.models import NewsItem, NewsSource
from amarket.domain.schemas import RawNewsItem
from amarket.repositories.base import BaseRepo


class NewsRepo(BaseRepo[NewsItem]):
    model = NewsItem

    # ----------------- 写 ----------------- #

    def upsert_from_raw(
        self,
        raw: RawNewsItem,
        *,
        source_id: int,
    ) -> tuple[NewsItem, bool]:
        """按 (source_id, source_msg_id) 唯一约束写入。

        Returns: (NewsItem, created: bool)。已存在则 created=False，不更新内容（新闻不可变）。
        """
        existing = self.get_by_source_msg_id(source_id=source_id, source_msg_id=raw.source_msg_id)
        if existing is not None:
            return existing, False

        item = NewsItem(
            source_id=source_id,
            source_msg_id=raw.source_msg_id,
            title=raw.title[:512],
            summary=raw.summary[:2048] if raw.summary else None,
            content=raw.content,
            url=raw.url[:1024] if raw.url else None,
            published_at=raw.published_at,
            raw_payload=raw.raw_payload or {},
        )
        return self.add(item), True

    def save_batch(
        self,
        raws: Sequence[RawNewsItem],
        *,
        source_id: int,
    ) -> tuple[int, int]:
        """批量保存。Returns: (inserted_count, skipped_count)。"""
        inserted = 0
        skipped = 0
        for raw in raws:
            _, created = self.upsert_from_raw(raw, source_id=source_id)
            if created:
                inserted += 1
            else:
                skipped += 1
        return inserted, skipped

    # ----------------- 读 ----------------- #

    def get_by_source_msg_id(
        self,
        *,
        source_id: int,
        source_msg_id: str,
    ) -> NewsItem | None:
        stmt = select(NewsItem).where(
            and_(
                NewsItem.source_id == source_id,
                NewsItem.source_msg_id == source_msg_id,
            )
        )
        return self.session.exec(stmt).first()

    def list_recent(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        source_code: str | None = None,
        since: datetime | None = None,
    ) -> list[tuple[NewsItem, NewsSource]]:
        """最新新闻列表，JOIN news_sources 拿 source 名字。"""
        stmt = (
            select(NewsItem, NewsSource)
            .join(NewsSource, NewsItem.source_id == NewsSource.id)  # type: ignore[arg-type]
            .order_by(NewsItem.published_at.desc())  # type: ignore[attr-defined]
            .offset(offset)
            .limit(limit)
        )
        if source_code:
            stmt = stmt.where(NewsSource.code == source_code)
        if since:
            stmt = stmt.where(NewsItem.published_at >= since)
        return list(self.session.exec(stmt))

    def list_without_event(self, *, limit: int = 500) -> list[NewsItem]:
        """列出尚未分配 event_id 的新闻（M2-b NewsDeduper 的输入源）。"""
        stmt = (
            select(NewsItem)
            .where(NewsItem.event_id.is_(None))  # type: ignore[union-attr]
            .order_by(NewsItem.published_at.desc())  # type: ignore[attr-defined]
            .limit(limit)
        )
        return list(self.session.exec(stmt))

    def count_filtered(
        self,
        *,
        source_code: str | None = None,
        since: datetime | None = None,
    ) -> int:
        from sqlalchemy import func

        stmt = (
            select(func.count())
            .select_from(NewsItem)
            .join(NewsSource, NewsItem.source_id == NewsSource.id)  # type: ignore[arg-type]
        )
        if source_code:
            stmt = stmt.where(NewsSource.code == source_code)
        if since:
            stmt = stmt.where(NewsItem.published_at >= since)
        return int(self.session.exec(stmt).one())


__all__ = ["NewsRepo"]
