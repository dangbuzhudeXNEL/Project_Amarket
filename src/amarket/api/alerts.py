"""`/api/alerts/*` endpoints — P0-P3 告警列表（M2-h）。"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from amarket.api.dependencies import db_session
from amarket.domain.enums import AlertLevel
from amarket.domain.models import Alert, NewsAnalysis, NewsItem, NewsSource
from amarket.domain.schemas import AlertDTO, AlertListResponse
from amarket.repositories.alert_repo import AlertRepo

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _to_dto(
    alert: Alert,
    *,
    news_title: str | None = None,
    news_source: str | None = None,
    primary_category: str | None = None,
) -> AlertDTO:
    assert alert.id is not None
    return AlertDTO(
        alert_id=alert.id,
        news_id=alert.news_id,
        level=alert.level.value,
        trigger_reason=alert.trigger_reason,
        analysis_id=alert.analysis_id,
        status=alert.status,
        created_at=alert.created_at,
        pushed_at=alert.pushed_at,
        news_title=news_title,
        news_source=news_source,
        primary_category=primary_category,
    )


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    level: str | None = Query(default=None, description="过滤 level：P0/P1/P2"),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="过滤状态：pending/pushed/dismissed",
    ),
    since: datetime | None = Query(default=None, description="ISO 8601 时间下限"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(db_session),
) -> AlertListResponse:
    """告警列表，按 created_at 倒序。"""
    repo = AlertRepo(session)

    levels: list[AlertLevel] | None = None
    if level:
        try:
            levels = [AlertLevel(level)]
        except ValueError:
            levels = None  # 无效 level 视为不过滤

    alerts = repo.list_recent(
        since=since, levels=levels, status=status_filter, limit=limit + offset
    )
    # 简单 offset（M2 阶段 OK；M3 后可改 SQL OFFSET）
    page = alerts[offset : offset + limit]

    # 联表拿 news_title / source / primary_category
    items: list[AlertDTO] = []
    for a in page:
        title = source_name = category = None
        if a.news_id is not None:
            news = session.get(NewsItem, a.news_id)
            if news is not None:
                title = news.title
                src = session.get(NewsSource, news.source_id)
                if src is not None:
                    source_name = src.name
        if a.analysis_id is not None:
            ana = session.get(NewsAnalysis, a.analysis_id)
            if ana is not None:
                category = ana.primary_category.value
        items.append(
            _to_dto(
                a,
                news_title=title,
                news_source=source_name,
                primary_category=category,
            )
        )

    # total 用同 filter 查个完整 count
    cnt_stmt = select(Alert)
    if since:
        cnt_stmt = cnt_stmt.where(Alert.created_at >= since)
    if levels:
        cnt_stmt = cnt_stmt.where(Alert.level.in_(levels))  # type: ignore[attr-defined]
    if status_filter:
        cnt_stmt = cnt_stmt.where(Alert.status == status_filter)
    total = len(list(session.exec(cnt_stmt)))

    return AlertListResponse(items=items, total=total, offset=offset, limit=limit)


__all__ = ["router"]
