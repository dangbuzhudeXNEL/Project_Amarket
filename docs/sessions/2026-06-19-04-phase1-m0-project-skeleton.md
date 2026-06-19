# Session 2026-06-19-04 — Phase 1 M0 实施（项目骨架）

**Duration**: ~2 小时（含依赖安装 + 多次 lint/mypy/test 修复迭代）
**Participants**: User + Claude (Opus 4.7, 1M ctx, effort: high)
**Branch**: `feat/m0-project-skeleton`
**Goal**: 完成 Phase 1 M0 — 把项目骨架 / 基础设施 / 工具链 / CI / 数据库 / API / UI / CLI / Notifier 骨架 / 测试套件全跑通，让小组成员 30 分钟内能 onboarding

---

## 本次目标

- [x] Session 启动 Checklist（CLAUDE.md / PROJECT_STATE.md / sessions 最新 / git log / git status）
- [x] 与用户对齐方向（直接 M0 实施，feature branch 模式）
- [x] 创建 `feat/m0-project-skeleton` 分支
- [x] M0-a 项目骨架（pyproject.toml + src 包结构）
- [x] M0-b 工具链（ruff + mypy + pytest + pre-commit + editorconfig）
- [x] M0-c CI（GitHub Actions）
- [x] M0-d 配置 + 日志（app.yml + ConfigService + structlog）
- [x] M0-e 数据库（SQLite + Alembic baseline + users migration）
- [x] M0-f FastAPI（/healthz + /metrics）
- [x] M0-g Streamlit Hello World
- [x] M0-h CLI（amarket version/healthcheck/db status）
- [x] M0-i 启动脚本（start.bat + start.sh）
- [x] M0-j Notifier 骨架（WeWork + Lark + 合规 footer）
- [x] M0-k smoke 测试 + conftest（42 tests）
- [x] 全套验证：uv sync + alembic + ruff + mypy + pytest 全绿
- [x] 更新知识沉淀文档（CHANGELOG / PROJECT_STATE / 本日志）
- [x] commit + push feature branch

---

## 关键决策与用户输入

### 用户原话："好的，我们直接开始做吧"

**触发**：上一次 session 末我问"要不要现在用 superpowers:writing-plans 出 Phase 1 M0-M6 详细实施计划"。

**我的解读**：考虑用户在 session 03 多次表达过偏好"action over planning"+"superpowers 不必每次用"，"直接开始做" = 直接 M0 实施，跳过 writing-plans。

**风险**：如果误解了用户意图（其实是想要 writing-plans），M0 实施会浪费 session。但 spec v3 §17.1 已经把 M0 拆得足够清楚，可以直接按 spec 实施。

### 分支策略

**约束**：CONTRIBUTING.md §3（session 03 创建）要求所有改动走 PR、不允许直接 push main。

**当前现实**：小组目前只有用户一人 + Claude，没有其他 reviewer 在线。

**决策**：本次在 feature branch `feat/m0-project-skeleton` 实施，push feature 分支到 origin，让用户决定 merge 方式（自审 push / open PR / 等小组成员 review）。

---

## 实际进展（按 M0-a 到 M0-z 顺序）

### M0-a 项目骨架

- 创建 `pyproject.toml`：
  - 项目元数据（authors / requires-python ">=3.11,<3.15" / scripts entry `amarket`）
  - 生产依赖按 Spec v3 §16.1 全列
  - market-data extras（akshare/efinance/yfinance）
  - dev 依赖（pytest 全套 + ruff + mypy + respx + freezegun）
  - 工具配置内联：ruff lint+format / mypy strict / pytest / coverage（fail_under=70）
- 创建 `src/amarket/` 完整包结构（21 个 `__init__.py` 占位 + 子目录）：
  - api/ services/ adapters/{notifiers,ai,news_sources,market_sources}/ repositories/ domain/ core/ db/migrations/versions/ ui/{pages,components}/
- 创建 `tests/{unit,integration,e2e,fixtures}/` 目录

### M0-b 工具链

- `.pre-commit-config.yaml`：ruff (lint+format) + mypy（仅 src/）+ 通用 hooks（trailing-whitespace / end-of-file-fixer / check-yaml / check-toml / check-merge-conflict / check-added-large-files / detect-private-key / mixed-line-ending — Windows 脚本保留 CRLF）
- `.editorconfig`：UTF-8 / LF / 4 空格 / YAML 2 空格 / Windows .bat 用 CRLF

### M0-c CI

- `.github/workflows/ci.yml`：
  - `concurrency` 取消重复运行
  - 4 个 job：lint / typecheck / test (matrix 3.11+3.12) / docs-check
  - astral-sh/setup-uv@v3 + enable-cache
  - 覆盖率 artifact 上传

### M0-d 配置 + 日志

- `config/app.yml`：app / api / ui / project_meta 4 段
- `.env.example`：Phase 1 必填（企微/飞书 webhook、邮件）+ Phase 1 AI（Anthropic/DeepSeek）+ Phase 2 Brainmaster（CLAUDE_CLI_PATH）+ Telegram（stub）+ 应用运行时
- `src/amarket/services/config_service.py`：
  - `AppConfig` / `AppSection` / `ApiSection` / `UiSection` / `ProjectMetaSection` Pydantic models
  - `EnvSettings`（pydantic-settings，含密钥默认空）
  - `get_app_config` / `get_env_settings` lru_cache + `reload_config()`
- `src/amarket/core/logging.py`：
  - structlog JSON / Console 双格式
  - **密钥脱敏 processor**：识别 `(api[_-]?key|token|secret|password|webhook(?:_url)?|bot[_-]?key)` 字段，长字符串保留首末各 4 字符；qyapi.weixin.qq.com URL 自动 mask `?key=xxx`
  - 标准库 logging 同时配置（FastAPI/uvicorn 走 root logger）
  - `get_logger()` 工厂
- `src/amarket/core/exceptions.py`：`AmarketError` 基类 + ConfigError/SourceError/AIError(Degraded/Timeout)/NotifierError/RateLimitedError/ParamError/ParamPermissionDeniedError

### M0-e 数据库

- `alembic.ini`：标准配置（避开中文，因 alembic 用 locale 编码读 .ini，Windows cp1252 不支持 em-dash）
- `src/amarket/db/migrations/env.py`：动态注入 database_url；render_as_batch=True（SQLite ALTER TABLE 安全）；compare_type + compare_server_default
- `src/amarket/db/migrations/script.py.mako`：sqlmodel-aware migration 模板
- `src/amarket/db/migrations/versions/20260619_m0_users.py`：创建 users 表
- `src/amarket/db/session.py`：lazy engine + session_scope context manager + FastAPI `get_session` dependency + 测试用 `reset_engine` / `init_db`

### M0-f FastAPI

- `src/amarket/services/observability.py`：
  - `_check_db()` 用 `SELECT 1` 探活，记录 latency_ms
  - `_aggregate()` ok/degraded/down → healthy/degraded/unhealthy
  - `get_health_report()` 返回 `HealthReport`（含 project_meta + uptime）
- `src/amarket/api/health.py`：`/healthz`，unhealthy → 503
- `src/amarket/api/metrics.py`：`/metrics`，暴露 `amarket_uptime_seconds` Gauge + `amarket_app` Info；`include_in_schema=False` 不污染 OpenAPI
- `src/amarket/main.py`：app 工厂 + lifespan 钩子（启动时 configure_logging + 写 banner）+ CORS（按 cors_origins 配置）

### M0-g Streamlit Hello World

- `src/amarket/ui/app.py`：
  - 顶部 4 个 metric（版本 / Spec / Phase / Milestone）
  - 后端健康检查（HTTP 调 /healthz + JSON 展开）
  - 当前 M0 进度条（11 子任务）
  - 文档导航 + 合规 footer

### M0-h CLI

- `src/amarket/cli.py`（Typer）：
  - `amarket version` — 版本 + Spec/Phase/Milestone
  - `amarket healthcheck` — 进程内直接调 `get_health_report()`（无需起 FastAPI）
  - `amarket healthcheck --remote` — HTTP 调远端
  - `amarket healthcheck --json` — 原始 JSON
  - `amarket db status` — DB 子命令

### M0-i 启动脚本

- `start.bat`（Windows）：
  - 校验 uv 在 PATH
  - `uv sync --dev` → `alembic upgrade head` → 新开两个 cmd 窗口分别跑 uvicorn + streamlit
- `start.sh`（Linux/macOS）：
  - bash strict mode (-euo pipefail)
  - 后台跑两个进程
  - trap INT/TERM 杀两个子进程
  - `wait -n` 等一个挂掉 → 杀另一个

### M0-j Notifier 骨架

- `base.py`：`Notifier` Protocol + `NotificationResult` + `NotifierHealth` + `CardSpec` + **`COMPLIANCE_FOOTER`**
- `wework_bot.py`：text/markdown/news 卡片；errcode != 0 走 `ok=False`；bot_label 支持多机器人（如 `wework_alert`）
- `lark_bot.py`：text/post(markdown)/interactive 卡片
- 两者均 disabled 时（webhook 空）直接拒绝发送

### M0-k smoke 测试 + conftest

- `tests/conftest.py`：
  - autouse `_configure_logging_for_tests`（WARNING + console，避免单测刷屏）
  - autouse `_reset_config_caches`（每个 test 前后清空 config / env 缓存）
  - `in_memory_engine` / `session` / `patched_engine`（monkeypatch 全局 engine）
  - `api_client`（FastAPI TestClient + patched engine）
  - `clean_env`（清空敏感 env var）
- 9 个测试文件：
  - `test_config_service.py` (6 tests)
  - `test_logging_redaction.py` (6 tests)
  - `test_observability.py` (5 tests)
  - `test_api_endpoints.py` (3 tests)
  - `test_notifiers.py` (11 tests — wework + lark + respx mock)
  - `test_cli.py` (4 tests — typer.testing.CliRunner)
  - `test_models.py` (3 tests)
  - `test_enums.py` (4 tests)
- **42 passed in 1.23s，覆盖率 91.59%**

### M0-z 验证 + 修复迭代

跑通过程中遇到 4 个小问题：

1. **hatchling 不接受 `license = "Proprietary"`**（非 SPDX）→ 删 license 字段
2. **Python 3.14 上 lxml 无 wheel + MSVC 编译失败** → `uv python pin 3.12`
3. **alembic.ini 含中文 em-dash，Windows cp1252 locale 读不了** → 改为纯 ASCII
4. **starlette 自定义 DeprecationWarning 触发 pytest filterwarnings=error** → 加 ignore 规则
5. **ruff 266 报错主要是 RUF001-003 中文标点 + TC002 fixture 运行时类型** → ignore 这些规则
6. **mypy 报 structlog.get_logger 返回 Any** → 加 `cast(BoundLogger, ...)`

修完全绿。

---

## 产出（文件 / commits）

### 新增（~30 个文件）

**项目根**：
- `pyproject.toml` / `uv.lock` / `.python-version` / `alembic.ini`
- `.pre-commit-config.yaml` / `.editorconfig` / `.env.example`
- `start.bat` / `start.sh`

**CI**：`.github/workflows/ci.yml`

**配置**：`config/app.yml`

**应用源**（`src/amarket/`）：
- `__init__.py` / `main.py` / `cli.py`
- `api/__init__.py` / `api/health.py` / `api/metrics.py`
- `services/__init__.py` / `services/config_service.py` / `services/observability.py`
- `adapters/__init__.py` + 子包占位 + `adapters/notifiers/{base,wework_bot,lark_bot}.py`
- `repositories/__init__.py`
- `domain/__init__.py` / `domain/enums.py` / `domain/models.py`
- `core/__init__.py` / `core/logging.py` / `core/exceptions.py`
- `db/__init__.py` / `db/session.py` / `db/migrations/{env.py,script.py.mako}` / `db/migrations/versions/20260619_m0_users.py`
- `ui/__init__.py` / `ui/app.py` / `ui/pages/__init__.py` / `ui/components/__init__.py`

**测试**：`tests/conftest.py` + `tests/{unit,integration,e2e}/__init__.py` + 9 个测试文件

### 修改

- `.gitignore`（注释掉 `.python-version`，让 uv pin 文件入库）
- `CHANGELOG.md`（M0 段）
- `docs/PROJECT_STATE.md`（M0 完成状态）

### Commits（即将创建）

- 1 个 commit on `feat/m0-project-skeleton`：`feat(m0): project skeleton + tooling + CI + DB + FastAPI + Streamlit + CLI + Notifier scaffolding + 42 tests (91.59% coverage)`

---

## 阻塞 / 待解

无硬阻塞。

**需用户决策**（下次 session 开头）：
1. `feat/m0-project-skeleton` 分支 merge 策略（自审 push / open PR / 等小组成员）
2. 选 1 个新闻源做 M1 spike（同花顺 / 东方财富 / 雅虎财经）

**Phase 1 M1 启动前可以并行准备**：
- 填实 `.github/CODEOWNERS` 中的 GitHub 账号占位符
- GitHub 分支保护规则配置
- 创建 1 个企微机器人 webhook，填入 `.env`
- 选定 1 个 LLM API key（M2 需要）

---

## 下一次 Session 接力点

**首要任务**：
1. Session 启动 Checklist 走完
2. 询问用户 merge 策略（A/B/C），执行 merge
3. 进入 Phase 1 M1（数据基座 + 1 源新闻 + 1 源行情）

**先读**：
1. `CLAUDE.md`（已更新到 v3 + 小组联合）
2. `docs/PROJECT_STATE.md`（已更新到 M0 完成状态）
3. 本 session log（session 04）
4. Spec v3 §6.2.1（NewsSource 接口）+ §7.2（11+ 张表完整字段）+ §17.1（M1 验收标准）
5. `pyproject.toml`（看依赖清单 + 工具配置）
6. `src/amarket/`（理解已有模块结构）

**M1 大致工作量**：
- ~10 张表 SQLModel + Alembic migrations（M0 只建了 users）
- 1 个 NewsSource adapter（同花顺 / 东方财富 / 雅虎财经其一）— 需要抓包确认 endpoint
- 1 个 MarketDataSource adapter（akshare 接上证指数日线）
- NewsRepo / MarketSnapshotRepo
- 最小 `/api/news` GET endpoint（list + filter）
- 集成测试（M1 通过 = 抓 → 入库 → API 查回 端到端）

预估 2-3 天半工时（含网页解析调试时间）。

---

## 学到的经验

1. **Python 3.14 太新**：很多 C 扩展（如 lxml / simhash）还没构建 wheel，必须 pin 到 3.12 或更低。`uv python pin` 一行解决，uv 自动下载对应版本。
2. **alembic.ini 必须 ASCII**：Windows 默认 locale=cp1252，含中文 em-dash 会让 alembic crash。
3. **pytest filterwarnings=error 会被第三方 DeprecationWarning 误伤**：starlette 用了自定义 `StarletteDeprecationWarning`，不是 `DeprecationWarning` 的子类，必须单独 ignore。
4. **中文项目要 ignore ruff RUF001-003**：默认这些规则会报中文标点（fullwidth comma 等）"ambiguous"，是 false positive。
5. **structlog 返回类型是 Any**：`get_logger()` 包装层加 `cast(BoundLogger, ...)` 让 mypy strict 不抱怨。
6. **`.python-version` 应该入库**：uv 项目标准做法是 pin Python 版本入版本管理，新成员 clone 后 uv 自动下载对应版本。

---

## 用到的 Skill / 工具

- `Read` / `Glob` / `Bash`（git + uv + alembic + pytest）— Session 启动 + 验证 + 命令执行
- `TaskCreate` / `TaskUpdate` — 12 个 M0 子任务跟踪
- `Write` / `Edit` — 大量文件创建 + 修复迭代
- **未用 superpowers** — 按用户偏好简单规划用原生

---

## 🏁 Session 结束（2026-06-19, Session 04）

### 收尾检查（CLAUDE.md Session 结束 Checklist）

- [x] `docs/PROJECT_STATE.md` 已更新（M0 完成 + 下次 session 必读 3 件事）
- [x] 本 session log 已写完
- [x] `CHANGELOG.md` 已更新（Phase 1 M0 段）
- [x] 即将 commit 到 `feat/m0-project-skeleton` + push 远程

### 下次 session 启动者必读

按 `CLAUDE.md` 顶部 Session 启动 Checklist 走：

1. 读 `CLAUDE.md`
2. 读 `docs/PROJECT_STATE.md` ← 标注"下次必读 3 件事"
3. 读本 session log + sessions 03/02/01
4. `git log --oneline -10`
5. `git status` / `git branch`

读完后第一个动作：**询问用户 feat/m0-project-skeleton 分支 merge 策略**。

### 一句话总结

> Session 04：Phase 1 M0 完成。30 个新文件、42 tests passing、覆盖率 91.59%、lint/type/test 全绿。在 `feat/m0-project-skeleton` 分支，等用户决定 merge 方式。下次直接进 M1（数据基座 + 1 源新闻 + 1 源行情）。
