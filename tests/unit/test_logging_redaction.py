"""structlog redaction processor 单元测试。"""

from __future__ import annotations

from amarket.core.logging import _redact_secrets  # type: ignore[attr-defined]


def test_redacts_api_key_field() -> None:
    result = _redact_secrets(None, "info", {"event": "x", "api_key": "sk-secret12345abc"})
    assert result["api_key"].startswith("sk-s")
    assert result["api_key"].endswith("5abc")
    assert "secret12345" not in result["api_key"]


def test_redacts_token_field() -> None:
    result = _redact_secrets(None, "info", {"token": "ghp_abcdefghij0123456789"})
    assert "abcdefg" not in result["token"]


def test_redacts_webhook_url_query_string() -> None:
    url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=abcdef-12345-secret"
    result = _redact_secrets(None, "info", {"webhook_url": url})
    # 字段名命中 → 整段脱敏
    assert "abcdef-12345-secret" not in result["webhook_url"]


def test_redacts_inline_qyapi_url_in_normal_field() -> None:
    url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=abc-secret"
    result = _redact_secrets(None, "info", {"target": url})
    # qyapi 域名命中 → ?key= 替换
    assert "?key=***" in result["target"]
    assert "abc-secret" not in result["target"]


def test_short_string_fully_masked() -> None:
    result = _redact_secrets(None, "info", {"password": "short"})
    assert result["password"] == "***"


def test_non_secret_field_untouched() -> None:
    payload = {"event": "x", "module": "news", "count": 42}
    result = _redact_secrets(None, "info", dict(payload))
    assert result == payload
