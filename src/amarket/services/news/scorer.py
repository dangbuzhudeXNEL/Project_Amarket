"""SimpleRuleScorer — 规则路径新闻评分（Spec v3 §6.1.4 + §8.4-§8.6, M2-d）。

输入：title + summary + ClassificationResult + source_priority + 发布时间
输出 ScoringResult：
- importance 1-5：分类基线 + 热词权重加分 + 多板块加分 + source priority delta
- urgency 1-5：分类基线 + 热词 urgency_bonus（受 cap）+ 盘中加 1
- sentiment 6 级：positive/negative hint 频次裁决
- confidence: 3（规则路径固定中等；AI 路径会另算）

定位：AI 全失败时的兜底（永不"无评分"）。
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from amarket.core.logging import get_logger
from amarket.domain.enums import NewsCategory, Sentiment, SourcePriority
from amarket.domain.models import NewsItem
from amarket.services.config_service import CONFIG_DIR, _load_yaml
from amarket.services.news.classifier import ClassificationResult

log = get_logger(__name__)

CN_TZ = ZoneInfo("Asia/Shanghai")

# --------------------------------------------------------------------------- #
# 评分基线表（Spec v3 §8.4 / §8.5）
# --------------------------------------------------------------------------- #

# 一级分类 → importance 基线
_CATEGORY_BASE_IMPORTANCE: dict[NewsCategory, int] = {
    NewsCategory.MACRO_POLICY: 4,
    NewsCategory.RISK_EVENT: 4,
    NewsCategory.COMPANY_ANNOUNCEMENT: 3,
    NewsCategory.OVERSEAS: 3,
    NewsCategory.MARKET: 3,
    NewsCategory.FUND_FLOW: 3,
    NewsCategory.COMMODITY: 2,
    NewsCategory.TRADE_HINT: 2,
}

# 一级分类 → urgency 基线
_CATEGORY_BASE_URGENCY: dict[NewsCategory, int] = {
    NewsCategory.RISK_EVENT: 3,
    NewsCategory.MACRO_POLICY: 3,
    NewsCategory.COMPANY_ANNOUNCEMENT: 2,
    NewsCategory.OVERSEAS: 2,
    NewsCategory.MARKET: 2,
    NewsCategory.FUND_FLOW: 2,
    NewsCategory.COMMODITY: 2,
    NewsCategory.TRADE_HINT: 1,
}

# Source priority → importance delta
_SOURCE_IMPORTANCE_DELTA: dict[SourcePriority, int] = {
    SourcePriority.HIGHEST: +1,
    SourcePriority.HIGH: 0,
    SourcePriority.MEDIUM: -1,
    SourcePriority.LOW: -1,
}


# --------------------------------------------------------------------------- #
# 结果 DTO
# --------------------------------------------------------------------------- #


@dataclass
class ScoringResult:
    importance: int  # 1-5
    urgency: int  # 1-5
    sentiment: Sentiment
    confidence: int = 3


# --------------------------------------------------------------------------- #
# Service
# --------------------------------------------------------------------------- #


class SimpleRuleScorer:
    """规则路径评分（importance / urgency / sentiment）。"""

    def __init__(self, *, keywords_rules: dict[str, Any]) -> None:
        self._hot = list(keywords_rules.get("hot_keywords", []))
        cfg = keywords_rules.get("config") or {}
        self._max_urgency_bonus = int(cfg.get("max_urgency_bonus", 2))
        # sentiment_hint_weight 当前未使用（hint 是 binary），保留供未来权重化
        self._sentiment_hint_weight = float(cfg.get("sentiment_hint_weight", 0.7))

    @classmethod
    def from_config(cls, config_dir: Path | None = None) -> SimpleRuleScorer:
        cdir = config_dir or CONFIG_DIR
        return cls(keywords_rules=_load_yaml(cdir / "keywords.yml"))

    # ---------------- 公共入口 ---------------- #

    def score(
        self,
        *,
        title: str,
        summary: str | None = None,
        classification: ClassificationResult,
        source_priority: SourcePriority,
        published_at: datetime | None = None,
    ) -> ScoringResult:
        text = title if not summary else f"{title} {summary}"
        hits = self._find_keyword_hits(text)
        max_kw_weight = max((int(kw.get("weight", 0)) for kw in hits), default=0)
        urgency_bonuses = [
            int(kw.get("urgency_bonus", 0)) for kw in hits if kw.get("urgency_bonus")
        ]
        sentiment_hints = [
            str(kw.get("sentiment_hint", "")) for kw in hits if kw.get("sentiment_hint")
        ]

        importance = self._compute_importance(
            classification=classification,
            source_priority=source_priority,
            max_keyword_weight=max_kw_weight,
        )
        urgency = self._compute_urgency(
            classification=classification,
            urgency_bonuses=urgency_bonuses,
            published_at=published_at,
        )
        sentiment = self._decide_sentiment(sentiment_hints)

        return ScoringResult(
            importance=importance,
            urgency=urgency,
            sentiment=sentiment,
            confidence=3,
        )

    def score_news(
        self,
        item: NewsItem,
        *,
        classification: ClassificationResult,
        source_priority: SourcePriority,
    ) -> ScoringResult:
        """便捷方法：直接喂 NewsItem。"""
        return self.score(
            title=item.title,
            summary=item.summary,
            classification=classification,
            source_priority=source_priority,
            published_at=item.published_at,
        )

    # ---------------- 内部 ---------------- #

    def _find_keyword_hits(self, text: str) -> list[dict[str, Any]]:
        return [kw for kw in self._hot if str(kw.get("value", "")) in text]

    def _compute_importance(
        self,
        *,
        classification: ClassificationResult,
        source_priority: SourcePriority,
        max_keyword_weight: int,
    ) -> int:
        base = _CATEGORY_BASE_IMPORTANCE.get(classification.primary_category, 2)
        if max_keyword_weight >= 8:
            base += 1
        if len(classification.related_sectors) >= 3:
            base += 1
        base += _SOURCE_IMPORTANCE_DELTA.get(source_priority, 0)
        return max(1, min(5, base))

    def _compute_urgency(
        self,
        *,
        classification: ClassificationResult,
        urgency_bonuses: list[int],
        published_at: datetime | None,
    ) -> int:
        base = _CATEGORY_BASE_URGENCY.get(classification.primary_category, 2)
        base += min(sum(urgency_bonuses), self._max_urgency_bonus)
        if published_at and _is_market_hours(published_at):
            base += 1
        return max(1, min(5, base))

    def _decide_sentiment(self, hints: list[str]) -> Sentiment:
        counts = Counter(hints)
        pos = counts.get("positive", 0)
        neg = counts.get("negative", 0)

        if pos == 0 and neg == 0:
            return Sentiment.NEUTRAL
        if pos > 0 and neg > 0 and abs(pos - neg) <= 1:
            return Sentiment.UNCERTAIN
        if pos > neg:
            return Sentiment.STRONG_POSITIVE if pos >= 3 else Sentiment.POSITIVE
        if neg > pos:
            return Sentiment.STRONG_NEGATIVE if neg >= 2 else Sentiment.NEGATIVE
        return Sentiment.UNCERTAIN  # 相等且都非 0（被上面 abs<=1 拦掉了，但保留兜底）


def _is_market_hours(dt: datetime) -> bool:
    """是否在 A 股交易时段（09:30-11:30 + 13:00-15:00 Asia/Shanghai，工作日）。"""
    cn = dt.astimezone(CN_TZ)
    if cn.weekday() >= 5:  # 周末
        return False
    hour_frac = cn.hour + cn.minute / 60
    return (9.5 <= hour_frac <= 11.5) or (13.0 <= hour_frac <= 15.0)


__all__ = ["ScoringResult", "SimpleRuleScorer"]
