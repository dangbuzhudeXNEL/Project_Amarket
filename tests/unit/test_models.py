"""Domain models smoke test。"""

from __future__ import annotations

from sqlmodel import Session, select

from amarket.domain.enums import UserRole
from amarket.domain.models import User


def test_user_can_be_persisted(session: Session) -> None:
    user = User(name="alice", role=UserRole.ANALYST)
    session.add(user)
    session.commit()
    session.refresh(user)

    assert user.id is not None
    assert user.role == UserRole.ANALYST
    assert user.timezone == "Asia/Shanghai"


def test_user_role_defaults_to_admin(session: Session) -> None:
    user = User(name="bob")
    session.add(user)
    session.commit()

    fetched = session.exec(select(User).where(User.name == "bob")).one()
    assert fetched.role == UserRole.ADMIN


def test_user_role_enum_string_values() -> None:
    assert UserRole.ADMIN.value == "admin"
    assert UserRole.ANALYST.value == "analyst"
    assert UserRole.TRADER.value == "trader"
    assert UserRole.GUEST.value == "guest"
