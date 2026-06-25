"""`/api/dashboard/*` endpoints — 看板聚合数据。

M1 阶段：
- GET /api/dashboard/market-status   顶部市场状态栏（从 market_snapshots 读最新）
- GET /api/dashboard/news-sources    数据源状态（含 last_pulled / consecutive_failures）

M3+ 起：summary / sectors / alerts / movers ...
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from amarket.adapters.market_sources.base import MAJOR_A_SHARE_INDEXES
from amarket.api.alerts import _to_dto as _alert_to_dto
from amarket.api.dependencies import db_session
from amarket.api.news import _highest_alert_for, _latest_analysis_for, _to_card
from amarket.domain.enums import AlertLevel, ReportKind
from amarket.domain.models import MarketSnapshot, NewsAnalysis, NewsItem, NewsSource
from amarket.domain.schemas import (
    AlertDTO,
    DashboardSummary,
    IndexSnapshot,
    MarketStatusBar,
    MoverDTO,
    MoversListResponse,
    NewsCardDTO,
    NewsSourceDTO,
    ReportDetailDTO,
    SectorListResponse,
)
from amarket.repositories.alert_repo import AlertRepo
from amarket.repositories.market_snapshot_repo import MarketSnapshotRepo
from amarket.repositories.news_analysis_repo import NewsAnalysisRepo
from amarket.repositories.news_repo import NewsRepo
from amarket.repositories.news_source_repo import NewsSourceRepo
from amarket.repositories.report_repo import ReportRepo
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


@router.get("/movers", response_model=MoversListResponse)
async def dashboard_movers(
    n: int = Query(default=10, ge=1, le=50),
    session: Session = Depends(db_session),
) -> MoversListResponse:
    """个股异动榜（M3b — 简化版）：从 MarketSnapshot 按 change_pct 取 top n。

    Phase 1 备注：依赖 asset_kind='stock' 的快照入库。当前调度只入 index，
    所以默认返回空列表 — 前端友好处理。M4 调度补 stock 快照后自动有值。
    """
    # 每个 code 取最新一条 stock 快照
    stmt = (
        select(MarketSnapshot)
        .where(MarketSnapshot.asset_kind == "stock")
        .order_by(MarketSnapshot.ts.desc())  # type: ignore[attr-defined]
    )
    seen: dict[str, MarketSnapshot] = {}
    for row in session.exec(stmt):
        if row.code not in seen:
            seen[row.code] = row

    snapshots = [s for s in seen.values() if s.change_pct is not None]
    gainers = sorted(snapshots, key=lambda s: s.change_pct or 0.0, reverse=True)[:n]
    losers = sorted(snapshots, key=lambda s: s.change_pct or 0.0)[:n]

    def to_dto(s: MarketSnapshot) -> MoverDTO:
        return MoverDTO(
            code=s.code,
            name=s.name,
            change_pct=s.change_pct,
            price=s.price,
            volume=s.volume,
            turnover=s.turnover,
        )

    return MoversListResponse(
        as_of=datetime.now(UTC),
        top_gainers=[to_dto(s) for s in gainers if (s.change_pct or 0.0) >= 0],
        top_losers=[to_dto(s) for s in losers if (s.change_pct or 0.0) < 0],
    )


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    news_limit: int = Query(default=30, ge=1, le=100),
    session: Session = Depends(db_session),
) -> DashboardSummary:
    """首页一次性聚合（M3b — POC index.html 用）。"""
    # 1. 行情 — 复用 market-status 逻辑（build IndexSnapshot instances → MarketStatusBar）
    market_repo = MarketSnapshotRepo(session)
    latest_idx = market_repo.latest_for_codes(list(MAJOR_A_SHARE_INDEXES.keys()))
    index_snapshots: list[IndexSnapshot] = []
    for code, name in MAJOR_A_SHARE_INDEXES.items():
        snap = latest_idx.get(code)
        if snap is None:
            continue
        extra = snap.extra_json if isinstance(snap.extra_json, dict) else {}
        index_snapshots.append(
            IndexSnapshot(
                code=code,
                name=snap.name or name,
                price=snap.price or 0.0,
                change_pct=snap.change_pct,
                change_abs=snap.change_abs,
                prev_close=extra.get("prev_close"),
                volume=snap.volume,
                turnover=snap.turnover,
                trading_date=None,
                source=str(extra.get("source", "akshare")),
                fetched_at=snap.ts,
            )
        )
    market_status_bar = MarketStatusBar(
        indexes=index_snapshots,
        fx=[],
        commodities=[],
        refreshed_at=datetime.now(UTC),
    )

    # 2. 最新新闻
    news_repo = NewsRepo(session)
    analysis_repo = NewsAnalysisRepo(session)
    alert_repo = AlertRepo(session)
    news_rows = news_repo.list_recent(limit=news_limit)
    latest_news: list[NewsCardDTO] = []
    for it, src in news_rows:
        assert it.id is not None
        ana = _latest_analysis_for(analysis_repo, it.id)
        alt = _highest_alert_for(alert_repo, it.id)
        latest_news.append(_to_card(it, src, analysis=ana, alert=alt))

    # 3. P0 / P1 alerts (with news_title/source/category joined for FE convenience)
    p0_alerts: list[AlertDTO] = []
    p1_alerts: list[AlertDTO] = []
    for level, bucket in ((AlertLevel.P0, p0_alerts), (AlertLevel.P1, p1_alerts)):
        alerts = alert_repo.list_recent(levels=[level], limit=10)
        for a in alerts:
            title = source_name = category = None
            if a.news_id is not None:
                news = session.get(NewsItem, a.news_id)
                if news is not None:
                    title = news.title
                    s = session.get(NewsSource, news.source_id)
                    if s is not None:
                        source_name = s.name
                if a.analysis_id is not None:
                    ana_row = session.get(NewsAnalysis, a.analysis_id)
                    if ana_row is not None:
                        category = ana_row.primary_category.value
            bucket.append(
                _alert_to_dto(
                    a,
                    news_title=title,
                    news_source=source_name,
                    primary_category=category,
                )
            )

    # 4. Top sectors（按 news_heat 排序的全 14 板块；前端按需截取前 N）
    svc = SectorTrendService(session)
    top_sectors = svc.top_n(by="news_heat", n=14, window=timedelta(days=1))

    # 5. Top movers — 复用 movers 端点逻辑
    movers_resp = await dashboard_movers(n=5, session=session)
    top_movers = movers_resp.top_gainers + movers_resp.top_losers

    # 6. Today reports
    report_repo = ReportRepo(session)
    today = datetime.now(UTC).date()
    today_rows = report_repo.list_today(today=today)
    today_reports: dict[str, ReportDetailDTO | None] = {}
    for kind in ReportKind:
        r = today_rows.get(kind.value)
        if r is None:
            today_reports[kind.value] = None
        else:
            assert r.id is not None
            today_reports[kind.value] = ReportDetailDTO(
                report_id=r.id,
                date=r.date,
                kind=r.kind.value,
                status=r.status,
                markdown=r.markdown,
                content_json=r.content_json if isinstance(r.content_json, dict) else {},
                generated_by=r.generated_by,
                generated_at=r.generated_at,
                push_count=r.push_count,
            )

    return DashboardSummary(
        as_of=datetime.now(UTC),
        market_status=market_status_bar,
        today_conclusion=None,
        latest_news=latest_news,
        p0_alerts=p0_alerts,
        p1_alerts=p1_alerts,
        top_sectors=top_sectors,
        top_movers=top_movers,
        today_reports=today_reports,
    )


__all__ = ["router"]
