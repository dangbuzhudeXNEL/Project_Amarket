"""`/metrics` endpoint — Prometheus 格式（Spec v3 §13.3）。

M0 阶段：仅暴露默认进程指标 + 自定义 uptime gauge。
后续 milestone 增量加 news / push / ai / scheduler 指标。
"""

from __future__ import annotations

import time

from fastapi import APIRouter, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    Gauge,
    Info,
    generate_latest,
)

from amarket.services.config_service import get_app_config

router = APIRouter(tags=["system"])

# 自定义指标
_APP_UPTIME_SECONDS = Gauge(
    "amarket_uptime_seconds",
    "Application uptime in seconds.",
)
_APP_INFO = Info(
    "amarket_app",
    "Application metadata.",
)
_START_TIME = time.time()


def _refresh_static_metrics() -> None:
    """每次 scrape 时刷新静态指标。"""
    cfg = get_app_config()
    _APP_UPTIME_SECONDS.set(time.time() - _START_TIME)
    _APP_INFO.info(
        {
            "name": cfg.app.name,
            "env": cfg.app.env,
            "spec_version": cfg.project_meta.spec_version,
            "phase": cfg.project_meta.current_phase,
            "milestone": cfg.project_meta.current_milestone,
        }
    )


@router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    """Prometheus scrape endpoint."""
    _refresh_static_metrics()
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )


__all__ = ["router"]
