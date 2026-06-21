"""NewsClassifier — 规则驱动新闻分类（Spec v3 §6.1.3, M2-c）。

输入：标题 + 摘要（可选）
输出 ClassificationResult：
- primary_category — 一级分类（NewsCategory enum，按 priority 取最高优先级命中）
- all_categories — multi-label 命中（受 max_categories 限制）
- tags — 二级标签（板块名）
- related_sectors — 含命中权重（= 命中关键词数）
- related_symbols — 板块代表股 + 直接被提及的股票名
- matched_keywords — 命中的所有关键词（debug 用）
- is_blacklisted — 是否命中黑名单（命中后仍正常分类，由上层决定怎么用）

规则来源：
- config/classification.yml — 一级分类规则
- config/sectors.yml — 二级板块 + 代表股
- config/keywords.yml — 黑名单
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from amarket.core.logging import get_logger
from amarket.domain.enums import NewsCategory
from amarket.domain.models import NewsItem
from amarket.services.config_service import CONFIG_DIR, _load_yaml

log = get_logger(__name__)


# --------------------------------------------------------------------------- #
# 结果 DTO
# --------------------------------------------------------------------------- #


@dataclass
class SectorMatch:
    name: str
    weight: int  # = 命中关键词数


@dataclass
class SymbolMatch:
    name: str
    weight: int = 1  # 默认 1；直接出现在文本中时 boost 到 2


@dataclass
class ClassificationResult:
    primary_category: NewsCategory
    all_categories: list[NewsCategory] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    related_sectors: list[SectorMatch] = field(default_factory=list)
    related_symbols: list[SymbolMatch] = field(default_factory=list)
    matched_keywords: list[str] = field(default_factory=list)
    is_blacklisted: bool = False


# --------------------------------------------------------------------------- #
# Classifier
# --------------------------------------------------------------------------- #


class NewsClassifier:
    """规则引擎 — 关键词最长匹配 → 一级分类 + 二级标签 + 板块/标的关联。"""

    def __init__(
        self,
        *,
        classification_rules: dict[str, Any],
        sectors_rules: dict[str, Any],
        keywords_rules: dict[str, Any],
    ) -> None:
        # —— 一级分类规则：按 priority 升序（数值小 = 优先级高）
        self._categories = sorted(
            classification_rules.get("categories", []),
            key=lambda c: int(c.get("priority", 999)),
        )
        c_cfg = classification_rules.get("config") or {}
        try:
            self._fallback = NewsCategory(c_cfg.get("fallback_category", "市场行情"))
        except ValueError:
            self._fallback = NewsCategory.MARKET
        self._multi_label: bool = bool(c_cfg.get("multi_label", True))
        self._max_categories: int = int(c_cfg.get("max_categories", 3))

        # —— 二级板块规则
        self._sectors = list(sectors_rules.get("sectors", []))
        s_cfg = sectors_rules.get("config") or {}
        self._max_sectors: int = int(s_cfg.get("max_sectors_per_news", 5))
        self._min_kw_hits: int = int(s_cfg.get("min_keyword_hits", 1))

        # —— 黑名单
        self._blacklist: list[str] = list(keywords_rules.get("blacklist", []))

    @classmethod
    def from_config(cls, config_dir: Path | None = None) -> NewsClassifier:
        """从默认 config/ 目录加载三份 YAML。"""
        cdir = config_dir or CONFIG_DIR
        return cls(
            classification_rules=_load_yaml(cdir / "classification.yml"),
            sectors_rules=_load_yaml(cdir / "sectors.yml"),
            keywords_rules=_load_yaml(cdir / "keywords.yml"),
        )

    # ---------------- 公共入口 ---------------- #

    def classify(self, *, title: str, summary: str | None = None) -> ClassificationResult:
        text = title if not summary else f"{title} {summary}"

        is_blacklisted = any(b in text for b in self._blacklist)
        all_cats, matched_keywords = self._match_categories(text)
        sector_matches, related_symbols = self._match_sectors(text)

        primary = all_cats[0] if all_cats else self._fallback
        if not all_cats:
            all_cats = [self._fallback]

        return ClassificationResult(
            primary_category=primary,
            all_categories=all_cats,
            tags=[s.name for s in sector_matches],
            related_sectors=sector_matches,
            related_symbols=related_symbols,
            matched_keywords=matched_keywords,
            is_blacklisted=is_blacklisted,
        )

    def classify_news(self, item: NewsItem) -> ClassificationResult:
        """便捷方法：直接喂 NewsItem。"""
        return self.classify(title=item.title, summary=item.summary)

    # ---------------- 内部 ---------------- #

    def _match_categories(self, text: str) -> tuple[list[NewsCategory], list[str]]:
        """返回命中的 categories（按 priority 优先）+ 去重的命中关键词列表。"""
        matched: list[tuple[NewsCategory, list[str]]] = []
        for cat in self._categories:
            cat_name = str(cat.get("name", ""))
            try:
                category_enum = NewsCategory(cat_name)
            except ValueError:
                log.warning("classifier.unknown_category", category=cat_name)
                continue

            hits: list[str] = []
            for rule in cat.get("rules", []):
                for kw in rule.get("any_keyword", []):
                    if kw in text:
                        hits.append(str(kw))
            if hits:
                matched.append((category_enum, hits))

        if not self._multi_label and matched:
            matched = matched[:1]
        else:
            matched = matched[: self._max_categories]

        all_cats = [c for c, _ in matched]
        # 去重命中关键词（保序）
        seen: set[str] = set()
        unique_kws: list[str] = []
        for _, hits in matched:
            for kw in hits:
                if kw not in seen:
                    seen.add(kw)
                    unique_kws.append(kw)
        return all_cats, unique_kws

    def _match_sectors(self, text: str) -> tuple[list[SectorMatch], list[SymbolMatch]]:
        """返回命中的板块（按命中数倒序，限 max_sectors）+ 关联个股。"""
        matched_sectors: list[SectorMatch] = []
        for sector in self._sectors:
            name = str(sector.get("name", ""))
            kws = sector.get("keywords", [])
            hits = sum(1 for kw in kws if str(kw) in text)
            if hits >= self._min_kw_hits:
                matched_sectors.append(SectorMatch(name=name, weight=hits))

        matched_sectors.sort(key=lambda s: -s.weight)
        matched_sectors = matched_sectors[: self._max_sectors]
        kept_names = {s.name for s in matched_sectors}

        # 收集这些板块的代表股，并对文中直接被提及的 boost 权重
        stock_weights: dict[str, int] = {}
        for sector in self._sectors:
            if str(sector.get("name", "")) not in kept_names:
                continue
            for stock in sector.get("representative_stocks", []):
                stock_str = str(stock)
                # 命中文本则 weight=2，否则 1
                boost = 2 if stock_str in text else 1
                stock_weights[stock_str] = max(stock_weights.get(stock_str, 0), boost)

        related_symbols = [SymbolMatch(name=n, weight=w) for n, w in stock_weights.items()]
        return matched_sectors, related_symbols


__all__ = [
    "ClassificationResult",
    "NewsClassifier",
    "SectorMatch",
    "SymbolMatch",
]
