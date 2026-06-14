# Project_Amarket

> A股量化 + 新闻一体化系统（个人自用 + 学习项目，预留 group use 扩展）

## 项目愿景

构建一个 A 股量化 + 新闻一体化系统，覆盖：

- 📰 **盘前新闻智能推送**（每个工作日 08:30 一次集中汇总）
- ⚡ **盘中 Breaking news 实时推送**（高优来源 + 关键词命中规则）
- 📊 **A 股 / ETF 量化选股**（多策略 + AI Agent 决策）
- 🔁 **历史回测**
- 🤖 **AI Feedback / 策略复盘**
- 💼 **资产配置与风险管理**

## 当前状态

🟡 **Spec #1 设计完成，准备进入实施计划阶段**

详见 [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md)。

## 路线图（4 个 Spec 串行交付）

| Spec | 范围 | 状态 |
|------|------|------|
| #1 | 通用基础设施 + 新闻引擎 | ⏳ 设计完成 |
| #2 | 行情数据基座 + 回测引擎 | 📋 待启动 |
| #3 | BrokerAdapter + AI 选股策略 | 📋 待启动 |
| #4 | 资产配置 + AI Feedback | 📋 待启动 |

## 技术栈（计划）

- **语言**：Python 3.11+
- **依赖管理**：uv
- **后端**：FastAPI + uvicorn
- **UI**：Streamlit（起步）
- **ORM**：SQLModel + Alembic
- **DB**：SQLite（起步，未来可平迁 PostgreSQL）
- **调度**：APScheduler
- **AI 集成**：**Brainmaster 模式** — `subprocess` 调 `claude` CLI + `.claude/agents/*.md` 定义 + 文件系统 JSON 输出，零 API key 需求
- **推送**：企业微信群机器人（主） + Telegram Bot（预留）
- **新闻源**：财联社 + 东方财富 7x24 + 新浪 7x24 + 华尔街见闻
- **日志**：structlog (JSON)
- **指标**：Prometheus client
- **测试**：pytest + pytest-asyncio + pytest-cov

## 项目结构

```
Project_Amarket/
├── CLAUDE.md                  # Claude Code 项目记忆（自动加载）
├── README.md                  # 本文件
├── CHANGELOG.md               # 变更历史
├── .claude/                   # Brainmaster 模式：AI 工作负载
│   ├── agents/                # Python subprocess 调用的 agent 定义
│   │   └── news-analyst.md
│   └── commands/              # 用户可手动调用的 slash commands
│       └── test-premarket.md
├── docs/
│   ├── PROJECT_STATE.md       # 项目"现在到哪了"快照
│   ├── sessions/              # 每次开发 session 的日志
│   ├── adr/                   # 架构决策记录
│   └── superpowers/
│       ├── specs/             # 设计文档
│       └── plans/             # 实施计划
├── config/                    # YAML 配置（M0 实施时创建）
├── src/amarket/               # 应用源码（M0 实施时创建）
├── tests/                     # 测试代码（M0 实施时创建）
└── scripts/watchdog/          # 外部 watchdog 脚本
```

## 文档导航

- [`CLAUDE.md`](CLAUDE.md) — Claude Code 自动加载的项目记忆 + 新 session 启动 checklist
- [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md) — 当前状态快照
- [`docs/superpowers/specs/2026-06-14-news-engine-design.md`](docs/superpowers/specs/2026-06-14-news-engine-design.md) — Spec #1 设计文档
- [`docs/sessions/`](docs/sessions/) — 历次开发 session 日志
- [`CHANGELOG.md`](CHANGELOG.md) — 变更日志

## 开发模式

本项目为 **多 session 协作开发**：用户 + Claude Code（多次 session）一起推进。每次 session 末必须：
1. 更新 `docs/PROJECT_STATE.md`
2. 写一篇 `docs/sessions/YYYY-MM-DD-NN-<topic>.md`
3. 必要时更新 `CHANGELOG.md`
4. commit + push

详见 [`CLAUDE.md`](CLAUDE.md) 的 Session 启动/结束 Checklist。

## 安全与合规

- 仅个人自用 / 学习用途
- 所有推送内容附"仅供个人学习参考，不构成投资建议"
- 网络抓取遵守 robots.txt + 限流（< 1 req/s/source）
- 所有密钥走 `.env`（已 gitignore）；PAT 等敏感凭据走 `PAT.txt`（已 gitignore）

## License

待定（个人项目，暂未选择许可证）

---

🤖 本项目使用 [Claude Code](https://claude.com/claude-code) 协作开发
