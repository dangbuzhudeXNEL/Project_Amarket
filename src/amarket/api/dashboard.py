"""`/api/dashboard/*` endpoints — 看板聚合数据。

M1 阶段：
- GET /api/dashboard/market-status   顶部市场状态栏（从 market_snapshots 读最新）
- GET /api/dashboard/news-sources    数据源状态（含 last_pulled / consecutive_failures）

M3+ 起：summary / sectors / alerts / movers ...
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlmodel import Session

from amarket.adapters.market_sources.base import MAJOR_A_SHARE_INDEXES
from amarket.api.dependencies import db_session
from amarket.domain.schemas import IndexSnapshot, MarketStatusBar, NewsSourceDTO
from amarket.repositories.market_snapshot_repo import MarketSnapshotRepo
from amarket.repositories.news_source_repo import NewsSourceRepo

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


__all__ = ["router"]
