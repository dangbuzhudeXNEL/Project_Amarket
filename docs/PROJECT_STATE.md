# Project State

**Last Updated**: 2026-06-24 (Session 12 结束 — M3 brainstorm + M3a-PR1 实现)
**Updated By**: Claude (Opus 4.7, 1M ctx) + User
**Next Action Owner**: 👤 **用户** + **Claude**（下次 session 开 M3a-PR2 = 剩余 3 页 + 赛博朋克）

---

## 🎯 下次 Session 必读：3 件事

### 1. 当前状态
- ✅ **main 上 CI 绿**（HEAD `7fbf17e`，含 PR #9 spec + PR #10 实现）
- ✅ **Phase 1 完成 4.5/7 milestones**（M0/M0+/M1/M2 + **M3a-PR1**）
- ✅ **POC 前端 3 页已上线**：index / news / news-detail（OKX 暗色金融风）
- ✅ **Dump 脚本 + 11 JSON 文件已 commit**：130 NewsItem + 73 Alert + 14 sectors mock + 15 params mock
- ✅ **测试 / 覆盖率**：**216 tests / 87.95%+ coverage**（207 之前 + 9 dump 新增）

### 2. 立刻可做 — **下次 session 开 M3a-PR2 = 剩余 3 页 + 赛博朋克**

PR2 范围（spec `2026-06-24-m3a-poc-pages-design.md` §11.2）：
- `poc/sectors.html` — 14 板块全屏 ECharts treemap + 联动新闻列表
- `poc/reports.html` — 6 时段日报展示 + Markdown 渲染（marked.js CDN）
- `poc/params.html` — **赛博朋克风**参数空壳（霓虹 cyan/magenta + 等宽字体 + 辉光）
- `poc/assets/css/theme-cyberpunk.css` — 赛博朋克 token + 扫描线 + 辉光效果

JSON 数据 PR1 已 dump 完（`sectors.json` / `reports.json` / `params.json`），PR2 只写消费数据的 HTML+CSS+JS。

**启动建议**：直接进 writing-plans 写 M3a-PR2 plan（spec 已批准 + scope 已定），不用再 brainstorm。预估 1 session。

### 3. 流程提醒
- M3a-PR2 完成后才进 **M3b**（API 联通 + 30s 自动 refresh）
- M3b 后才完整收掉 M3 里程碑

### 4. 严禁动作
- ❌ 在 main 上直接 commit（除 docs/session-wrap 等少数特例）
- ❌ Force push 任何分支
- ❌ 跳过 Session 启动 Checklist
- ❌ 引入实盘下单代码

---

## 当前阶段

- **Spec**: #1 v3 — A 股实时新闻分析与行情看板（小组联合版）
- **Phase**: 🟢 **Phase 1 实施中 — M3a-PR1 完成（64%）**
- **Milestone**: **M3a-PR1 已合并到 main** → 准备 M3a-PR2
- **Sprint progress**:
  - ✅ M0 项目骨架 + 工具链 + CI + DB baseline + FastAPI + Streamlit
  - ✅ M0+ 通知预留端到端
  - ✅ M1 数据基座
  - ✅ M2 智能层（11/11 子任务完成 + reviewer P1 全收）
  - 🟡 **M3 分为 M3a + M3b** （M3a 又分为 PR1 / PR2）
    - ✅ **M3a-PR1 框架 + 3 核心页 + 全量 mock dump**（本次完成）
    - 📋 M3a-PR2 剩余 3 页 + 赛博朋克（下次启动）
    - 📋 M3b 看板 API + SectorTrendService（M3a 完成后）
  - 📋 M4/M5/M6 待启动
- **Session count**: 12 sessions（详见 `docs/sessions/`）

---

## 活跃任务

**Phase 1 剩余 milestones**：

| M | 内容 | 状态 | 预估 |
|---|------|------|------|
| **M3a-PR2** | sectors.html + reports.html + params.html（赛博朋克）+ cyberpunk theme | 📋 **下次启动** | 1 session |
| **M3b** | 看板 API（/api/dashboard/summary/sectors/movers）+ SectorTrendService + 前端 fetch 切换 | 📋 待 M3a 完成 | 1-2 session |
| **M4** | 真实推送 + APScheduler 调度 + 6 时段日报基础 | 📋 待启动 | 2 session |
| **M5** | 参数配置模块（覆盖 params.html 赛博朋克 demo） | 📋 待启动 | 1-2 session |
| **M6** | 集成测试 + 文档 + UML + 7 天试运行 | 📋 待启动 | 1-2 session |

### 完成的 M3a-PR1 子任务（12/12）
- [x] Task 1 poc/ 骨架 + serve 脚本 + README
- [x] Task 2 theme-okx.css（269 行）
- [x] Task 3+4 shared.js + nav.js
- [x] Task 5 dump_poc_fixtures.py 骨架 + CLI
- [x] Task 6 dump_news + details + dashboard（TDD 4 测试）
- [x] Task 7 dump_alerts + 3 placeholder（TDD 4 测试）
- [x] Task 8 跑真实 dump + commit 11 JSON 文件
- [x] Task 9 index.html — Dashboard 首页（9 区域 + ECharts heatmap）
- [x] Task 10 news.html — 新闻流（5 维度筛选 + 3 排序）
- [x] Task 11 news-detail.html — 单条 + 完整 AI 分析 + 错误处理
- [x] Task 12 验证 + push + PR + merge

### 剩余 nice-to-have backlog（M2 reviewer P2，无阻塞）
- [ ] P2-1 `_compute_top_source` SQL GROUP BY 优化
- [ ] P2-2 `_source_cache` LRU 上限
- [ ] P2-3 SimHash distance==threshold 边界测试
- [ ] P2-4 market_hours 4 个端点边界 + 周末测试
- [ ] P2-5 DeepSeek json_object 中文 enum 真实 API 验证
- [ ] P2-6 `processed_by` 字符串集中常量

---

## 最近 5 个关键决策（按时间倒序）

1. **2026-06-24 (Session 12)**：**M3 拆分为 M3a 前端 / M3b API 后端**，M3a 又拆 PR1 (3 页框架) / PR2 (剩余 + 赛博朋克)
2. **2026-06-24 (Session 12)**：**OKX 暗色金融风 5 页 + 赛博朋克 params 空壳**（用户选定）；技术栈定 **Tailwind + Alpine + ECharts CDN，0 build**
3. **2026-06-24 (Session 11)**：收 Reviewer P1 backlog 4 个 fix + Windows Brainmaster 2 个 bug 修复
4. **2026-06-24 (Session 11)**：Demo Brainmaster 真跑通 — 5 条新闻 AI 分析明显优于规则
5. **2026-06-21 (Session 10)**：M2 完整完成 + code-reviewer 通过

---

## 阻塞 / 待用户/小组输入

**无硬阻塞** — M3a-PR2 可以直接启动。

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
| 2026-06-24 (Session 11) | Brainmaster Windows fix（PR #4）+ Reviewer P1 backlog 全清（PR #5） |
| **2026-06-24 (Session 12)** | **M3 brainstorm + spec（PR #9）+ M3a-PR1 实现（PR #10）** |

---

## 速查表

- **当前 spec**: `docs/superpowers/specs/2026-06-19-spec1-v3-merged.md`（v3 主）
- **M3a spec**: `docs/superpowers/specs/2026-06-24-m3a-poc-pages-design.md`（本 session 写的）
- **M3a-PR1 plan**: `docs/superpowers/plans/2026-06-24-m3a-pr1-frame-and-core.md`
- **当前 branch**: `main` (commit `7fbf17e`)
- **main HEAD**: `7fbf17e` (CI 绿 ✅，含 PR #1-10)
- **Phase / Milestone**: Phase 1 / **M3a-PR1 完成** → 准备 M3a-PR2
- **DB 现状**:
  - 130 NewsItem + 12 行情快照 + 130 NewsEvent
  - 130 NewsAnalysis（125 `rule` + 5 `agent:news-classifier-realtime`）
  - 73 Alert（1 P0 + 1 P1 + 71 P2）
- **POC 数据现状**（M3a-PR1 dump）:
  - `poc/assets/data/news.json` — 130 条富 DTO
  - `poc/assets/data/news-detail-*.json` — 5 条样本
  - `poc/assets/data/dashboard.json` + `alerts.json` + `sectors.json` + `reports.json` + `params.json`
- **测试 / 覆盖率**: **216 tests / 87.95% coverage**（含 9 个 dump 单测）
- **GitHub**: https://github.com/dangbuzhudeXNEL/coupon/Project_Amarket
- **本地路径**: `C:\AI\Claude\Project_Amarket`

---

## 命令速查（Phase 1 M3a-PR1 完成后）

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

# POC 前端（M3a-PR1 新增）
uv run python scripts/dump_poc_fixtures.py --pretty    # DB → poc/assets/data/*.json
cd poc && python -m http.server 8090                   # 起 POC server
# 浏览器开 http://127.0.0.1:8090/index.html

# 启动主服务
./start.bat                              # Windows
./start.sh                               # Linux/macOS
# → API:       http://127.0.0.1:8080/docs
# → /api/news: http://127.0.0.1:8080/api/news?limit=20
# → /api/alerts: http://127.0.0.1:8080/api/alerts?level=P0
# → /api/dashboard/market-status
# → Dashboard: http://127.0.0.1:8501 (Streamlit)

# 测试 + 覆盖率
uv run pytest -x
uv run pytest --cov=src/amarket --cov-report=term

# Lint / 类型
uv run ruff check . --fix
uv run ruff format .
uv run mypy src/ scripts/
```

## POC 端到端 demo（M3a-PR1）

```bash
# 1. 跑 dump（确保 data/amarket.db 有数据，如没有先跑 collect）
uv run python scripts/dump_poc_fixtures.py --pretty

# 2. 启动 POC server
cd poc && python -m http.server 8090

# 3. 浏览器开 http://127.0.0.1:8090/
# - 首页 9 区域 + ECharts 板块热力图
# - 新闻流 5 维度筛选
# - 详情页含完整 AI 分析（含 5 个样本可看）
```
