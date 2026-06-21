# Project State

**Last Updated**: 2026-06-21 (Session 09 结束)
**Updated By**: Claude (Opus 4.7, 1M ctx) + User
**Next Action Owner**: 👤 **用户** + **Claude**（下次 session 继续 M2-e）

---

## 🎯 下次 Session 必读：3 件事

### 1. 当前状态
- ✅ **main 上 CI 绿**（HEAD `034bb6e`，包含 PR #1 部署文档）
- ✅ **DB 现状**：130 条新闻 + 12 条 A 股指数 + 130 个 NewsEvent
- ✅ **Dashboard 真实可用**
- ⏳ **当前在 `feat/m2-news-processing` 分支 (`599a765`)**：M2-a + M2-b + M2-c + M2-d + M2-g 已 commit
- ✅ **PR #1 部署文档**已合 main

### 2. 立刻可做（下次 session 开干）
**M2-e NewsAnalysis service** — 关键路径，把三件事串起来：
1. 收新闻 → 用 NewsClassifier (M2-c) 分类
2. 走 AIProvider (M2-g)：FallbackChain (Brainmaster → SDK) 拿深度分析
3. AI 全失败 → 用 SimpleRuleScorer (M2-d) 兜底
4. 结果写入 `news_analysis` 表（已存在 schema）

预估 1.5h。接通后整个 Phase 1 处理 pipeline 就贯通了。

### 3. 严禁动作
- ❌ 在 main 上直接 commit（CI hotfix 是特例，未来都走 fix/* 分支 + PR）
- ❌ Force push 任何分支
- ❌ 跳过 Session 启动 Checklist
- ❌ 引入实盘下单代码

---

## 当前阶段

- **Spec**: #1 v3 — A 股实时新闻分析与行情看板（小组联合版）
- **Phase**: 🟢 **Phase 1 实施中（已完成 M0/M0+/M1 + M2-a/b/c/d/g）**
- **Milestone**: **M2 进行中**（feature branch `feat/m2-news-processing`）
- **Sprint progress**:
  - ✅ M0 项目骨架 + 工具链 + CI + DB baseline + FastAPI + Streamlit
  - ✅ M0+ 通知预留端到端
  - ✅ M1 数据基座（16 表 + 3 新闻源 + akshare + 6 Repo + 4 API + CLI collect + viz）
  - ✅ M2-a 规则配置（keywords/sectors/classification YAML）
  - ✅ M2-g 双路径 AI 架构（Brainmaster + SDK + Fallback chain）
  - ✅ M2-b 三层去重 NewsDeduper
  - ✅ **M2-c NewsClassifier（规则一级 8 类 + 二级 14 板块 + 标的）⭐ 本 session**
  - ✅ **M2-d SimpleRuleScorer（importance/urgency/sentiment）⭐ 本 session**
  - ⏳ M2-e/f/h/i/j/k 剩 6 个子任务
  - 📋 M3/M4/M5/M6 待启动
- **Session count**: 9 sessions（详见 `docs/sessions/`）

---

## 活跃任务（feature branch 上的，下次 session 接力）

| ID | 任务 | 依赖 | 预估 |
|----|------|------|------|
| **M2-e** | NewsAnalysis service（编排 Classifier → AIProvider 或 Scorer → 写 news_analysis 表） | M2-c/d/g | 1.5h |
| M2-f | AlertService（P0-P3 决策表 + alerts 表写入） | M2-e | 1h |
| M2-h | API 升级（/api/news 带分析字段 + /api/alerts） | M2-e, M2-f | 1h |
| M2-i | Dashboard 升级（新闻列表显示标签/评分/告警等级 + 告警区） | M2-h | 1h |
| M2-j | 集成测试（**把 130 条真实新闻喂进 pipeline 验证**）⭐ | 所有上面 | 2h |
| M2-k | 收尾 commit + push + 写 session 日志 | — | 0.5h |

**M2 总剩余 ~7-8 小时 ≈ 1 个 session**。

---

## 最近 5 个关键决策（按时间倒序）

1. **2026-06-21 (Session 09)**：**PR #1 立即 self-merge** + **classifier 子串重叠允许双计数** + **scorer confidence 规则路径固定 3**
2. **2026-06-21 (Session 08)**：**部署文档独立 PR**（用户指定）+ **Superpowers 使用边界协议**
3. **2026-06-21 (Session 08)**：**M2-b 默认 threshold=3 保守对齐 spec**；中文标题需 8-10 才有意义召回；语义判断留 M2-e
4. **2026-06-19 (Session 07)**：**CI hotfix 直 push main**（`.gitattributes` + ruff format）
5. **2026-06-19 (Session 06)**：**Brainmaster 提前到 M2** — `AIProvider` 双路径架构 + agent 文件输出

---

## 阻塞 / 待用户/小组输入

**无硬阻塞** — 可以直接继续 M2-e。

**软阻塞**（M4 启动前确认即可）：
- 企微 / 飞书 webhook（M4 真实推送时用）
- LLM API key（M2-e 启动前最好配一个，否则只能走规则兜底）
- Claude CLI 在 PATH（Brainmaster 主路径，M2-e 启动前验证）

---

## 重要环境/配置变化（按时间正序）

| 时间 | 变化 |
|------|------|
| 2026-06-14 ~ Session 03 | Spec v1 → v2 → v3；从个人项目升格小组联合 |
| 2026-06-19 (Session 04) | uv 项目初始化，pin Python 3.12 |
| 2026-06-19 (Session 05) | M1：16 张表 + 3 新闻源 + akshare + Repo + API + CLI + viz |
| 2026-06-19 (Session 06) | feat/m0-project-skeleton 合 main；M2-a 规则 + M2-g AI 双路径 |
| 2026-06-19 (Session 07) | CI hotfix（`.gitattributes` + ruff format）；CI 绿 |
| 2026-06-21 (Session 08) | 本地部署文档 PR #1 + M2-b NewsDeduper 端到端 |
| **2026-06-21 (Session 09)** | **PR #1 合 main + M2-c Classifier + M2-d Scorer（38 tests, 真数据验证）** |

---

## 速查表

- **当前 spec**: `docs/superpowers/specs/2026-06-19-spec1-v3-merged.md`
- **当前 branch**: `feat/m2-news-processing` (commit `599a765`)
- **main HEAD**: `034bb6e` (CI 绿 ✅，含 PR #1)
- **Phase / Milestone**: Phase 1 / M2 进行中（M0/M0+/M1/M2-a/b/c/d/g 完成）
- **DB 现状**: 130 条新闻（sina 60 + eastmoney 50 + yahoo 20）+ 12 条 A 股指数 + 130 NewsEvent
- **测试 / 覆盖率**: **168 tests / 88.90% coverage**（classifier 93% / scorer 95% / deduper 93%）
- **GitHub**: https://github.com/dangbuzhudeXNEL/Project_Amarket
- **本地路径**: `C:\AI\Claude\Project_Amarket`

---

## 命令速查（M2-d 起可用）

```bash
# 拉数据
uv run amarket collect market           # 6 个 A 股指数入库
uv run amarket collect news             # 默认 5min 窗口
uv run amarket collect news --full      # 12h 窗口

# 去重（M2-b）
uv run amarket dedupe news              # 默认 limit=500 threshold=3
uv run amarket dedupe news --threshold 10

# 启动整套
./start.bat                              # Windows
./start.sh                               # Linux/macOS

# 测试 + 覆盖率
uv run pytest -x                        # 快速
uv run pytest --cov=src/amarket --cov-report=term

# Lint / 类型
uv run ruff check . --fix
uv run ruff format .
uv run mypy src/

# 通知
uv run amarket notify status
uv run amarket notify test wework

# 数据库
uv run alembic upgrade head
```

## 验证 classifier/scorer（M2-c/d 一次性脚本，跑了能看完整分布）

```bash
PYTHONIOENCODING=utf-8 uv run python -c "
from collections import Counter
from amarket.db.session import session_scope
from amarket.domain.models import NewsItem, NewsSource
from amarket.domain.enums import SourcePriority
from amarket.services.news.classifier import NewsClassifier
from amarket.services.news.scorer import SimpleRuleScorer
from sqlmodel import select

clf = NewsClassifier.from_config()
scorer = SimpleRuleScorer.from_config()

with session_scope() as s:
    items = list(s.exec(select(NewsItem)))
    src_lookup = {src.id: src for src in s.exec(select(NewsSource))}
    cats = Counter()
    for it in items:
        c = clf.classify(title=it.title, summary=it.summary)
        cats[c.primary_category.value] += 1
    for cat, n in cats.most_common():
        print(f'{cat}: {n}')
"
```
