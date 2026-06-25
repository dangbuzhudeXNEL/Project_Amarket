# M3b — Dashboard API 补齐 + 前端 fetch 切真 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 M3a POC 6 个页面从读 mock JSON 改为读真实 FastAPI 端点；新增 5 类后端聚合/资源端点 + 1 个板块趋势 Service + 2 个新 Repo；前端加 30s polling toggle + FastAPI 同源 mount。

**Architecture:**
- 后端：新增 2 个 Repository（`ReportRepo`、`SectorTrendRepo`），1 个 Service（`SectorTrendService` Phase 1 简化版，从 `news_analysis.related_sectors` 反查新闻热度，`change_pct` Phase 1 留 `None`，等 M4 调度填表），1 个新 router（`reports.py`），扩 `dashboard.py` 加 `summary/sectors/movers` 3 端点；`main.py` 加 `StaticFiles` 把 `poc/` 挂到 `/poc`。
- 前端：`shared.js` 加 `startAutoRefresh(intervalMs, fn)`，`nav.js` 把占位 LIVE 改成可点 polling toggle（状态持久化到 localStorage），5 个 page JS 每个把 `assets/data/X.json` 一行改成 `/api/X`。
- 测试：TDD 模式 — 每个 Repo / Service / endpoint 先写失败测试再实现；复用 `tests/conftest.py` 的 `api_client / session / patched_engine` fixtures。

**Tech Stack:** FastAPI 0.115+, SQLModel 0.0.22+, Pydantic 2.x, pytest, structlog（沿用 M0-M2 的栈，0 新依赖）；前端 Tailwind+Alpine+ECharts CDN 不变。

---

## File Structure

### Backend — Create

| Path | 责任 |
|------|------|
| `src/amarket/repositories/report_repo.py` | Report 表 CRUD：`list_recent`, `get`, `today_by_kind`, `list_today` |
| `src/amarket/repositories/sector_trend_repo.py` | SectorTrend 表 CRUD：`bulk_upsert`, `latest_for_sectors` |
| `src/amarket/services/dashboard/sector_trend.py` | `SectorTrendService` — Phase 1 简化版：news_heat 从 NewsAnalysis 反查；change_pct/sentiment_score 等 M4 才填；提供 `list_sectors`、`top_n` 给 API 调用 |
| `src/amarket/api/reports.py` | `/api/reports` router：list / detail / today/{kind} 3 端点 |
| `tests/unit/test_report_repo.py` | ReportRepo 单测 |
| `tests/unit/test_sector_trend_repo.py` | SectorTrendRepo 单测 |
| `tests/unit/test_sector_trend_service.py` | SectorTrendService 单测 |
| `tests/unit/test_api_reports.py` | `/api/reports/*` API 集成测试 |
| `tests/unit/test_api_dashboard_m3b.py` | `/api/dashboard/summary|sectors|movers` 集成测试（新文件，不污染已有 test_api_news_dashboard.py） |
| `tests/unit/test_static_poc_mount.py` | `/poc/index.html` mount smoke test |

### Backend — Modify

| Path | 修改 |
|------|------|
| `src/amarket/domain/schemas.py` | 加 `SectorDTO`、`SectorListResponse`、`MoverDTO`、`MoversListResponse`、`ReportSummaryDTO`、`ReportDetailDTO`、`ReportListResponse`、`TodayReportsResponse`、`DashboardSummary` |
| `src/amarket/api/dashboard.py` | 加 `GET /summary`、`GET /sectors`、`GET /movers` 3 个 endpoint |
| `src/amarket/main.py` | `include_router(reports.router)` + `app.mount("/poc", StaticFiles(...))` |

### Frontend — Modify (1 行 fetch URL 改动 + polling 基础设施)

| Path | 修改 |
|------|------|
| `poc/assets/js/shared.js` | 加 `startAutoRefresh(intervalMs, fn)` + `setPollingEnabled(bool)` + `isPollingEnabled()` |
| `poc/assets/js/nav.js` | LIVE 改成可点 toggle，调用 polling API |
| `poc/assets/js/pages/index.js` | `assets/data/*.json` → `/api/*` |
| `poc/assets/js/pages/news.js` | 同上 |
| `poc/assets/js/pages/news-detail.js` | `assets/data/news-detail-${id}.json` → `/api/news/${id}` |
| `poc/assets/js/pages/sectors.js` | 同上 |
| `poc/assets/js/pages/reports.js` | 同上 |

---

## Task 1: 准备分支 + 验证 main 干净

**Files:**
- (no code changes)

- [ ] **Step 1: 验证 main 干净**

```bash
git -C C:/AI/Claude/Project_Amarket status
git -C C:/AI/Claude/Project_Amarket log --oneline -3
```

Expected:
```
On branch main
Your branch is up to date with 'origin/main'.
nothing to commit, working tree clean
```
最新 commit 是 `eeb4f5d docs(readme): 同步 M3a 完成状态…`。

- [ ] **Step 2: 拉远端最新**

```bash
git -C C:/AI/Claude/Project_Amarket pull --ff-only origin main
```

Expected: `Already up to date.`

- [ ] **Step 3: 开 feat 分支**

```bash
git -C C:/AI/Claude/Project_Amarket checkout -b feat/m3b-dashboard-api
```

Expected: `Switched to a new branch 'feat/m3b-dashboard-api'`

- [ ] **Step 4: 把本 plan 加进 git（plan 本身先 commit）**

```bash
git -C C:/AI/Claude/Project_Amarket add docs/superpowers/plans/2026-06-25-m3b-dashboard-api.md
git -C C:/AI/Claude/Project_Amarket commit -m "docs(plan): add M3b dashboard API + frontend wiring plan"
```

---

## Task 2: 新 DTO — schemas.py 加 M3b 需要的 9 个 Pydantic 模型

**Files:**
- Modify: `src/amarket/domain/schemas.py` (append at bottom before `__all__`)
- Test: `tests/unit/test_repositories.py`（已有 test_repositories.py；这里加一个 schema smoke 测试到 `tests/unit/test_models.py`）

- [ ] **Step 1: 写失败测试 — schema 实例化 + 序列化**

Append to `tests/unit/test_models.py` (末尾，`__all__` 之前如有则之前否则文件尾):

```python
# --------------------------------------------------------------------------- #
# M3b — Dashboard / Sector / Mover / Report DTOs
# --------------------------------------------------------------------------- #


def test_m3b_dtos_instantiate_and_serialize() -> None:
    """M3b 新增 9 个 DTO 都能实例化 + .model_dump_json() 不崩。"""
    from datetime import UTC, date, datetime

    from amarket.domain.schemas import (
        DashboardSummary,
        MoverDTO,
        MoversListResponse,
        ReportDetailDTO,
        ReportListResponse,
        ReportSummaryDTO,
        SectorDTO,
        SectorListResponse,
        TodayReportsResponse,
    )

    sector = SectorDTO(
        name="券商",
        change_pct=1.5,
        news_count_24h=12,
        market_cap_weight=0.07,
        top_symbols=[],
    )
    SectorListResponse(as_of=datetime.now(UTC), window="1d", sectors=[sector])

    mover = MoverDTO(code="600000", name="浦发银行", change_pct=2.1, price=10.5)
    MoversListResponse(as_of=datetime.now(UTC), top_gainers=[mover], top_losers=[])

    rsum = ReportSummaryDTO(
        report_id=1,
        date=date(2026, 6, 25),
        kind="premarket",
        status="completed",
        generated_by="agent:daily-report-writer",
        generated_at=datetime.now(UTC),
    )
    ReportListResponse(items=[rsum], total=1, offset=0, limit=50)

    detail = ReportDetailDTO(
        report_id=1,
        date=date(2026, 6, 25),
        kind="premarket",
        status="completed",
        markdown="## H",
        content_json={"x": 1},
        generated_by="agent",
        generated_at=datetime.now(UTC),
    )
    TodayReportsResponse(
        today=date(2026, 6, 25),
        reports_by_kind={"premarket": detail, "morning": None},
    )

    summary = DashboardSummary(
        as_of=datetime.now(UTC),
        market_status={"indexes": [], "fx": [], "commodities": []},
        today_conclusion=None,
        latest_news=[],
        p0_alerts=[],
        p1_alerts=[],
        top_sectors=[sector],
        top_movers=[mover],
        today_reports={"premarket": None, "morning": None, "noon": None,
                       "afternoon": None, "close": None, "evening": None},
    )
    # JSON 序列化不崩
    assert summary.model_dump_json()
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
uv run pytest tests/unit/test_models.py::test_m3b_dtos_instantiate_and_serialize -v
```

Expected: `ImportError` 或 `cannot import name 'SectorDTO' from 'amarket.domain.schemas'`。

- [ ] **Step 3: 在 schemas.py 加 9 个 DTO**

Append to `src/amarket/domain/schemas.py` 在 `__all__` **之前**：

```python
# --------------------------------------------------------------------------- #
# Sector DTOs（M3b）
# --------------------------------------------------------------------------- #


class SectorDTO(BaseModel):
    """单个板块的看板数据（Spec v3 §10.3 / M3a POC sectors.json 对齐）。"""

    name: str
    change_pct: float | None = None  # M3b Phase 1：None 占位，M4 真填
    news_count_24h: int = 0
    market_cap_weight: float | None = None  # M3b stub mapping
    top_symbols: list[dict[str, Any]] = Field(default_factory=list)


class SectorListResponse(BaseModel):
    """`GET /api/dashboard/sectors` 响应。"""

    as_of: datetime = Field(default_factory=lambda: datetime.now(UTC))
    window: str = "1d"  # '1h' | '4h' | '1d'
    sectors: list[SectorDTO] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Mover DTOs（M3b — 个股异动榜）
# --------------------------------------------------------------------------- #


class MoverDTO(BaseModel):
    code: str
    name: str | None = None
    change_pct: float | None = None
    price: float | None = None
    volume: float | None = None
    turnover: float | None = None


class MoversListResponse(BaseModel):
    """`GET /api/dashboard/movers` 响应。"""

    as_of: datetime = Field(default_factory=lambda: datetime.now(UTC))
    top_gainers: list[MoverDTO] = Field(default_factory=list)
    top_losers: list[MoverDTO] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Report DTOs（M3b — 6 时段日报）
# --------------------------------------------------------------------------- #


class ReportSummaryDTO(BaseModel):
    """`GET /api/reports` 列表项（不含 markdown 全文）。"""

    report_id: int
    date: date  # noqa: A003 — 与 spec/前端字段名一致
    kind: str  # 'premarket' | 'morning' | 'noon' | 'afternoon' | 'close' | 'evening'
    status: str  # 'pending' | 'completed' | 'failed'
    generated_by: str | None = None
    generated_at: datetime
    push_count: int = 0


class ReportDetailDTO(BaseModel):
    """`GET /api/reports/{id}` + `/today/{kind}` 响应（含 markdown 全文）。"""

    report_id: int
    date: date  # noqa: A003
    kind: str
    status: str
    markdown: str | None = None
    content_json: dict[str, Any] = Field(default_factory=dict)
    generated_by: str | None = None
    generated_at: datetime
    push_count: int = 0


class ReportListResponse(BaseModel):
    items: list[ReportSummaryDTO]
    total: int
    offset: int
    limit: int


class TodayReportsResponse(BaseModel):
    """`GET /api/reports/today` — 今日 6 时段（缺失为 None）。"""

    today: date
    reports_by_kind: dict[str, ReportDetailDTO | None] = Field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Dashboard Summary（M3b — 首页聚合）
# --------------------------------------------------------------------------- #


class DashboardSummary(BaseModel):
    """`GET /api/dashboard/summary` — 首页一次性聚合（前端 index.html 用）。"""

    as_of: datetime = Field(default_factory=lambda: datetime.now(UTC))
    market_status: dict[str, Any] = Field(default_factory=dict)
    today_conclusion: str | None = None
    latest_news: list[NewsCardDTO] = Field(default_factory=list)
    p0_alerts: list[AlertDTO] = Field(default_factory=list)
    p1_alerts: list[AlertDTO] = Field(default_factory=list)
    top_sectors: list[SectorDTO] = Field(default_factory=list)
    top_movers: list[MoverDTO] = Field(default_factory=list)
    today_reports: dict[str, ReportDetailDTO | None] = Field(default_factory=dict)
```

也要把 `date` 加到顶部 import：检查文件顶部已有 `from datetime import UTC, date, datetime` —— 已存在，不用改。

把 9 个新类加进 `__all__`：

```python
__all__ = [
    "AlertDTO",
    "AlertListResponse",
    "DashboardSummary",
    "IndexSnapshot",
    "MarketStatusBar",
    "MoverDTO",
    "MoversListResponse",
    "NewsCardDTO",
    "NewsListResponse",
    "NewsSourceDTO",
    "RawNewsItem",
    "ReportDetailDTO",
    "ReportListResponse",
    "ReportSummaryDTO",
    "SectorDTO",
    "SectorListResponse",
    "TodayReportsResponse",
]
```

- [ ] **Step 4: 跑测试确认 pass**

```bash
uv run pytest tests/unit/test_models.py::test_m3b_dtos_instantiate_and_serialize -v
```

Expected: `1 passed`。

- [ ] **Step 5: ruff + mypy**

```bash
uv run ruff check src/amarket/domain/schemas.py tests/unit/test_models.py
uv run mypy src/amarket/domain/schemas.py
```

Expected: 0 errors。

- [ ] **Step 6: commit**

```bash
git -C C:/AI/Claude/Project_Amarket add src/amarket/domain/schemas.py tests/unit/test_models.py
git -C C:/AI/Claude/Project_Amarket commit -m "feat(m3b): add 9 DTOs for sectors/movers/reports/summary"
```

---

## Task 3: ReportRepo

**Files:**
- Create: `src/amarket/repositories/report_repo.py`
- Create: `tests/unit/test_report_repo.py`

- [ ] **Step 1: 写失败测试**

`tests/unit/test_report_repo.py`：

```python
"""ReportRepo 单测（M3b）。"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from sqlmodel import Session

from amarket.domain.enums import ReportKind
from amarket.domain.models import Report
from amarket.repositories.report_repo import ReportRepo


@pytest.fixture
def seed_reports(session: Session) -> list[int]:
    """seed 3 reports：今日 premarket + 今日 morning + 昨日 close。"""
    today = datetime.now(UTC).date()
    yesterday = date(today.year, today.month, today.day - 1) if today.day > 1 else today

    rows = [
        Report(
            date=today,
            kind=ReportKind.PREMARKET,
            status="completed",
            markdown="## 盘前\n- A",
            generated_by="agent:daily-report-writer",
            generated_at=datetime.now(UTC),
        ),
        Report(
            date=today,
            kind=ReportKind.MORNING,
            status="completed",
            markdown="## 早盘",
            generated_by="agent:daily-report-writer",
            generated_at=datetime.now(UTC),
        ),
        Report(
            date=yesterday,
            kind=ReportKind.CLOSE,
            status="completed",
            markdown="## 收盘",
            generated_by="agent:daily-report-writer",
            generated_at=datetime.now(UTC),
        ),
    ]
    session.add_all(rows)
    session.commit()
    for r in rows:
        session.refresh(r)
    ids = [r.id for r in rows]
    assert all(i is not None for i in ids)
    return [i for i in ids if i is not None]


def test_list_recent_returns_descending(session: Session, seed_reports: list[int]) -> None:
    repo = ReportRepo(session)
    rows = repo.list_recent(limit=10)
    assert len(rows) == 3
    # date desc, kind desc 在同 date 内由 generated_at 决定
    assert rows[0].date >= rows[-1].date


def test_list_recent_filter_by_kind(session: Session, seed_reports: list[int]) -> None:
    repo = ReportRepo(session)
    rows = repo.list_recent(kind=ReportKind.PREMARKET, limit=10)
    assert len(rows) == 1
    assert rows[0].kind == ReportKind.PREMARKET


def test_list_recent_filter_by_date_range(session: Session, seed_reports: list[int]) -> None:
    repo = ReportRepo(session)
    today = datetime.now(UTC).date()
    rows = repo.list_recent(date_from=today, date_to=today, limit=10)
    assert len(rows) == 2
    assert all(r.date == today for r in rows)


def test_today_by_kind_hits(session: Session, seed_reports: list[int]) -> None:
    repo = ReportRepo(session)
    today = datetime.now(UTC).date()
    row = repo.today_by_kind(kind=ReportKind.PREMARKET, today=today)
    assert row is not None
    assert row.kind == ReportKind.PREMARKET


def test_today_by_kind_miss_returns_none(session: Session, seed_reports: list[int]) -> None:
    repo = ReportRepo(session)
    today = datetime.now(UTC).date()
    row = repo.today_by_kind(kind=ReportKind.EVENING, today=today)
    assert row is None


def test_list_today_returns_dict_by_kind(session: Session, seed_reports: list[int]) -> None:
    repo = ReportRepo(session)
    today = datetime.now(UTC).date()
    by_kind = repo.list_today(today=today)
    assert isinstance(by_kind, dict)
    # 至少应该包含 premarket 与 morning
    assert by_kind.get(ReportKind.PREMARKET.value) is not None
    assert by_kind.get(ReportKind.MORNING.value) is not None
    # 缺失的 kind 不存在或为 None
    assert by_kind.get(ReportKind.EVENING.value) is None
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
uv run pytest tests/unit/test_report_repo.py -v
```

Expected: `ImportError` `cannot import name 'ReportRepo' from 'amarket.repositories.report_repo'`。

- [ ] **Step 3: 实现 ReportRepo**

`src/amarket/repositories/report_repo.py`：

```python
"""ReportRepo — 6 时段日报表读写（M3b）。

M3b 阶段：只提供读接口给 /api/reports/*；写接口（generate / push）等 M4 ReportService。
"""

from __future__ import annotations

from datetime import date as date_t

from sqlmodel import select

from amarket.domain.enums import ReportKind
from amarket.domain.models import Report
from amarket.repositories.base import BaseRepo


class ReportRepo(BaseRepo[Report]):
    model = Report

    def list_recent(
        self,
        *,
        kind: ReportKind | None = None,
        date_from: date_t | None = None,
        date_to: date_t | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Report]:
        """按 date desc, generated_at desc 排序。"""
        stmt = select(Report).order_by(
            Report.date.desc(),  # type: ignore[attr-defined]
            Report.generated_at.desc(),  # type: ignore[attr-defined]
        )
        if kind is not None:
            stmt = stmt.where(Report.kind == kind)
        if date_from is not None:
            stmt = stmt.where(Report.date >= date_from)
        if date_to is not None:
            stmt = stmt.where(Report.date <= date_to)
        stmt = stmt.offset(offset).limit(limit)
        return list(self.session.exec(stmt))

    def count_filtered(
        self,
        *,
        kind: ReportKind | None = None,
        date_from: date_t | None = None,
        date_to: date_t | None = None,
    ) -> int:
        from sqlalchemy import func

        stmt = select(func.count()).select_from(Report)
        if kind is not None:
            stmt = stmt.where(Report.kind == kind)
        if date_from is not None:
            stmt = stmt.where(Report.date >= date_from)
        if date_to is not None:
            stmt = stmt.where(Report.date <= date_to)
        return int(self.session.exec(stmt).one())

    def today_by_kind(
        self,
        *,
        kind: ReportKind,
        today: date_t,
    ) -> Report | None:
        """同 date + kind 唯一约束 — 命中即唯一。"""
        stmt = (
            select(Report)
            .where(Report.date == today)
            .where(Report.kind == kind)
            .limit(1)
        )
        return self.session.exec(stmt).first()

    def list_today(self, *, today: date_t) -> dict[str, Report | None]:
        """今日 6 时段：返回 dict[kind_str -> Report | None]。"""
        result: dict[str, Report | None] = {k.value: None for k in ReportKind}
        stmt = select(Report).where(Report.date == today)
        for r in self.session.exec(stmt):
            result[r.kind.value] = r
        return result


__all__ = ["ReportRepo"]
```

- [ ] **Step 4: 跑测试确认 pass**

```bash
uv run pytest tests/unit/test_report_repo.py -v
```

Expected: `6 passed`。

- [ ] **Step 5: ruff + mypy**

```bash
uv run ruff check src/amarket/repositories/report_repo.py tests/unit/test_report_repo.py
uv run mypy src/amarket/repositories/report_repo.py
```

Expected: 0 errors。

- [ ] **Step 6: commit**

```bash
git -C C:/AI/Claude/Project_Amarket add src/amarket/repositories/report_repo.py tests/unit/test_report_repo.py
git -C C:/AI/Claude/Project_Amarket commit -m "feat(m3b): add ReportRepo with list/today/by-kind queries"
```

---

## Task 4: SectorTrendRepo

**Files:**
- Create: `src/amarket/repositories/sector_trend_repo.py`
- Create: `tests/unit/test_sector_trend_repo.py`

- [ ] **Step 1: 写失败测试**

`tests/unit/test_sector_trend_repo.py`：

```python
"""SectorTrendRepo 单测（M3b）。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlmodel import Session

from amarket.domain.models import SectorTrend
from amarket.repositories.sector_trend_repo import SectorTrendRepo


def test_bulk_upsert_inserts_new(session: Session) -> None:
    repo = SectorTrendRepo(session)
    now = datetime.now(UTC)
    rows = [
        SectorTrend(ts=now, sector_name="券商", change_pct=1.5, news_heat=10),
        SectorTrend(ts=now, sector_name="银行", change_pct=-0.5, news_heat=5),
    ]
    inserted = repo.bulk_upsert(rows)
    assert inserted == 2


def test_latest_for_sectors_returns_freshest(session: Session) -> None:
    repo = SectorTrendRepo(session)
    older = datetime.now(UTC) - timedelta(hours=2)
    newer = datetime.now(UTC)
    repo.bulk_upsert(
        [
            SectorTrend(ts=older, sector_name="券商", change_pct=0.5, news_heat=3),
            SectorTrend(ts=newer, sector_name="券商", change_pct=1.5, news_heat=10),
            SectorTrend(ts=newer, sector_name="银行", change_pct=-0.3, news_heat=5),
        ]
    )
    latest = repo.latest_for_sectors(["券商", "银行", "保险"])
    assert "券商" in latest
    assert latest["券商"].change_pct == 1.5  # 取新的
    assert "银行" in latest
    assert "保险" not in latest  # 没数据 → 不在 dict 中


def test_latest_for_sectors_empty_db(session: Session) -> None:
    repo = SectorTrendRepo(session)
    result = repo.latest_for_sectors(["券商"])
    assert result == {}
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
uv run pytest tests/unit/test_sector_trend_repo.py -v
```

Expected: `ImportError`。

- [ ] **Step 3: 实现 SectorTrendRepo**

`src/amarket/repositories/sector_trend_repo.py`：

```python
"""SectorTrendRepo — 板块趋势聚合表读写（M3b）。

M3b 阶段：表可能完全为空（M4 才有 APScheduler 写入），Repo 接口要稳。
"""

from __future__ import annotations

from sqlmodel import select

from amarket.domain.models import SectorTrend
from amarket.repositories.base import BaseRepo


class SectorTrendRepo(BaseRepo[SectorTrend]):
    model = SectorTrend

    def bulk_upsert(self, rows: list[SectorTrend]) -> int:
        """批量写入（M4 调度任务会调）。M3b 测试用。Returns: 写入行数。"""
        if not rows:
            return 0
        self.add_many(rows)
        return len(rows)

    def latest_for_sectors(self, sector_names: list[str]) -> dict[str, SectorTrend]:
        """每个 sector_name 取最新一条，dict[name -> row]。空表返回 {}。"""
        result: dict[str, SectorTrend] = {}
        for name in sector_names:
            stmt = (
                select(SectorTrend)
                .where(SectorTrend.sector_name == name)
                .order_by(SectorTrend.ts.desc())  # type: ignore[attr-defined]
                .limit(1)
            )
            row = self.session.exec(stmt).first()
            if row is not None:
                result[name] = row
        return result


__all__ = ["SectorTrendRepo"]
```

- [ ] **Step 4: 跑测试确认 pass**

```bash
uv run pytest tests/unit/test_sector_trend_repo.py -v
```

Expected: `3 passed`。

- [ ] **Step 5: ruff + mypy**

```bash
uv run ruff check src/amarket/repositories/sector_trend_repo.py tests/unit/test_sector_trend_repo.py
uv run mypy src/amarket/repositories/sector_trend_repo.py
```

Expected: 0 errors。

- [ ] **Step 6: commit**

```bash
git -C C:/AI/Claude/Project_Amarket add src/amarket/repositories/sector_trend_repo.py tests/unit/test_sector_trend_repo.py
git -C C:/AI/Claude/Project_Amarket commit -m "feat(m3b): add SectorTrendRepo with bulk_upsert + latest_for_sectors"
```

---

## Task 5: SectorTrendService（Phase 1 简化版）

**Files:**
- Create: `src/amarket/services/dashboard/sector_trend.py`
- Create: `tests/unit/test_sector_trend_service.py`

**Design note (Phase 1 简化版 spec v3 §6.1.7)**：
- `news_heat`：从 NewsAnalysis.related_sectors 反查（JSON list of dict），window 内匹配该 sector 的条数
- `change_pct`：M3b 留 None（M4 接 SectorIndex 真值时填）；如果 SectorTrend 表里有最近 4h 内的记录就用表里值
- `market_cap_weight`：用 hard-coded 14 板块的粗略 stub（M5 真做时由参数模块覆写）
- `top_symbols`：M3b 留空 list（M4 由行情聚合填）

- [ ] **Step 1: 写失败测试**

`tests/unit/test_sector_trend_service.py`：

```python
"""SectorTrendService 单测（M3b）— 关注 news_heat 计算 + stub 数据回退。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlmodel import Session

from amarket.domain.enums import (
    ActionHint,
    AlertLevel,
    ImpactHorizon,
    NewsCategory,
    Sentiment,
    SourcePriority,
)
from amarket.domain.models import NewsAnalysis, NewsItem, NewsSource, SectorTrend
from amarket.services.dashboard.sector_trend import (
    DEFAULT_SECTOR_NAMES,
    SectorTrendService,
)


@pytest.fixture
def seed_news_analyses(session: Session) -> None:
    """seed 1 source + 3 news + 3 analyses 关联到 '券商' / '银行' 板块。"""
    src = NewsSource(code="t", name="测试源", priority=SourcePriority.HIGH)
    session.add(src)
    session.commit()
    session.refresh(src)
    assert src.id is not None
    sid = src.id

    now = datetime.now(UTC)
    items = [
        NewsItem(
            source_id=sid,
            source_msg_id=f"m{i}",
            title=f"新闻{i}",
            published_at=now - timedelta(minutes=10 * i),
        )
        for i in range(3)
    ]
    session.add_all(items)
    session.commit()
    for it in items:
        session.refresh(it)
    iids = [it.id for it in items]
    assert all(x is not None for x in iids)

    # 2 个分析关联券商，1 个关联银行
    analyses = [
        NewsAnalysis(
            news_id=iids[0],
            primary_category=NewsCategory.MARKET,
            related_sectors=[{"name": "券商", "weight": 0.9}],
            sentiment=Sentiment.POSITIVE,
            importance_score=4,
            urgency_score=3,
            confidence_score=4,
            impact_horizon=ImpactHorizon.INTRADAY,
            action_hint=ActionHint.WATCH,
            processed_by="rule",
        ),
        NewsAnalysis(
            news_id=iids[1],
            primary_category=NewsCategory.MARKET,
            related_sectors=[{"name": "券商", "weight": 0.7}, {"name": "银行", "weight": 0.5}],
            sentiment=Sentiment.NEUTRAL,
            importance_score=3,
            urgency_score=2,
            confidence_score=3,
            impact_horizon=ImpactHorizon.INTRADAY,
            action_hint=ActionHint.WATCH,
            processed_by="rule",
        ),
        NewsAnalysis(
            news_id=iids[2],
            primary_category=NewsCategory.MARKET,
            related_sectors=[{"name": "保险", "weight": 0.6}],
            sentiment=Sentiment.NEGATIVE,
            importance_score=2,
            urgency_score=1,
            confidence_score=3,
            impact_horizon=ImpactHorizon.INTRADAY,
            action_hint=ActionHint.WATCH,
            processed_by="rule",
        ),
    ]
    session.add_all(analyses)
    session.commit()


def test_default_sector_names_has_14(session: Session) -> None:
    assert len(DEFAULT_SECTOR_NAMES) == 14
    assert "券商" in DEFAULT_SECTOR_NAMES


def test_list_sectors_empty_db_returns_14_with_zeros(session: Session) -> None:
    """空 DB（无 news + 无 SectorTrend）→ 返回 14 个板块，全 0 news_heat。"""
    svc = SectorTrendService(session)
    result = svc.list_sectors(window=timedelta(days=1))
    assert len(result) == 14
    for s in result:
        assert s.news_count_24h == 0
        assert s.change_pct is None  # M3b 默认 None
        # market_cap_weight stub 应有值
        assert s.market_cap_weight is not None
        assert s.top_symbols == []


def test_list_sectors_news_heat_from_analysis(
    session: Session, seed_news_analyses: None
) -> None:
    """有 news + analysis → 券商 heat=2，银行 heat=1，保险 heat=1。"""
    svc = SectorTrendService(session)
    result = svc.list_sectors(window=timedelta(days=1))
    by_name = {s.name: s for s in result}
    assert by_name["券商"].news_count_24h == 2
    assert by_name["银行"].news_count_24h == 1
    assert by_name["保险"].news_count_24h == 1
    # 没新闻的板块 = 0
    assert by_name["半导体"].news_count_24h == 0


def test_list_sectors_uses_sector_trend_change_pct_when_present(
    session: Session, seed_news_analyses: None
) -> None:
    """SectorTrend 表里有最近数据 → change_pct 用表里的。"""
    now = datetime.now(UTC)
    session.add(SectorTrend(ts=now, sector_name="券商", change_pct=2.5, news_heat=99))
    session.commit()

    svc = SectorTrendService(session)
    result = svc.list_sectors(window=timedelta(days=1))
    by_name = {s.name: s for s in result}
    # change_pct 用表里的（2.5），但 news_count_24h 用 NewsAnalysis 反查（实时更准）
    assert by_name["券商"].change_pct == 2.5
    assert by_name["券商"].news_count_24h == 2


def test_top_n_by_news_heat(session: Session, seed_news_analyses: None) -> None:
    svc = SectorTrendService(session)
    top3 = svc.top_n(by="news_heat", n=3, window=timedelta(days=1))
    assert len(top3) == 3
    # 第一名是 news_count_24h 最高（券商=2）
    assert top3[0].name == "券商"
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
uv run pytest tests/unit/test_sector_trend_service.py -v
```

Expected: `ImportError`。

- [ ] **Step 3: 实现 SectorTrendService**

`src/amarket/services/dashboard/sector_trend.py`：

```python
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
            sectors.sort(key=lambda s: (s.change_pct or 0.0), reverse=True)
        elif by == "market_cap_weight":
            sectors.sort(key=lambda s: (s.market_cap_weight or 0.0), reverse=True)
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
        counts: dict[str, int] = {name: 0 for name in sector_names}
        target = set(sector_names)
        for ana in self._session.exec(stmt):
            for s in ana.related_sectors or []:
                if isinstance(s, dict):
                    name = s.get("name")
                    if name in target:
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
```

- [ ] **Step 4: 跑测试确认 pass**

```bash
uv run pytest tests/unit/test_sector_trend_service.py -v
```

Expected: `5 passed`。

- [ ] **Step 5: ruff + mypy**

```bash
uv run ruff check src/amarket/services/dashboard/sector_trend.py tests/unit/test_sector_trend_service.py
uv run mypy src/amarket/services/dashboard/sector_trend.py
```

Expected: 0 errors。

- [ ] **Step 6: commit**

```bash
git -C C:/AI/Claude/Project_Amarket add src/amarket/services/dashboard/sector_trend.py tests/unit/test_sector_trend_service.py
git -C C:/AI/Claude/Project_Amarket commit -m "feat(m3b): SectorTrendService (Phase 1: news_heat from analyses, stub weights)"
```

---

## Task 6: API `/api/dashboard/sectors`

**Files:**
- Modify: `src/amarket/api/dashboard.py`（加 endpoint）
- Create: `tests/unit/test_api_dashboard_m3b.py`

- [ ] **Step 1: 写失败测试**

`tests/unit/test_api_dashboard_m3b.py`：

```python
"""M3b 新增的 dashboard endpoints 测试：sectors / movers / summary。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session

from amarket.domain.enums import (
    ActionHint,
    AlertLevel,
    ImpactHorizon,
    NewsCategory,
    Sentiment,
    SourcePriority,
)
from amarket.domain.models import Alert, MarketSnapshot, NewsAnalysis, NewsItem, NewsSource


# --------------------------------------------------------------------------- #
# /api/dashboard/sectors
# --------------------------------------------------------------------------- #


def test_sectors_empty_db_returns_14_with_zeros(api_client: TestClient) -> None:
    resp = api_client.get("/api/dashboard/sectors")
    assert resp.status_code == 200
    data = resp.json()
    assert "sectors" in data
    assert len(data["sectors"]) == 14
    assert all(s["news_count_24h"] == 0 for s in data["sectors"])
    assert all(s["change_pct"] is None for s in data["sectors"])
    # window 默认 1d
    assert data["window"] == "1d"


@pytest.fixture
def seed_sectors_data(patched_engine: Engine) -> None:
    with Session(patched_engine) as session:
        src = NewsSource(code="t", name="测试", priority=SourcePriority.HIGH)
        session.add(src)
        session.commit()
        session.refresh(src)
        assert src.id is not None
        sid = src.id

        item = NewsItem(
            source_id=sid,
            source_msg_id="m1",
            title="券商利好",
            published_at=datetime.now(UTC),
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        assert item.id is not None

        ana = NewsAnalysis(
            news_id=item.id,
            primary_category=NewsCategory.MARKET,
            related_sectors=[{"name": "券商", "weight": 0.9}],
            sentiment=Sentiment.POSITIVE,
            importance_score=4,
            urgency_score=3,
            confidence_score=4,
            impact_horizon=ImpactHorizon.INTRADAY,
            action_hint=ActionHint.WATCH,
            processed_by="rule",
        )
        session.add(ana)
        session.commit()


def test_sectors_news_heat_counted(
    api_client: TestClient, seed_sectors_data: None
) -> None:
    resp = api_client.get("/api/dashboard/sectors")
    assert resp.status_code == 200
    by_name = {s["name"]: s for s in resp.json()["sectors"]}
    assert by_name["券商"]["news_count_24h"] == 1
    assert by_name["银行"]["news_count_24h"] == 0


def test_sectors_window_param_accepts_short_windows(
    api_client: TestClient, seed_sectors_data: None
) -> None:
    """1h 窗口仍能拿到刚 seed 的（now-1min）那条。"""
    resp = api_client.get("/api/dashboard/sectors?window=1h")
    assert resp.status_code == 200
    data = resp.json()
    assert data["window"] == "1h"
    by_name = {s["name"]: s for s in data["sectors"]}
    assert by_name["券商"]["news_count_24h"] == 1


def test_sectors_invalid_window_falls_back_to_1d(
    api_client: TestClient, seed_sectors_data: None
) -> None:
    resp = api_client.get("/api/dashboard/sectors?window=bogus")
    assert resp.status_code == 200
    assert resp.json()["window"] == "1d"
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
uv run pytest tests/unit/test_api_dashboard_m3b.py::test_sectors_empty_db_returns_14_with_zeros -v
```

Expected: 404 (端点未实现)。

- [ ] **Step 3: 在 dashboard.py 加 `/sectors` endpoint**

Append to `src/amarket/api/dashboard.py`（在 `__all__` 之前）：

```python
from datetime import timedelta

from amarket.domain.schemas import SectorListResponse
from amarket.services.dashboard.sector_trend import SectorTrendService


_WINDOW_MAP: dict[str, timedelta] = {
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "1d": timedelta(days=1),
}


@router.get("/sectors", response_model=SectorListResponse)
async def dashboard_sectors(
    window: str = "1d",
    session: Session = Depends(db_session),
) -> SectorListResponse:
    """板块趋势看板（M3b — Phase 1 简化版）。

    - window：'1h' | '4h' | '1d'（默认 1d；无效值 fallback 到 1d）
    - 数据：news_count_24h 实时反查；change_pct 来自 SectorTrend 表（无则 None）
    """
    td = _WINDOW_MAP.get(window) or timedelta(days=1)
    effective_window = window if window in _WINDOW_MAP else "1d"
    svc = SectorTrendService(session)
    sectors = svc.list_sectors(window=td)
    return SectorListResponse(
        as_of=datetime.now(UTC),
        window=effective_window,
        sectors=sectors,
    )
```

Top of file 已经 `from datetime import UTC, datetime`，append `timedelta` 到现有 import 即可。

- [ ] **Step 4: 跑全部 sectors 测试**

```bash
uv run pytest tests/unit/test_api_dashboard_m3b.py -v -k sectors
```

Expected: 4 passed。

- [ ] **Step 5: ruff + mypy**

```bash
uv run ruff check src/amarket/api/dashboard.py tests/unit/test_api_dashboard_m3b.py
uv run mypy src/amarket/api/dashboard.py
```

Expected: 0 errors。

- [ ] **Step 6: commit**

```bash
git -C C:/AI/Claude/Project_Amarket add src/amarket/api/dashboard.py tests/unit/test_api_dashboard_m3b.py
git -C C:/AI/Claude/Project_Amarket commit -m "feat(m3b): add GET /api/dashboard/sectors (window + news heat)"
```

---

## Task 7: API `/api/dashboard/movers`

**Phase 1 简化版**：从 `MarketSnapshot` 按 `change_pct` 取 top gainers + losers。M3b 阶段 DB 里 `asset_kind='stock'` 几乎没数据 → 端点会返回空列表（前端友好处理）。但接口契约定好以便 M4 行情接入后即用。

**Files:**
- Modify: `src/amarket/api/dashboard.py`
- Modify: `tests/unit/test_api_dashboard_m3b.py`

- [ ] **Step 1: 写失败测试**

Append to `tests/unit/test_api_dashboard_m3b.py`：

```python
# --------------------------------------------------------------------------- #
# /api/dashboard/movers
# --------------------------------------------------------------------------- #


def test_movers_empty_db_returns_empty_lists(api_client: TestClient) -> None:
    resp = api_client.get("/api/dashboard/movers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["top_gainers"] == []
    assert data["top_losers"] == []


@pytest.fixture
def seed_market_snapshots(patched_engine: Engine) -> None:
    with Session(patched_engine) as session:
        rows = [
            MarketSnapshot(
                ts=datetime.now(UTC),
                asset_kind="stock",
                code="600000",
                name="浦发银行",
                price=10.5,
                change_pct=5.2,  # gainer
            ),
            MarketSnapshot(
                ts=datetime.now(UTC),
                asset_kind="stock",
                code="600519",
                name="贵州茅台",
                price=1700.0,
                change_pct=1.1,
            ),
            MarketSnapshot(
                ts=datetime.now(UTC),
                asset_kind="stock",
                code="000001",
                name="平安银行",
                price=11.2,
                change_pct=-3.8,  # loser
            ),
            MarketSnapshot(
                ts=datetime.now(UTC),
                asset_kind="stock",
                code="000333",
                name="美的集团",
                price=70.0,
                change_pct=-1.5,
            ),
            MarketSnapshot(
                ts=datetime.now(UTC),
                asset_kind="index",  # index 应该被过滤
                code="sh000001",
                name="上证",
                price=3200.0,
                change_pct=10.0,
            ),
        ]
        session.add_all(rows)
        session.commit()


def test_movers_returns_top_gainers_and_losers(
    api_client: TestClient, seed_market_snapshots: None
) -> None:
    resp = api_client.get("/api/dashboard/movers?n=2")
    assert resp.status_code == 200
    data = resp.json()
    # gainers desc by change_pct，过滤 asset_kind='stock'
    assert len(data["top_gainers"]) == 2
    assert data["top_gainers"][0]["code"] == "600000"
    assert data["top_gainers"][0]["change_pct"] == 5.2
    # losers asc by change_pct
    assert len(data["top_losers"]) == 2
    assert data["top_losers"][0]["code"] == "000001"
    assert data["top_losers"][0]["change_pct"] == -3.8
    # 不含 index
    all_codes = {m["code"] for m in data["top_gainers"] + data["top_losers"]}
    assert "sh000001" not in all_codes


def test_movers_n_param_bounded(api_client: TestClient, seed_market_snapshots: None) -> None:
    resp = api_client.get("/api/dashboard/movers?n=50")
    assert resp.status_code == 200
    # 只有 2 个 gainer + 2 个 loser
    assert len(resp.json()["top_gainers"]) == 2
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
uv run pytest tests/unit/test_api_dashboard_m3b.py::test_movers_empty_db_returns_empty_lists -v
```

Expected: 404。

- [ ] **Step 3: 实现 endpoint**

Append to `src/amarket/api/dashboard.py`：

```python
from fastapi import Query

from amarket.domain.models import MarketSnapshot
from amarket.domain.schemas import MoverDTO, MoversListResponse


@router.get("/movers", response_model=MoversListResponse)
async def dashboard_movers(
    n: int = Query(default=10, ge=1, le=50),
    session: Session = Depends(db_session),
) -> MoversListResponse:
    """个股异动榜（M3b — 简化版）：从 MarketSnapshot 按 change_pct 取 top n。

    Phase 1 备注：依赖 asset_kind='stock' 的快照入库。当前调度只入 index，
    所以默认返回空列表 — 前端友好处理。M4 调度补 stock 快照后自动有值。
    """
    from sqlmodel import select

    # 每个 code 取最新一条 stock 快照
    stmt = (
        select(MarketSnapshot)
        .where(MarketSnapshot.asset_kind == "stock")
        .order_by(MarketSnapshot.ts.desc())  # type: ignore[attr-defined]
    )
    seen: dict[str, MarketSnapshot] = {}
    for row in session.exec(stmt):
        if row.code not in seen:
            seen[row.code] = row

    snapshots = [s for s in seen.values() if s.change_pct is not None]
    gainers = sorted(snapshots, key=lambda s: s.change_pct or 0.0, reverse=True)[:n]
    losers = sorted(snapshots, key=lambda s: s.change_pct or 0.0)[:n]

    def to_dto(s: MarketSnapshot) -> MoverDTO:
        return MoverDTO(
            code=s.code,
            name=s.name,
            change_pct=s.change_pct,
            price=s.price,
            volume=s.volume,
            turnover=s.turnover,
        )

    return MoversListResponse(
        as_of=datetime.now(UTC),
        top_gainers=[to_dto(s) for s in gainers if (s.change_pct or 0.0) >= 0],
        top_losers=[to_dto(s) for s in losers if (s.change_pct or 0.0) < 0],
    )
```

- [ ] **Step 4: 跑测试确认 pass**

```bash
uv run pytest tests/unit/test_api_dashboard_m3b.py -v -k movers
```

Expected: 3 passed。

- [ ] **Step 5: ruff + mypy**

```bash
uv run ruff check src/amarket/api/dashboard.py
uv run mypy src/amarket/api/dashboard.py
```

Expected: 0 errors。

- [ ] **Step 6: commit**

```bash
git -C C:/AI/Claude/Project_Amarket add src/amarket/api/dashboard.py tests/unit/test_api_dashboard_m3b.py
git -C C:/AI/Claude/Project_Amarket commit -m "feat(m3b): add GET /api/dashboard/movers (top gainers/losers from snapshots)"
```

---

## Task 8: API `/api/dashboard/summary`（聚合）

**Files:**
- Modify: `src/amarket/api/dashboard.py`
- Modify: `tests/unit/test_api_dashboard_m3b.py`

- [ ] **Step 1: 写失败测试**

Append to `tests/unit/test_api_dashboard_m3b.py`：

```python
# --------------------------------------------------------------------------- #
# /api/dashboard/summary
# --------------------------------------------------------------------------- #


def test_summary_empty_db_returns_skeleton(api_client: TestClient) -> None:
    resp = api_client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "as_of" in data
    assert "market_status" in data
    assert "latest_news" in data
    assert data["latest_news"] == []
    assert data["p0_alerts"] == []
    assert data["p1_alerts"] == []
    assert len(data["top_sectors"]) == 14  # 14 板块都给出（即使 heat=0）
    assert "today_reports" in data
    # 6 时段 key 都有，但 value 可能 null
    for kind in ("premarket", "morning", "noon", "afternoon", "close", "evening"):
        assert kind in data["today_reports"]


def test_summary_aggregates_alerts_by_level(
    api_client: TestClient, patched_engine: Engine
) -> None:
    """seed 一个 P0 + 一个 P1 + 一个 P2 → summary p0_alerts 1 个，p1_alerts 1 个。"""
    with Session(patched_engine) as session:
        src = NewsSource(code="t", name="测试", priority=SourcePriority.HIGH)
        session.add(src)
        session.commit()
        session.refresh(src)
        assert src.id is not None

        item = NewsItem(
            source_id=src.id,
            source_msg_id="m1",
            title="重大政策",
            published_at=datetime.now(UTC),
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        assert item.id is not None
        nid = item.id

        for lvl in (AlertLevel.P0, AlertLevel.P1, AlertLevel.P2):
            session.add(
                Alert(
                    news_id=nid,
                    level=lvl,
                    trigger_reason="test",
                    status="pending",
                    created_at=datetime.now(UTC),
                )
            )
        session.commit()

    resp = api_client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["p0_alerts"]) == 1
    assert len(data["p1_alerts"]) == 1
    assert data["p0_alerts"][0]["level"] == "P0"


def test_summary_latest_news_limit(api_client: TestClient, patched_engine: Engine) -> None:
    """seed 60 条新闻 → summary.latest_news 默认 30 条上限。"""
    with Session(patched_engine) as session:
        src = NewsSource(code="t", name="测试", priority=SourcePriority.HIGH)
        session.add(src)
        session.commit()
        session.refresh(src)
        assert src.id is not None
        for i in range(60):
            session.add(
                NewsItem(
                    source_id=src.id,
                    source_msg_id=f"m{i}",
                    title=f"新闻{i}",
                    published_at=datetime.now(UTC),
                )
            )
        session.commit()

    resp = api_client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    assert len(resp.json()["latest_news"]) == 30
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
uv run pytest tests/unit/test_api_dashboard_m3b.py::test_summary_empty_db_returns_skeleton -v
```

Expected: 404。

- [ ] **Step 3: 实现 `/summary` endpoint**

Append to `src/amarket/api/dashboard.py`：

```python
from amarket.adapters.market_sources.base import MAJOR_A_SHARE_INDEXES as _INDEX_CODES
from amarket.api.alerts import _to_dto as _alert_to_dto
from amarket.api.news import _highest_alert_for, _latest_analysis_for, _to_card
from amarket.domain.enums import AlertLevel as _AlertLevel
from amarket.domain.enums import ReportKind as _ReportKind
from amarket.domain.schemas import (
    AlertDTO,
    DashboardSummary,
    NewsCardDTO,
    ReportDetailDTO,
)
from amarket.repositories.alert_repo import AlertRepo
from amarket.repositories.news_analysis_repo import NewsAnalysisRepo
from amarket.repositories.news_repo import NewsRepo
from amarket.repositories.report_repo import ReportRepo


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    news_limit: int = Query(default=30, ge=1, le=100),
    session: Session = Depends(db_session),
) -> DashboardSummary:
    """首页一次性聚合（M3b — POC index.html 用）。"""
    # 1. 行情 — 复用 market-status 逻辑
    market_repo = MarketSnapshotRepo(session)
    latest_idx = market_repo.latest_for_codes(list(_INDEX_CODES.keys()))
    market_status: dict[str, list[dict[str, object]]] = {
        "indexes": [],
        "fx": [],
        "commodities": [],
    }
    for code, name in _INDEX_CODES.items():
        snap = latest_idx.get(code)
        if snap is None:
            continue
        extra = snap.extra_json if isinstance(snap.extra_json, dict) else {}
        market_status["indexes"].append(
            {
                "code": code,
                "name": snap.name or name,
                "price": snap.price or 0.0,
                "change_pct": snap.change_pct,
                "change_abs": snap.change_abs,
                "prev_close": extra.get("prev_close"),
                "volume": snap.volume,
                "turnover": snap.turnover,
                "source": str(extra.get("source", "akshare")),
                "fetched_at": snap.ts.isoformat(),
            }
        )

    # 2. 最新新闻
    news_repo = NewsRepo(session)
    analysis_repo = NewsAnalysisRepo(session)
    alert_repo = AlertRepo(session)
    news_rows = news_repo.list_recent(limit=news_limit)
    latest_news: list[NewsCardDTO] = []
    for it, src in news_rows:
        assert it.id is not None
        ana = _latest_analysis_for(analysis_repo, it.id)
        alt = _highest_alert_for(alert_repo, it.id)
        latest_news.append(_to_card(it, src, analysis=ana, alert=alt))

    # 3. P0 / P1 alerts
    p0_alerts: list[AlertDTO] = []
    p1_alerts: list[AlertDTO] = []
    for level, bucket in ((_AlertLevel.P0, p0_alerts), (_AlertLevel.P1, p1_alerts)):
        alerts = alert_repo.list_recent(levels=[level], limit=10)
        for a in alerts:
            title = source_name = category = None
            if a.news_id is not None:
                from amarket.domain.models import NewsAnalysis, NewsItem, NewsSource

                news = session.get(NewsItem, a.news_id)
                if news is not None:
                    title = news.title
                    s = session.get(NewsSource, news.source_id)
                    if s is not None:
                        source_name = s.name
                if a.analysis_id is not None:
                    ana_row = session.get(NewsAnalysis, a.analysis_id)
                    if ana_row is not None:
                        category = ana_row.primary_category.value
            bucket.append(
                _alert_to_dto(
                    a,
                    news_title=title,
                    news_source=source_name,
                    primary_category=category,
                )
            )

    # 4. Top sectors（按 news_heat 排前 10）
    svc = SectorTrendService(session)
    top_sectors = svc.top_n(by="news_heat", n=10, window=timedelta(days=1))

    # 5. Top movers — 复用 movers 端点逻辑
    movers_resp = await dashboard_movers(n=5, session=session)
    top_movers = movers_resp.top_gainers + movers_resp.top_losers

    # 6. Today reports
    report_repo = ReportRepo(session)
    today = datetime.now(UTC).date()
    today_rows = report_repo.list_today(today=today)
    today_reports: dict[str, ReportDetailDTO | None] = {}
    for kind in _ReportKind:
        r = today_rows.get(kind.value)
        if r is None:
            today_reports[kind.value] = None
        else:
            assert r.id is not None
            today_reports[kind.value] = ReportDetailDTO(
                report_id=r.id,
                date=r.date,
                kind=r.kind.value,
                status=r.status,
                markdown=r.markdown,
                content_json=r.content_json if isinstance(r.content_json, dict) else {},
                generated_by=r.generated_by,
                generated_at=r.generated_at,
                push_count=r.push_count,
            )

    return DashboardSummary(
        as_of=datetime.now(UTC),
        market_status=market_status,
        today_conclusion=None,  # M4 接 ReportService 后从盘前日报抽取
        latest_news=latest_news,
        p0_alerts=p0_alerts,
        p1_alerts=p1_alerts,
        top_sectors=top_sectors,
        top_movers=top_movers,
        today_reports=today_reports,
    )
```

- [ ] **Step 4: 跑全部 summary 测试**

```bash
uv run pytest tests/unit/test_api_dashboard_m3b.py -v -k summary
```

Expected: 3 passed。

- [ ] **Step 5: ruff + mypy**

```bash
uv run ruff check src/amarket/api/dashboard.py tests/unit/test_api_dashboard_m3b.py
uv run mypy src/amarket/api/dashboard.py
```

Expected: 0 errors。

- [ ] **Step 6: commit**

```bash
git -C C:/AI/Claude/Project_Amarket add src/amarket/api/dashboard.py tests/unit/test_api_dashboard_m3b.py
git -C C:/AI/Claude/Project_Amarket commit -m "feat(m3b): add GET /api/dashboard/summary (aggregate market/news/alerts/sectors/reports)"
```

---

## Task 9: API `/api/reports/*`（list / detail / today/{kind}）

**Files:**
- Create: `src/amarket/api/reports.py`
- Modify: `src/amarket/main.py`（include router）
- Create: `tests/unit/test_api_reports.py`

- [ ] **Step 1: 写失败测试**

`tests/unit/test_api_reports.py`：

```python
"""API /api/reports/* 集成测试（M3b）。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session

from amarket.domain.enums import ReportKind
from amarket.domain.models import Report


@pytest.fixture
def seed_today_reports(patched_engine: Engine) -> None:
    with Session(patched_engine) as session:
        today = datetime.now(UTC).date()
        session.add(
            Report(
                date=today,
                kind=ReportKind.PREMARKET,
                status="completed",
                markdown="## 盘前\n- A",
                content_json={"sections": []},
                generated_by="agent:daily-report-writer",
                generated_at=datetime.now(UTC),
            )
        )
        session.add(
            Report(
                date=today,
                kind=ReportKind.MORNING,
                status="completed",
                markdown="## 早盘",
                generated_by="agent:daily-report-writer",
                generated_at=datetime.now(UTC),
            )
        )
        session.commit()


def test_reports_list_empty_db(api_client: TestClient) -> None:
    resp = api_client.get("/api/reports")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_reports_list_returns_items(
    api_client: TestClient, seed_today_reports: None
) -> None:
    resp = api_client.get("/api/reports")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    kinds = {it["kind"] for it in data["items"]}
    assert kinds == {"premarket", "morning"}
    # list view 不含 markdown（不污染列表）
    assert "markdown" not in data["items"][0]


def test_reports_list_filter_by_kind(
    api_client: TestClient, seed_today_reports: None
) -> None:
    resp = api_client.get("/api/reports?kind=premarket")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_reports_get_detail_includes_markdown(
    api_client: TestClient, seed_today_reports: None
) -> None:
    list_resp = api_client.get("/api/reports?kind=premarket")
    rid = list_resp.json()["items"][0]["report_id"]
    resp = api_client.get(f"/api/reports/{rid}")
    assert resp.status_code == 200
    data = resp.json()
    assert "## 盘前" in data["markdown"]
    assert data["content_json"] == {"sections": []}


def test_reports_get_detail_404(api_client: TestClient) -> None:
    resp = api_client.get("/api/reports/999999")
    assert resp.status_code == 404


def test_reports_today_returns_6_kinds(
    api_client: TestClient, seed_today_reports: None
) -> None:
    resp = api_client.get("/api/reports/today")
    assert resp.status_code == 200
    data = resp.json()
    assert set(data["reports_by_kind"].keys()) == {
        "premarket",
        "morning",
        "noon",
        "afternoon",
        "close",
        "evening",
    }
    assert data["reports_by_kind"]["premarket"]["status"] == "completed"
    assert data["reports_by_kind"]["evening"] is None


def test_reports_today_specific_kind(
    api_client: TestClient, seed_today_reports: None
) -> None:
    resp = api_client.get("/api/reports/today/premarket")
    assert resp.status_code == 200
    assert resp.json()["kind"] == "premarket"
    assert "## 盘前" in resp.json()["markdown"]


def test_reports_today_specific_kind_missing_returns_404(
    api_client: TestClient, seed_today_reports: None
) -> None:
    resp = api_client.get("/api/reports/today/evening")
    assert resp.status_code == 404
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
uv run pytest tests/unit/test_api_reports.py -v
```

Expected: 全部 404（端点 + router 未注册）。

- [ ] **Step 3: 实现 reports.py router**

`src/amarket/api/reports.py`：

```python
"""`/api/reports/*` endpoints — 6 时段日报（M3b）。

M3b 阶段：只做 read 端点（list / detail / today / today/{kind}）。
写端点（POST /generate、POST /{id}/push）由 M4 ReportService 实现。
"""

from __future__ import annotations

from datetime import UTC, date as date_t, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from amarket.api.dependencies import db_session
from amarket.domain.enums import ReportKind
from amarket.domain.models import Report
from amarket.domain.schemas import (
    ReportDetailDTO,
    ReportListResponse,
    ReportSummaryDTO,
    TodayReportsResponse,
)
from amarket.repositories.report_repo import ReportRepo

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _to_summary(r: Report) -> ReportSummaryDTO:
    assert r.id is not None
    return ReportSummaryDTO(
        report_id=r.id,
        date=r.date,
        kind=r.kind.value,
        status=r.status,
        generated_by=r.generated_by,
        generated_at=r.generated_at,
        push_count=r.push_count,
    )


def _to_detail(r: Report) -> ReportDetailDTO:
    assert r.id is not None
    return ReportDetailDTO(
        report_id=r.id,
        date=r.date,
        kind=r.kind.value,
        status=r.status,
        markdown=r.markdown,
        content_json=r.content_json if isinstance(r.content_json, dict) else {},
        generated_by=r.generated_by,
        generated_at=r.generated_at,
        push_count=r.push_count,
    )


def _parse_kind(kind: str) -> ReportKind:
    try:
        return ReportKind(kind)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"invalid kind: {kind}",
        ) from e


@router.get("", response_model=ReportListResponse)
async def list_reports(
    kind: str | None = Query(default=None),
    date_from: date_t | None = Query(default=None),
    date_to: date_t | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(db_session),
) -> ReportListResponse:
    repo = ReportRepo(session)
    kind_enum = _parse_kind(kind) if kind else None
    rows = repo.list_recent(
        kind=kind_enum, date_from=date_from, date_to=date_to, limit=limit, offset=offset
    )
    total = repo.count_filtered(kind=kind_enum, date_from=date_from, date_to=date_to)
    return ReportListResponse(
        items=[_to_summary(r) for r in rows],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/today", response_model=TodayReportsResponse)
async def today_reports(
    session: Session = Depends(db_session),
) -> TodayReportsResponse:
    """今日 6 时段（缺失 → None）。"""
    repo = ReportRepo(session)
    today = datetime.now(UTC).date()
    rows = repo.list_today(today=today)
    out: dict[str, ReportDetailDTO | None] = {}
    for k in ReportKind:
        r = rows.get(k.value)
        out[k.value] = _to_detail(r) if r is not None else None
    return TodayReportsResponse(today=today, reports_by_kind=out)


@router.get("/today/{kind}", response_model=ReportDetailDTO)
async def today_report_by_kind(
    kind: str,
    session: Session = Depends(db_session),
) -> ReportDetailDTO:
    kind_enum = _parse_kind(kind)
    repo = ReportRepo(session)
    today = datetime.now(UTC).date()
    r = repo.today_by_kind(kind=kind_enum, today=today)
    if r is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"today's {kind} report not generated yet",
        )
    return _to_detail(r)


@router.get("/{report_id}", response_model=ReportDetailDTO)
async def get_report(
    report_id: int,
    session: Session = Depends(db_session),
) -> ReportDetailDTO:
    repo = ReportRepo(session)
    r = repo.get(report_id)
    if r is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="report not found"
        )
    return _to_detail(r)


__all__ = ["router"]
```

- [ ] **Step 4: 注册到 main.py**

修改 `src/amarket/main.py`，在 import 段加 `reports`：

`from amarket.api import alerts, dashboard, health, metrics, news` → `from amarket.api import alerts, dashboard, health, metrics, news, reports`

`create_app()` 中 `app.include_router(alerts.router)  # M2-h` 之后加：

```python
    app.include_router(reports.router)  # M3b
```

- [ ] **Step 5: 跑全部 reports 测试**

```bash
uv run pytest tests/unit/test_api_reports.py -v
```

Expected: 8 passed.

⚠️ 注意路由顺序：`/api/reports/today` 必须在 `/api/reports/{report_id}` **之前**注册（FastAPI 按声明顺序匹配；否则 `today` 会被当成 `report_id` 解析失败）。已按此顺序写。

- [ ] **Step 6: ruff + mypy**

```bash
uv run ruff check src/amarket/api/reports.py src/amarket/main.py tests/unit/test_api_reports.py
uv run mypy src/amarket/api/reports.py src/amarket/main.py
```

Expected: 0 errors。

- [ ] **Step 7: commit**

```bash
git -C C:/AI/Claude/Project_Amarket add src/amarket/api/reports.py src/amarket/main.py tests/unit/test_api_reports.py
git -C C:/AI/Claude/Project_Amarket commit -m "feat(m3b): add /api/reports endpoints (list/detail/today)"
```

---

## Task 10: FastAPI 把 `poc/` mount 成静态目录

让前端跟后端同源运行，浏览器开 `http://127.0.0.1:8080/poc/index.html` 即可。

**Files:**
- Modify: `src/amarket/main.py`
- Create: `tests/unit/test_static_poc_mount.py`

- [ ] **Step 1: 写失败测试**

`tests/unit/test_static_poc_mount.py`：

```python
"""FastAPI mount poc/ 静态目录测试（M3b）。"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_poc_index_html_served(api_client: TestClient) -> None:
    resp = api_client.get("/poc/index.html")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Amarket" in resp.text


def test_poc_shared_js_served(api_client: TestClient) -> None:
    resp = api_client.get("/poc/assets/js/shared.js")
    assert resp.status_code == 200
    # MIME 可能是 text/javascript 或 application/javascript
    ct = resp.headers["content-type"]
    assert "javascript" in ct or "text/plain" in ct
    assert "fetchJSON" in resp.text


def test_poc_unknown_404(api_client: TestClient) -> None:
    resp = api_client.get("/poc/does_not_exist.html")
    assert resp.status_code == 404
```

- [ ] **Step 2: 跑测试确认 fail**

```bash
uv run pytest tests/unit/test_static_poc_mount.py -v
```

Expected: 全部 404（mount 未启用）。

- [ ] **Step 3: 改 main.py 加 StaticFiles mount**

`src/amarket/main.py` 顶部 import 加：

```python
from pathlib import Path

from fastapi.staticfiles import StaticFiles
```

`create_app()` 函数最末（return app 之前）加：

```python
    # POC 静态目录 mount（M3b — 同源避 CORS）
    poc_dir = Path(__file__).resolve().parents[2] / "poc"
    if poc_dir.is_dir():
        app.mount("/poc", StaticFiles(directory=poc_dir, html=True), name="poc")
```

> `parents[2]` 解释：`src/amarket/main.py` → parents[0]=amarket, parents[1]=src, parents[2]=项目根。

- [ ] **Step 4: 跑测试确认 pass**

```bash
uv run pytest tests/unit/test_static_poc_mount.py -v
```

Expected: 3 passed。

- [ ] **Step 5: ruff + mypy**

```bash
uv run ruff check src/amarket/main.py tests/unit/test_static_poc_mount.py
uv run mypy src/amarket/main.py
```

Expected: 0 errors。

- [ ] **Step 6: commit**

```bash
git -C C:/AI/Claude/Project_Amarket add src/amarket/main.py tests/unit/test_static_poc_mount.py
git -C C:/AI/Claude/Project_Amarket commit -m "feat(m3b): mount poc/ as static under /poc (same-origin frontend)"
```

---

## Task 11: 前端 `shared.js` — `startAutoRefresh` + polling 状态持久化

**Files:**
- Modify: `poc/assets/js/shared.js`

- [ ] **Step 1: 加 3 个新函数 + 导出**

在 `poc/assets/js/shared.js` 的 `function checkViewport()` 之后、`global.Amarket = ...` 之前，新增：

```javascript
  /**
   * 自动刷新工具（M3b polling）。
   * @param {number} intervalMs - 间隔毫秒
   * @param {Function} fn - 每 tick 调用（应为 async；忽略返回值；异常会被吞掉但 console.warn）
   * @returns {{stop: () => void}} 控制句柄
   */
  function startAutoRefresh(intervalMs, fn) {
    let stopped = false;
    let timer = null;
    async function tick() {
      if (stopped) return;
      try { await fn(); } catch (e) { console.warn('[autorefresh]', e); }
      if (!stopped) timer = setTimeout(tick, intervalMs);
    }
    timer = setTimeout(tick, intervalMs);
    return { stop() { stopped = true; if (timer) clearTimeout(timer); } };
  }

  const POLLING_LS_KEY = 'amarket.polling.enabled';

  /** 读 polling 开关（持久到 localStorage，默认 false）。 */
  function isPollingEnabled() {
    try { return localStorage.getItem(POLLING_LS_KEY) === '1'; }
    catch { return false; }
  }

  /** 写 polling 开关；返回新值。 */
  function setPollingEnabled(enabled) {
    try {
      localStorage.setItem(POLLING_LS_KEY, enabled ? '1' : '0');
    } catch { /* ignore */ }
    return enabled;
  }
```

修改 `global.Amarket = {...}` 把这 3 个新函数加入：

```javascript
  global.Amarket = {
    fetchJSON, formatNumber, formatChangePct, formatDateTime, formatTime,
    timeAgo, stars, sentimentClass, alertTagClass, showBanner,
    getQueryParam, startClock, checkViewport,
    startAutoRefresh, isPollingEnabled, setPollingEnabled,
  };
```

- [ ] **Step 2: 浏览器手动验证（可在 Task 14 一起做，这里仅 lint）**

不写自动化 JS 测试（POC 范围；浏览器 e2e 在 Task 14 集中验证）。

- [ ] **Step 3: 通过 shared.js 不破坏现有页面 smoke check**

```bash
uv run pytest tests/unit/test_static_poc_mount.py::test_poc_shared_js_served -v
```

Expected: 1 passed（断言里有 `fetchJSON`，仍存在）。

- [ ] **Step 4: commit**

```bash
git -C C:/AI/Claude/Project_Amarket add poc/assets/js/shared.js
git -C C:/AI/Claude/Project_Amarket commit -m "feat(m3b): shared.js — startAutoRefresh + polling localStorage toggle"
```

---

## Task 12: `nav.js` — LIVE 占位变可点 polling toggle

**Files:**
- Modify: `poc/assets/js/nav.js`

- [ ] **Step 1: 改 render() 内的 LIVE span 为可点 button**

在 `poc/assets/js/nav.js` 的 `render()` 中，把：

```javascript
      <div class="topbar-right">
        <span class="live-indicator">
          <span class="live-dot"></span>
          LIVE
        </span>
        <span id="topbar-clock">--:--:--</span>
      </div>
```

改为：

```javascript
      <div class="topbar-right">
        <button id="polling-toggle" class="live-indicator" type="button" aria-label="切换自动刷新">
          <span class="live-dot"></span>
          <span id="polling-label">LIVE</span>
        </button>
        <span id="topbar-clock">--:--:--</span>
      </div>
```

并在 `render()` 末尾、`document.addEventListener('DOMContentLoaded', render)` **之前**，加 button 的事件绑定：

```javascript
    const toggleBtn = document.getElementById('polling-toggle');
    const labelEl = document.getElementById('polling-label');
    if (toggleBtn && window.Amarket) {
      const sync = () => {
        const on = window.Amarket.isPollingEnabled();
        toggleBtn.classList.toggle('on', on);
        toggleBtn.classList.toggle('off', !on);
        if (labelEl) labelEl.textContent = on ? 'LIVE' : 'PAUSED';
      };
      sync();
      toggleBtn.addEventListener('click', () => {
        const next = !window.Amarket.isPollingEnabled();
        window.Amarket.setPollingEnabled(next);
        sync();
        // 广播一次自定义事件，每页 init 里监听决定是否重启 polling
        document.dispatchEvent(new CustomEvent('amarket:polling-changed', { detail: { enabled: next } }));
      });
    }
```

- [ ] **Step 2: 微调 theme-okx.css，加 PAUSED 视觉**

确保 `poc/assets/css/theme-okx.css` 已有的 `.live-indicator` / `.live-dot` 在 `.off` 状态下：在文件末尾追加：

```css
/* M3b polling toggle 状态样式 */
.live-indicator { cursor: pointer; border: none; outline: none; background: transparent; }
.live-indicator.off .live-dot { animation: none; background: #4a4d55; box-shadow: none; }
.live-indicator.off { color: #7a7d85; }
```

> 备注：如果 theme-cyberpunk.css 也想支持 toggle，本 task 不改；params.html 没用 nav.js，所以 cyberpunk 不受影响。

- [ ] **Step 3: 手动 sanity（启完 server 后看到按钮可点；自动化 e2e 留 Task 14）**

通过现有 mount 测试确认 nav.js 还能被 serve：

```bash
uv run pytest tests/unit/test_static_poc_mount.py -v
```

Expected: 3 passed。

- [ ] **Step 4: commit**

```bash
git -C C:/AI/Claude/Project_Amarket add poc/assets/js/nav.js poc/assets/css/theme-okx.css
git -C C:/AI/Claude/Project_Amarket commit -m "feat(m3b): nav.js LIVE → clickable polling toggle (persists in localStorage)"
```

---

## Task 13: 5 个 page JS — fetch URL 切真 + 接 polling 事件

**承诺兑现**：spec §0 / spec §10 — **每页改 ≤ 6 行**。

**Files:**
- Modify: `poc/assets/js/pages/index.js`
- Modify: `poc/assets/js/pages/news.js`
- Modify: `poc/assets/js/pages/news-detail.js`
- Modify: `poc/assets/js/pages/sectors.js`
- Modify: `poc/assets/js/pages/reports.js`

### 13.1 index.js

- [ ] **Step 1: 改 fetch URL + 接 polling 事件**

`poc/assets/js/pages/index.js` 中：

- 原来 4 个 `A.fetchJSON('assets/data/...')` 改成调 `/api/dashboard/summary` + `/api/dashboard/sectors` + `/api/alerts`。dashboard/summary 已经聚合，多数字段一次拿到，可以删 news / alerts 重复 fetch。

把 `init()` 中：

```javascript
        const [dashboard, news, alerts, sectors] = await Promise.all([
          A.fetchJSON('assets/data/dashboard.json'),
          A.fetchJSON('assets/data/news.json'),
          A.fetchJSON('assets/data/alerts.json'),
          A.fetchJSON('assets/data/sectors.json'),
        ]);
```

改成：

```javascript
        const [summary, sectorsResp] = await Promise.all([
          A.fetchJSON('/api/dashboard/summary'),
          A.fetchJSON('/api/dashboard/sectors'),
        ]);
        const dashboard = summary;
        const news = summary.latest_news || [];
        const alerts = [...(summary.p0_alerts || []), ...(summary.p1_alerts || [])];
        const sectors = sectorsResp;
```

并在 `init()` 末尾、`} catch` **之前**插入 polling 集成：

```javascript
        // M3b polling 集成
        if (A.isPollingEnabled()) this._startPolling();
        document.addEventListener('amarket:polling-changed', (e) => {
          if (e.detail.enabled) this._startPolling();
          else this._stopPolling();
        });
```

并在对象内（getter 之间或之后）加方法：

```javascript
    _polling: null,
    _startPolling() {
      if (this._polling) return;
      this._polling = A.startAutoRefresh(30000, () => this.init());
    },
    _stopPolling() {
      if (this._polling) { this._polling.stop(); this._polling = null; }
    },
```

- [ ] **Step 2: 没有自动化 JS 测试 — 留 Task 14 一起跑端到端 smoke**

- [ ] **Step 3: commit（单独 commit 便于 review）**

```bash
git -C C:/AI/Claude/Project_Amarket add poc/assets/js/pages/index.js
git -C C:/AI/Claude/Project_Amarket commit -m "feat(m3b): index.js — switch to /api/* + 30s polling"
```

### 13.2 news.js

- [ ] **Step 1: 改 fetch URL**

`poc/assets/js/pages/news.js` 中：

```javascript
        this.news = await A.fetchJSON('assets/data/news.json');
```

改为：

```javascript
        const resp = await A.fetchJSON('/api/news?limit=200');
        this.news = resp.items || [];
```

并在 `init()` 末尾加 polling 集成（同 index.js 模板）：

```javascript
        if (A.isPollingEnabled()) this._startPolling();
        document.addEventListener('amarket:polling-changed', (e) => {
          if (e.detail.enabled) this._startPolling();
          else this._stopPolling();
        });
```

在 return 的对象内加：

```javascript
    _polling: null,
    _startPolling() {
      if (this._polling) return;
      this._polling = A.startAutoRefresh(30000, () => this.init());
    },
    _stopPolling() {
      if (this._polling) { this._polling.stop(); this._polling = null; }
    },
```

- [ ] **Step 2: commit**

```bash
git -C C:/AI/Claude/Project_Amarket add poc/assets/js/pages/news.js
git -C C:/AI/Claude/Project_Amarket commit -m "feat(m3b): news.js — switch to /api/news + 30s polling"
```

### 13.3 news-detail.js

- [ ] **Step 1: 改 fetch URL**

`poc/assets/js/pages/news-detail.js` 中：

```javascript
        this.news = await A.fetchJSON(`assets/data/news-detail-${id}.json`);
```

改为：

```javascript
        this.news = await A.fetchJSON(`/api/news/${id}`);
```

并把 404 友好提示从 "M3a 只 dump 了 5 条..." 改成更通用：

```javascript
        if (e.message.includes('404')) {
          this.error = `新闻 #${id} 不存在或已被删除`;
```

详情页不需要 polling（单条静态内容），不加 polling 集成。

- [ ] **Step 2: commit**

```bash
git -C C:/AI/Claude/Project_Amarket add poc/assets/js/pages/news-detail.js
git -C C:/AI/Claude/Project_Amarket commit -m "feat(m3b): news-detail.js — switch to /api/news/{id}"
```

### 13.4 sectors.js

- [ ] **Step 1: 改 fetch URL + window 切换接 API**

`poc/assets/js/pages/sectors.js` 中：

```javascript
        [sectorsData, allNews] = await Promise.all([
          A.fetchJSON('assets/data/sectors.json'),
          A.fetchJSON('assets/data/news.json'),
        ]);
```

改成：

```javascript
        const [sectorsResp, newsResp] = await Promise.all([
          A.fetchJSON(`/api/dashboard/sectors?window=${this.window}`),
          A.fetchJSON('/api/news?limit=200'),
        ]);
        sectorsData = sectorsResp;
        allNews = newsResp.items || [];
```

把 `this.$watch('dimension', ...)` 之后加：

```javascript
        // M3b — window 切换重新拉
        this.$watch('window', async () => {
          try {
            sectorsData = await A.fetchJSON(`/api/dashboard/sectors?window=${this.window}`);
            this.sectorsList = sectorsData.sectors;
            this.renderChart();
          } catch (e) { A.showBanner(`刷新失败：${e.message}`); }
        });
        // polling
        if (A.isPollingEnabled()) this._startPolling();
        document.addEventListener('amarket:polling-changed', (e) => {
          if (e.detail.enabled) this._startPolling();
          else this._stopPolling();
        });
```

加 polling 方法：

```javascript
    _polling: null,
    _startPolling() {
      if (this._polling) return;
      this._polling = A.startAutoRefresh(30000, () => this.init());
    },
    _stopPolling() {
      if (this._polling) { this._polling.stop(); this._polling = null; }
    },
```

- [ ] **Step 2: commit**

```bash
git -C C:/AI/Claude/Project_Amarket add poc/assets/js/pages/sectors.js
git -C C:/AI/Claude/Project_Amarket commit -m "feat(m3b): sectors.js — switch to /api/dashboard/sectors + window switch live"
```

### 13.5 reports.js

- [ ] **Step 1: 改 fetch URL**

`poc/assets/js/pages/reports.js` 中：

```javascript
        const data = await A.fetchJSON('assets/data/reports.json');
        this.today = data.today || '';
        this.reportsByKind = data.reports_by_kind || {};
```

改为：

```javascript
        const data = await A.fetchJSON('/api/reports/today');
        this.today = data.today || '';
        this.reportsByKind = data.reports_by_kind || {};
```

（`/api/reports/today` 已经返回 `today + reports_by_kind` 形状一致，0 schema 改动。）

reports 页不加 polling（日报固定时段，30s 没必要）。

- [ ] **Step 2: commit**

```bash
git -C C:/AI/Claude/Project_Amarket add poc/assets/js/pages/reports.js
git -C C:/AI/Claude/Project_Amarket commit -m "feat(m3b): reports.js — switch to /api/reports/today"
```

---

## Task 14: 端到端 smoke 测试 + 全套测试 + 覆盖率

**Files:**
- (no code change — verification only)

- [ ] **Step 1: 跑全套测试**

```bash
uv run pytest -x --cov=src/amarket --cov-report=term-missing
```

Expected:
- 测试数从 216 涨到约 240+（本 plan 加了约 27 个测试：6 ReportRepo + 3 SectorTrendRepo + 5 SectorTrendService + 1 schema + 4 sectors API + 3 movers API + 3 summary API + 8 reports API + 3 static mount = 36；实际可能 30+）
- 全绿，覆盖率不下降（M2 base ≈ 87.95%）

- [ ] **Step 2: 起后端，浏览器验证 5 页面读真实 API**

新 terminal：

```bash
uv run uvicorn amarket.main:app --port 8080
```

浏览器开（注意现在端口 8080，路径 `/poc/`，不再用 `python -m http.server 8090`）：

- http://127.0.0.1:8080/poc/index.html — 9 区域全部有数据；点击 topbar LIVE，应切换 LIVE↔PAUSED
- http://127.0.0.1:8080/poc/news.html — 新闻流，5 维度筛选 + 3 排序
- http://127.0.0.1:8080/poc/news-detail.html?id=1 — 替换 1 为实际 news_id（看上一页里的）
- http://127.0.0.1:8080/poc/sectors.html — 14 板块 treemap；切 window 1h/4h/1d 看 news_count_24h 变化
- http://127.0.0.1:8080/poc/reports.html — 6 时段（M3b 阶段大部分 null，盘前可能也是 null 因为 DB 里没真实 Report 数据；UI 应灰禁用而不崩）

- [ ] **Step 3: API 文档 sanity**

http://127.0.0.1:8080/docs — 看 Swagger UI，确认 M3b 新端点都在：
- `/api/dashboard/summary`
- `/api/dashboard/sectors`
- `/api/dashboard/movers`
- `/api/reports`
- `/api/reports/{report_id}`
- `/api/reports/today`
- `/api/reports/today/{kind}`

- [ ] **Step 4: 覆盖率 + lint 总 check**

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src/
uv run pytest --cov=src/amarket --cov-report=term
```

Expected: 0 errors, 全绿。如果覆盖率掉到 < 85% 看下哪个新模块没被测覆盖，补 1-2 个测试。

- [ ] **Step 5: 验证 poc/assets/data/*.json 仍存在但不再被前端用**

```bash
ls C:/AI/Claude/Project_Amarket/poc/assets/data/
```

Expected: 11 文件仍在。**保留**作为 fallback / debug 用（不删；M3b 接 API 失败时仍可手动 `dump_poc_fixtures.py` 跑出来对照）。

---

## Task 15: 收尾 — 更新 PROJECT_STATE / CHANGELOG / session log + PR

**Files:**
- Modify: `docs/PROJECT_STATE.md`
- Modify: `CHANGELOG.md`
- Create: `docs/sessions/2026-06-25-13-m3b-dashboard-api.md`

- [ ] **Step 1: 更新 PROJECT_STATE.md**

把"下次 Session 必读"段标记 M3 整体完成（M3a + M3b = M3 完成），下次 Session 入口指向 **M4 — 真实推送 + APScheduler + 6 时段日报**。把 `## 当前阶段` 的"M3a 完整收官"改为"**M3 完成（M3a + M3b）**"，把 Sprint 表里的 M3b 状态从 📋 改为 ✅。

具体改三处：
1. `Last Updated` → 改成今天日期 + "Session 13 — M3b 完整收官"
2. `Next Action Owner` → 改 next action 为"开 M4"
3. 把"立刻可做"段从 M3b 描述改为 M4 描述

- [ ] **Step 2: 更新 CHANGELOG.md**

在 `## [Unreleased]` 下面新增一段：

```markdown
### Added — M3b 完整收官（看板 API 补齐 + 前端 fetch 切真）（2026-06-25, Session 13）

**后端 — 5 类新端点 + 2 Repo + 1 Service：**
- `src/amarket/repositories/report_repo.py` — list / get / today_by_kind / list_today
- `src/amarket/repositories/sector_trend_repo.py` — bulk_upsert / latest_for_sectors
- `src/amarket/services/dashboard/sector_trend.py` — Phase 1 简化版（news_heat 从 NewsAnalysis 反查；change_pct M4 才填；14 板块 stub 市值权重）
- `src/amarket/api/dashboard.py` 扩 3 端点：`GET /summary`、`GET /sectors`、`GET /movers`
- `src/amarket/api/reports.py` 新 router：`GET /api/reports`、`/{id}`、`/today`、`/today/{kind}`

**后端 — FastAPI 同源 mount：**
- `app.mount("/poc", StaticFiles(directory="poc", html=True))` → 浏览器 `http://127.0.0.1:8080/poc/*` 直接读前端

**前端 — fetch URL 切真 + polling toggle：**
- `shared.js` 加 `startAutoRefresh / isPollingEnabled / setPollingEnabled`
- `nav.js` 把占位 LIVE 改成可点 polling toggle，状态持久化到 localStorage
- 5 个 page JS：每页 1-2 行 fetch URL 改成 `/api/*`；index / news / sectors 接 30s polling 事件

**测试 / 覆盖率：**
- 新增 ~30 个测试（ReportRepo / SectorTrendRepo / SectorTrendService / dashboard endpoints / reports endpoints / static mount）
- 总测试数 216 → 250+；覆盖率维持 ≥ 85%
```

- [ ] **Step 3: 写 session 日志**

`docs/sessions/2026-06-25-13-m3b-dashboard-api.md`：包含
- 关键事件（按时间顺序：plan → 15 task 实施 → 端到端 smoke → PR）
- 关键决策（SectorTrendService Phase 1 简化范围、movers Phase 1 留空、详情/日报不 polling 的取舍）
- 产出（文件清单 + commit 列表）
- 测试结果（个数、覆盖率）
- 下次 session 接力点：**M4 — 真实推送 + APScheduler + 6 时段日报基础**

- [ ] **Step 4: commit docs**

```bash
git -C C:/AI/Claude/Project_Amarket add docs/PROJECT_STATE.md CHANGELOG.md docs/sessions/2026-06-25-13-m3b-dashboard-api.md
git -C C:/AI/Claude/Project_Amarket commit -m "docs: session 13 wrap — M3b complete (dashboard API + frontend live)"
```

- [ ] **Step 5: push 分支**

```bash
git -C C:/AI/Claude/Project_Amarket push -u origin feat/m3b-dashboard-api
```

- [ ] **Step 6: 开 PR**

```bash
cd C:/AI/Claude/Project_Amarket && gh pr create --title "feat(m3b): Dashboard API + frontend live wiring — M3 complete" --body "$(cat <<'EOF'
## Summary
- 后端补齐 `/api/dashboard/{summary,sectors,movers}` + `/api/reports/*`（list/detail/today）；新 `ReportRepo` + `SectorTrendRepo` + `SectorTrendService`（Phase 1 简化版）
- FastAPI `app.mount("/poc", StaticFiles)` 实现同源 — 浏览器开 `http://127.0.0.1:8080/poc/` 即用，避 CORS
- 前端每页 1-2 行 fetch URL 切到 `/api/*`；topbar LIVE 改成可点 polling toggle（localStorage 持久化）；index/news/sectors 接 30s polling

## 完成 M3 全部范围
- ✅ M3a（已 merge — PR #10/#12/#13）：6 个 POC 页面（5 OKX + 1 cyberpunk）
- ✅ M3b（本 PR）：API 补齐 + 前端 fetch 切真

## Test plan
- [x] `uv run pytest` — 全套绿（新增约 30 测试，216 → 250+）
- [x] 覆盖率 ≥ 85%
- [x] 浏览器手动 5 页面 smoke：summary 聚合 / sectors window 切换 / movers 列表 / today reports 灰禁用 / polling toggle 持久化
- [x] `/docs` Swagger UI 含全部 M3b 端点
- [x] ruff / mypy 全绿
- [x] poc/assets/data/*.json 仍保留作 fallback debug

## 后续
M3b 完成后下次 session 开 **M4 — 真实推送 + APScheduler + 6 时段日报**。

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 7: 等 CI 5/5 → squash merge**

```bash
gh pr checks --watch
```

Expected: 5/5 全绿，自助 `gh pr merge --squash --delete-branch` 或等用户 review 后 merge。

---

## 结束

完成 M3b 后：
- M3 整体收官（M3a + M3b 都 ✅）
- Phase 1 进度 6/7 milestones（M0/M0+/M1/M2/M3a/M3b）
- 下次 Session 入口：**M4 — 真实推送 + APScheduler + 6 时段日报**

**关键不变式（M3b 验收必须保持）：**
1. 实盘下单代码 = 0
2. `poc/assets/data/*.json` 保留可读但前端不再依赖
3. 旧 endpoint `/api/dashboard/market-status` 与 `/api/dashboard/news-sources` 不变
4. 现有测试全绿
5. main 分支只通过 PR 合入

**End of Plan**
