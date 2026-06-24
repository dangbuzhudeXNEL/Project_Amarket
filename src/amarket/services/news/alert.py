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
from pathlib import Path

from sqlmodel import Session

from amarket.core.logging import get_logger
from amarket.domain.enums import AlertLevel, NewsCategory
from amarket.domain.models import Alert, NewsAnalysis, NewsItem
from amarket.repositories.alert_repo import AlertRepo
from amarket.services.config_service import CONFIG_DIR, _load_yaml

log = get_logger(__name__)

_HIGH_IMPACT_CATEGORIES = {NewsCategory.RISK_EVENT, NewsCategory.MACRO_POLICY}

# Level priority — 数字越小越紧急（P0 = 0 最高）
_LEVEL_PRIORITY: dict[AlertLevel, int] = {
    AlertLevel.P0: 0,
    AlertLevel.P1: 1,
    AlertLevel.P2: 2,
    AlertLevel.P3: 3,
}


def _is_higher_priority(new_level: AlertLevel, old_level: AlertLevel) -> bool:
    """新 level 优先级是否高于旧 level（P0 高于 P1 高于 P2）。"""
    return _LEVEL_PRIORITY[new_level] < _LEVEL_PRIORITY[old_level]


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

    def __init__(
        self,
        session: Session,
        *,
        blacklist_keywords: Sequence[str] | None = None,
    ) -> None:
        """构造。

        Args:
            session: SQLModel session
            blacklist_keywords: 黑名单关键词列表。命中关键词的新闻不会生成 alert
                （修 reviewer P1-3 — 避免广告/导购模板新闻误触发告警）。默认空 = 不过滤。
                建议从 `keywords.yml` 的 `blacklist` 段加载。
        """
        self._session = session
        self._repo = AlertRepo(session)
        self._blacklist: list[str] = list(blacklist_keywords or [])

    @classmethod
    def from_config(
        cls,
        session: Session,
        *,
        config_dir: Path | None = None,
    ) -> AlertService:
        """从默认 config/ 加载黑名单关键词。"""
        cdir = config_dir or CONFIG_DIR
        keywords = _load_yaml(cdir / "keywords.yml")
        return cls(session, blacklist_keywords=keywords.get("blacklist", []))

    # ---------------- 公共入口 ---------------- #

    def evaluate_and_persist(self, analysis: NewsAnalysis) -> Alert | None:
        """决策 + 持久化。返回新建/已有 Alert；P3 返回 None。

        升档逻辑（修 reviewer P1-2）：如果同 news_id 已存在更低优先级的 pending
        alert（如旧 P2，新评估为 P0/P1），把旧的标 status='superseded'，防止
        M4 pusher 看到多条 pending 双推。

        黑名单（修 reviewer P1-3）：关联 NewsItem 命中 keywords.yml 的 blacklist
        关键词的新闻不生成 alert（保留 news_analysis 行可审计）。
        """
        level = evaluate_alert_level(analysis)
        if level == AlertLevel.P3:
            return None

        # 黑名单：命中则不生成 alert（news_analysis 行仍保留可审计）
        if self._is_news_blacklisted(analysis.news_id):
            log.info(
                "alert.blacklisted_skip",
                news_id=analysis.news_id,
                level=level.value,
            )
            return None

        # 幂等：同一 news_id + level 不重复
        existing = self._repo.get_for_news_and_level(news_id=analysis.news_id, level=level)
        if existing is not None:
            return existing

        # 升档：把同 news_id 的 pending + 更低优先级 alert 标 superseded
        self._supersede_lower_priority(analysis.news_id, new_level=level)

        alert = Alert(
            news_id=analysis.news_id,
            level=level,
            trigger_reason=_build_trigger_reason(analysis, level),
            analysis_id=analysis.id,
            status="pending",
        )
        return self._repo.add(alert)

    def _is_news_blacklisted(self, news_id: int) -> bool:
        """检查关联的 NewsItem 标题/摘要是否命中黑名单关键词。"""
        if not self._blacklist:
            return False
        news = self._session.get(NewsItem, news_id)
        if news is None:
            return False
        text = news.title + (news.summary or "")
        return any(kw in text for kw in self._blacklist)

    def _supersede_lower_priority(self, news_id: int, *, new_level: AlertLevel) -> int:
        """把同 news_id 中 priority 低于 new_level 的 pending alert 标 superseded。

        返回被 superseded 的行数。
        """
        existing = self._repo.list_for_news(news_id=news_id, limit=20)
        count = 0
        for old in existing:
            if old.status != "pending":
                continue
            if _is_higher_priority(new_level, old.level):
                old.status = "superseded"
                self._session.add(old)
                count += 1
        if count:
            self._session.commit()
            log.info(
                "alert.superseded",
                news_id=news_id,
                new_level=new_level.value,
                superseded_count=count,
            )
        return count

    def process_analyses(self, analyses: Sequence[NewsAnalysis]) -> AlertBatchResult:
        """批处理 — 对一批 NewsAnalysis 跑决策 + 写库。"""
        result = AlertBatchResult(total=len(analyses))
        for ana in analyses:
            level = evaluate_alert_level(ana)
            if level == AlertLevel.P3:
                result.p3_skipped += 1
                continue
            # NewsAnalysis.news_id 是 NOT NULL（schema 约束）— 不需要 None 防御

            # 黑名单：命中则不生成 alert（修 P1-3）
            if self._is_news_blacklisted(ana.news_id):
                result.p3_skipped += 1  # 视为 P3 不入库
                continue

            existing = self._repo.get_for_news_and_level(news_id=ana.news_id, level=level)
            if existing is not None:
                result.already_existed += 1
                continue

            # 升档时 supersede 旧的低优先级 alert（修 P1-2）
            self._supersede_lower_priority(ana.news_id, new_level=level)

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
