"""AIProvider 接口（Spec v3 §6.2.3）。

统一的 AI 调用入口 — Service 层只 import 这里，不 import 具体实现。

两条路径（M2 起共存，可配置切换 + 自动 fallback）：
- 🥇 主：ClaudeAgentRunner (Brainmaster 模式，subprocess + claude CLI + agent 文件)
- 🥈 备：AnthropicSDKProvider / DeepSeekSDKProvider (走 API key)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from amarket.domain.enums import (
    ActionHint,
    ImpactHorizon,
    NewsCategory,
    Sentiment,
)

# --------------------------------------------------------------------------- #
# DTOs
# --------------------------------------------------------------------------- #


class NewsAnalysisRequest(BaseModel):
    """喂给 AI 的单条新闻输入。"""

    news_id: int
    title: str
    summary: str | None = None
    content: str | None = None
    source: str
    published_at: datetime
    # 规则预分析结果（给 AI 上下文，让它知道规则已经判断了什么）
    rule_primary_category: NewsCategory | None = None
    rule_tags: list[str] = Field(default_factory=list)
    rule_importance: int | None = None
    # 近 24h 同类新闻 top 3（让 AI 知道 context，避免重复评估）
    similar_news_titles: list[str] = Field(default_factory=list)


class NewsAnalysisResult(BaseModel):
    """AI 返回的结构化分析（对应 NewsAnalysis 表）。"""

    primary_category: NewsCategory
    tags: list[str] = Field(default_factory=list)
    related_sectors: list[dict[str, object]] = Field(default_factory=list)
    related_symbols: list[dict[str, object]] = Field(default_factory=list)
    sentiment: Sentiment
    importance_score: int = Field(ge=1, le=5)
    urgency_score: int = Field(ge=1, le=5)
    confidence_score: int = Field(ge=1, le=5)
    impact_horizon: ImpactHorizon
    action_hint: ActionHint
    ai_reasoning: str | None = None
    risk_notes: str | None = None
    # 元数据
    processed_by: str  # 'agent:news-classifier-realtime' / 'sdk:anthropic-claude-x' / ...
    duration_ms: int
    finished_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


ProviderStatus = Literal["ok", "degraded", "timeout", "error", "disabled"]


class ProviderHealth(BaseModel):
    """AI provider 健康状态。"""

    code: str  # 'agent:news-classifier-realtime' / 'sdk:anthropic' / ...
    enabled: bool
    configured: bool
    status: ProviderStatus = "disabled"
    last_check_at: datetime | None = None
    last_error: str | None = None


# --------------------------------------------------------------------------- #
# Protocol
# --------------------------------------------------------------------------- #


@runtime_checkable
class AIProvider(Protocol):
    """统一 AI 调用接口（Brainmaster + SDK 共享）。"""

    code: str  # 唯一标识
    enabled: bool

    async def analyze_news(self, request: NewsAnalysisRequest) -> NewsAnalysisResult:
        """单条新闻深度分析。

        Raises:
            AIError 系列异常（AIAgentDegradedError / AIAgentTimeoutError / 通用 AIError）
        """
        ...

    def health_check(self) -> ProviderHealth: ...


__all__ = [
    "AIProvider",
    "NewsAnalysisRequest",
    "NewsAnalysisResult",
    "ProviderHealth",
    "ProviderStatus",
]
