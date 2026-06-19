"""AkshareSource 单元测试 — monkeypatch ak.stock_zh_index_daily。"""

from __future__ import annotations

import pandas as pd
import pytest

from amarket.adapters.market_sources.akshare_source import AkshareSource
from amarket.core.exceptions import SourceError


def _fake_df(close_today: float = 100.0, close_yest: float = 99.0) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-06-18", "2026-06-19"]).date,
            "open": [98.5, 99.5],
            "high": [99.5, 101.0],
            "low": [98.0, 99.0],
            "close": [close_yest, close_today],
            "volume": [1000.0, 1500.0],
        }
    )


@pytest.mark.asyncio
async def test_akshare_get_index_snapshot_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    source = AkshareSource()

    def fake_call(self: AkshareSource, code: str) -> pd.DataFrame:
        return _fake_df(close_today=100.0, close_yest=99.0)

    monkeypatch.setattr(AkshareSource, "_call_akshare_daily", fake_call)
    snapshots = await source.get_index_snapshot(["sh000001"])

    assert len(snapshots) == 1
    snap = snapshots[0]
    assert snap.code == "sh000001"
    assert snap.name == "上证指数"
    assert snap.price == 100.0
    assert snap.prev_close == 99.0
    assert snap.change_abs is not None
    assert round(snap.change_abs, 4) == 1.0
    assert snap.change_pct is not None
    assert round(snap.change_pct, 4) == round(1.0 / 99.0 * 100, 4)
    assert snap.volume == 1500.0


@pytest.mark.asyncio
async def test_akshare_skips_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    source = AkshareSource()
    call_count = {"n": 0}

    def fake_call(self: AkshareSource, code: str) -> pd.DataFrame:
        call_count["n"] += 1
        if code == "sh000001":
            return _fake_df()
        raise SourceError(f"boom for {code}")

    monkeypatch.setattr(AkshareSource, "_call_akshare_daily", fake_call)
    snapshots = await source.get_index_snapshot(["sh000001", "sz999999"])
    assert len(snapshots) == 1
    assert snapshots[0].code == "sh000001"
    assert call_count["n"] == 2


@pytest.mark.asyncio
async def test_akshare_insufficient_data(monkeypatch: pytest.MonkeyPatch) -> None:
    """只有一行数据应该报 SourceError（无法算 change_pct）。"""
    source = AkshareSource()

    def fake_call(self: AkshareSource, code: str) -> pd.DataFrame:
        return _fake_df().iloc[[-1]]  # 只留一行

    monkeypatch.setattr(AkshareSource, "_call_akshare_daily", fake_call)
    snapshots = await source.get_index_snapshot(["sh000001"])
    # 单条失败 → 跳过 → 返回空
    assert snapshots == []


@pytest.mark.asyncio
async def test_akshare_empty_codes() -> None:
    source = AkshareSource()
    assert await source.get_index_snapshot([]) == []


@pytest.mark.asyncio
async def test_market_data_service_default_codes(monkeypatch: pytest.MonkeyPatch) -> None:
    from amarket.services.dashboard.market_data import MarketDataService

    source = AkshareSource()

    def fake_call(self: AkshareSource, code: str) -> pd.DataFrame:
        return _fake_df()

    monkeypatch.setattr(AkshareSource, "_call_akshare_daily", fake_call)
    service = MarketDataService(source)
    snapshots = await service.get_index_snapshots()  # 默认 6 个指数
    assert len(snapshots) == 6
    bar = await service.get_market_status_bar()
    assert len(bar.indexes) == 6
