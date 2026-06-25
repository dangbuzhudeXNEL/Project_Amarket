"""`/api/news/*` endpoints — 新闻列表 / 详情（M1 基础 + M2-h 分析字段 + M3b detail 扩展）。

M2-h 升级：
- list_news 现在为每条 news 查最新 NewsAnalysis（任一 processed_by）+ 最新 Alert
- 字段 primary_category / tags / sentiment / importance / urgency / alert_level 已填充

M3b post-merge polish：
- `GET /api/news/{id}` 升级为返回 NewsDetailDTO（含全部 AI 分析字段 + related_news）
- 列表端点不变，仍用 NewsCardDTO 保持轻量
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from amarket.api.dependencies import db_session
from amarket.domain.models import Alert, NewsAnalysis, NewsItem, NewsSource
from amarket.domain.schemas import (
    NewsCardDTO,
    NewsDetailDTO,
    NewsListResponse,
    RelatedNewsDTO,
)
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
    """NewsItem + NewsSource (+ NewsAnalysis + Alert) → NewsCardDTO（列表用）。"""
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


def _to_detail(
    item: NewsItem,
    source: NewsSource,
    *,
    analysis: NewsAnalysis | None = None,
    alert: Alert | None = None,
    related_news: list[RelatedNewsDTO] | None = None,
) -> NewsDetailDTO:
    """NewsItem + 完整 AI 分析 + related_news → NewsDetailDTO（详情用）。

    与 _to_card 的区别：填充 content / confidence / impact_horizon / action_hint /
    related_sectors / related_symbols / ai_reasoning / risk_notes / processed_by /
    pushed / related_news 等"详情独有"字段。
    """
    assert item.id is not None
    return NewsDetailDTO(
        news_id=item.id,
        title=item.title,
        summary=item.summary,
        content=item.content,
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
        confidence=analysis.confidence_score if analysis else None,
        impact_horizon=analysis.impact_horizon.value if analysis else None,
        action_hint=analysis.action_hint.value if analysis else None,
        related_sectors=analysis.related_sectors if analysis else [],
        related_symbols=analysis.related_symbols if analysis else [],
        ai_reasoning=analysis.ai_reasoning if analysis else None,
        risk_notes=analysis.risk_notes if analysis else None,
        processed_by=analysis.processed_by if analysis else None,
        alert_level=alert.level.value if alert else None,
        pushed=(alert.status == "pushed") if alert else False,
        related_news=related_news or [],
    )


def _latest_analysis_for(repo: NewsAnalysisRepo, news_id: int) -> NewsAnalysis | None:
    """优先取 agent:* / sdk:* 分析（更深度），无则 rule，最新优先。"""
    rows = repo.list_for_news(news_id=news_id)
    if not rows:
        return None
    # 排序：agent/sdk 优先（0），rule 次之（1）；同优先级取 id 最大
    return sorted(
        rows,
        key=lambda a: (
            0 if a.processed_by.startswith(("agent:", "sdk:")) else 1,
            -(a.id or 0),
        ),
    )[0]


def _highest_alert_for(repo: AlertRepo, news_id: int) -> Alert | None:
    """优先返回 P0 > P1 > P2 的 alert（一个 news 可能多 alert）。

    修 review P0-1：用 repo.list_for_news(news_id) 直接查目标 news，避免
    全局 list_recent(limit=50) 在 alerts 表增长后静默丢失老 news 告警。
    """
    rows = repo.list_for_news(news_id=news_id, limit=10)
    if not rows:
        return None
    level_priority = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    rows.sort(key=lambda a: level_priority.get(a.level.value, 99))
    return rows[0]


def _related_news_for(session: Session, news: NewsItem, *, limit: int = 10) -> list[RelatedNewsDTO]:
    """同 event_id 下的其他新闻 — 详情页"相关新闻（同事件）"区。"""
    if news.event_id is None:
        return []
    stmt = (
        select(NewsItem, NewsSource)
        .join(NewsSource, NewsItem.source_id == NewsSource.id)  # type: ignore[arg-type]
        .where(NewsItem.event_id == news.event_id)
        .where(NewsItem.id != news.id)
        .order_by(NewsItem.published_at.desc())  # type: ignore[attr-defined]
        .limit(limit)
    )
    result: list[RelatedNewsDTO] = []
    for r_news, r_src in session.exec(stmt):
        assert r_news.id is not None
        result.append(
            RelatedNewsDTO(
                news_id=r_news.id,
                title=r_news.title,
                source=r_src.name,
                published_at=r_news.published_at,
                url=r_news.url,
            )
        )
    return result


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


@router.get("/{news_id}", response_model=NewsDetailDTO)
async def get_news(
    news_id: int,
    session: Session = Depends(db_session),
) -> NewsDetailDTO:
    """单条新闻完整详情（含全部 AI 分析字段 + 相关新闻）。

    M3b post-merge polish：返回 NewsDetailDTO（不是 NewsCardDTO），让前端
    news-detail.html 能渲染完整的 AI 分析（推理 / 风险提示 / 影响板块 / 关联标的 /
    相关新闻等）。
    """
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
    related = _related_news_for(session, item, limit=10)
    return _to_detail(item, src, analysis=ana, alert=alt, related_news=related)


__all__ = ["router"]
