"""SimpleRuleScorer 单元测试（Spec v3 §6.1.4 + §8.4-§8.6, M2-d）。

输出 3 个评分 + 1 个置信度（规则路径固定）：
- importance 1-5：基于一级分类 + source priority + 热词权重 + 板块数加分
- urgency 1-5：基于分类 + 热词 urgency_bonus + 是否盘中
- sentiment 6 级：positive/negative 热词频次裁决
- confidence: 3（规则路径默认中等；AI 路径会另算）
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from amarket.domain.enums import NewsCategory, Sentiment, SourcePriority
from amarket.services.news.classifier import (
    ClassificationResult,
    SectorMatch,
    SymbolMatch,
)
from amarket.services.news.scorer import ScoringResult, SimpleRuleScorer

# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


def _build_scorer() -> SimpleRuleScorer:
    """精简 keywords 测试规则。"""
    keywords_rules = {
        "hot_keywords": [
            # 政策大词
            {"value": "央行", "weight": 8, "categories": ["宏观政策"]},
            {"value": "降准", "weight": 10, "categories": ["宏观政策"]},
            # 紧急词
            {"value": "突发", "weight": 10, "urgency_bonus": 2},
            {"value": "紧急", "weight": 9, "urgency_bonus": 2},
            # 风险事件
            {"value": "黑天鹅", "weight": 10, "categories": ["风险事件"], "urgency_bonus": 2},
            {"value": "立案", "weight": 9, "categories": ["公司公告", "风险事件"]},
            # 情绪词
            {"value": "利好", "weight": 5, "sentiment_hint": "positive"},
            {"value": "利空", "weight": 5, "sentiment_hint": "negative"},
            {"value": "业绩预增", "weight": 6, "sentiment_hint": "positive"},
            {"value": "业绩预亏", "weight": 6, "sentiment_hint": "negative"},
            {"value": "回购", "weight": 6, "sentiment_hint": "positive"},
            {"value": "暴雷", "weight": 9, "sentiment_hint": "negative"},
        ],
        "blacklist": [],
        "config": {
            "sentiment_hint_weight": 0.7,
            "max_urgency_bonus": 2,
        },
    }
    return SimpleRuleScorer(keywords_rules=keywords_rules)


def _make_clf(
    primary: NewsCategory = NewsCategory.MARKET,
    *,
    all_cats: list[NewsCategory] | None = None,
    sectors: int = 0,
    symbols: int = 0,
) -> ClassificationResult:
    return ClassificationResult(
        primary_category=primary,
        all_categories=all_cats or [primary],
        related_sectors=[SectorMatch(name=f"s{i}", weight=1) for i in range(sectors)],
        related_symbols=[SymbolMatch(name=f"sym{i}") for i in range(symbols)],
    )


# --------------------------------------------------------------------------- #
# Importance
# --------------------------------------------------------------------------- #


def test_importance_risk_event_with_official_source_max() -> None:
    """央行降准（宏观政策 + HIGHEST 源 + 热词 weight=10）→ 应顶到 5。"""
    scorer = _build_scorer()
    r = scorer.score(
        title="央行紧急宣布降准 0.5 个百分点",
        classification=_make_clf(NewsCategory.MACRO_POLICY),
        source_priority=SourcePriority.HIGHEST,
    )
    assert r.importance == 5


def test_importance_blackswan_max() -> None:
    scorer = _build_scorer()
    r = scorer.score(
        title="突发黑天鹅事件，多家公司被立案",
        classification=_make_clf(NewsCategory.RISK_EVENT),
        source_priority=SourcePriority.HIGH,
    )
    assert r.importance >= 4


def test_importance_normal_company_news() -> None:
    """普通公司新闻 → 3 左右。"""
    scorer = _build_scorer()
    r = scorer.score(
        title="某公司发布回购计划",
        classification=_make_clf(NewsCategory.COMPANY_ANNOUNCEMENT),
        source_priority=SourcePriority.HIGH,
    )
    assert 2 <= r.importance <= 4


def test_importance_low_source_penalized() -> None:
    """LOW 源 → importance 比 HIGH 源低（同一内容比较）。"""
    scorer = _build_scorer()
    clf = _make_clf(NewsCategory.COMPANY_ANNOUNCEMENT)
    high = scorer.score(title="某公司公告", classification=clf, source_priority=SourcePriority.HIGH)
    low = scorer.score(title="某公司公告", classification=clf, source_priority=SourcePriority.LOW)
    assert low.importance < high.importance


def test_importance_multi_sector_bonus() -> None:
    """影响多个板块 → 加分（vs 单板块同分类）。"""
    scorer = _build_scorer()
    base = scorer.score(
        title="某公司新闻",
        classification=_make_clf(NewsCategory.COMPANY_ANNOUNCEMENT, sectors=1),
        source_priority=SourcePriority.HIGH,
    )
    multi = scorer.score(
        title="某公司新闻",
        classification=_make_clf(NewsCategory.COMPANY_ANNOUNCEMENT, sectors=4),
        source_priority=SourcePriority.HIGH,
    )
    assert multi.importance >= base.importance


def test_importance_clamped_to_1_5() -> None:
    """评分必须在 1-5 闭区间。"""
    scorer = _build_scorer()
    # 喂一个所有加分都满的极端 case
    r = scorer.score(
        title="央行突发降准黑天鹅立案",
        classification=_make_clf(NewsCategory.MACRO_POLICY, sectors=10),
        source_priority=SourcePriority.HIGHEST,
    )
    assert 1 <= r.importance <= 5
    # 喂一个所有加分都最低
    r2 = scorer.score(
        title="平淡边缘新闻",
        classification=_make_clf(NewsCategory.TRADE_HINT, sectors=0),
        source_priority=SourcePriority.LOW,
    )
    assert 1 <= r2.importance <= 5


# --------------------------------------------------------------------------- #
# Urgency
# --------------------------------------------------------------------------- #


def test_urgency_blackswan_high() -> None:
    scorer = _build_scorer()
    r = scorer.score(
        title="突发黑天鹅",
        classification=_make_clf(NewsCategory.RISK_EVENT),
        source_priority=SourcePriority.HIGH,
    )
    assert r.urgency >= 4


def test_urgency_normal_news_low() -> None:
    scorer = _build_scorer()
    r = scorer.score(
        title="常规财经新闻",
        classification=_make_clf(NewsCategory.MARKET),
        source_priority=SourcePriority.MEDIUM,
    )
    assert r.urgency <= 3


def test_urgency_keyword_bonus_capped() -> None:
    """多个 urgency 词不会无限堆 — 受 max_urgency_bonus 限制。"""
    scorer = _build_scorer()
    r = scorer.score(
        title="突发 紧急 黑天鹅 三连击",  # 3 个 urgency_bonus=2 的词
        classification=_make_clf(NewsCategory.RISK_EVENT),
        source_priority=SourcePriority.HIGH,
    )
    # 不应超过 5
    assert r.urgency <= 5


def test_urgency_during_market_hours_boost() -> None:
    """盘中（09:30-15:00 Asia/Shanghai 工作日）发布的同一条新闻紧急度更高。"""
    scorer = _build_scorer()
    # 2026-06-22 是周一；UTC 03:00 = Asia/Shanghai 11:00（盘中）
    intraday = datetime(2026, 6, 22, 3, 0, tzinfo=UTC)
    # 同一天 UTC 14:00 = Asia/Shanghai 22:00（盘后）
    afterhours = datetime(2026, 6, 22, 14, 0, tzinfo=UTC)

    clf = _make_clf(NewsCategory.COMPANY_ANNOUNCEMENT)
    r_intraday = scorer.score(
        title="某公司公告",
        classification=clf,
        source_priority=SourcePriority.HIGH,
        published_at=intraday,
    )
    r_after = scorer.score(
        title="某公司公告",
        classification=clf,
        source_priority=SourcePriority.HIGH,
        published_at=afterhours,
    )
    assert r_intraday.urgency >= r_after.urgency


# --------------------------------------------------------------------------- #
# Sentiment
# --------------------------------------------------------------------------- #


def test_sentiment_positive() -> None:
    scorer = _build_scorer()
    r = scorer.score(
        title="重大利好：公司宣布回购",
        classification=_make_clf(NewsCategory.COMPANY_ANNOUNCEMENT),
        source_priority=SourcePriority.HIGH,
    )
    assert r.sentiment in (Sentiment.POSITIVE, Sentiment.STRONG_POSITIVE)


def test_sentiment_strong_positive_when_multiple_hits() -> None:
    scorer = _build_scorer()
    r = scorer.score(
        title="业绩预增 同时启动回购 + 利好不断",
        classification=_make_clf(NewsCategory.COMPANY_ANNOUNCEMENT),
        source_priority=SourcePriority.HIGH,
    )
    assert r.sentiment == Sentiment.STRONG_POSITIVE


def test_sentiment_negative() -> None:
    scorer = _build_scorer()
    r = scorer.score(
        title="公司业绩预亏",
        classification=_make_clf(NewsCategory.COMPANY_ANNOUNCEMENT),
        source_priority=SourcePriority.HIGH,
    )
    assert r.sentiment in (Sentiment.NEGATIVE, Sentiment.STRONG_NEGATIVE)


def test_sentiment_strong_negative() -> None:
    scorer = _build_scorer()
    r = scorer.score(
        title="重大利空：公司暴雷 + 业绩预亏",
        classification=_make_clf(NewsCategory.RISK_EVENT),
        source_priority=SourcePriority.HIGH,
    )
    assert r.sentiment == Sentiment.STRONG_NEGATIVE


def test_sentiment_neutral_when_no_hints() -> None:
    scorer = _build_scorer()
    r = scorer.score(
        title="新闻无明显情绪倾向",
        classification=_make_clf(NewsCategory.MARKET),
        source_priority=SourcePriority.HIGH,
    )
    assert r.sentiment == Sentiment.NEUTRAL


def test_sentiment_uncertain_when_mixed() -> None:
    scorer = _build_scorer()
    r = scorer.score(
        title="利好和利空同时存在的复杂消息",
        classification=_make_clf(NewsCategory.MARKET),
        source_priority=SourcePriority.HIGH,
    )
    assert r.sentiment == Sentiment.UNCERTAIN


# --------------------------------------------------------------------------- #
# Confidence + 结构
# --------------------------------------------------------------------------- #


def test_confidence_default_3() -> None:
    """规则路径 confidence 固定 3。"""
    scorer = _build_scorer()
    r = scorer.score(
        title="任意新闻",
        classification=_make_clf(NewsCategory.MARKET),
        source_priority=SourcePriority.HIGH,
    )
    assert r.confidence == 3


def test_score_returns_correct_types() -> None:
    scorer = _build_scorer()
    r = scorer.score(
        title="央行降准",
        classification=_make_clf(NewsCategory.MACRO_POLICY),
        source_priority=SourcePriority.HIGHEST,
    )
    assert isinstance(r, ScoringResult)
    assert isinstance(r.importance, int)
    assert isinstance(r.urgency, int)
    assert isinstance(r.sentiment, Sentiment)
    assert isinstance(r.confidence, int)


@pytest.mark.parametrize(
    ("imp", "urg"),
    [(1, 1), (3, 3), (5, 5)],
)
def test_score_clamps_in_range(imp: int, urg: int) -> None:
    scorer = _build_scorer()
    r = scorer.score(
        title="x",
        classification=_make_clf(NewsCategory.MARKET),
        source_priority=SourcePriority.LOW,
    )
    assert 1 <= r.importance <= 5
    assert 1 <= r.urgency <= 5
    assert 1 <= r.confidence <= 5


# --------------------------------------------------------------------------- #
# from_config — 真实 YAML
# --------------------------------------------------------------------------- #


def test_scorer_from_config_loads_real_yaml() -> None:
    scorer = SimpleRuleScorer.from_config()
    r = scorer.score(
        title="央行宣布降息 25 个基点",
        classification=_make_clf(NewsCategory.MACRO_POLICY),
        source_priority=SourcePriority.HIGHEST,
    )
    assert r.importance >= 4
    assert r.urgency >= 3
