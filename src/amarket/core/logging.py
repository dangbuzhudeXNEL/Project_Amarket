"""structlog 配置 — JSON 输出（生产）/ Console 输出（开发）。

约定（Spec v3 §13.2）：
- 关键字段：timestamp, level, event, module, user_id, news_id, trace_id, duration_ms
- 密钥永远脱敏（不在日志出现完整 webhook / api key）
- DEBUG/INFO 普通业务事件；WARN 单源失败；ERROR 推送/AI 失败；CRITICAL 调度死
"""

from __future__ import annotations

import logging
import re
import sys
from typing import Any, cast

import structlog
from structlog.contextvars import merge_contextvars
from structlog.processors import (
    JSONRenderer,
    StackInfoRenderer,
    TimeStamper,
    UnicodeDecoder,
    add_log_level,
    format_exc_info,
)
from structlog.stdlib import (
    BoundLogger,
    ProcessorFormatter,
    add_logger_name,
)

# 已知密钥字段名（key 名命中即脱敏）
_SECRET_KEY_PATTERN = re.compile(
    r"(?:api[_-]?key|token|secret|password|webhook(?:_url)?|bot[_-]?key)",
    re.IGNORECASE,
)
# Webhook URL 中的 ?key=xxx 子串
_WEBHOOK_KEY_QUERY = re.compile(r"([?&]key=)([^&\s]+)")


def _redact_value(value: Any) -> Any:
    """脱敏单个值（字符串保留首末各 4 个字符）。"""
    if not isinstance(value, str) or len(value) < 12:
        return "***"
    return f"{value[:4]}***{value[-4:]}"


def _redact_secrets(
    _logger: Any,
    _method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """structlog processor — 把含敏感关键字的字段脱敏。"""
    for key, value in list(event_dict.items()):
        if _SECRET_KEY_PATTERN.search(key):
            event_dict[key] = _redact_value(value)
        elif isinstance(value, str) and "qyapi.weixin.qq.com" in value:
            event_dict[key] = _WEBHOOK_KEY_QUERY.sub(r"\1***", value)
    return event_dict


def configure_logging(
    *,
    log_level: str = "INFO",
    log_format: str = "json",
) -> None:
    """初始化全局 structlog 配置。

    Args:
        log_level: DEBUG / INFO / WARNING / ERROR / CRITICAL
        log_format: 'json' 生产用；'console' 开发用（带颜色 + key=value 格式）
    """
    level = logging.getLevelName(log_level.upper())

    shared_processors: list[Any] = [
        merge_contextvars,
        add_log_level,
        add_logger_name,
        TimeStamper(fmt="iso", utc=True),
        StackInfoRenderer(),
        UnicodeDecoder(),
        _redact_secrets,
    ]

    if log_format == "console":
        renderer: Any = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 同步把标准库 logging 转发到 structlog（FastAPI/uvicorn 等会用 logging）
    formatter = ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(level)

    # 降噪：uvicorn access log 走 INFO 即可
    for noisy in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(noisy).propagate = True


def get_logger(name: str | None = None) -> BoundLogger:
    """获取一个 structlog logger。

    用法::

        log = get_logger(__name__)
        log.info("news.collected", source="ths", count=42)
    """
    return cast(BoundLogger, structlog.get_logger(name))


__all__ = ["configure_logging", "get_logger"]
