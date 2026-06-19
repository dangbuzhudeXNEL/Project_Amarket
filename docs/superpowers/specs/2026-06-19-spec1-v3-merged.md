# Spec #1 v3 — A 股实时新闻分析与行情看板（小组联合版）

| 元数据 | 值 |
|--------|----|
| 文档版本 | **v3.0** |
| 创建日期 | 2026-06-19 |
| 上一版本 | [v2.0 — 基础设施 + 新闻引擎](2026-06-14-news-engine-design.md)（个人项目时期，仍是 Phase 2 来源） |
| 作者 | Project_Amarket 小组 + Claude（AI 协作伙伴） |
| 状态 | **待小组审阅** |
| 上游来源 | `Peersession/a_share_realtime_news_dashboard_prd.md` (v1.0, 2026-06-17) + `Peersession/a_share_quant_project_timeline.docx` |
| 项目性质 | **小组联合项目**（多人协作，仓库 `dangbuzhudeXNEL/Project_Amarket`） |
| 本 Spec 范围 | **Phase 1**：三大模块（新闻 / 交易看板 / 参数配置）/ **Phase 2**：原 v2 内容（盘前推送 / Brainmaster AI / 信号交易） |
| 整体定位 | A 股中低频量化交易**辅助**平台 — 永远不做实盘下单 |

---

## 0. 文档导航

- [1. 背景与目标](#1-背景与目标)
- [2. 范围与非目标](#2-范围与非目标)
- [3. 关键决策汇总](#3-关键决策汇总)
- [4. 用户与场景](#4-用户与场景)
- [5. 系统架构](#5-系统架构)
- [6. 模块详细设计](#6-模块详细设计)
- [7. 数据模型](#7-数据模型)
- [8. 新闻分类与评分体系](#8-新闻分类与评分体系)
- [9. 关键工作流](#9-关键工作流)
- [10. 看板与 API 设计](#10-看板与-api-设计)
- [11. 参数配置模块](#11-参数配置模块)
- [12. 配置与密钥管理](#12-配置与密钥管理)
- [13. 错误处理与可观察性](#13-错误处理与可观察性)
- [14. 测试策略](#14-测试策略)
- [15. 项目结构](#15-项目结构)
- [16. 依赖清单](#16-依赖清单)
- [17. 实施里程碑](#17-实施里程碑)
- [18. 安全与合规](#18-安全与合规)
- [19. 未来扩展点](#19-未来扩展点)
- [20. 多 Session 开发 + 小组协作](#20-多-session-开发--小组协作)
- [21. 待小组确认事项](#21-待小组确认事项)
- [附录 A：术语表](#附录-a术语表)
- [附录 B：参考资料](#附录-b参考资料)
- [附录 C：v2 → v3 章节映射](#附录-cv2--v3-章节映射)

---

## 1. 背景与目标

### 1.1 产品愿景

构建一个面向**二级市场分析师与交易团队**的 A 股新闻分析与行情看板平台。

新闻不是孤立阅读对象，而是行情变化的解释变量和交易情绪的触发器。系统要解决三个问题：

1. **今天发生了什么重要新闻？**
2. **这些新闻可能影响哪些指数、板块、个股或风格？**
3. **当前行情变化是被新闻驱动，还是技术面 / 资金面 / 情绪面推动？**

系统从实时新闻、指数行情、板块表现、个股异动、海外市场和宏观事件中提取**交易相关信号**，形成日报、盘中提醒和前端看板。

### 1.2 项目交付边界

| 项 | 决策 |
|----|------|
| 交付目标 | 完整 PRD、系统架构、UML / 流程图、前端 POC、可运行 MVP（Phase 1）+ 后续 Phase 2 增强 |
| **明确不做** | ① 自动实盘下单；② 生产级交易系统；③ 公开策略核心细节；④ 多用户付费 SaaS；⑤ 移动 App |
| 风险态度 | 范围可控、模块清晰、架构可信、展示直观；宁可少做不可做错 |

### 1.3 Phase 1 / Phase 2 划分

本 Spec 把工作拆成两个 Phase 串行交付：

| Phase | 范围 | 来源文档 | 备注 |
|-------|------|---------|------|
| **Phase 1** | 三大模块（**新闻模块** + **交易看板模块** + **参数配置模块**）+ 6 时段日报 + P0-P3 告警 + 看板 API | `Peersession/*` PRD + Timeline | 小组联合主线 |
| **Phase 2** | 原 v2 内容：Brainmaster AI 集成、Claude Code agent、盘前推送、信号交易（仍不实盘） | `2026-06-14-news-engine-design.md` v2 | 个人项目时期工件，不抛弃 |

Phase 1 与 Phase 2 的交集复用一套基础设施（DB、配置、调度、日志、可观察性、UI 框架、CLI），不重复造轮子。Phase 2 启动时间不设硬约束。

### 1.4 成功标准

#### 1.4.1 功能性（Phase 1 完成时）

- 至少 **3 个新闻源**（同花顺 / 东方财富 / 雅虎财经）持续抓取，覆盖率 ≥ 90% breaking
- **6 个固定时点**自动生成日报（盘前 / 早盘 / 午间 / 尾盘 / 收盘 / 晚间）
- **P0-P3 四级告警**正确分流，P0 黑天鹅推送平均延迟 < 2 分钟
- 看板 API 全部就绪，POC 前端能 5 分钟内演示完三大模块价值
- 参数配置支持版本化、回滚、权限矩阵、审计日志

#### 1.4.2 工程性

- 单元测试覆盖率 ≥ 70%
- 关键路径有集成测试 / E2E 测试
- 7×24 小时连续运行不宕机，单点故障可自愈
- Streamlit / 静态 HTML 看板能查询新闻历史、推送日志、健康状态、可调阈值
- 小组多人协作流程顺畅（PR review 平均 24h 内闭环）

---

## 2. 范围与非目标

### 2.1 Phase 1 In Scope（小组联合主线，本 Spec 主要内容）

| 类别 | 项 |
|------|------|
| **基础设施**（贯穿 Phase 1+2） | 配置加载、密钥管理、日志、调度、Metrics、健康检查、SQLite + Alembic 迁移、Streamlit UI 框架、FastAPI 后端、CLI |
| **新闻采集** | 同花顺 / 东方财富 7x24 / 雅虎财经 / 交易所公告 / 央行 + 证监会 + 财政部官网；备用源 财联社 / 证券时报 / Reuters / CNBC |
| **新闻去重** | URL 去重、标题精确去重、标题相似度去重（SimHash）、同事件多源聚合（events 表） |
| **新闻分类与评分** | 8 个一级分类 + 14+ 二级标签；重要性 1-5 / 紧急度 1-5 / 置信度 1-5；情绪 6 级；影响板块 / 相关标的 / 操作提示 / 影响时长 |
| **AI 分析模块** | 对每条新闻生成结构化分析（影响板块、相关标的、情绪方向、操作提示、风险提示）。**Phase 1 用规则 + Tier 2 LLM SDK 简化版**；Phase 2 接 Brainmaster |
| **行情数据基座**（轻量版） | A 股指数 / 个股 / 板块行情接入（akshare/efinance），每日级别快照；高频实时行情留 Phase 2 之后 |
| **板块趋势** | 板块涨跌 / 新闻热度 / 情绪分 / 资金状态 / 代表个股 / 趋势判断 |
| **6 时段日报生成** | 盘前 / 早盘 / 午间 / 尾盘 / 收盘 / 晚间，模板化输出（Markdown + JSON 双份） |
| **P0-P3 告警与推送** | 黑天鹅强提醒 → 即时推 → 汇总推 → 仅入库；推送渠道企业微信（主） + 飞书（备用） + 邮件 |
| **看板 API** | `/api/news` / `/api/dashboard` / `/api/reports` / `/api/config` 完整 REST API |
| **前端 POC** | 静态或半静态 HTML 页面（pure HTML + 少量 JS，能跑数据但不要求完美交互） |
| **参数配置模块** | 参数类型、权限矩阵、版本号、回滚机制、审计、脱敏展示 |
| **测试** | 单元、集成、E2E |
| **部署** | 本地 Windows 开发机直接 `uv run` 启动；提供 `start.bat` 一键启动 |
| **小组协作基础设施** | CONTRIBUTING.md、分支策略、PR 模板、CODEOWNERS、CI（GitHub Actions） |

### 2.2 Phase 2 In Scope（沿用 v2 内容）

| 类别 | 项 |
|------|------|
| **Brainmaster AI 集成** | `.claude/agents/news-analyst.md`、`ClaudeAgentRunner`、subprocess 调用 + 输出文件校验 |
| **盘前 08:30 单次集中推送** | 已设计的 v2 工作流（与 Phase 1 6 时段日报兼容并存） |
| **Breaking news 实时推送**（增强版） | 在 Phase 1 P0-P3 之上，引入纯规则的低延迟通道（< 60s） |
| **AI Prompt Cache** | LLMProvider 统一 cache 层 |
| **信号交易准备**（**永不下单**） | BrokerAdapter 接口、SignalOnly / Paper 实现；为 Spec #3 做铺垫 |
| **回测引擎接口准备** | 留给 Spec #2 |

### 2.3 Out of Scope（明确不在本 Spec 任何 Phase）

- ❌ **自动实盘下单**（无论何时、何 Phase 都不做）
- ❌ 历史 K 线 / 财务数据 / 完整资金面（Spec #2）
- ❌ 完整回测引擎（Spec #2）
- ❌ AI 选股策略（Spec #3）
- ❌ 资产配置 / 组合优化 / 波动告警（Spec #4）
- ❌ AI Feedback / 策略复盘（Spec #4）
- ❌ 多用户付费 / SaaS / 收费策略
- ❌ 移动端 App（推送通过企微 / 飞书即可触达手机）
- ❌ 公网部署 / Docker / Kubernetes（MVP 本地常驻 + 内网即可）

### 2.4 显式 YAGNI（暂不做的诱惑）

- 消息队列（Redis/Kafka）：APScheduler in-process 完全够
- 微服务拆分：单体应用 + 清晰模块边界即可
- React 前端：Streamlit + 静态 HTML POC 起步
- 用户认证 / RBAC：MVP 单角色单租户，预留 `user_id` 字段
- 全量 AI 增强：MVP 部分新闻才过 AI（按规则筛选）
- 自动交易接入：BrokerAdapter 永远只到信号 / 模拟两层

---

## 3. 关键决策汇总

### 3.1 产品决策

| # | 决策维度 | 决策值 | 理由 |
|---|---------|--------|------|
| 1 | **项目性质** | 小组联合开发，仓库共有 | 课程作业基础上发展为长期实用项目 |
| 2 | **业务范围** | A 股新闻分析 + 行情看板 + 6 时段日报 | 来自 Peersession PRD |
| 3 | **不做实盘** | 永远只做信号 + 模拟，BrokerAdapter 仅到 SignalOnly/Paper 两层 | 合规风险、个人无券商接入资质 |
| 4 | **推送等级** | P0-P3 四级（黑天鹅 / 重要 / 普通 / 仅入库） | PRD §7.6 |
| 5 | **日报频次** | 6 时段（08:00 / 09:25 / 11:30 / 14:30 / 15:15 / 20:00） | PRD §3.1 |
| 6 | **新闻评分维度** | 重要性 / 紧急度 / 置信度 各 1-5；情绪 6 级 | PRD §6 |

### 3.2 技术决策

| # | 决策维度 | 决策值 | 理由 |
|---|---------|--------|------|
| 7 | **运行环境** | 本地 Windows 开发机常驻 (`C:\AI\Claude\Project_Amarket`) | 隐私好、成本 0、调试方便 |
| 8 | **主语言** | Python 3.11+ | 量化生态最强 |
| 9 | **HTTP 客户端** | `httpx`（async） | HTTP/2、原生 async |
| 10 | **持久化** | SQLite + SQLModel + Alembic | 零运维；ORM 切 PG 0 改动 |
| 11 | **调度** | APScheduler in-process | MVP 不需要分布式队列 |
| 12 | **依赖管理** | `uv` (Astral) | 比 pip/poetry 快 10-100x |
| 13 | **后端框架** | FastAPI | async 友好、OpenAPI 自动生成、看板 API 直接走它 |
| 14 | **前端 POC** | 静态 HTML（Phase 1 M3）+ Streamlit 管理面板（Phase 1 M5） | 时间紧时静态优先；Streamlit 用于运维 |
| 15 | **新闻源策略**（Phase 1） | 同花顺 + 东方财富 7x24 + 雅虎财经 + 交易所公告 + 央行/证监会/财政部 | PRD §4.1，覆盖最高优先级 |
| 16 | **行情源策略**（Phase 1 轻量） | akshare / efinance / yfinance；只接日线快照 + 主要指数实时 | 高频实时留后续 Spec |
| 17 | **AI 分析模式（Phase 1）** | 规则引擎为主 + Tier 2 LLM SDK（OpenAI 协议）调用 DeepSeek / Anthropic 走 API | 简化、可量化输出、便于测试 |
| 18 | **AI 分析模式（Phase 2）** | **Brainmaster 模式** — Python 通过 subprocess 调 `claude` CLI，agent 在 `.claude/agents/*.md`，输出 JSON 文件。零 API 成本 | 与隔壁 Brainmaster 项目对齐，复用 Claude Code 订阅 |
| 19 | **推送渠道（Phase 1）** | 企业微信群机器人（主） + 飞书机器人（备） + 邮件（P0 备用） | PRD §7.6 |
| 20 | **日志** | `structlog` JSON | 结构化、可后接 ELK/Loki |
| 21 | **指标** | Prometheus 格式 `/metrics` | 标准生态 |
| 22 | **节假日** | `chinese-calendar` Python 库 + akshare 备选 | 标准生态 |

### 3.3 协作决策

| # | 决策维度 | 决策值 | 理由 |
|---|---------|--------|------|
| 23 | **仓库** | `dangbuzhudeXNEL/Project_Amarket` (Public) | 已建好；Phase 1 升格为小组仓库 |
| 24 | **分支策略** | `main`（受保护，需 PR）+ `feat/<member>-<topic>` 个人分支 | 详见 §20.3.2 |
| 25 | **PR 流程** | 至少 1 人 review；CI 通过；不允许直接 push main | 详见 §20.3.3 |
| 26 | **代码标准** | type hints 必加、structlog、密钥不入库、commit 格式 `<type>(<scope>): <subject>` | 沿用 v2 |
| 27 | **多 Session 开发** | CLAUDE.md + PROJECT_STATE.md + sessions/ + CHANGELOG.md 四件套 | 沿用 v2 §16 |
| 28 | **Spec 优先级** | 完整完成 Phase 1 (M0-M6) 再开 Phase 2 brainstorming | 串行降低复杂度 |

---

## 4. 用户与场景

### 4.1 用户角色

| 角色 | 描述 | Phase 1 权限 |
|------|------|-------------|
| **分析师** | 关心新闻、行情归因、撰写日报；高频读 | 看新闻 / 看板 / 日报；编辑参数（部分） |
| **交易员** | 关心 P0/P1 告警、板块强弱、操作提示 | 看新闻 / 告警 / 板块趋势 / 个股异动 |
| **项目管理员** | 配置数据源、推送渠道、阈值；查日志 | 全部参数 + 系统配置 + 审计日志 |
| **来宾**（预留） | 仅看公开看板，不看告警与参数 | 限制查看范围 |

### 4.2 核心场景

#### 场景 A：盘前判断当日主线（08:00-08:45）
分析师打开看板 → 看顶部市场状态栏（隔夜美股、大宗商品）→ 看盘前日报（政策面 / 公司面 / 行业面）→ 看高优先级 P1 告警 → 决定关注哪些板块。

#### 场景 B：盘中突发告警（任意时段）
交易员收到企微推送（P0 黑天鹅 / P1 重要新闻）→ 看板"突发告警区"自动顶部置顶 → 跳转新闻详情查看 AI 分析（影响板块 / 相关标的 / 操作提示）→ 决策。

#### 场景 C：尾盘资金归因（14:30-15:00）
分析师看尾盘日报 → 看板块趋势看板（哪些板块放量、新闻热度高）→ 看个股异动榜（拉升 / 跳水原因）→ 整理为复盘笔记。

#### 场景 D：参数调优（任意时段）
项目管理员发现 P0 误报率高 → 进参数配置页 → 调"突发关键词权重"→ 保存为新版本 → 观察 24h 效果 → 不行就一键回滚。

### 4.3 用户流程图（高层）

```
分析师/交易员
   │
   │ ① 打开看板
   ▼
┌──────────────────────────────────────┐
│  顶部：市场状态栏（指数/汇率/商品）  │
├──────────────────────────────────────┤
│  实时新闻流 (筛选: 来源/分类/情绪)  │
│  ┌──────┐  ┌──────┐  ┌──────────┐  │
│  │ 突发 │  │ 板块 │  │ 个股异动 │  │
│  │ 告警 │  │ 趋势 │  │   榜     │  │
│  └──────┘  └──────┘  └──────────┘  │
├──────────────────────────────────────┤
│  日报入口 (盘前/午间/收盘/...)      │
└──────────────┬───────────────────────┘
               │ ② 点击新闻
               ▼
        新闻详情页
        (AI 分析 / 影响板块 / 相关标的)
               │
               │ ③ 点击告警
               ▼
        告警详情 + 历史相似事件
```

---

## 5. 系统架构

### 5.1 分层架构图

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            Project_Amarket (单体进程)                          │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ 静态 POC     │  │ Streamlit    │  │ CLI (Typer)  │  │  APScheduler   │ │
│  │ HTML 看板    │  │ 管理面板      │  │ 人工触发/调试 │  │  cron 任务     │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └────────┬───────┘ │
│         └─────────────────┴─────────────────┴────────────────────┘          │
│                                  ↓                                          │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │               ⚡ FastAPI HTTP Server (REST API)                     │    │
│  │   /api/news     /api/dashboard    /api/reports                     │    │
│  │   /api/config   /api/alerts       /api/params                      │    │
│  │   /healthz      /metrics                                           │    │
│  └────────────────────────────┬────────────────────────────────────────┘    │
│                                ↓                                            │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │     🧠 Service Layer（纯 Python，可单元测试）                        │    │
│  │                                                                    │    │
│  │  ╔═══ 新闻模块 ════╗  ╔═══ 看板模块 ═══╗  ╔═ 参数配置模块 ═╗      │    │
│  │  ║ NewsCollector ║  ║ DashboardSvc  ║  ║ ParamConfigSvc ║      │    │
│  │  ║ NewsClassifier║  ║ SectorTrendSvc║  ║ AuditService   ║      │    │
│  │  ║ NewsAnalysis  ║  ║ AlertService  ║  ║                ║      │    │
│  │  ║ NewsDeduper   ║  ║ ReportService ║  ║                ║      │    │
│  │  ║ NewsPusher    ║  ║               ║  ║                ║      │    │
│  │  ╚═══════════════╝  ╚═══════════════╝  ╚════════════════╝      │    │
│  │                                                                    │    │
│  │  ┌─ 公共服务 ─────────────────────────────────────────────────┐  │    │
│  │  │ MarketDataService │ AIService │ ConfigService            │  │    │
│  │  │ SchedulerService  │ ObservabilityService                  │  │    │
│  │  └────────────────────────────────────────────────────────────┘  │    │
│  └─────────────┬─────────────────────────────────────┬──────────────┘    │
│                ↓                                      ↓                    │
│  ┌──────────────────────────┐         ┌────────────────────────────────┐ │
│  │ 📦 Repository Layer       │         │ 🔌 Adapter Layer                │ │
│  │ news / events / analysis  │         │ NewsSource(5+):                 │ │
│  │ market / sector / alert   │         │   THS / Eastmoney / Yahoo /     │ │
│  │ report / push / source    │         │   Exchange / Government         │ │
│  │ param / audit / config    │         │ MarketDataSource:               │ │
│  │ (SQLModel ORM)            │         │   akshare / efinance / yfinance │ │
│  └─────────┬─────────────────┘         │ AIProvider:                     │ │
│            ↓                            │   ClaudeAgent (Phase 2 主)      │ │
│  ┌──────────────────────────┐          │   AnthropicSDK / DeepSeekSDK    │ │
│  │ 💾 SQLite (本地文件)      │          │ Notifier:                       │ │
│  └──────────────────────────┘          │   WeWork / Lark / Email         │ │
│                                         └────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 三大模块边界

| 模块 | 职责 | 关键服务 | 关键 API 前缀 |
|------|------|---------|--------------|
| **新闻模块** | 采集 / 去重 / 分类 / 评分 / 分析 / 推送 | `NewsCollector`、`NewsClassifier`、`NewsAnalysis`、`NewsPusher` | `/api/news/*` |
| **交易看板模块** | 行情快照、板块趋势、新闻流呈现、告警分发、日报生成 | `DashboardService`、`SectorTrendService`、`AlertService`、`ReportService` | `/api/dashboard/*`、`/api/reports/*`、`/api/alerts/*` |
| **参数配置模块** | 参数版本化、权限矩阵、审计日志、脱敏展示 | `ParamConfigService`、`AuditService` | `/api/params/*`、`/api/config/*` |

模块边界靠 **Service 层方法签名** 划定，Repository 可跨模块共用（DB 是统一 schema）。

### 5.3 进程模型

MVP 阶段所有组件**跑在同一个 Python 进程**：

```
python -m amarket  →  启动一个进程，内含：
├── FastAPI/uvicorn (端口 8080)         # REST API + 健康检查 + metrics
├── APScheduler                          # 在 FastAPI 启动钩子中起
└── Streamlit 单独进程 (端口 8501)       # 通过 start.bat 同时拉起
└── 静态 HTML POC                        # 直接 file:// 打开或 python -m http.server
```

后期可拆分为：API 进程 + Worker 进程 + UI 进程，但 MVP 不必。

### 5.4 核心架构原则

1. **依赖倒置**：Service 层依赖 Adapter 接口（`NewsSource`、`MarketDataSource`、`AIProvider`、`Notifier`），不直接依赖实现
2. **单一入口配置**：所有可调参数走 `config/*.yml` + `.env`，**禁止硬编码**
3. **结构化日志**：`structlog` 输出 JSON，便于后续接入聚合系统
4. **故障隔离**：任一新闻源 / AI / 推送渠道故障不影响整体（断路器 + 降级链）
5. **多租户数据模型**：所有业务表带 `user_id`（MVP 单值，扩展不破坏）
6. **可测试性优先**：每个 service 30s 内单元测试通过，无需启动 DB（依赖注入）
7. **可观察性内建**：Prometheus metrics + 健康检查 + 结构化日志，从 day 1 就有
8. **AI 不可幻觉**：所有 AI 输出必须有原文链接溯源、置信度评分、降级路径

---

## 6. 模块详细设计

### 6.1 Service 层模块（按三大模块分组）

#### 新闻模块

##### 6.1.1 `NewsCollector`（新闻采集服务）
- **职责**：调度各 `NewsSource` 拉取新闻、标准化、写入 `news_items` 表
- **关键方法**：
  - `collect_since(since: datetime) -> List[NewsItem]`：日报用，拉过去 N 小时
  - `poll_realtime() -> List[NewsItem]`：实时轮询，频率按 §3.1 PRD 表
- **依赖**：`NewsSource[]`、`NewsRepo`、`SourceHealthRepo`、`ObservabilityService`
- **故障处理**：单源失败不影响其他源；连续 3 次失败 → `source_health` 标记 + 告警
- **频率**（PRD §7.2，按时段分级）：
  - 08:00-09:30：1 分钟一次
  - 09:30-11:30：1-3 分钟一次
  - 11:30-13:00：3-5 分钟一次
  - 13:00-15:00：1-3 分钟一次
  - 15:00-16:30：3-5 分钟一次
  - 夜间：5-15 分钟一次

##### 6.1.2 `NewsDeduper`（新闻去重服务）
- **职责**：URL / 标题 / SimHash 三层去重；同事件多源聚合到 `news_events`
- **关键方法**：
  - `dedupe_batch(items: List[NewsItem]) -> DedupeResult`
  - `find_event_for(item: NewsItem) -> NewsEvent | None`
  - `merge_into_event(item, event)`
- **去重逻辑**（PRD §7.3）：
  1. URL 完全相同 → 同条
  2. 标题完全相同（normalize 后）→ 同条
  3. SimHash 距离 < 阈值（默认 3）→ 同事件，并入 `news_events`
  4. 同事件多源新闻在事件里追加时间线

##### 6.1.3 `NewsClassifier`（新闻分类服务）
- **职责**：一级分类（8 类）+ 二级标签（14+）+ 影响板块 + 相关标的（规则引擎）
- **关键方法**：
  - `classify(item: NewsItem) -> NewsClassification`
- **依赖**：规则文件（`config/classification.yml`）、`SubscriptionRepo`、`SectorMappingRepo`
- **算法**：
  1. 关键词匹配（最长匹配优先）→ 一级分类
  2. 板块词库（PRD §5.2 14+ 二级标签）→ 二级标签
  3. 个股名称 / 代码扫描 → 相关标的

##### 6.1.4 `NewsAnalysis`（AI 分析服务）
- **职责**：对新闻生成 AI 分析（影响板块 / 相关标的 / 情绪 / 重要性 / 紧急度 / 操作提示 / 风险提示 / 影响时长）
- **关键方法**：
  - `analyze(item: NewsItem, classification: NewsClassification) -> NewsAnalysis`
  - `analyze_batch(items, *, mode='sync'|'async') -> List[NewsAnalysis]`
- **Phase 1 实现**：
  - 走 `AIProvider`（Tier 2 LLM SDK：DeepSeek / Anthropic 走 API）
  - 输入：标题 + 摘要 + 来源 + 时间 + 一级 / 二级标签 + 近 24h 同类新闻 top 3
  - 输出 schema 见 §8.3
  - 限制：单次调用 timeout 30s；批量并发 max 5；失败降级到规则引擎打分
- **Phase 2 增强**：
  - 加入 Brainmaster 模式（详 §6.3）
  - 加入 Prompt Cache
  - 加入"逐条新闻 vs 批量 AI"两条路径，根据 importance / urgency 选

##### 6.1.5 `NewsPusher`（推送服务）
- **职责**：渲染模板、按 P0-P3 路由、节流、失败重试、写日志
- **关键方法**：
  - `push_alert(item, level: AlertLevel) -> PushRecord`：P0/P1 单条告警
  - `push_batch(batch_id) -> List[PushRecord]`：P2 汇总推送
  - `push_report(report_id, channels)`：日报推送
- **依赖**：`Notifier[]`、`PushRepo`、`ConfigService`、`ParamConfigService`（取阈值）
- **节流**：
  - 全局 P0 无上限；P1 max 6/h；P2 汇总 1/30min；P3 不推
  - 用户级（订阅相关）无上限
- **重试**：3 次指数退避（1s/2s/4s）；最终失败切换备用渠道；再失败告警
- **路由表**（PRD §7.6）：
  | 等级 | 渠道 | 动作 |
  |------|------|------|
  | P0 | 企微 + 飞书 + 邮件 | 即时强提醒，全渠道并发 |
  | P1 | 企微 + 飞书 | 即时推送 |
  | P2 | 企微 | 汇总推送（每 30min） |
  | P3 | 不推送 | 仅入库 + 看板展示 |

#### 交易看板模块

##### 6.1.6 `MarketDataService`（行情数据服务）
- **职责**：管理行情源、缓存最新快照、计算指数 / 板块 / 个股的当前涨跌
- **关键方法**：
  - `get_index_snapshot(codes: List[str]) -> List[IndexSnapshot]`
  - `get_sector_snapshot(names: List[str]) -> List[SectorSnapshot]`
  - `get_stock_snapshot(codes: List[str]) -> List[StockSnapshot]`
  - `refresh_snapshots()`：被调度器周期调用
- **Phase 1 范围**：日线快照 + 主要指数（上证 / 深证 / 创业板 / 科创 50 / 北证 50 / 恒科 / 纳指）；个股按需查询，不全量缓存
- **依赖**：`MarketDataSource`（akshare / efinance / yfinance adapter）

##### 6.1.7 `SectorTrendService`（板块趋势服务）
- **职责**：综合行情 + 新闻热度 + 情绪分 + 资金状态计算板块趋势判断
- **关键方法**：
  - `compute_sector_trend(sector: str, window: timedelta) -> SectorTrend`
  - `top_n_sectors(by: 'rise'|'fall'|'news_heat', n: int) -> List[SectorTrend]`
- **算法**：
  - 综合涨跌幅、相关新闻数 + 情绪分 + 重要性加权
  - 趋势判断：延续 / 分歧 / 退潮 / 反转（基于近 N 天的板块涨跌 + 新闻热度变化）

##### 6.1.8 `AlertService`（告警服务）
- **职责**：根据评分把新闻分配到 P0-P3，写入 `alerts` 表，触发 `NewsPusher`
- **关键方法**：
  - `evaluate(news_id: int, analysis: NewsAnalysis) -> AlertLevel`
  - `dispatch(alert: Alert)`
- **算法**：
  ```
  if importance >= 5 AND urgency >= 5 AND category in (黑天鹅 / 战争 / 重大政策 / 制裁):
      level = P0
  elif (importance >= 4 AND urgency >= 4) OR 命中用户订阅:
      level = P1
  elif importance >= 3:
      level = P2
  else:
      level = P3
  ```

##### 6.1.9 `ReportService`（日报生成服务）
- **职责**：在固定时点把过去时段的新闻 + 行情聚合为日报
- **关键方法**：
  - `generate(kind: 'premarket'|'morning'|'noon'|'afternoon'|'close'|'evening', date: date) -> Report`
  - `render(report: Report, format: 'markdown'|'json'|'html') -> str`
- **依赖**：`NewsRepo`、`MarketDataService`、`SectorTrendService`、`AIProvider`（Phase 2 走 Brainmaster `daily-report-writer` agent）
- **6 时段（PRD §3.1）**：

  | 时段 | 时间 | 核心目的 | 输出内容 |
  |------|------|---------|---------|
  | 盘前 | 08:00-08:45 | 判断开盘情绪和当日主线 | 隔夜海外 / 政策 / 公告 / 风险事件 / 今日关注板块 |
  | 早盘跟踪 | 09:25-10:15 | 捕捉开盘异动和新闻验证 | 高低开原因 / 板块强弱 / 首批异动个股 |
  | 午间 | 11:30-12:20 | 上午行情归因 | 上午复盘 / 午后关注 / 资金流 / 板块轮动 |
  | 尾盘 | 14:30-15:00 | 尾盘资金 + 隔夜风险 | 尾盘拉升/跳水 / 资金抢筹或避险 |
  | 收盘后 | 15:15-16:30 | 全天复盘 | 全天复盘 / 新闻归因 / 明日关注 / 策略提示 |
  | 晚间 | 20:00-22:30 | 公告 + 海外开盘 | 重要公告 / 海外风险 / 美股开盘影响 |

##### 6.1.10 `DashboardService`（看板编排服务）
- **职责**：聚合多个 service 数据，给前端单次返回完整看板状态
- **关键方法**：
  - `get_summary() -> DashboardSummary`：首页用
  - `get_news_stream(filter: NewsFilter) -> List[NewsCardDTO]`
  - `get_market_status() -> MarketStatusBar`

#### 参数配置模块

##### 6.1.11 `ParamConfigService`（参数配置服务）
- **职责**：参数管理、版本化、回滚、权限控制
- **关键方法**：
  - `get(key: str, *, mask_secret=False) -> ParamValue`
  - `set(key: str, value: Any, user: User, reason: str) -> ParamVersion`
  - `rollback(key: str, to_version: int, user: User)`
  - `list_versions(key: str) -> List[ParamVersion]`
- **依赖**：`ParamRepo`、`AuditService`、`UserRepo`

##### 6.1.12 `AuditService`（审计日志服务）
- **职责**：记录敏感操作（参数变更、用户操作、推送决策）
- **关键方法**：
  - `log(event: AuditEvent)`
  - `query(filter: AuditFilter) -> List[AuditEvent]`
- **依赖**：`AuditRepo`

#### 公共服务

##### 6.1.13 `AIService`（AI 编排服务，跨 Phase）
- **Phase 1**：通过 `AIProvider` 接口调 LLM SDK（Anthropic / DeepSeek 走 API）
- **Phase 2**：默认走 `ClaudeAgentRunner`（Brainmaster 模式 — subprocess + 文件输出）；保留 SDK 作为 fallback

##### 6.1.14 `ConfigService`（配置服务）
- **职责**：加载 YAML 配置、热重载、密钥脱敏
- 沿用 v2 §5.1.5

##### 6.1.15 `SchedulerService`（调度服务）
- **职责**：cron 任务、节假日判断、6 时段日报触发
- 沿用 v2 §5.1.6 + 扩展任务清单：

  | 任务 | 触发 | 备注 |
  |------|------|------|
  | `news_realtime_poll` | 按时段动态频率（§6.1.1） | 全周 7×24 |
  | `report_generate_premarket` | 工作日 07:55 | 触发盘前日报，08:00 推送 |
  | `report_generate_morning` | 工作日 09:25 | |
  | `report_generate_noon` | 工作日 11:32 | |
  | `report_generate_afternoon` | 工作日 14:30 | |
  | `report_generate_close` | 工作日 15:15 | |
  | `report_generate_evening` | 每日 20:00 | 周末仍跑（捕捉海外） |
  | `market_snapshot_refresh` | 每 5 分钟（交易时段）/ 每 30 分钟（其他） | |
  | `sector_trend_refresh` | 每 15 分钟 | |
  | `health_self_check` | 每 5 分钟 | |
  | `weekend_archive_poll` | 非交易日每 30 分钟 | 仅入库不推送 |

##### 6.1.16 `ObservabilityService`（可观察性服务）
- 沿用 v2 §5.1.7

### 6.2 Adapter 层模块

#### 6.2.1 `NewsSource` 接口

```python
class NewsSource(Protocol):
    code: str           # 'ths' / 'eastmoney' / 'yahoo' / 'exchange_sse' / 'gov_pbc' / ...
    name: str
    priority: Literal['highest', 'high', 'medium', 'low']

    async def fetch_since(self, since: datetime) -> List[RawNewsItem]: ...
    async def fetch_realtime(self) -> List[RawNewsItem]: ...
    def health_check(self) -> SourceHealth: ...
```

Phase 1 实现：
- `ThsNewsSource`（同花顺）
- `EastmoneyNewsSource`（东方财富 7x24）
- `YahooFinanceNewsSource`（雅虎财经）
- `ExchangeSseSource` / `ExchangeSzseSource` / `ExchangeBseSource`（交易所公告）
- `GovPbcSource` / `GovCsrcSource` / `GovMofSource`（央行 / 证监会 / 财政部）

接入方式：M1 实施时按源做抓包确认，每个 adapter 必须有 `tests/fixtures/<source>_sample.{html,json}` 用于回归测试。

⚠️ **合规**：
- 所有抓取设置合理 User-Agent
- 控制频率（< 1 req/s/source）
- 遵守 robots.txt
- 失败 3 次自动暂停 30 分钟

#### 6.2.2 `MarketDataSource` 接口

```python
class MarketDataSource(Protocol):
    code: str           # 'akshare' / 'efinance' / 'yfinance'

    async def get_index(self, code: str) -> IndexSnapshot: ...
    async def get_stock(self, code: str) -> StockSnapshot: ...
    async def get_sector(self, name: str) -> SectorSnapshot: ...
    async def get_index_daily(self, code: str, days: int) -> List[DailyBar]: ...
```

Phase 1 实现：
- `AkshareSource`（A 股）
- `EfinanceSource`（A 股备用）
- `YfinanceSource`（美股 / 港股 / 日韩）

#### 6.2.3 `AIProvider` 接口

Phase 1 用 SDK 调用，Phase 2 用 `ClaudeAgentRunner`，统一接口：

```python
class AIProvider(Protocol):
    code: str           # 'claude_agent' / 'anthropic_sdk' / 'deepseek_sdk'

    async def analyze_news(
        self,
        item: NewsItem,
        classification: NewsClassification,
        context: List[NewsItem],
    ) -> NewsAnalysisResult: ...

    async def generate_report(
        self,
        kind: ReportKind,
        items: List[NewsItem],
        market_data: MarketStatusBar,
    ) -> ReportResult: ...
```

##### 6.2.3.1 `ClaudeAgentRunner`（Phase 2 主路径）

沿用 v2 §5.2.2，封装 subprocess + 输出校验。

```python
class ClaudeAgentRunner:
    def __init__(self, cli_path: str = "claude", default_timeout: int = 600):
        import shutil
        self._cli = shutil.which(cli_path) or cli_path
        self._default_timeout = default_timeout

    def run(
        self,
        agent_name: str,
        prompt: str,
        expected_output: Path,
        timeout: int | None = None,
        cwd: Path | None = None,
    ) -> AgentRunResult:
        """status ∈ {completed, degraded, timeout, error}"""
        ...
```

##### 6.2.3.2 `AnthropicSDKProvider`（Phase 1 + Tier 2 Fallback）
##### 6.2.3.3 `DeepSeekSDKProvider`（Phase 1 + Tier 2 Fallback）

走 OpenAI 兼容协议；用 `ANTHROPIC_API_KEY` / `DEEPSEEK_API_KEY` 配置。

#### 6.2.4 `Notifier` 接口

```python
class Notifier(Protocol):
    code: str           # 'wework' / 'lark' / 'email' / 'telegram'

    async def send_text(self, text: str) -> NotificationResult: ...
    async def send_markdown(self, markdown: str) -> NotificationResult: ...
    async def send_card(self, card: CardSpec) -> NotificationResult: ...
    def health_check(self) -> NotifierHealth: ...
```

实现：
- `WeWorkBotNotifier`（主，Phase 1）
- `LarkBotNotifier`（飞书，Phase 1 备用）
- `EmailNotifier`（P0 备用，Phase 1）
- `TelegramBotNotifier`（Phase 2 stub）

### 6.3 Claude Code Agents（Phase 2 工作负载定义）

按 Brainmaster 模式，所有 AI 工作负载放在 `.claude/agents/*.md`，由 `ClaudeAgentRunner` 通过 subprocess 触发。

#### 6.3.1 Phase 2 需要的 Agents

| Agent 名称 | 触发场景 | 输入 | 输出（强制路径） | 默认 model | maxTurns |
|-----------|---------|------|---------------|----------|----------|
| `news-analyst` | 盘前日报 / 6 时段日报兜底 | `data/news/raw/<date>/*.json` | `data/news/summaries/<date>-<kind>.json` | sonnet | 30 |
| `news-classifier-realtime`（新增） | 高优新闻深度分析 | 单条新闻 JSON | `data/news/processed/<news_id>.json` | sonnet | 5 |
| `daily-report-writer`（新增） | 6 时段日报增强模式 | `data/news/raw/<date>/*.json` + `data/market/<date>.json` | `data/reports/<date>-<kind>.json` | opus | 50 |

`news-analyst` 已经在 v2 完整设计（见 `.claude/agents/news-analyst.md`），v3 保留并兼容。

#### 6.3.2 Slash Commands

| Command | 用途 | 触发方式 |
|---------|------|---------|
| `/test-premarket` | 手动触发盘前汇总（已有） | 用户 |
| `/test-report <kind>` | 手动触发任意时段日报 | 用户 |
| `/test-classify <news_id>` | 手动触发深度分类 | 用户 |

### 6.4 Repository 层模块

每个 Repo 封装一类聚合根的 CRUD + 查询：

| Repo | 主要表 | 关键方法 |
|------|-------|---------|
| `NewsRepo` | `news_items` | `save_batch` / `find_unprocessed` / `find_by_simhash_within` / `query_by_window` / `export_raw_for_date` |
| `NewsEventRepo` | `news_events` | `save` / `merge_news_into_event` / `find_by_signature` |
| `NewsAnalysisRepo` | `news_analysis` | `save` / `get_by_news_id` / `find_by_importance_gte` |
| `MarketSnapshotRepo` | `market_snapshots` | `upsert` / `get_latest` / `query_history` |
| `SectorTrendRepo` | `sector_trends` | `upsert` / `top_n` |
| `AlertRepo` | `alerts` | `save` / `find_recent` / `find_by_level` |
| `ReportRepo` | `reports` | `save` / `find_by_date_kind` / `list_recent` |
| `PushRepo` | `push_records` | `save` / `count_within_window` / `find_recent_by_user` |
| `SourceHealthRepo` | `source_health` | `upsert` / `find_unhealthy` |
| `ParamRepo` | `params` + `param_versions` | `get` / `set` / `list_versions` / `rollback` |
| `AuditRepo` | `audit_events` | `save` / `query` |
| `UserRepo` | `users` + `subscriptions` | `get_default_user` / `list_subscriptions` |
| `ConfigRepo` | `config_versions` | （仅做版本审计；运行时配置走 YAML） |

### 6.5 Domain 层

```
src/amarket/domain/
├── models.py       # SQLModel 表
├── enums.py        # SourcePriority / NewsCategory / Sentiment / AlertLevel / PushStatus / ReportKind / ImpactHorizon / ActionHint / ParamScope ...
└── schemas.py      # Pydantic 业务对象（NewsAnalysisResult / ReportContent / SectorTrendDTO / DashboardSummary / ParamValue ...）
```

---

## 7. 数据模型

### 7.1 表设计概览（11 张核心表）

| 表 | 主要目的 | 估算行数（1 年） | 来源 |
|----|---------|---------------|------|
| `users` | 用户（MVP 单行，扩展预留） | 1-N | v2 |
| `subscriptions` | 关注的股票 / 板块 / 关键词 | 10-100 | v2 |
| `news_sources` | 新闻源配置 + 运行时统计 | 5-15 | v2 |
| `source_health` | 数据源健康（每次轮询一行写入） | 100-200 万 | PRD §10 |
| `news_items` | 原始新闻 | 50-200 万 | v2 |
| `news_events` | 同事件聚合表（去重后的事件） | 10-50 万 | PRD §10 |
| `news_analysis` | AI / 规则分析结果 | 50-200 万 | PRD §10 |
| `market_snapshots` | 行情快照 | 100-500 万 | PRD §10 |
| `sector_trends` | 板块趋势 | 5-20 万 | PRD §10 |
| `alerts` | P0-P3 告警记录 | 5000-2 万 | PRD §10 |
| `reports` | 6 时段日报 | 1500-2000 | PRD §10 |
| `push_records` | 推送日志 | 5000-2 万 | v2 |
| `params` + `param_versions` | 参数配置 + 版本 | 100 + 1000 | Timeline M5 |
| `audit_events` | 审计日志 | 5000-5 万 | Timeline M5 |
| `config_versions` | 系统配置版本 | 100 | PRD §10 |

### 7.2 详细字段

#### `users`
```
id            INTEGER PRIMARY KEY
name          TEXT NOT NULL
role          TEXT NOT NULL DEFAULT 'analyst'   -- 'analyst'|'trader'|'admin'|'guest'
timezone      TEXT DEFAULT 'Asia/Shanghai'
created_at    DATETIME NOT NULL
```

#### `subscriptions`
```
id            INTEGER PRIMARY KEY
user_id       INTEGER NOT NULL REFERENCES users(id)
kind          TEXT NOT NULL CHECK (kind IN ('stock','sector','keyword','market'))
value         TEXT NOT NULL
weight        INTEGER DEFAULT 50      -- 0-100
enabled       BOOLEAN DEFAULT TRUE
created_at    DATETIME
INDEX (user_id, kind, enabled)
UNIQUE (user_id, kind, value)
```

#### `news_sources`
```
id              INTEGER PRIMARY KEY
code            TEXT UNIQUE NOT NULL
name            TEXT NOT NULL
priority        TEXT DEFAULT 'medium'           -- 'highest'|'high'|'medium'|'low'
enabled         BOOLEAN DEFAULT TRUE
last_pulled_at  DATETIME
last_error      TEXT
consecutive_failures INTEGER DEFAULT 0
config_json     JSON                           -- 各源个性化配置
```

#### `source_health`
```
id              INTEGER PRIMARY KEY
source_id       INTEGER NOT NULL REFERENCES news_sources(id)
ts              DATETIME NOT NULL
status          TEXT NOT NULL                  -- 'ok'|'degraded'|'down'
latency_ms      INTEGER
error           TEXT
items_returned  INTEGER
INDEX (source_id, ts)
```

#### `news_items`（核心表，原文）
```
id              INTEGER PRIMARY KEY
source_id       INTEGER NOT NULL REFERENCES news_sources(id)
source_msg_id   TEXT NOT NULL
event_id        INTEGER REFERENCES news_events(id)   -- nullable，去重后回填
title           TEXT NOT NULL
summary         TEXT
content         TEXT
url             TEXT
published_at    DATETIME NOT NULL
fetched_at      DATETIME NOT NULL
content_hash    TEXT                                -- SimHash 64-bit hex
raw_payload     JSON
UNIQUE (source_id, source_msg_id)
INDEX (published_at)
INDEX (content_hash)
INDEX (event_id)
```

#### `news_events`（同事件聚合）
```
id              INTEGER PRIMARY KEY
signature       TEXT NOT NULL                  -- SimHash + normalize
canonical_title TEXT NOT NULL
first_seen_at   DATETIME NOT NULL
last_seen_at    DATETIME NOT NULL
news_count      INTEGER DEFAULT 1
top_source      TEXT
INDEX (signature)
INDEX (last_seen_at)
```

#### `news_analysis`（AI / 规则结果，PRD §5.3）
```
id                  INTEGER PRIMARY KEY
news_id             INTEGER NOT NULL REFERENCES news_items(id)
event_id            INTEGER REFERENCES news_events(id)

-- 分类（PRD §5.1, §5.2）
primary_category    TEXT NOT NULL                  -- '宏观政策'|'市场行情'|'公司公告'|'海外映射'|'大宗商品'|'风险事件'|'资金流'|'交易提示'
tags                JSON                           -- ['AI算力','半导体',...]
related_markets     JSON                           -- ['A股','港股','美股','日韩','商品']
related_sectors     JSON                           -- [{name, weight}]
related_symbols     JSON                           -- [{code, name, weight}]

-- 评分（PRD §6）
sentiment           TEXT                           -- '强利多'|'利多'|'中性'|'利空'|'强利空'|'不确定'
importance_score    INTEGER                        -- 1-5
urgency_score       INTEGER                        -- 1-5
confidence_score    INTEGER                        -- 1-5
impact_horizon      TEXT                           -- '即时'|'日内'|'短期'|'中期'

-- 决策辅助
action_hint         TEXT                           -- '观察'|'关注'|'加仓'|'减仓'|'规避'
ai_reasoning        TEXT                           -- AI 解释（可空）
risk_notes          TEXT                           -- 风险提示

-- 元数据
processed_by        TEXT                           -- 'rule'|'sdk:anthropic-claude-x'|'agent:news-analyst'
processed_at        DATETIME
duration_ms         INTEGER
UNIQUE (news_id, processed_by)
INDEX (importance_score, processed_at)
INDEX (urgency_score, processed_at)
INDEX (primary_category)
```

#### `market_snapshots`（行情快照，PRD §10）
```
id              INTEGER PRIMARY KEY
ts              DATETIME NOT NULL
asset_kind      TEXT NOT NULL                  -- 'index'|'stock'|'sector'|'commodity'|'fx'
code            TEXT NOT NULL                  -- 'sh000001'|'000001.SZ'|'PCB'|'XAU'|'USDCNY'
name            TEXT
price           REAL
change_pct      REAL                           -- 涨跌幅 %
change_abs      REAL
volume          REAL
turnover        REAL
extra_json      JSON
INDEX (ts, asset_kind)
INDEX (code, ts)
```

#### `sector_trends`（板块趋势）
```
id              INTEGER PRIMARY KEY
ts              DATETIME NOT NULL
sector_name     TEXT NOT NULL
change_pct      REAL
news_heat       INTEGER                        -- 相关新闻数量加权
sentiment_score REAL                           -- -1.0 ~ +1.0
fund_status     TEXT                           -- '放量'|'缩量'|'流入'|'流出'
representative_stocks JSON
trend_judgment  TEXT                           -- '延续'|'分歧'|'退潮'|'反转'
INDEX (ts, sector_name)
```

#### `alerts`（P0-P3 告警）
```
id              INTEGER PRIMARY KEY
news_id         INTEGER REFERENCES news_items(id)
level           TEXT NOT NULL                  -- 'P0'|'P1'|'P2'|'P3'
trigger_reason  TEXT NOT NULL
analysis_id     INTEGER REFERENCES news_analysis(id)
status          TEXT NOT NULL                  -- 'pending'|'pushed'|'dismissed'
created_at      DATETIME NOT NULL
pushed_at       DATETIME
INDEX (level, created_at)
INDEX (status)
```

#### `reports`（6 时段日报）
```
id              INTEGER PRIMARY KEY
date            DATE NOT NULL
kind            TEXT NOT NULL                  -- 'premarket'|'morning'|'noon'|'afternoon'|'close'|'evening'
status          TEXT NOT NULL                  -- 'pending'|'completed'|'failed'
markdown        TEXT
content_json    JSON                           -- 结构化内容
generated_by    TEXT                           -- 'rule'|'sdk:...'|'agent:daily-report-writer'
generated_at    DATETIME NOT NULL
push_count      INTEGER DEFAULT 0
UNIQUE (date, kind)
INDEX (kind, date)
```

#### `push_records`（推送日志）
```
id              INTEGER PRIMARY KEY
user_id         INTEGER REFERENCES users(id)
kind            TEXT NOT NULL                  -- 'alert_p0'|'alert_p1'|'alert_p2_batch'|'report'|'manual'
ref_id          INTEGER                        -- alerts.id 或 reports.id
channel         TEXT NOT NULL                  -- 'wework'|'lark'|'email'|'telegram'
content         TEXT NOT NULL
sent_at         DATETIME
status          TEXT NOT NULL                  -- 'pending'|'sent'|'failed'|'rate_limited'
error_message   TEXT
attempt_count   INTEGER DEFAULT 0
INDEX (user_id, sent_at)
INDEX (kind, sent_at)
INDEX (status)
```

#### `params` + `param_versions`（参数配置）
```
-- params: 当前生效值
key             TEXT PRIMARY KEY
current_version INTEGER NOT NULL REFERENCES param_versions(id)
scope           TEXT NOT NULL                  -- 'global'|'user:<id>'|'sector:<name>'
sensitive       BOOLEAN DEFAULT FALSE
description     TEXT

-- param_versions: 历史
id              INTEGER PRIMARY KEY
key             TEXT NOT NULL REFERENCES params(key)
value_json      JSON NOT NULL
changed_by      INTEGER REFERENCES users(id)
change_reason   TEXT
created_at      DATETIME NOT NULL
INDEX (key, created_at)
```

#### `audit_events`（审计）
```
id              INTEGER PRIMARY KEY
ts              DATETIME NOT NULL
actor_id        INTEGER REFERENCES users(id)
action          TEXT NOT NULL                  -- 'param.set'|'param.rollback'|'alert.dismiss'|'config.reload'|...
target_kind     TEXT
target_id       TEXT
metadata_json   JSON
INDEX (ts)
INDEX (actor_id, ts)
INDEX (action)
```

#### `config_versions`（系统配置版本）
```
id              INTEGER PRIMARY KEY
config_name     TEXT NOT NULL                  -- 'sources.yml'|'keywords.yml'|...
version         INTEGER NOT NULL
content_yaml    TEXT NOT NULL
changed_by      INTEGER REFERENCES users(id)
created_at      DATETIME NOT NULL
UNIQUE (config_name, version)
```

### 7.3 配置 vs 数据库

| 数据类型 | 存储位置 | 理由 |
|---------|---------|------|
| 关键词词典 / 板块映射表 | `config/keywords.yml`、`config/sectors.yml` | 版本化、可 review |
| 推送时间表 | `config/scheduler.yml` | 同上 |
| 来源权重 | `config/sources.yml` | 同上 |
| AI Prompt 模板 | `config/prompts/*.j2` | 同上 |
| LLM 选型 / 参数 | `config/agents.yml` + `config/llm.yml` | 同上 |
| API 密钥 / Webhook | `.env`（git ignore） | 安全 |
| 用户订阅 | DB | 运行时增删 |
| **可调阈值**（如告警权重） | DB（`params` 表） | 运行时调优 + 版本化 + 审计 |
| 调度执行历史 | DB（APScheduler 表） | 运行时状态 |
| 业务数据 | DB | 持续累积 |

### 7.4 数据保留策略

| 数据 | 保留期 | 策略 |
|------|--------|------|
| `news_items` 原文 | 永久 | 1 年约 200-800 MB，可控 |
| `news_analysis` | 永久 | 未来 AI 训练价值 |
| `market_snapshots` | 永久 | 历史回测可用 |
| `source_health` | 90 天 | 仅运维用 |
| `alerts` | 永久 | 审计 |
| `reports` | 永久 | 用户访问 |
| `push_records` | 永久 | 审计 |
| `audit_events` | 永久 | 合规 |
| 应用日志（文件） | 90 天滚动 | `loguru` rotation |
| APScheduler 执行历史 | 30 天 | 防表膨胀 |

### 7.5 时间与节假日

- **存储统一 UTC**，显示按用户时区（默认 `Asia/Shanghai`）
- 交易日历用 `chinese-calendar` Python 库 + `akshare.tool_trade_date_hist_sina()` 缓存到 `data/trade_calendar.json`
- 6 时段日报中：盘前 / 早盘 / 午间 / 尾盘 / 收盘 仅工作日跑；晚间 7×24 跑
- 节假日跳过新闻轮询的高频时段，但**不停止低频归档**

---

## 8. 新闻分类与评分体系

### 8.1 一级分类（8 类，PRD §5.1）

| 一级分类 | 说明 | 示例 |
|---------|------|------|
| **宏观政策** | 货币、财政、地产、产业、监管 | 央行降准、证监会发声 |
| **市场行情** | 指数、板块、成交额、涨跌停、资金面 | 涨停潮、ETF 异动 |
| **公司公告** | 业绩、回购、并购、减持、合同、处罚 | 业绩预告、定增 |
| **海外映射** | 美股、港股、日韩、中概、海外科技链 | 标普收跌、英伟达财报 |
| **大宗商品** | 原油、黄金、有色、黑色、农产品 | 原油暴涨、黄金创新高 |
| **风险事件** | 黑天鹅、地缘冲突、违约、灾害、系统故障 | 战争、债务违约 |
| **资金流** | 北向、ETF、两融、机构、龙虎榜 | 北向流入、龙虎榜 |
| **交易提示** | 停复牌、解禁、分红、转债、申购 | XX 解禁 / 分红 |

### 8.2 二级标签（14+ 板块，可扩展）

PRD §5.2 给出的初始标签：

```
AI算力 / 半导体 / CPO / PCB / 新能源车 / 光伏储能 / 创新药 /
消费 / 券商 / 地产链 / 军工 / 低空经济 / 有色金属 /
红利高股息 / 出海链 / ...
```

二级标签**配置化**（`config/sectors.yml`），支持运行时新增。

### 8.3 新闻结构化字段（18 字段，PRD §5.3）

每条新闻入库 + 分析后包含：

| 字段 | 说明 | 来源 |
|------|------|------|
| `news_id` | 唯一 ID | 自增 |
| `title` | 标题 | 源 |
| `summary` | 摘要 | 源 / AI 生成 |
| `source` | 来源 | 源 |
| `url` | 原文链接 | 源 |
| `published_at` | 发布时间 | 源 |
| `fetched_at` | 抓取时间 | Collector |
| `primary_category` | 一级分类 | Classifier |
| `tags` | 二级标签 | Classifier |
| `related_markets` | 影响市场（A股/港股/...） | Analysis |
| `related_sectors` | 影响板块 | Analysis |
| `related_symbols` | 相关标的 | Analysis |
| `sentiment` | 情绪方向（6 级） | Analysis |
| `importance_score` | 重要性 1-5 | Analysis |
| `urgency_score` | 紧急度 1-5 | Analysis |
| `confidence_score` | 置信度 1-5 | Analysis |
| `impact_horizon` | 即时/日内/短期/中期 | Analysis |
| `action_hint` | 观察/关注/加仓/减仓/规避 | Analysis |
| `ai_reasoning` | AI 分析逻辑 | Analysis |
| `duplicate_group_id` | 去重事件组 ID（= `event_id`） | Deduper |

### 8.4 重要性评分模型（1-5）

PRD §6.1：

| 评分 | 触发因子（任一） |
|------|----------------|
| **5** | 央行 / 证监会 / 国务院重大政策；战争 / 黑天鹅；监管立案 |
| **4** | 行业政策；权重股重大公告；市场指数 5 分钟剧烈异动 |
| **3** | 普通板块新闻；个股普通公告；海外指数中度波动 |
| **2** | 一般行业新闻；非权重股公告 |
| **1** | 边缘新闻 / 灰度内容 |

加分因子（可叠加，max +2）：
- +1：是否官方发布
- +1：是否影响多个板块
- +1：是否影响当前热点
- +1：是否涉及用户订阅标的

### 8.5 紧急度评分模型（1-5）

PRD §6.2：

| 评分 | 触发条件 |
|------|---------|
| **5** | 黑天鹅、官方重大政策（盘中突发） |
| **4** | 指数 / 板块快速异动；个股重大停牌 / 处罚 |
| **3** | 海外市场大幅波动；重要数据公布 |
| **2** | 普通公告；常规研报 |
| **1** | 收盘后 / 非交易时段非紧急 |

### 8.6 情绪方向（6 级）

```
强利多 → 利多 → 中性 → 利空 → 强利空 → 不确定
```

### 8.7 推送等级 P0-P3 映射（决策表）

```python
def evaluate_alert_level(analysis: NewsAnalysis, subscriptions: List[Subscription]) -> AlertLevel:
    if analysis.primary_category in (RISK_EVENT, MAJOR_POLICY) and analysis.importance >= 5 and analysis.urgency >= 5:
        return P0   # 黑天鹅 / 重大政策强提醒
    if (analysis.importance >= 4 and analysis.urgency >= 4) or hits_subscriptions(analysis, subscriptions):
        return P1   # 即时推送
    if analysis.importance >= 3:
        return P2   # 汇总推送
    return P3       # 仅入库
```

---

## 9. 关键工作流

### 9.1 实时新闻采集与处理流程

```
APScheduler 按时段动态频率触发 news_realtime_poll_job()
  │
  ├─→ NewsCollector.poll_realtime()
  │     ├─→ 各 NewsSource 并发 fetch_realtime()（max 5 并发）
  │     ├─→ 写 source_health 表
  │     └─→ 返回 RawNewsItem[]
  │
  ├─→ NewsCollector 标准化 + 写 news_items（UNIQUE 跳重复）
  │
  ├─→ NewsDeduper.dedupe_batch(new_items)
  │     ├─→ URL 去重 → 标题去重 → SimHash 去重
  │     └─→ 写 news_events，回填 news_items.event_id
  │
  ├─→ NewsClassifier.classify(item) for new_items
  │     ├─→ 关键词匹配 → primary_category
  │     ├─→ 板块词库扫描 → tags
  │     └─→ 个股名/代码扫描 → related_symbols
  │
  ├─→ NewsAnalysis.analyze(item, classification) for filtered
  │     ├─→ 过滤：importance_pre >= 3 OR 命中订阅
  │     ├─→ 走 AIProvider（Phase 1: SDK / Phase 2: Brainmaster agent）
  │     └─→ 失败降级到规则评分
  │
  ├─→ AlertService.evaluate(item, analysis)
  │     ├─→ 决策表 → AlertLevel
  │     └─→ 写 alerts 表
  │
  └─→ for alert in P0/P1/P2:
        NewsPusher.push_alert(alert)（按节流 + 路由表）
```

### 9.2 6 时段日报生成流程

```
APScheduler 在每个时段前 5 分钟触发 report_generate_<kind>_job()
  │
  ├─→ ReportService.generate(kind, today)
  │     ├─→ NewsRepo.query_by_window(start, end) → 获取该时段相关新闻
  │     ├─→ MarketDataService.get_market_status_bar() → 顶部行情
  │     ├─→ SectorTrendService.top_n_sectors(by='news_heat', n=10) → 热门板块
  │     ├─→ AIProvider.generate_report(kind, items, market_data)
  │     │     ├─→ Phase 1: 用 SDK 生成 Markdown + JSON
  │     │     └─→ Phase 2: 走 daily-report-writer agent（subprocess）
  │     ├─→ 写 reports 表
  │     └─→ 触发 NewsPusher.push_report(report_id, [wework, lark])
  │
  └─→ 失败降级：
        ├─→ AIProvider 失败 → 走原文头条列表模板（不依赖 AI）
        └─→ 推送失败 → 重试 3 次 → 切换备用渠道 → 仍失败发告警
```

### 9.3 P0-P3 告警分发流程

```
NewsAnalysis 完成 → AlertService.evaluate()
  │
  ├─→ 决策表（§8.7）→ AlertLevel
  │
  ├─→ 写 alerts 表（status='pending'）
  │
  ├─→ NewsPusher.push_alert(alert):
  │     │
  │     ├─→ if P0:
  │     │     ├─→ 全渠道并发：企微 + 飞书 + 邮件
  │     │     ├─→ 不限节流
  │     │     └─→ 推送内容含【强提醒】+ 完整 AI 分析
  │     │
  │     ├─→ elif P1:
  │     │     ├─→ 企微 + 飞书
  │     │     ├─→ 节流 max 6/h
  │     │     └─→ 推送内容含 AI 分析
  │     │
  │     ├─→ elif P2:
  │     │     ├─→ 加入"P2 burst batch"队列
  │     │     ├─→ 每 30min 触发一次汇总推送（企微）
  │     │     └─→ 推送内容为新闻列表 + 简要标签
  │     │
  │     └─→ elif P3:
  │           └─→ 仅入库（看板查询）
  │
  └─→ alerts.status = 'pushed' / 'failed' / 'dismissed'
```

### 9.4 板块趋势更新流程

```
每 15 分钟 SchedulerService 触发 sector_trend_refresh_job()
  │
  ├─→ for sector in known_sectors:
  │     ├─→ MarketDataService.get_sector_snapshot(sector)
  │     ├─→ NewsRepo.count_by_sector(sector, last_24h) → news_heat
  │     ├─→ NewsAnalysisRepo.avg_sentiment(sector, last_24h) → sentiment_score
  │     ├─→ SectorTrendService.compute_sector_trend(sector)
  │     └─→ 写 sector_trends 表
  │
  └─→ 暴露 /api/dashboard/sectors 给前端
```

### 9.5 AI 工作流（Phase 1：SDK / Phase 2：Brainmaster）

#### Phase 1：通过 SDK

```
NewsAnalysis.analyze(item)
  │
  ├─→ AIProvider = AnthropicSDKProvider | DeepSeekSDKProvider
  │
  ├─→ provider.analyze_news(item, classification, context)
  │     ├─→ render prompt (templates/analyze_news.j2)
  │     ├─→ call SDK with timeout=30s
  │     └─→ parse JSON response
  │
  ├─→ 校验输出 schema → NewsAnalysisResult
  │
  └─→ 失败降级：
        ├─→ Tier 2: 切换备用 SDK
        └─→ Tier 3: 走规则评分（SimpleRuleScorer）
```

#### Phase 2：通过 ClaudeAgentRunner（沿用 v2 §7.3）

```
AIService.summarize_for_premarket(news_ids, date)
  │
  ├─→ NewsRepo.export_raw_for_date(date) → data/news/raw/<date>/*.json
  │
  ├─→ render prompts/run_premarket_agent.j2
  │
  ├─→ ClaudeAgentRunner.run(
  │     agent_name="news-analyst",
  │     prompt=...,
  │     expected_output=Path("data/news/summaries/<date>-premarket.json"),
  │     timeout=600
  │   )
  │     ├─→ subprocess.run(["claude", "--agent", "news-analyst", "-p", prompt])
  │     ├─→ status='completed' iff (exit=0 AND mtime>pre AND json valid AND fields ok)
  │     └─→ 否则 status ∈ {degraded, timeout, error}
  │
  └─→ 失败降级：Tier 2 (SDK) → Tier 3 (规则模板) → 告警
```

---

## 10. 看板与 API 设计

### 10.1 看板首页布局（PRD §8.1）

```
┌────────────────────────────────────────────────────────────────────┐
│  ① 顶部市场状态栏                                                   │
│  上证 -0.5% │ 深证 -0.3% │ 创业板 +0.2% │ 科创50 │ 北证50 │ 恒科 │ │
│  纳斯达克 │ 美元指数 │ USD/CNY │ 原油 │ 黄金                       │
├────────────────────────────────────────────────────────────────────┤
│  ② 今日核心结论 (盘前日报抓取)                                      │
├──────────────────┬─────────────────────────────────────────────────┤
│  ③ 实时新闻流     │  ④ 重要新闻卡片 (P0/P1)                         │
│  时间｜来源｜标题  │  ┌──────────────┐  ┌──────────────┐           │
│  分类｜重要性｜情绪│  │ 央行降准 ...  │  │ XX 公告 ...  │           │
│  影响板块 / 标的  │  └──────────────┘  └──────────────┘           │
│  [筛选: 来源/分类/│                                                │
│   情绪/重要性]    │  ⑤ 板块热力图                                  │
│                  │     (top 20 板块涨跌 + 新闻热度)                │
│                  │                                                │
│                  │  ⑥ 新闻影响板块榜                               │
│                  │  ⑦ 个股异动榜                                   │
│                  │  ⑧ 突发告警区 (置顶 P0)                         │
├──────────────────┴─────────────────────────────────────────────────┤
│  ⑨ 日报入口 (盘前 / 早盘 / 午间 / 尾盘 / 收盘 / 晚间)               │
└────────────────────────────────────────────────────────────────────┘
```

### 10.2 完整 API 端点清单（PRD §9）

#### 新闻 API

```text
GET    /api/news                  # 列表（query: source, category, sentiment, importance, since, limit）
GET    /api/news/{news_id}        # 详情（含 AI 分析）
GET    /api/news/events           # 事件聚合列表
POST   /api/news/refresh          # 强制刷新（管理员）
GET    /api/news/search           # 全文搜索
```

#### 看板 API

```text
GET    /api/dashboard/summary     # 首页聚合数据
GET    /api/dashboard/market-status # 顶部市场状态栏
GET    /api/dashboard/sectors     # 板块趋势看板
GET    /api/dashboard/alerts      # 突发告警区
GET    /api/dashboard/movers      # 个股异动榜
```

#### 日报 API

```text
POST   /api/reports/generate      # 手动触发日报生成（管理员）
GET    /api/reports               # 日报列表（query: kind, date_from, date_to）
GET    /api/reports/{report_id}   # 日报详情
POST   /api/reports/{report_id}/push  # 重新推送
GET    /api/reports/today/{kind}  # 今日某时段日报
```

#### 告警 API

```text
GET    /api/alerts                # 告警列表
GET    /api/alerts/{alert_id}
POST   /api/alerts/{alert_id}/dismiss
GET    /api/alerts/stats          # 各级别统计
```

#### 配置 API

```text
GET    /api/config/sources        # 数据源列表 + 健康
PUT    /api/config/sources/{code} # 启用/禁用源
GET    /api/config/alert-rules    # 告警规则
PUT    /api/config/alert-rules
GET    /api/config/versions       # 配置文件版本历史
```

#### 参数 API（参数配置模块）

```text
GET    /api/params                # 列表
GET    /api/params/{key}          # 单参数（含历史版本）
PUT    /api/params/{key}          # 修改（写新版本）
POST   /api/params/{key}/rollback?to=<version>
GET    /api/params/audit          # 审计日志
```

#### 系统 API

```text
GET    /healthz
GET    /metrics                   # Prometheus
```

### 10.3 关键 DTO 示例

#### `NewsCardDTO`（新闻流单条）

```json
{
  "news_id": 12345,
  "title": "央行降准 0.25%",
  "summary": "...",
  "source": "央行官网",
  "url": "...",
  "published_at": "2026-06-19T08:30:00+08:00",
  "primary_category": "宏观政策",
  "tags": ["货币政策"],
  "sentiment": "强利多",
  "importance": 5,
  "urgency": 5,
  "confidence": 5,
  "impact_horizon": "即时",
  "action_hint": "关注",
  "related_sectors": [{"name": "券商", "weight": 0.9}, {"name": "地产链", "weight": 0.7}],
  "related_symbols": [{"code": "601318", "name": "中国平安"}],
  "alert_level": "P0",
  "pushed": true
}
```

#### `DashboardSummary`

```json
{
  "market_status": { "indexes": [...], "fx": [...], "commodities": [...] },
  "today_conclusion": "...",
  "p0_alerts": [...],
  "p1_alerts": [...],
  "top_sectors": [...],
  "top_movers": [...],
  "latest_news": [...],
  "today_reports": { "premarket": {...}, "morning": null, ... }
}
```

#### `Report`

```json
{
  "report_id": 42,
  "date": "2026-06-19",
  "kind": "premarket",
  "status": "completed",
  "markdown": "## 隔夜美股\n...\n## 政策面\n...",
  "content_json": {
    "sections": [
      {"name": "隔夜美股", "items": [...]},
      {"name": "政策面", "items": [...]},
      ...
    ]
  },
  "generated_by": "sdk:anthropic-claude-3-5-sonnet",
  "generated_at": "2026-06-19T07:58:14+08:00"
}
```

---

## 11. 参数配置模块

### 11.1 参数类型

| 类型 | 示例 | scope |
|------|------|-------|
| 数据源开关 | `sources.ths.enabled` | global |
| 抓取频率 | `news.realtime_poll_seconds` | global |
| 关键词权重 | `keywords.涨停.weight` | global |
| 告警阈值 | `alert.p0.importance_min` / `alert.p0.urgency_min` | global |
| 推送渠道开关 | `push.wework.enabled` | global |
| 用户订阅 | `subscription.<user_id>.<kind>.<value>.weight` | user |
| 板块映射 | `sectors.AI算力.keywords` | global |

### 11.2 权限矩阵（基础版）

| 角色 | 读取参数 | 修改非敏感参数 | 修改敏感参数 | 回滚 | 审计查询 |
|------|---------|---------------|------------|------|---------|
| **admin** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **analyst** | ✅ | 🔍（自己 scope） | ❌ | ❌ | 🔍（仅看自己） |
| **trader** | ✅ | 🔍（自己 scope） | ❌ | ❌ | ❌ |
| **guest** | 🔍（脱敏） | ❌ | ❌ | ❌ | ❌ |

敏感参数定义（`params.sensitive=TRUE`）：
- 任何含密钥 / token / webhook 的参数
- 推送渠道开关
- 数据源全局禁用

### 11.3 版本与回滚

每次 `set` 都写一行 `param_versions`，并更新 `params.current_version`。

回滚：
1. 找到目标历史版本 `param_versions(id=N)`
2. 创建一行新的 `param_versions`，`value_json` 复制自 N
3. 更新 `params.current_version` 指向新行
4. 写 `audit_events` 记录"回滚到版本 N"

> **保留写入而非物理删除**：保证审计完整。

### 11.4 审计日志

每次参数读 / 写 / 回滚都写 `audit_events`：

```json
{
  "ts": "2026-06-19T10:23:11+08:00",
  "actor_id": 1,
  "action": "param.set",
  "target_kind": "param",
  "target_id": "alert.p0.importance_min",
  "metadata_json": {
    "from_version": 7,
    "to_version": 8,
    "old_value": 5,
    "new_value": 4,
    "reason": "降低 P0 阈值适配端午行情"
  }
}
```

### 11.5 脱敏展示

读取敏感参数：
- admin：可看明文
- 其他角色：返回 `***xxx`（保留末 4 位）+ `sensitive: true` flag
- API 响应 + 日志均脱敏

---

## 12. 配置与密钥管理

### 12.1 配置文件清单

```
config/
├── app.yml                # 应用全局
├── agents.yml             # Phase 2 Brainmaster agent 配置
├── llm.yml                # Phase 1+2 SDK fallback
├── sources.yml            # 新闻源
├── market_sources.yml     # 行情源
├── sectors.yml            # 板块映射
├── keywords.yml           # 关键词词典
├── classification.yml     # 一级 / 二级分类规则
├── scheduler.yml          # 调度时间表
├── notifiers.yml          # 推送渠道
├── alert_rules.yml        # P0-P3 决策规则
├── params_seed.yml        # 参数初始种子
└── prompts/
    ├── analyze_news.j2
    ├── generate_report_<kind>.j2
    ├── run_premarket_agent.j2     # Phase 2
    └── run_report_agent.j2         # Phase 2
```

### 12.2 关键示例

#### `app.yml`

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
poc:
  port: 8000          # 静态 HTML POC
```

#### `sources.yml`

```yaml
sources:
  - code: ths
    name: 同花顺
    priority: high
    base_url: https://news.10jqka.com.cn
    poll_interval_seconds: 60
  - code: eastmoney
    name: 东方财富 7x24
    priority: high
    base_url: https://kuaixun.eastmoney.com
    poll_interval_seconds: 60
  - code: yahoo
    name: 雅虎财经
    priority: medium
    base_url: https://finance.yahoo.com
    poll_interval_seconds: 120
  - code: exchange_sse
    name: 上交所公告
    priority: highest
    base_url: http://www.sse.com.cn
    poll_interval_seconds: 300
  - code: gov_pbc
    name: 央行
    priority: highest
    base_url: http://www.pbc.gov.cn
    poll_interval_seconds: 600
  # ...
```

#### `alert_rules.yml`

```yaml
levels:
  P0:
    importance_min: 5
    urgency_min: 5
    categories: ['风险事件', '宏观政策']
    channels: ['wework', 'lark', 'email']
    rate_limit_per_hour: -1   # 不限
  P1:
    importance_min: 4
    urgency_min: 4
    or_subscription_hit: true
    channels: ['wework', 'lark']
    rate_limit_per_hour: 6
  P2:
    importance_min: 3
    channels: ['wework']
    batch_window_minutes: 30
  P3:
    channels: []
```

#### `scheduler.yml`

```yaml
jobs:
  # 新闻轮询（按时段动态频率）
  - id: news_realtime_poll_morning
    enabled: true
    cron: "*/1 8-9 * * 1-5"
  - id: news_realtime_poll_intraday
    enabled: true
    cron: "*/2 9-11 * * 1-5"
  # ...

  # 6 时段日报
  - id: report_premarket
    cron: "55 7 * * 1-5"
  - id: report_morning
    cron: "25 9 * * 1-5"
  - id: report_noon
    cron: "32 11 * * 1-5"
  - id: report_afternoon
    cron: "30 14 * * 1-5"
  - id: report_close
    cron: "15 15 * * 1-5"
  - id: report_evening
    cron: "0 20 * * *"           # 7 天

  # 行情快照
  - id: market_snapshot_intraday
    cron: "*/5 9-15 * * 1-5"
  - id: market_snapshot_other
    cron: "*/30 * * * *"

  # 板块趋势
  - id: sector_trend_refresh
    cron: "*/15 * * * *"

  # 健康检查
  - id: health_self_check
    cron: "*/5 * * * *"
```

### 12.3 `.env.example`

```bash
# ===== Phase 1 必填 =====
WEWORK_BOT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxx
WEWORK_ALERT_BOT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxx
LARK_BOT_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx
EMAIL_SMTP_HOST=smtp.example.com
EMAIL_SMTP_PORT=465
EMAIL_USER=
EMAIL_PASS=

# ===== Phase 1 AI（至少配一个）=====
ANTHROPIC_API_KEY=sk-ant-xxxxx
# 或
DEEPSEEK_API_KEY=sk-xxxxx

# ===== Phase 2 Brainmaster（无 API key 需求）=====
# 仅需 Claude CLI 在 PATH

# ===== App =====
APP_ENV=dev
LOG_LEVEL=INFO
```

> **Phase 1 至少需要一个 LLM API key**（用于 SDK 路径）；Phase 2 可完全去除 API key 依赖。

### 12.4 密钥处理原则

- `.env` 永远在 `.gitignore`
- 启动时密钥脱敏后写一行 INFO 日志（如 `LLM key loaded: sk-ant-***xxx`）
- 任何日志 / 异常堆栈中不允许出现完整密钥（用 `structlog` processor 过滤）
- 参数模块敏感字段统一脱敏读取（详 §11.5）

---

## 13. 错误处理与可观察性

### 13.1 故障隔离矩阵

| 故障类型 | 隔离策略 | 告警阈值 |
|---------|---------|---------|
| 单个新闻源不可用 | 标记 `source_health.status=down`、其他源继续 | 连续 3 次失败 |
| 行情源不可用 | 切换备用行情源 → 仍失败用最近一份缓存 | 缓存超过 1h |
| AI（SDK）不可用 | 切换备用 SDK → 切换到规则评分 | 连续 5 次失败 |
| AI（Phase 2 agent）不可用 | 走 Tier 2 SDK → 走 Tier 3 规则模板 | 同上 |
| 推送渠道失败 | 3 次指数退避 → 切换备用渠道 | 备用也失败 |
| 数据库不可用 | 关键写操作进内存队列、恢复后重放 | 30 秒未恢复 |
| 调度器卡死 | 外部 watchdog（每 5 分钟 ping `/healthz`）+ 自动重启 | 单次未响应 |

> **Watchdog**：与主应用进程独立（Windows 用 Task Scheduler 注册 `watchdog.ps1`，每 5 分钟运行）。脚本放在 `scripts/watchdog/`。

### 13.2 日志策略

- 框架：`structlog` → JSON 输出
- 文件：`logs/app.{YYYY-MM-DD}.jsonl`，按日滚动，保留 90 天
- 关键字段：`timestamp`, `level`, `event`, `module`, `user_id`, `news_id`, `trace_id`, `duration_ms`
- 错误同时写一份纯文本到 `logs/errors.log` 方便人工浏览
- **审计**：参数 / 配置 / 推送决策另写 `audit_events` 表

### 13.3 Prometheus 指标 (`/metrics`)

```
# 采集
news_items_collected_total{source}
news_collection_duration_seconds{source}
news_collection_failures_total{source, error_type}
source_health_status{source}              # 0=down, 1=degraded, 2=ok

# 分类与分析
news_classified_total{category, level}
news_analyzed_total{provider, success}
news_analysis_duration_seconds{provider}
ai_calls_total{provider, model, success}
ai_tokens_used_total{provider, model, kind}

# 告警与推送
alerts_total{level, status}
push_records_total{channel, kind, status}
push_duration_seconds{channel}
push_throttled_total{user_id, reason}

# 行情
market_snapshot_refresh_total{source, success}
sector_trend_refresh_total{success}

# 日报
report_generated_total{kind, status}
report_generation_duration_seconds{kind}

# 健康
scheduler_jobs_run_total{job_id, status}
scheduler_jobs_misfired_total{job_id}
db_query_duration_seconds{operation}
```

### 13.4 健康检查 `/healthz`

```json
{
  "status": "healthy|degraded|unhealthy",
  "checks": {
    "db": { "status": "ok", "latency_ms": 3 },
    "scheduler": { "status": "ok", "running_jobs": 12 },
    "sources": {
      "ths": { "status": "ok" },
      "eastmoney": { "status": "ok" },
      "yahoo": { "status": "degraded", "last_error": "..." }
    },
    "market_sources": {
      "akshare": { "status": "ok" }
    },
    "ai": { "status": "ok", "active_provider": "anthropic_sdk" },
    "notifier": { "status": "ok" }
  },
  "phase1_status": {
    "last_news_collected": "2026-06-19T10:30:12+08:00",
    "last_report_generated": "2026-06-19T07:58:14+08:00",
    "last_p0_alert": "2026-06-18T14:23:11+08:00"
  },
  "uptime_seconds": 123456
}
```

### 13.5 告警分级与路由

| 级别 | 触发条件 | 路由 |
|------|---------|------|
| DEBUG/INFO | 普通业务事件 | 仅日志 |
| WARN | 单源失败、节流、降级 | 日志 + 标记 |
| ERROR | 推送失败、AI 全降级、DB 异常 | 日志 + 企微告警机器人 |
| CRITICAL | 调度器死、watchdog 触发、Phase 关键流程全失败 | 日志 + 全渠道告警 + 尝试自愈 |

告警渠道**与业务推送渠道分离**（独立机器人 webhook），避免告警自己被节流。

---

## 14. 测试策略

### 14.1 测试金字塔

```
              /\
             /E2E\           5-8 个 E2E 场景（真抓 1-2 源、Mock LLM、Mock 推送）
            /─────\
           /集成测试 \         每 service 1-2 个，用 SQLite in-memory
          /─────────\
         /  单元测试    \      覆盖率 ≥ 70%（Repo / Service / Adapter）
        /─────────────\
```

### 14.2 工具栈

- `pytest` + `pytest-asyncio` + `pytest-cov`
- `pytest-mock` mock
- `httpx-mock` HTTP mock
- `freezegun` 时间穿越
- `respx` SDK HTTP mock
- 真实 LLM / 推送走 `--integration` 标记，CI 不跑

### 14.3 关键测试场景

| 编号 | 场景 | 类型 |
|------|------|------|
| T-01 | 同源新闻去重（按 `source_msg_id`） | 单元 |
| T-02 | 跨源同事件聚合（SimHash） | 单元 |
| T-03 | 一级分类规则准确性 | 单元 |
| T-04 | 二级标签提取 | 单元 |
| T-05 | 重要性 / 紧急度评分（多用例） | 单元 |
| T-06 | P0/P1/P2/P3 告警决策正确 | 单元 |
| T-07 | 用户订阅命中 → P1 升级 | 单元 |
| T-08 | 节流：1 分钟内第 2 条 P1 → 拒绝/累积 | 单元 |
| T-09 | 节假日不触发盘前 / 早盘 / 午间 / 尾盘 / 收盘日报 | 单元（freezegun） |
| T-10 | 单源 500 错误其他源继续 | 集成 |
| T-11 | AI SDK 超时降级到规则评分 | 集成 |
| T-12 | 推送失败重试 3 次 + 切换备用渠道 | 集成 |
| T-13 | 板块趋势计算（行情 + 新闻热度） | 集成 |
| T-14 | E2E：完整盘前日报流程（抓→分类→分析→生成→推送→入库） | E2E |
| T-15 | E2E：完整 P0 告警流程 | E2E |
| T-16 | E2E：参数修改 + 回滚 + 审计验证 | E2E |
| T-17 | E2E：watchdog 触发自愈 | E2E |
| T-18 | E2E：Phase 2 Brainmaster agent 调用（仅本地，CI skip） | E2E |

### 14.4 CI（GitHub Actions）

```yaml
name: CI
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
  lint-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: uv run markdownlint docs/
```

---

## 15. 项目结构

```
Project_Amarket/
├── README.md
├── CLAUDE.md
├── CHANGELOG.md
├── CONTRIBUTING.md           # 🆕 小组协作指南
├── CODEOWNERS                # 🆕 模块 owner
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── start.bat
├── start.sh
│
├── docs/
│   ├── PROJECT_STATE.md
│   ├── sessions/
│   ├── adr/
│   ├── peersession-source/      # 🆕 原始 PRD + Timeline 归档
│   │   ├── a_share_realtime_news_dashboard_prd.md
│   │   └── a_share_quant_project_timeline.docx
│   ├── ARCHITECTURE.md          # 🆕 单独的架构图（M2 交付）
│   ├── UML/                     # 🆕 UML 图（Timeline M7）
│   └── superpowers/
│       ├── specs/
│       │   ├── 2026-06-14-news-engine-design.md   # v2 历史
│       │   └── 2026-06-19-spec1-v3-merged.md      # ← 本文件
│       └── plans/
│
├── .claude/                  # Phase 2: Brainmaster
│   ├── agents/
│   │   ├── news-analyst.md            # 已有 (v2)
│   │   ├── news-classifier-realtime.md  # 🆕 Phase 2
│   │   └── daily-report-writer.md       # 🆕 Phase 2
│   ├── commands/
│   │   ├── test-premarket.md          # 已有
│   │   ├── test-report.md             # 🆕
│   │   └── test-classify.md           # 🆕
│   └── settings.json
│
├── scripts/
│   ├── watchdog/
│   │   ├── watchdog.ps1
│   │   └── watchdog.sh
│   ├── seed_db.py            # 初始化数据库种子
│   └── extract_docx.py       # docx → md 工具
│
├── config/
│   ├── app.yml
│   ├── agents.yml
│   ├── llm.yml
│   ├── sources.yml
│   ├── market_sources.yml
│   ├── sectors.yml
│   ├── keywords.yml
│   ├── classification.yml
│   ├── scheduler.yml
│   ├── notifiers.yml
│   ├── alert_rules.yml
│   ├── params_seed.yml
│   └── prompts/
│       ├── analyze_news.j2
│       ├── generate_report_premarket.j2
│       ├── generate_report_morning.j2
│       ├── generate_report_noon.j2
│       ├── generate_report_afternoon.j2
│       ├── generate_report_close.j2
│       ├── generate_report_evening.j2
│       ├── run_premarket_agent.j2
│       └── run_report_agent.j2
│
├── data/                     # 运行时（gitignore）
│   ├── amarket.db
│   ├── trade_calendar.json
│   ├── logs/
│   ├── news/
│   │   ├── raw/
│   │   ├── processed/
│   │   └── summaries/
│   ├── reports/
│   └── market/
│
├── poc/                      # 🆕 静态 HTML POC（Timeline M6）
│   ├── index.html
│   ├── news.html
│   ├── dashboard.html
│   ├── reports.html
│   ├── params.html
│   ├── assets/
│   │   ├── css/
│   │   ├── js/
│   │   └── data/             # 静态 demo 数据 fallback
│   └── README.md
│
├── src/
│   └── amarket/
│       ├── __init__.py
│       ├── main.py
│       ├── cli.py
│       ├── ui/                  # Streamlit 管理面板
│       │   ├── app.py
│       │   ├── pages/
│       │   └── components/
│       │
│       ├── api/                 # FastAPI routers
│       │   ├── news.py
│       │   ├── dashboard.py
│       │   ├── reports.py
│       │   ├── alerts.py
│       │   ├── config.py
│       │   ├── params.py
│       │   ├── health.py
│       │   └── metrics.py
│       │
│       ├── services/
│       │   ├── news/                # 新闻模块
│       │   │   ├── collector.py
│       │   │   ├── deduper.py
│       │   │   ├── classifier.py
│       │   │   ├── analysis.py
│       │   │   └── pusher.py
│       │   ├── dashboard/           # 看板模块
│       │   │   ├── service.py
│       │   │   ├── market_data.py
│       │   │   ├── sector_trend.py
│       │   │   ├── alert.py
│       │   │   └── report.py
│       │   ├── params/              # 参数配置模块
│       │   │   ├── config.py
│       │   │   └── audit.py
│       │   ├── ai_service.py        # 公共
│       │   ├── config_service.py
│       │   ├── scheduler_service.py
│       │   └── observability.py
│       │
│       ├── adapters/
│       │   ├── news_sources/
│       │   │   ├── base.py
│       │   │   ├── ths.py
│       │   │   ├── eastmoney.py
│       │   │   ├── yahoo.py
│       │   │   ├── exchange.py
│       │   │   └── government.py
│       │   ├── market_sources/
│       │   │   ├── base.py
│       │   │   ├── akshare_source.py
│       │   │   ├── efinance_source.py
│       │   │   └── yfinance_source.py
│       │   ├── ai/
│       │   │   ├── base.py
│       │   │   ├── claude_agent_runner.py   # Phase 2
│       │   │   ├── verification.py
│       │   │   ├── anthropic_sdk.py         # Phase 1+2
│       │   │   ├── deepseek_sdk.py          # Phase 1+2
│       │   │   └── rule_scorer.py           # Tier 3 fallback
│       │   └── notifiers/
│       │       ├── base.py
│       │       ├── wework_bot.py
│       │       ├── lark_bot.py
│       │       ├── email.py
│       │       └── telegram_bot.py
│       │
│       ├── repositories/
│       │   ├── base.py
│       │   ├── news_repo.py
│       │   ├── news_event_repo.py
│       │   ├── news_analysis_repo.py
│       │   ├── market_snapshot_repo.py
│       │   ├── sector_trend_repo.py
│       │   ├── alert_repo.py
│       │   ├── report_repo.py
│       │   ├── push_repo.py
│       │   ├── source_health_repo.py
│       │   ├── param_repo.py
│       │   ├── audit_repo.py
│       │   ├── config_repo.py
│       │   └── user_repo.py
│       │
│       ├── domain/
│       │   ├── models.py        # SQLModel
│       │   ├── enums.py
│       │   └── schemas.py       # Pydantic DTOs
│       │
│       ├── core/
│       │   ├── logging.py
│       │   ├── exceptions.py
│       │   ├── cache.py
│       │   ├── market_calendar.py
│       │   ├── simhash.py
│       │   ├── ratelimit.py
│       │   └── utils.py
│       │
│       └── db/
│           ├── session.py
│           ├── base.py
│           └── migrations/
│               ├── env.py
│               └── versions/
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── unit/
    ├── integration/
    ├── e2e/
    └── fixtures/
        ├── news_sources/
        ├── market_sources/
        └── llm_responses/
```

---

## 16. 依赖清单

### 16.1 生产依赖（Phase 1）

| 包 | 用途 | 版本约束 |
|------|------|---------|
| `fastapi` | HTTP 框架 | ^0.115 |
| `uvicorn[standard]` | ASGI 服务器 | ^0.32 |
| `streamlit` | 管理面板 | ^1.40 |
| `sqlmodel` | ORM | ^0.0.22 |
| `alembic` | DB 迁移 | ^1.13 |
| `apscheduler` | 调度 | ^3.10 |
| `httpx` | HTTP 客户端 | ^0.27 |
| `structlog` | 日志 | ^24.0 |
| `loguru` | 日志辅助 | ^0.7 |
| `typer` | CLI | ^0.14 |
| `pydantic` | 数据校验 | ^2.9 |
| `pydantic-settings` | 配置加载 | ^2.6 |
| `jinja2` | 模板 | ^3.1 |
| `chinese-calendar` | 节假日 | ^1.10 |
| `simhash` | 文本去重 | ^2.1 |
| `prometheus-client` | 指标 | ^0.21 |
| `tenacity` | 重试 | ^9.0 |
| `pyyaml` | YAML | ^6.0 |
| `python-dotenv` | env | ^1.0 |
| `akshare` | A 股数据 | ^1.16 |
| `efinance` | A 股备用 | ^0.5 |
| `yfinance` | 海外行情 | ^0.2 |
| `anthropic` | Claude SDK（Phase 1 主，Phase 2 fallback） | ^0.40 |
| `openai` | DeepSeek 兼容协议 | ^1.50 |
| `lxml` / `beautifulsoup4` | HTML 解析 | latest |
| `feedparser` | RSS | ^6.0 |

### 16.2 开发依赖

| 包 | 用途 |
|------|------|
| `pytest` / `pytest-asyncio` / `pytest-cov` / `pytest-mock` | 测试 |
| `httpx-mock` / `respx` | HTTP / SDK mock |
| `freezegun` | 时间穿越 |
| `ruff` | Lint + Format |
| `mypy` | 静态类型检查 |
| `pre-commit` | git hooks |
| `markdownlint-cli` | Markdown lint |

---

## 17. 实施里程碑

### 17.1 Phase 1 — Peersession 三大模块（M0-M6）

| 阶段 | 关键交付 | 完成判定 |
|------|---------|---------|
| **M0：项目骨架 + 小组仓库基础设施** | uv 项目初始化、CI、pre-commit、SQLite + Alembic baseline、健康检查 `/healthz`、Streamlit Hello World、CONTRIBUTING / CODEOWNERS / 分支保护、企微/飞书机器人 hello 推送 | 能本地启动 + 推送一条"hello"到企微/飞书；CI 全绿；新成员能在 30 分钟内 onboarding |
| **M1：数据基座（DB + 1 源新闻 + 1 源行情）** | 11 张表 schema + alembic 迁移、`NewsCollector` 接同花顺 1 源、`NewsRepo`、`MarketDataService` 接 akshare 1 源、最小 `/api/news` GET | 能从同花顺抓 → 入库 → API 查到；能从 akshare 拿到上证指数 |
| **M2：新闻处理（去重 / 分类 / 评分）** | 4 源新闻接入、URL+标题+SimHash 三层去重、`news_events` 聚合、规则分类（一级 + 二级）、规则评分（重要性 / 紧急度 / 情绪）；P0-P3 告警决策 | 4 源同时拉取 + 准确去重 + 评分准确率人工抽样 ≥ 80% |
| **M3：看板 API + 静态 POC 前端** | `/api/dashboard/*` `/api/news` `/api/alerts` 完整、`SectorTrendService` 计算、静态 HTML POC（首页 + 新闻流 + 板块热力图 + 详情页 + 日报页） | 浏览器打开 POC 能在 5 分钟内完整演示；API 文档（Swagger）齐全 |
| **M4：6 时段日报 + P0-P3 告警** | `ReportService` 6 时段全跑通、`NewsPusher` 全渠道（企微 / 飞书 / 邮件）、AI 分析模块（Phase 1 SDK 路径）、降级链 | 1 周内自动生成 30 份日报；推送 P0/P1 告警延迟 < 2 分钟 |
| **M5：参数配置 + 权限矩阵** | `params` + `param_versions` 表、版本化 / 回滚 / 审计、权限矩阵实现、Streamlit 参数面板、`/api/params/*` 完整 | 修改参数 → 回滚 → 审计日志 → 完整链路验证 |
| **M6：集成测试 + 文档 + UML + 试运行** | 18 个测试场景全跑过、`docs/ARCHITECTURE.md`、`docs/UML/*` 流程图 + 时序图、运维手册、连续运行 1 周 | 7 天无人工干预正常运转；测试覆盖率 ≥ 70%；UML 至少 5 张关键图 |

### 17.2 Phase 2 — Brainmaster AI + 推送增强（M7-M9）

| 阶段 | 关键交付 | 完成判定 |
|------|---------|---------|
| **M7：Brainmaster AI 集成** | `ClaudeAgentRunner` (subprocess + 校验)、3 个 agent 定义、Tier 1 切换为 agent、prompt cache | `python -m amarket test-premarket` 走 subprocess 调 claude CLI → agent 写 JSON → Python 读取 → 渲染推送；agent 模式 vs SDK 模式可一键切换 |
| **M8：推送系统增强** | Breaking news < 60s 通道、Telegram 接入、邮件富文本、推送内容 A/B 测试 | Breaking 95th 分位延迟 < 60s |
| **M9：信号交易准备**（**永不下单**） | BrokerAdapter 接口、SignalOnly 实现、Paper trading 实现、信号订阅 / 历史回放 | 模拟交易跑 1 周历史信号无错；为 Spec #2 / #3 做铺垫 |

### 17.3 阶段评审

每个里程碑结束：

1. 跑全部测试（不退化）
2. 手动 demo 关键功能（小组成员观看）
3. 更新 `CHANGELOG.md`
4. Git tag `phase1-m0` / `phase1-m1` / ...
5. 分小组 retro：哪里慢了 / 哪里返工 / 下个阶段调整

---

## 18. 安全与合规

### 18.1 数据合规

- 个人 / 小组自用阶段，不收集他人数据，无 PII 风险
- 抓取新闻源遵守 `robots.txt`、控制 QPS（< 1 req/s/source），不构成 DoS
- 推送内容只用于内部参考，不对外转载 / 二次分发，避免版权问题
- 日志不记录用户身份信息（小组成员也尽量脱敏）

### 18.2 密钥安全

- 所有密钥（API key、webhook）走 `.env`，**严禁提交**
- `.gitignore` 强制包含 `.env`、`data/`、`logs/`、`PAT.txt`、`*.docx`（避免误提交内部材料）
- 启动时校验关键密钥是否齐全，缺失则 fail-fast
- 日志中密钥永远脱敏

### 18.3 推送内容合规

- **所有日报 / 推送末尾固定附加合规声明**："📌 本信息仅供个人 / 小组学习参考，不构成任何投资建议"
- **禁止给出"买入 / 卖出"等明确操作指令**：`action_hint` 字段最多写"观察 / 关注 / 加仓 / 减仓 / 规避"，不允许"立即买入"等
- 涉及个股的内容必须含原文 url 溯源（避免 AI 幻觉）

### 18.4 网络抓取边界

- 单源失败容忍：连续 3 次 5xx 自动暂停 30 分钟
- IP 被封风险：所有 adapter 通过统一 `httpx.AsyncClient` + 共享代理（如配置）+ User-Agent 池
- 未来若被限制，可通过配置接入第三方源聚合服务（如金十、汇通）

### 18.5 实盘交易显式禁令

- BrokerAdapter 接口设计上不暴露 `place_order` 真实实现
- 任何 PR 引入实盘交易代码自动 reject
- 在 README + CONTRIBUTING + CLAUDE.md 三处文档强调

---

## 19. 未来扩展点

### 19.1 后续 Spec 依赖

| Spec | 直接复用本 Spec 的能力 |
|------|---------------------|
| Spec #2 行情数据 + 回测 | DB 框架、配置管理、调度、日志、Streamlit、CLI、健康检查、`market_snapshots` 表、`MarketDataSource` 接口 |
| Spec #3 BrokerAdapter + AI 选股 | `AIProvider` / `ClaudeAgentRunner`、Notifier、可观察性、Phase 2 M9 的 BrokerAdapter 接口 |
| Spec #4 资产配置 + AI Feedback | AI 工作流、用户订阅模型、UI 页面、推送 |

### 19.2 渐进增强清单

| 增强 | 触发条件 | 改造点 |
|------|---------|--------|
| AI 全量增强（每条新闻都过 AI） | 用户反馈摘要价值高、成本可接受 | 调 `news.analysis_filter_threshold` 参数 |
| 增加新闻源 | 发现覆盖盲区 | 写新 `NewsSource` adapter |
| 增加推送渠道（Bark / 邮件富文本） | 用户需要多端覆盖 | 写新 `Notifier` adapter |
| AI 评分混合规则 | 纯规则误报率高 | 改 `AlertService.evaluate()` 加权 |
| 多用户（group use） | 需求出现 | `users` / `subscriptions` 已支持，加身份层 + UI |
| 替换 React 前端 | POC 后期复杂可视化需求 | 不改 API；新增 `frontend/` 项目 |
| 切换 PostgreSQL | 数据量超 5GB 或多用户高并发 | 改 `database_url`；alembic 迁移 |
| 拆分进程（API / Worker / UI） | 部署到云端 | `main.py` 加运行模式参数 |
| 接入 MCP 工具（akshare-mcp、tavily-mcp） | Phase 2 增强 | 在 agent frontmatter 声明 mcps |

---

## 20. 多 Session 开发 + 小组协作

### 20.1 知识沉淀工件清单（沿用 v2 §16）

| 工件 | 角色 | 更新频率 |
|------|------|---------|
| `CLAUDE.md`（项目根） | 项目身份卡 + Session 启动 / 结束 checklist + 命令速查 | 当架构 / 规范 / 命令变化 |
| `docs/PROJECT_STATE.md` | "现在到哪了"快照：当前里程碑、活跃任务、最近决策、阻塞、下一步 | **每次 session 结束** |
| `docs/sessions/YYYY-MM-DD-NN-<topic>.md` | 时间序列日志 | **每次 session 新建一篇** |
| `CHANGELOG.md` | 用户视角的"做了什么"，按里程碑分组 | 当里程碑 / 重要功能上线 |
| `CONTRIBUTING.md` | 🆕 小组协作规范 | 新规则确立时 |
| `CODEOWNERS` | 🆕 模块 owner 映射 | 模块责任变动时 |

### 20.2 Session 启动 / 结束协议

沿用 v2 §16.2/§16.3，CLAUDE.md 已固化。

### 20.3 小组协作

#### 20.3.1 角色分工（来自 Timeline §5，可调）

| 角色 | 主要负责 |
|------|---------|
| **产品负责人** | PRD、模块边界、页面设计、答辩逻辑（如需）、新闻分类与评分模型迭代 |
| **技术负责人** | 系统架构、数据流、UML、技术可行性评估、CI/CD、`adapters/` & `core/` |
| **前端负责人** | POC 页面、Streamlit 面板、页面交互、视觉统一 |
| **策略 / 数据负责人** | 看板信号解释、参数配置边界、规则引擎调优、行情接入 |
| **项目负责人**（兼） | 时间推进、文档整合、最终交付 |
| **AI 协作伙伴**（Claude） | 技术合伙人 + 全栈实现：架构 / 实现 / 测试 / 运维；遇决策点主动询问 |

#### 20.3.2 分支策略

```
main                        # 受保护，需 PR + 1 人 review + CI 通过
├── feat/<member>-<topic>   # 个人功能分支（如 feat/alice-dedup）
├── fix/<member>-<topic>    # bug 修复
├── docs/<member>-<topic>   # 文档
└── chore/<member>-<topic>  # 杂事
```

- 分支命名包含成员名，避免冲突
- 每个分支生命周期 ≤ 5 天，长开发分阶段合并
- 不允许直接 push main
- 不允许 force push main / 长存活分支

#### 20.3.3 Code Review 流程

1. 开发者提 PR，关联 milestone + issue（如有）
2. CI 必须全绿（lint / mypy / pytest）
3. 至少 1 人 review，敏感模块（`adapters/ai/`、`services/news/pusher.py`）需要 2 人
4. PR 描述模板：背景 / 改动 / 风险 / 测试方案
5. Review 评论需 24h 内回复
6. 不允许"自我 approve"

#### 20.3.4 PR 模板

```markdown
## 背景
（这个 PR 解决什么问题，关联哪个 milestone / issue）

## 改动
- 改动 1
- 改动 2

## 风险与回滚
- 风险点 1：xxx，回滚方式：xxx

## 测试
- [ ] 单元测试通过
- [ ] 集成测试通过（如适用）
- [ ] 手动验证步骤：xxx

## Checklist
- [ ] 类型 hint 完整
- [ ] 走 structlog（不用 print/logging）
- [ ] 配置走 YAML，密钥走 .env
- [ ] CHANGELOG 已更新（如适用）
```

#### 20.3.5 CODEOWNERS（草案）

```text
# 全局 fallback
* @projectlead

# 文档
/docs/                       @productlead @projectlead

# 后端
/src/amarket/services/news/  @newsmodule_owner
/src/amarket/services/dashboard/  @dashboard_owner
/src/amarket/services/params/     @configowner
/src/amarket/adapters/ai/    @techowner @claude_assistant
/src/amarket/adapters/notifiers/  @projectlead

# CI / 配置
/.github/                    @techowner
/config/                     @projectlead
/CLAUDE.md                   @projectlead
/CONTRIBUTING.md             @projectlead
```

> **Note**：CODEOWNERS 中的占位符 `@xxx_owner` 在小组成员到位后填实际 GitHub 用户名。

---

## 21. 待小组确认事项

### 21.1 已确认（截至 2026-06-19）

| # | 事项 | 决议 |
|---|------|------|
| ✅1 | 项目升格为小组联合仓库 | 仓库 `dangbuzhudeXNEL/Project_Amarket` 共有；分支策略见 §20.3.2 |
| ✅2 | 以 Peersession PRD 为 Phase 1 主线 | v2 内容降级为 Phase 2 |
| ✅3 | 不赶 6.27 截止 | 按自己节奏交付，但保留 Peersession Timeline 中里程碑结构作为参考 |
| ✅4 | LLM 集成模式 | Phase 1 走 SDK；Phase 2 走 Brainmaster |
| ✅5 | 不做实盘下单 | 永远 |

### 21.2 仍需小组确认

| # | 事项 | 默认 | 何时确认 |
|---|------|------|---------|
| ❓6 | GitHub 用户名 → 角色映射（CODEOWNERS 填充） | 占位符 | M0 启动前 |
| ❓7 | 企微 / 飞书机器人 webhook URL | 占位 | M0 末填 `.env` |
| ❓8 | LLM API key 选型（Anthropic / DeepSeek / 兼用） | 默认 Anthropic 主、DeepSeek 备 | M1 启动前 |
| ❓9 | 静态 POC 是否要框架（Vue / 原生 JS） | 默认原生 + Tailwind via CDN | M3 启动前 |
| ❓10 | 代码许可证 | 暂不加（小组内部） | M0 末 push 远程前 |
| ❓11 | 数据库种子 | 1 admin + 4 个角色样例 + 5 个新闻源 + 3 个行情源 | M0 末 |
| ❓12 | Claude CLI 在 PATH | 验证 `claude --version` 可调（Phase 2 启动前） | M7 启动前 |
| ❓13 | 是否要 Phase 1 中接 Brainmaster（提前到 M3） | 默认不接，Phase 2 才接 | 视进度 |
| ❓14 | 移除 `*.docx` 加入 `.gitignore`？还是保留 Peersession 原始材料？ | **保留**到 `docs/peersession-source/` 归档 | 本 session |

---

## 附录 A：术语表

| 术语 | 解释 |
|------|------|
| Spec | Specification，本系列的设计文档单元 |
| Phase 1 / Phase 2 | 本 Spec 内分两阶段：Phase 1 = Peersession 三大模块；Phase 2 = 原 v2 内容（Brainmaster AI 等） |
| Adapter | 适配器，封装外部依赖的统一接口实现 |
| Service | 业务服务，无状态、纯逻辑、可独立测试 |
| Repository | 数据访问层，封装 ORM 细节 |
| SimHash | 局部敏感哈希算法，用于文本相似度 |
| P0-P3 | 推送告警等级（P0 黑天鹅 / P1 重要 / P2 汇总 / P3 仅入库） |
| Brainmaster 模式 | Python `subprocess` 调 `claude` CLI + agent 文件输出的 AI 集成模式 |
| Breaking | 突发新闻，需立即推送 |
| Premarket | 盘前 |
| 节流（Rate limiting） | 控制单位时间内消息发送次数 |
| 降级链 | 主路径失败时按预定顺序切换到备用方案 |
| Prompt Cache | LLM 调用时复用相同前缀输入，减少计费 |

## 附录 B：参考资料

- Anthropic SDK: <https://docs.anthropic.com/en/api/client-sdks>
- akshare 文档: <https://akshare.akfamily.xyz/>
- 企业微信群机器人: <https://developer.work.weixin.qq.com/document/path/91770>
- 飞书机器人: <https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/bot-v2/bot/events/im.message.receive_v1>
- APScheduler: <https://apscheduler.readthedocs.io/>
- SQLModel: <https://sqlmodel.tiangolo.com/>
- uv: <https://docs.astral.sh/uv/>
- Brainmaster 参考项目: `C:\AI\Claude\Brainmaster`
- Peersession 原始 PRD: `docs/peersession-source/a_share_realtime_news_dashboard_prd.md`
- Peersession Timeline: `docs/peersession-source/a_share_quant_project_timeline.docx`

## 附录 C：v2 → v3 章节映射

| v3 章节 | v2 来源 | 处置 |
|--------|--------|------|
| 1. 背景与目标 | v2 §1 | 改写：愿景调整为 Peersession 主线；新增 Phase 1/2 划分 |
| 2. 范围与非目标 | v2 §2 | 大改：分 Phase 1/2 InScope；显式禁实盘 |
| 3. 关键决策汇总 | v2 §3 | 大改：扩 28 个决策点，含产品 / 技术 / 协作三组 |
| 4. 用户与场景 | （新增） | PRD §1 启发 + 4 角色 |
| 5. 系统架构 | v2 §4 | 改写：分层图扩展，加入三大模块边界 |
| 6. 模块详细设计 | v2 §5 | 大改：16 个 service（v2 是 7 个）+ 多 adapter |
| 7. 数据模型 | v2 §6 | 大改：11+ 张表（v2 是 7 张），新增 events / market / sectors / alerts / reports / source_health / params / audit / config_versions |
| 8. 新闻分类与评分体系 | （新增） | PRD §5/§6 |
| 9. 关键工作流 | v2 §7 | 大改：5 个工作流（实时新闻 / 6 时段日报 / P0-P3 告警 / 板块趋势 / AI 工作流双 Phase） |
| 10. 看板与 API 设计 | （新增） | PRD §8/§9 |
| 11. 参数配置模块 | （新增） | Timeline M5 |
| 12. 配置与密钥管理 | v2 §8 | 适配：增 alert_rules.yml、market_sources.yml、sectors.yml、classification.yml、params_seed.yml |
| 13. 错误处理与可观察性 | v2 §9 | 沿用 + 扩展指标 |
| 14. 测试策略 | v2 §10 | 沿用 + 18 个 case |
| 15. 项目结构 | v2 §11 | 大改：services 按三大模块分包；新增 poc/、market_sources/ |
| 16. 依赖清单 | v2 §12 | 增 akshare/efinance/yfinance、anthropic/openai 移到生产 |
| 17. 实施里程碑 | v2 §13 | 重写：Phase 1 M0-M6 + Phase 2 M7-M9 |
| 18. 安全与合规 | v2 §14 | 沿用 + 强化"不做实盘"显式禁令 |
| 19. 未来扩展点 | v2 §15 | 沿用 + 增 MCP 工具集成 |
| 20. 多 Session 开发 + 小组协作 | v2 §16 | 沿用 + 新增小组协作（分支策略 / PR / CODEOWNERS / 角色分工） |
| 21. 待小组确认事项 | v2 §17 | 重新列 |

---

**文档结束 — Spec v3.0**
