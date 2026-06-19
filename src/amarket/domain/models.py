"""SQLModel ORM 表定义 — Spec v3 §7.2 完整 schema。

M0：仅 `users` 表（baseline）
M1：本次新增 14 张业务表（subscriptions / news_sources / source_health /
    news_items / news_events / news_analysis / market_snapshots /
    sector_trends / alerts / reports / push_records /
    params / param_versions / audit_events / config_versions）

约定：
- 所有时间字段用 UTC（domain 层不暴露时区差）
- JSON 字段用 sa_type=JSON（SQLite 存 TEXT，PG 切换 0 改动）
- enum 字段存 TEXT，类型用 enums.py 中的 StrEnum
- 外键显式 foreign_key 声明
- 复合 unique constraint 用 __table_args__
"""

from __future__ import annotations

from datetime import UTC, datetime
from datetime import date as date_t
from typing import Any

from sqlalchemy import JSON, UniqueConstraint
from sqlmodel import Field, SQLModel

from amarket.domain.enums import (
    ActionHint,
    AlertLevel,
    ImpactHorizon,
    NewsCategory,
    PushKind,
    PushStatus,
    ReportKind,
    Sentiment,
    SourceHealthStatus,
    SourcePriority,
    UserRole,
)

# --------------------------------------------------------------------------- #
# Mixins
# --------------------------------------------------------------------------- #


class TimestampMixin(SQLModel):
    """共享时间戳字段（仅在子类用 `table=True` 时生效）。"""

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# --------------------------------------------------------------------------- #
# 用户与订阅
# --------------------------------------------------------------------------- #


class User(TimestampMixin, table=True):
    """用户表（Spec v3 §7.2 - `users`）。"""

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=64)
    role: UserRole = Field(default=UserRole.ADMIN)
    timezone: str = Field(default="Asia/Shanghai", max_length=64)


class Subscription(TimestampMixin, table=True):
    """用户订阅（关注的股票 / 板块 / 关键词 / 市场）。"""

    __tablename__ = "subscriptions"
    __table_args__ = (UniqueConstraint("user_id", "kind", "value", name="uq_user_kind_value"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    kind: str = Field(max_length=16)  # 'stock' | 'sector' | 'keyword' | 'market'
    value: str = Field(max_length=128)
    weight: int = Field(default=50, ge=0, le=100)
    enabled: bool = Field(default=True)


# --------------------------------------------------------------------------- #
# 新闻源 + 健康
# --------------------------------------------------------------------------- #


class NewsSource(SQLModel, table=True):
    """新闻源配置（持久化运行时状态）。"""

    __tablename__ = "news_sources"

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True, max_length=32)
    name: str = Field(max_length=64)
    priority: SourcePriority = Field(default=SourcePriority.MEDIUM)
    enabled: bool = Field(default=True)
    last_pulled_at: datetime | None = Field(default=None)
    last_error: str | None = Field(default=None, max_length=512)
    consecutive_failures: int = Field(default=0)
    config_json: dict[str, Any] = Field(default_factory=dict, sa_type=JSON)


class SourceHealth(SQLModel, table=True):
    """新闻 / 行情源每次轮询的健康记录（仅运维 90 天保留）。"""

    __tablename__ = "source_health"

    id: int | None = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="news_sources.id", index=True)
    ts: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    status: SourceHealthStatus = Field(default=SourceHealthStatus.OK)
    latency_ms: float | None = Field(default=None)
    error: str | None = Field(default=None, max_length=512)
    items_returned: int = Field(default=0)


# --------------------------------------------------------------------------- #
# 新闻原文 + 事件聚合 + AI 分析
# --------------------------------------------------------------------------- #


class NewsItem(SQLModel, table=True):
    """原始新闻条目（不可变，所有源标准化后入库）。"""

    __tablename__ = "news_items"
    __table_args__ = (UniqueConstraint("source_id", "source_msg_id", name="uq_source_msgid"),)

    id: int | None = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="news_sources.id", index=True)
    source_msg_id: str = Field(max_length=256)
    event_id: int | None = Field(default=None, foreign_key="news_events.id", index=True)

    title: str = Field(max_length=512)
    summary: str | None = Field(default=None, max_length=2048)
    content: str | None = Field(default=None)
    url: str | None = Field(default=None, max_length=1024)

    published_at: datetime = Field(index=True)
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    content_hash: str | None = Field(default=None, max_length=64, index=True)
    raw_payload: dict[str, Any] = Field(default_factory=dict, sa_type=JSON)


class NewsEvent(SQLModel, table=True):
    """同事件聚合（多源对同一事件去重后归到一组）。"""

    __tablename__ = "news_events"

    id: int | None = Field(default=None, primary_key=True)
    signature: str = Field(index=True, max_length=64)  # SimHash hex
    canonical_title: str = Field(max_length=512)
    first_seen_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_seen_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    news_count: int = Field(default=1)
    top_source: str | None = Field(default=None, max_length=32)


class NewsAnalysis(SQLModel, table=True):
    """AI / 规则分析结果（按 processed_by 区分版本）。"""

    __tablename__ = "news_analysis"
    __table_args__ = (UniqueConstraint("news_id", "processed_by", name="uq_news_processed_by"),)

    id: int | None = Field(default=None, primary_key=True)
    news_id: int = Field(foreign_key="news_items.id", index=True)
    event_id: int | None = Field(default=None, foreign_key="news_events.id")

    # 分类
    primary_category: NewsCategory = Field(index=True)
    tags: list[str] = Field(default_factory=list, sa_type=JSON)
    related_markets: list[str] = Field(default_factory=list, sa_type=JSON)
    related_sectors: list[dict[str, Any]] = Field(default_factory=list, sa_type=JSON)
    related_symbols: list[dict[str, Any]] = Field(default_factory=list, sa_type=JSON)

    # 评分（1-5）
    sentiment: Sentiment = Field(default=Sentiment.NEUTRAL)
    importance_score: int = Field(default=1, ge=1, le=5, index=True)
    urgency_score: int = Field(default=1, ge=1, le=5, index=True)
    confidence_score: int = Field(default=3, ge=1, le=5)
    impact_horizon: ImpactHorizon = Field(default=ImpactHorizon.INTRADAY)

    # 决策辅助
    action_hint: ActionHint = Field(default=ActionHint.WATCH)
    ai_reasoning: str | None = Field(default=None)
    risk_notes: str | None = Field(default=None)

    # 元数据
    processed_by: str = Field(max_length=64)
    processed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    duration_ms: int | None = Field(default=None)


# --------------------------------------------------------------------------- #
# 行情 + 板块
# --------------------------------------------------------------------------- #


class MarketSnapshot(SQLModel, table=True):
    """行情快照（指数 / 股票 / 板块 / 商品 / 汇率）。"""

    __tablename__ = "market_snapshots"

    id: int | None = Field(default=None, primary_key=True)
    ts: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    asset_kind: str = Field(max_length=16, index=True)  # 'index'|'stock'|'sector'|'commodity'|'fx'
    code: str = Field(max_length=32, index=True)
    name: str | None = Field(default=None, max_length=64)
    price: float | None = Field(default=None)
    change_pct: float | None = Field(default=None)
    change_abs: float | None = Field(default=None)
    volume: float | None = Field(default=None)
    turnover: float | None = Field(default=None)
    extra_json: dict[str, Any] = Field(default_factory=dict, sa_type=JSON)


class SectorTrend(SQLModel, table=True):
    """板块趋势聚合（每 15 分钟刷新）。"""

    __tablename__ = "sector_trends"

    id: int | None = Field(default=None, primary_key=True)
    ts: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    sector_name: str = Field(max_length=64, index=True)
    change_pct: float | None = Field(default=None)
    news_heat: int = Field(default=0)
    sentiment_score: float | None = Field(default=None)  # -1.0 ~ +1.0
    fund_status: str | None = Field(default=None, max_length=16)  # 放量/缩量/流入/流出
    representative_stocks: list[dict[str, Any]] = Field(default_factory=list, sa_type=JSON)
    trend_judgment: str | None = Field(default=None, max_length=16)  # 延续/分歧/退潮/反转


# --------------------------------------------------------------------------- #
# 告警 + 日报 + 推送
# --------------------------------------------------------------------------- #


class Alert(SQLModel, table=True):
    """P0-P3 告警记录（决策后写入 → 待推送）。"""

    __tablename__ = "alerts"

    id: int | None = Field(default=None, primary_key=True)
    news_id: int | None = Field(default=None, foreign_key="news_items.id", index=True)
    level: AlertLevel = Field(index=True)
    trigger_reason: str = Field(max_length=256)
    analysis_id: int | None = Field(default=None, foreign_key="news_analysis.id")
    status: str = Field(default="pending", max_length=16, index=True)  # pending|pushed|dismissed
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    pushed_at: datetime | None = Field(default=None)


class Report(SQLModel, table=True):
    """6 时段日报。"""

    __tablename__ = "reports"
    __table_args__ = (UniqueConstraint("date", "kind", name="uq_report_date_kind"),)

    id: int | None = Field(default=None, primary_key=True)
    date: date_t = Field(index=True)
    kind: ReportKind = Field(index=True)
    status: str = Field(default="pending", max_length=16)  # pending|completed|failed
    markdown: str | None = Field(default=None)
    content_json: dict[str, Any] = Field(default_factory=dict, sa_type=JSON)
    generated_by: str | None = Field(default=None, max_length=64)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    push_count: int = Field(default=0)


class PushRecord(SQLModel, table=True):
    """推送日志（一行 = 一次实际发送尝试）。"""

    __tablename__ = "push_records"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    kind: PushKind = Field(index=True)
    ref_id: int | None = Field(default=None)  # alerts.id 或 reports.id（弱关联）
    channel: str = Field(max_length=32)
    content: str
    sent_at: datetime | None = Field(default=None, index=True)
    status: PushStatus = Field(default=PushStatus.PENDING, index=True)
    error_message: str | None = Field(default=None, max_length=512)
    attempt_count: int = Field(default=0)


# --------------------------------------------------------------------------- #
# 参数配置 + 审计 + 配置版本
# --------------------------------------------------------------------------- #


class Param(SQLModel, table=True):
    """参数当前值索引（实际值在 ParamVersion）。"""

    __tablename__ = "params"

    key: str = Field(primary_key=True, max_length=128)
    current_version: int  # 指向 param_versions.id（不设 FK 避免循环）
    scope: str = Field(default="global", max_length=64)  # global | user:<id> | sector:<name>
    sensitive: bool = Field(default=False)
    description: str | None = Field(default=None, max_length=256)


class ParamVersion(SQLModel, table=True):
    """参数版本历史（写入即新 row，不可变）。"""

    __tablename__ = "param_versions"

    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(max_length=128, index=True)
    value_json: Any = Field(sa_type=JSON)
    changed_by: int | None = Field(default=None, foreign_key="users.id")
    change_reason: str | None = Field(default=None, max_length=256)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)


class AuditEvent(SQLModel, table=True):
    """审计日志（参数变更 / 用户操作 / 推送决策 / 告警 dismiss 等）。"""

    __tablename__ = "audit_events"

    id: int | None = Field(default=None, primary_key=True)
    ts: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    actor_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    action: str = Field(max_length=64, index=True)
    target_kind: str | None = Field(default=None, max_length=32)
    target_id: str | None = Field(default=None, max_length=128)
    metadata_json: dict[str, Any] = Field(default_factory=dict, sa_type=JSON)


class ConfigVersion(SQLModel, table=True):
    """系统配置文件版本（YAML 文本快照，仅审计用）。"""

    __tablename__ = "config_versions"
    __table_args__ = (UniqueConstraint("config_name", "version", name="uq_config_name_ver"),)

    id: int | None = Field(default=None, primary_key=True)
    config_name: str = Field(max_length=64)
    version: int
    content_yaml: str
    changed_by: int | None = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


__all__ = [
    "Alert",
    "AuditEvent",
    "ConfigVersion",
    "MarketSnapshot",
    "NewsAnalysis",
    "NewsEvent",
    "NewsItem",
    "NewsSource",
    "Param",
    "ParamVersion",
    "PushRecord",
    "Report",
    "SectorTrend",
    "SourceHealth",
    "Subscription",
    "TimestampMixin",
    "User",
]
