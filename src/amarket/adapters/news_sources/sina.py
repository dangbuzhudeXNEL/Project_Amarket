"""SinaSource — 新浪财经 7x24 直播流（M1 备用源）。

Endpoint: https://zhibo.sina.com.cn/api/zhibo/feed?page=1&page_size=N&zhibo_id=152
zhibo_id=152 是财经直播频道。
返回 JSON: {result: {data: {feed: {list: [{id, rich_text, create_time, docurl, ...}]}}}}
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from amarket.adapters.news_sources.base import NewsSource
from amarket.core.exceptions import SourceError
from amarket.core.logging import get_logger
from amarket.domain.enums import SourcePriority
from amarket.domain.schemas import RawNewsItem

log = get_logger(__name__)

_BEIJING = ZoneInfo("Asia/Shanghai")
_DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


class SinaSource(NewsSource):
    """新浪财经 7x24 直播。"""

    code: str = "sina"
    name: str = "新浪财经 7x24"
    priority: SourcePriority = SourcePriority.MEDIUM

    DEFAULT_ENDPOINT = "https://zhibo.sina.com.cn/api/zhibo/feed"
    DEFAULT_ZHIBO_ID = 152  # 财经直播频道

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        zhibo_id: int | None = None,
        page_size: int = 30,
        timeout: float = 10.0,
        user_agent: str = _DEFAULT_UA,
    ) -> None:
        self._endpoint = endpoint or self.DEFAULT_ENDPOINT
        self._zhibo_id = zhibo_id if zhibo_id is not None else self.DEFAULT_ZHIBO_ID
        self._page_size = page_size
        self._timeout = timeout
        self._headers = {"User-Agent": user_agent}

    async def fetch_since(self, since: datetime) -> list[RawNewsItem]:
        items = await self._fetch_page(self._page_size)
        return [it for it in items if it.published_at >= since]

    async def fetch_realtime(self) -> list[RawNewsItem]:
        return await self.fetch_since(datetime.now(UTC) - timedelta(minutes=5))

    async def _fetch_page(self, page_size: int) -> list[RawNewsItem]:
        params = {
            "page": "1",
            "page_size": str(page_size),
            "zhibo_id": str(self._zhibo_id),
            "type": "0",
        }
        try:
            async with httpx.AsyncClient(headers=self._headers, timeout=self._timeout) as client:
                resp = await client.get(self._endpoint, params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            raise SourceError(f"sina fetch failed: {exc}") from exc
        except ValueError as exc:
            raise SourceError(f"sina returned non-JSON: {exc}") from exc

        # 新浪 nested: {result:{status:{code:0}, data:{feed:{list:[...]}}}}
        result = data.get("result") if isinstance(data, dict) else None
        if not isinstance(result, dict):
            raise SourceError("sina: missing 'result'")
        feed = (result.get("data") or {}).get("feed") if isinstance(result, dict) else None
        if not isinstance(feed, dict):
            raise SourceError("sina: missing 'result.data.feed'")
        items_list = feed.get("list", [])
        if not isinstance(items_list, list):
            return []

        out: list[RawNewsItem] = []
        for raw in items_list:
            if not isinstance(raw, dict):
                continue
            try:
                item = self._parse(raw)
            except Exception as exc:
                log.warning("sina.parse_failed", error=str(exc)[:120])
                continue
            out.append(item)
        return out

    def _parse(self, raw: dict[str, Any]) -> RawNewsItem:
        msg_id = str(raw.get("id") or raw.get("uuid") or "")
        if not msg_id:
            raise ValueError("missing id")
        title = str(raw.get("rich_text") or raw.get("title") or "").strip()
        if not title:
            raise ValueError("empty title")
        # 新浪 create_time 是 unix timestamp（int 或 str）
        ts_raw = raw.get("create_time") or 0
        try:
            ts = int(ts_raw)
        except (TypeError, ValueError):
            ts = 0
        if ts > 0:
            published_at = datetime.fromtimestamp(ts, tz=_BEIJING).astimezone(UTC)
        else:
            published_at = datetime.now(UTC)
        return RawNewsItem(
            source_code=self.code,
            source_msg_id=msg_id,
            title=title[:512],
            summary=None,
            content=None,
            url=(raw.get("docurl") or None),
            published_at=published_at,
            raw_payload=raw,
        )


__all__ = ["SinaSource"]
