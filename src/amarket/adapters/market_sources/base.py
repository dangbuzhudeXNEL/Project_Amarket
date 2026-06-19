"""MarketDataSource 接口（Spec v3 §6.2.2）。

所有行情源（akshare / efinance / yfinance / ...）实现这个 Protocol。
Service 层只 import 接口，不 import 具体实现。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from amarket.domain.schemas import IndexSnapshot


@runtime_checkable
class MarketDataSource(Protocol):
    """行情源统一接口。"""

    code: str  # 'akshare' / 'efinance' / 'yfinance'

    async def get_index_snapshot(self, codes: list[str]) -> list[IndexSnapshot]:
        """拉取一组指数的最新快照。

        Args:
            codes: 标准化代码列表，akshare 形如 ['sh000001', 'sz399001']

        Returns:
            按 codes 顺序的 IndexSnapshot 列表（找不到的源略过）
        """
        ...


# 几个常用指数代码集（适配器统一字典名 + 中文名）
MAJOR_A_SHARE_INDEXES: dict[str, str] = {
    "sh000001": "上证指数",
    "sz399001": "深证成指",
    "sz399006": "创业板指",
    "sh000300": "沪深300",
    "sh000016": "上证50",
    "sh000688": "科创50",
}


__all__ = ["MAJOR_A_SHARE_INDEXES", "MarketDataSource"]
