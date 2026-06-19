"""Project_Amarket — 测试公共 fixtures。

约定：
- 所有单元测试 in-memory SQLite，跑完即销毁
- 配置 / env 在 fixture 中重置，避免相互污染
- httpx mock 用 respx；时间穿越用 freezegun
"""

from __future__ import annotations

import os
from collections.abc import Generator, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from amarket import db as db_module
from amarket.core.logging import configure_logging
from amarket.services import config_service

# --------------------------------------------------------------------------- #
# Logging — 测试统一用 console 格式 + INFO，避免单测被 JSON 刷屏
# --------------------------------------------------------------------------- #


@pytest.fixture(autouse=True, scope="session")
def _configure_logging_for_tests() -> None:
    configure_logging(log_level="WARNING", log_format="console")


# --------------------------------------------------------------------------- #
# Config / env 隔离
# --------------------------------------------------------------------------- #


@pytest.fixture(autouse=True)
def _reset_config_caches() -> Iterator[None]:
    """每个测试前后清空 config / env 缓存，避免 monkeypatch 残留。"""
    config_service.reload_config()
    yield
    config_service.reload_config()


@pytest.fixture
def project_root() -> Path:
    return config_service.PROJECT_ROOT


# --------------------------------------------------------------------------- #
# DB — in-memory SQLite，每个测试独立
# --------------------------------------------------------------------------- #


@pytest.fixture
def in_memory_engine() -> Generator[Engine, None, None]:
    """每个测试一个全新的 in-memory SQLite engine + 完整 schema。"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(in_memory_engine: Engine) -> Iterator[Session]:
    with Session(in_memory_engine) as s:
        yield s


@pytest.fixture
def patched_engine(
    monkeypatch: pytest.MonkeyPatch,
    in_memory_engine: Engine,
) -> Engine:
    """把 amarket.db.session 模块的全局 engine 替换为 in_memory_engine。"""
    from amarket.db import session as session_module

    monkeypatch.setattr(session_module, "_engine", in_memory_engine)
    return in_memory_engine


# --------------------------------------------------------------------------- #
# FastAPI TestClient
# --------------------------------------------------------------------------- #


@pytest.fixture
def api_client(patched_engine: Engine) -> Iterator[TestClient]:
    """TestClient，DB 走 in-memory engine。"""
    # 必须延迟 import 以拿到刚 monkeypatch 过的 engine
    from amarket.main import create_app

    app = create_app()
    with TestClient(app) as client:
        yield client


# --------------------------------------------------------------------------- #
# 环境变量帮助
# --------------------------------------------------------------------------- #


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """清空与 Project_Amarket 相关的环境变量，避免开发者 .env 干扰。"""
    for var in [
        "WEWORK_BOT_WEBHOOK_URL",
        "WEWORK_ALERT_BOT_WEBHOOK_URL",
        "LARK_BOT_WEBHOOK_URL",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_BASE_URL",
        "DEEPSEEK_API_KEY",
    ]:
        monkeypatch.delenv(var, raising=False)
    return monkeypatch


# 保证 db_module 引用被 IDE 识别 + 防止未用 import 警告
_ = db_module
_ = os
