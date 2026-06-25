"""`/api/dashboard/*` endpoints — 看板聚合数据。

M1 阶段：
- GET /api/dashboard/market-status   顶部市场状态栏（从 market_snapshots 读最新）
- GET /api/dashboard/news-sources    数据源状态（含 last_pulled / consecutive_failures）

M3+ 起：summary / sectors / alerts / movers ...
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlmodel import Session

from amarket.adapters.market_sources.base import MAJOR_A_SHARE_INDEXES
from amarket.api.dependencies import db_session
from amarket.domain.schemas import (
    IndexSnapshot,
    MarketStatusBar,
    NewsSourceDTO,
    SectorListResponse,
)
from amarket.repositories.market_snapshot_repo import MarketSnapshotRepo
from amarket.repositories.news_source_repo import NewsSourceRepo
from amarket.services.dashboard.sector_trend import SectorTrendService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/market-status", response_model=MarketStatusBar)
async def market_status(
    session: Session = Depends(db_session),
) -> MarketStatusBar:
    """顶部市场状态栏 — 从 market_snapshots 读最新（不实时调 akshare）。

    刷新数据：`uv run amarket collect market`（M4+ 起自动调度）。
    """
    repo = MarketSnapshotRepo(session)
    latest = repo.latest_for_codes(list(MAJOR_A_SHARE_INDEXES.keys()))

    indexes: list[IndexSnapshot] = []
    for code, name in MAJOR_A_SHARE_INDEXES.items():
        snap = latest.get(code)
        if snap is None:
            continue
        extra = snap.extra_json if isinstance(snap.extra_json, dict) else {}
        indexes.append(
            IndexSnapshot(
                code=code,
                name=snap.name or name,
                price=snap.price or 0.0,
                change_pct=snap.change_pct,
                change_abs=snap.change_abs,
                prev_close=extra.get("prev_close"),
                volume=snap.volume,
                turnover=snap.turnover,
                trading_date=None,  # 表里已序列化为 ISO 字符串，M1 暂不回传
                source=str(extra.get("source", "akshare")),
                fetched_at=snap.ts,
            )
        )
    return MarketStatusBar(indexes=indexes, refreshed_at=datetime.now(UTC))


@router.get("/news-sources", response_model=list[NewsSourceDTO])
async def news_sources(
    session: Session = Depends(db_session),
) -> list[NewsSourceDTO]:
    """数据源运维状态（M3 看板"数据源健康"区域用）。"""
    repo = NewsSourceRepo(session)
    rows = repo.list_all(limit=100)
    return [
        NewsSourceDTO(
            code=src.code,
            name=src.name,
            priority=str(src.priority),
            enabled=src.enabled,
            last_pulled_at=src.last_pulled_at,
            last_error=src.last_error,
            consecutive_failures=src.consecutive_failures,
        )
        for src in rows
    ]


_WINDOW_MAP: dict[str, timedelta] = {
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "1d": timedelta(days=1),
}


@router.get("/sectors", response_model=SectorListResponse)
async def dashboard_sectors(
    window: str = "1d",
    session: Session = Depends(db_session),
) -> SectorListResponse:
    """板块趋势看板（M3b — Phase 1 简化版）。

    - window：'1h' | '4h' | '1d'（默认 1d；无效值 fallback 到 1d）
    - 数据：news_count_24h 实时反查；change_pct 来自 SectorTrend 表（无则 None）
    """
    td = _WINDOW_MAP.get(window) or timedelta(days=1)
    effective_window = window if window in _WINDOW_MAP else "1d"
    svc = SectorTrendService(session)
    sectors = svc.list_sectors(window=td)
    return SectorListResponse(
        as_of=datetime.now(UTC),
        window=effective_window,
        sectors=sectors,
    )


__all__ = ["router"]
