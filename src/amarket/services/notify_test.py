"""同步包装：给 Streamlit / CLI 发送测试通知用。

设计意图：
- Streamlit / CLI 是同步上下文，但 Notifier 接口是 async
- 这里提供 `send_test_message_sync()` 一个公共入口
- 真实业务推送（M4+）请直接走 async NewsPusher 服务
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from amarket.adapters.notifiers.base import NotificationResult
from amarket.core.logging import get_logger
from amarket.services.observability import get_notifier

log = get_logger(__name__)


def _build_test_message(channel: str) -> str:
    ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    return (
        f"# 🧪 Project_Amarket 通知测试\n\n"
        f"- channel: `{channel}`\n"
        f"- 触发时间: {ts}\n"
        f"- 阶段: Phase 1 M0\n\n"
        "如果你看到这条消息，说明 webhook 配置成功 ✅"
    )


def send_test_message_sync(channel: str) -> NotificationResult:
    """同步发送一条测试消息到指定 channel。

    Args:
        channel: 'wework' | 'wework_alert' | 'lark'

    Returns:
        NotificationResult — 即使发送失败也返回（不抛异常），便于 UI / CLI 展示
    """
    notifier = get_notifier(channel)
    if notifier is None:
        return NotificationResult(
            ok=False,
            channel=channel,
            error=f"channel '{channel}' not configured (check .env)",
        )

    message = _build_test_message(channel)
    log.info("notify_test.sending", channel=channel)
    try:
        return asyncio.run(notifier.send_markdown(message))
    except RuntimeError as exc:
        # 已有 event loop（不太可能在 streamlit / cli 出现，但保险起见）
        log.warning("notify_test.event_loop_collision", error=str(exc))
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(notifier.send_markdown(message))
        finally:
            loop.close()


__all__ = ["send_test_message_sync"]
