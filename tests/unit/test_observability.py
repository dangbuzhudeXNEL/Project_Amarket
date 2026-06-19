"""ObservabilityService / HealthReport 单元测试。"""

from __future__ import annotations

from sqlalchemy.engine import Engine

from amarket.services.observability import (
    HealthReport,
    _aggregate,
    _check_db,
    get_health_report,
)


def test_check_db_ok_with_in_memory_engine(patched_engine: Engine) -> None:
    result = _check_db()
    assert result.status == "ok"
    assert result.latency_ms is not None
    assert result.latency_ms >= 0


def test_aggregate_all_ok_is_healthy() -> None:
    from amarket.services.observability import CheckResult

    assert _aggregate({"a": CheckResult(status="ok"), "b": CheckResult(status="ok")}) == "healthy"


def test_aggregate_degraded() -> None:
    from amarket.services.observability import CheckResult

    assert (
        _aggregate({"a": CheckResult(status="ok"), "b": CheckResult(status="degraded")})
        == "degraded"
    )


def test_aggregate_any_down_is_unhealthy() -> None:
    from amarket.services.observability import CheckResult

    assert (
        _aggregate(
            {
                "a": CheckResult(status="ok"),
                "b": CheckResult(status="degraded"),
                "c": CheckResult(status="down"),
            }
        )
        == "unhealthy"
    )


def test_get_health_report_with_in_memory_db(patched_engine: Engine) -> None:
    report = get_health_report()
    assert isinstance(report, HealthReport)
    assert report.status == "healthy"
    assert "db" in report.checks
    assert report.checks["db"].status == "ok"
    assert report.uptime_seconds >= 0
    assert report.project_meta["spec_version"] == "v3.0"
