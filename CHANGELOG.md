# Changelog

All notable changes to **Project_Amarket** are documented here.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format and
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Each Spec corresponds to a major milestone. Within a Spec, M0-M9 are intermediate releases.

---

## [Unreleased] — Spec #1 v3 进行中

### Added — Phase 1 M0 实施完成（2026-06-19, Session 04, branch `feat/m0-project-skeleton`）

**Phase 1 M0：项目骨架 + 小组仓库基础设施** ✅

- **uv 项目初始化**：`pyproject.toml` (Python 3.11+，pin 3.12)、`uv.lock`、`.python-version`
  - 生产依赖：fastapi/uvicorn/streamlit/sqlmodel/alembic/apscheduler/httpx/structlog/loguru/typer/pydantic+settings/jinja2/chinese-calendar/simhash/prometheus-client/tenacity/pyyaml/python-dotenv/lxml/beautifulsoup4/feedparser/anthropic/openai
  - 可选依赖：market-data extra（akshare/efinance/yfinance）
  - 开发依赖：pytest+asyncio+cov+mock/httpx/respx/freezegun/ruff/mypy/pre-commit/types-pyyaml

- **工具链**：
  - `ruff` (lint + format)：开启 E/W/F/I/B/C4/UP/ARG/SIM/RUF，ignore 中文标点 RUF001-003
  - `mypy` (strict 模式，Python 3.11+ target)
  - `pytest` + `pytest-asyncio` + `pytest-cov`（覆盖率门槛 70%）
  - `pre-commit` (ruff + mypy + 通用钩子)
  - `.editorconfig`

- **CI**（`.github/workflows/ci.yml`）：
  - lint job（ruff check + format check）
  - typecheck job（mypy src/）
  - test job（matrix Python 3.11 + 3.12）
  - docs-check job（必需文档存在性 + CODEOWNERS TODO 警告）

- **数据库**：
  - `alembic.ini` + `src/amarket/db/migrations/env.py`（动态注入 database_url）
  - 第一个 migration：`20260619_m0_users.py`（创建 users 表）
  - `src/amarket/db/session.py`（engine + session factory + FastAPI 依赖）

- **配置 + 日志**：
  - `config/app.yml`（应用全局 + API + UI + project_meta）
  - `.env.example`（Phase 1+2 全部 env var 模板）
  - `src/amarket/services/config_service.py`（pydantic-settings，含 lru_cache + reload_config）
  - `src/amarket/core/logging.py`（structlog JSON / Console + 密钥脱敏 processor）
  - `src/amarket/core/exceptions.py`（AmarketError + 子类）

- **HTTP API**（FastAPI）：
  - `src/amarket/main.py`（app 工厂 + lifespan 钩子 + CORS）
  - `src/amarket/api/health.py`（`/healthz` — healthy/degraded → 200，unhealthy → 503）
  - `src/amarket/api/metrics.py`（`/metrics` — Prometheus 格式 + amarket_uptime_seconds + amarket_app info）
  - `src/amarket/services/observability.py`（DB 探活 + aggregate 总状态）

- **UI**：
  - `src/amarket/ui/app.py`（Streamlit Hello — 状态卡 + /healthz 调用 + M0 进度 + 文档导航）

- **CLI**（Typer）：
  - `amarket version` — 版本 + Spec/Phase/Milestone
  - `amarket healthcheck` / `--json` / `--remote` — 进程内或远端健康检查
  - `amarket db status` — DB 探活

- **启动脚本**：
  - `start.bat`（Windows，新窗口分别拉起 FastAPI + Streamlit）
  - `start.sh`（Linux/macOS，trap INT/TERM 一键启停）

- **Notifier 骨架**（Spec v3 §6.2.4）：
  - `src/amarket/adapters/notifiers/base.py`（Notifier Protocol + NotificationResult + NotifierHealth + CardSpec + **COMPLIANCE_FOOTER 全外发消息合规附加**）
  - `src/amarket/adapters/notifiers/wework_bot.py`（企微：text/markdown/news，含 errcode 处理）
  - `src/amarket/adapters/notifiers/lark_bot.py`（飞书：text/post/interactive 卡片）

- **Domain 层**：
  - `src/amarket/domain/enums.py`（UserRole/SourcePriority/NewsCategory/Sentiment/ImpactHorizon/ActionHint/AlertLevel/PushStatus/PushKind/ReportKind/SourceHealthStatus/ProcessingProvider — Spec v3 §8）
  - `src/amarket/domain/models.py`（User SQLModel，TimestampMixin）

- **测试**：
  - `tests/conftest.py`（公共 fixtures：in_memory_engine / session / patched_engine / api_client / clean_env / log 静默）
  - 9 个测试文件：config_service / logging_redaction / observability / api_endpoints / notifiers (wework+lark) / cli / models / enums
  - **42 unit tests passed in 1.23s**
  - **Coverage: 91.59%**（要求 70%）

- **小修**：
  - `.gitignore` 把 `.python-version` 从忽略列表移出（uv 项目标准做法）

### Pending — 接下来

- 用户决定 `feat/m0-project-skeleton` 分支 merge 策略（自审 push / open PR / 等小组 review）
- Phase 1 M1：数据基座（11+ 张完整表 schema + 1 源新闻 + 1 源行情 + NewsRepo + 最小 /api/news）

### Added — M0+ 通知预留端到端（2026-06-19, Session 04 续）

**目标**：让企微 / 飞书通知"配好 webhook 就能立刻验证"，不必等 M4 真实推送。

- **`/healthz`**：新增 `notifiers: dict[str, NotifierHealth]` 字段（每个已配置的渠道暴露 ok/down/disabled 状态 + 上次错误）；notifier `down` 不致命但触发 overall `degraded`
- **`ObservabilityService`**：新增 `iter_notifiers()` / `get_notifier(channel)` / `list_notifier_channels()` — 单一入口枚举所有已配置 notifier
- **`services/notify_test.py`**：同步包装（asyncio.run）— 给 Streamlit / CLI 共用
- **Streamlit dashboard**：新增"📬 通知测试"区域，企微业务 / 企微告警 / 飞书三栏并排显示配置状态 + 一键"🧪 发测试"按钮
- **CLI**：
  - `amarket notify status` — 列出渠道配置 + 健康
  - `amarket notify test <channel>` — 发测试消息（`channel ∈ wework|wework_alert|lark|all`）
  - `amarket healthcheck` 输出增加 `notifiers:` 段
- **测试**：新增 14 个 test 覆盖（observability notifier 路径 + notify_test wrapper + CLI notify 命令）
- **总计**：**56 tests passed (从 42)**，覆盖率 **91.10%**
- 同步小修：`dict()` 替代 dict comprehension（ruff C416）

### Changed — Spec v3: 升格小组联合项目 + 融合 Peersession PRD（2026-06-19）

**重大方向转变**：项目从"个人自用 + 学习"升格为**小组联合项目**。

- **Spec v3 发布**：`docs/superpowers/specs/2026-06-19-spec1-v3-merged.md`（2391 行）
  - 上一版 Spec v2（`2026-06-14-news-engine-design.md`）保留作为历史
  - 章节结构以 Peersession PRD 为主线，融合 v2 工程化内容
  - 双 Phase 划分：
    - **Phase 1** = 三大模块（新闻 / 交易看板 / 参数配置）+ 6 时段日报 + P0-P3 告警 + 看板 API + 静态 POC + Streamlit 管理面板
    - **Phase 2** = 原 v2 内容（Brainmaster AI 集成 / 信号交易 / Breaking 实时通道）
  - 新增章节：§4 用户与场景 / §8 新闻分类与评分体系 / §10 看板与 API 设计 / §11 参数配置模块
  - 改写章节：§3 决策表（扩到 28 项）/ §5 架构（三大模块边界）/ §6 模块设计（16 个 service）/ §7 数据模型（11+ 张表）/ §9 工作流 / §17 实施里程碑（M0-M9）
  - 附录 C 给出完整 v2 → v3 章节映射

- **永远不做实盘下单**：显式禁令写入 Spec / CLAUDE.md / CONTRIBUTING / README
- **AI 集成双路径**：
  - Phase 1：通过 `AIProvider` 接口走 SDK（Anthropic / DeepSeek 走 API；需要 API key）
  - Phase 2：通过 `ClaudeAgentRunner` 走 Brainmaster 模式（subprocess + claude CLI + agent 文件输出；零 API key）

### Added — 小组协作工件（2026-06-19）

- **`CONTRIBUTING.md`**：30 分钟 onboarding / 分支策略 / commit 规范 / PR 流程 / 敏感模块（2 人 review）/ 编码规范 / 测试要求 / 文档协议 / AI 协作伙伴约定 / 合规 reminder
- **`.github/CODEOWNERS`**：模块 owner 映射（占位符待填实际 GitHub 账号）
- **`.github/PULL_REQUEST_TEMPLATE.md`**：PR 描述模板（背景 / 改动 / 风险与回滚 / 测试 / Checklist）

### Added — 归档与文档（2026-06-19）

- **`docs/peersession-source/`**：归档小组成员原始素材
  - `a_share_realtime_news_dashboard_prd.md`（来自 2026-06-17）
  - `a_share_quant_project_timeline.docx`（来自 2026-06-17）
  - `a_share_quant_project_timeline.extracted.txt`（docx 文本提取）

### Changed — 项目基础文档（2026-06-19）

- **`README.md`** 大改：反映小组联合 + Phase 1/2 + 新核心能力清单
- **`CLAUDE.md`** 大改：
  - 项目身份卡更新（性质 = 小组联合 / 双 Phase 路线图 / AI 集成双路径表）
  - 编码规范扩展（新增"不允许直接 push main" + "不允许引入实盘下单代码"）
  - YAGNI 列表更新（增"实盘下单"、改"AI" → 双 Phase 表述）
  - 协作模式扩展（小组角色 + AI 协作约束 + superpowers 使用原则）
  - 链接更新（v3 作为当前 spec）
  - 文档地图扩展（CONTRIBUTING / CODEOWNERS / peersession-source）
- **`docs/PROJECT_STATE.md`** 大改：标注 Session 03 状态 + 下次 session 必读 + 待审阅清单

### Pending — 接下来

- 小组审阅 Spec v3 + 小组协作工件
- 填实 CODEOWNERS 中 GitHub 账号占位符
- GitHub 分支保护规则配置（main 需 PR + review）
- 若直接 M0：用户准备企微 / 飞书 webhook + LLM API key
- 若先 writing-plans：调用 `superpowers:writing-plans` 撰写 Phase 1 实施计划
- 进入 Phase 1 M0：项目骨架 + 小组仓库基础设施

---

## [Unreleased] — Spec #1 v2（已被 v3 替代）

### Added — Design Phase v1（2026-06-14）
- 项目初始化：git 仓库、`.gitignore`、文档目录结构
- Spec #1 v1 设计文档：`docs/superpowers/specs/2026-06-14-news-engine-design.md`
  - 17 个章节 + 2 个附录，约 1500 行
  - 覆盖：架构、模块、数据模型、工作流、错误处理、测试、里程碑、多 session 支持
- 知识沉淀机制：
  - `CLAUDE.md` 项目记忆
  - `docs/PROJECT_STATE.md` 状态快照
  - `docs/sessions/` 历次 session 日志目录
  - `CHANGELOG.md` 本文件
- GitHub public repo 创建：`dangbuzhudeXNEL/Project_Amarket`

### Changed — Architecture Adjustment v2（2026-06-14, late）
- **AI 集成模式从 "Anthropic SDK + localhost proxy" 改为 Brainmaster 模式**
  - Python 通过 `subprocess.run(["claude", "--agent", ...])` 调用 Claude CLI
  - Agent 定义在 `.claude/agents/*.md`，输出走文件系统 JSON
  - 完全不需要 API key 或 localhost proxy
  - Anthropic SDK 降级为可选 Tier 2 fallback（MVP 不启用）
  - Spec 章节 §3 / §5.1.4 / §5.2.2 / §7.3 / §8.2 / §11 / §12 / §13 / §17 全部更新
  - 与隔壁 Brainmaster 项目（`C:\AI\Claude\Brainmaster`）保持一致的 AI 集成模式
- 新增 Claude Code 工件：
  - `.claude/agents/news-analyst.md` (sonnet, 30 turns) — 盘前新闻汇总 agent
  - `.claude/commands/test-premarket.md` — 手动测试盘前流程的 slash command

---

## 历史里程碑（汇总）

| 时间 | 关键事件 |
|------|---------|
| 2026-06-14 | Spec v1 设计完成 + GitHub repo 上线 |
| 2026-06-14 | Spec v2 — 采纳 Brainmaster AI 集成模式 |
| **2026-06-19** | **Spec v3 — 融合 Peersession PRD，升格小组联合项目** |
| 待定 | Phase 1 M0 启动 |
