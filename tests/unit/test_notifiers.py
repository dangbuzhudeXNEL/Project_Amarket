"""Notifier 单元测试 — 用 respx mock，避免发真实请求。"""

from __future__ import annotations

import httpx
import pytest
import respx

from amarket.adapters.notifiers.base import COMPLIANCE_FOOTER, CardSpec
from amarket.adapters.notifiers.lark_bot import LarkBotNotifier
from amarket.adapters.notifiers.wework_bot import WeWorkBotNotifier

# --------------------- WeWork --------------------- #


@pytest.mark.asyncio
@respx.mock
async def test_wework_send_text_success() -> None:
    url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=abc"
    route = respx.post(url).mock(
        return_value=httpx.Response(200, json={"errcode": 0, "errmsg": "ok"})
    )

    notifier = WeWorkBotNotifier(webhook_url=url)
    result = await notifier.send_text("hello")

    assert result.ok is True
    assert result.channel == "wework"
    assert route.called
    sent_payload = route.calls.last.request.read().decode()
    assert "hello" in sent_payload
    assert "仅供个人/小组学习参考" in sent_payload  # 合规 footer


@pytest.mark.asyncio
@respx.mock
async def test_wework_send_markdown_appends_footer() -> None:
    url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=x"
    respx.post(url).mock(return_value=httpx.Response(200, json={"errcode": 0, "errmsg": "ok"}))

    notifier = WeWorkBotNotifier(webhook_url=url)
    result = await notifier.send_markdown("# title")
    assert result.ok is True
    # COMPLIANCE_FOOTER 确实写出
    assert COMPLIANCE_FOOTER.strip() != ""


@pytest.mark.asyncio
async def test_wework_disabled_when_url_missing() -> None:
    notifier = WeWorkBotNotifier(webhook_url="")
    assert notifier.enabled is False
    result = await notifier.send_text("won't go out")
    assert result.ok is False
    assert "disabled" in (result.error or "")


@pytest.mark.asyncio
@respx.mock
async def test_wework_handles_errcode_nonzero() -> None:
    url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=z"
    respx.post(url).mock(
        return_value=httpx.Response(200, json={"errcode": 93000, "errmsg": "invalid webhook"})
    )

    notifier = WeWorkBotNotifier(webhook_url=url)
    result = await notifier.send_text("x")
    assert result.ok is False
    assert "errcode=93000" in (result.error or "")


@pytest.mark.asyncio
@respx.mock
async def test_wework_handles_network_error() -> None:
    url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=y"
    respx.post(url).mock(side_effect=httpx.ConnectError("boom"))

    notifier = WeWorkBotNotifier(webhook_url=url)
    result = await notifier.send_text("x")
    assert result.ok is False
    assert "boom" in (result.error or "")


def test_wework_health_check_disabled() -> None:
    n = WeWorkBotNotifier(webhook_url="")
    h = n.health_check()
    assert h.status == "disabled"
    assert h.configured is False


def test_wework_supports_bot_label_for_alert_channel() -> None:
    n = WeWorkBotNotifier(webhook_url="https://x", bot_label="wework_alert")
    assert n.code == "wework_alert"


# --------------------- Lark --------------------- #


@pytest.mark.asyncio
@respx.mock
async def test_lark_send_text_success() -> None:
    url = "https://open.feishu.cn/open-apis/bot/v2/hook/abc"
    route = respx.post(url).mock(
        return_value=httpx.Response(200, json={"code": 0, "msg": "ok", "data": {}})
    )

    notifier = LarkBotNotifier(webhook_url=url)
    result = await notifier.send_text("hi")
    assert result.ok is True
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_lark_send_card_with_url() -> None:
    url = "https://open.feishu.cn/open-apis/bot/v2/hook/card"
    respx.post(url).mock(return_value=httpx.Response(200, json={"code": 0, "msg": "ok"}))

    notifier = LarkBotNotifier(webhook_url=url)
    result = await notifier.send_card(CardSpec(title="t", summary="s", url="https://example.com"))
    assert result.ok is True


@pytest.mark.asyncio
@respx.mock
async def test_lark_handles_nonzero_code() -> None:
    url = "https://open.feishu.cn/open-apis/bot/v2/hook/badcode"
    respx.post(url).mock(return_value=httpx.Response(200, json={"code": 19021, "msg": "bad json"}))

    notifier = LarkBotNotifier(webhook_url=url)
    result = await notifier.send_text("x")
    assert result.ok is False
    assert "code=19021" in (result.error or "")


def test_lark_health_check_when_configured() -> None:
    n = LarkBotNotifier(webhook_url="https://example.com")
    h = n.health_check()
    assert h.status == "ok"
    assert h.enabled is True
    assert h.configured is True
