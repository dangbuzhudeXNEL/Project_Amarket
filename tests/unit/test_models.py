"""Domain models smoke test。"""

from __future__ import annotations

from sqlmodel import Session, select

from amarket.domain.enums import UserRole
from amarket.domain.models import User


def test_user_can_be_persisted(session: Session) -> None:
    user = User(name="alice", role=UserRole.ANALYST)
    session.add(user)
    session.commit()
    session.refresh(user)

    assert user.id is not None
    assert user.role == UserRole.ANALYST
    assert user.timezone == "Asia/Shanghai"


def test_user_role_defaults_to_admin(session: Session) -> None:
    user = User(name="bob")
    session.add(user)
    session.commit()

    fetched = session.exec(select(User).where(User.name == "bob")).one()
    assert fetched.role == UserRole.ADMIN


def test_user_role_enum_string_values() -> None:
    assert UserRole.ADMIN.value == "admin"
    assert UserRole.ANALYST.value == "analyst"
    assert UserRole.TRADER.value == "trader"
    assert UserRole.GUEST.value == "guest"


# --------------------------------------------------------------------------- #
# M3b — Dashboard / Sector / Mover / Report DTOs
# --------------------------------------------------------------------------- #


def test_m3b_dtos_instantiate_and_serialize() -> None:
    """M3b 新增 9 个 DTO 都能实例化 + .model_dump_json() 不崩。"""
    from datetime import UTC, date, datetime

    from amarket.domain.schemas import (
        DashboardSummary,
        MarketStatusBar,
        MoverDTO,
        MoversListResponse,
        ReportDetailDTO,
        ReportListResponse,
        ReportSummaryDTO,
        SectorDTO,
        SectorListResponse,
        TodayReportsResponse,
    )

    sector = SectorDTO(
        name="券商",
        change_pct=1.5,
        news_count_24h=12,
        market_cap_weight=0.07,
        top_symbols=[],
    )
    SectorListResponse(as_of=datetime.now(UTC), window="1d", sectors=[sector])

    mover = MoverDTO(code="600000", name="浦发银行", change_pct=2.1, price=10.5)
    MoversListResponse(as_of=datetime.now(UTC), top_gainers=[mover], top_losers=[])

    rsum = ReportSummaryDTO(
        report_id=1,
        date=date(2026, 6, 25),
        kind="premarket",
        status="completed",
        generated_by="agent:daily-report-writer",
        generated_at=datetime.now(UTC),
    )
    ReportListResponse(items=[rsum], total=1, offset=0, limit=50)

    detail = ReportDetailDTO(
        report_id=1,
        date=date(2026, 6, 25),
        kind="premarket",
        status="completed",
        markdown="## H",
        content_json={"x": 1},
        generated_by="agent",
        generated_at=datetime.now(UTC),
    )
    TodayReportsResponse(
        today=date(2026, 6, 25),
        reports_by_kind={"premarket": detail, "morning": None},
    )

    summary = DashboardSummary(
        as_of=datetime.now(UTC),
        market_status=MarketStatusBar(),
        today_conclusion=None,
        latest_news=[],
        p0_alerts=[],
        p1_alerts=[],
        top_sectors=[sector],
        top_movers=[mover],
        today_reports={
            "premarket": None,
            "morning": None,
            "noon": None,
            "afternoon": None,
            "close": None,
            "evening": None,
        },
    )
    # JSON 序列化不崩
    assert summary.model_dump_json()
