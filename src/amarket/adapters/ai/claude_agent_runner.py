"""ClaudeAgentRunner — Brainmaster 模式（Spec v3 §6.2.3.1）。

通过 `subprocess.run(["claude", "--agent", <name>, "-p", <prompt>])` 调用
本地 Claude CLI，agent 写 JSON 文件到约定路径，Python 校验 + 读取。

零 API 成本（复用用户 Claude Code 订阅）。

约定：
- agent 定义在 `.claude/agents/<name>.md`（含 YAML frontmatter）
- agent 必须把结构化输出写到 prompt 中告知的 expected_output 路径
- Python 校验：subprocess exit=0 + 文件 mtime 已更新 + JSON valid + 必需字段齐
- 任一校验失败 → 抛 AIAgentDegradedError，由 factory 走 fallback
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from amarket.adapters.ai.base import (
    AIProvider,
    NewsAnalysisRequest,
    NewsAnalysisResult,
    ProviderHealth,
)
from amarket.core.exceptions import (
    AIAgentDegradedError,
    AIAgentTimeoutError,
    AIError,
)
from amarket.core.logging import get_logger
from amarket.services.config_service import PROJECT_ROOT

log = get_logger(__name__)

# data/ai/inputs/  和 data/ai/outputs/  下放 agent 的输入 prompt 和输出 JSON
_AI_DATA_DIR = PROJECT_ROOT / "data" / "ai"


class ClaudeAgentRunner(AIProvider):
    """通用 Claude CLI agent runner — 任何 .claude/agents/<name>.md 都能跑。

    M2 阶段先支持 `news-classifier-realtime` agent 做单条新闻深度分析。
    M4+ 支持 `daily-report-writer`, `news-analyst`（盘前）等。
    """

    code: str = "agent:claude-runner"

    def __init__(
        self,
        *,
        agent_name: str = "news-classifier-realtime",
        cli_path: str = "claude",
        default_timeout: int = 120,
        cwd: Path | None = None,
        enabled: bool = True,
    ) -> None:
        # Windows 下 claude 是 .cmd 包装器，必须用 shutil.which 查
        self._cli = shutil.which(cli_path) or cli_path
        self._agent_name = agent_name
        self._default_timeout = default_timeout
        self._cwd = cwd or PROJECT_ROOT
        self.enabled = enabled
        self.code = f"agent:{agent_name}"
        self._last_check_at: datetime | None = None
        self._last_error: str | None = None

        # 创建 IO 目录
        (_AI_DATA_DIR / "inputs").mkdir(parents=True, exist_ok=True)
        (_AI_DATA_DIR / "outputs").mkdir(parents=True, exist_ok=True)

    # ----------------- 公共接口 ----------------- #

    async def analyze_news(self, request: NewsAnalysisRequest) -> NewsAnalysisResult:
        """单条新闻深度分析（subprocess 调 agent，输出 JSON 文件）。

        实现细节：
        1. 把 request 序列化到 data/ai/inputs/<news_id>.json
        2. 构造 prompt（指明 agent 读 inputs 文件 + 写到 outputs 文件）
        3. subprocess.run 调 claude CLI
        4. 校验：exit=0 + outputs 文件已更新 + JSON valid + 必需字段
        5. 读 outputs 解析为 NewsAnalysisResult 返回
        """
        if not self.enabled:
            raise AIError("ClaudeAgentRunner disabled")

        input_path = _AI_DATA_DIR / "inputs" / f"{request.news_id}.json"
        output_path = _AI_DATA_DIR / "outputs" / f"{request.news_id}.json"

        input_path.write_text(
            request.model_dump_json(indent=2),
            encoding="utf-8",
        )

        # output 文件 mtime 比对的 baseline（不存在 → 0.0）
        pre_mtime = output_path.stat().st_mtime if output_path.exists() else 0.0

        prompt = self._build_prompt(input_path, output_path)

        # 由于 subprocess.run 是阻塞的，用 asyncio.to_thread 避免阻塞 event loop
        import asyncio

        started = time.perf_counter()
        try:
            completed = await asyncio.to_thread(
                self._run_subprocess_blocking,
                prompt,
            )
        except AIAgentTimeoutError as exc:
            self._record_failure(str(exc))
            raise

        duration_ms = int((time.perf_counter() - started) * 1000)

        # 校验
        if completed.returncode != 0:
            err = f"claude CLI exit={completed.returncode} stderr={completed.stderr[:200]}"
            self._record_failure(err)
            raise AIError(err)

        if not output_path.exists() or output_path.stat().st_mtime <= pre_mtime:
            err = f"agent did not update {output_path}"
            self._record_failure(err)
            raise AIAgentDegradedError(err)

        try:
            raw = json.loads(output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            err = f"invalid JSON in {output_path}: {exc}"
            self._record_failure(err)
            raise AIAgentDegradedError(err) from exc

        try:
            result = self._parse_agent_output(raw, duration_ms)
        except Exception as exc:
            err = f"agent output schema invalid: {exc}"
            self._record_failure(err)
            raise AIAgentDegradedError(err) from exc

        self._record_success()
        return result

    def health_check(self) -> ProviderHealth:
        # 是否真能执行 claude CLI 仅作 best-effort 检查（不实际跑）
        cli_ok = bool(self._cli) and (Path(self._cli).exists() or self._cli == "claude")
        status: Any
        if not self.enabled:
            status = "disabled"
        elif not cli_ok:
            status = "down"
        elif self._last_error:
            status = "degraded"
        else:
            status = "ok"

        return ProviderHealth(
            code=self.code,
            enabled=self.enabled,
            configured=cli_ok,
            status=status,
            last_check_at=self._last_check_at,
            last_error=self._last_error,
        )

    # ----------------- 内部 ----------------- #

    def _build_prompt(self, input_path: Path, output_path: Path) -> str:
        """构造 agent prompt。要求 agent 读 input 文件 → 分析 → 写 output JSON。"""
        rel_in = input_path.relative_to(self._cwd).as_posix()
        rel_out = output_path.relative_to(self._cwd).as_posix()
        return (
            f"读取 `{rel_in}` 中的新闻数据（NewsAnalysisRequest schema），"
            f"分析后写出 NewsAnalysisResult 结构 JSON 到 `{rel_out}`。"
            f"必需字段见 .claude/agents/{self._agent_name}.md。"
        )

    def _run_subprocess_blocking(self, prompt: str) -> subprocess.CompletedProcess[str]:
        """同步子进程调用（由 asyncio.to_thread 包装为 async）。"""
        cmd = [self._cli, "--agent", self._agent_name, "-p", prompt]
        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                cwd=self._cwd,
                timeout=self._default_timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise AIAgentTimeoutError(
                f"agent {self._agent_name} timed out after {self._default_timeout}s"
            ) from exc
        except FileNotFoundError as exc:
            raise AIError(f"claude CLI not found: {self._cli}") from exc

    def _parse_agent_output(
        self,
        raw: dict[str, Any],
        duration_ms: int,
    ) -> NewsAnalysisResult:
        """把 agent JSON 输出转为 NewsAnalysisResult。"""
        # 注入 processed_by + duration_ms（agent 不写也没事）
        raw.setdefault("processed_by", self.code)
        raw["duration_ms"] = duration_ms
        return NewsAnalysisResult.model_validate(raw)

    def _record_success(self) -> None:
        self._last_error = None
        self._last_check_at = datetime.now(UTC)

    def _record_failure(self, error: str) -> None:
        self._last_error = error[:200]
        self._last_check_at = datetime.now(UTC)
        log.warning("claude_agent.failure", agent=self._agent_name, error=self._last_error)


__all__ = ["ClaudeAgentRunner"]
