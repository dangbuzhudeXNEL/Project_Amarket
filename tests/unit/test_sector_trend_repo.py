"""SectorTrendRepo 单测（M3b）。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlmodel import Session

from amarket.domain.models import SectorTrend
from amarket.repositories.sector_trend_repo import SectorTrendRepo


def test_bulk_upsert_inserts_new(session: Session) -> None:
    repo = SectorTrendRepo(session)
    now = datetime.now(UTC)
    rows = [
        SectorTrend(ts=now, sector_name="券商", change_pct=1.5, news_heat=10),
        SectorTrend(ts=now, sector_name="银行", change_pct=-0.5, news_heat=5),
    ]
    inserted = repo.bulk_upsert(rows)
    assert inserted == 2


def test_latest_for_sectors_returns_freshest(session: Session) -> None:
    repo = SectorTrendRepo(session)
    older = datetime.now(UTC) - timedelta(hours=2)
    newer = datetime.now(UTC)
    repo.bulk_upsert(
        [
            SectorTrend(ts=older, sector_name="券商", change_pct=0.5, news_heat=3),
            SectorTrend(ts=newer, sector_name="券商", change_pct=1.5, news_heat=10),
            SectorTrend(ts=newer, sector_name="银行", change_pct=-0.3, news_heat=5),
        ]
    )
    latest = repo.latest_for_sectors(["券商", "银行", "保险"])
    assert "券商" in latest
    assert latest["券商"].change_pct == 1.5  # 取新的
    assert "银行" in latest
    assert "保险" not in latest  # 没数据 → 不在 dict 中


def test_latest_for_sectors_empty_db(session: Session) -> None:
    repo = SectorTrendRepo(session)
    result = repo.latest_for_sectors(["券商"])
    assert result == {}
