# CLAUDE.md — Project_Amarket 项目记忆

> 这是 Claude Code **自动加载**的项目级记忆文件。每次新 session 打开此项目时，你（Claude）会首先读到本文件。请严格按下面的 **Session 启动 checklist** 走，确保接得住前面 session 的进度。

---

## 项目身份卡

**项目名**：Project_Amarket
**愿景**：A股量化 + 新闻一体化系统（个人自用 + 学习，预留 group use 扩展）
**当前阶段**：Spec #1（基础设施 + 新闻引擎）设计完成，准备进入 writing-plans 阶段
**整体路线图**：4 个 Spec 串行交付
- Spec #1 ⏳ 进行中：通用基础设施 + 新闻引擎（盘前 + Breaking 推送）
- Spec #2 📋 待启动：行情数据基座 + 回测引擎
- Spec #3 📋 待启动：BrokerAdapter + AI 选股策略
- Spec #4 📋 待启动：资产配置 + AI Feedback

**主语言**：Python 3.11+
**运行环境**：本地 Windows 开发机 `C:\AI\Claude\Project_Amarket`
**AI 集成模式**：**Brainmaster 模式** — Python 通过 `subprocess` 调用 `claude` CLI，agent 定义在 `.claude/agents/*.md`，输出走文件系统 JSON。零 API 成本，复用用户 Claude Code 订阅。

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
| 设计方案 / spec | `docs/superpowers/specs/` |
| 实施计划 | `docs/superpowers/plans/`（writing-plans 阶段后会有） |
| 项目当前状态 | `docs/PROJECT_STATE.md` |
| 历次 session 日志 | `docs/sessions/` |
| 重大架构决策 | `docs/adr/`（按需创建） |
| 用户视角的变更历史 | `CHANGELOG.md` |
| 配置文件示例 | `config/` 和 spec 的 Section 8 |

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
6. **AI 集成走 ClaudeAgentRunner**：Service 层禁止直接 `subprocess.run` 调 `claude`；统一走 `ClaudeAgentRunner` adapter；agent 输出严格校验
7. **测试优先**：写 Service 前先写它的单元测试骨架（不强制 TDD，但要先想好怎么测）
8. **commit 信息**：`<type>(<scope>): <subject>` 格式（如 `feat(news_collector): add cls adapter`）；中文/英文都行，但 type 用英文
9. **不允许 amend commits**：除非用户明确要求

---

## 项目约束

- **个人自用**：MVP 阶段不做认证；架构预留 `user_id` 字段
- **信号 + 模拟优先**：BrokerAdapter 接口必须有，但 MVP 只实现 `SignalOnly` 和 `Paper`，不接实盘
- **本地优先**：所有功能必须能在用户的开发机上跑通；不假设有公网部署
- **故障隔离**：任一新闻源/LLM/推送渠道故障不能拖垮整体
- **可观察性内建**：Prometheus metrics + `/healthz` + 结构化日志，从 day 1 就要有

---

## 当前已知的"不要做"列表（YAGNI）

- ❌ 消息队列（Redis/Kafka）—— APScheduler in-process 够用
- ❌ 微服务拆分 —— 单体 + 清晰模块边界
- ❌ React 前端 —— Streamlit 起步
- ❌ 用户认证 —— 单用户配置文件
- ❌ Docker / K8s —— MVP 本地常驻
- ❌ 全量新闻过 AI —— 只对盘前汇总用 AI（breaking 走纯规则）
- ❌ Anthropic SDK 直接调用 —— 走 Claude Code agent (Brainmaster 模式)
- ❌ API key for LLM —— 用 Claude CLI subprocess 即可

如果未来这些限制要打破，**先写 ADR**（`docs/adr/`），再动手。

---

## 协作模式说明

- **用户角色**：产品 owner + 最终决策者；提供方向、领域知识、合规判断、关键数据源访问
- **Claude 角色**：技术合伙人 / 全栈开发；提供架构、实现、测试、运维；遇到决策点要主动询问，不擅自定方向
- **多 session 接力**：每次 session 都可能是不同的 Claude 实例 → 严格依赖 PROJECT_STATE.md + session log 接续上下文

---

## 链接

- 当前 Spec：[docs/superpowers/specs/2026-06-14-news-engine-design.md](docs/superpowers/specs/2026-06-14-news-engine-design.md)
- 项目状态：[docs/PROJECT_STATE.md](docs/PROJECT_STATE.md)
- 变更日志：[CHANGELOG.md](CHANGELOG.md)
- GitHub: https://github.com/dangbuzhudeXNEL/Project_Amarket
