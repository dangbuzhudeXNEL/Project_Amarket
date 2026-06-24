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


# ---- 各 dump 函数（骨架，下个 task 填充）---- #


def dump_dashboard(session: Session, *, news_limit: int) -> dict[str, Any]:
    return {}


def dump_news(session: Session, *, limit: int) -> list[dict[str, Any]]:
    return []


def dump_news_details(
    session: Session, out: Path, *, limit: int, pretty: bool
) -> list[int]:
    return []


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
