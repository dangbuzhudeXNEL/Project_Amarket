# Project State

**Last Updated**: 2026-06-21 (Session 08 结束)
**Updated By**: Claude (Opus 4.7, 1M ctx) + User
**Next Action Owner**: 👤 **用户** + **Claude**（下次 session 继续 M2-c/d 并行）

---

## 🎯 下次 Session 必读：3 件事

### 1. 当前状态
- ✅ **main 上 CI 绿**（hotfix `c40088c`）
- ✅ **`.gitattributes` 已就位** — 跨平台行尾不再抖
- ✅ **DB 现状**：130 条新闻 + 12 条 A 股指数 + **130 个 NewsEvent**（M2-b 默认 threshold=3 下 1:1）
- ✅ **Dashboard 真实可用**
- ⏳ **当前在 `feat/m2-news-processing` 分支**：M2-a + M2-g + **M2-b** 已 commit
- ⏳ **`docs/local-deployment-guide` 分支** → **PR #1 待 review** (https://github.com/dangbuzhudeXNEL/Project_Amarket/pull/1)

### 2. 立刻可做（下次 session 开干）
**M2-c NewsClassifier** — 用 M2-a 规则（keywords/sectors/classification）做：
- 一级 8 类分类（宏观政策 / 市场行情 / 公司公告 / 海外映射 / 大宗商品 / 风险事件 / 资金流 / 交易提示）
- 二级 14+ 标签
- 板块关联（最长匹配）
- 个股关联（代码/名称扫描）

**和 M2-d SimpleRuleScorer 可并行**（都只依赖 M2-a 规则）— 一个 session 内并发做完。

### 3. 严禁动作
- ❌ 在 main 上直接 commit（CI hotfix 是特例，未来都走 fix/* 分支 + PR）
- ❌ Force push 任何分支
- ❌ 跳过 Session 启动 Checklist
- ❌ 引入实盘下单代码

---

## 当前阶段

- **Spec**: #1 v3 — A 股实时新闻分析与行情看板（小组联合版）
- **Phase**: 🟢 **Phase 1 实施中（已完成 M0/M0+/M1 + M2-a/b/g）**
- **Milestone**: **M2 进行中**（feature branch `feat/m2-news-processing`）
- **Sprint progress**:
  - ✅ M0 项目骨架 + 工具链 + CI + DB baseline + FastAPI + Streamlit
  - ✅ M0+ 通知预留端到端
  - ✅ M1 数据基座（16 表 + 3 新闻源 + akshare + 6 Repo + 4 API + CLI collect + viz）
  - ✅ M2-a 规则配置（keywords/sectors/classification YAML）
  - ✅ M2-g 双路径 AI 架构（Brainmaster + SDK + Fallback chain）
  - ✅ **M2-b 三层去重 NewsDeduper（URL / normalize / SimHash + news_events 聚合）⭐ 本 session**
  - ⏳ M2-c/d/e/f/h/i/j/k 剩 8 个子任务
  - 📋 M3/M4/M5/M6 待启动
- **Session count**: 8 sessions（详见 `docs/sessions/`）

---

## 活跃任务（feature branch 上的，下次 session 接力）

| ID | 任务 | 依赖 | 预估 |
|----|------|------|------|
| M2-c | NewsClassifier（一级 8 类 + 二级 14+ 标签 + 板块/标的关联） | M2-a | 2h |
| M2-d | SimpleRuleScorer（重要性/紧急度/情绪规则评分） | M2-a | 2h |
| M2-e | NewsAnalysis service（编排 Classifier → AIProvider 或 Scorer → 写 news_analysis 表） | M2-c, M2-d, M2-g | 1h |
| M2-f | AlertService（P0-P3 决策表 + alerts 表写入） | M2-e | 1h |
| M2-h | API 升级（/api/news 带分析字段 + /api/alerts） | M2-e, M2-f | 1h |
| M2-i | Dashboard 升级（新闻列表显示标签/评分/告警等级 + 告警区） | M2-h | 1h |
| M2-j | 集成测试（**把 130 条真实新闻喂进 pipeline 验证**）⭐ | 所有上面 | 2h |
| M2-k | 收尾 commit + push + 写 session 日志 | — | 0.5h |

**M2 总剩余 ~10-11 小时 ≈ 1-2 个 session**。

---

## 最近 5 个关键决策（按时间倒序）

1. **2026-06-21 (Session 08)**：**部署文档独立 PR**（用户指定）+ **Superpowers 使用边界协议** — 复杂任务才用 brainstorming/writing-plans；中小任务直接干
2. **2026-06-21 (Session 08)**：**M2-b 默认 threshold=3 保守对齐 spec**；真实数据验证显示中文标题需 8-10 才有意义召回；语义判断留 M2-e
3. **2026-06-19 (Session 07)**：**CI hotfix 直 push main** — 行尾差异导致 ruff format 在 Win/Linux 行为不一致，加 `.gitattributes` 永久修复
4. **2026-06-19 (Session 06)**：**Brainmaster 提前到 M2** — `AIProvider` 双路径架构 + agent 文件输出已就位
5. **2026-06-19 (Session 06)**：**feat/m0-project-skeleton 合 main** — M0 + M0+ + M1 一起合并；从此严格走 PR 流程

---

## 阻塞 / 待用户/小组输入

**无硬阻塞** — 可以直接继续 M2-c/d。

**待处理**：
- **PR #1**（本地部署文档）等 1 人 review 后 merge 到 main

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
| 2026-06-19 (Session 07) | CI hotfix（`.gitattributes` + ruff format）；CI 绿 |
| **2026-06-21 (Session 08)** | **本地部署文档 PR #1 + M2-b NewsDeduper 端到端（19 tests, 真实数据验证）** |

---

## 速查表

- **当前 spec**: `docs/superpowers/specs/2026-06-19-spec1-v3-merged.md`
- **当前 branch**: `feat/m2-news-processing` (commit `cf5d691`)
- **main HEAD**: `c40088c` (CI 绿 ✅)
- **docs branch**: `docs/local-deployment-guide` (commit `1b3c59f`) → PR #1 待 review
- **Phase / Milestone**: Phase 1 / M2 进行中（M0/M0+/M1/M2-a/b/g 完成）
- **DB 现状**: 130 条新闻（sina 60 + eastmoney 50 + yahoo 20）+ 12 条 A 股指数 + 130 个 NewsEvent
- **测试 / 覆盖率**: **130 tests / 88.34% coverage**（M2-b 加了 19 tests，整体涨 0.6%）
- **GitHub**: https://github.com/dangbuzhudeXNEL/Project_Amarket
- **本地路径**: `C:\AI\Claude\Project_Amarket`

---

## 命令速查（M2-b 起可用）

```bash
# 拉数据
uv run amarket collect market           # 6 个 A 股指数入库
uv run amarket collect news             # 默认 5min 窗口
uv run amarket collect news --full      # 12h 窗口

# 去重（M2-b 新增）
uv run amarket dedupe news                                # 默认 limit=500 threshold=3
uv run amarket dedupe news --threshold 10                 # 放宽 L3
uv run amarket dedupe news --limit 1000 --lookback-hours 48

# 启动整套
./start.bat                              # Windows
./start.sh                               # Linux/macOS

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
