"""NewsSourceRepo — 新闻源配置 + 健康状态读写。"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import select

from amarket.domain.enums import SourcePriority
from amarket.domain.models import NewsSource
from amarket.repositories.base import BaseRepo


class NewsSourceRepo(BaseRepo[NewsSource]):
    model = NewsSource

    def get_by_code(self, code: str) -> NewsSource | None:
        stmt = select(NewsSource).where(NewsSource.code == code)
        return self.session.exec(stmt).first()

    def list_enabled(self) -> list[NewsSource]:
        stmt = select(NewsSource).where(NewsSource.enabled == True)  # noqa: E712
        return list(self.session.exec(stmt))

    def upsert(
        self,
        *,
        code: str,
        name: str,
        priority: SourcePriority = SourcePriority.MEDIUM,
        enabled: bool = True,
    ) -> NewsSource:
        """按 code 查找或新建。"""
        existing = self.get_by_code(code)
        if existing:
            existing.name = name
            existing.priority = priority
            existing.enabled = enabled
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing
        src = NewsSource(code=code, name=name, priority=priority, enabled=enabled)
        return self.add(src)

    def mark_pulled(self, source_id: int, *, success: bool, error: str | None = None) -> None:
        """更新最后拉取状态。"""
        src = self.get(source_id)
        if src is None:
            return
        src.last_pulled_at = datetime.now(UTC)
        if success:
            src.last_error = None
            src.consecutive_failures = 0
        else:
            src.last_error = (error or "")[:512]
            src.consecutive_failures += 1
        self.session.add(src)
        self.session.commit()


__all__ = ["NewsSourceRepo"]
