"""ConfigService — 加载 YAML 配置 + 环境变量，提供运行时访问。

约定（Spec v3 §12 + CLAUDE.md 编码规范 #4）：
- 所有可调参数走 `config/*.yml`
- 所有密钥走 `.env`，代码里只用 env var 名
- 配置加载用 `pydantic-settings`，不允许零散读 YAML
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from amarket.core.exceptions import ConfigError

PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]
CONFIG_DIR: Path = PROJECT_ROOT / "config"


class AppSection(BaseModel):
    """`app.yml -> app:` 段。"""

    name: str = "amarket"
    env: str = "dev"
    timezone: str = "Asia/Shanghai"
    log_level: str = "INFO"
    data_dir: str = "./data"
    database_url: str = "sqlite:///./data/amarket.db"


class ApiSection(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8080
    cors_origins: list[str] = Field(default_factory=list)


class UiSection(BaseModel):
    streamlit_port: int = 8501
    poc_port: int = 8000


class ProjectMetaSection(BaseModel):
    spec_version: str = "v3.0"
    current_phase: str = "Phase1"
    current_milestone: str = "M0"


class AppConfig(BaseModel):
    """`config/app.yml` 的完整结构。"""

    app: AppSection = Field(default_factory=AppSection)
    api: ApiSection = Field(default_factory=ApiSection)
    ui: UiSection = Field(default_factory=UiSection)
    project_meta: ProjectMetaSection = Field(default_factory=ProjectMetaSection)


class EnvSettings(BaseSettings):
    """读 `.env` 与环境变量。

    Pydantic-settings 约定：env var 名大写，命中字段后自动注入。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用
    app_env: str = "dev"
    log_level: str = "INFO"
    log_format: str = "json"

    # Notifier webhooks（默认空，未配置时 notifier 会拒绝发送）
    wework_bot_webhook_url: str = ""
    wework_alert_bot_webhook_url: str = ""
    lark_bot_webhook_url: str = ""

    # AI
    anthropic_api_key: str = ""
    anthropic_base_url: str = ""
    deepseek_api_key: str = ""

    # Claude CLI (Phase 2)
    claude_cli_path: str = "claude"


# --------------------------------------------------------------------------- #
# 加载函数（带 lru_cache 一次性加载，热重载用 reload_config）
# --------------------------------------------------------------------------- #


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"Top-level YAML in {path} must be a mapping")
    return data


@lru_cache(maxsize=1)
def get_app_config(config_dir: Path | None = None) -> AppConfig:
    """加载 `config/app.yml`。结果被缓存。"""
    cdir = config_dir or CONFIG_DIR
    raw = _load_yaml(cdir / "app.yml")
    try:
        return AppConfig.model_validate(raw)
    except Exception as exc:
        raise ConfigError(f"Invalid app.yml structure: {exc}") from exc


@lru_cache(maxsize=1)
def get_env_settings() -> EnvSettings:
    """加载 `.env` + 环境变量。"""
    return EnvSettings()


def reload_config() -> None:
    """清空缓存，下次访问重新加载。

    用于配置热重载场景；测试中也常用。
    """
    get_app_config.cache_clear()
    get_env_settings.cache_clear()


__all__ = [
    "CONFIG_DIR",
    "PROJECT_ROOT",
    "AppConfig",
    "EnvSettings",
    "get_app_config",
    "get_env_settings",
    "reload_config",
]
