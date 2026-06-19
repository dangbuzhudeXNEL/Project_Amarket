"""FastAPI 依赖注入工厂。

集中管理 DB session / source / service 的注入，便于测试 override。
"""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends
from sqlmodel import Session

from amarket.adapters.market_sources.akshare_source import AkshareSource
from amarket.adapters.market_sources.base import MarketDataSource
from amarket.db.session import get_session
from amarket.services.dashboard.market_data import MarketDataService

# --------------------------------------------------------------------------- #
# DB session
# --------------------------------------------------------------------------- #


def db_session() -> Generator[Session, None, None]:
    """每请求一个 session。"""
    yield from get_session()


# --------------------------------------------------------------------------- #
# Market data
# --------------------------------------------------------------------------- #


def _akshare_source() -> MarketDataSource:
    """默认行情源 — 进程单例 OK 因为是无状态 adapter。"""
    return AkshareSource()


def market_data_service(
    source: MarketDataSource = Depends(_akshare_source),
) -> MarketDataService:
    return MarketDataService(source)


__all__ = ["db_session", "market_data_service"]
