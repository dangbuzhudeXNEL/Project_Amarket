"""ReportRepo — 6 时段日报表读写（M3b）。

M3b 阶段：只提供读接口给 /api/reports/*；写接口（generate / push）等 M4 ReportService。
"""

from __future__ import annotations

from datetime import date as date_t

from sqlmodel import select

from amarket.domain.enums import ReportKind
from amarket.domain.models import Report
from amarket.repositories.base import BaseRepo


class ReportRepo(BaseRepo[Report]):
    model = Report

    def list_recent(
        self,
        *,
        kind: ReportKind | None = None,
        date_from: date_t | None = None,
        date_to: date_t | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Report]:
        """按 date desc, generated_at desc 排序。"""
        stmt = select(Report).order_by(
            Report.date.desc(),  # type: ignore[attr-defined]
            Report.generated_at.desc(),  # type: ignore[attr-defined]
        )
        if kind is not None:
            stmt = stmt.where(Report.kind == kind)
        if date_from is not None:
            stmt = stmt.where(Report.date >= date_from)
        if date_to is not None:
            stmt = stmt.where(Report.date <= date_to)
        stmt = stmt.offset(offset).limit(limit)
        return list(self.session.exec(stmt))

    def count_filtered(
        self,
        *,
        kind: ReportKind | None = None,
        date_from: date_t | None = None,
        date_to: date_t | None = None,
    ) -> int:
        from sqlalchemy import func

        stmt = select(func.count()).select_from(Report)
        if kind is not None:
            stmt = stmt.where(Report.kind == kind)
        if date_from is not None:
            stmt = stmt.where(Report.date >= date_from)
        if date_to is not None:
            stmt = stmt.where(Report.date <= date_to)
        return int(self.session.exec(stmt).one())

    def today_by_kind(
        self,
        *,
        kind: ReportKind,
        today: date_t,
    ) -> Report | None:
        """同 date + kind 唯一约束 — 命中即唯一。"""
        stmt = select(Report).where(Report.date == today).where(Report.kind == kind).limit(1)
        return self.session.exec(stmt).first()

    def list_today(self, *, today: date_t) -> dict[str, Report | None]:
        """今日 6 时段：返回 dict[kind_str -> Report | None]。"""
        result: dict[str, Report | None] = {k.value: None for k in ReportKind}
        stmt = select(Report).where(Report.date == today)
        for r in self.session.exec(stmt):
            result[r.kind.value] = r
        return result


__all__ = ["ReportRepo"]
