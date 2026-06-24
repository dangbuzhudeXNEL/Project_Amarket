# Project State

**Last Updated**: 2026-06-24 (Session 11 结束 — Brainmaster fix + P1 backlog 清零)
**Updated By**: Claude (Opus 4.7, 1M ctx) + User + superpowers:code-reviewer agent
**Next Action Owner**: 👤 **用户** + **Claude**（下次 session 开 M3 静态 POC 页面）

---

## 🎯 下次 Session 必读：3 件事

### 1. 当前状态
- ✅ **main 上 CI 绿**（HEAD `8e644bc`，含 PR #1/2/3/4/5 全部合并）
- ✅ **M2 已完成 + 工程债务清零**：reviewer 4 个 P1 全收，剩 6 个 P2 nice-to-have
- ✅ **Brainmaster 真跑通**：Windows 子进程 2 个 bug 已修（permission-mode + stdin）
- ✅ **DB 现状**：130 NewsItem + 12 行情 + 130 NewsEvent + 130 NewsAnalysis（含 5 行真 AI）+ 73 Alerts
- ✅ **Phase 1 完成 4/7 milestones**（M0/M0+/M1/M2）

### 2. 立刻可做 — **下次 session 开 M3 静态 POC 页面**
Spec v3 §10.1 定义 5 个静态 HTML 页面：
1. **首页** — 状态栏 + 指数 + 重要新闻 + 板块趋势
2. **新闻流页** — 长列表，时间/重要性排序
3. **详情页** — 单条新闻 + 完整 AI 分析
4. **板块热力图** — 14 个板块热度可视化
5. **日报页** — 6 时段日报展示

**启动建议**：用 `superpowers:brainstorming` 先走一遍（新模块设计要 brainstorm），确定技术选型（vanilla HTML+JS vs 框架）+ 数据源（fetch /api/* vs mock）+ POC 目录结构。

### 3. M3 启动前的待办（无）
P1 backlog 已全清。M3 可以直接开干。

### 4. 严禁动作
- ❌ 在 main 上直接 commit（CI hotfix 是特例，未来都走 fix/* 分支 + PR）
- ❌ Force push 任何分支
- ❌ 跳过 Session 启动 Checklist
- ❌ 引入实盘下单代码

---

## 当前阶段

- **Spec**: #1 v3 — A 股实时新闻分析与行情看板（小组联合版）
- **Phase**: 🟢 **Phase 1 实施中 — M2 完成 + 工程债务清零（57%）**
- **Milestone**: **M2 已完成 + 4 个 P1 fix merge 到 main** → 准备 M3
- **Sprint progress**:
  - ✅ M0 项目骨架 + 工具链 + CI + DB baseline + FastAPI + Streamlit
  - ✅ M0+ 通知预留端到端
  - ✅ M1 数据基座
  - ✅ M2 智能层（11/11 子任务完成 + reviewer P1 全收）⭐
  - 📋 M3 静态 HTML POC 页面（下次 session 启动）
  - 📋 M4/M5/M6 待启动
- **Session count**: 11 sessions（详见 `docs/sessions/`）

---

## 活跃任务

**Phase 1 剩余 milestones**：

| M | 内容 | 状态 | 预估 |
|---|------|------|------|
| **M3** | 静态 HTML POC 看板（首页 / 新闻流 / 详情页 / 板块热力图 / 日报页）| 📋 **下次启动** | 2-3 session |
| **M4** | 真实推送 + APScheduler 调度 — 把分析结果实际推到企微/飞书 | 📋 待启动 | 2 session |
| **M5** | 6 时段自动日报（盘前/早盘/午间/尾盘/收盘/晚间）| 📋 待启动 | 2 session |
| **M6** | 参数配置模块（版本/回滚/审计 — Phase 1 三大模块之三）| 📋 待启动 | 1-2 session |

### 完成的 backlog（M2 reviewer P1）
- [x] P1-1 NewsAnalysisService skip provider-aware
- [x] P1-2 AlertService 升档 supersede
- [x] P1-3 黑名单 → skip alert
- [x] P1-5 analyze_batch 每 task 独立 session

### 剩余 nice-to-have backlog（reviewer P2，无阻塞）
- [ ] P2-1 `_compute_top_source` SQL GROUP BY 优化
- [ ] P2-2 `_source_cache` LRU 上限
- [ ] P2-3 SimHash distance==threshold 边界测试
- [ ] P2-4 market_hours 4 个端点边界 + 周末测试
- [ ] P2-5 DeepSeek json_object 中文 enum 真实 API 验证
- [ ] P2-6 `processed_by` 字符串集中常量

---

## 最近 5 个关键决策（按时间倒序）

1. **2026-06-24 (Session 11)**：**收 Reviewer P1 backlog 4 个 fix** + **Windows Brainmaster 2 个 bug 修复** — `--permission-mode acceptEdits` + prompt 走 stdin
2. **2026-06-24 (Session 11)**：**Demo Brainmaster 真跑通** — 5 条新闻 AI 分析，明显优于规则（关联到 A 股个股代码 + reasoning）
3. **2026-06-21 (Session 10)**：**M2 完整完成 + code-reviewer 通过** — P0 + P1-4 已修，4 P1 留 backlog
4. **2026-06-21 (Session 09)**：**PR #1 立即 self-merge** + classifier 子串重叠允许双计数 + scorer confidence 规则路径固定 3
5. **2026-06-21 (Session 08)**：**部署文档独立 PR** + **Superpowers 使用边界协议**

---

## 阻塞 / 待用户/小组输入

**无硬阻塞** — M3 可以直接启动。

**软阻塞**（M4 启动前必须）：
- 企微 / 飞书 webhook（M4 真实推送时用）
- LLM API key（已可选；当前 Brainmaster 路径无需，但配 API key 后 AI 并发更快）

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
| 2026-06-21 (Session 09) | PR #1 合 main + M2-c Classifier + M2-d Scorer |
| 2026-06-21 (Session 10) | M2 全部完成（e/f/h/i/j/k）+ 端到端 pipeline + code review 通过 |
| **2026-06-24 (Session 11)** | **Brainmaster Windows fix（PR #4）+ Reviewer P1 backlog 全清（PR #5）** |

---

## 速查表

- **当前 spec**: `docs/superpowers/specs/2026-06-19-spec1-v3-merged.md`
- **当前 branch**: `main` (commit `8e644bc`)
- **main HEAD**: `8e644bc` (CI 绿 ✅，含 PR #1/2/3/4/5)
- **Phase / Milestone**: Phase 1 / **M2 + P1 backlog 已完成** → 准备 M3 POC 页面
- **DB 现状**:
  - 130 NewsItem + 12 行情快照 + 130 NewsEvent
  - 130 NewsAnalysis（125 `rule` + **5 `agent:news-classifier-realtime`** 真 AI）
  - 73 Alert（1 P0 + 1 P1 + 71 P2）
- **测试 / 覆盖率**: **207 tests / 87.95% coverage**
- **GitHub**: https://github.com/dangbuzhudeXNEL/Project_Amarket
- **本地路径**: `C:\AI\Claude\Project_Amarket`

---

## 命令速查（Phase 1 M2 完成后）

```bash
# 拉数据
uv run amarket collect market           # 6 个 A 股指数入库
uv run amarket collect news             # 默认 5min 窗口
uv run amarket collect news --full      # 12h 窗口

# 智能分析 pipeline（M2 完整）
uv run amarket dedupe news              # L1/L2/L3 三层去重
uv run amarket analyze news             # AI + 规则 + alerts 决策（一条 CLI 全链路）
uv run amarket analyze news --no-ai     # 强制规则路径
uv run amarket analyze news --reanalyze --limit 500  # 重处理（P1-1 修了之后，rule→AI 自动重跑）

# 启动整套
./start.bat                              # Windows
./start.sh                               # Linux/macOS
# → API:       http://127.0.0.1:8080/docs
# → /api/news: http://127.0.0.1:8080/api/news?limit=20
# → /api/alerts: http://127.0.0.1:8080/api/alerts?level=P0
# → Dashboard: http://127.0.0.1:8501

# 测试 + 覆盖率
uv run pytest -x
uv run pytest --cov=src/amarket --cov-report=term

# Lint / 类型
uv run ruff check . --fix
uv run ruff format .
uv run mypy src/
```

## 端到端 demo（一条命令跑完整 pipeline）

```bash
uv run amarket dedupe news --threshold 3       # 去重
uv run amarket analyze news --no-ai --limit 200 --reanalyze   # 规则路径分析 + 告警
# 或者：
uv run amarket analyze news --ai --limit 5     # AI 路径（5 条 ~3 分钟）
```

