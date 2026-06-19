# Project State

**Last Updated**: 2026-06-19 (Session 07 结束)
**Updated By**: Claude (Opus 4.7, 1M ctx) + User
**Next Action Owner**: 👤 **用户** + **Claude**（下次 session 继续 M2-b 接力）

---

## 🎯 下次 Session 必读：3 件事

### 1. 当前状态
- ✅ **main 上 CI 绿了**（hotfix `c40088c` 修了 ruff format 行尾差异问题）
- ✅ **`.gitattributes` 已就位**，未来 Windows / Linux 行尾不再触发 ruff 抖动
- ✅ **DB 已有真实数据**：130 条新闻（sina 60 + eastmoney 50 + yahoo 20）+ 12 条 A 股指数快照
- ✅ **Dashboard 真实可用**（M1 数据可视化 + M0+ 通知测试 + M0 健康检查）
- ⏳ **当前在 `feat/m2-news-processing` 分支**：M2-a + M2-g 已 commit；M2-b/c/d/e/f/h/i/j/k 待做

### 2. 立刻可做（下次 session 开干）
**M2-b NewsDeduper** — 三层去重（URL → 标题 → SimHash） + `news_events` 聚合
- 输入：130 条已抓的新闻（DB 里）
- 输出：news_events 表里出现"同事件多源聚合"行
- 不依赖 AI，纯规则；1-2 小时

**接着 M2-c NewsClassifier** — 用 M2-a 规则做一级 / 二级分类 + 板块 / 标的关联

### 3. 严禁动作
- ❌ 在 main 上直接 commit（CI hotfix 是特例，未来都走 fix/* 分支 + PR）
- ❌ Force push 任何分支
- ❌ 跳过 Session 启动 Checklist
- ❌ 引入实盘下单代码

---

## 当前阶段

- **Spec**: #1 v3 — A 股实时新闻分析与行情看板（小组联合版）
- **Phase**: 🟢 **Phase 1 实施中（已完成 M0/M0+/M1 + M2-a/g）**
- **Milestone**: **M2 进行中**（feature branch `feat/m2-news-processing`）
- **Sprint progress**:
  - ✅ M0 项目骨架 + 工具链 + CI + DB baseline + FastAPI + Streamlit
  - ✅ M0+ 通知预留端到端
  - ✅ M1 数据基座（16 表 + 3 新闻源 + akshare + 6 Repo + 4 API + CLI collect + viz）
  - ✅ M2-a 规则配置（keywords/sectors/classification YAML）
  - ✅ M2-g 双路径 AI 架构（Brainmaster + SDK + Fallback chain）
  - ⏳ M2-b/c/d/e/f/h/i/j/k 剩 9 个子任务
  - 📋 M3/M4/M5/M6 待启动
- **Session count**: 7 sessions（详见 `docs/sessions/`）

---

## 活跃任务（feature branch 上的，下次 session 接力）

| ID | 任务 | 依赖 | 预估 |
|----|------|------|------|
| M2-b | NewsDeduper（三层去重 + events 聚合） | 无 | 2h |
| M2-c | NewsClassifier（一级 8 类 + 二级 14+ 标签 + 板块/标的关联） | M2-a | 2h |
| M2-d | SimpleRuleScorer（重要性/紧急度/情绪规则评分） | M2-a | 2h |
| M2-e | NewsAnalysis service（编排 Classifier → AIProvider 或 Scorer → 写 news_analysis 表） | M2-c, M2-d, M2-g | 1h |
| M2-f | AlertService（P0-P3 决策表 + alerts 表写入） | M2-e | 1h |
| M2-h | API 升级（/api/news 带分析字段 + /api/alerts） | M2-e, M2-f | 1h |
| M2-i | Dashboard 升级（新闻列表显示标签/评分/告警等级 + 告警区） | M2-h | 1h |
| M2-j | 集成测试（**把 130 条真实新闻喂进 pipeline 验证**）⭐ | 所有上面 | 2h |
| M2-k | 收尾 commit + push + 写 session 日志 | — | 0.5h |

**M2 总剩余 ~12-13 小时 ≈ 1-2 个 session**。

---

## 最近 5 个关键决策（按时间倒序）

1. **2026-06-19 (Session 07)**：**CI hotfix 直 push main** — 行尾差异导致 ruff format 在 Win/Linux 行为不一致，加 `.gitattributes` 永久修复；视为合理的 hotfix 例外
2. **2026-06-19 (Session 06)**：**Brainmaster 提前到 M2** — 用户原话"本地 claude code 主，兼容 API 备"。`AIProvider` 双路径架构 + agent 文件输出已就位
3. **2026-06-19 (Session 06)**：**feat/m0-project-skeleton 合 main** — M0 + M0+ + M1 一起合并；从此严格走 PR 流程（hotfix 除外）
4. **2026-06-19 (Session 05)**：M1 数据基座 — 3 个真实新闻源 + akshare 行情 + 端到端 demo 验证
5. **2026-06-19 (Session 03)**：升格小组联合 + Spec v3 融合 Peersession PRD（双阶段：Phase 1 三大模块 / Phase 2 v2 内容）

---

## 阻塞 / 待用户/小组输入

**无硬阻塞** — 可以直接继续 M2。

**软阻塞**（M4 启动前确认即可）：
- 企微 / 飞书 webhook（M4 真实推送时用）
- LLM API key（如果想让 SDK 备路径生效；M2-e/M4 才必需）
- Claude CLI 在 PATH（Brainmaster 主路径，M2-e/M4 启动前验证）

---

## 重要环境/配置变化（按时间正序）

| 时间 | 变化 |
|------|------|
| 2026-06-14 ~ Session 03 | Spec v1 → v2 → v3；从个人项目升格小组联合 |
| 2026-06-19 (Session 04) | uv 项目初始化，pin Python 3.12 |
| 2026-06-19 (Session 05) | M1：16 张表 + 3 新闻源 + akshare + Repo + API + CLI + viz |
| 2026-06-19 (Session 06) | feat/m0-project-skeleton 合 main；M2-a 规则 + M2-g AI 双路径 |
| **2026-06-19 (Session 07)** | CI hotfix（`.gitattributes` + ruff format）；CI 绿 |

---

## 速查表

- **当前 spec**: `docs/superpowers/specs/2026-06-19-spec1-v3-merged.md`
- **当前 branch**: `feat/m2-news-processing` (commit `9c25f89`)
- **main HEAD**: `c40088c` (CI 绿 ✅)
- **Phase / Milestone**: Phase 1 / M2 进行中（M0/M0+/M1/M2-a/g 完成）
- **DB 现状**: 130 条新闻（sina 60 + eastmoney 50 + yahoo 20）+ 12 条 A 股指数
- **测试 / 覆盖率**: 111 tests / 87.70% coverage（M2-g 后）
- **GitHub Actions CI**: Run #2 `main` `success` ✅
- **GitHub**: https://github.com/dangbuzhudeXNEL/2026-06-19-spec1-v3-merged.md
- **本地路径**: `C:\AI\Claude\Project_Amarket`

---

## 命令速查（M1+ 可用）

```bash
# 拉数据
uv run amarket collect market           # 6 个 A 股指数入库
uv run amarket collect news             # 默认 5min 窗口
uv run amarket collect news --full      # 12h 窗口

# 启动整套
./start.bat                              # Windows
./start.sh                               # Linux/macOS
# → FastAPI: http://127.0.0.1:8080/docs
# → Streamlit: http://127.0.0.1:8501

# 测试 + 覆盖率
uv run pytest -x                        # 快速
uv run pytest --cov=src/amarket --cov-report=term  # 带覆盖率

# Lint / 类型
uv run ruff check . --fix
uv run ruff format .
uv run mypy src/

# 通知
uv run amarket notify status            # 看 3 个渠道配置
uv run amarket notify test wework       # 配好 webhook 后测试

# 数据库
uv run alembic upgrade head             # 应用迁移
```
