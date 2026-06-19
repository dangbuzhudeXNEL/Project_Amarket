"""EastmoneySource — 东方财富 7x24 新闻源（M1 主源）。

Endpoint: https://newsapi.eastmoney.com/kuaixun/v2/api/list?client=web&pagesize=N&pageindex=1
返回 JSON: {rc:1, me:"", news:[{id, newsid, title, digest, showtime, url_w, ...}]}
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


class EastmoneySource(NewsSource):
    """东方财富 7x24 快讯。"""

    code: str = "eastmoney"
    name: str = "东方财富 7x24"
    priority: SourcePriority = SourcePriority.HIGH

    DEFAULT_ENDPOINT = "https://newsapi.eastmoney.com/kuaixun/v2/api/list"

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        page_size: int = 50,
        timeout: float = 10.0,
        user_agent: str = _DEFAULT_UA,
    ) -> None:
        self._endpoint = endpoint or self.DEFAULT_ENDPOINT
        self._page_size = page_size
        self._timeout = timeout
        self._headers = {"User-Agent": user_agent}

    # ----------------- 公共接口 ----------------- #

    async def fetch_since(self, since: datetime) -> list[RawNewsItem]:
        items = await self._fetch_page(self._page_size)
        # 截掉 since 之前的
        return [it for it in items if it.published_at >= since]

    async def fetch_realtime(self) -> list[RawNewsItem]:
        """近 5 分钟（pageSize 默认 50 已足够覆盖）。"""
        return await self.fetch_since(datetime.now(UTC) - timedelta(minutes=5))

    # ----------------- 内部 ----------------- #

    async def _fetch_page(self, page_size: int) -> list[RawNewsItem]:
        params = {
            "client": "web",
            "pagesize": str(page_size),
            "pageindex": "1",
        }
        try:
            async with httpx.AsyncClient(headers=self._headers, timeout=self._timeout) as client:
                resp = await client.get(self._endpoint, params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            raise SourceError(f"eastmoney fetch failed: {exc}") from exc
        except ValueError as exc:  # JSONDecodeError
            raise SourceError(f"eastmoney returned non-JSON: {exc}") from exc

        if not isinstance(data, dict) or data.get("rc") != 1:
            raise SourceError(f"eastmoney rc != 1: {data.get('me')!r}")

        news_list = data.get("news", [])
        if not isinstance(news_list, list):
            raise SourceError("eastmoney 'news' is not a list")

        out: list[RawNewsItem] = []
        for raw in news_list:
            if not isinstance(raw, dict):
                continue
            try:
                item = self._parse(raw)
            except Exception as exc:  # 单条失败不阻断全部
                log.warning("eastmoney.parse_failed", error=str(exc)[:120])
                continue
            out.append(item)
        return out

    def _parse(self, raw: dict[str, Any]) -> RawNewsItem:
        msg_id = str(raw.get("newsid") or raw.get("id") or "")
        if not msg_id:
            raise ValueError("missing id/newsid")
        title = str(raw.get("title") or "").strip()
        if not title:
            raise ValueError("empty title")
        published_at = _parse_em_time(str(raw.get("showtime") or raw.get("ordertime") or ""))
        return RawNewsItem(
            source_code=self.code,
            source_msg_id=msg_id,
            title=title,
            summary=(raw.get("digest") or None),
            content=None,
            url=(raw.get("url_w") or raw.get("url_m") or None),
            published_at=published_at,
            raw_payload=raw,
        )


def _parse_em_time(s: str) -> datetime:
    """东财时间格式：'2026-06-19 14:30:25'（北京时间，无时区）。"""
    if not s:
        return datetime.now(UTC)
    try:
        naive = datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return datetime.now(UTC)
    return naive.replace(tzinfo=_BEIJING).astimezone(UTC)


__all__ = ["EastmoneySource"]
