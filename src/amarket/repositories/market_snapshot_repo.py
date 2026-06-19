"""MarketSnapshotRepo — 行情快照读写。"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlmodel import and_, select

from amarket.domain.models import MarketSnapshot
from amarket.domain.schemas import IndexSnapshot
from amarket.repositories.base import BaseRepo


class MarketSnapshotRepo(BaseRepo[MarketSnapshot]):
    model = MarketSnapshot

    # ----------------- 写 ----------------- #

    def bulk_insert_index_snapshots(self, snapshots: list[IndexSnapshot]) -> int:
        """把 IndexSnapshot DTO 批量插入。Returns: 插入行数。"""
        rows = [
            MarketSnapshot(
                ts=snap.fetched_at,
                asset_kind="index",
                code=snap.code,
                name=snap.name,
                price=snap.price,
                change_pct=snap.change_pct,
                change_abs=snap.change_abs,
                volume=snap.volume,
                turnover=snap.turnover,
                extra_json={
                    "source": snap.source,
                    "prev_close": snap.prev_close,
                    "trading_date": snap.trading_date.isoformat() if snap.trading_date else None,
                },
            )
            for snap in snapshots
        ]
        if not rows:
            return 0
        self.add_many(rows)
        return len(rows)

    # ----------------- 读 ----------------- #

    def get_latest(
        self,
        code: str,
        *,
        asset_kind: str = "index",
    ) -> MarketSnapshot | None:
        stmt = (
            select(MarketSnapshot)
            .where(and_(MarketSnapshot.code == code, MarketSnapshot.asset_kind == asset_kind))
            .order_by(MarketSnapshot.ts.desc())  # type: ignore[attr-defined]
            .limit(1)
        )
        return self.session.exec(stmt).first()

    def latest_for_codes(
        self,
        codes: list[str],
        *,
        asset_kind: str = "index",
    ) -> dict[str, MarketSnapshot]:
        """每个 code 取最新一条，返回 dict[code -> snapshot]。"""
        result: dict[str, MarketSnapshot] = {}
        for code in codes:
            snap = self.get_latest(code, asset_kind=asset_kind)
            if snap is not None:
                result[code] = snap
        return result

    def query_window(
        self,
        *,
        since: datetime,
        until: datetime | None = None,
        asset_kind: str | None = None,
    ) -> list[MarketSnapshot]:
        """时间窗口范围内的所有快照。"""
        stmt = select(MarketSnapshot).where(MarketSnapshot.ts >= since)
        if until is not None:
            stmt = stmt.where(MarketSnapshot.ts < until)
        if asset_kind is not None:
            stmt = stmt.where(MarketSnapshot.asset_kind == asset_kind)
        stmt = stmt.order_by(MarketSnapshot.ts.asc())  # type: ignore[attr-defined]
        return list(self.session.exec(stmt))

    def count_recent(
        self,
        *,
        window: timedelta = timedelta(hours=1),
        asset_kind: str | None = None,
    ) -> int:
        from datetime import UTC

        from sqlalchemy import func

        since = datetime.now(UTC) - window
        stmt = select(func.count()).select_from(MarketSnapshot).where(MarketSnapshot.ts >= since)
        if asset_kind is not None:
            stmt = stmt.where(MarketSnapshot.asset_kind == asset_kind)
        return int(self.session.exec(stmt).one())


__all__ = ["MarketSnapshotRepo"]
