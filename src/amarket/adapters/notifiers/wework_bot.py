"""企业微信群机器人 Notifier。

API: https://developer.work.weixin.qq.com/document/path/91770
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


class WeWorkBotNotifier:
    """企微群机器人 — 支持 text / markdown / card（M5 实现）。"""

    code: str = "wework"

    def __init__(
        self,
        webhook_url: str,
        *,
        timeout: float = 5.0,
        enabled: bool = True,
        bot_label: str = "wework",
    ) -> None:
        self._webhook_url = webhook_url.strip()
        self._timeout = timeout
        self.enabled = enabled and bool(self._webhook_url)
        self.code = bot_label  # 允许多机器人区分（e.g. 'wework_alert'）
        self._last_check_at: datetime | None = None
        self._last_error: str | None = None

    # --------------------------- 公共接口 --------------------------- #

    async def send_text(self, text: str) -> NotificationResult:
        return await self._post(
            {
                "msgtype": "text",
                "text": {"content": text + COMPLIANCE_FOOTER},
            }
        )

    async def send_markdown(self, markdown: str) -> NotificationResult:
        return await self._post(
            {
                "msgtype": "markdown",
                "markdown": {"content": markdown + COMPLIANCE_FOOTER},
            }
        )

    async def send_card(self, card: CardSpec) -> NotificationResult:
        # 企微 news 卡片（最小可用版本）
        articles = [
            {
                "title": card.title,
                "description": card.summary,
                "url": card.url or "",
                "picurl": card.extras.get("picurl", "") if isinstance(card.extras, dict) else "",
            }
        ]
        return await self._post(
            {
                "msgtype": "news",
                "news": {"articles": articles},
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
                "wework.send_failed", error=self._last_error, msgtype=payload.get("msgtype")
            )
            return NotificationResult(ok=False, channel=self.code, error=self._last_error)

        # 企微返回 {"errcode": 0, "errmsg": "ok"}
        errcode = data.get("errcode", -1)
        self._last_check_at = datetime.now(UTC)
        if errcode == 0:
            self._last_error = None
            return NotificationResult(ok=True, channel=self.code, response=data)

        self._last_error = f"errcode={errcode} errmsg={data.get('errmsg')}"
        log.warning("wework.send_rejected", **data)
        return NotificationResult(
            ok=False, channel=self.code, error=self._last_error, response=data
        )


__all__ = ["WeWorkBotNotifier"]
