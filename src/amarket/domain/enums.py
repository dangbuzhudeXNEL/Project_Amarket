"""核心枚举定义。

跨 Phase 1 / Phase 2 共用。Service / API 层应该使用这些枚举而非裸字符串。
"""

from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    """用户角色（Spec v3 §4.1）。"""

    ADMIN = "admin"
    ANALYST = "analyst"
    TRADER = "trader"
    GUEST = "guest"


class SourcePriority(StrEnum):
    """新闻 / 行情源优先级（Spec v3 §6.2.1）。"""

    HIGHEST = "highest"  # 央行 / 证监会 / 财政部 / 交易所
    HIGH = "high"  # 同花顺 / 东方财富
    MEDIUM = "medium"  # 雅虎财经 / 备用源
    LOW = "low"


class NewsCategory(StrEnum):
    """新闻一级分类（Spec v3 §8.1 — PRD §5.1）。"""

    MACRO_POLICY = "宏观政策"
    MARKET = "市场行情"
    COMPANY_ANNOUNCEMENT = "公司公告"
    OVERSEAS = "海外映射"
    COMMODITY = "大宗商品"
    RISK_EVENT = "风险事件"
    FUND_FLOW = "资金流"
    TRADE_HINT = "交易提示"


class Sentiment(StrEnum):
    """情绪方向（Spec v3 §8.6 — PRD §6.3）。"""

    STRONG_POSITIVE = "强利多"
    POSITIVE = "利多"
    NEUTRAL = "中性"
    NEGATIVE = "利空"
    STRONG_NEGATIVE = "强利空"
    UNCERTAIN = "不确定"


class ImpactHorizon(StrEnum):
    """影响时长（Spec v3 §8.3）。"""

    IMMEDIATE = "即时"
    INTRADAY = "日内"
    SHORT_TERM = "短期"
    MEDIUM_TERM = "中期"


class ActionHint(StrEnum):
    """决策辅助提示（Spec v3 §8.3 — **永远不会出现"买入/卖出"等明确指令**）。"""

    WATCH = "观察"
    FOLLOW = "关注"
    ADD = "加仓"
    REDUCE = "减仓"
    AVOID = "规避"


class AlertLevel(StrEnum):
    """推送告警等级（Spec v3 §3.1 决策 #4）。"""

    P0 = "P0"  # 黑天鹅 / 重大政策 — 即时强提醒，全渠道并发
    P1 = "P1"  # 重要 / 订阅命中 — 即时推送
    P2 = "P2"  # 普通重要 — 汇总推送（每 30min）
    P3 = "P3"  # 一般 — 仅入库

    @property
    def is_pushable(self) -> bool:
        return self in (AlertLevel.P0, AlertLevel.P1, AlertLevel.P2)


class PushStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"


class PushKind(StrEnum):
    ALERT_P0 = "alert_p0"
    ALERT_P1 = "alert_p1"
    ALERT_P2_BATCH = "alert_p2_batch"
    REPORT = "report"
    MANUAL = "manual"


class ReportKind(StrEnum):
    """6 时段日报（Spec v3 §6.1.9 — PRD §3.1）。"""

    PREMARKET = "premarket"  # 08:00-08:45 盘前
    MORNING = "morning"  # 09:25-10:15 早盘跟踪
    NOON = "noon"  # 11:30-12:20 午间
    AFTERNOON = "afternoon"  # 14:30-15:00 尾盘
    CLOSE = "close"  # 15:15-16:30 收盘后
    EVENING = "evening"  # 20:00-22:30 晚间


class SourceHealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"


class ProcessingProvider(StrEnum):
    """`news_analysis.processed_by` 的几个标准值。"""

    RULE = "rule"
    SDK_ANTHROPIC = "sdk:anthropic"
    SDK_DEEPSEEK = "sdk:deepseek"
    AGENT_NEWS_ANALYST = "agent:news-analyst"
    AGENT_REALTIME_CLASSIFIER = "agent:news-classifier-realtime"
    AGENT_DAILY_REPORT_WRITER = "agent:daily-report-writer"


__all__ = [
    "ActionHint",
    "AlertLevel",
    "ImpactHorizon",
    "NewsCategory",
    "ProcessingProvider",
    "PushKind",
    "PushStatus",
    "ReportKind",
    "Sentiment",
    "SourceHealthStatus",
    "SourcePriority",
    "UserRole",
]
