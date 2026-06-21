# Project State

**Last Updated**: 2026-06-21 (Session 10 结束 — M2 完整完成)
**Updated By**: Claude (Opus 4.7, 1M ctx) + User + superpowers:code-reviewer agent
**Next Action Owner**: 👤 **用户** — 决定先开 PR 合 main 还是直接进 M3

---

## 🎯 下次 Session 必读：3 件事

### 1. 当前状态
- ✅ **main 上 CI 绿**（HEAD `034bb6e`，含 PR #1 部署文档）
- ✅ **DB 现状**：130 条新闻 + 12 条 A 股指数 + 130 NewsEvent + **130 NewsAnalysis + 73 Alerts (1 P0 + 1 P1 + 71 P2)**
- ✅ **Dashboard 全功能可用**（告警区 + 新闻 badges + milestone 进度）
- ✅ **Phase 1 M2 智能层全部 11/11 子任务完成**，端到端 pipeline 已跑通真实数据
- ✅ **code-reviewer agent 已通过专业 review**，P0 + 1 个 P1 已修，剩 4 个 P1 留 TODO
- ⏳ **当前在 `feat/m2-news-processing` 分支 (`d9d6ac2`)** — **准备开 PR 合 main**

### 2. 立刻可做（下次 session 开干）
**两条路径任选**：

#### 路径 A（推荐）：开 PR 把 M2 合 main
- 整理 PR description（列 M2 全部子任务 + 测试结果 + reviewer 报告）
- 等 CI 全绿
- self-merge 到 main
- 然后开 M3

#### 路径 B：直接进 M3 不先合
- 风险：feat 分支越来越大，main 落后
- 不推荐

### 3. M3 启动前必修（reviewer P1，已在 backlog）
- **P1-1**：`_has_any_analysis` 改 provider-aware（避免 rule 锁死）
- **P1-5**：`analyze_batch` 每 task 独立 session（避免 race 隐患）
- **P1-2**：等级升档 supersede 策略（避免 M4 双推）
- **P1-3**：黑名单与 alert 的关系（设计选择）

### 4. 严禁动作
- ❌ 在 main 上直接 commit（CI hotfix 是特例，未来都走 fix/* 分支 + PR）
- ❌ Force push 任何分支
- ❌ 跳过 Session 启动 Checklist
- ❌ 引入实盘下单代码

---

## 当前阶段

- **Spec**: #1 v3 — A 股实时新闻分析与行情看板（小组联合版）
- **Phase**: 🟢 **Phase 1 实施中 — M0/M0+/M1/M2 全部完成（37%）**
- **Milestone**: **M2 已完成**（feature branch `feat/m2-news-processing` 待开 PR）
- **Sprint progress**:
  - ✅ M0 项目骨架 + 工具链 + CI + DB baseline + FastAPI + Streamlit
  - ✅ M0+ 通知预留端到端
  - ✅ M1 数据基座（16 表 + 3 新闻源 + akshare + 6 Repo + 4 API + CLI collect + viz）
  - ✅ **M2 智能层（11/11 子任务全部完成）**：
    - M2-a 规则配置 YAML / M2-g AI 双路径 / M2-b 三层去重 /
    - M2-c 规则分类 / M2-d 规则评分 /
    - **M2-e NewsAnalysis 编排 / M2-f AlertService P0-P3 /**
    - **M2-h API 升级 / M2-i Dashboard 升级 /**
    - **M2-j 端到端集成测试 / M2-k 收尾 + code review** ⭐ 本 session
  - 📋 M3/M4/M5/M6 待启动
- **Session count**: 10 sessions（详见 `docs/sessions/`）

---

## 活跃任务

**M2 全部完成。等待用户决策下一步（开 PR 合 main vs 直接进 M3）**

### Phase 1 剩余 milestones
| M | 内容 | 状态 | 预估 |
|---|------|------|------|
| **M3** | 静态 HTML POC 看板（首页 / 新闻流 / 详情页 / 板块热力图 / 日报页）| 📋 待启动 | 2-3 session |
| **M4** | 真实推送 + APScheduler 调度 — 把分析结果实际推到企微/飞书 | 📋 待启动 | 2 session |
| **M5** | 6 时段自动日报（盘前/早盘/午间/尾盘/收盘/晚间）| 📋 待启动 | 2 session |
| **M6** | 参数配置模块（版本/回滚/审计 — Phase 1 三大模块之三）| 📋 待启动 | 1-2 session |

### M3 启动前 backlog（reviewer P1）
- [ ] `_has_any_analysis` provider-aware（避免 rule 锁死）
- [ ] `analyze_batch` 每 task 独立 session（避免 future race）
- [ ] 同 news 等级升档 supersede 策略（避免 M4 双推）
- [ ] 黑名单与 alert 关系决策（abstain vs cap importance）

### nice-to-have backlog（reviewer P2）
- [ ] `_compute_top_source` SQL GROUP BY 优化
- [ ] `_source_cache` LRU 上限
- [ ] SimHash distance==threshold 边界测试
- [ ] market_hours 4 个端点边界 + 周末测试
- [ ] DeepSeek json_object 中文 enum 真实 API 验证
- [ ] `processed_by` 字符串集中常量

---

## 最近 5 个关键决策（按时间倒序）

1. **2026-06-21 (Session 10)**：**M2 完整完成 + code-reviewer 通过**；P0 + P1-4 已修，4 P1 留 TODO 给 M3
2. **2026-06-21 (Session 09)**：**PR #1 立即 self-merge** + classifier 子串重叠允许双计数 + scorer confidence 规则路径固定 3
3. **2026-06-21 (Session 08)**：**部署文档独立 PR**（用户指定）+ **Superpowers 使用边界协议**
4. **2026-06-21 (Session 08)**：**M2-b 默认 threshold=3 保守对齐 spec**
5. **2026-06-19 (Session 07)**：**CI hotfix 直 push main**（`.gitattributes` + ruff format）

---

## 阻塞 / 待用户/小组输入

**无硬阻塞** — M2 整体已完成。

**待决策**：
- 开 PR 合 main vs 直接进 M3（用户决定）

**软阻塞**（M4 启动前必须）：
- 企微 / 飞书 webhook（M4 真实推送时用）
- LLM API key（M2-e/g 已支持，但目前规则路径足够 demo；想升级 AI 分析时配）
- Claude CLI 在 PATH（Brainmaster 主路径，配了体验更好）

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
| **2026-06-21 (Session 10)** | **M2 全部完成（e/f/h/i/j/k）+ 端到端 pipeline 跑通 + code review 通过** |

---

## 速查表

- **当前 spec**: `docs/superpowers/specs/2026-06-19-spec1-v3-merged.md`
- **当前 branch**: `feat/m2-news-processing` (commit `d9d6ac2`)
- **main HEAD**: `034bb6e` (CI 绿 ✅，含 PR #1)
- **Phase / Milestone**: Phase 1 / **M2 已完成（11/11）** → 准备开 PR 合 main
- **DB 现状**:
  - 130 条新闻（sina 60 + eastmoney 50 + yahoo 20）
  - 12 条 A 股指数快照
  - 130 个 NewsEvent（去重 1:1）
  - 130 行 NewsAnalysis（规则路径全跑通）
  - 73 行 Alert（1 P0 + 1 P1 + 71 P2）
- **测试 / 覆盖率**: **195 tests / 87.25% coverage**
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
uv run amarket analyze news --no-ai     # 强制规则路径（无 API key 时用）
uv run amarket analyze news --reanalyze --limit 500  # 重处理

# 启动整套
./start.bat                              # Windows
./start.sh                               # Linux/macOS
# → API:        http://127.0.0.1:8080/docs
# → /api/news:  http://127.0.0.1:8080/api/news?limit=20
# → /api/alerts: http://127.0.0.1:8080/api/alerts?level=P0
# → Dashboard:  http://127.0.0.1:8501

# 测试 + 覆盖率
uv run pytest -x
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

## 端到端 demo（一条命令跑完整 pipeline）

```bash
# 已有数据时：
uv run amarket dedupe news --threshold 3      # 去重
uv run amarket analyze news --no-ai --limit 200 --reanalyze   # 分析 + 告警

# 期望输出（基于本 session 实测）：
# 分析完成：130 条 → 130 NewsAnalysis（rule_fallback）
# 告警决策：1 P0（伊朗战争）+ 1 P1（韩国前防长）+ 71 P2 + 57 P3
```
