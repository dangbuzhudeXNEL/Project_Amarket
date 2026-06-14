# Spec #1 — 基础设施 + 新闻引擎 (News Engine) 设计文档

| 元数据 | 值 |
|--------|----|
| 文档版本 | v1.0 |
| 创建日期 | 2026-06-14 |
| 作者 | Project_Amarket 团队（个人项目） |
| 状态 | 待用户审核 |
| 关联项目 | A股量化 + 新闻系统 整体平台（共 4 个 Spec） |
| 本 Spec 范围 | L0 通用基础设施 + L1-A 新闻引擎 MVP |
| 预计工时 | 3-4 周（半工时）/ 1.5-2 周（全工时） |

---

## 0. 文档导航

- [1. 背景与目标](#1-背景与目标)
- [2. 范围与非目标](#2-范围与非目标)
- [3. 关键决策汇总](#3-关键决策汇总)
- [4. 系统架构](#4-系统架构)
- [5. 模块详细设计](#5-模块详细设计)
- [6. 数据模型](#6-数据模型)
- [7. 关键工作流](#7-关键工作流)
- [8. 配置与密钥管理](#8-配置与密钥管理)
- [9. 错误处理与可观察性](#9-错误处理与可观察性)
- [10. 测试策略](#10-测试策略)
- [11. 项目结构](#11-项目结构)
- [12. 依赖清单](#12-依赖清单)
- [13. 实施里程碑](#13-实施里程碑)
- [14. 安全与合规](#14-安全与合规)
- [15. 未来扩展点](#15-未来扩展点)
- [16. 待用户确认事项](#16-待用户确认事项)

---

## 1. 背景与目标

### 1.1 产品愿景
构建一个 A 股量化 + 新闻一体化系统，覆盖：
- 盘前新闻智能推送
- 盘中 breaking news 实时推送
- A 股 / ETF 量化选股与策略执行
- 历史回测
- AI Feedback 与策略复盘
- 资产配置与风险管理

整个产品按"L0 基础设施 → L1 数据/新闻 → L2 回测 → L3 策略 → L4 智能"的依赖分层，按 4 个 Spec 分期交付。

### 1.2 本 Spec 的角色
本文档定义**首期 Spec #1**：通用基础设施（贯穿后续所有 Spec）+ 新闻引擎 MVP（独立可用）。
- 目的 1：快速跑通"调度 → 数据接入 → AI 处理 → 推送"完整闭环，验证整体架构假设
- 目的 2：铺设公共基础设施（配置、日志、可观察性、UI 框架、DB、调度），让后续 Spec 直接复用
- 目的 3：每日产出可见价值（推送），保持开发动力

### 1.3 成功标准

**功能性**：
- 工作日每天 08:30 准时推送 1 次盘前汇总（成功率 ≥ 99%）
- 盘中 breaking news 平均延迟 < 2 分钟（定义：从 `published_at` 时间戳到 `push_records.sent_at` 时间戳）
- 推送内容主观可读、信息密度合理，不产生"消息轰炸"

**工程性**：
- 单元测试覆盖率 ≥ 70%
- 关键路径有集成测试 / E2E 测试
- 7×24 小时连续运行不宕机，单点故障可自愈
- Streamlit 管理面板能查询新闻历史、推送日志、健康状态、可调阈值

---

## 2. 范围与非目标

### 2.1 In Scope（本 Spec 必须交付）

| 类别 | 项 |
|------|------|
| 基础设施 | 配置加载、密钥管理、日志、调度、Metrics、健康检查、SQLite + Alembic 迁移、Streamlit UI 框架、FastAPI 后端 |
| 新闻采集 | 财联社 / 东方财富 7x24 / 新浪 7x24 / 华尔街见闻 四源接入 |
| 新闻处理 | 跨源去重（SimHash）、规则分类（财报/政策/行业/公司/宏观）、Breaking 判定（来源 + 关键词） |
| AI 增强 | Claude API 集成（默认 `claude-sonnet-4-x`，具体 model id 在 `llm.yml` 中 pin）、Prompt 模板（Jinja2）、Prompt 缓存、降级链（Claude → DeepSeek → 原文） |
| 推送 | 企业微信群机器人（主渠道）、Telegram Bot adapter（仅 stub 实现） |
| UI | Streamlit 5 页：总览 / 新闻列表 / 推送日志 / 配置编辑 / 测试工具 |
| CLI | Typer 命令行：手动触发推送、查询、健康检查、数据库迁移 |
| 测试 | 单元、集成、E2E |
| 部署 | 本地 Windows 开发机直接 `uv run` 启动；提供 `start.bat` 一键启动 |

### 2.2 Out of Scope（明确不在本 Spec）

- A 股 / ETF 行情数据（Spec #2）
- 历史 K 线 / 财务数据 / 资金面（Spec #2）
- 回测引擎（Spec #2）
- BrokerAdapter / 模拟撮合 / 实盘接口（Spec #3）
- AI 选股策略 / 策略执行（Spec #3）
- 资产配置 / 组合优化 / 波动告警（Spec #4）
- AI Feedback / 策略复盘（Spec #4）
- 用户认证 / 多租户（数据模型预留但不实现）
- 移动端 App（推送通过企微即可触达手机）
- 公网部署 / Docker / Kubernetes（MVP 本地常驻即可）

### 2.3 显式 YAGNI（暂不做的诱惑）

- 消息队列（Redis/Kafka）：MVP 用 APScheduler in-process 完全够
- 微服务拆分：单体应用 + 清晰模块边界即可
- React 前端：Streamlit MVP 足够
- 用户系统：单用户配置文件即可
- 全量 AI 增强：MVP 只对盘前汇总 + breaking 摘要用 AI

---

## 3. 关键决策汇总

| 决策维度 | 决策值 | 理由 |
|---------|--------|------|
| **项目定位** | 个人自用 + 学习，预留 group use 扩展 | 当前个人需求；架构预留多租户字段（`user_id`）以便后期扩展 |
| **交易模式** | 信号 + 模拟，BrokerAdapter 预留实盘 | 个人开发无券商接入资质；架构分层后未来加 adapter 即可 |
| **运行环境** | 本地 Windows 开发机常驻 (`C:\AI\Claude\Project_Amarket`) | 隐私好、成本 0、调试方便；后续可平迁云端 |
| **主语言** | Python 3.11+ | 量化生态最强；类型 hints 完善 |
| **数据源策略** | akshare + efinance + yfinance + RSS（Spec #2 主用） | 免费可控；多源抽象 + 路由后期可加付费源 |
| **新闻源** | 财联社 / 东财 7x24 / 新浪 7x24 / 华尔街见闻 | 覆盖国内主流 breaking 90% 以上 |
| **LLM** | Claude (Anthropic API)，默认 Sonnet（具体 model id 在 `llm.yml` 配置，如 `claude-sonnet-4-5`、`claude-sonnet-4-7` 等，实施时 pin 当时最新版本）；`LLMProvider` 接口预留 DeepSeek / 通义 / 本地 | 用户已有 Anthropic 接入；Sonnet 性价比 vs Opus 显著更好 |
| **盘前推送** | 工作日 08:30 一次（节假日跳过） | 信息集中、低打扰、适合上班族 |
| **Breaking 判定** | 纯规则：高优来源 + 关键词命中 → 立即推；其他不推 | 延迟低、可预测、成本 0；可演进 |
| **推送渠道** | 企业微信群机器人（主） + Telegram Bot（仅 adapter stub） | 中国大陆稳定；架构多渠道可插拔 |
| **UI** | Streamlit 极简面板 + 业务/UI 分层架构 | 1-2 天即可搭出；后期 Spec #2+ 可按需替换为 React |
| **持久化** | SQLite + SQLModel + Alembic | 零运维；ORM 切 PostgreSQL 0 改动 |
| **调度** | APScheduler in-process | MVP 不需要分布式队列 |
| **依赖管理** | `uv` (Astral) | 比 pip/poetry 快 10-100x，现代工具 |
| **HTTP 客户端** | `httpx`（异步） | 替代 requests，原生 async / HTTP2 |
| **日志** | `structlog` JSON | 结构化、可后接 ELK/Loki |
| **指标** | Prometheus 格式 `/metrics` | 标准生态 |

---

## 4. 系统架构

### 4.1 分层架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Project_Amarket                              │
│                                                                     │
│  ┌──────────────────┐    ┌─────────────────┐    ┌────────────────┐ │
│  │  Streamlit UI    │    │   CLI (Typer)   │    │  APScheduler   │ │
│  │  Admin Panel     │    │   人工触发/调试  │    │  cron 任务     │ │
│  └─────────┬────────┘    └────────┬────────┘    └────────┬───────┘ │
│            └──────────────────────┴───────────────────────┘         │
│                                ↓                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │            ⚡ FastAPI HTTP Server (REST API)                 │   │
│  │  /api/news /api/push /api/config /healthz /metrics          │   │
│  └────────────────────────────┬────────────────────────────────┘   │
│                                ↓                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │     🧠 Service Layer（纯 Python，可单元测试）                 │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │   │
│  │  │NewsCollector │  │ NewsClassifier│  │ NewsPusher       │ │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘ │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │   │
│  │  │ AIService    │  │ ConfigService│  │ ObservabilityService│ │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘ │   │
│  │  ┌──────────────┐                                          │   │
│  │  │SchedulerSvc  │                                          │   │
│  │  └──────────────┘                                          │   │
│  └────────────┬─────────────────────────────────┬─────────────┘   │
│               ↓                                  ↓                  │
│  ┌──────────────────────┐         ┌────────────────────────────┐  │
│  │ 📦 Repository Layer  │         │ 🔌 Adapter Layer            │  │
│  │ - NewsRepo           │         │ NewsSource(4):              │  │
│  │ - PushLogRepo        │         │  Cls / Eastmoney / Sina /   │  │
│  │ - ConfigRepo         │         │  Wallstreet                 │  │
│  │ - UserRepo           │         │ LLMProvider:                │  │
│  │ (SQLModel ORM)       │         │  Claude(主) / DeepSeek(备)  │  │
│  └─────────┬────────────┘         │ Notifier:                   │  │
│            ↓                       │  WeWorkBot(主) / Telegram(预)│ │
│  ┌──────────────────────┐         └────────────────────────────┘  │
│  │ 💾 SQLite (本地文件)  │                                          │
│  └──────────────────────┘                                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 核心架构原则

1. **依赖倒置**：Service 层依赖 Adapter 接口（`NewsSource`、`LLMProvider`、`Notifier`），不直接依赖实现
2. **单一入口配置**：所有可调参数走 `config/*.yml` + `.env`，**禁止硬编码**
3. **结构化日志**：`structlog` 输出 JSON，便于后续接入聚合系统
4. **故障隔离**：任一新闻源 / LLM / 推送渠道故障不影响整体（断路器 + 降级链）
5. **多租户数据模型**：所有业务表带 `user_id`（MVP 单值，扩展不破坏）
6. **可测试性优先**：每个 service 30s 内单元测试通过，无需启动 DB（依赖注入）
7. **可观察性内建**：Prometheus metrics + 健康检查 + 结构化日志，从 day 1 就有

### 4.3 进程模型

MVP 阶段所有组件**跑在同一个 Python 进程**：
```
python -m amarket  →  启动一个进程，内含：
├── FastAPI/uvicorn (端口 8080)         # API + 健康检查 + metrics
├── APScheduler                          # 在 FastAPI 启动钩子中起
└── Streamlit 单独进程 (端口 8501)       # 通过 start.bat 同时拉起
```

后期可拆分为：API 进程 + Worker 进程 + UI 进程，但 MVP 不必。

---

## 5. 模块详细设计

### 5.1 Service 层模块

#### 5.1.1 `NewsCollector`（新闻采集服务）
- **职责**：调度各 `NewsSource` 拉取新闻、标准化、去重、入库
- **关键方法**：
  - `collect_since(since: datetime) -> List[NewsItem]`：盘前用，拉过去 N 小时
  - `poll_realtime() -> List[NewsItem]`：实时轮询，每 60s 调用
- **依赖**：`NewsSource[]`、`NewsRepo`、`ObservabilityService`
- **故障处理**：单源失败不影响其他源；连续 3 次失败发告警

#### 5.1.2 `NewsClassifier`（新闻分类与判定服务）
- **职责**：对入库的新闻进行规则分类（tag/sentiment 初版可空）、Breaking 判定
- **关键方法**：
  - `process_batch(items: List[NewsItem]) -> List[NewsProcessing]`
  - `classify_realtime(item: NewsItem) -> NewsProcessing`：含 breaking 判定
  - `is_breaking(item: NewsItem) -> bool`：规则引擎
- **依赖**：`NewsRepo`、`ConfigService`（拿关键词/权重）、`UserRepo`（拿订阅）
- **去重逻辑**：SimHash(标准化标题) 距离 < 阈值（如 3）则视为同事件

#### 5.1.3 `NewsPusher`（推送服务）
- **职责**：渲染模板、多渠道路由、节流、失败重试、写日志
- **关键方法**：
  - `push_premarket(summary: str) -> PushRecord`
  - `push_breaking(item: NewsItem, processing: NewsProcessing) -> PushRecord`
  - `push_manual(content: str, channels: List[str]) -> PushRecord`
- **依赖**：`Notifier[]`、`PushLogRepo`、`ConfigService`
- **节流**：全局 6/h + 1/min；订阅相关无上限；其他 3/h
- **重试**：3 次指数退避（1s/2s/4s）；最终失败切换备用渠道；再失败告警

#### 5.1.4 `AIService`（LLM 调用服务）
- **职责**：封装 LLM 调用，Prompt 缓存、超时控制、降级链
- **关键方法**：
  - `summarize_for_premarket(items: List[NewsItem]) -> str`（Markdown 摘要）
  - `summarize_breaking(item: NewsItem) -> BreakingSummary`（结构化）
  - `call(prompt_id: str, vars: dict, output_schema: BaseModel | None) -> Any`
- **依赖**：`LLMProvider[]`（Claude 主、DeepSeek 备）、`PromptCache`
- **缓存**：`hash(prompt_id, vars)` 为 key，TTL 24h；Claude 启用 prompt caching
- **降级**：主 LLM 失败 → 备 LLM；都失败 → 抛 `LLMUnavailableError`，调用方决定

#### 5.1.5 `ConfigService`（配置服务）
- **职责**：加载 YAML 配置、热重载、密钥脱敏（日志中）
- **关键方法**：
  - `get(key: str, default=None) -> Any`
  - `reload()`：从文件重读
  - `watch()`：可选 inotify 监听
- **依赖**：文件系统、`pydantic-settings`

#### 5.1.6 `SchedulerService`（调度服务）
- **职责**：注册 cron 任务、节假日判断
- **关键方法**：
  - `start()` / `stop()`
  - `add_job(func, trigger)`
  - `list_jobs()` / `pause(job_id)` / `resume(job_id)`
- **依赖**：`APScheduler`、`MarketCalendar`
- **任务清单**：
  - `premarket_push`：工作日 08:25 触发（08:30 完成推送）
  - `realtime_poll`：交易时段每 60s（9:25-11:35, 12:55-15:05）
  - `weekend_archive_poll`：非交易日（周末 + 节假日）每 30 分钟低频归档入库，不推送
  - `health_self_check`：每 5 分钟自检并暴露

#### 5.1.7 `ObservabilityService`（可观察性服务）
- **职责**：健康检查、Prometheus 指标、异常告警分发
- **依赖**：`Notifier`（告警专用渠道）

### 5.2 Adapter 层模块

#### 5.2.1 `NewsSource` 接口

```python
class NewsSource(Protocol):
    code: str  # 'cls' / 'eastmoney' / 'sina' / 'wallstreet'
    name: str
    priority: Literal['high', 'medium', 'low']

    async def fetch_since(self, since: datetime) -> List[RawNewsItem]: ...
    async def fetch_realtime(self) -> List[RawNewsItem]: ...
    def health_check(self) -> SourceHealth: ...
```

每个实现按"先 HTTP 抓取 → 解析 HTML/JSON → 标准化为 `RawNewsItem`"流水线。具体来源接入方式 **需在 M1/M2 实施阶段实地调研、抓包确认**（下列仅为初步推测，发现实际端点可能变化）：

- **财联社**：候选入口 `https://www.cls.cn/telegraph`（HTML 抓取）或抓包发现的 JSON 接口
- **东方财富 7x24**：候选入口 `https://kuaixun.eastmoney.com/`（公开 API 或抓包）
- **新浪 7x24**：候选入口 `https://finance.sina.com.cn/7x24/`（HTML 抓取或 RSS）
- **华尔街见闻**：候选入口 `https://wallstreetcn.com/live/global`（API 或 RSS）

⚠️ **接入预期**：M1/M2 实施时需为每个源单独写 adapter，建立 fixtures（保存真实响应样本），保证回归测试稳定。源 API/HTML 结构变化是常见维护成本。

⚠️ **合规注意**：所有抓取需设置合理 User-Agent、遵守 robots.txt、控制频率（< 1 req/s/source），避免被封 IP。

#### 5.2.2 `LLMProvider` 接口

```python
class LLMProvider(Protocol):
    model_id: str
    
    async def complete(
        self,
        messages: List[Message],
        max_tokens: int,
        temperature: float = 0.3,
        response_format: Literal['text', 'json'] | dict = 'text',
        cache_breakpoints: List[int] | None = None,  # 用于 prompt caching
    ) -> LLMResponse: ...
    
    def get_usage(self) -> LLMUsage: ...
```

`ClaudeProvider` 实现使用 Anthropic SDK，启用 prompt caching（节省 90% 输入成本）。

#### 5.2.3 `Notifier` 接口

```python
class Notifier(Protocol):
    code: str  # 'wework' / 'telegram'
    
    async def send_text(self, text: str) -> NotificationResult: ...
    async def send_markdown(self, markdown: str) -> NotificationResult: ...
    async def send_card(self, card: CardSpec) -> NotificationResult: ...
    def health_check(self) -> NotifierHealth: ...
```

- `WeWorkBotNotifier`：调用 `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=XXX`
- `TelegramBotNotifier`：调用 Telegram Bot API（MVP 只 stub，不实际测试）

### 5.3 Repository 层模块

每个 Repo 封装一类聚合根的 CRUD + 查询：

- `NewsRepo`：`save_batch`、`get_by_source_msg_id`、`find_unprocessed`、`find_by_simhash_within`、`query_by_window`
- `PushLogRepo`：`save`、`count_within_window`、`find_recent_by_user`
- `ConfigRepo`：（暂不用，配置走 YAML；预留）
- `UserRepo`：`get_default_user`（MVP）、`list_subscriptions`

### 5.4 Domain 层

`domain/models.py` 包含所有 SQLModel 表 + Pydantic 业务对象。  
`domain/enums.py` 包含所有枚举（`SourcePriority`、`NewsTag`、`Sentiment`、`PushKind`、`PushStatus` 等）。

---

## 6. 数据模型

### 6.1 表设计概览

| 表 | 主要目的 | 估算行数（1 年） |
|----|---------|---------------|
| `users` | 用户（MVP 单行） | 1 |
| `subscriptions` | 关注的股票/板块/关键词 | 10-100 |
| `news_sources` | 新闻源配置 + 运行时统计 | 4 |
| `news_items` | 原始新闻 | 50-200 万 |
| `news_processings` | 分类/评分/AI 摘要结果 | 50-200 万 |
| `push_records` | 推送日志 | 5000-2 万 |
| `push_batches` | 推送批次（盘前汇总） | 250-500 |

### 6.2 详细字段

#### `users`
```
id            INTEGER PRIMARY KEY
name          TEXT NOT NULL
timezone      TEXT DEFAULT 'Asia/Shanghai'
created_at    DATETIME NOT NULL
```

#### `subscriptions`
```
id            INTEGER PRIMARY KEY
user_id       INTEGER NOT NULL REFERENCES users(id)
kind          TEXT NOT NULL CHECK (kind IN ('stock','sector','keyword'))
value         TEXT NOT NULL  -- e.g., '000001', '半导体', '降息'
weight        INTEGER DEFAULT 50  -- 0-100, 影响 breaking 评分
enabled       BOOLEAN DEFAULT TRUE
created_at    DATETIME
INDEX (user_id, kind, enabled)
UNIQUE (user_id, kind, value)
```

#### `news_sources`
```
id              INTEGER PRIMARY KEY
code            TEXT UNIQUE NOT NULL  -- 'cls'|'eastmoney'|'sina'|'wallstreet'
name            TEXT NOT NULL
priority        TEXT DEFAULT 'medium'  -- 'high'|'medium'|'low'
enabled         BOOLEAN DEFAULT TRUE
last_pulled_at  DATETIME
last_error      TEXT
consecutive_failures INTEGER DEFAULT 0
```

#### `news_items`（核心表）
```
id              INTEGER PRIMARY KEY
source_id       INTEGER NOT NULL REFERENCES news_sources(id)
source_msg_id   TEXT NOT NULL  -- 源平台原始 ID
title           TEXT NOT NULL
content         TEXT  -- 可空（部分快讯只有标题）
url             TEXT
published_at    DATETIME NOT NULL  -- 源平台发布时间
ingested_at     DATETIME NOT NULL  -- 我方入库时间
content_hash    TEXT  -- SimHash 64-bit hex，跨源去重用
raw_payload     JSON  -- 源 API 原始数据
UNIQUE (source_id, source_msg_id)
INDEX (published_at)
INDEX (content_hash)
INDEX (source_id, published_at)
```

#### `news_processings`
```
id              INTEGER PRIMARY KEY
news_id         INTEGER NOT NULL REFERENCES news_items(id)
tag             TEXT  -- 'finance'|'policy'|'industry'|'company'|'macro'|'other'
sentiment       TEXT  -- 'positive'|'negative'|'neutral'
importance      INTEGER  -- 0-10
stocks          JSON  -- [{code, name, weight}]
sectors         JSON  -- [{name, weight}]
keywords        JSON  -- [str]
summary         TEXT  -- AI 生成的摘要
is_breaking     BOOLEAN DEFAULT FALSE
processed_by    TEXT  -- 'rule'|'llm:claude-sonnet-4-x'|...
processed_at    DATETIME
UNIQUE (news_id, processed_by)
INDEX (is_breaking, processed_at)
```

#### `push_records`
```
id              INTEGER PRIMARY KEY
user_id         INTEGER NOT NULL REFERENCES users(id)
kind            TEXT NOT NULL  -- 'premarket'|'breaking'|'manual'
batch_id        INTEGER REFERENCES push_batches(id)  -- nullable
channel         TEXT NOT NULL  -- 'wework'|'telegram'
news_ids        JSON  -- 关联新闻 id 列表
content         TEXT NOT NULL  -- 渲染后的实际内容（审计用）
sent_at         DATETIME
status          TEXT NOT NULL  -- 'pending'|'sent'|'failed'|'rate_limited'
error_message   TEXT
attempt_count   INTEGER DEFAULT 0
INDEX (user_id, sent_at)
INDEX (kind, sent_at)
INDEX (status, sent_at)
```

#### `push_batches`
```
id              INTEGER PRIMARY KEY
kind            TEXT NOT NULL  -- 'premarket'|'breaking_burst'
trigger_time    DATETIME NOT NULL
news_count      INTEGER
status          TEXT  -- 'pending'|'completed'|'failed'
created_at      DATETIME
```

### 6.3 配置 vs 数据库

| 数据类型 | 存储位置 | 理由 |
|---------|---------|------|
| 关键词词典 | `config/keywords.yml` | 版本化、可 review |
| 推送时间表 | `config/scheduler.yml` | 同上 |
| 来源权重 | `config/sources.yml` | 同上 |
| AI Prompt 模板 | `config/prompts/*.j2` | 同上 |
| LLM 选型/参数 | `config/llm.yml` | 同上 |
| API 密钥/Webhook | `.env`（git ignore） | 安全 |
| 用户订阅 | DB | 运行时增删 |
| 调度执行历史 | DB（APScheduler 自带表） | 运行时状态 |
| 业务数据 | DB | 持续累积 |

### 6.4 数据保留策略

| 数据 | 保留期 | 策略 |
|------|--------|------|
| `news_items` 原文 | 永久 | 1 年约 100-500 MB，可控 |
| `news_processings` | 永久 | 未来 AI 训练价值 |
| `push_records` | 永久 | 审计需要 |
| 应用日志（文件） | 90 天滚动 | `loguru` rotation |
| APScheduler 执行历史 | 30 天 | 防表膨胀 |

### 6.5 时间与节假日

- **存储统一 UTC**，显示按用户时区（默认 `Asia/Shanghai`）
- 交易日历用 `chinese-calendar` Python 库（PyPI 上保持年度更新，使用时 pin 当时最新版）；备用 `akshare.tool_trade_date_hist_sina()` 缓存到 `data/trade_calendar.json`
- 节假日跳过盘前 / 盘中调度；周末仍以**低频归档模式**（每 30 分钟）收集新闻入库，不主动推送（用于后续回顾分析）

---

## 7. 关键工作流

### 7.1 盘前推送流程（工作日 08:30）

```
08:25 APScheduler cron 触发 premarket_push_job()
  │
  ├─→ MarketCalendar.is_trading_day(today)? → 否则直接 return
  │
  ├─→ NewsCollector.collect_since(now - 12h)
  │     ├─→ [Cls, Eastmoney, Sina, Wallstreet].fetch_since(...) 并行
  │     ├─→ NewsRepo.save_batch(...) UNIQUE(source_id, source_msg_id) 跳重复
  │     └─→ 返回新增的 news_items
  │
  ├─→ NewsClassifier.process_batch(unprocessed_items)
  │     ├─→ 规则打标 (tag, sentiment 初版可空)
  │     ├─→ SimHash 跨源去重
  │     └─→ 写 news_processings
  │
  ├─→ AIService.summarize_for_premarket(top_N_items)
  │     ├─→ 渲染 prompts/summarize_premarket.j2
  │     ├─→ LLMProvider.complete(<sonnet-model-id-from-config>)
  │     │     prompt: "你是A股资深分析师..."
  │     │     输出: Markdown 格式 5 段（夜美股/政策/公司/行业/重点）
  │     └─→ 失败 → 降级 DeepSeek → 仍失败 → 走"原文头条列表"模板
  │
  ├─→ NewsPusher.push_premarket(summary)
  │     ├─→ 渲染 templates/premarket.j2（加 emoji + 日期 + 来源标注）
  │     ├─→ WeWorkBotNotifier.send_markdown(content)
  │     │     失败 3 次重试 → 切换备用渠道（如配置） → 仍失败发告警
  │     ├─→ PushLogRepo.save(push_record)
  │     └─→ Prometheus metrics 上报
  │
  └─→ ObservabilityService.report_premarket_complete()
```

### 7.2 Breaking news 流程（交易时段每 60s）

```
APScheduler 每 60s 触发 realtime_poll_job()
  │
  ├─→ MarketCalendar.is_trading_hours()? → 否则 return
  │
  ├─→ NewsCollector.poll_realtime()
  │     └─→ 各源 fetch_realtime()（只取最近 5 分钟）
  │
  ├─→ for item in new_items:
  │     ├─→ NewsClassifier.classify_realtime(item)
  │     │     ├─→ 规则1: source.priority='high' AND keyword_hit(HOT_KEYWORDS) → breaking
  │     │     ├─→ 规则2: hit user subscriptions → breaking
  │     │     └─→ SimHash 跨源去重（5 min 窗口）→ 同事件不重复推
  │     │
  │     └─→ if is_breaking:
  │           ├─→ 节流检查：
  │           │    - 全局: max 6/h, max 1/min
  │           │    - 用户级: 订阅相关无上限, 通用 max 3/h
  │           ├─→ 通过 → NewsPusher.push_breaking(item)
  │           └─→ 被节流 → 加入 burst_batch，5 min 后汇总推送
```

### 7.3 AI 调用降级链

```
AIService.summarize(prompt_id, vars, model=<sonnet-model-id-from-config>)
  │
  ├─→ PromptCache.lookup(hash(prompt_id, vars)) [TTL 24h]
  │     └─→ HIT → 返回缓存
  │
  ├─→ MISS → LLMProvider.complete()
  │     ├─→ ClaudeProvider:
  │     │     - 启用 prompt caching (system prompt 加 cache_control)
  │     │     - 30s 超时
  │     │     - 2 次指数退避重试
  │     ├─→ 失败 → 降级 DeepSeek（若配置）
  │     └─→ 仍失败 → 抛 LLMUnavailableError
  │
  ├─→ 调用方处理 LLMUnavailableError:
  │     - 盘前: 走"原文头条列表"模板（不依赖 AI）
  │     - Breaking: 走"原文标题+来源"模板
  │
  └─→ 成功 → PromptCache.save(...) → 返回结构化结果
```

---

## 8. 配置与密钥管理

### 8.1 配置文件清单

```
config/
├── app.yml             # 应用全局配置
├── llm.yml             # LLM 选型与参数
├── sources.yml         # 新闻源配置 + 权重
├── keywords.yml        # Breaking 关键词词典
├── scheduler.yml       # 调度时间表
├── notifiers.yml       # 推送渠道配置
└── prompts/
    ├── summarize_premarket.j2
    └── breaking_template.j2
```

### 8.2 示例配置

**`app.yml`**
```yaml
app:
  name: amarket
  env: dev
  timezone: Asia/Shanghai
  log_level: INFO
  data_dir: ./data
  database_url: sqlite:///./data/amarket.db
api:
  host: 127.0.0.1
  port: 8080
ui:
  port: 8501
```

**`llm.yml`**
```yaml
default_provider: claude
default_model: claude-sonnet-4-5  # 实施时 pin 当时最新 Sonnet model id（如 claude-sonnet-4-7 等），参考 https://docs.anthropic.com/en/docs/about-claude/models
fallback_chain:
  - claude
  - deepseek
providers:
  claude:
    model: claude-sonnet-4-5
    max_tokens: 2000
    temperature: 0.3
    timeout_seconds: 30
    enable_prompt_cache: true
    api_key_env: ANTHROPIC_API_KEY
  deepseek:
    model: deepseek-chat
    max_tokens: 2000
    temperature: 0.3
    timeout_seconds: 30
    api_key_env: DEEPSEEK_API_KEY
    base_url: https://api.deepseek.com
```

**`sources.yml`**
```yaml
sources:
  - code: cls
    name: 财联社电报
    priority: high
    base_url: https://www.cls.cn
    poll_interval_seconds: 60
    rate_limit_per_minute: 30
  - code: eastmoney
    name: 东方财富 7x24
    priority: high
    base_url: https://kuaixun.eastmoney.com
    poll_interval_seconds: 60
    rate_limit_per_minute: 30
  - code: sina
    name: 新浪财经 7x24
    priority: medium
    base_url: https://finance.sina.com.cn
    poll_interval_seconds: 90
    rate_limit_per_minute: 20
  - code: wallstreet
    name: 华尔街见闻
    priority: medium
    base_url: https://wallstreetcn.com
    poll_interval_seconds: 120
    rate_limit_per_minute: 15
```

**`keywords.yml`**
```yaml
hot_keywords:  # 命中即视为 breaking 候选
  - { value: 涨停, weight: 8 }
  - { value: 跌停, weight: 8 }
  - { value: 突发, weight: 10 }
  - { value: 重大, weight: 9 }
  - { value: 紧急, weight: 9 }
  - { value: 利好, weight: 6 }
  - { value: 利空, weight: 6 }
  - { value: 停牌, weight: 9 }
  - { value: 复牌, weight: 7 }
  - { value: 加息, weight: 9 }
  - { value: 降息, weight: 9 }
  - { value: 央行, weight: 7 }
  - { value: 证监会, weight: 8 }
  # ... 用户可在 UI 中扩充
blacklist:  # 含这些词的新闻直接过滤（广告/无关）
  - 推广
  - 广告
  - 内含链接的导购
```

**`scheduler.yml`**
```yaml
jobs:
  - id: premarket_push
    enabled: true
    cron: "25 8 * * 1-5"   # 工作日 08:25 启动（推送前 5 min 预拉数据）
    timezone: Asia/Shanghai
    skip_holidays: true
  - id: realtime_poll
    enabled: true
    interval_seconds: 60
    active_windows:
      - { start: "09:25", end: "11:35" }
      - { start: "12:55", end: "15:05" }
    skip_holidays: true
  - id: weekend_archive_poll   # 周末/节假日低频归档（仅入库不推送）
    enabled: true
    interval_seconds: 1800   # 每 30 分钟
    only_on_non_trading_days: true
  - id: health_self_check
    enabled: true
    interval_seconds: 300
```

**`notifiers.yml`**
```yaml
default_business_channel: wework
default_alert_channel: wework_alert
channels:
  wework:
    type: wework_bot
    webhook_url_env: WEWORK_BOT_WEBHOOK_URL
    rate_limit_per_minute: 20
  wework_alert:
    type: wework_bot
    webhook_url_env: WEWORK_ALERT_BOT_WEBHOOK_URL
    rate_limit_per_minute: 20
  telegram:
    type: telegram_bot
    bot_token_env: TELEGRAM_BOT_TOKEN
    chat_id_env: TELEGRAM_CHAT_ID
    enabled: false  # MVP 不启用
```

### 8.3 `.env.example`

```bash
# ===== LLM =====
ANTHROPIC_API_KEY=sk-ant-xxxxx
DEEPSEEK_API_KEY=
# ===== Notifier =====
WEWORK_BOT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxx
WEWORK_ALERT_BOT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxx
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
# ===== App =====
APP_ENV=dev
LOG_LEVEL=INFO
```

### 8.4 密钥处理原则

- `.env` 永远在 `.gitignore`
- 启动时密钥脱敏后写一行 INFO 日志（如 `LLM key loaded: sk-ant-***xxx`）
- 任何日志/异常堆栈中不允许出现完整密钥（用 `structlog` processor 过滤）

---

## 9. 错误处理与可观察性

### 9.1 故障隔离矩阵

| 故障类型 | 隔离策略 | 告警阈值 |
|---------|---------|---------|
| 单个新闻源不可用 | 标记 `last_error`、其他源继续 | 连续 3 次失败 |
| LLM API 不可用 | 降级到备用 LLM → 降级到纯规则 | 连续 5 次失败 |
| 推送渠道失败 | 3 次指数退避 → 切换备用渠道 | 备用也失败 |
| 数据库不可用 | 关键写操作进内存队列、恢复后重放 | 30 秒未恢复 |
| 调度器卡死 | 外部 watchdog（每 5 分钟 ping `/healthz`）+ 自动重启脚本 | 单次未响应 |

> **Watchdog 归属说明**：watchdog 是一个**与主应用进程独立**的小脚本（Windows 用 Task Scheduler 注册 `watchdog.ps1`，每 5 分钟运行一次；Linux 用 systemd timer 或 cron）。其唯一职责是 `curl /healthz`，超时或返回非 healthy 时执行 `taskkill /F /IM uvicorn.exe` 然后重启 `start.bat`。脚本本身放在 `scripts/watchdog/`。

### 9.2 日志策略

- 框架：`structlog` → JSON 输出
- 文件：`logs/app.{YYYY-MM-DD}.jsonl`，按日滚动，保留 90 天
- 关键字段：`timestamp`, `level`, `event`, `module`, `user_id`, `news_id`, `trace_id`, `duration_ms`
- 错误同时写一份纯文本到 `logs/errors.log` 方便人工浏览

### 9.3 Prometheus 指标 (`/metrics`)

```
# 采集
news_items_collected_total{source}
news_collection_duration_seconds{source}
news_collection_failures_total{source, error_type}

# 分类
news_classified_total{tag, is_breaking}
news_classification_duration_seconds

# 推送
push_records_total{channel, kind, status}
push_duration_seconds{channel}
push_throttled_total{user_id, reason}

# AI
ai_calls_total{provider, model, success}
ai_tokens_used_total{provider, model, kind}   # kind=input|output|cache_read|cache_write
ai_call_duration_seconds{provider, model}
ai_cache_hits_total{prompt_id}

# 健康
scheduler_jobs_run_total{job_id, status}
scheduler_jobs_misfired_total{job_id}
db_query_duration_seconds{operation}
```

### 9.4 健康检查 `/healthz`

```json
{
  "status": "healthy|degraded|unhealthy",
  "checks": {
    "db": { "status": "ok", "latency_ms": 3 },
    "scheduler": { "status": "ok", "running_jobs": 2 },
    "sources": {
      "cls": { "status": "ok", "last_pulled_at": "..." },
      "eastmoney": { "status": "ok" },
      "sina": { "status": "ok" },
      "wallstreet": { "status": "degraded", "last_error": "..." }
    },
    "llm": { "status": "ok", "active_provider": "claude" },
    "notifier": { "status": "ok" }
  },
  "last_successful_premarket": "2026-06-13T08:30:12+08:00",
  "last_successful_breaking": "2026-06-13T14:15:33+08:00",
  "uptime_seconds": 123456
}
```

### 9.5 告警分级与路由

| 级别 | 触发条件 | 路由 |
|------|---------|------|
| DEBUG/INFO | 普通业务事件 | 仅日志 |
| WARN | 单源失败、节流、降级 | 日志 + 标记 |
| ERROR | 推送失败、AI 全降级、DB 异常 | 日志 + 企微告警机器人 |
| CRITICAL | 调度器死、watchdog 触发 | 日志 + 告警 + 尝试自愈 |

告警渠道必须**与业务推送渠道分离**（独立机器人 webhook），避免告警自己被节流。

---

## 10. 测试策略

### 10.1 测试金字塔

```
                /\
               /E2E\           3-5 个 E2E 场景（真抓 1 源、Mock LLM、Mock 推送）
              /─────\
             /集成测试 \         每 service 1-2 个，用 SQLite in-memory
            /─────────\
           /  单元测试    \      覆盖率 ≥ 70%（Repo / Service / Adapter）
          /─────────────\
```

### 10.2 工具栈

- `pytest` + `pytest-asyncio` + `pytest-cov`
- `pytest-mock` 用于 mock
- `httpx-mock` 用于 HTTP 接口 mock（新闻源抓取）
- `freezegun` 用于时间穿越（节假日、调度时间）
- `respx` 用于 Anthropic SDK HTTP mock
- 真实 LLM 调用走 `--integration` 标记，CI 不跑

### 10.3 关键测试场景

| 编号 | 场景 | 类型 |
|------|------|------|
| T-01 | 同源新闻去重（按 source_msg_id） | 单元 |
| T-02 | 跨源同事件去重（SimHash） | 单元 |
| T-03 | Breaking 判定规则：高优源 + 关键词 → 通过 | 单元 |
| T-04 | Breaking 判定：低优源 + 关键词 → 不通过 | 单元 |
| T-05 | 用户订阅命中 → breaking | 单元 |
| T-06 | 节流：1 分钟内第 2 条 breaking → 拒绝/累积 | 单元 |
| T-07 | 节假日不触发盘前推送 | 单元（freezegun） |
| T-08 | 单源 500 错误其他源继续 | 集成 |
| T-09 | LLM 超时降级到原文模板 | 集成 |
| T-10 | 推送失败重试 3 次 + 切换备用渠道 | 集成 |
| T-11 | E2E：完整盘前流程（抓→分类→AI→推送→入库） | E2E |
| T-12 | E2E：完整 breaking 流程 | E2E |
| T-13 | E2E：watchdog 触发自愈 | E2E |

### 10.4 CI（GitHub Actions）

```yaml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --dev
      - run: uv run ruff check .
      - run: uv run mypy src/
      - run: uv run pytest --cov=src --cov-report=xml --cov-fail-under=70
```

---

## 11. 项目结构

```
Project_Amarket/
├── README.md
├── pyproject.toml              # uv 项目配置
├── uv.lock
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── start.bat                   # Windows 一键启动脚本
├── start.sh                    # Linux/macOS 一键启动脚本
│
├── docs/
│   └── superpowers/
│       ├── specs/
│       │   └── 2026-06-14-news-engine-design.md   ← 本文件
│       └── plans/              # 实施计划（下一步用 writing-plans 生成）
│
├── config/
│   ├── app.yml
│   ├── llm.yml
│   ├── sources.yml
│   ├── keywords.yml
│   ├── scheduler.yml
│   ├── notifiers.yml
│   └── prompts/
│       ├── summarize_premarket.j2
│       └── breaking_template.j2
│
├── data/                       # 运行时数据（.gitignore）
│   ├── amarket.db
│   ├── trade_calendar.json
│   └── logs/
│
├── src/
│   └── amarket/
│       ├── __init__.py
│       ├── main.py             # FastAPI app 入口
│       ├── cli.py              # Typer CLI
│       ├── ui/                 # Streamlit
│       │   ├── __init__.py
│       │   ├── app.py          # Streamlit 入口
│       │   ├── pages/
│       │   │   ├── 01_home.py
│       │   │   ├── 02_news_list.py
│       │   │   ├── 03_push_log.py
│       │   │   ├── 04_config_editor.py
│       │   │   └── 05_test_tools.py
│       │   └── components/
│       │
│       ├── api/                # FastAPI routers
│       │   ├── __init__.py
│       │   ├── news.py
│       │   ├── push.py
│       │   ├── config.py
│       │   ├── health.py
│       │   └── metrics.py
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   ├── news_collector.py
│       │   ├── news_classifier.py
│       │   ├── news_pusher.py
│       │   ├── ai_service.py
│       │   ├── config_service.py
│       │   ├── scheduler_service.py
│       │   └── observability.py
│       │
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── news_sources/
│       │   │   ├── base.py
│       │   │   ├── cls.py
│       │   │   ├── eastmoney.py
│       │   │   ├── sina.py
│       │   │   └── wallstreet.py
│       │   ├── llm/
│       │   │   ├── base.py
│       │   │   ├── claude.py
│       │   │   └── deepseek.py
│       │   └── notifiers/
│       │       ├── base.py
│       │       ├── wework_bot.py
│       │       └── telegram_bot.py
│       │
│       ├── repositories/
│       │   ├── base.py
│       │   ├── news_repo.py
│       │   ├── push_repo.py
│       │   ├── config_repo.py
│       │   └── user_repo.py
│       │
│       ├── domain/
│       │   ├── models.py       # SQLModel 表
│       │   ├── enums.py
│       │   └── schemas.py      # Pydantic 业务对象
│       │
│       ├── core/
│       │   ├── logging.py      # structlog 配置
│       │   ├── exceptions.py
│       │   ├── cache.py        # Prompt cache
│       │   ├── market_calendar.py
│       │   ├── simhash.py
│       │   ├── ratelimit.py
│       │   └── utils.py
│       │
│       └── db/
│           ├── session.py
│           ├── base.py
│           └── migrations/     # Alembic
│               ├── env.py
│               └── versions/
│
└── tests/
    ├── __init__.py
    ├── conftest.py             # 公共 fixtures
    ├── unit/
    │   ├── services/
    │   ├── adapters/
    │   ├── repositories/
    │   └── core/
    ├── integration/
    │   ├── test_news_pipeline.py
    │   ├── test_push_pipeline.py
    │   └── test_ai_fallback.py
    ├── e2e/
    │   └── test_premarket_flow.py
    └── fixtures/
        ├── cls_sample.html
        ├── eastmoney_sample.json
        └── llm_responses.json
```

---

## 12. 依赖清单

### 12.1 生产依赖

| 包 | 用途 | 版本约束 |
|------|------|---------|
| `fastapi` | HTTP 框架 | ^0.115 |
| `uvicorn[standard]` | ASGI 服务器 | ^0.32 |
| `streamlit` | UI 框架 | ^1.40 |
| `sqlmodel` | ORM | ^0.0.22 |
| `alembic` | DB 迁移 | ^1.13 |
| `apscheduler` | 调度 | ^3.10 |
| `anthropic` | Claude SDK | ^0.40 |
| `httpx` | HTTP 客户端 | ^0.27 |
| `structlog` | 结构化日志 | ^24.0 |
| `loguru` | 日志辅助（rotation） | ^0.7 |
| `typer` | CLI | ^0.14 |
| `pydantic` | 数据校验 | ^2.9 |
| `pydantic-settings` | 配置加载 | ^2.6 |
| `jinja2` | 模板渲染 | ^3.1 |
| `chinese-calendar` | 节假日 | ^1.10 |
| `simhash` | 文本去重 | ^2.1 |
| `prometheus-client` | 指标 | ^0.21 |
| `tenacity` | 重试 | ^9.0 |
| `pyyaml` | YAML 解析 | ^6.0 |
| `python-dotenv` | env 加载 | ^1.0 |

### 12.2 开发依赖

| 包 | 用途 |
|------|------|
| `pytest` | 测试 |
| `pytest-asyncio` | async 测试 |
| `pytest-cov` | 覆盖率 |
| `pytest-mock` | mock |
| `httpx-mock` | HTTP mock |
| `respx` | Anthropic SDK mock |
| `freezegun` | 时间穿越 |
| `ruff` | Lint + Format |
| `mypy` | 静态类型检查 |
| `pre-commit` | git hooks |

---

## 13. 实施里程碑

### 13.1 里程碑划分

| 阶段 | 时长（半工时） | 关键交付 | 完成判定 |
|------|---------------|---------|---------|
| **M0：项目骨架** | 1-2 天 | uv 项目初始化、CI、pre-commit、SQLite+Alembic baseline、健康检查 `/healthz`、Streamlit Hello World、企微机器人 hello 推送 | 能本地启动 + 推送一条"hello"到企微 |
| **M1：单源端到端** | 2-3 天 | 财联社 adapter、`NewsCollector` 基础、`NewsRepo`、最小推送链路 | 财联社抓 → 入库 → 推送一条到企微 |
| **M2：多源 + 去重 + 规则分类** | 3-4 天 | 4 源全部接入、SimHash 去重、`NewsClassifier` 规则、breaking 判定 | 4 源同时拉取 + 准确去重 + 高优新闻被标 breaking |
| **M3：AI 增强** | 2-3 天 | `LLMProvider`（Claude + DeepSeek）、Prompt 缓存、降级链 | 一条新闻 → AI 摘要 → 结构化输出 |
| **M4：盘前 + 调度** | 2-3 天 | APScheduler 集成、节假日、08:30 cron、模板渲染 | 模拟运行下能按 cron 触发完整盘前流程 |
| **M5：可观察性 + UI** | 2-3 天 | Streamlit 5 页、`/metrics` 完整指标、告警机器人 | UI 能看新闻/推送/配置、Prometheus 能爬指标 |
| **M6：集成测试 + 文档 + 试运行** | 2-3 天 | E2E 测试、README、运维手册、连续运行 1 周 | 7 天无人工干预正常运转、生成运行报告 |

**总计 ≈ 3-4 周（半工时）/ 1.5-2 周（全工时）**

### 13.2 里程碑评审点

每个里程碑结束：
1. 跑全部测试（确保不退化）
2. 手动 demo 关键功能
3. 更新 `docs/CHANGELOG.md`
4. Git tag `m0` / `m1` / ...

---

## 14. 安全与合规

### 14.1 数据合规

- 个人自用阶段，不收集他人数据，无 PII 风险
- 抓取新闻源遵守 `robots.txt`、控制 QPS（< 1 req/s/source），不构成 DoS
- 推送内容只用于自用，不对外转载/二次分发，避免版权问题
- 日志中不记录用户身份信息（MVP 单用户也尽量脱敏）

### 14.2 密钥安全

- 所有密钥（API key、webhook）走 `.env`，**严禁提交**
- `.gitignore` 强制包含 `.env`、`data/`、`logs/`
- 启动时校验关键密钥是否齐全，缺失则 fail-fast
- 日志中密钥永远脱敏（中段星号化）

### 14.3 推送内容合规

- 盘前/breaking 推送末尾固定附加："📌 本信息仅供个人学习参考，不构成任何投资建议"
- 不在推送中直接给出"买入/卖出"等操作指令（即使是个人自用阶段，保持习惯避免日后扩展时翻车）

### 14.4 网络抓取边界

- 单源失败容忍：连续 3 次 5xx 自动暂停 30 分钟
- IP 被封风险：所有 adapter 通过统一 `httpx.AsyncClient` + 共享代理（如配置）+ User-Agent 池
- 未来若被限制，可通过配置接入第三方源聚合服务（如金十、汇通）

---

## 15. 未来扩展点

本 Spec 完成后，下列扩展不需要重大架构变动：

### 15.1 后续 Spec 依赖

| Spec | 直接复用本 Spec 的能力 |
|------|---------------------|
| Spec #2 行情数据 + 回测 | DB 框架、配置管理、调度、日志、Streamlit UI 框架、CLI、健康检查 |
| Spec #3 BrokerAdapter + AI 选股 | LLM 调用层、Notifier（推送策略信号）、可观察性 |
| Spec #4 资产配置 + AI Feedback | LLM 调用层、用户订阅模型、UI 页面、推送 |

### 15.2 渐进增强清单

| 增强 | 触发条件 | 改造点 |
|------|---------|--------|
| AI 全量增强（每条新闻都过 AI） | 用户反馈摘要价值高、成本可接受 | 仅扩 `NewsClassifier` 流程，加配置开关 |
| 增加新闻源 | 发现新闻覆盖盲区 | 写新 `NewsSource` adapter |
| 增加推送渠道（Bark/邮件） | 用户需要多端覆盖 | 写新 `Notifier` adapter |
| AI 评分加权（混合规则 + AI） | 纯规则误报率高 | 改 `NewsClassifier.is_breaking()` 加 AI 评分调用 |
| 多用户（group use） | 需求出现 | 在 user/订阅表新增多行；UI 加身份层；推送渠道按 user 拆分 |
| 替换 React 前端 | Spec #2 复杂可视化需求 | 不改业务/API；新增 `frontend/` 项目 |
| 切换到 PostgreSQL | 数据量超 5GB 或多用户高并发 | 改 `database_url`；alembic 迁移；其他 0 改动 |
| 拆分进程（API/Worker/UI） | 部署到云端 | 在 `main.py` 加运行模式参数 |

---

## 16. 待用户确认事项

以下事项尚未完全敲定，建议在实施开始前确认。**未确认时使用方括号内的默认值**：

1. **Anthropic API 接入方式**：MVP 默认使用 `ANTHROPIC_API_KEY` 环境变量调用 Anthropic 官方 API（按 token 计费）。是否有特殊的 Bedrock/Vertex/中转方式？[默认：官方 API]
2. **Claude 模型 ID**：实施 M0 前请 pin 当时最新 Sonnet 4.x model id（如 `claude-sonnet-4-5`、`claude-sonnet-4-7` 等）。是否在某些场景升级到 `opus`？[默认：Sonnet 4.x 全场景统一；仅当成本/质量出现明显问题时切 Opus]
3. **GitHub 仓库**：是否需要推送到远程？私有/公开？[默认：暂只本地，需要时再加 remote]
4. **代码许可证**：[默认：暂不加 LICENSE，个人项目]
5. **数据库初始内容**：MVP 启动需要哪些种子数据？默认会插入：1 个用户 + 4 个新闻源记录
6. **企微机器人 webhook**：你需要自行在企业微信群创建机器人并把 webhook 填入 `.env.WEWORK_BOT_WEBHOOK_URL`
7. **是否提交后续 Spec 设计**：本文档完成后，是否立刻开始 Spec #2（行情数据 + 回测）的 brainstorming？[默认：先完成 Spec #1 实施再开始 Spec #2]

---

## 附录 A：术语表

| 术语 | 解释 |
|------|------|
| Spec | Specification，本系列的设计文档单元 |
| Adapter | 适配器，封装外部依赖的统一接口实现 |
| Service | 业务服务，无状态、纯逻辑、可独立测试 |
| Repository | 数据访问层，封装 ORM 细节 |
| SimHash | 用于计算文本相似度的局部敏感哈希算法 |
| Breaking | 突发新闻，需立即推送 |
| Premarket | 盘前，A 股开盘前的时间窗口 |
| 节流 (Rate limiting) | 控制单位时间内消息发送次数 |
| 降级链 | 主路径失败时按预定顺序切换到备用方案 |
| Prompt Cache | LLM 调用时复用相同前缀输入，减少计费的机制 |

## 附录 B：参考资料

- Anthropic SDK: <https://docs.anthropic.com/en/api/client-sdks>
- akshare 文档: <https://akshare.akfamily.xyz/>
- 企业微信群机器人: <https://developer.work.weixin.qq.com/document/path/91770>
- APScheduler: <https://apscheduler.readthedocs.io/>
- SQLModel: <https://sqlmodel.tiangolo.com/>
- uv: <https://docs.astral.sh/uv/>

---

**文档结束**
