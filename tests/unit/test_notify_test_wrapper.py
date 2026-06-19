"""notify_test sync wrapper 单元测试。"""

from __future__ import annotations

import httpx
import pytest
import respx

from amarket.services.notify_test import send_test_message_sync


def test_send_test_unknown_channel_returns_error(clean_env: pytest.MonkeyPatch) -> None:
    result = send_test_message_sync("wework")
    assert result.ok is False
    assert "not configured" in (result.error or "")


@respx.mock
def test_send_test_to_wework_success(clean_env: pytest.MonkeyPatch) -> None:
    url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=abc"
    clean_env.setenv("WEWORK_BOT_WEBHOOK_URL", url)
    from amarket.services.config_service import reload_config

    reload_config()
    respx.post(url).mock(return_value=httpx.Response(200, json={"errcode": 0, "errmsg": "ok"}))

    result = send_test_message_sync("wework")
    assert result.ok is True
    assert result.channel == "wework"


@respx.mock
def test_send_test_to_lark_handles_failure(clean_env: pytest.MonkeyPatch) -> None:
    url = "https://open.feishu.cn/open-apis/bot/v2/hook/bad"
    clean_env.setenv("LARK_BOT_WEBHOOK_URL", url)
    from amarket.services.config_service import reload_config

    reload_config()
    respx.post(url).mock(return_value=httpx.Response(200, json={"code": 19021, "msg": "bad"}))

    result = send_test_message_sync("lark")
    assert result.ok is False
    assert "code=19021" in (result.error or "")
