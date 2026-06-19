"""Pydantic 业务对象 / API DTOs（Spec v3 §10.3）。

注意：SQLModel 表定义在 `models.py`；这里只放纯 BaseModel 的对外 DTOs。
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# Market 行情 DTOs
# --------------------------------------------------------------------------- #


class IndexSnapshot(BaseModel):
    """指数行情快照（adapter 返回 + API 输出共用）。"""

    code: str  # 'sh000001' / 'sz399001' / ...
    name: str  # '上证指数' / ...
    price: float
    change_pct: float | None = None  # 涨跌幅 %
    change_abs: float | None = None  # 涨跌额
    prev_close: float | None = None
    volume: float | None = None
    turnover: float | None = None
    trading_date: date | None = None
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source: str = "akshare"


class MarketStatusBar(BaseModel):
    """看板顶部市场状态栏（Spec v3 §10.1 ①）。"""

    indexes: list[IndexSnapshot] = Field(default_factory=list)
    fx: list[IndexSnapshot] = Field(default_factory=list)
    commodities: list[IndexSnapshot] = Field(default_factory=list)
    refreshed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# --------------------------------------------------------------------------- #
# News DTOs
# --------------------------------------------------------------------------- #


class RawNewsItem(BaseModel):
    """新闻源 adapter 返回的标准化条目（入库前 DTO）。"""

    source_code: str  # 对应 NewsSource.code
    source_msg_id: str  # 源平台原始 ID（去重用）
    title: str
    summary: str | None = None
    content: str | None = None
    url: str | None = None
    published_at: datetime
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class NewsCardDTO(BaseModel):
    """新闻流单条 DTO（Spec v3 §10.3）。M1 阶段是简化版，M2 起填充分析字段。"""

    news_id: int
    title: str
    summary: str | None = None
    source: str
    source_priority: str | None = None
    url: str | None = None
    published_at: datetime
    fetched_at: datetime
    # M2+ 字段（M1 阶段返回 None）
    primary_category: str | None = None
    tags: list[str] = Field(default_factory=list)
    sentiment: str | None = None
    importance: int | None = None
    urgency: int | None = None
    alert_level: str | None = None


class NewsListResponse(BaseModel):
    """`GET /api/news` 响应。"""

    items: list[NewsCardDTO]
    total: int  # 当前 filter 下的总数
    offset: int
    limit: int


# --------------------------------------------------------------------------- #
# Source DTOs
# --------------------------------------------------------------------------- #


class NewsSourceDTO(BaseModel):
    """新闻源状态（用于 `/api/dashboard/news-sources`）。"""

    code: str
    name: str
    priority: str
    enabled: bool
    last_pulled_at: datetime | None = None
    last_error: str | None = None
    consecutive_failures: int = 0
    recent_items_count: int | None = None  # 最近 1h


__all__ = [
    "IndexSnapshot",
    "MarketStatusBar",
    "NewsCardDTO",
    "NewsListResponse",
    "NewsSourceDTO",
    "RawNewsItem",
]
