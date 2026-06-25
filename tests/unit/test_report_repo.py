"""ReportRepo 单测（M3b）。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlmodel import Session

from amarket.domain.enums import ReportKind
from amarket.domain.models import Report
from amarket.repositories.report_repo import ReportRepo


@pytest.fixture
def seed_reports(session: Session) -> list[int]:
    """seed 3 reports：今日 premarket + 今日 morning + 昨日 close。"""
    today = datetime.now(UTC).date()
    yesterday = (datetime.now(UTC) - timedelta(days=1)).date()

    rows = [
        Report(
            date=today,
            kind=ReportKind.PREMARKET,
            status="completed",
            markdown="## 盘前\n- A",
            generated_by="agent:daily-report-writer",
            generated_at=datetime.now(UTC),
        ),
        Report(
            date=today,
            kind=ReportKind.MORNING,
            status="completed",
            markdown="## 早盘",
            generated_by="agent:daily-report-writer",
            generated_at=datetime.now(UTC),
        ),
        Report(
            date=yesterday,
            kind=ReportKind.CLOSE,
            status="completed",
            markdown="## 收盘",
            generated_by="agent:daily-report-writer",
            generated_at=datetime.now(UTC),
        ),
    ]
    session.add_all(rows)
    session.commit()
    for r in rows:
        session.refresh(r)
    ids = [r.id for r in rows]
    assert all(i is not None for i in ids)
    return [i for i in ids if i is not None]


def test_list_recent_returns_descending(session: Session, seed_reports: list[int]) -> None:
    repo = ReportRepo(session)
    rows = repo.list_recent(limit=10)
    assert len(rows) == 3
    # date desc, kind desc 在同 date 内由 generated_at 决定
    assert rows[0].date >= rows[-1].date


def test_list_recent_filter_by_kind(session: Session, seed_reports: list[int]) -> None:
    repo = ReportRepo(session)
    rows = repo.list_recent(kind=ReportKind.PREMARKET, limit=10)
    assert len(rows) == 1
    assert rows[0].kind == ReportKind.PREMARKET


def test_list_recent_filter_by_date_range(session: Session, seed_reports: list[int]) -> None:
    repo = ReportRepo(session)
    today = datetime.now(UTC).date()
    rows = repo.list_recent(date_from=today, date_to=today, limit=10)
    assert len(rows) == 2
    assert all(r.date == today for r in rows)


def test_today_by_kind_hits(session: Session, seed_reports: list[int]) -> None:
    repo = ReportRepo(session)
    today = datetime.now(UTC).date()
    row = repo.today_by_kind(kind=ReportKind.PREMARKET, today=today)
    assert row is not None
    assert row.kind == ReportKind.PREMARKET


def test_today_by_kind_miss_returns_none(session: Session, seed_reports: list[int]) -> None:
    repo = ReportRepo(session)
    today = datetime.now(UTC).date()
    row = repo.today_by_kind(kind=ReportKind.EVENING, today=today)
    assert row is None


def test_list_today_returns_dict_by_kind(session: Session, seed_reports: list[int]) -> None:
    repo = ReportRepo(session)
    today = datetime.now(UTC).date()
    by_kind = repo.list_today(today=today)
    assert isinstance(by_kind, dict)
    # 至少应该包含 premarket 与 morning
    assert by_kind.get(ReportKind.PREMARKET.value) is not None
    assert by_kind.get(ReportKind.MORNING.value) is not None
    # 缺失的 kind 不存在或为 None
    assert by_kind.get(ReportKind.EVENING.value) is None
