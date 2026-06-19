"""NewsEventRepo — 同事件聚合表（M2 起会大量用，M1 仅占位）。"""

from __future__ import annotations

from sqlmodel import select

from amarket.domain.models import NewsEvent
from amarket.repositories.base import BaseRepo


class NewsEventRepo(BaseRepo[NewsEvent]):
    model = NewsEvent

    def get_by_signature(self, signature: str) -> NewsEvent | None:
        stmt = select(NewsEvent).where(NewsEvent.signature == signature)
        return self.session.exec(stmt).first()


__all__ = ["NewsEventRepo"]
