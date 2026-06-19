# Project State

**Last Updated**: 2026-06-19 (Session 04, M0 实施完成)
**Updated By**: Claude (Opus 4.7, 1M ctx) + User
**Next Action Owner**: 👤 **用户**（review feat/m0-project-skeleton 分支 → 决定 merge 方式）

---

## 🎯 下次 Session 必读：3 件事

### 1. 当前状态
- ✅ **Phase 1 M0 实施完成**，在分支 `feat/m0-project-skeleton` 上
- ✅ 42 unit tests passed
- ✅ Coverage 91.59%（要求 70%）
- ✅ Ruff / Mypy 全绿
- ✅ Alembic baseline migration 跑通
- ✅ FastAPI `/healthz` + `/metrics` 可用
- ✅ Streamlit Hello World 可起
- ✅ CLI `amarket healthcheck` 可用

### 2. 等待用户决定 merge 策略

**`feat/m0-project-skeleton` 分支**含 ~30 个新文件（pyproject + src/ + tests/ + CI + scripts），覆盖率 91.59% 已经过 CI 门槛。

| 选项 | 适用 | 操作 |
|------|------|------|
| **A. 自审 + push main**（当前推荐） | 暂无其他小组成员上线 review | `git checkout main && git merge feat/m0-project-skeleton --no-ff && git push origin main` |
| **B. 开 PR + self-approve** | 想走 PR 流程留痕 | `gh pr create --base main --head feat/m0-project-skeleton`，自审后用 admin 权限合 |
| **C. 等小组成员 review** | 其他成员近期能上线 | 把 branch push 远程，邀请成员到 GitHub repo 后 review 合 |

无论哪种选项，下次 session 开始时分支已经存在，可以直接继续 M1（数据基座 + 1 源新闻 + 1 源行情）。

### 3. 严禁动作
- ❌ 在 main 上直接修改（必须经分支 + merge）
- ❌ Force push main / feature branch
- ❌ 跳过 Session 启动 Checklist
- ❌ 引入任何形式的实盘下单代码

---

## 当前阶段

- **Spec**: #1 v3 — A 股实时新闻分析与行情看板（小组联合版）
- **Phase**: 🟢 **Phase 1 实施中**
- **Milestone**: **M0 ✅ 完成**（在分支 feat/m0-project-skeleton；待 merge main）
- **Sprint progress**: 1/6 Phase 1 milestones started + completed（M0 done；M1 next）
- **Session count**: 4 sessions
  - 2026-06-14 01: brainstorm + spec v1
  - 2026-06-14 02: Brainmaster 模式 → spec v2
  - 2026-06-19 03: Peersession PRD merge → spec v3 + 小组协作工件
  - **2026-06-19 04: M0 项目骨架实施（本次）**

---

## M0 实施总结

| 子阶段 | 交付 | 状态 |
|--------|------|------|
| M0-a | 项目骨架（pyproject.toml + src/amarket/ 完整包结构） | ✅ |
| M0-b | 工具链（ruff lint+format + mypy strict + pytest + pre-commit + editorconfig） | ✅ |
| M0-c | CI（.github/workflows/ci.yml — lint/typecheck/test，Python 3.11+3.12 矩阵） | ✅ |
| M0-d | 配置 + 日志（config/app.yml + ConfigService + structlog JSON + 密钥脱敏 processor） | ✅ |
| M0-e | 数据库（SQLite + Alembic baseline + users 表 migration） | ✅ |
| M0-f | FastAPI（/healthz + /metrics + 启动钩子 + CORS） | ✅ |
| M0-g | Streamlit Hello World（展示项目状态 + 调 /healthz） | ✅ |
| M0-h | CLI（Typer：amarket version / healthcheck / healthcheck --json / db status） | ✅ |
| M0-i | 启动脚本（start.bat + start.sh：一键 uv sync → alembic upgrade → FastAPI + Streamlit） | ✅ |
| M0-j | Notifier 骨架（base.py + WeWorkBotNotifier + LarkBotNotifier，含合规 footer） | ✅ |
| M0-k | smoke 测试 + conftest 基础设施（42 tests，conftest 含 in-memory engine / TestClient / env 隔离 fixtures） | ✅ |

**关键约束坚持**：
- ✅ 所有 public 函数 / 方法带 type hints
- ✅ 日志全走 structlog（无 print / 标准库 logging）
- ✅ 密钥走 .env，代码只用 env var 名
- ✅ 配置走 YAML + pydantic-settings
- ✅ 推送内容自动附加合规 footer（"📌 本信息仅供个人/小组学习参考，不构成任何投资建议"）
- ✅ 无实盘下单代码

---

## 下一步路径

### 立即（下次 session 开头）
1. Session 启动 Checklist
2. 询问用户 merge 方式（A/B/C），执行 merge
3. 进入 M1（数据基座）

### Phase 1 M1（数据基座）— 下次 session 主要工作
- 完整 11+ 张表 SQLModel + Alembic migrations（news_items / news_events / news_analysis / market_snapshots / sector_trends / alerts / reports / push_records / source_health / params / param_versions / audit_events / config_versions / subscriptions / news_sources）
- 1 源新闻 adapter（建议从同花顺或东方财富 7x24 开始）
- 1 源行情 adapter（akshare 接上证指数）
- NewsRepo + MarketSnapshotRepo
- 最小 `/api/news` GET endpoint
- 集成测试：抓取 → 入库 → 通过 API 查回

### Phase 1 M2-M6 概览
- M2：新闻去重 + 分类 + 评分；P0-P3 告警决策
- M3：完整看板 API + 静态 HTML POC
- M4：6 时段日报 + 完整推送（企微 + 飞书 + 邮件）
- M5：参数配置模块（版本 / 回滚 / 权限矩阵 / 审计）
- M6：集成测试 + UML + 文档 + 试运行

---

## 阻塞 / 待用户/小组输入

**软阻塞**（M1 启动前确认即可）：
- 填实 `.github/CODEOWNERS` 中的 GitHub 账号占位符
- GitHub 分支保护规则配置（main 受保护、需 PR + review）
- 选择 1 个新闻源做 M1 spike（同花顺 / 东方财富 / 雅虎财经）
- 配置至少 1 个 LLM API key（M2 AI 分析模块用）
- 创建 1 个企微机器人 webhook（M1 末验证 hello 推送）

**无硬阻塞** — 可以直接继续 M1。

---

## 当前 git 状态

- **分支**：`feat/m0-project-skeleton`（在分支上，未推远程）
- **main 上一次 commit**：`f41589f arch(spec1): merge peersession PRD into spec v3 + upgrade to team repo`
- **本分支累计**：M0 实施一次 commit（即将创建）

---

## 重要环境/配置变化（新增本次）

| 时间 | 变化 |
|------|------|
| **2026-06-19 (session 04)** | uv 项目初始化，pin Python 3.12（Python 3.14 上 lxml 无 wheel 需编译） |
| 2026-06-19 (session 04) | 安装 ~80 个生产依赖 + 15 个 dev 依赖 |
| 2026-06-19 (session 04) | SQLite DB 文件首次生成于 `data/amarket.db` |
| 2026-06-19 (session 04) | `.python-version` 入库（之前被 .gitignore 屏蔽，已修正） |

---

## 文档地图（增量）

新增 / 变化：

| 文档 / 文件 | 用途 |
|------------|------|
| `pyproject.toml` | uv 项目元数据 + 依赖 + 工具配置（ruff/mypy/pytest/coverage） |
| `.python-version` | 项目 Python 版本锁（3.12） |
| `uv.lock` | uv 依赖锁文件 |
| `alembic.ini` | Alembic 配置（动态注入 database_url） |
| `.pre-commit-config.yaml` | pre-commit 钩子（ruff + mypy + 通用） |
| `.editorconfig` | 跨编辑器格式统一 |
| `.github/workflows/ci.yml` | GitHub Actions CI（lint / mypy / test 3.11+3.12 矩阵） |
| `config/app.yml` | 应用全局 YAML 配置 |
| `.env.example` | 环境变量模板 |
| `start.bat` / `start.sh` | 一键启动脚本 |
| `src/amarket/**` | 应用源码（main.py / cli.py / ui/app.py / api/* / services/* / adapters/notifiers/* / domain/* / core/* / db/*） |
| `tests/**` | 测试套件（conftest + 9 个测试文件，42 tests） |

---

## 速查表（更新）

- **当前 spec**：`docs/superpowers/specs/2026-06-19-spec1-v3-merged.md` (v3)
- **当前 phase**：Phase 1 M0 ✅
- **当前 branch**：`feat/m0-project-skeleton`
- **首选 Python**：3.12
- **测试**：`uv run pytest -x` （42 tests，~1s）
- **覆盖率**：`uv run pytest --cov=src/amarket --cov-report=term-missing` （91.59%）
- **Lint**：`uv run ruff check .` + `uv run ruff format --check .`
- **类型**：`uv run mypy src/`
- **启动**：`./start.bat` / `./start.sh` → http://127.0.0.1:8080/docs + http://127.0.0.1:8501
- **健康检查**：`uv run amarket healthcheck` 或 `curl http://127.0.0.1:8080/healthz`
- **DB migration**：`uv run alembic upgrade head`
