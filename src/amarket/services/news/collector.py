"""NewsCollector — 调度各 NewsSource 拉取新闻、标准化、入库（Spec v3 §6.1.1）。

M1 阶段：
- 单源失败不影响其他源（fail-isolation）
- 写入 NewsRepo（按 source_id + source_msg_id 唯一约束自动去重）
- 写入 SourceHealth（每次轮询一条记录）
- 更新 NewsSource.last_pulled_at / last_error / consecutive_failures

M2+ 起：
- 跨源 SimHash 去重（写 news_events）
- 连续 3 次失败发告警
- 节流 / 重试
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlmodel import Session

from amarket.adapters.news_sources.base import NewsSource
from amarket.core.exceptions import SourceError
from amarket.core.logging import get_logger
from amarket.domain.enums import SourceHealthStatus
from amarket.domain.schemas import RawNewsItem
from amarket.repositories.news_repo import NewsRepo
from amarket.repositories.news_source_repo import NewsSourceRepo
from amarket.repositories.source_health_repo import SourceHealthRepo

log = get_logger(__name__)


@dataclass
class SourceCollectResult:
    code: str
    success: bool
    inserted: int = 0
    skipped: int = 0
    fetched: int = 0
    latency_ms: float = 0.0
    error: str | None = None


@dataclass
class CollectReport:
    started_at: datetime
    finished_at: datetime
    per_source: list[SourceCollectResult] = field(default_factory=list)

    @property
    def total_inserted(self) -> int:
        return sum(r.inserted for r in self.per_source)

    @property
    def total_fetched(self) -> int:
        return sum(r.fetched for r in self.per_source)

    @property
    def failed_sources(self) -> list[str]:
        return [r.code for r in self.per_source if not r.success]


class NewsCollector:
    """编排多源新闻采集 + 入库 + 健康记录。"""

    def __init__(self, sources: list[NewsSource], session: Session) -> None:
        self._sources = sources
        self._session = session
        self._news_repo = NewsRepo(session)
        self._source_repo = NewsSourceRepo(session)
        self._health_repo = SourceHealthRepo(session)

    async def collect_realtime(self) -> CollectReport:
        """每个源调 fetch_realtime() 并入库。"""
        return await self._collect(realtime=True)

    async def collect_since(self, since: datetime) -> CollectReport:
        """每个源调 fetch_since(since) 并入库。"""
        return await self._collect(realtime=False, since=since)

    async def _collect(
        self,
        *,
        realtime: bool,
        since: datetime | None = None,
    ) -> CollectReport:
        started = datetime.now(UTC)
        results: list[SourceCollectResult] = []

        for source in self._sources:
            result = await self._collect_one(source, realtime=realtime, since=since)
            results.append(result)
            log.info(
                "collector.source_done",
                code=result.code,
                success=result.success,
                inserted=result.inserted,
                skipped=result.skipped,
                fetched=result.fetched,
                latency_ms=round(result.latency_ms, 2),
                error=result.error,
            )

        return CollectReport(
            started_at=started,
            finished_at=datetime.now(UTC),
            per_source=results,
        )

    async def _collect_one(
        self,
        source: NewsSource,
        *,
        realtime: bool,
        since: datetime | None,
    ) -> SourceCollectResult:
        # 1. 确保 source 已注册
        src_db = self._source_repo.upsert(
            code=source.code, name=source.name, priority=source.priority
        )
        assert src_db.id is not None  # 由 DB 自增填充

        # 2. 抓取
        started = time.perf_counter()
        items: list[RawNewsItem] = []
        try:
            if realtime:
                items = await source.fetch_realtime()
            else:
                assert since is not None
                items = await source.fetch_since(since)
        except SourceError as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            return self._record_failure(src_db.id, source.code, exc, latency_ms)
        except Exception as exc:  # 兜底：未预期异常也不让单源拖垮整体
            latency_ms = (time.perf_counter() - started) * 1000
            log.error("collector.unexpected_error", code=source.code, error=str(exc))
            return self._record_failure(src_db.id, source.code, exc, latency_ms)

        latency_ms = (time.perf_counter() - started) * 1000

        # 3. 入库
        inserted, skipped = self._news_repo.save_batch(items, source_id=src_db.id)

        # 4. 健康 + source 状态
        self._health_repo.record(
            source_id=src_db.id,
            status=SourceHealthStatus.OK,
            latency_ms=latency_ms,
            items_returned=len(items),
        )
        self._source_repo.mark_pulled(src_db.id, success=True)

        return SourceCollectResult(
            code=source.code,
            success=True,
            inserted=inserted,
            skipped=skipped,
            fetched=len(items),
            latency_ms=latency_ms,
        )

    def _record_failure(
        self,
        source_id: int,
        code: str,
        exc: BaseException,
        latency_ms: float,
    ) -> SourceCollectResult:
        err_msg = str(exc)[:200]
        self._health_repo.record(
            source_id=source_id,
            status=SourceHealthStatus.DOWN,
            latency_ms=latency_ms,
            error=err_msg,
            items_returned=0,
        )
        self._source_repo.mark_pulled(source_id, success=False, error=err_msg)
        return SourceCollectResult(
            code=code,
            success=False,
            latency_ms=latency_ms,
            error=err_msg,
        )


def build_default_sources() -> list[NewsSource]:
    """M1 默认源集（1 主 2 备）。后续 milestone 改为读 config/sources.yml。"""
    from amarket.adapters.news_sources.eastmoney import EastmoneySource
    from amarket.adapters.news_sources.sina import SinaSource
    from amarket.adapters.news_sources.yahoo import YahooFinanceRssSource

    return [
        EastmoneySource(),
        SinaSource(),
        YahooFinanceRssSource(),
    ]


__all__ = ["CollectReport", "NewsCollector", "SourceCollectResult", "build_default_sources"]
