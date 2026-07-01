# Project State

**Last Updated**: 2026-06-30 (Session 14 — PR #17 post-M3b polish 已 merge + Brainmaster agent B demo 实测通过)
**Updated By**: Claude (Opus 4.7, 1M ctx) + User
**Next Action Owner**: 👤 **用户** + **Claude**（下次 session 开 **M4-mini** = APScheduler + 行情/新闻调度 + SectorTrendService 写表）

---

## 🎯 下次 Session 必读：3 件事

### 1. 当前状态
- ✅ **main HEAD `f96b944`**（PR #17 已 merge — post-M3b polish 三件套：Alpine defer bug fix + `/api/news/{id}` 扩 NewsDetailDTO + sectors null UX fix）
- ✅ **Phase 1 完成 6/7 milestones**（M0/M0+/M1/M2/M3a/**M3b**）
- ✅ **POC 6 个页面全部上线** + fetch `/api/*` 真数据 + polling toggle + 同源 mount
- ✅ **news-detail 页现在显示完整 AI 分析**（6 评分 + 影响板块带权重 + 关联标的 + AI 推理 + 风险提示）
- ✅ **Brainmaster agent 路径实测**（Session 14）：20 条走 `agent:news-classifier-realtime`，**90% AI 成功率**，零 API key 成本，平均 ~15s/条
- ✅ **测试 / 覆盖率**：**253 tests / 87.97% coverage**

### 2. 立刻可做 — **下次 session 开 M4-mini（推荐路径）**

**M4-mini（1 session，无需你给配置）**：
- **APScheduler** 集成到 FastAPI lifespan（进程内运行）
- **行情快照调度**：交易时段每 5min `collect market`（chinese_calendar 判断交易日）
- **新闻轮询调度**：每 60s `collect news` → `dedupe` → `analyze`（走 Brainmaster agent）
- **SectorTrendService 写表调度**：每 15min 计算板块趋势 → 写 `sector_trends` 表 → sectors 页 `change_pct` **真正有值**
- **`/api/dashboard/scheduler-status`** 端点：last_run / next_run / 错误可视化

**M4-full 追加（后续 1 session，需要你给东西）**：
- 6 时段 ReportService（走 `daily-report-writer` agent 生成 Markdown）
- NewsPusher 真发企微/飞书（**需要你给 webhook URL**）

**已有现成基础**：
- notifiers (`wework_bot` / `lark_bot`) 已写好（M0+）— 只差 webhook URL 配置
- Report/AlertRepo 已就位（M3b）
- `/api/reports/*` 端点已能读（M3b）
- Brainmaster agent 路径已实测稳定（Session 14）— 单条 ~15s / 90% 成功率
- chinese_calendar 已在依赖里（M0 加的）

**启动建议**：直接进 `superpowers:writing-plans` 写 M4-mini plan。**不需要 brainstorm**（spec v3 §6.1.7/§17.1 已定义 + Session 14 实测数据给了并发/超时决策依据）。

### 3. 流程提醒
- M3 整体已收官（M3a + M3b 全 merge + PR #17 polish 全 merge）
- M4 之后进 M5（参数模块覆盖赛博朋克 demo）+ M6（集成测试 + 7 天试运行）

### 4. 严禁动作
- ❌ 在 main 上直接 commit（除少数特例）
- ❌ Force push 任何分支
- ❌ 跳过 Session 启动 Checklist
- ❌ 引入实盘下单代码

---

## 当前阶段

- **Spec**: #1 v3 — A 股实时新闻分析与行情看板（小组联合版）
- **Phase**: 🟢 **Phase 1 实施中 — M3 完成 + PR #17 polish（86%）**
- **Milestone**: **M3 整体收官（M3a + M3b + PR #17 polish 全部 merge）** → 准备 M4-mini
- **Sprint progress**:
  - ✅ M0 项目骨架 + 工具链 + CI + DB baseline + FastAPI + Streamlit
  - ✅ M0+ 通知预留端到端
  - ✅ M1 数据基座
  - ✅ M2 智能层（11/11 子任务完成 + reviewer P1 全收）
  - ✅ **M3a — POC 前端 6 页 + dump 脚本**（Session 12）
    - ✅ PR #10 M3a-PR1：框架 + 3 OKX 核心页 + 全量 mock dump
    - ✅ PR #12 fix：theme 不生效 bug 修复 + visual polish + 3 stub pages
    - ✅ PR #13 M3a-PR2：剩余 3 页（sectors/reports/params）+ 赛博朋克 theme
  - ✅ **M3b — 看板 API 补齐 + SectorTrendService + 前端切真 + polling toggle**（Session 13, PR #16）
  - ✅ **PR #17 post-M3b polish** — Alpine defer bug + `/api/news/{id}` detail 扩 + sectors null UX（Session 14 早期）
  - 📋 M4-mini 调度自动化（下次启动，1 session）
  - 📋 M4-full 推送 + 6 时段日报（等 webhook 配置，1 session）
  - 📋 M5/M6 待启动
- **Session count**: 14 sessions（详见 `docs/sessions/`）

---

## 活跃任务

**Phase 1 剩余 milestones**：

| M | 内容 | 状态 | 预估 |
|---|------|------|------|
| **M4-mini** | APScheduler + 行情/新闻调度 + SectorTrendService 写表（**无需 webhook/API key**）| 📋 **下次启动（推荐）** | 1 session |
| **M4-full** | 上面 + 6 时段 ReportService + NewsPusher 真推送（需要 webhook）| 📋 M4-mini 后 | 1 session |
| **M5** | 参数配置模块（覆盖 params.html 赛博朋克 demo） | 📋 待启动 | 1-2 session |
| **M6** | 集成测试 + 文档 + UML + 7 天试运行 | 📋 待启动 | 1-2 session |

### 已完成的 M3a 全部交付（合计 3 PR + 1 spec PR）
- **PR #9** spec 设计（821 行 spec）
- **PR #10** PR1 实现（13 文件 + 11 JSON）
- **PR #12** theme fix + 视觉 polish + 3 stub 占位页
- **PR #13** PR2 实现（3 真实页面 + cyberpunk theme）

### 已完成的 M3b 全部交付（PR #16 20 commits merged）
- 后端：dashboard 3 端点（summary / sectors / movers）+ reports 4 端点
- 后端：ReportRepo + SectorTrendRepo + SectorTrendService（Phase 1 简化版）
- 后端：9 DTO + main.py 同源 mount /poc
- 前端：5 个 page JS 切 `/api/*` + polling toggle + 30s 自动刷新
- 测试：+36 测试（216 → 252），coverage 87.95% → 87.97%

### 已完成的 PR #17 post-M3b polish（Session 14 早期，3 commits merged）
- fix: Alpine defer 加载顺序 bug — 6 个 POC HTML 去掉 page JS 的 `defer`
- feat: `/api/news/{id}` 返回 `NewsDetailDTO`（原来是精简 `NewsCardDTO`，缺 `ai_reasoning / related_sectors / related_symbols / risk_notes / content / related_news` 等 11 个"详情独有"字段）
- fix: sectors 页 `change_pct == null` 时显示 "—" + 中性灰（原来显示 "+null%" + 假绿）
- 新增 1 测试；总测试数 252 → 253

### 已完成的 Brainmaster agent B demo（Session 14 后期）
- `uv run amarket analyze news --reanalyze --limit 20 --concurrency 5`
- 结果：**18/20 AI 成功（90%）**、2 条 JSON parse 失败降级到 rule；新增 **2 P1 + 5 P2 alerts**
- 单条平均 ~15 秒（并发 5，总 ~90 秒）；零 API key 成本
- 质量：agent 能推理隐含语义（"洪水危机缓解 → 情绪中性"）、主动识别次生受影响板块（洪水 → 保险 + 水利建设）、给出具体标的（中国人保 / 太保 / 中石化 等）
- **给 M4 调度的量化决策依据**：每分钟最多 20 条 → 60s 轮询 + concurrency 5 够用；rule 降级链必须保留（10% 失败率）

### 剩余 nice-to-have backlog（M2 reviewer P2，无阻塞）
- [ ] P2-1 `_compute_top_source` SQL GROUP BY 优化
- [ ] P2-2 `_source_cache` LRU 上限
- [ ] P2-3 SimHash distance==threshold 边界测试
- [ ] P2-4 market_hours 4 个端点边界 + 周末测试
- [ ] P2-5 DeepSeek json_object 中文 enum 真实 API 验证
- [ ] P2-6 `processed_by` 字符串集中常量

---

## 最近 6 个关键决策（按时间倒序）

1. **2026-06-30 (Session 14)**：**M4 拆 M4-mini / M4-full** — mini 只做无外部依赖的调度部分（1 session、不需要 webhook / API key），full 加日报生成 + 真实推送（需要 webhook）；理由：避免被外部配置卡进度
2. **2026-06-30 (Session 14)**：**Brainmaster agent 路径实测通过** — 20 条测试 90% AI 成功、单条 15s、零 API key 成本；确认主 AI 路径就走 Brainmaster，SDK 只作 fallback
3. **2026-06-27~30 (Session 14)**：**PR #17 post-M3b polish** — 通过 gstack 浏览器 dogfood 发现 Alpine defer bug + `/api/news/{id}` 返回精简 DTO 隐藏 AI 分析 + sectors null UX 三个问题；一并修完 merge
4. **2026-06-25 (Session 13)**：**M3b 完整收官** — Dashboard API 全补齐（summary/sectors/movers/reports）+ 前端 5 页 fetch /api/* + 30s polling toggle + FastAPI mount /poc 同源 = M3 整体完成
5. **2026-06-24 (Session 12)**：**M3a 完整收官** — 6 个页面（5 OKX + 1 赛博朋克）+ mock dump 全部上线 + 用户验收通过（"赛博朋克很不错"）
6. **2026-06-24 (Session 12)**：**theme bug 修复 + 视觉 polish** — data-theme 从 body 移到 html；加 LIVE 脉动 / hero 大数字 / macro KPI 条 / cyan glow
7. **2026-06-24 (Session 12)**：**M3 拆分为 M3a 前端 / M3b API 后端**，M3a 又拆 PR1 (3 页框架) / PR2 (剩余 + 赛博朋克)
8. **2026-06-24 (Session 11)**：收 Reviewer P1 backlog 4 个 fix + Windows Brainmaster 2 个 bug 修复

---

## 阻塞 / 待用户/小组输入

**M4-mini 无硬阻塞** — 可以直接启动。

**M4-full 启动前必须（可与 M4-mini 并行准备）**：
- 企微 / 飞书 webhook URL（用于 NewsPusher）
- LLM API key（**可选，Brainmaster 主路径无需**；若想走 SDK fallback 提速再配）

**M4-mini 已解决的历史软阻塞**：
- ~~Brainmaster agent 路径是否稳定？~~ Session 14 实测 90% 成功率，可以生产用

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
| 2026-06-24 (Session 11) | Brainmaster Windows fix（PR #4）+ Reviewer P1 backlog 全清（PR #5） |
| 2026-06-24 (Session 12) | M3 brainstorm + spec（PR #9）+ M3a-PR1 实现（PR #10）+ theme fix + polish（PR #12）+ M3a-PR2 实现（PR #13）= M3a 完整收官 |
| 2026-06-25 (Session 13) | M3b 完整收官（dashboard API 5 类 + 2 Repo + 1 Service + 前端 fetch 切真 + polling toggle） |
| **2026-06-27~30 (Session 14)** | **PR #17 polish（Alpine defer / detail endpoint / sectors null UX）+ Brainmaster agent B demo 90% 成功率**；DB 手动 refresh：230 news / 203 analyses (23 agent + 180 rule) / 103 alerts |

---

## 速查表

- **当前 spec**: `docs/superpowers/specs/2026-06-19-spec1-v3-merged.md`（v3 主）
- **M3a spec**: `docs/superpowers/specs/2026-06-24-m3a-poc-pages-design.md`
- **M3a-PR1 plan**: `docs/superpowers/plans/2026-06-24-m3a-pr1-frame-and-core.md`
- **M3b plan**: `docs/superpowers/plans/2026-06-25-m3b-dashboard-api.md`
- **当前 branch**: `main`（工作区干净）
- **main HEAD**: `f96b944` — `fix(poc): post-M3b polish — Alpine load order + full news-detail AI + sectors null UX (#17)`
- **Phase / Milestone**: Phase 1 / **M3 完整收官 + PR #17 polish 全 merge** → 准备 M4-mini
- **DB 现状**（Session 14 refresh 后）:
  - **230 NewsItem** + 18 行情快照 + 229 NewsEvent
  - **203 NewsAnalysis**（180 `rule` + 23 `agent:news-classifier-realtime`）
  - **103 Alert**（1 P0 + 3 P1 + 99 P2）
- **POC 现状**（M3 完整）:
  - 6 个 HTML 页面（5 OKX + 1 cyberpunk）+ **fetch /api/* 真数据 + 完整 AI 分析显示**
  - 11 mock JSON 文件保留作 fallback debug（dump 脚本仍可用）
  - 2 CSS 主题（theme-okx + theme-cyberpunk）
  - 同源 mount：`http://127.0.0.1:8080/poc/*.html`（无需 `python -m http.server`）
- **测试 / 覆盖率**: **253 tests / 87.97% coverage**
- **GitHub**: https://github.com/dangbuzhudeXNEL/Project_Amarket
- **本地路径**: `C:\AI\Claude\Project_Amarket`

---

## 命令速查（Phase 1 M3 完成后）

```bash
# 拉数据
uv run amarket collect market           # 6 个 A 股指数入库
uv run amarket collect news             # 默认 5min 窗口
uv run amarket collect news --full      # 12h 窗口

# 智能分析 pipeline
uv run amarket dedupe news              # L1/L2/L3 三层去重
uv run amarket analyze news             # AI + 规则 + alerts 决策
uv run amarket analyze news --no-ai     # 强制规则路径
uv run amarket analyze news --reanalyze --limit 500

# POC 前端（M3 完整 6 页 + fetch /api/* 真数据）
uv run python scripts/dump_poc_fixtures.py --pretty    # （可选）DB → poc/assets/data/*.json fallback
# 启动主服务后浏览器直接开（同源 mount）：
# - http://127.0.0.1:8080/poc/index.html        (Dashboard 首页)
# - http://127.0.0.1:8080/poc/news.html         (新闻流)
# - http://127.0.0.1:8080/poc/news-detail.html?id=130
# - http://127.0.0.1:8080/poc/sectors.html      (全屏板块热力图)
# - http://127.0.0.1:8080/poc/reports.html      (6 时段日报)
# - http://127.0.0.1:8080/poc/params.html       (⚡ 赛博朋克控制台)

# 启动主服务
./start.bat                              # Windows
./start.sh                               # Linux/macOS
# 浏览器开 http://127.0.0.1:8080/poc/index.html (同源 mount 后，无需 python -m http.server)

# 测试 + 覆盖率
uv run pytest -x
uv run pytest --cov=src/amarket --cov-report=term

# Lint / 类型
uv run ruff check . --fix
uv run ruff format .
uv run mypy src/ scripts/
```

## POC 端到端 demo（M3 完整）

```bash
# 现在只要起后端，浏览器直接开 /poc/*.html

# 1. 启动后端（FastAPI 8080 + 同源 mount /poc）
./start.bat                                          # Windows
# 或：uv run uvicorn amarket.main:app --port 8080

# 2. 浏览器开（同源 + fetch /api/* 真数据）
# - http://127.0.0.1:8080/poc/index.html       9 区域 + summary 聚合端点
# - http://127.0.0.1:8080/poc/news.html        5 维度筛选 + 30s polling
# - http://127.0.0.1:8080/poc/news-detail.html?id=130   完整 AI 分析
# - http://127.0.0.1:8080/poc/sectors.html     全屏 treemap + window 切换 live
# - http://127.0.0.1:8080/poc/reports.html     6 时段 tab + marked.js
# - http://127.0.0.1:8080/poc/params.html      ⚡ 赛博朋克 console

# 3. topbar LIVE → click 即可切 polling on/off（localStorage 持久化）
```
