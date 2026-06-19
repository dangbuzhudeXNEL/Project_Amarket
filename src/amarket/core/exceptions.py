"""自定义异常基类。

约定：
- 所有业务异常继承 `AmarketError`
- HTTP API 层会把这些异常映射为合适的 status code
"""

from __future__ import annotations


class AmarketError(Exception):
    """所有 amarket 业务异常的基类。"""


class ConfigError(AmarketError):
    """配置加载 / 校验失败。"""


class SourceError(AmarketError):
    """新闻 / 行情源访问失败。"""


class AIError(AmarketError):
    """AI Provider 调用失败（Phase 1 SDK / Phase 2 Brainmaster）。"""


class AIAgentDegradedError(AIError):
    """ClaudeAgentRunner: 子进程退出但 expected_output 文件未写或无效。"""


class AIAgentTimeoutError(AIError):
    """ClaudeAgentRunner: 子进程超时。"""


class NotifierError(AmarketError):
    """推送渠道发送失败。"""


class RateLimitedError(NotifierError):
    """被节流（用户级 / 渠道级 / 全局级）。"""


class ParamError(AmarketError):
    """参数读写 / 权限 / 版本相关错误。"""


class ParamPermissionDeniedError(ParamError):
    """用户无权限读 / 写该参数。"""
