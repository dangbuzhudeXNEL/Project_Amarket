"""MarketDataService — 行情数据服务（Spec v3 §6.1.6）。

M1 阶段：
- 通过 AkshareSource 拉 A 股主要指数快照
- 提供 get_market_status_bar() 给 /api/dashboard/market-status
- 提供 persist_snapshots() 写入 MarketSnapshot 表

后续 milestone：
- M2+ 加多源 fallback（akshare → efinance → yfinance）
- M2+ 加缓存（最近 5 分钟内不重复拉）
"""

from __future__ import annotations

from sqlmodel import Session

from amarket.adapters.market_sources.base import MAJOR_A_SHARE_INDEXES, MarketDataSource
from amarket.core.logging import get_logger
from amarket.domain.schemas import IndexSnapshot, MarketStatusBar
from amarket.repositories.market_snapshot_repo import MarketSnapshotRepo

log = get_logger(__name__)


class MarketDataService:
    """行情数据服务 — 编排 MarketDataSource，提供业务级接口。"""

    def __init__(self, source: MarketDataSource) -> None:
        self._source = source

    async def get_index_snapshots(
        self,
        codes: list[str] | None = None,
    ) -> list[IndexSnapshot]:
        """拉一组指数快照。默认拉 6 个 A 股主要指数。"""
        target_codes = codes if codes is not None else list(MAJOR_A_SHARE_INDEXES.keys())
        snapshots = await self._source.get_index_snapshot(target_codes)
        log.info(
            "market.snapshots_fetched",
            requested=len(target_codes),
            returned=len(snapshots),
            source=getattr(self._source, "code", "unknown"),
        )
        return snapshots

    async def get_market_status_bar(self) -> MarketStatusBar:
        """看板顶部市场状态栏。"""
        indexes = await self.get_index_snapshots()
        return MarketStatusBar(indexes=indexes)

    def persist_snapshots(
        self,
        snapshots: list[IndexSnapshot],
        session: Session,
    ) -> int:
        """把 IndexSnapshot 列表落地到 market_snapshots 表。返回插入行数。"""
        repo = MarketSnapshotRepo(session)
        return repo.bulk_insert_index_snapshots(snapshots)


__all__ = ["MarketDataService"]
