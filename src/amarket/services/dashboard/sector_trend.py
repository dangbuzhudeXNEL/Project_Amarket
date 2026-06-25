"""SectorTrendService — 板块趋势看板服务（M3b Phase 1 简化版）。

Spec v3 §6.1.7：综合行情 + 新闻热度 + 情绪 + 资金状态计算板块趋势判断。

M3b 简化范围：
- `news_count_24h`：从 NewsAnalysis.related_sectors 反查（窗口内匹配该板块的条数）
- `change_pct`：M3b Phase 1 留 None；若 SectorTrend 表里有最近 4h 内的记录则用表里值
- `market_cap_weight`：14 板块的粗略 stub 映射（M5 参数模块上线后由参数覆写）
- `top_symbols`：M3b 留空 list（M4 行情聚合填）

M4+ 将加：APScheduler 任务每 15 分钟刷 SectorTrend 表；行情接入后 change_pct 真填。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from amarket.core.logging import get_logger
from amarket.domain.models import NewsAnalysis, NewsItem
from amarket.domain.schemas import SectorDTO
from amarket.repositories.sector_trend_repo import SectorTrendRepo

log = get_logger(__name__)


# 14 个 A 股主板块（与 M3a dump_sectors_placeholder 对齐）。
DEFAULT_SECTOR_NAMES: list[str] = [
    "券商",
    "银行",
    "保险",
    "半导体",
    "新能源",
    "医药",
    "白酒",
    "地产链",
    "煤炭",
    "钢铁",
    "军工",
    "通信",
    "传媒",
    "AI",
]

# Stub 市值权重（M3b 静态值，M5 参数模块上线后由 params.sectors.<name>.market_cap_weight 覆写）。
# 14 个权重总和 ≈ 1.0（粗估）。
_SECTOR_CAP_WEIGHTS: dict[str, float] = {
    "券商": 0.07,
    "银行": 0.12,
    "保险": 0.05,
    "半导体": 0.10,
    "新能源": 0.09,
    "医药": 0.08,
    "白酒": 0.06,
    "地产链": 0.06,
    "煤炭": 0.04,
    "钢铁": 0.04,
    "军工": 0.05,
    "通信": 0.07,
    "传媒": 0.05,
    "AI": 0.12,
}

# 当 SectorTrend 表里数据 > 这个时长就视为过期，不使用其 change_pct。
_SECTOR_TREND_FRESHNESS = timedelta(hours=4)


class SectorTrendService:
    """板块趋势查询服务（聚合 NewsAnalysis + SectorTrend 表）。"""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._sector_repo = SectorTrendRepo(session)

    def list_sectors(
        self,
        *,
        window: timedelta = timedelta(days=1),
        sector_names: list[str] | None = None,
    ) -> list[SectorDTO]:
        """返回所有（或指定）板块的看板 DTO 列表。

        - news_count_24h：window 内 NewsAnalysis.related_sectors 命中该板块的条数
        - change_pct：取 SectorTrend 表里最近 _SECTOR_TREND_FRESHNESS 内最新一条；否则 None
        - market_cap_weight：来自 _SECTOR_CAP_WEIGHTS stub
        - top_symbols：M3b 留空
        """
        names = sector_names if sector_names is not None else DEFAULT_SECTOR_NAMES
        heat_by_name = self._compute_news_heat(names, window=window)
        change_by_name = self._latest_change_pct(names)

        result: list[SectorDTO] = []
        for name in names:
            result.append(
                SectorDTO(
                    name=name,
                    change_pct=change_by_name.get(name),
                    news_count_24h=heat_by_name.get(name, 0),
                    market_cap_weight=_SECTOR_CAP_WEIGHTS.get(name),
                    top_symbols=[],
                )
            )
        return result

    def top_n(
        self,
        *,
        by: str = "news_heat",
        n: int = 10,
        window: timedelta = timedelta(days=1),
    ) -> list[SectorDTO]:
        """按 'news_heat' | 'change_pct' | 'market_cap_weight' 排序取前 n。"""
        sectors = self.list_sectors(window=window)
        if by == "news_heat":
            sectors.sort(key=lambda s: s.news_count_24h, reverse=True)
        elif by == "change_pct":
            sectors.sort(key=lambda s: s.change_pct or 0.0, reverse=True)
        elif by == "market_cap_weight":
            sectors.sort(key=lambda s: s.market_cap_weight or 0.0, reverse=True)
        else:
            log.warning("sector.top_n.unknown_by", by=by)
        return sectors[:n]

    # ----------------- 内部 ----------------- #

    def _compute_news_heat(
        self,
        sector_names: list[str],
        *,
        window: timedelta,
    ) -> dict[str, int]:
        """从 NewsAnalysis.related_sectors 反查每个板块的命中条数。

        SQLite JSON 字段不支持 ->> 查询，所以拉所有 window 内 analyses 在 Python 里聚合。
        实际数据量（M3b 数百到数千条）下完全 OK；M4+ 需要时再优化为 SQL JSON_EXTRACT。
        """
        since = datetime.now(UTC) - window
        stmt = (
            select(NewsAnalysis)
            .join(NewsItem, NewsItem.id == NewsAnalysis.news_id)  # type: ignore[arg-type]
            .where(NewsItem.published_at >= since)
        )
        counts: dict[str, int] = dict.fromkeys(sector_names, 0)
        target = set(sector_names)
        for ana in self._session.exec(stmt):
            for s in ana.related_sectors or []:
                if isinstance(s, dict):
                    name = s.get("name")
                    if isinstance(name, str) and name in target:
                        counts[name] += 1
        return counts

    def _latest_change_pct(self, sector_names: list[str]) -> dict[str, float | None]:
        """从 SectorTrend 表读最新 change_pct（如果 < freshness 阈值）。"""
        latest = self._sector_repo.latest_for_sectors(sector_names)
        cutoff = datetime.now(UTC) - _SECTOR_TREND_FRESHNESS
        result: dict[str, float | None] = {}
        for name, row in latest.items():
            ts = row.ts
            # row.ts 来自 SQLite 可能是 naive；统一按 UTC 比较
            ts_aware = ts if ts.tzinfo else ts.replace(tzinfo=UTC)
            if ts_aware >= cutoff and row.change_pct is not None:
                result[name] = row.change_pct
        return result


__all__ = ["DEFAULT_SECTOR_NAMES", "SectorTrendService"]
