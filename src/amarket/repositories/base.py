"""Repository 层公共基类。

Repository 模式：每个聚合根一个 Repo，封装 CRUD + 查询。
Service 层只接受 Session，自己创建 Repo（避免循环依赖）。
"""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlmodel import Session, SQLModel, select

T = TypeVar("T", bound=SQLModel)


class BaseRepo(Generic[T]):
    """SQLModel CRUD 基类，按需子类化。"""

    model: type[T]  # 子类必须设置

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, obj: T) -> T:
        """新增一条（自动 commit + refresh）。"""
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def add_many(self, objs: list[T]) -> list[T]:
        """批量新增（一次 commit）。"""
        if not objs:
            return []
        self.session.add_all(objs)
        self.session.commit()
        for o in objs:
            self.session.refresh(o)
        return objs

    def get(self, obj_id: int) -> T | None:
        return self.session.get(self.model, obj_id)

    def list_all(self, *, limit: int = 100, offset: int = 0) -> list[T]:
        return list(self.session.exec(select(self.model).offset(offset).limit(limit)))

    def count(self) -> int:
        from sqlalchemy import func

        result = self.session.exec(select(func.count()).select_from(self.model))
        return int(result.one())


__all__ = ["BaseRepo"]
