"""Repository 层关键路径测试。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlmodel import Session

from amarket.domain.enums import SourceHealthStatus, SourcePriority
from amarket.domain.schemas import IndexSnapshot, RawNewsItem
from amarket.repositories.market_snapshot_repo import MarketSnapshotRepo
from amarket.repositories.news_repo import NewsRepo
from amarket.repositories.news_source_repo import NewsSourceRepo
from amarket.repositories.source_health_repo import SourceHealthRepo

# --------------------------------------------------------------------------- #
# NewsSourceRepo
# --------------------------------------------------------------------------- #


def test_news_source_repo_upsert_creates_then_updates(session: Session) -> None:
    repo = NewsSourceRepo(session)
    src = repo.upsert(code="x1", name="X 1", priority=SourcePriority.MEDIUM)
    assert src.id is not None
    assert src.priority == SourcePriority.MEDIUM

    src2 = repo.upsert(code="x1", name="X 1 v2", priority=SourcePriority.HIGH)
    assert src2.id == src.id  # 同 row
    assert src2.priority == SourcePriority.HIGH


def test_news_source_repo_mark_pulled(session: Session) -> None:
    repo = NewsSourceRepo(session)
    src = repo.upsert(code="x", name="X")
    assert src.id is not None

    repo.mark_pulled(src.id, success=True)
    refreshed = repo.get(src.id)
    assert refreshed is not None
    assert refreshed.last_error is None
    assert refreshed.last_pulled_at is not None
    assert refreshed.consecutive_failures == 0

    repo.mark_pulled(src.id, success=False, error="boom")
    refreshed = repo.get(src.id)
    assert refreshed is not None
    assert refreshed.last_error == "boom"
    assert refreshed.consecutive_failures == 1


def test_news_source_repo_list_enabled(session: Session) -> None:
    repo = NewsSourceRepo(session)
    repo.upsert(code="a", name="A", enabled=True)
    repo.upsert(code="b", name="B", enabled=False)
    enabled = repo.list_enabled()
    codes = {s.code for s in enabled}
    assert "a" in codes
    assert "b" not in codes


# --------------------------------------------------------------------------- #
# NewsRepo
# --------------------------------------------------------------------------- #


def test_news_repo_save_batch_and_dedupe(session: Session) -> None:
    src_repo = NewsSourceRepo(session)
    src = src_repo.upsert(code="cls", name="CLS")
    assert src.id is not None

    repo = NewsRepo(session)
    raws = [
        RawNewsItem(
            source_code="cls",
            source_msg_id="1",
            title="t1",
            published_at=datetime.now(UTC),
        ),
        RawNewsItem(
            source_code="cls",
            source_msg_id="2",
            title="t2",
            published_at=datetime.now(UTC),
        ),
    ]
    inserted, skipped = repo.save_batch(raws, source_id=src.id)
    assert inserted == 2
    assert skipped == 0

    inserted2, skipped2 = repo.save_batch(raws, source_id=src.id)
    assert inserted2 == 0
    assert skipped2 == 2


def test_news_repo_list_recent_filter_by_source(session: Session) -> None:
    src_repo = NewsSourceRepo(session)
    src_a = src_repo.upsert(code="a", name="A")
    src_b = src_repo.upsert(code="b", name="B")
    assert src_a.id is not None
    assert src_b.id is not None

    repo = NewsRepo(session)
    repo.save_batch(
        [
            RawNewsItem(
                source_code="a", source_msg_id="1", title="A1", published_at=datetime.now(UTC)
            )
        ],
        source_id=src_a.id,
    )
    repo.save_batch(
        [
            RawNewsItem(
                source_code="b", source_msg_id="2", title="B1", published_at=datetime.now(UTC)
            )
        ],
        source_id=src_b.id,
    )

    rows_a = repo.list_recent(source_code="a")
    assert len(rows_a) == 1
    assert rows_a[0][0].title == "A1"

    rows_all = repo.list_recent()
    assert len(rows_all) == 2

    assert repo.count_filtered(source_code="b") == 1


# --------------------------------------------------------------------------- #
# MarketSnapshotRepo
# --------------------------------------------------------------------------- #


def test_market_snapshot_repo_bulk_insert_and_latest(session: Session) -> None:
    repo = MarketSnapshotRepo(session)
    snapshots = [
        IndexSnapshot(code="sh000001", name="上证指数", price=4090.0, change_pct=-0.5),
        IndexSnapshot(code="sz399001", name="深证成指", price=16000.0, change_pct=0.9),
    ]
    inserted = repo.bulk_insert_index_snapshots(snapshots)
    assert inserted == 2

    latest = repo.latest_for_codes(["sh000001", "sz399001", "missing"])
    assert "sh000001" in latest
    assert latest["sh000001"].price == 4090.0
    assert "missing" not in latest

    # 写入第二个 sh000001 快照（更新版）
    repo.bulk_insert_index_snapshots(
        [IndexSnapshot(code="sh000001", name="上证指数", price=4100.0, change_pct=0.2)]
    )
    latest2 = repo.get_latest("sh000001")
    assert latest2 is not None
    assert latest2.price == 4100.0


def test_market_snapshot_repo_empty_input(session: Session) -> None:
    repo = MarketSnapshotRepo(session)
    assert repo.bulk_insert_index_snapshots([]) == 0


# --------------------------------------------------------------------------- #
# SourceHealthRepo
# --------------------------------------------------------------------------- #


def test_source_health_repo_record(session: Session) -> None:
    src_repo = NewsSourceRepo(session)
    src = src_repo.upsert(code="x", name="X")
    assert src.id is not None

    repo = SourceHealthRepo(session)
    h = repo.record(
        source_id=src.id, status=SourceHealthStatus.OK, latency_ms=12.3, items_returned=5
    )
    assert h.id is not None
    assert h.status == SourceHealthStatus.OK

    repo.record(source_id=src.id, status=SourceHealthStatus.DOWN, error="bad")
    recent = repo.recent_for_source(src.id, window=timedelta(hours=1))
    assert len(recent) == 2
