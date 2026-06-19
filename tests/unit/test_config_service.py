"""ConfigService 单元测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from amarket.core.exceptions import ConfigError
from amarket.services.config_service import (
    AppConfig,
    EnvSettings,
    get_app_config,
    get_env_settings,
    reload_config,
)


def test_get_app_config_returns_validated_pydantic_model(project_root: Path) -> None:
    cfg = get_app_config()
    assert isinstance(cfg, AppConfig)
    assert cfg.app.name == "amarket"
    assert cfg.app.timezone == "Asia/Shanghai"
    assert cfg.project_meta.current_phase == "Phase1"
    # milestone 跟随项目实际推进，不硬编码到 test
    assert cfg.project_meta.current_milestone.startswith("M")


def test_get_app_config_is_cached(project_root: Path) -> None:
    a = get_app_config()
    b = get_app_config()
    assert a is b


def test_reload_config_clears_cache(project_root: Path) -> None:
    a = get_app_config()
    reload_config()
    b = get_app_config()
    assert a is not b
    assert a.app.name == b.app.name  # 内容一致


def test_get_app_config_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        get_app_config(config_dir=tmp_path)


def test_env_settings_defaults(clean_env: pytest.MonkeyPatch) -> None:
    env = get_env_settings()
    assert isinstance(env, EnvSettings)
    assert env.app_env == "dev"
    assert env.log_level == "INFO"
    assert env.wework_bot_webhook_url == ""


def test_env_settings_picks_up_env_var(
    clean_env: pytest.MonkeyPatch,
) -> None:
    clean_env.setenv("WEWORK_BOT_WEBHOOK_URL", "https://example.com/webhook?key=abc")
    reload_config()
    env = get_env_settings()
    assert env.wework_bot_webhook_url == "https://example.com/webhook?key=abc"
