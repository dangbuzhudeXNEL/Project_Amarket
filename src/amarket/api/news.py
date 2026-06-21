"""`/api/news/*` endpoints — 新闻列表 / 详情（M1 基础 + M2-h 分析字段）。

M2-h 升级：
- list_news 现在为每条 news 查最新 NewsAnalysis（任一 processed_by）+ 最新 Alert
- 字段 primary_category / tags / sentiment / importance / urgency / alert_level 已填充
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from amarket.api.dependencies import db_session
from amarket.domain.models import Alert, NewsAnalysis, NewsItem, NewsSource
from amarket.domain.schemas import NewsCardDTO, NewsListResponse
from amarket.repositories.alert_repo import AlertRepo
from amarket.repositories.news_analysis_repo import NewsAnalysisRepo
from amarket.repositories.news_repo import NewsRepo
from amarket.repositories.news_source_repo import NewsSourceRepo

router = APIRouter(prefix="/api/news", tags=["news"])


def _to_card(
    item: NewsItem,
    source: NewsSource,
    *,
    analysis: NewsAnalysis | None = None,
    alert: Alert | None = None,
) -> NewsCardDTO:
    """NewsItem + NewsSource (+ NewsAnalysis + Alert) → NewsCardDTO。"""
    assert item.id is not None
    return NewsCardDTO(
        news_id=item.id,
        title=item.title,
        summary=item.summary,
        source=source.name,
        source_priority=str(source.priority),
        url=item.url,
        published_at=item.published_at,
        fetched_at=item.fetched_at,
        primary_category=(analysis.primary_category.value if analysis else None),
        tags=analysis.tags if analysis else [],
        sentiment=analysis.sentiment.value if analysis else None,
        importance=analysis.importance_score if analysis else None,
        urgency=analysis.urgency_score if analysis else None,
        alert_level=alert.level.value if alert else None,
    )


def _latest_analysis_for(repo: NewsAnalysisRepo, news_id: int) -> NewsAnalysis | None:
    rows = repo.list_for_news(news_id=news_id)
    return rows[0] if rows else None


def _highest_alert_for(repo: AlertRepo, news_id: int) -> Alert | None:
    """优先返回 P0 > P1 > P2 的 alert（一个 news 可能多 alert）。"""
    rows = repo.list_recent(limit=50)  # 取 recent，按 created_at desc
    # 过滤同 news_id
    news_alerts = [a for a in rows if a.news_id == news_id]
    if not news_alerts:
        return None
    # P0 > P1 > P2 > P3
    level_priority = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    news_alerts.sort(key=lambda a: level_priority.get(a.level.value, 99))
    return news_alerts[0]


@router.get("", response_model=NewsListResponse)
async def list_news(
    source: str | None = Query(default=None, description="按 NewsSource.code 过滤"),
    since: datetime | None = Query(default=None, description="ISO 8601 时间下限"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(db_session),
) -> NewsListResponse:
    """新闻列表（含分析字段 + alert 等级）。"""
    repo = NewsRepo(session)
    analysis_repo = NewsAnalysisRepo(session)
    alert_repo = AlertRepo(session)

    rows = repo.list_recent(limit=limit, offset=offset, source_code=source, since=since)
    total = repo.count_filtered(source_code=source, since=since)

    items: list[NewsCardDTO] = []
    for news, src in rows:
        assert news.id is not None
        ana = _latest_analysis_for(analysis_repo, news.id)
        alt = _highest_alert_for(alert_repo, news.id)
        items.append(_to_card(news, src, analysis=ana, alert=alt))

    return NewsListResponse(items=items, total=total, offset=offset, limit=limit)


@router.get("/{news_id}", response_model=NewsCardDTO)
async def get_news(
    news_id: int,
    session: Session = Depends(db_session),
) -> NewsCardDTO:
    """单条新闻详情（含分析字段）。"""
    news_repo = NewsRepo(session)
    src_repo = NewsSourceRepo(session)
    analysis_repo = NewsAnalysisRepo(session)
    alert_repo = AlertRepo(session)

    item = news_repo.get(news_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="news not found")
    src = src_repo.get(item.source_id)
    if src is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="source not found")

    ana = _latest_analysis_for(analysis_repo, news_id)
    alt = _highest_alert_for(alert_repo, news_id)
    return _to_card(item, src, analysis=ana, alert=alt)


__all__ = ["router"]
