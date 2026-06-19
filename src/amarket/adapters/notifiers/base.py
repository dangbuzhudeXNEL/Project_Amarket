"""Notifier 接口（Spec v3 §6.2.4）。

约定：
- 所有 notifier 实现统一通过 `Notifier` Protocol
- 业务层（NewsPusher）只 import 这里，不 import 具体实现
- 实现不抛裸异常；用 `NotificationResult.ok=False + error` 反馈失败
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class NotificationResult(BaseModel):
    """单次发送结果。"""

    ok: bool
    channel: str
    sent_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    error: str | None = None
    response: dict[str, Any] | None = None  # 渠道原始返回（截短）


class NotifierHealth(BaseModel):
    """渠道健康状态（用于 `/healthz` 子检查）。"""

    code: str
    enabled: bool
    configured: bool  # webhook / token 是否配置
    last_check_at: datetime | None = None
    last_error: str | None = None
    status: Literal["ok", "degraded", "down", "disabled"] = "disabled"


class CardSpec(BaseModel):
    """卡片消息（暂未规范化跨渠道字段；M5 起填充）。"""

    title: str
    summary: str
    url: str | None = None
    extras: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class Notifier(Protocol):
    """所有推送渠道实现这个 Protocol。"""

    code: str
    enabled: bool

    async def send_text(self, text: str) -> NotificationResult: ...
    async def send_markdown(self, markdown: str) -> NotificationResult: ...
    async def send_card(self, card: CardSpec) -> NotificationResult: ...
    def health_check(self) -> NotifierHealth: ...


COMPLIANCE_FOOTER: str = "\n\n---\n📌 本信息仅供个人/小组学习参考，不构成任何投资建议。"
"""所有外发消息**必须**附加（Spec v3 §18.3 合规）。Notifier 实现统一注入。"""


__all__ = [
    "COMPLIANCE_FOOTER",
    "CardSpec",
    "NotificationResult",
    "Notifier",
    "NotifierHealth",
]
