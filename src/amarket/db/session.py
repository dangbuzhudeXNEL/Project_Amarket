"""DB session 工厂 + 引擎管理。

约定：
- 应用代码通过依赖注入获取 session（不直接拿全局 engine）
- 测试用 `tests/conftest.py` 里的 in-memory SQLite fixture 覆盖
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from amarket.services.config_service import get_app_config

_engine: Engine | None = None


def get_engine(database_url: str | None = None) -> Engine:
    """获取全局 SQLAlchemy engine（lazy init）。

    Args:
        database_url: 显式指定时覆盖配置（测试 fixture 用）
    """
    global _engine
    if _engine is None:
        url = database_url or get_app_config().app.database_url
        connect_args: dict[str, Any] = {}
        if url.startswith("sqlite"):
            # SQLite + FastAPI 多线程
            connect_args["check_same_thread"] = False
        _engine = create_engine(
            url,
            echo=False,
            connect_args=connect_args,
        )
    return _engine


def reset_engine() -> None:
    """重置全局引擎（测试用，不要在生产代码调）。"""
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None


def init_db() -> None:
    """对测试 / dev 场景：直接根据 metadata 建表。

    生产请用 alembic migration。
    """
    SQLModel.metadata.create_all(get_engine())


@contextmanager
def session_scope() -> Iterator[Session]:
    """同步事务 context manager（CLI / 脚本场景常用）。"""
    session = Session(get_engine())
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Iterator[Session]:
    """FastAPI 依赖（每请求一个 session）。"""
    with Session(get_engine()) as session:
        yield session


__all__ = ["get_engine", "get_session", "init_db", "reset_engine", "session_scope"]
