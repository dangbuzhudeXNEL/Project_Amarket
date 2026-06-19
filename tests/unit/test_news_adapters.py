"""新闻源 adapter 单元测试 — 用 respx 替换网络。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest
import respx

from amarket.adapters.news_sources.eastmoney import EastmoneySource
from amarket.adapters.news_sources.sina import SinaSource
from amarket.adapters.news_sources.yahoo import YahooFinanceRssSource
from amarket.core.exceptions import SourceError

# --------------------- Eastmoney --------------------- #


@pytest.mark.asyncio
@respx.mock
async def test_eastmoney_parses_real_payload() -> None:
    payload = {
        "rc": 1,
        "me": "",
        "news": [
            {
                "newsid": "202606193776860363",
                "id": "202606193776860363",
                "title": "央行降准 0.25%",
                "digest": "央行宣布降准 25 个基点。",
                "showtime": "2026-06-19 14:30:25",
                "url_w": "https://finance.eastmoney.com/a/202606193776860363.html",
            },
            {
                "newsid": "202606193776860400",
                "title": "无效条目缺时间",
                "showtime": "",
                "digest": "",
            },
        ],
    }
    respx.get("https://newsapi.eastmoney.com/kuaixun/v2/api/list").mock(
        return_value=httpx.Response(200, json=payload),
    )

    source = EastmoneySource()
    items = await source.fetch_since(datetime(2020, 1, 1, tzinfo=UTC))

    assert len(items) == 2  # 两条都解析成功（即使时间为空也 fallback）
    assert items[0].title == "央行降准 0.25%"
    assert items[0].source_msg_id == "202606193776860363"
    assert items[0].source_code == "eastmoney"
    assert items[0].url and "eastmoney.com" in items[0].url


@pytest.mark.asyncio
@respx.mock
async def test_eastmoney_raises_on_rc_error() -> None:
    respx.get("https://newsapi.eastmoney.com/kuaixun/v2/api/list").mock(
        return_value=httpx.Response(200, json={"rc": 0, "me": "param error", "news": []})
    )
    source = EastmoneySource()
    with pytest.raises(SourceError, match=r"rc != 1"):
        await source.fetch_realtime()


@pytest.mark.asyncio
@respx.mock
async def test_eastmoney_raises_on_http_error() -> None:
    respx.get("https://newsapi.eastmoney.com/kuaixun/v2/api/list").mock(
        return_value=httpx.Response(500),
    )
    source = EastmoneySource()
    with pytest.raises(SourceError):
        await source.fetch_realtime()


@pytest.mark.asyncio
@respx.mock
async def test_eastmoney_filters_by_since() -> None:
    """fetch_since 应该过滤掉 since 之前的条目。"""
    payload = {
        "rc": 1,
        "me": "",
        "news": [
            {
                "newsid": "old",
                "title": "old item",
                "showtime": "2020-01-01 00:00:00",
                "digest": "",
            },
            {
                "newsid": "new",
                "title": "new item",
                "showtime": "2099-12-31 23:59:59",
                "digest": "",
            },
        ],
    }
    respx.get("https://newsapi.eastmoney.com/kuaixun/v2/api/list").mock(
        return_value=httpx.Response(200, json=payload),
    )
    source = EastmoneySource()
    items = await source.fetch_since(datetime.now(UTC) - timedelta(hours=1))
    assert len(items) == 1
    assert items[0].source_msg_id == "new"


# --------------------- Sina --------------------- #


@pytest.mark.asyncio
@respx.mock
async def test_sina_parses_nested_payload() -> None:
    payload = {
        "result": {
            "status": {"code": 0},
            "data": {
                "feed": {
                    "list": [
                        {
                            "id": "12345",
                            "rich_text": "央行公告 ...",
                            "create_time": 1750000000,
                            "docurl": "https://finance.sina.com.cn/x.html",
                        }
                    ]
                }
            },
        }
    }
    respx.get("https://zhibo.sina.com.cn/api/zhibo/feed").mock(
        return_value=httpx.Response(200, json=payload),
    )
    source = SinaSource()
    # fetch_realtime 默认过滤近 5 min，fixture 时间戳过老 → 期望 0 条
    realtime = await source.fetch_realtime()
    assert realtime == []

    # 全量拉则有 1 条
    items_no_filter = await source.fetch_since(datetime(2020, 1, 1, tzinfo=UTC))
    assert len(items_no_filter) == 1
    assert items_no_filter[0].source_msg_id == "12345"
    assert items_no_filter[0].source_code == "sina"


@pytest.mark.asyncio
@respx.mock
async def test_sina_raises_on_missing_feed_key() -> None:
    respx.get("https://zhibo.sina.com.cn/api/zhibo/feed").mock(
        return_value=httpx.Response(200, json={"result": {"data": {}}})
    )
    source = SinaSource()
    with pytest.raises(SourceError, match=r"missing 'result\.data\.feed'"):
        await source.fetch_realtime()


# --------------------- Yahoo --------------------- #


@pytest.mark.asyncio
@respx.mock
async def test_yahoo_parses_rss() -> None:
    rss = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>S&P 500 Headlines</title>
    <item>
      <title>Markets close higher</title>
      <link>https://finance.yahoo.com/news/markets-close-higher</link>
      <pubDate>Mon, 19 Jun 2026 14:30:00 +0000</pubDate>
      <description>Stocks gained on positive earnings.</description>
      <guid>https://finance.yahoo.com/news/markets-close-higher</guid>
    </item>
  </channel>
</rss>"""
    respx.get("https://feeds.finance.yahoo.com/rss/2.0/headline").mock(
        return_value=httpx.Response(200, text=rss, headers={"content-type": "application/xml"}),
    )
    source = YahooFinanceRssSource()
    items = await source.fetch_since(datetime(2020, 1, 1, tzinfo=UTC))
    assert len(items) == 1
    assert items[0].title == "Markets close higher"
    assert items[0].source_code == "yahoo"
    assert items[0].url == "https://finance.yahoo.com/news/markets-close-higher"


@pytest.mark.asyncio
@respx.mock
async def test_yahoo_handles_malformed_rss() -> None:
    respx.get("https://feeds.finance.yahoo.com/rss/2.0/headline").mock(
        return_value=httpx.Response(200, text="not valid xml at all"),
    )
    source = YahooFinanceRssSource()
    items = await source.fetch_realtime()
    # 出错的 ticker 被跳过（log warning），不抛异常
    assert items == []
