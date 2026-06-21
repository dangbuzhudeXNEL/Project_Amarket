"""Project_Amarket CLI（Typer）— 入口 `amarket`。

M0/M1 命令：
- `amarket version`            打印版本与 Spec / Phase / Milestone
- `amarket healthcheck`        本地或远端调用 /healthz
- `amarket db status`          打印当前数据库连接状态
- `amarket notify status/test` 通知渠道管理
- `amarket collect news`       拉取所有 enabled 新闻源最新批次
- `amarket collect market`     拉取主要指数快照写入 market_snapshots

后续 Milestone 会扩展 `amarket push premarket` / `amarket report generate` 等。
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import sys

import httpx
import typer

from amarket import __version__
from amarket.adapters.market_sources.akshare_source import AkshareSource
from amarket.db.session import session_scope
from amarket.services.config_service import get_app_config
from amarket.services.dashboard.market_data import MarketDataService
from amarket.services.news.collector import NewsCollector, build_default_sources
from amarket.services.notify_test import send_test_message_sync
from amarket.services.observability import (
    get_health_report,
    iter_notifiers,
    list_notifier_channels,
)


def _ensure_utf8_streams() -> None:
    """Windows console: 强制 stdout/stderr UTF-8，否则中文 / emoji 输出会挂（cp1252）。"""
    for _stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, OSError):
            _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]


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

collect_app = typer.Typer(help="数据采集 — 触发新闻 / 行情入库。")
app.add_typer(collect_app, name="collect")

dedupe_app = typer.Typer(help="新闻去重 — L1 URL / L2 标题 / L3 SimHash 三层 + 事件聚合。")
app.add_typer(dedupe_app, name="dedupe")


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


# --------------------------------------------------------------------------- #
# collect news / market
# --------------------------------------------------------------------------- #


@collect_app.command("news")
def collect_news(
    full: bool = typer.Option(
        False,
        "--full",
        help="拉过去 12h（默认仅 realtime ~5min）",
    ),
) -> None:
    """从所有已配置的新闻源拉一批入库。

    M1 默认 3 个源：东方财富 7x24（主） + 新浪 7x24（备） + 雅虎 RSS（备）。
    单源失败不影响其他；详细结果按源分行输出。
    """
    from datetime import UTC, datetime, timedelta

    sources = build_default_sources()
    typer.echo(f"→ 启动 collector，{len(sources)} 个源：{[s.code for s in sources]}")

    with session_scope() as session:
        collector = NewsCollector(sources, session)
        if full:
            since = datetime.now(UTC) - timedelta(hours=12)
            report = asyncio.run(collector.collect_since(since))
        else:
            report = asyncio.run(collector.collect_realtime())

    duration = (report.finished_at - report.started_at).total_seconds()
    typer.echo("")
    typer.echo(f"采集完成 ({duration:.1f}s)：")
    for r in report.per_source:
        if r.success:
            typer.secho(
                f"  ✅ {r.code:12s} fetched={r.fetched:>3d} inserted={r.inserted:>3d} "
                f"skipped={r.skipped:>3d} latency={r.latency_ms:.0f}ms",
                fg=typer.colors.GREEN,
            )
        else:
            typer.secho(
                f"  ❌ {r.code:12s} ERROR: {r.error}",
                fg=typer.colors.RED,
            )

    typer.echo("")
    typer.echo(f"汇总：fetched={report.total_fetched}, inserted={report.total_inserted}")
    if report.failed_sources:
        typer.secho(f"  失败源：{report.failed_sources}", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)


@collect_app.command("market")
def collect_market() -> None:
    """拉一次主要 A 股指数快照写入 market_snapshots 表。

    M4+ 起会改成 APScheduler 定时任务。
    """
    typer.echo("→ 拉取 A 股主要指数（akshare）...")
    source = AkshareSource()
    service = MarketDataService(source)

    snapshots = asyncio.run(service.get_index_snapshots())
    if not snapshots:
        typer.secho("❌ 未拿到任何指数数据（akshare 端点可能挂了）", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    with session_scope() as session:
        inserted = service.persist_snapshots(snapshots, session)

    typer.echo("")
    for s in snapshots:
        sign = "+" if (s.change_pct or 0) >= 0 else ""
        change = f"{sign}{s.change_pct:.2f}%" if s.change_pct is not None else "n/a"
        typer.echo(f"  {s.code:10s} {s.name:8s} {s.price:>10.2f}  {change}")

    typer.secho(f"\n✅ 入库 {inserted} 条快照", fg=typer.colors.GREEN)


# --------------------------------------------------------------------------- #
# dedupe news（M2-b）
# --------------------------------------------------------------------------- #


@dedupe_app.command("news")
def dedupe_news(
    limit: int = typer.Option(500, "--limit", help="处理最近多少条未去重的新闻"),
    lookback_hours: int = typer.Option(
        24, "--lookback-hours", help="L2/L3 候选事件回看窗口（小时）"
    ),
    threshold: int = typer.Option(3, "--threshold", help="SimHash 距离阈值"),
) -> None:
    """对 news_items.event_id IS NULL 的条目跑 3 层去重 + 写 news_events。

    示例:
        amarket dedupe news                          # 默认 500 条 / 24h / 阈值 3
        amarket dedupe news --limit 1000             # 处理更多
        amarket dedupe news --threshold 8            # 放宽 L3（更激进合并）
    """
    from amarket.repositories.news_repo import NewsRepo
    from amarket.services.news.deduper import NewsDeduper

    with session_scope() as session:
        news_repo = NewsRepo(session)
        candidates = news_repo.list_without_event(limit=limit)
        if not candidates:
            typer.secho(
                "✅ 没有待去重的新闻（所有 news_items.event_id 已分配）", fg=typer.colors.GREEN
            )
            raise typer.Exit(code=0)

        typer.echo(
            f"→ 找到 {len(candidates)} 条待去重新闻，"
            f"threshold={threshold} lookback={lookback_hours}h"
        )

        deduper = NewsDeduper(
            session,
            simhash_threshold=threshold,
            lookback_hours=lookback_hours,
        )
        result = deduper.dedupe_batch(candidates)

    typer.echo("")
    typer.secho("去重完成：", fg=typer.colors.GREEN)
    typer.echo(f"  total                 : {result.total}")
    typer.echo(f"  new events            : {result.new_events}")
    typer.echo(f"  merged into existing  : {result.merged_into_existing}")
    typer.echo(f"  skipped (already set) : {result.skipped_already_event}")
    typer.echo(f"  events touched        : {len(result.events_touched)}")
    if result.total > 0:
        ratio = (result.new_events + result.merged_into_existing) / result.total
        typer.echo(f"  processing ratio      : {ratio:.1%}")


def main() -> None:
    """python -m amarket.cli 入口。"""
    _ensure_utf8_streams()
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
    sys.exit(0)
