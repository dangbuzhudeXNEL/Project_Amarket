"""ObservabilityService — 健康检查 / 指标 / 告警分发。

M0 阶段：仅 DB 探活；后续 milestone 增量加 source / ai / notifier 检查。
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy import text

from amarket.core.logging import get_logger
from amarket.db.session import get_engine
from amarket.services.config_service import get_app_config

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
    project_meta: dict[str, str]
    uptime_seconds: float
    timestamp: datetime


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


def _aggregate(checks: dict[str, CheckResult]) -> OverallStatus:
    """根据子 check 决定总体状态。"""
    statuses = [c.status for c in checks.values()]
    if any(s == "down" for s in statuses):
        return "unhealthy"
    if any(s == "degraded" for s in statuses):
        return "degraded"
    return "healthy"


def get_health_report() -> HealthReport:
    """生成完整健康报告。"""
    cfg = get_app_config()
    checks = {
        "db": _check_db(),
    }
    return HealthReport(
        status=_aggregate(checks),
        checks=checks,
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


__all__ = ["CheckResult", "HealthReport", "HealthStatus", "OverallStatus", "get_health_report"]
