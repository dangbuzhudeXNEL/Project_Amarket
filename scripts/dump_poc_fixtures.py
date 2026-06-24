"""一次性 dump 脚本：从 data/amarket.db 读出数据，输出到 poc/assets/data/*.json。

用法：
    uv run python scripts/dump_poc_fixtures.py
    uv run python scripts/dump_poc_fixtures.py --limit 50
    uv run python scripts/dump_poc_fixtures.py --pretty
    uv run python scripts/dump_poc_fixtures.py --db custom.db --out custom/data

M3b 接入 API 后此脚本仅用于本地 debug，不再是前端数据源。
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlmodel import Session, create_engine

from amarket.adapters.market_sources.base import MAJOR_A_SHARE_INDEXES
from amarket.domain.models import Alert, NewsAnalysis, NewsItem, NewsSource
from amarket.repositories.alert_repo import AlertRepo
from amarket.repositories.market_snapshot_repo import MarketSnapshotRepo
from amarket.repositories.news_analysis_repo import NewsAnalysisRepo
from amarket.repositories.news_repo import NewsRepo

DEFAULT_DB = "sqlite:///data/amarket.db"
DEFAULT_OUT = Path("poc/assets/data")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Dump amarket DB → POC mock JSON files.")
    p.add_argument("--db", default=DEFAULT_DB, help="SQLAlchemy URL (default: %(default)s)")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output dir (default: %(default)s)")
    p.add_argument("--limit", type=int, default=300, help="Max news items to dump")
    p.add_argument(
        "--detail-samples", type=int, default=5, help="How many news-detail-*.json to dump"
    )
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON with indent=2")
    return p.parse_args()


def write_json(path: Path, data: Any, *, pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    indent = 2 if pretty else None
    text = json.dumps(data, ensure_ascii=False, indent=indent, default=_json_default)
    path.write_text(text, encoding="utf-8")
    print(f"  ✓ wrote {path} ({len(text):,} bytes)")


def _json_default(o: Any) -> Any:
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(f"unserializable: {type(o).__name__}")


def main() -> int:
    args = parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    print(f"Connecting to {args.db} ...")
    engine = create_engine(args.db)

    with Session(engine) as session:
        print("\n=== Dumping dashboard.json ===")
        write_json(
            out / "dashboard.json",
            dump_dashboard(session, news_limit=30),
            pretty=args.pretty,
        )

        print("\n=== Dumping news.json ===")
        write_json(
            out / "news.json", dump_news(session, limit=args.limit), pretty=args.pretty
        )

        print(f"\n=== Dumping news-detail-*.json (top {args.detail_samples}) ===")
        for nid in dump_news_details(
            session, out, limit=args.detail_samples, pretty=args.pretty
        ):
            print(f"  ✓ news-detail-{nid}.json")

        print("\n=== Dumping alerts.json ===")
        write_json(out / "alerts.json", dump_alerts(session), pretty=args.pretty)

        print("\n=== Dumping sectors.json (M3a placeholder, M3b 接 SectorTrendService) ===")
        write_json(out / "sectors.json", dump_sectors_placeholder(), pretty=args.pretty)

        print("\n=== Dumping reports.json (M3a placeholder, M4 真填) ===")
        write_json(out / "reports.json", dump_reports_placeholder(), pretty=args.pretty)

        print("\n=== Dumping params.json (handwritten, M5 真填) ===")
        write_json(out / "params.json", dump_params_handwritten(), pretty=args.pretty)

    print("\n✅ All done.")
    return 0


# ---- 各 dump 函数 ---- #


def _news_to_card(
    session: Session,
    news: NewsItem,
    source: NewsSource,
    analysis: NewsAnalysis | None,
    alert: Alert | None,
) -> dict[str, Any]:
    """NewsItem + JOIN → 富 DTO（超过 NewsCardDTO，含 spec §10.3 全部字段）。"""
    return {
        "news_id": news.id,
        "title": news.title,
        "summary": news.summary,
        "source": source.name,
        "source_code": source.code,
        "source_priority": source.priority.value,
        "url": news.url,
        "published_at": news.published_at,
        "fetched_at": news.fetched_at,
        "primary_category": analysis.primary_category.value if analysis else None,
        "tags": analysis.tags if analysis else [],
        "sentiment": analysis.sentiment.value if analysis else None,
        "importance": analysis.importance_score if analysis else None,
        "urgency": analysis.urgency_score if analysis else None,
        "confidence": analysis.confidence_score if analysis else None,
        "impact_horizon": analysis.impact_horizon.value if analysis else None,
        "action_hint": analysis.action_hint.value if analysis else None,
        "related_sectors": analysis.related_sectors if analysis else [],
        "related_symbols": analysis.related_symbols if analysis else [],
        "alert_level": alert.level.value if alert else None,
        "pushed": (alert.status == "pushed") if alert else False,
        "processed_by": analysis.processed_by if analysis else None,
    }


def _highest_alert(alerts: list[Alert]) -> Alert | None:
    if not alerts:
        return None
    priority = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    return sorted(alerts, key=lambda a: priority.get(a.level.value, 99))[0]


def _pick_best_analysis(analyses: list[NewsAnalysis]) -> NewsAnalysis | None:
    """优先取 agent:* / sdk:* 分析，无则 rule，最新优先。"""
    if not analyses:
        return None
    return sorted(
        analyses,
        key=lambda a: (
            0 if a.processed_by.startswith(("agent:", "sdk:")) else 1,
            -(a.id or 0),
        ),
    )[0]


def _alert_to_dict(session: Session, alert: Alert) -> dict[str, Any]:
    title = source_name = category = None
    if alert.news_id is not None:
        news = session.get(NewsItem, alert.news_id)
        if news is not None:
            title = news.title
            src = session.get(NewsSource, news.source_id)
            if src is not None:
                source_name = src.name
    if alert.analysis_id is not None:
        ana = session.get(NewsAnalysis, alert.analysis_id)
        if ana is not None:
            category = ana.primary_category.value
    return {
        "alert_id": alert.id,
        "news_id": alert.news_id,
        "level": alert.level.value,
        "trigger_reason": alert.trigger_reason,
        "analysis_id": alert.analysis_id,
        "status": alert.status,
        "created_at": alert.created_at,
        "pushed_at": alert.pushed_at,
        "news_title": title,
        "news_source": source_name,
        "primary_category": category,
    }


def dump_dashboard(session: Session, *, news_limit: int) -> dict[str, Any]:
    market_repo = MarketSnapshotRepo(session)
    alert_repo = AlertRepo(session)

    # market_status — 拿 11 个 A 股指数最新
    latest = market_repo.latest_for_codes(list(MAJOR_A_SHARE_INDEXES.keys()))
    indexes = []
    for code, name in MAJOR_A_SHARE_INDEXES.items():
        snap = latest.get(code)
        if snap is None:
            continue
        extra = snap.extra_json if isinstance(snap.extra_json, dict) else {}
        indexes.append(
            {
                "code": code,
                "name": snap.name or name,
                "price": snap.price,
                "change_pct": snap.change_pct,
                "change_abs": snap.change_abs,
                "prev_close": extra.get("prev_close"),
                "volume": snap.volume,
                "turnover": snap.turnover,
                "source": str(extra.get("source", "akshare")),
                "fetched_at": snap.ts,
            }
        )

    # latest_news
    latest_news = dump_news(session, limit=news_limit)

    # P0 / P1 alerts
    recent = alert_repo.list_recent(limit=200)
    p0_list = [_alert_to_dict(session, a) for a in recent if a.level.value == "P0"][:10]
    p1_list = [_alert_to_dict(session, a) for a in recent if a.level.value == "P1"][:10]

    return {
        "as_of": datetime.now(UTC),
        "market_status": {
            "indexes": indexes,
            "fx": [],
            "commodities": [],
            "refreshed_at": datetime.now(UTC),
        },
        "today_conclusion": "（M3a 占位 — M4 接盘前日报）",
        "latest_news": latest_news,
        "p0_alerts": p0_list,
        "p1_alerts": p1_list,
        "top_sectors": [],  # M3b 接 SectorTrendService
        "top_movers": [],  # M3b 接
        "today_reports": {  # M4 真填
            "premarket": None,
            "morning": None,
            "noon": None,
            "afternoon": None,
            "close": None,
            "evening": None,
        },
    }


def dump_news(session: Session, *, limit: int) -> list[dict[str, Any]]:
    repo = NewsRepo(session)
    analysis_repo = NewsAnalysisRepo(session)
    alert_repo = AlertRepo(session)

    rows = repo.list_recent(limit=limit)
    result: list[dict[str, Any]] = []
    for news, src in rows:
        assert news.id is not None
        analyses = analysis_repo.list_for_news(news_id=news.id)
        ana = _pick_best_analysis(analyses)
        alerts = alert_repo.list_for_news(news_id=news.id, limit=10)
        alt = _highest_alert(alerts)
        result.append(_news_to_card(session, news, src, ana, alt))
    return result


def dump_news_details(
    session: Session, out: Path, *, limit: int, pretty: bool
) -> list[int]:
    """Dump top N news 的详情（含 related_news 同事件其他 news）到独立文件。"""
    from sqlmodel import select

    repo = NewsRepo(session)
    analysis_repo = NewsAnalysisRepo(session)
    alert_repo = AlertRepo(session)

    rows = repo.list_recent(limit=limit)
    written: list[int] = []
    for news, src in rows:
        assert news.id is not None
        analyses = analysis_repo.list_for_news(news_id=news.id)
        ana = _pick_best_analysis(analyses)
        alerts = alert_repo.list_for_news(news_id=news.id, limit=10)
        alt = _highest_alert(alerts)
        card = _news_to_card(session, news, src, ana, alt)

        related: list[dict[str, Any]] = []
        if news.event_id is not None:
            stmt = (
                select(NewsItem, NewsSource)
                .join(NewsSource, NewsItem.source_id == NewsSource.id)  # type: ignore[arg-type]
                .where(NewsItem.event_id == news.event_id)
                .where(NewsItem.id != news.id)
                .limit(10)
            )
            for r_news, r_src in session.exec(stmt):
                related.append(
                    {
                        "news_id": r_news.id,
                        "title": r_news.title,
                        "source": r_src.name,
                        "published_at": r_news.published_at,
                        "url": r_news.url,
                    }
                )
        card["related_news"] = related
        card["ai_reasoning"] = ana.ai_reasoning if ana else None
        card["risk_notes"] = ana.risk_notes if ana else None
        card["content"] = news.content

        write_json(out / f"news-detail-{news.id}.json", card, pretty=pretty)
        written.append(news.id)
    return written


def dump_alerts(session: Session) -> list[dict[str, Any]]:
    return []


def dump_sectors_placeholder() -> dict[str, Any]:
    return {}


def dump_reports_placeholder() -> dict[str, Any]:
    return {}


def dump_params_handwritten() -> list[dict[str, Any]]:
    return []


if __name__ == "__main__":
    raise SystemExit(main())
