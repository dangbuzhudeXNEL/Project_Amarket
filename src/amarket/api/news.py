"""`/api/news/*` endpoints — 新闻列表 / 详情。

M1 阶段：
- GET /api/news      列表 + filter (source / since / limit / offset)
- GET /api/news/{news_id}  详情
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from amarket.api.dependencies import db_session
from amarket.domain.schemas import NewsCardDTO, NewsListResponse
from amarket.repositories.news_repo import NewsRepo
from amarket.repositories.news_source_repo import NewsSourceRepo

router = APIRouter(prefix="/api/news", tags=["news"])


def _to_card(item: object, source: object) -> NewsCardDTO:
    """NewsItem + NewsSource → NewsCardDTO。"""
    return NewsCardDTO(
        news_id=item.id,  # type: ignore[attr-defined]
        title=item.title,  # type: ignore[attr-defined]
        summary=item.summary,  # type: ignore[attr-defined]
        source=source.name,  # type: ignore[attr-defined]
        source_priority=str(source.priority),  # type: ignore[attr-defined]
        url=item.url,  # type: ignore[attr-defined]
        published_at=item.published_at,  # type: ignore[attr-defined]
        fetched_at=item.fetched_at,  # type: ignore[attr-defined]
    )


@router.get("", response_model=NewsListResponse)
async def list_news(
    source: str | None = Query(default=None, description="按 NewsSource.code 过滤"),
    since: datetime | None = Query(default=None, description="ISO 8601 时间下限"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(db_session),
) -> NewsListResponse:
    """新闻列表。"""
    repo = NewsRepo(session)
    rows = repo.list_recent(limit=limit, offset=offset, source_code=source, since=since)
    total = repo.count_filtered(source_code=source, since=since)
    items = [_to_card(news, src) for news, src in rows]
    return NewsListResponse(items=items, total=total, offset=offset, limit=limit)


@router.get("/{news_id}", response_model=NewsCardDTO)
async def get_news(
    news_id: int,
    session: Session = Depends(db_session),
) -> NewsCardDTO:
    """单条新闻详情。"""
    news_repo = NewsRepo(session)
    src_repo = NewsSourceRepo(session)
    item = news_repo.get(news_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="news not found")
    src = src_repo.get(item.source_id)
    if src is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="source not found")
    return _to_card(item, src)


__all__ = ["router"]
