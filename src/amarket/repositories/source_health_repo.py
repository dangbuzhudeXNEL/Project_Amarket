"""SourceHealthRepo — 数据源探活记录。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlmodel import select

from amarket.domain.enums import SourceHealthStatus
from amarket.domain.models import SourceHealth
from amarket.repositories.base import BaseRepo


class SourceHealthRepo(BaseRepo[SourceHealth]):
    model = SourceHealth

    def record(
        self,
        *,
        source_id: int,
        status: SourceHealthStatus,
        latency_ms: float | None = None,
        error: str | None = None,
        items_returned: int = 0,
    ) -> SourceHealth:
        """记录一次健康探测。"""
        h = SourceHealth(
            source_id=source_id,
            status=status,
            latency_ms=latency_ms,
            error=(error or "")[:512] if error else None,
            items_returned=items_returned,
        )
        return self.add(h)

    def recent_for_source(
        self,
        source_id: int,
        *,
        window: timedelta = timedelta(hours=1),
        limit: int = 50,
    ) -> list[SourceHealth]:
        """近 N 小时该源的健康记录。"""
        since = datetime.now(UTC) - window
        stmt = (
            select(SourceHealth)
            .where(SourceHealth.source_id == source_id)
            .where(SourceHealth.ts >= since)
            .order_by(SourceHealth.ts.desc())  # type: ignore[attr-defined]
            .limit(limit)
        )
        return list(self.session.exec(stmt))


__all__ = ["SourceHealthRepo"]
