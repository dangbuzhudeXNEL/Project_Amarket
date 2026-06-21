# Project_Amarket — 本地部署指南

> **适用对象**：小组新成员、希望在自己机器上跑通整套系统的开发者
> **预计耗时**：30 ~ 60 分钟（取决于网络）
> **难度**：⭐⭐ 跟着步骤走基本能跑通；遇问题看末尾 [故障排查](#故障排查-faq)

---

## 0. 你将得到什么

跑完本指南后，你的本机会有：

- ✅ FastAPI 后端跑在 `http://127.0.0.1:8080`（含 `/docs` Swagger UI、`/healthz`、`/api/news` 等）
- ✅ Streamlit 看板跑在 `http://127.0.0.1:8501`（A 股指数 + 真实新闻预览 + 通知测试）
- ✅ SQLite 数据库（`amarket.db`，文件在仓库根）含 16 张表 + 真实新闻数据
- ✅ `uv run amarket ...` CLI 可用（抓行情、抓新闻、测通知）
- ✅ 全部测试用例可跑（≥ 111 passed，覆盖率 ≥ 70%）

---

## 1. 前置条件

| 工具 | 版本 | 检查命令 |
|------|------|----------|
| **Git** | 任意现代版本 | `git --version` |
| **Python** | 3.11 / 3.12 / 3.13 | `python --version`（uv 会自动管理，可选） |
| **uv** | 最新版（Astral 出品的 Python 项目管理器） | `uv --version` |
| **make**（可选） | 任意 | 暂无 Makefile，未来可能加 |

### 1.1 装 uv

**Windows (PowerShell)**：
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

**macOS / Linux**：
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

装完**重启终端**，然后：
```bash
uv --version   # 应输出形如 uv 0.5.x
```

> 💡 uv 会在 `uv sync` 时**自动下载** pinned 的 Python 版本到 `.venv/`，所以你**不需要**事先在系统装 Python。

### 1.2 确认 GitHub 访问

仓库是 Public 的，clone 不需要 token：
```bash
git ls-remote https://github.com/dangbuzhudeXNEL/Project_Amarket.git HEAD
```
能输出一行 commit hash 就说明网络通。

---

## 2. Clone + 装依赖（5 分钟）

```bash
# 1. clone（选个你喜欢的目录）
git clone https://github.com/dangbuzhudeXNEL/Project_Amarket.git
cd Project_Amarket

# 2. 看一下当前分支
git branch -a
# main 是稳定线；feat/m2-news-processing 是当前活跃开发分支

# 3. 装所有依赖（含 dev tools：pytest / ruff / mypy）
uv sync --dev
```

`uv sync --dev` 会：
- 在 `.venv/` 里建虚拟环境
- 装 pyproject.toml 里所有 `dependencies`
- 装 `dependency-groups.dev` 里所有开发依赖
- 第一次会下载 Python 3.12（约 30MB）+ 全部依赖（约 200MB）

**预期耗时**：3 ~ 5 分钟（看网速）。

### 2.1 装可选的行情依赖（akshare 等）

行情数据源（akshare / efinance / yfinance）是 **optional dependencies**，因为体积大且不是每个人都需要：

```bash
uv sync --dev --extra market-data
```

> ⚠️ 不装的话 `uv run amarket collect market` 会报 ImportError。如果你只是想看 UI / 测试新闻流，不装也行。

---

## 3. 配置环境变量（5 分钟）

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

打开 `.env`，**M0/M1/M2 阶段都不强制填任何东西**就能跑。下面说明各项的用处，按需填：

| 变量 | 何时需要 | 怎么拿 |
|------|--------|--------|
| `WEWORK_BOT_WEBHOOK_URL` | 想真实推送到企微群 | 企业微信群 → 添加群机器人 → 复制 webhook |
| `WEWORK_ALERT_BOT_WEBHOOK_URL` | P0 告警走独立渠道避免被节流 | 同上，新建一个机器人 |
| `LARK_BOT_WEBHOOK_URL` | 想推飞书 | 飞书群 → 添加自定义机器人 |
| `ANTHROPIC_API_KEY` | 想用 Claude SDK 跑 AI 分析 | https://console.anthropic.com |
| `DEEPSEEK_API_KEY` | 想用 DeepSeek SDK 兜底 | https://platform.deepseek.com |
| `CLAUDE_CLI_PATH` | Phase 2 Brainmaster 路径 | 装了 [Claude Code CLI](https://claude.com/claude-code) 后默认在 PATH，不用改 |
| `APP_ENV` / `LOG_LEVEL` / `LOG_FORMAT` | 调整运行行为 | 开发期 `LOG_FORMAT=console` 更易读 |

**最简上手配置**（什么也不填）：所有 SDK / 通知 / Brainmaster 都会 graceful degrade，dashboard 会显示"未配置"，但**绝不会崩溃**。

---

## 4. 初始化数据库（1 分钟）

```bash
uv run alembic upgrade head
```

这会在仓库根创建 `amarket.db`（SQLite 文件），并建好 16 张业务表。

验证：
```bash
# 看一眼数据库表
uv run python -c "import sqlite3; con=sqlite3.connect('amarket.db'); print('\n'.join([r[0] for r in con.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall()]))"
```

应该列出：`alembic_version`, `users`, `news_sources`, `news_items`, `news_events`, `news_analysis`, `market_snapshots`, `sector_trends`, `alerts`, `reports`, `push_records`, `params`, `param_versions`, `audit_events`, `config_versions`, `source_health`, `subscriptions` 等。

---

## 5. 跑测试验证（2 分钟）

```bash
uv run pytest -x
```

**期望**：`111 passed in XXs`（M2-g 阶段的基线）。

带覆盖率：
```bash
uv run pytest --cov=src/amarket --cov-report=term-missing
```

应该看到 `TOTAL ... 87%` 左右（M2 推进会涨）。

如果有 fail，去 [故障排查](#故障排查-faq) §A。

---

## 6. 一键启动（30 秒）

**Windows**：
```cmd
start.bat
```

**macOS / Linux**：
```bash
chmod +x start.sh   # 第一次需要
./start.sh
```

启动脚本会：
1. 自动 `uv sync --dev`（确认依赖最新）
2. 自动 `alembic upgrade head`（确认 DB schema 最新）
3. 拉起 **FastAPI** (port 8080) 和 **Streamlit** (port 8501)

> Windows 会开两个新 cmd 窗口分别跑两个服务；Linux/Mac 在前台跑，`Ctrl-C` 同时退两个。

---

## 7. 验证一切正常（2 分钟）

打开浏览器：

| URL | 应该看到 |
|-----|--------|
| http://127.0.0.1:8080/healthz | JSON：`{"status": "ok", "db": "ok", "version": "0.1.0"}` |
| http://127.0.0.1:8080/docs | Swagger UI（FastAPI 自带文档） |
| http://127.0.0.1:8080/api/news?limit=5 | JSON 数组（可能为空，下面 §8 拉数据） |
| http://127.0.0.1:8501 | Streamlit 看板：顶部 metric 卡 + 通知测试区 + 指数 + 新闻预览 |

---

## 8. 拉真实数据跑通端到端（3 分钟）

新开一个终端（保持服务在跑）：

```bash
# 抓 6 个 A 股指数（上证/深证/创业板/沪深300/中证500/科创50）
uv run amarket collect market

# 抓最近 12 小时全部 3 个新闻源
uv run amarket collect news --full
```

预期：
- `collect market` → `Inserted N market snapshots`
- `collect news --full` → 每个 source 报 `inserted=XX skipped=YY`，累计应 ≥ 100 条

刷新 Streamlit (http://127.0.0.1:8501) → 应该看到指数卡片和新闻列表都有内容。

---

## 9. 常用开发命令速查

```bash
# === 跑测试 ===
uv run pytest -x                                  # 快速，遇错即停
uv run pytest -k "test_news"                      # 只跑包含 news 的
uv run pytest --cov=src/amarket --cov-report=term # 带覆盖率

# === Lint / 类型 / 格式 ===
uv run ruff check .                # 检查
uv run ruff check . --fix          # 自动修小错
uv run ruff format .               # 重格式化
uv run mypy src/                   # 严格类型检查

# === DB 迁移 ===
uv run alembic upgrade head                            # 应用最新
uv run alembic downgrade -1                            # 回退一步
uv run alembic revision --autogenerate -m "msg"        # 生成新迁移
uv run alembic history                                  # 看历史

# === CLI ===
uv run amarket --help              # 看全部命令
uv run amarket collect market      # 抓行情
uv run amarket collect news        # 抓新闻（默认 5min 窗口）
uv run amarket collect news --full # 抓新闻（12h 窗口）
uv run amarket notify status       # 看 3 个通知渠道配置
uv run amarket notify test wework  # 配好 webhook 后测试

# === 单独跑服务（不用 start.bat / start.sh）===
uv run uvicorn amarket.main:app --host 127.0.0.1 --port 8080 --reload
uv run streamlit run src/amarket/ui/app.py --server.port 8501
```

---

## 10. 工作流（开发新功能）

详见 [`CONTRIBUTING.md`](../CONTRIBUTING.md)。**速记**：

```bash
# 1. 同步最新 main
git checkout main
git pull origin main

# 2. 开个人功能分支（名字带你的标识）
git checkout -b feat/<你的名字>-<topic>
# 如 feat/alice-news-dedup

# 3. 写代码 + 写测试

# 4. 提交前自检（绿了再 push）
uv run ruff check . --fix
uv run ruff format .
uv run mypy src/
uv run pytest -x

# 5. commit（用 Conventional Commits）
git add <你改的文件>
git commit -m "feat(news_collector): add eastmoney rss parser"

# 6. push + 开 PR
git push -u origin feat/<你的名字>-<topic>
gh pr create   # 用模板填好描述

# 7. CI 等绿，找 1 人 review，merge
```

---

## 11. 项目地图（去哪找什么）

| 想找 | 去 |
|------|---|
| 项目当前状态 | [`docs/PROJECT_STATE.md`](PROJECT_STATE.md) |
| Claude 协作约定 | [`CLAUDE.md`](../CLAUDE.md) |
| 协作规范 | [`CONTRIBUTING.md`](../CONTRIBUTING.md) |
| 当前 spec | [`docs/superpowers/specs/2026-06-19-spec1-v3-merged.md`](superpowers/specs/2026-06-19-spec1-v3-merged.md) |
| 历次 session 干了啥 | [`docs/sessions/`](sessions/) |
| 模块 owner | [`.github/CODEOWNERS`](../.github/CODEOWNERS) |
| Source 代码 | `src/amarket/` |
| 测试 | `tests/` |
| 配置 | `config/*.yml`（业务参数） + `.env`（密钥） |

---

## 故障排查 FAQ

### A. `pytest` 报错

#### A1. `ModuleNotFoundError: No module named 'amarket'`
没装好。重跑：
```bash
uv sync --dev
```

#### A2. `pytest: command not found`
忘了走 uv。所有命令前加 `uv run`：
```bash
uv run pytest -x
```

#### A3. 测试报 timezone / freeze 相关错
检查机器时钟是不是异常（Windows 偶发漂移）。

### B. `uv sync` 失败

#### B1. 网络错（下载 Python 或 package 超时）
1. 重试
2. 配 PyPI 镜像（中国大陆）：
   ```bash
   export UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple   # macOS/Linux
   set UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple      # Windows
   ```
3. 重跑 `uv sync --dev`

#### B2. `Python 3.12 not found`
让 uv 自动下载（默认行为）。如果你装了 Python 限制版本切换，把系统 PATH 里的 Python 临时移除再跑。

### C. `alembic upgrade head` 失败

#### C1. `Target database is not up to date`
说明本地 DB schema 跟代码不一致：
```bash
# 简单粗暴：删了重来
rm amarket.db        # macOS/Linux
del amarket.db       # Windows
uv run alembic upgrade head
```
(本地开发环境 DB 没价值数据，删了重来最快)

### D. 启动服务后访问报错

#### D1. `127.0.0.1:8080` 打不开
- 看启动脚本输出有没有报错
- 端口被占？换端口：
  ```bash
  uv run uvicorn amarket.main:app --port 8090
  ```

#### D2. Streamlit 转圈不出来
- 第一次启动慢，等 30 秒
- 看启动窗口有没有报错
- 强刷浏览器 (Ctrl+Shift+R)

### E. `uv run amarket collect news` 抓不到数据

#### E1. 网络问题
3 个新闻源（sina/eastmoney/yahoo）都需要外网。开 VPN 重试。

#### E2. 报 SSL / certificate 错
- macOS：装 certifi
- Windows：检查代理 / 防火墙

#### E3. 全部抓 0 条
- 看下结构化日志（`LOG_FORMAT=console` 更易读）
- 可能是新闻源页面改版了 → 报 issue / 群里说

### F. ruff format 在 CI 红、本地绿

历史问题，已修复（参见 [`.gitattributes`](../.gitattributes) 和 [session 07 日志](sessions/2026-06-19-07-ci-hotfix-and-m2-status.md)）。
如果你 clone 时间早于这次 hotfix，重新 pull main 即可。

### G. AI Provider 报"not configured"

完全正常。Phase 1 / M2 阶段 AI 是可选的：
- 想用 Claude SDK：填 `ANTHROPIC_API_KEY`
- 想用 DeepSeek SDK：填 `DEEPSEEK_API_KEY`
- 想用 Brainmaster（零 API key）：装 [Claude Code CLI](https://claude.com/claude-code) + `claude` 在 PATH
- 都不配也行，会自动 fallback 到规则评分

---

## 还卡住？

1. 看 [`docs/sessions/`](sessions/) 最新一篇，可能你遇到的问题最近刚解决
2. 群里 @ 技术负责人，**贴完整报错 + `uv run python -c "import sys; print(sys.version)"` + 操作系统**
3. 别憋着调一下午

---

**Last updated**: 2026-06-21
**Maintained by**: 见 [`.github/CODEOWNERS`](../.github/CODEOWNERS)
