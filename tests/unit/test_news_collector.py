"""NewsCollector 编排逻辑测试 — 用 stub NewsSource。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from amarket.core.exceptions import SourceError
from amarket.domain.enums import SourceHealthStatus, SourcePriority
from amarket.domain.models import NewsItem, NewsSource, SourceHealth
from amarket.domain.schemas import RawNewsItem
from amarket.services.news.collector import NewsCollector


class _StubSource:
    """简易 stub —— 模拟 NewsSource Protocol。"""

    def __init__(
        self,
        *,
        code: str,
        name: str,
        priority: SourcePriority = SourcePriority.HIGH,
        items: list[RawNewsItem] | None = None,
        raise_exc: BaseException | None = None,
    ) -> None:
        self.code = code
        self.name = name
        self.priority = priority
        self._items = items or []
        self._raise_exc = raise_exc

    async def fetch_realtime(self) -> list[RawNewsItem]:
        if self._raise_exc:
            raise self._raise_exc
        return self._items

    async def fetch_since(self, since: datetime) -> list[RawNewsItem]:
        if self._raise_exc:
            raise self._raise_exc
        return [it for it in self._items if it.published_at >= since]


def _make_raw(code: str, msg_id: str, *, title: str = "x") -> RawNewsItem:
    return RawNewsItem(
        source_code=code,
        source_msg_id=msg_id,
        title=title,
        published_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_collector_happy_path(in_memory_engine: Engine) -> None:
    src = _StubSource(
        code="src1",
        name="Source 1",
        items=[_make_raw("src1", "m1"), _make_raw("src1", "m2")],
    )
    with Session(in_memory_engine) as session:
        collector = NewsCollector([src], session)
        report = await collector.collect_realtime()

    assert report.total_fetched == 2
    assert report.total_inserted == 2
    assert report.failed_sources == []
    r = report.per_source[0]
    assert r.success is True
    assert r.code == "src1"
    assert r.inserted == 2
    assert r.skipped == 0


@pytest.mark.asyncio
async def test_collector_dedupe_on_second_run(in_memory_engine: Engine) -> None:
    items = [_make_raw("src1", "dup"), _make_raw("src1", "dup")]  # 同 msg_id 两次
    src = _StubSource(code="src1", name="Source 1", items=items)
    with Session(in_memory_engine) as session:
        collector = NewsCollector([src], session)
        report = await collector.collect_realtime()
    assert report.total_inserted == 1
    assert report.per_source[0].skipped == 1


@pytest.mark.asyncio
async def test_collector_failure_does_not_break_others(in_memory_engine: Engine) -> None:
    src_ok = _StubSource(code="ok", name="OK", items=[_make_raw("ok", "x")])
    src_fail = _StubSource(code="fail", name="Fail", raise_exc=SourceError("network down"))

    with Session(in_memory_engine) as session:
        collector = NewsCollector([src_ok, src_fail], session)
        report = await collector.collect_realtime()

    assert report.total_inserted == 1
    assert report.failed_sources == ["fail"]
    fail_result = next(r for r in report.per_source if r.code == "fail")
    assert fail_result.success is False
    assert fail_result.error and "network down" in fail_result.error

    with Session(in_memory_engine) as session:
        # SourceHealth 记录 fail
        healths = list(session.exec(select(SourceHealth).where(SourceHealth.error.isnot(None))))  # type: ignore[attr-defined]
        assert any(h.status == SourceHealthStatus.DOWN for h in healths)
        # NewsSource 表 consecutive_failures > 0
        fail_src = session.exec(select(NewsSource).where(NewsSource.code == "fail")).one()
        assert fail_src.consecutive_failures >= 1


@pytest.mark.asyncio
async def test_collector_unexpected_exception_caught(in_memory_engine: Engine) -> None:
    """非 SourceError 也不应 propagate。"""
    src = _StubSource(code="boom", name="boom", raise_exc=RuntimeError("kapow"))
    with Session(in_memory_engine) as session:
        collector = NewsCollector([src], session)
        report = await collector.collect_realtime()
    assert report.failed_sources == ["boom"]


@pytest.mark.asyncio
async def test_collector_collect_since_filters(in_memory_engine: Engine) -> None:
    old = _make_raw("s", "old")
    old.published_at = datetime(2020, 1, 1, tzinfo=UTC)
    new = _make_raw("s", "new")
    src = _StubSource(code="s", name="S", items=[old, new])

    with Session(in_memory_engine) as session:
        collector = NewsCollector([src], session)
        report = await collector.collect_since(datetime.now(UTC) - timedelta(hours=1))

    # old 应该被 stub.fetch_since 过滤掉
    assert report.total_inserted == 1
    with Session(in_memory_engine) as session:
        rows = list(session.exec(select(NewsItem)))
        assert len(rows) == 1
        assert rows[0].source_msg_id == "new"


def test_build_default_sources_returns_three() -> None:
    from amarket.services.news.collector import build_default_sources

    sources = build_default_sources()
    assert len(sources) == 3
    codes = {s.code for s in sources}
    assert codes == {"eastmoney", "sina", "yahoo"}
