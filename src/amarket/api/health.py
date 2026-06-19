"""`/healthz` endpoint — Spec v3 §13.4。"""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from amarket.services.observability import HealthReport, get_health_report

router = APIRouter(tags=["system"])


@router.get(
    "/healthz",
    response_model=HealthReport,
    responses={
        200: {"description": "healthy or degraded"},
        503: {"description": "unhealthy"},
    },
)
async def healthz(response: Response) -> HealthReport:
    """健康检查。

    - `status == "healthy"` → HTTP 200
    - `status == "degraded"` → HTTP 200（功能可用但部分降级）
    - `status == "unhealthy"` → HTTP 503（外部 watchdog 应触发重启）
    """
    report = get_health_report()
    if report.status == "unhealthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return report


__all__ = ["router"]
