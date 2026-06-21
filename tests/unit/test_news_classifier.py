"""NewsClassifier 单元测试（Spec v3 §6.1.3 — M2-c）。

规则驱动：
- 一级 8 类（NewsCategory），按 priority 排序，最低 priority = primary_category
- 二级 14+ 板块标签（sectors.yml）
- 板块 → 代表个股关联（representative_stocks）
- 黑名单关键词（hot_keywords.blacklist）
"""

from __future__ import annotations

from amarket.domain.enums import NewsCategory
from amarket.services.news.classifier import (
    ClassificationResult,
    NewsClassifier,
    SectorMatch,
    SymbolMatch,
)

# --------------------------------------------------------------------------- #
# Fixtures — 用最小化的规则集，独立于真实 config/，避免规则改动碾测试
# --------------------------------------------------------------------------- #


def _build_test_classifier() -> NewsClassifier:
    """构建一个测试用的精简 classifier。"""
    classification_rules = {
        "categories": [
            {
                "name": "宏观政策",
                "priority": 1,
                "rules": [{"any_keyword": ["央行", "降准", "降息", "美联储"]}],
            },
            {
                "name": "风险事件",
                "priority": 2,
                "rules": [{"any_keyword": ["黑天鹅", "暴雷", "立案", "战争"]}],
            },
            {
                "name": "公司公告",
                "priority": 3,
                "rules": [{"any_keyword": ["业绩预增", "回购", "停牌", "并购"]}],
            },
            {
                "name": "市场行情",
                "priority": 7,
                "rules": [{"any_keyword": ["上证", "涨停", "成交额"]}],
            },
        ],
        "config": {
            "fallback_category": "市场行情",
            "multi_label": True,
            "max_categories": 3,
        },
    }
    sectors_rules = {
        "sectors": [
            {
                "name": "AI算力",
                "keywords": ["AI算力", "算力", "GPU", "大模型"],
                "representative_stocks": ["寒武纪", "中科曙光"],
            },
            {
                "name": "半导体",
                "keywords": ["半导体", "芯片", "光刻"],
                "representative_stocks": ["中芯国际", "韦尔股份"],
            },
            {
                "name": "新能源车",
                "keywords": ["新能源车", "电动车", "比亚迪"],
                "representative_stocks": ["比亚迪", "宁德时代"],
            },
        ],
        "config": {"max_sectors_per_news": 5, "min_keyword_hits": 1},
    }
    keywords_rules = {
        "hot_keywords": [],
        "blacklist": ["广告", "扫码", "震惊", "速看"],
        "config": {},
    }
    return NewsClassifier(
        classification_rules=classification_rules,
        sectors_rules=sectors_rules,
        keywords_rules=keywords_rules,
    )


# --------------------------------------------------------------------------- #
# 一级分类
# --------------------------------------------------------------------------- #


def test_classify_macro_policy_news() -> None:
    clf = _build_test_classifier()
    r = clf.classify(title="央行宣布降准0.5个百分点")
    assert r.primary_category == NewsCategory.MACRO_POLICY
    assert NewsCategory.MACRO_POLICY in r.all_categories


def test_classify_risk_event_higher_priority_than_company() -> None:
    """同时命中风险事件（priority=2）和公司公告（priority=3） → primary=风险事件。"""
    clf = _build_test_classifier()
    r = clf.classify(title="XX 公司财务造假被立案调查，紧急停牌")
    assert r.primary_category == NewsCategory.RISK_EVENT
    # multi_label=True，应同时记录到 all_categories
    assert NewsCategory.RISK_EVENT in r.all_categories
    assert NewsCategory.COMPANY_ANNOUNCEMENT in r.all_categories


def test_classify_no_match_returns_fallback() -> None:
    """无任何关键词命中 → fallback=市场行情。"""
    clf = _build_test_classifier()
    r = clf.classify(title="今天天气不错")
    assert r.primary_category == NewsCategory.MARKET
    assert r.all_categories == [NewsCategory.MARKET]


def test_classify_max_categories_capped() -> None:
    """multi_label 同时命中 3 个以上时，最多保留 max_categories=3 个（按 priority 优先）。"""
    clf = _build_test_classifier()
    r = clf.classify(
        title="央行降准的同时美联储加息，引发市场暴雷，多家公司业绩预增 涨停",
    )
    assert len(r.all_categories) <= 3


def test_classify_uses_title_and_summary() -> None:
    """summary 也参与匹配。"""
    clf = _build_test_classifier()
    r = clf.classify(title="一条无关标题", summary="正文里出现了 央行 关键词")
    assert r.primary_category == NewsCategory.MACRO_POLICY


# --------------------------------------------------------------------------- #
# 板块标签 + 标的关联
# --------------------------------------------------------------------------- #


def test_classify_extracts_sector_tags() -> None:
    clf = _build_test_classifier()
    r = clf.classify(title="国产 AI算力 突破，寒武纪股价大涨")
    assert "AI算力" in r.tags
    assert any(s.name == "AI算力" for s in r.related_sectors)


def test_classify_multiple_sectors() -> None:
    clf = _build_test_classifier()
    r = clf.classify(title="AI算力需求带动半导体行业景气度上行")
    tag_names = [s.name for s in r.related_sectors]
    assert "AI算力" in tag_names
    assert "半导体" in tag_names


def test_classify_sector_weight_is_keyword_hit_count() -> None:
    """命中关键词越多，板块权重越高。

    注：M2-c v1 用简单子串匹配，重叠 keyword（"AI算力" + "算力"）会被分别计数；
    weight 仅用于板块排序，精确性不重要。"""
    clf = _build_test_classifier()
    r = clf.classify(title="AI算力 大模型 GPU 全面爆发")  # 命中 AI算力/算力/大模型/GPU 共 4 个
    ai = next(s for s in r.related_sectors if s.name == "AI算力")
    assert ai.weight >= 3  # 容忍子串重复计数


def test_classify_extracts_representative_symbols() -> None:
    """命中板块时，把代表个股一并放进 related_symbols。"""
    clf = _build_test_classifier()
    r = clf.classify(title="AI算力 板块大涨")
    symbol_names = [s.name for s in r.related_symbols]
    # 至少 AI算力 的代表股出现
    assert "寒武纪" in symbol_names or "中科曙光" in symbol_names


def test_classify_directly_mentioned_symbol_extracted() -> None:
    """新闻直接提到个股名 → 加入 related_symbols（即使板块没匹配）。"""
    clf = _build_test_classifier()
    # 比亚迪在 sectors 的 keywords 里，会触发"新能源车"板块匹配
    r = clf.classify(title="比亚迪发布全新车型")
    symbol_names = [s.name for s in r.related_symbols]
    assert "比亚迪" in symbol_names


def test_classify_no_sector_match_empty_symbols() -> None:
    clf = _build_test_classifier()
    r = clf.classify(title="央行降准")  # 宏观政策但无板块词
    assert r.related_sectors == []
    assert r.related_symbols == []


# --------------------------------------------------------------------------- #
# 黑名单
# --------------------------------------------------------------------------- #


def test_classify_blacklist_marks_but_still_returns() -> None:
    clf = _build_test_classifier()
    r = clf.classify(title="震惊！速看 央行重大消息")
    assert r.is_blacklisted is True
    # 仍然分类（让上层 service 决定怎么用）
    assert r.primary_category == NewsCategory.MACRO_POLICY


def test_classify_non_blacklist_clean() -> None:
    clf = _build_test_classifier()
    r = clf.classify(title="央行降准")
    assert r.is_blacklisted is False


# --------------------------------------------------------------------------- #
# 元信息
# --------------------------------------------------------------------------- #


def test_classify_returns_matched_keywords_for_debug() -> None:
    clf = _build_test_classifier()
    r = clf.classify(title="央行宣布降准0.5个百分点")
    # 至少应包含命中的两个 keyword
    assert "央行" in r.matched_keywords
    assert "降准" in r.matched_keywords


def test_classification_result_types() -> None:
    """类型检查 — 结构稳定。"""
    clf = _build_test_classifier()
    r = clf.classify(title="央行降准")
    assert isinstance(r, ClassificationResult)
    assert isinstance(r.primary_category, NewsCategory)
    assert isinstance(r.all_categories, list)
    assert isinstance(r.tags, list)
    assert all(isinstance(s, SectorMatch) for s in r.related_sectors)
    assert all(isinstance(s, SymbolMatch) for s in r.related_symbols)


# --------------------------------------------------------------------------- #
# from_config — 用真实 YAML 加载
# --------------------------------------------------------------------------- #


def test_classifier_from_config_loads_real_yaml() -> None:
    """从真实 config/ 下三个 YAML 加载，应能 instantiate。"""
    clf = NewsClassifier.from_config()
    # 跑一条真实标题做 smoke test
    r = clf.classify(title="央行：12月15日起下调金融机构存款准备金率0.5%")
    assert r.primary_category == NewsCategory.MACRO_POLICY
