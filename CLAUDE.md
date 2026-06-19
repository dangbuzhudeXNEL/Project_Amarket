# CLAUDE.md — Project_Amarket 项目记忆

> 这是 Claude Code **自动加载**的项目级记忆文件。每次新 session 打开此项目时，你（Claude）会首先读到本文件。请严格按下面的 **Session 启动 checklist** 走，确保接得住前面 session 的进度。

---

## 项目身份卡

**项目名**：Project_Amarket
**性质**：**小组联合项目** — 多人协作（含 AI 协作伙伴 Claude）
**愿景**：A 股**新闻分析 + 行情看板**平台 — 永远不做实盘下单
**当前阶段**：Spec #1 **v3**（小组联合版，融合 Peersession PRD）设计完成，准备启动 Phase 1 M0
**整体路线图**：

### Spec #1 v3（当前，双阶段串行）

- **Phase 1** ⏳ 即将启动：三大模块（新闻 / 交易看板 / 参数配置）+ 6 时段日报 + P0-P3 告警 + 看板 API（M0-M6）
- **Phase 2** 📋 待 Phase 1 完成：Brainmaster AI 集成（subprocess + claude CLI agent）+ 信号交易（M7-M9）

### 后续 Spec

- Spec #2 📋 待启动：行情数据基座 + 回测引擎
- Spec #3 📋 待启动：BrokerAdapter + AI 选股策略（仍不实盘）
- Spec #4 📋 待启动：资产配置 + AI Feedback

**主语言**：Python 3.11+
**运行环境**：本地 Windows 开发机 `C:\AI\Claude\Project_Amarket`
**仓库**：https://github.com/dangbuzhudeXNEL/Project_Amarket (Public，小组共有)

**AI 集成模式**（双 Phase）：

| Phase | 模式 | 是否需要 API key |
|-------|------|----------------|
| **Phase 1** | 通过 `AIProvider` 接口走 SDK（Anthropic / DeepSeek 走 API） | ✅ 需要 |
| **Phase 2** | **Brainmaster 模式** — `subprocess` 调 `claude` CLI + `.claude/agents/*.md` + JSON 文件输出 | ❌ 零 API 成本（复用 Claude Code 订阅） |

---

## 🔴 Session 启动 Checklist（每次必走，按顺序）

```
1. 读 CLAUDE.md（本文件）
2. 读 docs/PROJECT_STATE.md            ← 必读：现在到哪了
3. 读 docs/sessions/ 最新一篇          ← 必读：上次干了啥，下次接力点
4. 跑 git log --oneline -10            ← 看最近提交
5. 跑 git status                       ← 看工作区状态
6. （可选）gh pr list                  ← 看在做的 PR
```

完成 1-5 后再开始本 session 的工作。如果用户给了具体任务，先确认任务和当前阶段是否吻合。

---

## 🟢 Session 结束 Checklist（每次必走）

```
1. 更新 docs/PROJECT_STATE.md                            ← 更新当前状态
2. 新建 docs/sessions/YYYY-MM-DD-NN-<topic>.md           ← 写本次 session 日志
3. 如有里程碑变化，更新 CHANGELOG.md
4. git add 相关文件 && git commit -m "session: <topic>"
5. git push origin main
```

**绝不允许在没有走完 1-5 的情况下结束 session。** 即使用户说"好了今天就这样"，也要主动说："我把今天的进度沉淀一下再结束"，然后跑完 checklist。

---

## 关键路径速查

### 文档地图（去哪找什么）

| 想知道什么 | 去哪 |
|----------|------|
| 当前 spec | `docs/superpowers/specs/2026-06-19-spec1-v3-merged.md`（v3，**主**） |
| 上一版 spec | `docs/superpowers/specs/2026-06-14-news-engine-design.md`（v2，**历史**） |
| Peersession 原始素材（小组成员撰写） | `docs/peersession-source/` |
| 实施计划 | `docs/superpowers/plans/` |
| 项目当前状态 | `docs/PROJECT_STATE.md` |
| 历次 session 日志 | `docs/sessions/` |
| 重大架构决策 | `docs/adr/`（按需创建） |
| 用户视角的变更历史 | `CHANGELOG.md` |
| 小组协作规范 | `CONTRIBUTING.md` |
| 模块 owner / review 责任 | `.github/CODEOWNERS` |
| PR 模板 | `.github/PULL_REQUEST_TEMPLATE.md` |
| 系统架构图 | `docs/ARCHITECTURE.md`（M2 交付后） |
| UML / 时序图 | `docs/UML/`（M7 交付后） |
| 配置文件示例 | `config/` 和 spec v3 §12 |

### 开发命令速查（M0 完成后填充）

```bash
# 安装依赖
uv sync

# 启动服务（FastAPI + Streamlit + APScheduler）
./start.bat           # Windows
./start.sh            # Linux/macOS

# 测试
uv run pytest -x                       # 跑所有测试，遇错即停
uv run pytest --cov=src --cov-report=term-missing  # 带覆盖率
uv run pytest -k "test_news_collector"             # 跑特定测试

# Lint / Type check
uv run ruff check .
uv run ruff format .
uv run mypy src/

# 数据库迁移
uv run alembic upgrade head            # 应用迁移
uv run alembic revision --autogenerate -m "msg"  # 生成新迁移

# 手动触发（CLI）
uv run amarket push premarket          # 手动触发盘前推送（debug 用）
uv run amarket healthcheck             # 健康检查

# Streamlit UI
uv run streamlit run src/amarket/ui/app.py --server.port 8501
```

---

## 编码规范（强制）

1. **类型注解必加**：所有 public 函数/方法的参数和返回值必须有 type hints
2. **日志走 structlog**：禁止 `print()`；禁止使用标准库 `logging` 模块（已被 structlog 取代）
3. **密钥禁止硬编码**：所有 API key / webhook URL 走 `.env`，代码里只用 env var 名
4. **配置走 YAML + Pydantic**：所有可调参数走 `config/*.yml`，加载用 `pydantic-settings`
5. **依赖倒置**：Service 层禁止 import Adapter 实现，只 import `adapters/*/base.py` 中的接口
6. **AI 集成走统一接口**：Service 层只调用 `AIProvider` 接口；Phase 1 实现走 `AnthropicSDKProvider` / `DeepSeekSDKProvider`；Phase 2 实现走 `ClaudeAgentRunner`（subprocess + JSON 校验）；**禁止**在 Service 里直接 `subprocess.run` 或直接 SDK 调用
7. **测试优先**：写 Service 前先写它的单元测试骨架（不强制 TDD，但要先想好怎么测）
8. **commit 信息**：`<type>(<scope>): <subject>` 格式（如 `feat(news_collector): add ths adapter`）；中文/英文都行，但 type 用英文
9. **不允许 amend commits**：除非小组明确要求
10. **不允许直接 push main**：所有改动走 PR，详见 `CONTRIBUTING.md` §3-§5
11. **不允许引入实盘下单代码**：BrokerAdapter 永远只到 SignalOnly / Paper

---

## 项目约束

- **小组内部使用**：当前不做对外认证；架构预留 `user_id` + `role`（admin/analyst/trader/guest）字段
- **永远不做实盘下单**：BrokerAdapter 仅到 `SignalOnly` 和 `Paper` 两层；任何 PR 引入实盘交易代码自动 reject
- **本地优先**：所有功能必须能在小组成员开发机上跑通；不假设有公网部署
- **故障隔离**：任一新闻源 / 行情源 / AI / 推送渠道故障不能拖垮整体
- **可观察性内建**：Prometheus metrics + `/healthz` + 结构化日志，从 day 1 就要有
- **AI 不可幻觉**：所有 AI 输出必须有原文链接溯源、置信度评分、降级路径

---

## 当前已知的"不要做"列表（YAGNI）

- ❌ **实盘下单**（任何阶段都不做）
- ❌ 消息队列（Redis/Kafka）—— APScheduler in-process 够用
- ❌ 微服务拆分 —— 单体 + 清晰模块边界
- ❌ React 前端 —— Phase 1 用静态 HTML POC + Streamlit；React 留 future
- ❌ 用户认证 —— Phase 1 单角色，预留 `user_id` + `role`
- ❌ Docker / K8s —— MVP 本地常驻
- ❌ 全量新闻过 AI —— 按 importance + urgency 过滤后才过 AI
- ❌ 直接 `subprocess.run` 调 `claude` —— 走 `ClaudeAgentRunner` adapter（Phase 2）
- ❌ 直接 SDK 调用 —— 走 `AIProvider` 接口（Phase 1+2）
- ❌ 直接 push main —— 走 PR 流程

如果未来这些限制要打破，**先写 ADR**（`docs/adr/`），再动手。

---

## 协作模式说明

### 小组成员角色（详见 `CONTRIBUTING.md` 和 spec v3 §20.3）

- **产品负责人**：PRD、模块边界、页面设计、新闻分类与评分模型迭代
- **技术负责人**：系统架构、数据流、UML、CI/CD、`adapters/` & `core/`
- **前端负责人**：POC 页面、Streamlit 面板、视觉统一
- **策略 / 数据负责人**：看板信号、参数边界、规则引擎调优、行情接入
- **项目负责人**（可兼）：时间推进、文档整合、最终交付

### AI 协作伙伴（Claude）

- 角色：技术合伙人 / 全栈开发 / 文档合伙人
- 提供：架构、实现、测试、运维、spec 起草
- 约束：
  - 遇决策点**主动询问**用户 / 小组，不擅自定方向
  - 不绕过 PR 流程
  - 不写未经审阅的 spec 改动
  - 不引入实盘下单代码
  - 严格走 Session 启动 / 结束 Checklist

### 多 Session 接力

每次 session 都可能是不同的 Claude 实例 → 严格依赖 `PROJECT_STATE.md` + `sessions/` + `CHANGELOG.md` 接续上下文。

### Superpowers 工具的使用原则

不是每个任务都需要走 superpowers 流程。指南：

- **简单规划**（小改、单文件、思路明确）→ 用原生 `/plan` 或直接 TaskCreate 跟踪
- **复杂任务**（多文件、跨模块、需要 brainstorming）→ 用 superpowers 对应技能
- **关键决策**（架构 / 范围 / 接口）→ 不论简单复杂都要用 `superpowers:brainstorming` 走一遍
- **打算实施代码**（多步、需 review）→ 用 `superpowers:writing-plans` 出实施计划
- **写代码** → 用 `superpowers:test-driven-development`（如果适用）
- **完工自审** → 用 `superpowers:verification-before-completion`

---

## 链接

- **当前 Spec (v3)**：[docs/superpowers/specs/2026-06-19-spec1-v3-merged.md](docs/superpowers/specs/2026-06-19-spec1-v3-merged.md)
- 上一版 Spec (v2，历史)：[docs/superpowers/specs/2026-06-14-news-engine-design.md](docs/superpowers/specs/2026-06-14-news-engine-design.md)
- 项目状态：[docs/PROJECT_STATE.md](docs/PROJECT_STATE.md)
- 变更日志：[CHANGELOG.md](CHANGELOG.md)
- 小组协作规范：[CONTRIBUTING.md](CONTRIBUTING.md)
- 模块 owner：[.github/CODEOWNERS](.github/CODEOWNERS)
- PR 模板：[.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md)
- Peersession 原始素材：[docs/peersession-source/](docs/peersession-source/)
- GitHub: https://github.com/dangbuzhudeXNEL/Project_Amarket
