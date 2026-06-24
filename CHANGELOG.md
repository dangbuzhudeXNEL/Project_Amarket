# Changelog

All notable changes to **Project_Amarket** are documented here.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format and
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Each Spec corresponds to a major milestone. Within a Spec, M0-M9 are intermediate releases.

---

## [Unreleased] — Spec #1 v3 进行中

### Added — M3a 完整收官（POC 6 页 + 双主题 + dump 脚本）（2026-06-24, Session 12, merged via PR #9 + #10 + #12 + #13）

**Phase 1 M3 拆分为 M3a（前端）+ M3b（API），M3a 又分 PR1（框架+核心3页）+ fix（theme+polish）+ PR2（剩余+赛博朋克）。本次完成 M3a 全部 3 个实现 PR。**

#### PR #13: M3a-PR2 — 剩余 3 页 + 赛博朋克 theme（commit `caf4c82`）

**替换 fix PR 加的 3 个占位页为真实实现：**

- `poc/assets/css/theme-cyberpunk.css` — 霓虹 cyan #00f5ff / magenta #ff006e / yellow #fcff00 + CRT 扫描线 + 背景网格 + Orbitron 标题 + JetBrains Mono 正文 + 边框辉光
- `poc/sectors.html` + `sectors.js` — 全屏 ECharts treemap (62vh) + 时间窗口切换 (1h/4h/1d) + 维度切换 (涨跌幅 / 新闻热度 / 市值权重) + 点格子联动该板块新闻列表（从 news.json 按 related_sectors 过滤 + 自定义 tooltip）
- `poc/reports.html` + `reports.js` — 6 时段 tab + marked.js CDN Markdown 渲染 + 未生成时段灰禁用 + 自定义 `.md-render` 样式（h1/h2/h3 / code / blockquote / hr 全套）
- `poc/params.html` + `params.js` — 赛博朋克 console UI：boot 进度条 + Orbitron 大标题（cyan→magenta→yellow 三色渐变）+ 参数分组（DATA_SOURCES / NEWS_COLLECTOR / KEYWORDS / AI_ENGINE / ALERTS / SCHEDULER）+ EDIT 按钮 magenta toast "EDIT_LOCKED // unlock = M5" + cyber-topbar 不引 nav.js + 自己的 ASCII 风 nav `<< back_to://amarket`

**用户验收**："最后的赛博朋克风很不错"

#### PR #12: theme not applying fix + 视觉 polish + 3 stub pages（commit `de7bcc8`）

**关键 bug fix：**
- 用户反馈 M3a-PR1 上线后页面是**纯白**，不是预期的 OKX 暗色
- 根因：`data-theme="okx"` 设在 `<body>`，但 CSS 用 `:root[data-theme]` 选择器（`:root` 即 `<html>`），CSS 变量没定义 → Tailwind preflight 默认白底覆盖
- 修：3 个 HTML 文件的 `data-theme` 从 `<body>` 移到 `<html>`

**视觉 polish（用户要求 "更 OKX 风、字号大点、大胆点"）：**
- 全局基准字号 14→**15px**
- 更深底色 #07080a + 更亮主文字 #f0f1f3
- 更饱和涨跌色 #00d97e / #ff4d5e（带辉光）
- LOGO 加白→cyan 渐变；topbar LIVE 脉动绿点
- Hero 市场卡片（22px 大价格 + ▲▼ 涨跌"药丸"）
- Macro 顶条 4 KPI（总新闻 / P0+P1 / 板块涨跌 / 数据时间）
- 卡片标题加左侧 cyan 小条 + 辉光
- 卡片 hover 抬升 2px + cyan glow
- Active nav 底部 cyan 下划线辉光
- 告警卡按等级染色左条

**404 修复：**
- 加 3 个 "PR2 即将" 占位页（sectors / reports / params）
- 每页 4 feature 卡片预告 PR2 内容
- params 占位页用 magenta 渐变彩虹色提前体验赛博朋克味

#### PR #10: M3a-PR1 — POC 框架 + 核心 3 页 + 全量 dump（commit `7fbf17e`）

**前端 — POC 3 个核心页面：**
- `poc/index.html` — Dashboard 首页：9 区域（市场状态栏 / 今日结论 / 实时新闻流 / P0-P1 卡片 / ECharts treemap mini 板块热力图 / 影响板块榜 / 个股异动占位 / 突发告警时间线 / 6 时段日报入口）
- `poc/news.html` — 新闻流：5 维度筛选（来源 / 分类 / 情绪 / 重要性 / 搜索）+ 3 种排序
- `poc/news-detail.html` — 单条新闻 + 完整 AI 分析（6 个评分指标 + 影响板块 + 关联标的 + 分析理由 + 风险提示 + 相关新闻 + URL 缺失/404 友好错误）

**前端 — 共享基础设施：**
- `poc/assets/css/theme-okx.css`（269 行）：OKX 配色 token + 卡片 / 表格 / tag / num / 滚动条等共享组件类
- `poc/assets/js/shared.js`：fetch wrapper / 数字-涨跌-时间-情绪格式化 / banner 错误注入 / 时钟 / 桌面宽度检测
- `poc/assets/js/nav.js`：5+1 链接顶部 nav 自动注入 + 当前页高亮 + 时钟 + 占位 refresh toggle（M3b 接）

**后端 — Mock 数据 dump 脚本：**
- `scripts/dump_poc_fixtures.py`（430 行）：从 `data/amarket.db` 一次性 dump 7 类 JSON
- 真实数据：dashboard.json (26KB) + news.json (117KB, 130 条) + 5×news-detail (含 related_news + ai_reasoning + risk_notes + content) + alerts.json (26KB, 73 条)
- Placeholder 数据：sectors.json (14 板块 mock) + reports.json (1 盘前 + 5 null) + params.json (15 个手写参数)
- CLI: `--db` / `--out` / `--limit` / `--pretty` / `--detail-samples`
- Windows cp1252 stdout 编码 fix（中文 print 不再崩）

**启动 + 工具脚本：**
- `poc/serve.bat` + `poc/serve.sh`：一键起 `python -m http.server 8090`
- `poc/README.md`：完整启动 + 故障排查

**测试 + 工程：**
- `tests/unit/test_dump_poc_fixtures.py`：9 个单测（含 tmp SQLite 种子 fixture）
- ruff / format / mypy 全绿
- CI 5/5 通过：Lint + Test (Py 3.11) + Test (Py 3.12) + Typecheck + Docs sanity

**`.gitignore` 修复**：加 `!poc/assets/data/` negation（之前 `data/` 规则误匹配）

#### PR #9: M3a 设计 spec（commit `9881763`）

写 `docs/superpowers/specs/2026-06-24-m3a-poc-pages-design.md`（821 行）。

### M3a 总体收益

- **6 个 POC 页面全部上线** — 5 OKX 暗色金融风 + 1 赛博朋克控制台
- **测试增量**：207 → 216（+9 dump 单测），coverage 维持 87.95%+
- **M3b 接 API 时改动 ≤ 6 行**：每页只改一行 `fetch('/assets/data/X.json')` → `fetch('/api/X')`
- **下一步**：M3b（看板 API + SectorTrendService）→ M4（推送 + 调度）→ M5（参数模块覆盖赛博朋克 demo）

---

### Fixed — M2 Brainmaster + Reviewer P1 backlog（2026-06-24, Session 11, merged via PR #4 + #5）

**Phase 1 M2 工程债务清零** ✅
Demo Brainmaster 路径暴露 2 个 Windows 真实环境 bug（unit test 测不出，mock 跳过了）+
收掉 reviewer 留下的 4 个 P1 backlog。M3 启动前所有阻塞已清。

#### PR #4: Brainmaster 真实环境兼容性（commit `52dfb18`）

**Bug #1 — Claude CLI v2.1+ 非交互模式 Write 工具静默失败**
- 现象：subprocess exit=0 但 agent 不写 output 文件
- 根因：`-p` 模式下 Write 需要 permission，默认要求用户交互确认
- 修复：加 `--permission-mode acceptEdits` 让 Write 自动被许可
- agent 只在 `data/ai/outputs/` 下写，安全可控

**Bug #2 — Windows `.CMD` wrapper 多行中文 prompt 乱码**
- 现象：手动 bash 跑 OK，Python subprocess 调失败
- 根因：`shutil.which('claude')` 返回 `claude.CMD`，cmd.exe 转发多行中文 + 反引号会被字符集转换乱码
- 修复：prompt 走 stdin (`input=`)，cmd 列表只保留 `-p` flag

**真实验证**：5 条高 importance 新闻通过 Brainmaster，AI 输出明显优于规则：
- 马克龙伊朗战争 → AI 关联能源/油气/军工/黄金 + 5 个 A 股个股代码 + 推理
- 俄罗斯央行降息 → AI 识别俄国≠中国央行，importance 5→3
- 广东省方案 → AI 识别区域政策非全国级，importance 5→3

**Regression tests**（防回归）：
- `test_claude_runner_uses_permission_mode_accept_edits`
- `test_claude_runner_passes_prompt_via_stdin_not_argv`

#### PR #5: Reviewer P1 backlog（commit `8e644bc`）

| ID | 问题 | 修复 |
|----|------|------|
| **P1-1** | `_has_any_analysis` provider-agnostic → rule 锁死 AI 升级 | 改 `_has_analysis_for_current_path`，AI 路径只看 `agent:*/sdk:*` 行 |
| **P1-2** | 同 news 升档双 alert → M4 双推 | 新 alert 高于已有时把旧 pending 标 `superseded`（升档 only） |
| **P1-3** | 黑名单新闻仍生成 alert | AlertService 加 `blacklist_keywords` + `from_config()` 自动加载 keywords.yml |
| **P1-5** | asyncio.gather 共享 session race 隐患 | `Session(engine)` 每 task 独立 + `expunge` 让 detached 对象可访问 |

**设计决策**：
- P1-2 只升档 supersede 不降档：避免误丢 P0 历史告警痕迹
- P1-3 黑名单只 skip alert 不删 analysis 行：保留审计能力
- P1-5 fallback 共享 session：engine 抓不到时（特殊场景）兼容原行为

**Regression tests**：10 个新 case（4 P1-1 / 3 P1-2 / 3 P1-3 / 1 P1-5）

#### Changed

- `config/app.yml`：`current_milestone: M1 → M2`（dashboard 顶部显示）
- CLI: `AlertService(session)` → `AlertService.from_config(session)`（一行升级 + 自动加载黑名单）

#### 统计

- **207 tests passed**（从 195 → +12: PR #4 +2 + PR #5 +10）
- **87.95% coverage**（不变）
- ruff + mypy + CI 5/5 全过
- 7 文件改动 / 530 行新增（含 commits 总和）

#### 留 backlog（reviewer P2，无阻塞）

- P2-1 `_compute_top_source` SQL GROUP BY 优化
- P2-2 `_source_cache` LRU 上限
- P2-3 SimHash distance==threshold 边界测试
- P2-4 market_hours 4 个端点边界 + 周末测试
- P2-5 DeepSeek json_object 中文 enum 真实 API 验证
- P2-6 `processed_by` 字符串集中常量

### Added — Phase 1 M2 智能层完整闭环（2026-06-21, Sessions 08-10, merged via PR #2）

**Phase 1 M2：新闻去重 + 分类 + 评分 + AI 分析 + P0-P3 告警 + 完整 pipeline** ✅
11 个子任务（M2-a 至 M2-k）全部完成，端到端 pipeline 用 130 条真新闻验证通过。

#### M2-b NewsDeduper — 三层去重 + 事件聚合（Session 08）
- L1 URL 完全相同 / L2 标题 normalize 后相同 / L3 SimHash 距离 < 3
- 写 `news_events` 聚合表 + 回填 `news_items.event_id + content_hash`
- 幂等：已分配 event_id 跳过；top_source 按命中频次自动更新
- 19 单测 / 93% coverage / `amarket dedupe news` CLI

#### M2-c NewsClassifier — 规则一级 / 二级 / 板块 / 标的（Session 09）
- 一级 8 类（multi_label，按 priority 排序）+ 二级 14+ 板块 + 代表股关联
- 黑名单标记不阻断分类（由上层决定怎么用）
- `from_config()` 一键加载真实 YAML
- 16 单测 / 93% coverage

#### M2-d SimpleRuleScorer — 规则路径评分（Session 09）
- importance/urgency 1-5 + sentiment 6 级 + confidence 固定 3
- 分类基线 + 热词权重 + source priority delta + 多板块加分
- urgency 受 max_urgency_bonus cap，盘中 +1（Asia/Shanghai 工作日 09:30-11:30/13:00-15:00）
- 22 单测 / 95% coverage

#### M2-e NewsAnalysisService — 编排（Session 10）
- 工作流：Classifier → AIProvider (FallbackChain) → Scorer 兜底 → 写 `news_analysis`
- 幂等 upsert by `(news_id, processed_by)`
- 异步批处理 + `asyncio.Semaphore` 并发控制 + 单条失败不拖垮 batch
- `AnalysisBatchResult` 统计 ai_success / rule_fallback / skipped / failed
- 10 单测含 fake AI provider 三态（success / fail / disabled）

#### M2-f AlertService — P0-P3 决策（Session 10）
- Spec §8.7 决策表：P0 (RISK/MACRO ∧ imp≥5 ∧ urg≥5) / P1 (imp≥4 ∧ urg≥4) / P2 (imp≥3) / P3
- 只对 P0/P1/P2 写 alerts 表；P3 仅留在 news_analysis
- 幂等 by `(news_id, level)`
- 纯函数 `evaluate_alert_level()` 可单独测；17 单测含 parametrize 决策表全 8 组

#### M2-h API 升级（Session 10）
- `/api/news` 自动 join 最新 NewsAnalysis + 最高 Alert，填充 primary_category / tags / sentiment / importance / urgency / alert_level
- 新增 `/api/alerts`（filter by level/status/since，含 news_title join）
- `AlertDTO` + `AlertListResponse` schemas

#### M2-i Dashboard 升级（Session 10）
- 新增 🚨 P0-P3 告警区（颜色标记 + level 筛选 + 触发原因展示）
- 新闻列表 badges：alert_level / 分类 / 情绪图标 / imp/urg / tags
- Milestone 进度同步到 M2 子任务粒度

#### M2-j 端到端集成测试（Session 10）
- 130 条真新闻 → `amarket analyze news --no-ai --reanalyze`
- 结果：130 NewsAnalysis (rule_fallback) + 0 failed
- AlertService：**1 P0**（马克龙伊朗战争）+ **1 P1**（韩国前防长泄密）+ **71 P2** + **57 P3**
- DB 一致：news_analysis 130 行 / alerts 73 行 ✓
- API 验证：`curl /api/alerts?level=P0` 正确返回 1 条

#### M2-k 收尾 + Code Review
- 调用 superpowers:code-reviewer agent 全面 review
- **报告**：1 P0 + 5 P1 + 6 P2
- **已修**：P0-1（`_highest_alert_for` 重写）+ P1-4（`/api/alerts` total 用 SQL COUNT）
- **进 backlog**（M3 启动前必收）：
  - P1-1 `_has_any_analysis` provider-agnostic skip
  - P1-2 等级升档双 alert 隐患
  - P1-3 黑名单与 alert 关系设计
  - P1-5 `asyncio.gather` + 共享 session race 隐患
- **进 backlog**（nice-to-have，无阻塞）：P2-1 至 P2-6 详见 `docs/sessions/2026-06-21-10-m2-complete.md`

### 统计
- **38 文件 / 5687 行新增**（5 个 commit squash 成 main `1773bbd`）
- **195 tests passed**（从 91 → 195，+104 个 M2 测试）
- **覆盖率 87.25%**（deduper 93% / classifier 93% / scorer 95% / analysis 88% / alert 96%）
- Mypy 66 files / Ruff / Pytest 全绿；CI 5/5 check 全过

### CLI 新增
- `amarket dedupe news [--limit] [--threshold] [--lookback-hours]`
- `amarket analyze news [--ai/--no-ai] [--alerts/--no-alerts] [--concurrency] [--reanalyze]`

### 设计决策（与 spec 一致）
- 默认 SimHash threshold=3（保守对齐 spec），生产可调到 8-10 平衡精召
- 黑名单只标记不阻断（M2-e/AI 路径有更多上下文做决策）
- 规则路径 confidence 固定 3（AI 路径会另算）
- AlertService 不考虑 subscriptions（留 M6 参数模块上线后接入）

### 已知不足（待后续 milestone 优化）
- 一级分类：英文 Yahoo 模板新闻全 fallback 到"市场行情"（M2-e AI 路径可补语义判断）
- Sentiment：规则路径覆盖 hint 词少，130 条真新闻全 NEUTRAL（M2-e AI 必须接通才有效）
- Pipeline 节点：当前 collector + dedupe + analyze 是 CLI 手动触发；M4 起接 APScheduler 自动跑

### Added — PR #1: 本地部署指南（2026-06-21, Session 08, merged `034bb6e`）

**Phase 1 文档加固**：给小组成员的完整本地部署文档 ✅

- 新增 `docs/LOCAL_DEPLOYMENT.md`（11 节 + 12 个 FAQ）
- 覆盖：uv 装法（Win/Mac/Linux）/ Python 自动管理 / 可选行情依赖 / `.env` 每项说明 / DB 初始化 / 跑测试验证 / 启动 + 4 URL 验证 / 端到端验证 / 常用命令 / 开发工作流 / 12 种故障排查
- `CONTRIBUTING.md §2` + `README.md 快速开始` 改为指向新文档
- 393 行新文档 / CI 5/5 全过

### Added — Phase 1 M2-a + M2-g 开场（2026-06-19, Session 06, branch `feat/m2-news-processing`）

**M2-a 规则配置 + M2-g 双路径 AI 架构** ✅（M2 后续 b/c/d/e/f/h/i/j/k 下次 session）

#### M2-a：规则配置文件
- `config/keywords.yml` — 60+ 突发关键词词典（含权重、关联类别、紧急度加分、情绪 hint）+ 黑名单（广告/导购过滤）
- `config/sectors.yml` — 14+ 板块映射表（AI算力/半导体/CPO/PCB/新能源车/光伏储能/创新药/消费/券商/地产链/红利/军工/低空经济/有色金属/出海链）+ 每板块 4-8 个代表个股
- `config/classification.yml` — 8 类一级分类规则（宏观政策/风险事件/公司公告/资金流/海外映射/大宗商品/市场行情/交易提示）+ priority 排序 + multi_label 配置

#### M2-g：Brainmaster + SDK 双路径 AI 架构（核心）
- **`AIProvider` Protocol**：统一 AI 调用入口，Service 层只 import 这里
- **`ClaudeAgentRunner`**（Tier 1 主，Brainmaster 模式）
  - subprocess 调本地 claude CLI + agent 文件输出 JSON
  - **零 API key 需求**（复用 Claude Code 订阅）
  - 校验链：exit=0 + 文件 mtime 已更新 + JSON valid + 必需字段齐
  - 失败分级：AIError / AIAgentDegradedError / AIAgentTimeoutError
  - asyncio.to_thread 包装阻塞 subprocess.run
- **`AnthropicSDKProvider`**（Tier 2 备）
  - 走 ANTHROPIC_API_KEY；支持 ANTHROPIC_BASE_URL（localhost proxy）
  - 默认 model: claude-sonnet-4-5（max_tokens=1500，temperature=0.3）
- **`DeepSeekSDKProvider`**（Tier 3 备）
  - 兼容 OpenAI SDK 协议（openai package）
  - 用 response_format=json_object 强制 JSON 输出
- **`FallbackChainProvider`**
  - 按优先级 try-then-fallback；任一子 provider AIError 自动切下一个
  - 全部失败 → 抛 AIError（调用方降级到 SimpleRuleScorer）
  - `children_health()` 暴露各子 provider 状态
- **`build_default_ai_provider()`** factory
  - 默认创建 [ClaudeAgentRunner, AnthropicSDK, DeepSeekSDK] 链
  - 可单独禁用任一 tier（M2 后期可在 dashboard 切换）
- **`.claude/agents/news-classifier-realtime.md`** — agent 定义
  - YAML frontmatter: sonnet / 8 turns / Read+Write+Glob+Grep 工具
  - 输入：`data/ai/inputs/<news_id>.json`（NewsAnalysisRequest schema）
  - 输出：`data/ai/outputs/<news_id>.json`（NewsAnalysisResult schema）
  - 严格输出契约 + 5 类异常处理 + 5 个禁止项（不允许"买入/卖出"具体指令）
- **`config/agents.yml`** — 完整配置：brainmaster + fallback_sdk + priority_order
- **测试**：`tests/unit/test_ai_providers.py`
  - 20 个新 test：ClaudeAgentRunner happy / degraded / timeout / error / health 4 路径
  - AnthropicSDK / DeepSeekSDK：happy / 无 key 禁用 / JSON 错误处理
  - FallbackChainProvider：4 种降级路径
  - Factory：默认/可禁用 tier
  - Protocol conformance（所有实现都符合 AIProvider Protocol）
  - 全部 mock subprocess + SDK，不打真 API

### 统计
- **新增 8 文件**（5 src + 1 agent + 2 config）
- **111 tests passed** (从 91 → 111, +20 个 AI 测试)
- **覆盖率 87.70%**
- Mypy 58 files / Ruff / Pytest 全绿

### 设计要点（提前 Brainmaster 到 M2 vs 原 Spec v3 设计）
- 原 Spec v3：Phase 1 仅 SDK，Brainmaster 留 Phase 2
- 用户决策：**Phase 1 M2 起就提供 Brainmaster + SDK 双路径**（一个 fallback chain）
  - 优点：零 API key 启动 + 同时兼容 SDK；架构灵活
  - Brainmaster + SDK 走同一个 `AIProvider` Protocol，Service 层一行代码切换

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
- Phase 1 M2：新闻处理（去重 / 分类 / 评分 / P0-P3 决策）

### Added — Phase 1 M1 实施完成（2026-06-19, Session 04 续）

**Phase 1 M1：数据基座 + 3 个新闻源 + 主要指数行情** ✅ 在同一 feature branch

- **DB schema 扩到 16 表**（M0 仅 users）：subscriptions / news_sources / source_health / news_items / news_events / news_analysis / market_snapshots / sector_trends / alerts / reports / push_records / params + param_versions / audit_events / config_versions
- **Repository 层**（BaseRepo + 6 个）：news / news_event / news_source / source_health / market_snapshot
- **新闻源 adapters**：
  - 🟢 EastmoneySource（主，东方财富 7x24，公开 JSON API，priority=high）
  - 🟢 SinaSource（备，新浪财经 7x24 直播流，priority=medium）
  - 🟢 YahooFinanceRssSource（备，雅虎财经 RSS，外市场覆盖，priority=medium）
  - 统一 `NewsSource` Protocol；async；fail-isolation
- **行情源 adapter**：
  - AkshareSource（A 股 6 个主要指数：上证 / 深证成指 / 创业板 / 沪深 300 / 上证 50 / 科创 50）
  - 串行调用绕开 mini_racer 并发 crash（Windows 已知问题）
- **Service 层**：
  - NewsCollector（编排多源 + 写 SourceHealth + 单源失败隔离）
  - MarketDataService（编排行情源 + 落地 market_snapshots）
- **API endpoints**：
  - `GET /api/news` (list+filter+paging)
  - `GET /api/news/{id}` (详情，404 处理)
  - `GET /api/dashboard/market-status` (从 market_snapshots 读最新)
  - `GET /api/dashboard/news-sources` (源运维状态)
- **CLI**：
  - `amarket collect news [--full]` — 3 源并行抓取（默认 5min realtime / `--full` 拉 12h）
  - `amarket collect market` — 一次性拉 6 个 A 股主要指数入库
- **Streamlit dashboard 升级**：
  - 新增 "📊 主要指数快照" 区域（6 个 metric 卡，颜色随涨跌）
  - 新增 "📰 最近新闻预览" 区域（含源筛选下拉，超链接到原文）
  - "🎯 当前 Milestone" 进度扩到 Phase 1 全 16 项（M0/M0+/M1-a~h + M2-M6 占位）
- **实测端到端**：
  - `collect news` 真实拉到 **100 条新闻** (eastmoney 50 + sina 30 + yahoo 20，~3.1s)
  - `collect market` 真实拉到 **6 个 A 股指数** (上证 4090.48 / 深证 16030.70 / 创业板 4252.39 / 沪深 300 4941.60 / 上证 50 2928.75 / 科创 50 1911.51)
- **测试**：5 个新测试文件 / 35 个新 case
  - test_news_adapters.py（respx mock 3 源）
  - test_news_collector.py（stub source 测编排 + 失败隔离）
  - test_market_akshare.py（monkeypatch ak.stock_zh_index_daily）
  - test_repositories.py（6 个 repo 关键路径）
  - test_api_news_dashboard.py（TestClient + in-memory SQLite + StaticPool）
  - **91 tests passed, 90.14% coverage**
- **修复 4 个工程坑**：
  - alembic.ini 中文 em-dash → ASCII (Windows cp1252 locale)
  - akshare mini_racer 并发 native crash → 改串行调用
  - Windows console cp1252 输出 emoji 挂 → cli.py 入口 reconfigure stdout=utf-8
  - SQLite `:memory:` per-connection 隔离 → conftest 用 StaticPool 共享 connection
- **Milestone 标识**：config/app.yml 的 `current_milestone: M0` → `M1`

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
