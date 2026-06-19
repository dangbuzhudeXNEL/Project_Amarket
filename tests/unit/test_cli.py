"""CLI smoke tests."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from sqlalchemy.engine import Engine
from typer.testing import CliRunner

from amarket.cli import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_version_command(runner: CliRunner) -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "amarket 0.1.0" in result.stdout
    assert "Phase1" in result.stdout
    assert "M0" in result.stdout


def test_healthcheck_inprocess_returns_zero(
    runner: CliRunner,
    patched_engine: Engine,
    clean_env: pytest.MonkeyPatch,
) -> None:
    result = runner.invoke(app, ["healthcheck"])
    assert result.exit_code == 0
    assert "status: healthy" in result.stdout
    assert "db" in result.stdout


def test_healthcheck_json(
    runner: CliRunner,
    patched_engine: Engine,
    clean_env: pytest.MonkeyPatch,
) -> None:
    result = runner.invoke(app, ["healthcheck", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "healthy"
    assert "db" in payload["checks"]


def test_db_status(
    runner: CliRunner,
    patched_engine: Engine,
    clean_env: pytest.MonkeyPatch,
) -> None:
    result = runner.invoke(app, ["db", "status"])
    assert result.exit_code == 0
    assert "db: ok" in result.stdout


def test_notify_status_all_unconfigured(
    runner: CliRunner,
    clean_env: pytest.MonkeyPatch,
) -> None:
    result = runner.invoke(app, ["notify", "status"])
    assert result.exit_code == 0
    assert "wework: not configured" in result.stdout
    assert "lark: not configured" in result.stdout


def test_notify_test_unknown_channel(
    runner: CliRunner,
    clean_env: pytest.MonkeyPatch,
) -> None:
    result = runner.invoke(app, ["notify", "test", "wework"])
    assert result.exit_code == 1  # 未配置 → 失败
    assert "not configured" in result.stdout


@respx.mock
def test_notify_test_wework_success(
    runner: CliRunner,
    clean_env: pytest.MonkeyPatch,
) -> None:
    url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=cli-test"
    clean_env.setenv("WEWORK_BOT_WEBHOOK_URL", url)
    from amarket.services.config_service import reload_config

    reload_config()
    respx.post(url).mock(return_value=httpx.Response(200, json={"errcode": 0, "errmsg": "ok"}))

    result = runner.invoke(app, ["notify", "test", "wework"])
    assert result.exit_code == 0
    assert "wework: ok" in result.stdout
