"""FastAPI 应用入口。

启动方式：
- 开发：`uv run uvicorn amarket.main:app --reload --port 8080`
- 通过 start.bat / start.sh：FastAPI + Streamlit 同时启动
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from amarket import __version__
from amarket.api import health, metrics
from amarket.core.logging import configure_logging, get_logger
from amarket.services.config_service import get_app_config, get_env_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
    """应用启动 / 关闭钩子。

    - 启动：初始化日志、记录 banner、（M4 起）启动 APScheduler
    - 关闭：（M4 起）停止 APScheduler
    """
    env = get_env_settings()
    configure_logging(log_level=env.log_level, log_format=env.log_format)

    log = get_logger("amarket.main")
    cfg = get_app_config()
    log.info(
        "app.starting",
        version=__version__,
        env=cfg.app.env,
        spec=cfg.project_meta.spec_version,
        phase=cfg.project_meta.current_phase,
        milestone=cfg.project_meta.current_milestone,
    )

    yield

    log.info("app.stopping")


def create_app() -> FastAPI:
    """创建 FastAPI app（工厂模式，便于测试覆盖）。"""
    cfg = get_app_config()
    app = FastAPI(
        title="Project_Amarket",
        description=(
            "A 股新闻分析 + 行情看板平台 — 小组联合项目（永不实盘）。\n\n"
            f"Spec: {cfg.project_meta.spec_version} / "
            f"Phase: {cfg.project_meta.current_phase} / "
            f"Milestone: {cfg.project_meta.current_milestone}"
        ),
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS
    if cfg.api.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cfg.api.cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["*"],
        )

    # System routers
    app.include_router(health.router)
    app.include_router(metrics.router)

    return app


# Uvicorn 入口（amarket.main:app）
app: FastAPI = create_app()


__all__ = ["app", "create_app", "lifespan"]
