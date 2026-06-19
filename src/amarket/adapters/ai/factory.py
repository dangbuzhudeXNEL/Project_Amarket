"""AIProviderFactory — 根据 config 创建合适的 provider，含自动 fallback 链。

工作流（Spec v3 §6.1.4 NewsAnalysis 服务的降级链）：
    Tier 1 (主)   → Brainmaster (ClaudeAgentRunner)
    Tier 2 (备)   → Anthropic SDK
    Tier 3 (备)   → DeepSeek SDK
    全部失败       → 调用方降级到规则评分（SimpleRuleScorer）

Provider 选择优先级在 config/agents.yml 里。
"""

from __future__ import annotations

from amarket.adapters.ai.base import (
    AIProvider,
    NewsAnalysisRequest,
    NewsAnalysisResult,
    ProviderHealth,
)
from amarket.adapters.ai.claude_agent_runner import ClaudeAgentRunner
from amarket.adapters.ai.sdk_providers import AnthropicSDKProvider, DeepSeekSDKProvider
from amarket.core.exceptions import AIError
from amarket.core.logging import get_logger

log = get_logger(__name__)


class FallbackChainProvider(AIProvider):
    """组合多个 provider，按优先级 try-then-fallback。"""

    code: str = "fallback-chain"

    def __init__(self, providers: list[AIProvider]) -> None:
        if not providers:
            raise ValueError("FallbackChainProvider needs >= 1 provider")
        self._providers = providers
        self.enabled = any(p.enabled for p in providers)

    async def analyze_news(self, request: NewsAnalysisRequest) -> NewsAnalysisResult:
        last_exc: Exception | None = None
        for provider in self._providers:
            if not provider.enabled:
                continue
            try:
                return await provider.analyze_news(request)
            except AIError as exc:
                log.warning(
                    "ai.provider_failed_fallback",
                    provider=provider.code,
                    next_provider=self._next_enabled_code(provider),
                    error=str(exc)[:120],
                )
                last_exc = exc
                continue
        # 全部失败
        if last_exc:
            raise AIError(f"All AI providers failed; last error: {last_exc}") from last_exc
        raise AIError("No enabled AI provider in fallback chain")

    def health_check(self) -> ProviderHealth:
        """聚合子 provider 健康为单一 ProviderHealth。

        子 provider 详情通过 `.children_health` 单独提供（避免破坏 Protocol 返回类型）。
        """
        children = [p.health_check() for p in self._providers]
        enabled_children = [c for c in children if c.enabled]
        if not enabled_children:
            return ProviderHealth(
                code=self.code, enabled=False, configured=False, status="disabled"
            )
        # 聚合状态：第一个 enabled 子 provider 的状态代表 chain（最后会被 fallback 兜底）
        first_enabled = enabled_children[0]
        # 收集所有错误信息（如有），方便 diagnostic
        errors = [f"{c.code}:{c.last_error}" for c in children if c.last_error]
        return ProviderHealth(
            code=self.code,
            enabled=True,
            configured=any(c.configured for c in children),
            status=first_enabled.status,
            last_check_at=first_enabled.last_check_at,
            last_error=" | ".join(errors) if errors else None,
        )

    def children_health(self) -> list[ProviderHealth]:
        """各子 provider 的健康详情（给运维 / dashboard 用）。"""
        return [p.health_check() for p in self._providers]

    def _next_enabled_code(self, current: AIProvider) -> str | None:
        seen = False
        for p in self._providers:
            if seen and p.enabled:
                return p.code
            if p is current:
                seen = True
        return None

    @property
    def providers(self) -> list[AIProvider]:
        return list(self._providers)


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #


def build_default_ai_provider(
    *,
    enable_brainmaster: bool = True,
    enable_anthropic: bool = True,
    enable_deepseek: bool = True,
    agent_name: str = "news-classifier-realtime",
) -> AIProvider:
    """按 Spec v3 §6.2.3 默认顺序构造 fallback chain。

    Tier 1: ClaudeAgentRunner (Brainmaster，零 API key)
    Tier 2: AnthropicSDKProvider (需 ANTHROPIC_API_KEY)
    Tier 3: DeepSeekSDKProvider (需 DEEPSEEK_API_KEY)

    未配置的 tier 会被 chain 跳过（health_check 返回 disabled）。
    至少需要一个 tier enabled，否则 chain.enabled=False，调用 analyze 直接抛。
    """
    chain: list[AIProvider] = []
    if enable_brainmaster:
        chain.append(ClaudeAgentRunner(agent_name=agent_name))
    if enable_anthropic:
        chain.append(AnthropicSDKProvider())
    if enable_deepseek:
        chain.append(DeepSeekSDKProvider())
    return FallbackChainProvider(chain)


__all__ = ["FallbackChainProvider", "build_default_ai_provider"]
