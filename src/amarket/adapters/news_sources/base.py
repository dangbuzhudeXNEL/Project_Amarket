"""NewsSource 接口（Spec v3 §6.2.1）。

所有新闻源（同花顺 / 东方财富 / 雅虎财经 / ...）实现这个 Protocol。
统一返回标准化的 RawNewsItem，由 NewsCollector / NewsRepo 统一入库。
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from amarket.domain.enums import SourcePriority
from amarket.domain.schemas import RawNewsItem


@runtime_checkable
class NewsSource(Protocol):
    """新闻源统一接口。"""

    code: str  # 'eastmoney' / 'sina' / 'yahoo' / ...
    name: str
    priority: SourcePriority

    async def fetch_since(self, since: datetime) -> list[RawNewsItem]:
        """拉取 since 时间点之后的新闻（典型 12h 窗口，盘前用）。"""
        ...

    async def fetch_realtime(self) -> list[RawNewsItem]:
        """拉取最近一批（典型 5min 窗口，盘中实时轮询用）。

        实现可以等价于 fetch_since(now - 5min)，但允许 adapter 用更高效的端点。
        """
        ...


__all__ = ["NewsSource"]
