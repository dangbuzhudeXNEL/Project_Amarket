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
# News Detail DTOs（M3b post-merge polish — `/api/news/{id}` 完整 AI 分析）
# --------------------------------------------------------------------------- #


class RelatedNewsDTO(BaseModel):
    """同事件聚合下的其他新闻（news-detail 页"相关新闻"区）。"""

    news_id: int
    title: str
    source: str
    published_at: datetime
    url: str | None = None


class NewsDetailDTO(BaseModel):
    """`GET /api/news/{id}` 完整详情 DTO — 含全部 AI 分析字段 + 相关新闻。

    与列表用的 NewsCardDTO 区别：
    - 加 content（正文全文）
    - 加全部 AI 评分（confidence / impact_horizon / action_hint）
    - 加 related_sectors / related_symbols（JSON list[dict]）
    - 加 ai_reasoning / risk_notes（AI 推理 + 风险提示）
    - 加 processed_by（哪个 provider 跑的：rule / sdk:* / agent:*）
    - 加 pushed（是否已推送过）
    - 加 related_news（同 event_id 下的其他新闻）
    """

    # 基础字段
    news_id: int
    title: str
    summary: str | None = None
    content: str | None = None  # 详情独有：正文全文
    source: str
    source_priority: str | None = None
    url: str | None = None
    published_at: datetime
    fetched_at: datetime

    # AI 分类
    primary_category: str | None = None
    tags: list[str] = Field(default_factory=list)

    # AI 评分（1-5）
    sentiment: str | None = None
    importance: int | None = None
    urgency: int | None = None
    confidence: int | None = None  # 详情独有
    impact_horizon: str | None = None  # 详情独有
    action_hint: str | None = None  # 详情独有

    # 影响范围 — 详情独有
    related_sectors: list[dict[str, Any]] = Field(default_factory=list)
    related_symbols: list[dict[str, Any]] = Field(default_factory=list)

    # AI 推理 — 详情独有
    ai_reasoning: str | None = None
    risk_notes: str | None = None
    processed_by: str | None = None

    # 告警
    alert_level: str | None = None
    pushed: bool = False  # 详情独有

    # 相关新闻（同事件） — 详情独有
    related_news: list[RelatedNewsDTO] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Alert DTOs（M2-h）
# --------------------------------------------------------------------------- #


class AlertDTO(BaseModel):
    """`GET /api/alerts` 单条 DTO。"""

    alert_id: int
    news_id: int | None
    level: str  # 'P0' / 'P1' / 'P2'
    trigger_reason: str
    analysis_id: int | None = None
    status: str  # 'pending' / 'pushed' / 'dismissed'
    created_at: datetime
    pushed_at: datetime | None = None
    # 便利字段（join news 拿）
    news_title: str | None = None
    news_source: str | None = None
    primary_category: str | None = None


class AlertListResponse(BaseModel):
    items: list[AlertDTO]
    total: int
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


# --------------------------------------------------------------------------- #
# Sector DTOs（M3b）
# --------------------------------------------------------------------------- #


class SectorDTO(BaseModel):
    """单个板块的看板数据（Spec v3 §10.3 / M3a POC sectors.json 对齐）。"""

    name: str
    change_pct: float | None = None  # M3b Phase 1：None 占位，M4 真填
    news_count_24h: int = 0
    market_cap_weight: float | None = None  # M3b stub mapping
    top_symbols: list[dict[str, Any]] = Field(default_factory=list)


class SectorListResponse(BaseModel):
    """`GET /api/dashboard/sectors` 响应。"""

    as_of: datetime = Field(default_factory=lambda: datetime.now(UTC))
    window: str = "1d"  # '1h' | '4h' | '1d'
    sectors: list[SectorDTO] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Mover DTOs（M3b — 个股异动榜）
# --------------------------------------------------------------------------- #


class MoverDTO(BaseModel):
    """个股异动榜单条 DTO（M3b — 简化版，行情从 MarketSnapshot 取）。"""

    code: str
    name: str | None = None
    change_pct: float | None = None
    price: float | None = None
    volume: float | None = None
    turnover: float | None = None


class MoversListResponse(BaseModel):
    """`GET /api/dashboard/movers` 响应。"""

    as_of: datetime = Field(default_factory=lambda: datetime.now(UTC))
    top_gainers: list[MoverDTO] = Field(default_factory=list)
    top_losers: list[MoverDTO] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Report DTOs（M3b — 6 时段日报）
# --------------------------------------------------------------------------- #


class ReportSummaryDTO(BaseModel):
    """`GET /api/reports` 列表项（不含 markdown 全文）。"""

    report_id: int
    date: date  # 与 spec/前端字段名一致
    kind: str  # 'premarket' | 'morning' | 'noon' | 'afternoon' | 'close' | 'evening'
    status: str  # 'pending' | 'completed' | 'failed'
    generated_by: str | None = None
    generated_at: datetime
    push_count: int = 0


class ReportDetailDTO(BaseModel):
    """`GET /api/reports/{id}` + `/today/{kind}` 响应（含 markdown 全文）。"""

    report_id: int
    date: date  # 与 spec/前端字段名一致
    kind: str
    status: str
    markdown: str | None = None
    content_json: dict[str, Any] = Field(default_factory=dict)
    generated_by: str | None = None
    generated_at: datetime
    push_count: int = 0


class ReportListResponse(BaseModel):
    items: list[ReportSummaryDTO]
    total: int
    offset: int
    limit: int


class TodayReportsResponse(BaseModel):
    """`GET /api/reports/today` — 今日 6 时段（缺失为 None）。"""

    today: date
    # NOTE: 字段名保留为 `reports_by_kind`；DashboardSummary 用 `today_reports` 表达同样的结构 —— 故意不统一，保持各自 API 的 POC JSON 约定
    reports_by_kind: dict[str, ReportDetailDTO | None] = Field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Dashboard Summary（M3b — 首页聚合）
# --------------------------------------------------------------------------- #


class DashboardSummary(BaseModel):
    """`GET /api/dashboard/summary` — 首页一次性聚合（前端 index.html 用）。"""

    as_of: datetime = Field(default_factory=lambda: datetime.now(UTC))
    market_status: MarketStatusBar = Field(default_factory=MarketStatusBar)
    today_conclusion: str | None = None
    latest_news: list[NewsCardDTO] = Field(default_factory=list)
    p0_alerts: list[AlertDTO] = Field(default_factory=list)
    p1_alerts: list[AlertDTO] = Field(default_factory=list)
    top_sectors: list[SectorDTO] = Field(default_factory=list)
    top_movers: list[MoverDTO] = Field(default_factory=list)
    # NOTE: 字段名保留为 `today_reports`；TodayReportsResponse 用 `reports_by_kind` 表达同样的结构 —— 故意不统一，保持各自 API 的 POC JSON 约定
    today_reports: dict[str, ReportDetailDTO | None] = Field(default_factory=dict)


__all__ = [
    "AlertDTO",
    "AlertListResponse",
    "DashboardSummary",
    "IndexSnapshot",
    "MarketStatusBar",
    "MoverDTO",
    "MoversListResponse",
    "NewsCardDTO",
    "NewsDetailDTO",
    "NewsListResponse",
    "NewsSourceDTO",
    "RawNewsItem",
    "RelatedNewsDTO",
    "ReportDetailDTO",
    "ReportListResponse",
    "ReportSummaryDTO",
    "SectorDTO",
    "SectorListResponse",
    "TodayReportsResponse",
]
