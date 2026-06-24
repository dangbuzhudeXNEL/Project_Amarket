"""AI Provider 单元测试（M2-g）— 全部 mock，不打真 subprocess / 真 API。"""

from __future__ import annotations

import asyncio
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from amarket.adapters.ai.base import (
    AIProvider,
    NewsAnalysisRequest,
    NewsAnalysisResult,
)
from amarket.adapters.ai.claude_agent_runner import ClaudeAgentRunner
from amarket.adapters.ai.factory import FallbackChainProvider, build_default_ai_provider
from amarket.adapters.ai.sdk_providers import AnthropicSDKProvider, DeepSeekSDKProvider
from amarket.core.exceptions import (
    AIAgentDegradedError,
    AIAgentTimeoutError,
    AIError,
)


def _sample_request() -> NewsAnalysisRequest:
    return NewsAnalysisRequest(
        news_id=42,
        title="央行降准 0.25%",
        summary="央行宣布降准 25 个基点。",
        source="eastmoney",
        published_at=datetime(2026, 6, 19, 8, 30, tzinfo=UTC),
    )


def _valid_agent_output(processed_by: str = "agent:news-classifier-realtime") -> dict[str, Any]:
    return {
        "primary_category": "宏观政策",
        "tags": ["货币政策", "降准"],
        "related_sectors": [{"name": "券商", "weight": 0.9}],
        "related_symbols": [{"code": "601318", "name": "中国平安"}],
        "sentiment": "强利多",
        "importance_score": 5,
        "urgency_score": 5,
        "confidence_score": 5,
        "impact_horizon": "即时",
        "action_hint": "关注",
        "ai_reasoning": "降准利好金融 / 地产链",
        "risk_notes": None,
        "processed_by": processed_by,
        "duration_ms": 0,
    }


# =========================================================================== #
# ClaudeAgentRunner
# =========================================================================== #


@pytest.mark.asyncio
async def test_claude_runner_happy_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = ClaudeAgentRunner(agent_name="news-classifier-realtime")
    request = _sample_request()

    # 模拟 subprocess 调用：写好 output 文件后返回 exit=0
    def fake_subprocess(
        self: ClaudeAgentRunner,
        prompt: str,
    ) -> subprocess.CompletedProcess[str]:
        # 模拟 agent 写文件
        from amarket.services.config_service import PROJECT_ROOT

        out = PROJECT_ROOT / "data" / "ai" / "outputs" / f"{request.news_id}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(_valid_agent_output()), encoding="utf-8")
        return subprocess.CompletedProcess(args=["claude"], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(ClaudeAgentRunner, "_run_subprocess_blocking", fake_subprocess)

    result = await runner.analyze_news(request)

    assert isinstance(result, NewsAnalysisResult)
    assert result.primary_category.value == "宏观政策"
    assert result.importance_score == 5
    assert result.sentiment.value == "强利多"
    assert result.processed_by.startswith("agent:")
    assert result.duration_ms >= 0


@pytest.mark.asyncio
async def test_claude_runner_degraded_when_output_not_written(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = ClaudeAgentRunner(agent_name="news-classifier-realtime")
    request = NewsAnalysisRequest(
        news_id=99001,
        title="test",
        source="x",
        published_at=datetime.now(UTC),
    )

    def fake_subprocess(
        self: ClaudeAgentRunner,
        prompt: str,
    ) -> subprocess.CompletedProcess[str]:
        # 不写文件
        return subprocess.CompletedProcess(args=["claude"], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(ClaudeAgentRunner, "_run_subprocess_blocking", fake_subprocess)

    # 确保 output 文件不存在
    from amarket.services.config_service import PROJECT_ROOT

    out = PROJECT_ROOT / "data" / "ai" / "outputs" / f"{request.news_id}.json"
    out.unlink(missing_ok=True)

    with pytest.raises(AIAgentDegradedError, match=r"did not update"):
        await runner.analyze_news(request)


@pytest.mark.asyncio
async def test_claude_runner_error_on_nonzero_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = ClaudeAgentRunner(agent_name="news-classifier-realtime")

    def fake_subprocess(
        self: ClaudeAgentRunner,
        prompt: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=["claude"], returncode=1, stdout="", stderr="boom")

    monkeypatch.setattr(ClaudeAgentRunner, "_run_subprocess_blocking", fake_subprocess)

    with pytest.raises(AIError, match=r"exit=1"):
        await runner.analyze_news(_sample_request())


@pytest.mark.asyncio
async def test_claude_runner_timeout_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = ClaudeAgentRunner(agent_name="news-classifier-realtime", default_timeout=1)

    def fake_subprocess(
        self: ClaudeAgentRunner,
        prompt: str,
    ) -> subprocess.CompletedProcess[str]:
        raise AIAgentTimeoutError("simulated timeout")

    monkeypatch.setattr(ClaudeAgentRunner, "_run_subprocess_blocking", fake_subprocess)

    with pytest.raises(AIAgentTimeoutError):
        await runner.analyze_news(_sample_request())


def test_claude_runner_health_check_disabled() -> None:
    runner = ClaudeAgentRunner(enabled=False)
    h = runner.health_check()
    assert h.status == "disabled"


# --------------------------------------------------------------------------- #
# Brainmaster 真实环境兼容性 regression tests
# （fix: Claude CLI v2.1+ 在 -p 模式下的两个坑）
# --------------------------------------------------------------------------- #


def test_claude_runner_uses_permission_mode_accept_edits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: 必须传 --permission-mode acceptEdits 才能让 Write 工具不静默失败。

    Claude CLI v2.1+ 非交互模式 (-p) 下 Write 工具需要 permission；不加这个 flag
    agent 会在写文件那一步默默失败，subprocess exit=0 但 output 文件没更新。
    """
    runner = ClaudeAgentRunner(agent_name="news-classifier-realtime")
    captured: dict[str, Any] = {}

    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    runner._run_subprocess_blocking("test prompt")

    cmd = captured["cmd"]
    assert "--permission-mode" in cmd
    assert "acceptEdits" in cmd
    # 顺序也要对：--permission-mode 紧跟 acceptEdits
    idx = cmd.index("--permission-mode")
    assert cmd[idx + 1] == "acceptEdits"


def test_claude_runner_passes_prompt_via_stdin_not_argv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: prompt 必须走 stdin 不能走 argv。

    Windows 上 `claude.CMD` wrapper 通过 cmd.exe 转发 args，多行中文 + 反引号会
    被乱码。所以 ClaudeAgentRunner 故意把 prompt 走 `input=` 参数（stdin），
    cmd 列表里只保留 `-p` flag 不带 positional prompt。
    """
    runner = ClaudeAgentRunner(agent_name="news-classifier-realtime")
    captured: dict[str, Any] = {}

    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    test_prompt = "多行测试 prompt\n带 `反引号` 和中文"
    runner._run_subprocess_blocking(test_prompt)

    # prompt 必须在 stdin，不在 argv
    assert captured["kwargs"].get("input") == test_prompt
    assert test_prompt not in captured["cmd"]
    # cmd 应以 `-p` 结尾（无 positional prompt）
    assert captured["cmd"][-1] == "-p"


# =========================================================================== #
# AnthropicSDKProvider
# =========================================================================== #


class _FakeContentBlock:
    type = "text"

    def __init__(self, text: str) -> None:
        self.text = text


class _FakeAnthropicResponse:
    def __init__(self, text: str) -> None:
        self.content = [_FakeContentBlock(text)]


class _FakeAnthropicMessages:
    def __init__(self, response_text: str) -> None:
        self._text = response_text
        self.last_kwargs: dict[str, Any] = {}

    async def create(self, **kwargs: Any) -> _FakeAnthropicResponse:
        self.last_kwargs = kwargs
        return _FakeAnthropicResponse(self._text)


class _FakeAnthropic:
    def __init__(self, *_args: Any, response_text: str = "", **_kwargs: Any) -> None:
        self.messages = _FakeAnthropicMessages(response_text)


@pytest.mark.asyncio
async def test_anthropic_sdk_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-12345")

    valid_output = _valid_agent_output(processed_by="sdk:anthropic")
    valid_output.pop("processed_by")  # SDK 由 _parse_sdk_response 注入
    valid_output.pop("duration_ms")

    def fake_async_anthropic_factory(*_args: Any, **_kwargs: Any) -> _FakeAnthropic:
        return _FakeAnthropic(response_text=json.dumps(valid_output))

    with patch(
        "anthropic.AsyncAnthropic",
        side_effect=fake_async_anthropic_factory,
    ):
        provider = AnthropicSDKProvider()
        result = await provider.analyze_news(_sample_request())

    assert result.primary_category.value == "宏观政策"
    assert result.processed_by.startswith("sdk:anthropic")


@pytest.mark.asyncio
async def test_anthropic_sdk_disabled_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    provider = AnthropicSDKProvider()
    assert provider.enabled is False
    with pytest.raises(AIError, match=r"disabled"):
        await provider.analyze_news(_sample_request())


@pytest.mark.asyncio
async def test_anthropic_sdk_invalid_json_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")

    def fake_async_anthropic_factory(*_args: Any, **_kwargs: Any) -> _FakeAnthropic:
        return _FakeAnthropic(response_text="not json at all")

    with patch("anthropic.AsyncAnthropic", side_effect=fake_async_anthropic_factory):
        provider = AnthropicSDKProvider()
        with pytest.raises(AIError, match=r"non-JSON"):
            await provider.analyze_news(_sample_request())


def test_anthropic_sdk_health_disabled() -> None:
    provider = AnthropicSDKProvider(api_key="")
    h = provider.health_check()
    assert h.status == "disabled"


# =========================================================================== #
# DeepSeekSDKProvider
# =========================================================================== #


class _FakeOpenAIMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeOpenAIChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeOpenAIMessage(content)


class _FakeOpenAIResponse:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeOpenAIChoice(content)]


class _FakeChatCompletions:
    def __init__(self, response_text: str) -> None:
        self._text = response_text

    async def create(self, **_kwargs: Any) -> _FakeOpenAIResponse:
        return _FakeOpenAIResponse(self._text)


class _FakeChat:
    def __init__(self, response_text: str) -> None:
        self.completions = _FakeChatCompletions(response_text)


class _FakeAsyncOpenAI:
    def __init__(self, *_args: Any, response_text: str = "", **_kwargs: Any) -> None:
        self.chat = _FakeChat(response_text)


@pytest.mark.asyncio
async def test_deepseek_sdk_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-deepseek-fake")
    valid = _valid_agent_output(processed_by="sdk:deepseek")
    valid.pop("processed_by")
    valid.pop("duration_ms")

    with patch(
        "openai.AsyncOpenAI",
        side_effect=lambda *_a, **_kw: _FakeAsyncOpenAI(response_text=json.dumps(valid)),
    ):
        provider = DeepSeekSDKProvider()
        result = await provider.analyze_news(_sample_request())

    assert result.primary_category.value == "宏观政策"
    assert result.processed_by.startswith("sdk:deepseek")


def test_deepseek_sdk_disabled_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    provider = DeepSeekSDKProvider()
    assert provider.enabled is False


# =========================================================================== #
# FallbackChainProvider
# =========================================================================== #


class _StubProvider:
    """简易 stub —— 模拟 AIProvider Protocol。"""

    def __init__(
        self,
        code: str,
        *,
        enabled: bool = True,
        raise_exc: BaseException | None = None,
        result: NewsAnalysisResult | None = None,
    ) -> None:
        self.code = code
        self.enabled = enabled
        self._raise = raise_exc
        self._result = result or NewsAnalysisResult.model_validate(_valid_agent_output(code))

    async def analyze_news(self, request: NewsAnalysisRequest) -> NewsAnalysisResult:
        if self._raise:
            raise self._raise
        return self._result

    def health_check(self) -> object:
        from amarket.adapters.ai.base import ProviderHealth

        return ProviderHealth(
            code=self.code,
            enabled=self.enabled,
            configured=True,
            status="ok" if self.enabled else "disabled",
        )


@pytest.mark.asyncio
async def test_fallback_chain_uses_first_enabled() -> None:
    p1 = _StubProvider("p1", enabled=True)
    p2 = _StubProvider("p2", enabled=True)
    chain = FallbackChainProvider([p1, p2])
    result = await chain.analyze_news(_sample_request())
    assert result.processed_by == "p1"


@pytest.mark.asyncio
async def test_fallback_chain_skips_disabled() -> None:
    p1 = _StubProvider("p1", enabled=False)
    p2 = _StubProvider("p2", enabled=True)
    chain = FallbackChainProvider([p1, p2])
    result = await chain.analyze_news(_sample_request())
    assert result.processed_by == "p2"


@pytest.mark.asyncio
async def test_fallback_chain_falls_back_on_aierror() -> None:
    p1 = _StubProvider("p1", enabled=True, raise_exc=AIError("p1 down"))
    p2 = _StubProvider("p2", enabled=True)
    chain = FallbackChainProvider([p1, p2])
    result = await chain.analyze_news(_sample_request())
    assert result.processed_by == "p2"


@pytest.mark.asyncio
async def test_fallback_chain_all_fail_raises() -> None:
    p1 = _StubProvider("p1", enabled=True, raise_exc=AIError("p1 down"))
    p2 = _StubProvider("p2", enabled=True, raise_exc=AIAgentDegradedError("p2 degraded"))
    chain = FallbackChainProvider([p1, p2])
    with pytest.raises(AIError, match=r"All AI providers failed"):
        await chain.analyze_news(_sample_request())


@pytest.mark.asyncio
async def test_fallback_chain_no_enabled_raises() -> None:
    p1 = _StubProvider("p1", enabled=False)
    chain = FallbackChainProvider([p1])
    with pytest.raises(AIError, match=r"No enabled"):
        await chain.analyze_news(_sample_request())


def test_fallback_chain_health_lists_providers() -> None:
    p1 = _StubProvider("p1", enabled=True)
    p2 = _StubProvider("p2", enabled=False)
    chain = FallbackChainProvider([p1, p2])
    h = chain.health_check()
    assert h.code == "fallback-chain"
    assert h.enabled is True  # p1 enabled
    # children_health 拿子详情
    children = chain.children_health()
    assert len(children) == 2


# =========================================================================== #
# Factory
# =========================================================================== #


def test_build_default_includes_all_tiers(clean_env: pytest.MonkeyPatch) -> None:
    chain = build_default_ai_provider()
    assert isinstance(chain, FallbackChainProvider)
    codes = [p.code for p in chain.providers]
    assert codes[0].startswith("agent:")
    assert "sdk:anthropic" in codes
    assert "sdk:deepseek" in codes


def test_build_default_can_disable_tiers() -> None:
    chain = build_default_ai_provider(
        enable_brainmaster=False,
        enable_anthropic=False,
        enable_deepseek=True,
    )
    assert isinstance(chain, FallbackChainProvider)
    codes = [p.code for p in chain.providers]
    assert codes == ["sdk:deepseek"]


# =========================================================================== #
# Protocol conformance
# =========================================================================== #


def test_all_providers_conform_to_aiprovider_protocol() -> None:
    runner = ClaudeAgentRunner(enabled=False)
    anthropic = AnthropicSDKProvider(api_key="")
    deepseek = DeepSeekSDKProvider(api_key="")
    chain = FallbackChainProvider([_StubProvider("stub")])

    for p in (runner, anthropic, deepseek, chain):
        assert isinstance(p, AIProvider)


# Just so asyncio.run-style imports don't get flagged unused
_ = asyncio
