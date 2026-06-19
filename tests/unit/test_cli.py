"""CLI smoke tests."""

from __future__ import annotations

import json

import pytest
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
) -> None:
    result = runner.invoke(app, ["healthcheck"])
    assert result.exit_code == 0
    assert "status: healthy" in result.stdout
    assert "db" in result.stdout


def test_healthcheck_json(runner: CliRunner, patched_engine: Engine) -> None:
    result = runner.invoke(app, ["healthcheck", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "healthy"
    assert "db" in payload["checks"]


def test_db_status(runner: CliRunner, patched_engine: Engine) -> None:
    result = runner.invoke(app, ["db", "status"])
    assert result.exit_code == 0
    assert "db: ok" in result.stdout
