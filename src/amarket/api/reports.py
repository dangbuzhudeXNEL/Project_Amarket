"""`/api/reports/*` endpoints — 6 时段日报（M3b）。

M3b 阶段：只做 read 端点（list / detail / today / today/{kind}）。
写端点（POST /generate、POST /{id}/push）由 M4 ReportService 实现。
"""

from __future__ import annotations

from datetime import UTC, datetime
from datetime import date as date_t

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from amarket.api.dependencies import db_session
from amarket.domain.enums import ReportKind
from amarket.domain.models import Report
from amarket.domain.schemas import (
    ReportDetailDTO,
    ReportListResponse,
    ReportSummaryDTO,
    TodayReportsResponse,
)
from amarket.repositories.report_repo import ReportRepo

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _to_summary(r: Report) -> ReportSummaryDTO:
    assert r.id is not None
    return ReportSummaryDTO(
        report_id=r.id,
        date=r.date,
        kind=r.kind.value,
        status=r.status,
        generated_by=r.generated_by,
        generated_at=r.generated_at,
        push_count=r.push_count,
    )


def _to_detail(r: Report) -> ReportDetailDTO:
    assert r.id is not None
    return ReportDetailDTO(
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


def _parse_kind(kind: str) -> ReportKind:
    try:
        return ReportKind(kind)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"invalid kind: {kind}",
        ) from e


@router.get("", response_model=ReportListResponse)
async def list_reports(
    kind: str | None = Query(default=None),
    date_from: date_t | None = Query(default=None),
    date_to: date_t | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(db_session),
) -> ReportListResponse:
    repo = ReportRepo(session)
    kind_enum = _parse_kind(kind) if kind else None
    rows = repo.list_recent(
        kind=kind_enum, date_from=date_from, date_to=date_to, limit=limit, offset=offset
    )
    total = repo.count_filtered(kind=kind_enum, date_from=date_from, date_to=date_to)
    return ReportListResponse(
        items=[_to_summary(r) for r in rows],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/today", response_model=TodayReportsResponse)
async def today_reports(
    session: Session = Depends(db_session),
) -> TodayReportsResponse:
    """今日 6 时段（缺失 → None）。"""
    repo = ReportRepo(session)
    today = datetime.now(UTC).date()
    rows = repo.list_today(today=today)
    out: dict[str, ReportDetailDTO | None] = {}
    for k in ReportKind:
        r = rows.get(k.value)
        out[k.value] = _to_detail(r) if r is not None else None
    return TodayReportsResponse(today=today, reports_by_kind=out)


@router.get("/today/{kind}", response_model=ReportDetailDTO)
async def today_report_by_kind(
    kind: str,
    session: Session = Depends(db_session),
) -> ReportDetailDTO:
    kind_enum = _parse_kind(kind)
    repo = ReportRepo(session)
    today = datetime.now(UTC).date()
    r = repo.today_by_kind(kind=kind_enum, today=today)
    if r is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"today's {kind} report not generated yet",
        )
    return _to_detail(r)


@router.get("/{report_id}", response_model=ReportDetailDTO)
async def get_report(
    report_id: int,
    session: Session = Depends(db_session),
) -> ReportDetailDTO:
    repo = ReportRepo(session)
    r = repo.get(report_id)
    if r is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report not found")
    return _to_detail(r)


__all__ = ["router"]
