"""Enums and AlertLevel pushable property test。"""

from __future__ import annotations

from amarket.domain.enums import AlertLevel, NewsCategory, ReportKind, Sentiment


def test_alert_level_p0_p1_p2_pushable() -> None:
    assert AlertLevel.P0.is_pushable is True
    assert AlertLevel.P1.is_pushable is True
    assert AlertLevel.P2.is_pushable is True
    assert AlertLevel.P3.is_pushable is False


def test_news_category_chinese_values() -> None:
    assert NewsCategory.MACRO_POLICY.value == "宏观政策"
    assert NewsCategory.RISK_EVENT.value == "风险事件"
    assert NewsCategory.FUND_FLOW.value == "资金流"


def test_sentiment_six_levels() -> None:
    values = {s.value for s in Sentiment}
    assert values == {"强利多", "利多", "中性", "利空", "强利空", "不确定"}


def test_report_kind_six_periods() -> None:
    kinds = {k.value for k in ReportKind}
    assert kinds == {"premarket", "morning", "noon", "afternoon", "close", "evening"}
