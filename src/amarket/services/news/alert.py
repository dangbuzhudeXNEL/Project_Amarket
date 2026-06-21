"""AlertService — P0-P3 决策表 + alerts 表写入（Spec v3 §8.7, M2-f）。

决策表（Spec v3 §8.7 + PRD §3.1 决策 #4）：

| 等级 | 触发 | 推送行为 |
|------|------|----------|
| P0 | (RISK_EVENT 或 MACRO_POLICY) ∧ importance ≥ 5 ∧ urgency ≥ 5 | 即时全渠道强提醒（M4 实施）|
| P1 | importance ≥ 4 ∧ urgency ≥ 4，或命中订阅（M6+） | 即时单渠道推送 |
| P2 | importance ≥ 3 | 30 分钟汇总推送 |
| P3 | 其他 | 仅入库 news_analysis（不写 alerts 行）|

只对 P0/P1/P2 写 alerts 表。P3 仅留在 news_analysis（节省告警表存量）。
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from sqlmodel import Session

from amarket.core.logging import get_logger
from amarket.domain.enums import AlertLevel, NewsCategory
from amarket.domain.models import Alert, NewsAnalysis
from amarket.repositories.alert_repo import AlertRepo

log = get_logger(__name__)

_HIGH_IMPACT_CATEGORIES = {NewsCategory.RISK_EVENT, NewsCategory.MACRO_POLICY}


# --------------------------------------------------------------------------- #
# 纯函数 — 决策表（可单独测，不需要 DB）
# --------------------------------------------------------------------------- #


def evaluate_alert_level(analysis: NewsAnalysis) -> AlertLevel:
    """根据分析结果定 P0-P3 等级。

    暂不考虑订阅命中（M6 参数模块上线后接入）。
    """
    if (
        analysis.primary_category in _HIGH_IMPACT_CATEGORIES
        and analysis.importance_score >= 5
        and analysis.urgency_score >= 5
    ):
        return AlertLevel.P0
    if analysis.importance_score >= 4 and analysis.urgency_score >= 4:
        return AlertLevel.P1
    if analysis.importance_score >= 3:
        return AlertLevel.P2
    return AlertLevel.P3


def _build_trigger_reason(analysis: NewsAnalysis, level: AlertLevel) -> str:
    """给 trigger_reason 字段构造一个人类可读的简短说明。"""
    return (
        f"{level.value} | {analysis.primary_category.value} "
        f"| imp={analysis.importance_score} urg={analysis.urgency_score}"
    )


# --------------------------------------------------------------------------- #
# Batch 结果
# --------------------------------------------------------------------------- #


@dataclass
class AlertBatchResult:
    total: int = 0
    p0: int = 0
    p1: int = 0
    p2: int = 0
    p3_skipped: int = 0  # P3 不入 alerts 表
    already_existed: int = 0
    created_alert_ids: list[int] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Service
# --------------------------------------------------------------------------- #


class AlertService:
    """从 NewsAnalysis 生成 Alert。"""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = AlertRepo(session)

    # ---------------- 公共入口 ---------------- #

    def evaluate_and_persist(self, analysis: NewsAnalysis) -> Alert | None:
        """决策 + 持久化。返回新建/已有 Alert；P3 返回 None。"""
        level = evaluate_alert_level(analysis)
        if level == AlertLevel.P3:
            return None
        # NewsAnalysis.news_id 是 NOT NULL（schema 约束）— 不需要 None 防御

        # 幂等：同一 news_id + level 不重复
        existing = self._repo.get_for_news_and_level(news_id=analysis.news_id, level=level)
        if existing is not None:
            return existing

        alert = Alert(
            news_id=analysis.news_id,
            level=level,
            trigger_reason=_build_trigger_reason(analysis, level),
            analysis_id=analysis.id,
            status="pending",
        )
        return self._repo.add(alert)

    def process_analyses(self, analyses: Sequence[NewsAnalysis]) -> AlertBatchResult:
        """批处理 — 对一批 NewsAnalysis 跑决策 + 写库。"""
        result = AlertBatchResult(total=len(analyses))
        for ana in analyses:
            level = evaluate_alert_level(ana)
            if level == AlertLevel.P3:
                result.p3_skipped += 1
                continue
            # NewsAnalysis.news_id 是 NOT NULL（schema 约束）— 不需要 None 防御

            existing = self._repo.get_for_news_and_level(news_id=ana.news_id, level=level)
            if existing is not None:
                result.already_existed += 1
                continue

            alert = self._repo.add(
                Alert(
                    news_id=ana.news_id,
                    level=level,
                    trigger_reason=_build_trigger_reason(ana, level),
                    analysis_id=ana.id,
                    status="pending",
                )
            )
            if alert.id is not None:
                result.created_alert_ids.append(alert.id)
            if level == AlertLevel.P0:
                result.p0 += 1
            elif level == AlertLevel.P1:
                result.p1 += 1
            elif level == AlertLevel.P2:
                result.p2 += 1

        log.info(
            "alert.batch_done",
            total=result.total,
            p0=result.p0,
            p1=result.p1,
            p2=result.p2,
            p3_skipped=result.p3_skipped,
            already=result.already_existed,
        )
        return result


__all__ = [
    "AlertBatchResult",
    "AlertService",
    "evaluate_alert_level",
]
