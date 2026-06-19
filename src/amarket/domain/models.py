"""SQLModel ORM 表定义。

M0 阶段：仅 `users` 表（演示 alembic baseline 工作流）。
后续 Milestone 增量添加（M1 加 news_items / news_sources / source_health；M2 加 events 等）。

参考 Spec v3 §7.2 完整字段定义。
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel

from amarket.domain.enums import UserRole


class TimestampMixin(SQLModel):
    """所有业务表共享的时间戳字段（仅在子类用 `table=True` 时生效）。"""

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class User(TimestampMixin, table=True):
    """用户表（Spec v3 §7.2 - `users`）。

    MVP 单角色，但 schema 已经预留 role 与 timezone 字段，方便扩展多用户。
    """

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=64)
    role: UserRole = Field(default=UserRole.ADMIN)
    timezone: str = Field(default="Asia/Shanghai", max_length=64)


__all__ = ["TimestampMixin", "User"]
