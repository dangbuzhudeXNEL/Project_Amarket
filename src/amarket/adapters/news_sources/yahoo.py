"""YahooFinanceRssSource — 雅虎财经 RSS（M1 海外市场备用）。

Endpoint: https://feeds.finance.yahoo.com/rss/2.0/headline?s=<TICKER>&region=US&lang=en-US
默认拉 ^GSPC（标普 500），用户可自配额外 ticker。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser
import httpx

from amarket.adapters.news_sources.base import NewsSource
from amarket.core.exceptions import SourceError
from amarket.core.logging import get_logger
from amarket.domain.enums import SourcePriority
from amarket.domain.schemas import RawNewsItem

log = get_logger(__name__)

_DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


class YahooFinanceRssSource(NewsSource):
    """雅虎财经 RSS 聚合（海外市场覆盖）。"""

    code: str = "yahoo"
    name: str = "雅虎财经 RSS"
    priority: SourcePriority = SourcePriority.MEDIUM

    DEFAULT_TICKERS: tuple[str, ...] = ("^GSPC",)  # 标普 500
    BASE_URL = "https://feeds.finance.yahoo.com/rss/2.0/headline"

    def __init__(
        self,
        *,
        tickers: list[str] | tuple[str, ...] | None = None,
        timeout: float = 10.0,
        user_agent: str = _DEFAULT_UA,
    ) -> None:
        self._tickers = list(tickers or self.DEFAULT_TICKERS)
        self._timeout = timeout
        self._headers = {"User-Agent": user_agent}

    async def fetch_since(self, since: datetime) -> list[RawNewsItem]:
        items = await self._fetch_all_tickers()
        return [it for it in items if it.published_at >= since]

    async def fetch_realtime(self) -> list[RawNewsItem]:
        return await self.fetch_since(datetime.now(UTC) - timedelta(minutes=15))

    async def _fetch_all_tickers(self) -> list[RawNewsItem]:
        all_items: list[RawNewsItem] = []
        for ticker in self._tickers:
            try:
                items = await self._fetch_ticker(ticker)
            except SourceError as exc:
                log.warning("yahoo.ticker_failed", ticker=ticker, error=str(exc)[:120])
                continue
            all_items.extend(items)
        return all_items

    async def _fetch_ticker(self, ticker: str) -> list[RawNewsItem]:
        params = {"s": ticker, "region": "US", "lang": "en-US"}
        try:
            async with httpx.AsyncClient(headers=self._headers, timeout=self._timeout) as client:
                resp = await client.get(self.BASE_URL, params=params)
                resp.raise_for_status()
                xml_text = resp.text
        except httpx.HTTPError as exc:
            raise SourceError(f"yahoo fetch {ticker} failed: {exc}") from exc

        return self._parse_rss(xml_text, ticker)

    def _parse_rss(self, xml: str, ticker: str) -> list[RawNewsItem]:
        feed = feedparser.parse(xml)
        if feed.bozo and feed.entries == []:
            raise SourceError(f"yahoo {ticker}: malformed RSS")

        out: list[RawNewsItem] = []
        for entry in feed.entries:
            try:
                item = self._parse_entry(entry, ticker)
            except Exception as exc:
                log.warning("yahoo.entry_parse_failed", error=str(exc)[:120])
                continue
            out.append(item)
        return out

    def _parse_entry(self, entry: Any, ticker: str) -> RawNewsItem:
        guid = str(entry.get("id") or entry.get("guid") or entry.get("link") or "")
        title = str(entry.get("title") or "").strip()
        if not guid or not title:
            raise ValueError("missing guid/title")

        published_at = _parse_rss_date(
            entry.get("published") or entry.get("updated") or entry.get("date"),
        )
        return RawNewsItem(
            source_code=self.code,
            source_msg_id=guid,
            title=title[:512],
            summary=str(entry.get("summary") or "")[:2048] or None,
            content=None,
            url=str(entry.get("link") or "") or None,
            published_at=published_at,
            raw_payload={"ticker": ticker, "guid": guid},
        )


def _parse_rss_date(s: Any) -> datetime:
    """RFC 822 / RFC 2822 时间格式（Mon, 19 Jun 2026 09:30:00 +0000）。"""
    if not s:
        return datetime.now(UTC)
    try:
        dt = parsedate_to_datetime(str(s))
    except (TypeError, ValueError):
        return datetime.now(UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


__all__ = ["YahooFinanceRssSource"]
