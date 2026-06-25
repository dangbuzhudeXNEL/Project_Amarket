"""SectorTrendRepo — 板块趋势聚合表读写（M3b）。

M3b 阶段：表可能完全为空（M4 才有 APScheduler 写入），Repo 接口要稳。
"""

from __future__ import annotations

from sqlmodel import select

from amarket.domain.models import SectorTrend
from amarket.repositories.base import BaseRepo


class SectorTrendRepo(BaseRepo[SectorTrend]):
    model = SectorTrend

    def bulk_upsert(self, rows: list[SectorTrend]) -> int:
        """批量写入（M4 调度任务会调）。M3b 测试用。Returns: 写入行数。"""
        if not rows:
            return 0
        self.add_many(rows)
        return len(rows)

    def latest_for_sectors(self, sector_names: list[str]) -> dict[str, SectorTrend]:
        """每个 sector_name 取最新一条，dict[name -> row]。空表返回 {}。"""
        result: dict[str, SectorTrend] = {}
        for name in sector_names:
            stmt = (
                select(SectorTrend)
                .where(SectorTrend.sector_name == name)
                .order_by(SectorTrend.ts.desc())  # type: ignore[attr-defined]
                .limit(1)
            )
            row = self.session.exec(stmt).first()
            if row is not None:
                result[name] = row
        return result


__all__ = ["SectorTrendRepo"]
