"""SDK Provider 基础工具 + Anthropic / DeepSeek 实现（Spec v3 §6.2.3.2/3）。

Phase 1 备路径（M2+）。用于：
- ClaudeAgentRunner 不可用时 fallback（degraded/timeout/error）
- 高并发批量打分（subprocess 启动慢，SDK 更适合）

两个实现共享同一 Pydantic prompt template + JSON schema 解析逻辑，
仅 SDK client 调用 + model id 不同。
"""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from typing import Any

from amarket.adapters.ai.base import (
    AIProvider,
    NewsAnalysisRequest,
    NewsAnalysisResult,
    ProviderHealth,
)
from amarket.core.exceptions import AIError
from amarket.core.logging import get_logger

log = get_logger(__name__)

_SYSTEM_PROMPT = """你是 A 股专业新闻分析师。给定一条新闻 JSON，输出严格的结构化分析 JSON。

输出 JSON 必须包含这些字段（值取自给定 enum）：
- primary_category: 宏观政策 / 市场行情 / 公司公告 / 海外映射 / 大宗商品 / 风险事件 / 资金流 / 交易提示
- tags: 二级标签数组（板块名 / 主题词）
- related_sectors: [{name, weight 0-1}]
- related_symbols: [{code, name}]
- sentiment: 强利多 / 利多 / 中性 / 利空 / 强利空 / 不确定
- importance_score: 1-5（5=央行/重大政策/黑天鹅）
- urgency_score: 1-5（5=必须即时推送）
- confidence_score: 1-5（你对自己评分的信心）
- impact_horizon: 即时 / 日内 / 短期 / 中期
- action_hint: 观察 / 关注 / 加仓 / 减仓 / 规避（永远不允许"买入/卖出"具体指令）
- ai_reasoning: 简短解释（≤ 100 字）
- risk_notes: 风险提示（≤ 80 字，无风险写 null）

严格输出 JSON 单个对象，不要 markdown 包裹，不要解释。
"""


def _build_user_prompt(req: NewsAnalysisRequest) -> str:
    """构造用户消息：把 NewsAnalysisRequest 转 JSON 块。"""
    return f"待分析新闻 JSON:\n```json\n{req.model_dump_json(indent=2)}\n```"


def _parse_sdk_response(text: str, *, processed_by: str, duration_ms: int) -> NewsAnalysisResult:
    """SDK 返回文本 → NewsAnalysisResult。容错处理 ```json ... ``` 包裹。"""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # 去掉 ```json ... ``` markdown 围栏
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    try:
        raw = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AIError(f"SDK returned non-JSON: {exc}") from exc

    raw["processed_by"] = processed_by
    raw["duration_ms"] = duration_ms
    return NewsAnalysisResult.model_validate(raw)


# --------------------------------------------------------------------------- #
# Anthropic
# --------------------------------------------------------------------------- #


class AnthropicSDKProvider(AIProvider):
    """Anthropic API SDK provider — 用 ANTHROPIC_API_KEY 环境变量。"""

    code: str = "sdk:anthropic"

    DEFAULT_MODEL = "claude-sonnet-4-5"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        max_tokens: int = 1500,
        timeout: float = 30.0,
        enabled: bool = True,
    ) -> None:
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self._base_url = base_url or os.getenv("ANTHROPIC_BASE_URL", "") or None
        self._model = model or self.DEFAULT_MODEL
        self._max_tokens = max_tokens
        self._timeout = timeout
        self.enabled = enabled and bool(self._api_key)
        self._last_check_at: datetime | None = None
        self._last_error: str | None = None

    async def analyze_news(self, request: NewsAnalysisRequest) -> NewsAnalysisResult:
        if not self.enabled:
            raise AIError("AnthropicSDKProvider disabled (missing ANTHROPIC_API_KEY)")

        # 延迟 import，避免未安装时 import 失败
        try:
            from anthropic import AsyncAnthropic
        except ImportError as exc:
            raise AIError("`anthropic` package not installed") from exc

        client = AsyncAnthropic(
            api_key=self._api_key,
            base_url=self._base_url,
            timeout=self._timeout,
        )

        started = time.perf_counter()
        try:
            resp = await client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": _build_user_prompt(request)}],
            )
        except Exception as exc:
            self._record_failure(str(exc))
            raise AIError(f"Anthropic SDK call failed: {exc}") from exc

        duration_ms = int((time.perf_counter() - started) * 1000)

        # 取第一个 text block
        text_chunks = [blk.text for blk in resp.content if getattr(blk, "type", "") == "text"]  # type: ignore[union-attr]
        text = "".join(text_chunks) if text_chunks else ""
        if not text:
            self._record_failure("empty content")
            raise AIError("Anthropic SDK returned empty content")

        result = _parse_sdk_response(
            text,
            processed_by=f"{self.code}-{self._model}",
            duration_ms=duration_ms,
        )
        self._record_success()
        return result

    def health_check(self) -> ProviderHealth:
        status: Any
        if not self.enabled:
            status = "disabled"
        elif self._last_error:
            status = "degraded"
        else:
            status = "ok"
        return ProviderHealth(
            code=self.code,
            enabled=self.enabled,
            configured=bool(self._api_key),
            status=status,
            last_check_at=self._last_check_at,
            last_error=self._last_error,
        )

    def _record_success(self) -> None:
        self._last_error = None
        self._last_check_at = datetime.now(UTC)

    def _record_failure(self, error: str) -> None:
        self._last_error = error[:200]
        self._last_check_at = datetime.now(UTC)
        log.warning("anthropic_sdk.failure", error=self._last_error)


# --------------------------------------------------------------------------- #
# DeepSeek（走 OpenAI 兼容协议）
# --------------------------------------------------------------------------- #


class DeepSeekSDKProvider(AIProvider):
    """DeepSeek API provider — 用 DEEPSEEK_API_KEY 环境变量。

    DeepSeek 兼容 OpenAI SDK，复用 openai package。
    """

    code: str = "sdk:deepseek"

    DEFAULT_MODEL = "deepseek-chat"
    DEFAULT_BASE_URL = "https://api.deepseek.com"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        max_tokens: int = 1500,
        timeout: float = 30.0,
        enabled: bool = True,
    ) -> None:
        self._api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self._base_url = base_url or self.DEFAULT_BASE_URL
        self._model = model or self.DEFAULT_MODEL
        self._max_tokens = max_tokens
        self._timeout = timeout
        self.enabled = enabled and bool(self._api_key)
        self._last_check_at: datetime | None = None
        self._last_error: str | None = None

    async def analyze_news(self, request: NewsAnalysisRequest) -> NewsAnalysisResult:
        if not self.enabled:
            raise AIError("DeepSeekSDKProvider disabled (missing DEEPSEEK_API_KEY)")

        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise AIError("`openai` package not installed") from exc

        client = AsyncOpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
            timeout=self._timeout,
        )

        started = time.perf_counter()
        try:
            resp = await client.chat.completions.create(
                model=self._model,
                max_tokens=self._max_tokens,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": _build_user_prompt(request)},
                ],
            )
        except Exception as exc:
            self._record_failure(str(exc))
            raise AIError(f"DeepSeek SDK call failed: {exc}") from exc

        duration_ms = int((time.perf_counter() - started) * 1000)

        if not resp.choices:
            self._record_failure("no choices in response")
            raise AIError("DeepSeek SDK returned no choices")

        text = (resp.choices[0].message.content or "").strip()
        if not text:
            self._record_failure("empty content")
            raise AIError("DeepSeek SDK returned empty content")

        result = _parse_sdk_response(
            text,
            processed_by=f"{self.code}-{self._model}",
            duration_ms=duration_ms,
        )
        self._record_success()
        return result

    def health_check(self) -> ProviderHealth:
        status: Any
        if not self.enabled:
            status = "disabled"
        elif self._last_error:
            status = "degraded"
        else:
            status = "ok"
        return ProviderHealth(
            code=self.code,
            enabled=self.enabled,
            configured=bool(self._api_key),
            status=status,
            last_check_at=self._last_check_at,
            last_error=self._last_error,
        )

    def _record_success(self) -> None:
        self._last_error = None
        self._last_check_at = datetime.now(UTC)

    def _record_failure(self, error: str) -> None:
        self._last_error = error[:200]
        self._last_check_at = datetime.now(UTC)
        log.warning("deepseek_sdk.failure", error=self._last_error)


__all__ = ["AnthropicSDKProvider", "DeepSeekSDKProvider"]
