"""NewsDeduper — 三层去重 + 同事件聚合（Spec v3 §6.1.2, M2-b）。

去重逻辑（PRD §7.3）：
  L1 — URL 完全相同 → 同事件
  L2 — 标题 normalize 后相同 → 同事件（lookback 窗口内）
  L3 — SimHash 汉明距离 < threshold（默认 3） → 同事件（lookback 窗口内）
  否则 → 创建新事件

事件聚合到 `news_events`，回填 `news_items.event_id` + `content_hash`。
"""

from __future__ import annotations

import string
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from simhash import Simhash
from sqlmodel import Session, select

from amarket.core.logging import get_logger
from amarket.domain.models import NewsEvent, NewsItem, NewsSource
from amarket.repositories.news_event_repo import NewsEventRepo

log = get_logger(__name__)

# 中文标点（覆盖 GB 18030 常见）
_CN_PUNCT = "，。、；：？！“”‘’（）【】《》—…·「」『』〔〕"
_PUNCT_TABLE = str.maketrans("", "", string.punctuation + string.whitespace + _CN_PUNCT)


# --------------------------------------------------------------------------- #
# 纯函数
# --------------------------------------------------------------------------- #


def normalize_title(title: str) -> str:
    """标题归一化：lowercase + 去空白 + 去中英标点。

    用于 L2 完全匹配（同事件不同源、文字小修小补）。
    """
    if not title:
        return ""
    return title.lower().translate(_PUNCT_TABLE)


def compute_simhash(text: str) -> str:
    """64-bit SimHash 的 16 字符十六进制表示。"""
    return f"{Simhash(text).value:016x}"


def hamming_distance(h1_hex: str, h2_hex: str) -> int:
    """两个 64-bit hex hash 的汉明距离。"""
    return bin(int(h1_hex, 16) ^ int(h2_hex, 16)).count("1")


# --------------------------------------------------------------------------- #
# 结果 DTO
# --------------------------------------------------------------------------- #


@dataclass
class DedupeResult:
    total: int = 0
    new_events: int = 0
    merged_into_existing: int = 0
    skipped_already_event: int = 0  # 幂等：已有 event_id 的不重复处理
    events_touched: list[int] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Service
# --------------------------------------------------------------------------- #


class NewsDeduper:
    """三层去重 + 事件聚合服务。"""

    def __init__(
        self,
        session: Session,
        *,
        simhash_threshold: int = 3,
        lookback_hours: int = 24,
        recent_candidates: int = 200,
    ) -> None:
        self._session = session
        self._event_repo = NewsEventRepo(session)
        self._threshold = simhash_threshold
        self._lookback = timedelta(hours=lookback_hours)
        self._recent_limit = recent_candidates

    # ---------------- 公共入口 ---------------- #

    def dedupe_batch(self, items: Sequence[NewsItem]) -> DedupeResult:
        """对一批 NewsItem 跑去重，回填 event_id + content_hash。

        前提：items 已入 DB（有 id）。
        幂等：已有 event_id 的会被跳过。
        """
        result = DedupeResult(total=len(items))
        events_set: set[int] = set()

        for item in items:
            if item.id is None:
                log.warning("deduper.skip_unsaved_item", title=item.title[:80])
                continue

            if item.event_id is not None:
                result.skipped_already_event += 1
                events_set.add(item.event_id)
                continue

            sig = compute_simhash(item.title)
            item.content_hash = sig

            matched = (
                self._find_event_l1_url(item)
                or self._find_event_l2_title(item)
                or self._find_event_l3_simhash(sig)
            )

            if matched is not None:
                self._merge_into_event(item, matched)
                result.merged_into_existing += 1
                assert matched.id is not None
                events_set.add(matched.id)
            else:
                new_event = self._create_event(item, signature=sig)
                result.new_events += 1
                assert new_event.id is not None
                events_set.add(new_event.id)

        self._session.commit()
        result.events_touched = sorted(events_set)
        log.info(
            "deduper.batch_done",
            total=result.total,
            new_events=result.new_events,
            merged=result.merged_into_existing,
            skipped=result.skipped_already_event,
        )
        return result

    def find_event_for(self, item: NewsItem) -> NewsEvent | None:
        """对单条 item 找最匹配的 event（L1 → L2 → L3）。不修改 DB。"""
        sig = compute_simhash(item.title)
        return (
            self._find_event_l1_url(item)
            or self._find_event_l2_title(item)
            or self._find_event_l3_simhash(sig)
        )

    # ---------------- 三层匹配 ---------------- #

    def _find_event_l1_url(self, item: NewsItem) -> NewsEvent | None:
        """L1: 另有 news_items 同 URL 且已有 event。"""
        if not item.url:
            return None
        stmt = (
            select(NewsItem)
            .where(NewsItem.url == item.url)
            .where(NewsItem.id != item.id)
            .where(NewsItem.event_id.is_not(None))  # type: ignore[union-attr]
            .limit(1)
        )
        other = self._session.exec(stmt).first()
        if other is None or other.event_id is None:
            return None
        return self._session.get(NewsEvent, other.event_id)

    def _find_event_l2_title(self, item: NewsItem) -> NewsEvent | None:
        """L2: canonical_title 完全相同 + 在 lookback 窗内。"""
        norm = normalize_title(item.title)
        if not norm:
            return None
        cutoff = datetime.now(UTC) - self._lookback
        stmt = (
            select(NewsEvent)
            .where(NewsEvent.canonical_title == norm)
            .where(NewsEvent.last_seen_at >= cutoff)
            .order_by(NewsEvent.last_seen_at.desc())  # type: ignore[attr-defined]
            .limit(1)
        )
        return self._session.exec(stmt).first()

    def _find_event_l3_simhash(self, sig: str) -> NewsEvent | None:
        """L3: 最近 N 个 event 里找汉明距离 < threshold 的。"""
        cutoff = datetime.now(UTC) - self._lookback
        candidates = self._event_repo.list_recent(since=cutoff, limit=self._recent_limit)
        for ev in candidates:
            if hamming_distance(ev.signature, sig) < self._threshold:
                return ev
        return None

    # ---------------- 写入辅助 ---------------- #

    def _create_event(self, item: NewsItem, *, signature: str) -> NewsEvent:
        norm = normalize_title(item.title)
        src_code = self._get_source_code(item.source_id)
        now = datetime.now(UTC)
        ev = NewsEvent(
            signature=signature,
            canonical_title=norm or item.title[:512],
            first_seen_at=item.published_at,
            last_seen_at=now,
            news_count=1,
            top_source=src_code,
        )
        self._event_repo.add(ev)  # commit + refresh，拿到 id
        assert ev.id is not None
        item.event_id = ev.id
        self._session.add(item)
        return ev

    def _merge_into_event(self, item: NewsItem, event: NewsEvent) -> None:
        """把 item 并入 event：更新 news_count + last_seen_at + top_source。"""
        assert event.id is not None
        event.news_count += 1
        event.last_seen_at = datetime.now(UTC)

        item.event_id = event.id
        self._session.add(item)
        # flush 让 _compute_top_source 的查询能看到刚 set 的 event_id
        self._session.flush()

        event.top_source = self._compute_top_source(event)
        self._session.add(event)

    def _get_source_code(self, source_id: int) -> str | None:
        src = self._session.get(NewsSource, source_id)
        return src.code if src else None

    def _compute_top_source(self, event: NewsEvent) -> str | None:
        """统计 event 下所有 news_items 的 source.code，取最高频。"""
        stmt = select(NewsItem).where(NewsItem.event_id == event.id)
        items = list(self._session.exec(stmt))
        codes: list[str] = []
        for it in items:
            src = self._session.get(NewsSource, it.source_id)
            if src is not None:
                codes.append(src.code)
        if not codes:
            return event.top_source
        return Counter(codes).most_common(1)[0][0]


__all__ = [
    "DedupeResult",
    "NewsDeduper",
    "compute_simhash",
    "hamming_distance",
    "normalize_title",
]
