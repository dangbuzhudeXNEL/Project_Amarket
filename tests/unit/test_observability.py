"""ObservabilityService / HealthReport 单元测试。"""

from __future__ import annotations

import pytest
from sqlalchemy.engine import Engine

from amarket.services.observability import (
    CheckResult,
    HealthReport,
    _aggregate,
    _check_db,
    _check_notifiers,
    get_health_report,
    get_notifier,
    iter_notifiers,
    list_notifier_channels,
)


def test_check_db_ok_with_in_memory_engine(patched_engine: Engine) -> None:
    result = _check_db()
    assert result.status == "ok"
    assert result.latency_ms is not None
    assert result.latency_ms >= 0


def test_aggregate_all_ok_is_healthy() -> None:
    assert _aggregate({"a": CheckResult(status="ok"), "b": CheckResult(status="ok")}) == "healthy"


def test_aggregate_degraded() -> None:
    assert (
        _aggregate({"a": CheckResult(status="ok"), "b": CheckResult(status="degraded")})
        == "degraded"
    )


def test_aggregate_any_down_is_unhealthy() -> None:
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
    # notifiers 字段存在（可能为空 dict 如果未配置）
    assert isinstance(report.notifiers, dict)


def test_list_notifier_channels_includes_wework_and_lark() -> None:
    channels = list_notifier_channels()
    assert "wework" in channels
    assert "wework_alert" in channels
    assert "lark" in channels


def test_iter_notifiers_empty_when_no_env(clean_env: pytest.MonkeyPatch) -> None:
    notifiers = list(iter_notifiers())
    assert notifiers == []


def test_iter_notifiers_picks_up_wework(clean_env: pytest.MonkeyPatch) -> None:
    clean_env.setenv("WEWORK_BOT_WEBHOOK_URL", "https://qyapi.weixin.qq.com/x?key=abc")
    from amarket.services.config_service import reload_config

    reload_config()

    labels = [label for label, _ in iter_notifiers()]
    assert "wework" in labels
    assert "wework_alert" not in labels  # 没配


def test_get_notifier_returns_none_when_not_configured(clean_env: pytest.MonkeyPatch) -> None:
    assert get_notifier("wework") is None
    assert get_notifier("lark") is None


def test_get_notifier_returns_instance_when_configured(clean_env: pytest.MonkeyPatch) -> None:
    clean_env.setenv("LARK_BOT_WEBHOOK_URL", "https://open.feishu.cn/hook/x")
    from amarket.services.config_service import reload_config

    reload_config()

    n = get_notifier("lark")
    assert n is not None
    assert n.code == "lark"


def test_check_notifiers_returns_health_for_each(clean_env: pytest.MonkeyPatch) -> None:
    clean_env.setenv("WEWORK_BOT_WEBHOOK_URL", "https://qyapi.weixin.qq.com/x?key=abc")
    clean_env.setenv("LARK_BOT_WEBHOOK_URL", "https://open.feishu.cn/hook/y")
    from amarket.services.config_service import reload_config

    reload_config()

    result = _check_notifiers()
    assert set(result.keys()) == {"wework", "lark"}
    assert all(h.status in {"ok", "degraded", "down", "disabled"} for h in result.values())


def test_health_report_degraded_when_notifier_down(
    patched_engine: Engine,
    clean_env: pytest.MonkeyPatch,
) -> None:
    """模拟：notifier 配置好但发送过且失败 → status=down → overall degraded。"""
    from amarket.adapters.notifiers.base import NotifierHealth
    from amarket.services.observability import _aggregate as agg

    checks = {"db": CheckResult(status="ok")}
    notifiers = {
        "wework": NotifierHealth(
            code="wework", enabled=True, configured=True, status="down", last_error="boom"
        ),
    }
    assert agg(checks, notifiers) == "degraded"


def test_health_report_healthy_when_notifier_disabled() -> None:
    """notifier disabled（未配置）不应让整体降级。"""
    from amarket.adapters.notifiers.base import NotifierHealth
    from amarket.services.observability import _aggregate as agg

    checks = {"db": CheckResult(status="ok")}
    notifiers = {
        "wework": NotifierHealth(code="wework", enabled=False, configured=False, status="disabled"),
    }
    assert agg(checks, notifiers) == "healthy"
