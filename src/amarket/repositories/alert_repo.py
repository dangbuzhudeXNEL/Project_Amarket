"""AlertRepo — P0-P3 告警表读写（M2-f）。"""

from __future__ import annotations

from datetime import datetime

from sqlmodel import and_, select

from amarket.domain.enums import AlertLevel
from amarket.domain.models import Alert
from amarket.repositories.base import BaseRepo


class AlertRepo(BaseRepo[Alert]):
    model = Alert

    def get_for_news_and_level(
        self,
        *,
        news_id: int,
        level: AlertLevel,
    ) -> Alert | None:
        """同一 news_id + level 只保留一行（幂等检查）。"""
        stmt = select(Alert).where(and_(Alert.news_id == news_id, Alert.level == level))
        return self.session.exec(stmt).first()

    def list_recent(
        self,
        *,
        since: datetime | None = None,
        levels: list[AlertLevel] | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[Alert]:
        """按 created_at 倒序，可选按 level / status 过滤。"""
        stmt = select(Alert).order_by(Alert.created_at.desc())  # type: ignore[attr-defined]
        if since:
            stmt = stmt.where(Alert.created_at >= since)
        if levels:
            stmt = stmt.where(Alert.level.in_(levels))  # type: ignore[attr-defined]
        if status:
            stmt = stmt.where(Alert.status == status)
        stmt = stmt.limit(limit)
        return list(self.session.exec(stmt))

    def list_pending(self, *, limit: int = 100) -> list[Alert]:
        return self.list_recent(status="pending", limit=limit)


__all__ = ["AlertRepo"]
