# Project_Amarket

> A 股**新闻分析 + 行情看板**平台 — **小组联合项目**（永远不做实盘下单）

## 项目愿景

构建一个面向**二级市场分析师与交易团队**的 A 股新闻分析与行情看板平台。新闻不是孤立阅读对象，而是行情变化的解释变量和交易情绪的触发器。系统要解决三个问题：

1. 今天发生了什么重要新闻？
2. 这些新闻可能影响哪些指数、板块、个股或风格？
3. 当前行情变化是被新闻驱动，还是技术面 / 资金面 / 情绪面推动？

系统从实时新闻、指数行情、板块表现、个股异动、海外市场和宏观事件中提取**交易相关信号**，形成日报、盘中提醒和前端看板。

## 当前状态

🟢 **Phase 1 实施中（M0/M0+/M1/M2 已完成，准备 M3 静态 POC 页面）**

- 当前 Spec：[Spec #1 v3 — A 股实时新闻分析与行情看板（小组联合版）](docs/superpowers/specs/2026-06-19-spec1-v3-merged.md)
- 状态快照：[`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md)
- 进度：4/7 milestones 完成，端到端 pipeline（采集 → 去重 → 分类 → AI 分析 → P0-P3 告警 → API → Dashboard）已跑通真实数据
- 测试：207 tests / 87.95% coverage / CI 全绿

## 路线图（Phase 1 + Phase 2 + 后续 Spec）

### Spec #1 v3（当前）

| Phase | 范围 | 状态 |
|-------|------|------|
| **Phase 1** | 三大模块（新闻 / 交易看板 / 参数配置）+ 6 时段日报 + P0-P3 告警 + 看板 API | 🟢 **M0/M0+/M1/M2 完成（57%），准备 M3** |
| **Phase 2** | Brainmaster AI 集成（subprocess + claude CLI agent）、信号交易（不下单） | 📋 待 Phase 1 完成 |

### 后续 Spec

| Spec | 范围 | 状态 |
|------|------|------|
| #2 | 行情数据基座 + 回测引擎 | 📋 待启动 |
| #3 | BrokerAdapter + AI 选股策略（仍不实盘） | 📋 待启动 |
| #4 | 资产配置 + AI Feedback | 📋 待启动 |

## 核心能力（Phase 1 完成时）

- 📰 **多源新闻采集**：同花顺 + 东方财富 + 雅虎财经 + 交易所公告 + 央行/证监会/财政部
- 🔁 **三层去重**：URL / 标题 / SimHash + 同事件聚合
- 🏷️ **8 类一级 + 14+ 二级标签**：宏观政策 / 市场行情 / 公司公告 / 海外映射 / 大宗商品 / 风险事件 / 资金流 / 交易提示
- 🧠 **AI 新闻分析**：影响板块 / 相关标的 / 情绪 / 重要性 1-5 / 紧急度 1-5 / 操作提示 / 风险提示
- 📊 **行情快照 + 板块趋势看板**：指数 / 个股 / 板块多源接入，趋势判断（延续 / 分歧 / 退潮 / 反转）
- 📅 **6 时段自动日报**：盘前 / 早盘 / 午间 / 尾盘 / 收盘 / 晚间
- 🚨 **P0-P3 告警**：黑天鹅强提醒 → 即时推 → 汇总推 → 仅入库
- 📬 **多渠道推送**：企业微信 + 飞书 + 邮件
- 🎨 **看板 POC**：静态 HTML（首页 / 新闻流 / 详情页 / 板块热力图 / 日报页）+ Streamlit 管理面板
- ⚙️ **参数配置**：版本化 / 回滚 / 权限矩阵 / 审计日志

## 技术栈

- **语言**：Python 3.11+
- **依赖管理**：[uv](https://docs.astral.sh/uv/)
- **后端**：FastAPI + uvicorn
- **UI**：Streamlit（管理面板）+ 静态 HTML（POC 看板）
- **ORM**：SQLModel + Alembic
- **DB**：SQLite（起步，可平迁 PostgreSQL）
- **调度**：APScheduler
- **行情数据**：akshare / efinance / yfinance
- **AI 集成**：
  - **Phase 1**：Anthropic SDK / DeepSeek SDK（走 API）
  - **Phase 2**：**Brainmaster 模式** — `subprocess` 调 `claude` CLI + `.claude/agents/*.md` 定义 + 文件系统 JSON 输出，零 API key 需求
- **推送渠道**：企业微信群机器人（主）+ 飞书机器人（备）+ 邮件（P0 备用）+ Telegram（Phase 2 stub）
- **日志**：structlog (JSON)
- **指标**：Prometheus client
- **测试**：pytest + pytest-asyncio + pytest-cov

## 项目结构

```
Project_Amarket/
├── CLAUDE.md                # Claude Code 项目记忆（自动加载）
├── README.md                # 本文件
├── CONTRIBUTING.md          # 🆕 小组协作指南
├── CHANGELOG.md             # 变更历史
├── .github/                 # 🆕 GitHub 协作（CODEOWNERS / PR 模板）
├── .claude/                 # Brainmaster 模式：AI 工作负载（Phase 2 启用）
│   ├── agents/              # subprocess 调用的 agent 定义
│   └── commands/            # 用户手动调的 slash commands
├── docs/
│   ├── PROJECT_STATE.md            # 项目"现在到哪了"快照
│   ├── peersession-source/         # 🆕 原始 PRD + Timeline 归档
│   ├── sessions/                   # 每次开发 session 日志
│   ├── adr/                        # 架构决策记录
│   ├── ARCHITECTURE.md             # 系统架构图（M2 交付）
│   ├── UML/                        # UML 图（M7 交付）
│   └── superpowers/
│       ├── specs/                  # 设计文档（v2/v3 并存）
│       └── plans/                  # 实施计划
├── config/                  # YAML 配置（M0 后创建）
├── src/amarket/             # 应用源码（M0 后创建）
│   ├── services/news/       # 新闻模块
│   ├── services/dashboard/  # 看板模块
│   ├── services/params/     # 参数配置模块
│   ├── adapters/            # 外部依赖适配器
│   ├── repositories/        # 数据访问层
│   └── ...
├── poc/                     # 静态 HTML POC（M3 后创建）
├── tests/                   # 测试代码（M0 后创建）
└── scripts/watchdog/        # 外部 watchdog 脚本
```

## 文档导航

| 想了解 | 去哪 |
|--------|------|
| 项目当前在哪 | [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md) |
| 当前 spec | [`docs/superpowers/specs/2026-06-19-spec1-v3-merged.md`](docs/superpowers/specs/2026-06-19-spec1-v3-merged.md) |
| 上一版 spec（v2） | [`docs/superpowers/specs/2026-06-14-news-engine-design.md`](docs/superpowers/specs/2026-06-14-news-engine-design.md) |
| 小组协作规范 | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| Claude 协作约定 | [`CLAUDE.md`](CLAUDE.md) |
| 历次 session | [`docs/sessions/`](docs/sessions/) |
| 变更日志 | [`CHANGELOG.md`](CHANGELOG.md) |
| 原始 PRD（小组成员撰写） | [`docs/peersession-source/`](docs/peersession-source/) |

## 协作模式

本项目为 **小组 + AI 多 session 协作开发**：

- 多名小组成员（产品 / 技术 / 前端 / 策略 / 项目负责人）
- AI 协作伙伴（Claude / Claude Code）作为团队一员
- 严格 PR 流程 + 至少 1 人 review（敏感模块 2 人）
- 每次 session 末更新知识沉淀工件（PROJECT_STATE / sessions/ / CHANGELOG）

详细规范见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。

## 快速开始

**完整指南**：[`docs/LOCAL_DEPLOYMENT.md`](docs/LOCAL_DEPLOYMENT.md)（含故障排查、`.env` 每项说明、端到端验证）

**速记版本**：
```bash
# 1. clone + 装 uv（详见上面链接）
git clone https://github.com/dangbuzhudeXNEL/Project_Amarket.git
cd Project_Amarket

# 2. 装依赖 + 初始化 DB
uv sync --dev
uv run alembic upgrade head

# 3. 配置 .env（可先留空）
cp .env.example .env

# 4. 跑测试
uv run pytest -x

# 5. 启动
./start.bat                 # Windows
./start.sh                  # Linux/macOS
```

启动后访问：
- API docs: http://127.0.0.1:8080/docs
- Healthz: http://127.0.0.1:8080/healthz
- Dashboard: http://127.0.0.1:8501

## 安全与合规

- **永远不做实盘下单**（任何 PR 引入实盘下单代码自动 reject）
- 仅小组内部 / 学习用途；不对外二次分发
- 所有推送内容附"📌 本信息仅供个人/小组学习参考，不构成任何投资建议"
- 网络抓取遵守 robots.txt + 限流（< 1 req/s/source）
- 所有密钥走 `.env`（已 gitignore）；PAT 等敏感凭据走 `PAT.txt`（已 gitignore）

## License

待定（小组内部项目）。任何外部分发前必须先确认 LICENSE。

---

🤖 本项目使用 [Claude Code](https://claude.com/claude-code) 作为 AI 协作伙伴共同开发
