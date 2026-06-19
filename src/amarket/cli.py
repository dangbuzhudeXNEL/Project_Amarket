"""Project_Amarket CLI（Typer）— 入口 `amarket`。

M0 命令：
- `amarket version`            打印版本与 Spec / Phase / Milestone
- `amarket healthcheck`        本地或远端调用 /healthz，pretty-print 结果
- `amarket healthcheck --json` 输出原始 JSON（便于脚本）
- `amarket db status`          打印当前 alembic head（占位实现）

后续 Milestone 会扩展 `amarket push premarket` / `amarket collect news` 等。
"""

from __future__ import annotations

import json
import sys

import httpx
import typer

from amarket import __version__
from amarket.services.config_service import get_app_config
from amarket.services.notify_test import send_test_message_sync
from amarket.services.observability import (
    get_health_report,
    iter_notifiers,
    list_notifier_channels,
)

app = typer.Typer(
    name="amarket",
    help="Project_Amarket — A 股新闻分析 + 行情看板平台 CLI（永不实盘）",
    no_args_is_help=True,
    add_completion=False,
)

db_app = typer.Typer(help="数据库管理子命令。")
app.add_typer(db_app, name="db")

notify_app = typer.Typer(help="通知渠道管理 / 测试。")
app.add_typer(notify_app, name="notify")


# --------------------------------------------------------------------------- #
# version
# --------------------------------------------------------------------------- #


@app.command()
def version() -> None:
    """打印版本与项目元信息。"""
    cfg = get_app_config()
    typer.echo(f"amarket {__version__}")
    typer.echo(f"  spec     : {cfg.project_meta.spec_version}")
    typer.echo(f"  phase    : {cfg.project_meta.current_phase}")
    typer.echo(f"  milestone: {cfg.project_meta.current_milestone}")
    typer.echo(f"  env      : {cfg.app.env}")


# --------------------------------------------------------------------------- #
# healthcheck
# --------------------------------------------------------------------------- #


@app.command()
def healthcheck(
    remote: bool = typer.Option(
        False,
        "--remote",
        help="走 HTTP 调用远端 /healthz（默认走进程内函数，便于无依赖检查）",
    ),
    as_json: bool = typer.Option(
        False,
        "--json",
        help="输出原始 JSON",
    ),
    url: str | None = typer.Option(
        None,
        "--url",
        help="自定义 healthz URL（默认按 config/app.yml 的 api.host:port 拼）",
    ),
) -> None:
    """健康检查。

    默认走进程内直接调用 `get_health_report()`（无需运行 FastAPI）。
    `--remote` 则走 HTTP 调用。
    """
    if remote:
        cfg = get_app_config()
        target = url or f"http://{cfg.api.host}:{cfg.api.port}/healthz"
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(target)
            payload = resp.json()
            exit_code = 0 if resp.status_code == 200 else 1
        except httpx.RequestError as exc:
            typer.secho(f"❌ 无法连接 {target}: {exc}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=2) from exc
    else:
        report = get_health_report()
        payload = report.model_dump(mode="json")
        exit_code = 0 if report.status != "unhealthy" else 1

    if as_json:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _pretty_print_health(payload)

    raise typer.Exit(code=exit_code)


def _pretty_print_health(payload: dict[str, object]) -> None:
    status = str(payload.get("status", "unknown"))
    icon = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "❌"}.get(status, "❓")
    typer.echo(f"{icon} status: {status}")
    typer.echo(f"  uptime: {payload.get('uptime_seconds')}s")

    meta = payload.get("project_meta") or {}
    if isinstance(meta, dict):
        typer.echo("  project:")
        for key, value in meta.items():
            typer.echo(f"    {key}: {value}")

    checks = payload.get("checks") or {}
    if isinstance(checks, dict):
        typer.echo("  checks:")
        for name, info in checks.items():
            if not isinstance(info, dict):
                continue
            sub_status = str(info.get("status", "?"))
            sub_icon = {"ok": "✓", "degraded": "~", "down": "✗"}.get(sub_status, "?")
            extras: list[str] = []
            if (latency := info.get("latency_ms")) is not None:
                extras.append(f"{latency}ms")
            if detail := info.get("detail"):
                extras.append(str(detail)[:80])
            extra_str = (" — " + " | ".join(extras)) if extras else ""
            typer.echo(f"    {sub_icon} {name}: {sub_status}{extra_str}")

    notifiers = payload.get("notifiers") or {}
    if isinstance(notifiers, dict) and notifiers:
        typer.echo("  notifiers:")
        for name, info in notifiers.items():
            if not isinstance(info, dict):
                continue
            sub_status = str(info.get("status", "?"))
            sub_icon = {"ok": "🟢", "degraded": "🟡", "down": "🔴", "disabled": "⚪"}.get(
                sub_status, "❓"
            )
            typer.echo(f"    {sub_icon} {name}: {sub_status}")


# --------------------------------------------------------------------------- #
# db status
# --------------------------------------------------------------------------- #


@db_app.command("status")
def db_status() -> None:
    """打印当前数据库连接状态（M0 占位；M1 起接 alembic current）。"""
    try:
        report = get_health_report()
    except Exception as exc:  # pragma: no cover
        typer.secho(f"❌ 健康检查失败: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    db_check = report.checks.get("db")
    if db_check is None:
        typer.secho("❓ 未注册 db 健康检查", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)

    icon = {"ok": "✅", "degraded": "⚠️", "down": "❌"}.get(db_check.status, "❓")
    typer.echo(f"{icon} db: {db_check.status}")
    if db_check.latency_ms is not None:
        typer.echo(f"  latency: {db_check.latency_ms}ms")
    if db_check.detail:
        typer.echo(f"  detail : {db_check.detail}")


# --------------------------------------------------------------------------- #
# notify status / test
# --------------------------------------------------------------------------- #


@notify_app.command("status")
def notify_status() -> None:
    """列出所有通知渠道及配置状态。"""
    configured = dict(iter_notifiers())
    all_channels = list_notifier_channels()
    if not all_channels:
        typer.secho("（无已知 channel）", fg=typer.colors.YELLOW)
        raise typer.Exit(code=0)

    for channel in all_channels:
        if channel in configured:
            h = configured[channel].health_check()
            icon = {"ok": "🟢", "degraded": "🟡", "down": "🔴", "disabled": "⚪"}.get(
                h.status, "❓"
            )
            extra = f" — last_error: {h.last_error}" if h.last_error else ""
            typer.echo(f"{icon} {channel}: {h.status} (configured){extra}")
        else:
            typer.echo(f"⚪ {channel}: not configured")


@notify_app.command("test")
def notify_test(
    channel: str = typer.Argument(
        ...,
        help="渠道：wework | wework_alert | lark | all",
    ),
) -> None:
    """发送一条测试消息验证 webhook 配置。

    示例:
        amarket notify test wework
        amarket notify test all
    """
    targets: list[str] = list_notifier_channels() if channel == "all" else [channel]

    exit_code = 0
    for target in targets:
        typer.echo(f"→ 发送测试到 {target}...")
        result = send_test_message_sync(target)
        if result.ok:
            ts = result.sent_at.strftime("%H:%M:%S UTC")
            typer.secho(f"  ✅ {target}: ok @ {ts}", fg=typer.colors.GREEN)
        else:
            typer.secho(f"  ❌ {target}: {result.error}", fg=typer.colors.RED)
            exit_code = 1

    raise typer.Exit(code=exit_code)


def main() -> None:
    """python -m amarket.cli 入口。"""
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
    sys.exit(0)
