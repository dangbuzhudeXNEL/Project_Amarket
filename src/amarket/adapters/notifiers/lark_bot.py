"""飞书（Lark）群机器人 Notifier。

API: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/bot-v2/bot/events/im.message.receive_v1
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

from amarket.adapters.notifiers.base import (
    COMPLIANCE_FOOTER,
    CardSpec,
    NotificationResult,
    NotifierHealth,
)
from amarket.core.logging import get_logger

log = get_logger(__name__)


class LarkBotNotifier:
    """飞书群机器人 — 支持 text / markdown(post) / card（M5 实现完整 card）。"""

    code: str = "lark"

    def __init__(
        self,
        webhook_url: str,
        *,
        timeout: float = 5.0,
        enabled: bool = True,
        bot_label: str = "lark",
    ) -> None:
        self._webhook_url = webhook_url.strip()
        self._timeout = timeout
        self.enabled = enabled and bool(self._webhook_url)
        self.code = bot_label
        self._last_check_at: datetime | None = None
        self._last_error: str | None = None

    # --------------------------- 公共接口 --------------------------- #

    async def send_text(self, text: str) -> NotificationResult:
        return await self._post(
            {
                "msg_type": "text",
                "content": {"text": text + COMPLIANCE_FOOTER},
            }
        )

    async def send_markdown(self, markdown: str) -> NotificationResult:
        """飞书无单独 markdown 类型，用 post 富文本承载。"""
        return await self._post(
            {
                "msg_type": "post",
                "content": {
                    "post": {
                        "zh_cn": {
                            "title": "",
                            "content": [
                                [
                                    {
                                        "tag": "md",
                                        "text": markdown + COMPLIANCE_FOOTER,
                                    }
                                ]
                            ],
                        }
                    }
                },
            }
        )

    async def send_card(self, card: CardSpec) -> NotificationResult:
        """飞书 interactive 卡片（最小版本）。"""
        return await self._post(
            {
                "msg_type": "interactive",
                "card": {
                    "config": {"wide_screen_mode": True},
                    "header": {"title": {"tag": "plain_text", "content": card.title}},
                    "elements": [
                        {
                            "tag": "div",
                            "text": {"tag": "lark_md", "content": card.summary + COMPLIANCE_FOOTER},
                        },
                        *(
                            [
                                {
                                    "tag": "action",
                                    "actions": [
                                        {
                                            "tag": "button",
                                            "text": {"tag": "plain_text", "content": "查看原文"},
                                            "url": card.url,
                                            "type": "default",
                                        }
                                    ],
                                }
                            ]
                            if card.url
                            else []
                        ),
                    ],
                },
            }
        )

    def health_check(self) -> NotifierHealth:
        return NotifierHealth(
            code=self.code,
            enabled=self.enabled,
            configured=bool(self._webhook_url),
            last_check_at=self._last_check_at,
            last_error=self._last_error,
            status=("disabled" if not self.enabled else ("down" if self._last_error else "ok")),
        )

    # --------------------------- 内部 --------------------------- #

    async def _post(self, payload: dict[str, Any]) -> NotificationResult:
        if not self.enabled:
            return NotificationResult(
                ok=False, channel=self.code, error="notifier disabled or missing webhook"
            )

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(self._webhook_url, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            self._last_error = str(exc)[:200]
            self._last_check_at = datetime.now(UTC)
            log.warning(
                "lark.send_failed", error=self._last_error, msg_type=payload.get("msg_type")
            )
            return NotificationResult(ok=False, channel=self.code, error=self._last_error)

        # 飞书返回 {"code":0, "msg":"ok", "data":{}}
        code = data.get("code", -1)
        self._last_check_at = datetime.now(UTC)
        if code == 0:
            self._last_error = None
            return NotificationResult(ok=True, channel=self.code, response=data)

        self._last_error = f"code={code} msg={data.get('msg')}"
        log.warning("lark.send_rejected", **data)
        return NotificationResult(
            ok=False, channel=self.code, error=self._last_error, response=data
        )


__all__ = ["LarkBotNotifier"]
