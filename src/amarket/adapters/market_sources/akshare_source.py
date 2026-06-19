"""AkshareSource — A 股指数行情 adapter（同步阻塞库，async 包一层）。

约定：
- 用 `ak.stock_zh_index_daily(symbol=...)` 拉日线数据
- 取最后两行算 change_pct（last_close - prev_close）/ prev_close
- akshare 是同步库，用 `asyncio.to_thread` 避免阻塞 event loop
- 网络失败 → 抛 SourceError，调用方决定怎么降级
"""

from __future__ import annotations

import asyncio
from typing import Any

from amarket.adapters.market_sources.base import MAJOR_A_SHARE_INDEXES
from amarket.core.exceptions import SourceError
from amarket.core.logging import get_logger
from amarket.domain.schemas import IndexSnapshot

log = get_logger(__name__)


class AkshareSource:
    """akshare 行情源（A 股主要指数）。"""

    code: str = "akshare"

    def __init__(self, *, index_names: dict[str, str] | None = None) -> None:
        # 代码 → 中文名 映射，默认覆盖 6 个 A 股主要指数
        self._names = dict(index_names or MAJOR_A_SHARE_INDEXES)

    async def get_index_snapshot(self, codes: list[str]) -> list[IndexSnapshot]:
        """串行拉一组指数的最新快照。

        注意：akshare 在 Windows 上的 mini_racer 后端在并发调用时会 native crash，
        这里用串行（asyncio.to_thread 单调）。串行 6 个指数 ~5-15s，可接受。
        """
        if not codes:
            return []

        snapshots: list[IndexSnapshot] = []
        for code in codes:
            try:
                snap = await asyncio.to_thread(self._fetch_one_blocking, code)
            except SourceError as exc:
                log.warning("akshare.fetch_failed", code=code, error=str(exc)[:120])
                continue
            except Exception as exc:  # 兜底（mini_racer crash 这种）
                log.error(
                    "akshare.unexpected_error",
                    code=code,
                    error_type=type(exc).__name__,
                    error=str(exc)[:120],
                )
                continue
            snapshots.append(snap)
        return snapshots

    # ------------------------------------------------------------------ #
    # 内部：同步阻塞实现（必须由 asyncio.to_thread 调用）
    # ------------------------------------------------------------------ #

    def _fetch_one_blocking(self, code: str) -> IndexSnapshot:
        """同步拉一个指数的最新两日，构造 IndexSnapshot。"""
        df = self._call_akshare_daily(code)
        if df is None or len(df) < 2:
            raise SourceError(f"insufficient data for {code} (need >= 2 rows)")

        last = df.iloc[-1]
        prev = df.iloc[-2]
        last_close = float(last["close"])
        prev_close = float(prev["close"])
        change_abs = last_close - prev_close
        change_pct = (change_abs / prev_close * 100) if prev_close else None

        return IndexSnapshot(
            code=code,
            name=self._names.get(code, code),
            price=last_close,
            change_pct=round(change_pct, 4) if change_pct is not None else None,
            change_abs=round(change_abs, 4),
            prev_close=prev_close,
            volume=float(last["volume"]) if "volume" in last else None,
            turnover=None,  # daily 端点不含 turnover
            trading_date=last.get("date", None),
            source=self.code,
        )

    def _call_akshare_daily(self, code: str) -> Any:
        """单独抽出便于测试 monkeypatch。"""
        import akshare as ak

        try:
            return ak.stock_zh_index_daily(symbol=code)
        except Exception as exc:
            raise SourceError(f"akshare.stock_zh_index_daily({code}) failed: {exc}") from exc


__all__ = ["AkshareSource"]
