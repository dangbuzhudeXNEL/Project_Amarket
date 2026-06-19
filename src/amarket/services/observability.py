"""ObservabilityService — 健康检查 / 指标 / 告警分发。

M0 阶段：DB 探活 + Notifier 配置状态。
后续 milestone 增量加 source / ai 检查。
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy import text

from amarket.adapters.notifiers.base import Notifier, NotifierHealth
from amarket.adapters.notifiers.lark_bot import LarkBotNotifier
from amarket.adapters.notifiers.wework_bot import WeWorkBotNotifier
from amarket.core.logging import get_logger
from amarket.db.session import get_engine
from amarket.services.config_service import get_app_config, get_env_settings

HealthStatus = Literal["ok", "degraded", "down"]
OverallStatus = Literal["healthy", "degraded", "unhealthy"]

log = get_logger(__name__)

_START_TIME: float = time.time()


class CheckResult(BaseModel):
    status: HealthStatus
    latency_ms: float | None = None
    detail: str | None = None
    extra: dict[str, object] = Field(default_factory=dict)


class HealthReport(BaseModel):
    status: OverallStatus
    checks: dict[str, CheckResult]
    notifiers: dict[str, NotifierHealth] = Field(default_factory=dict)
    project_meta: dict[str, str]
    uptime_seconds: float
    timestamp: datetime


# --------------------------------------------------------------------------- #
# Sub-checks
# --------------------------------------------------------------------------- #


def _check_db() -> CheckResult:
    """探活 DB：执行 SELECT 1。"""
    started = time.perf_counter()
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - started) * 1000
        return CheckResult(status="ok", latency_ms=round(latency_ms, 2))
    except Exception as exc:  # pragma: no cover - DB 故障路径
        log.error("healthcheck.db_failed", error=str(exc))
        return CheckResult(status="down", detail=str(exc)[:200])


def _check_notifiers() -> dict[str, NotifierHealth]:
    """探活所有注册的 notifier — 仅检查配置 + 上次发送状态，不主动 ping。"""
    return {n.code: n.health_check() for _, n in iter_notifiers()}


# --------------------------------------------------------------------------- #
# Notifier 注册表（M0 阶段：根据 env 自动注册企微/飞书）
# --------------------------------------------------------------------------- #


def iter_notifiers() -> Iterator[tuple[str, Notifier]]:
    """枚举所有"已配置"的 notifier。返回 (channel_label, notifier) 元组。

    M0 阶段从 EnvSettings 读取 webhook URL；M4+ 起改成从 ConfigService 拿。
    """
    env = get_env_settings()
    if env.wework_bot_webhook_url:
        yield "wework", WeWorkBotNotifier(env.wework_bot_webhook_url, bot_label="wework")
    if env.wework_alert_bot_webhook_url:
        yield (
            "wework_alert",
            WeWorkBotNotifier(env.wework_alert_bot_webhook_url, bot_label="wework_alert"),
        )
    if env.lark_bot_webhook_url:
        yield "lark", LarkBotNotifier(env.lark_bot_webhook_url, bot_label="lark")


def get_notifier(channel: str) -> Notifier | None:
    """按 channel label 拿一个 notifier，没配置返回 None。"""
    for label, n in iter_notifiers():
        if label == channel:
            return n
    return None


def list_notifier_channels() -> list[str]:
    """已知 channel label 列表（包括未配置的，便于 UI 展示）。"""
    return ["wework", "wework_alert", "lark"]


# --------------------------------------------------------------------------- #
# Aggregate
# --------------------------------------------------------------------------- #


def _aggregate(
    checks: dict[str, CheckResult],
    notifiers: dict[str, NotifierHealth] | None = None,
) -> OverallStatus:
    """根据子 check 决定总体状态。

    - 任一 `checks` 项 down → unhealthy
    - 任一 `checks` 项 degraded → degraded
    - notifier down → degraded（不致命，但要标注）
    - notifier disabled → 不影响整体（"未配置"是预期状态）
    """
    statuses = [c.status for c in checks.values()]
    if any(s == "down" for s in statuses):
        return "unhealthy"

    notifier_down = any(h.status == "down" for h in (notifiers or {}).values())
    has_degraded = any(s == "degraded" for s in statuses)
    if has_degraded or notifier_down:
        return "degraded"
    return "healthy"


def get_health_report() -> HealthReport:
    """生成完整健康报告。"""
    cfg = get_app_config()
    checks = {
        "db": _check_db(),
    }
    notifiers = _check_notifiers()
    return HealthReport(
        status=_aggregate(checks, notifiers),
        checks=checks,
        notifiers=notifiers,
        project_meta={
            "name": cfg.app.name,
            "env": cfg.app.env,
            "spec_version": cfg.project_meta.spec_version,
            "current_phase": cfg.project_meta.current_phase,
            "current_milestone": cfg.project_meta.current_milestone,
        },
        uptime_seconds=round(time.time() - _START_TIME, 2),
        timestamp=datetime.now(UTC),
    )


__all__ = [
    "CheckResult",
    "HealthReport",
    "HealthStatus",
    "OverallStatus",
    "get_health_report",
    "get_notifier",
    "iter_notifiers",
    "list_notifier_channels",
]
