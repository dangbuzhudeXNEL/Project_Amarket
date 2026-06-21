# Contributing to Project_Amarket

> 本文档面向小组成员（包括 AI 协作伙伴 Claude）。新成员请先读完本文后再提第一个 PR。

---

## 1. 项目身份回顾

- **项目**：Project_Amarket — A 股新闻分析 + 行情看板平台（**永远不做实盘下单**）
- **当前阶段**：Phase 1（Peersession 三大模块：新闻 / 看板 / 参数配置）
- **当前 Spec**：[`docs/superpowers/specs/2026-06-19-spec1-v3-merged.md`](docs/superpowers/specs/2026-06-19-spec1-v3-merged.md)
- **状态快照**：[`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md)
- **下次会议接力点**：[`docs/sessions/`](docs/sessions/) 最新一篇

---

## 2. 上手 (Onboarding) — 30 分钟内跑通

**👉 详细分步指南见 [`docs/LOCAL_DEPLOYMENT.md`](docs/LOCAL_DEPLOYMENT.md)**，包含：
- 装 uv / Python 的细节
- `.env` 每一项的用途
- 启动验证 checklist
- 12 种常见故障的排查

**速记 6 步版本**（适合已经搭过的成员复习）：

```bash
# 1. clone
git clone https://github.com/dangbuzhudeXNEL/Project_Amarket.git
cd Project_Amarket

# 2. 装 uv（如果还没有）
# Windows: irm https://astral.sh/uv/install.ps1 | iex
# macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. 安装依赖
uv sync --dev

# 4. 配置 .env（可全留空，能跑）
cp .env.example .env

# 5. 初始化 DB + 跑测试
uv run alembic upgrade head
uv run pytest -x

# 6. 启动
./start.bat    # Windows
./start.sh     # Linux/macOS
```

如果到第 6 步还没跑通，**先在群里说 + 贴报错**，不要憋着调一下午。

---

## 3. 分支策略

```
main                        # 受保护，需 PR + 1 人 review + CI 通过
├── feat/<member>-<topic>   # 个人功能分支（如 feat/alice-news-dedup）
├── fix/<member>-<topic>    # bug 修复
├── docs/<member>-<topic>   # 文档
└── chore/<member>-<topic>  # 杂事
```

**规则**：
- 分支名包含成员标识，避免冲突
- 每个分支生命周期 ≤ 5 天；长开发请分阶段合并
- **不允许直接 push main**
- **不允许 force push main 或长存活分支**
- PR 合并方式：默认 `Squash and merge`（保持 main 历史干净）

---

## 4. 提交（Commit）规范

Conventional Commits 简化版：

```
<type>(<scope>): <subject>
```

`<type>`：
- `feat` 新功能
- `fix` 修 bug
- `docs` 文档
- `chore` 杂事（依赖更新、配置改动）
- `refactor` 重构（无新功能 / 无 bug 修复）
- `test` 测试
- `perf` 性能
- `style` 格式（不影响功能）
- `arch` 架构调整（v2/v3 升级这种）
- `session` Session 收尾 commit（每次 session 末固定写）

`<scope>` 可选，用模块名：`news_collector` / `dashboard_api` / `ai_service` / `params_module` / 等。

示例：
- `feat(news_collector): add ths adapter`
- `fix(deduper): correct simhash threshold edge case`
- `docs(spec): merge peersession prd into v3`
- `session(2026-06-19-03): merge peersession prd → spec v3`

**规则**：
- 不允许 `--amend` 已 push 的 commit（除非用户/小组成员明确同意）
- commit message 中文 / 英文均可，但 `<type>` 用英文
- **commit 前**：先 `uv run ruff check .` + `uv run pytest -x`，CI 红的 PR 不能合

---

## 5. Pull Request 流程

1. 在分支上完成开发 + 测试
2. push 分支到远程
3. `gh pr create` 创建 PR，关联 milestone / issue
4. **PR 描述**用 [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md) 默认模板
5. 等 CI 全绿
6. 至少 **1 人 review**（敏感模块需要 **2 人**，详见 §6）
7. Reviewer 评论 24h 内回复
8. 合并：`Squash and merge`，commit message 沿用 PR 标题

**禁止**：
- 自我 approve 后合并
- CI 红的 PR 合并
- review 评论未解决就合并

---

## 6. 敏感模块（需 2 人 review）

| 路径 | 原因 |
|------|------|
| `src/amarket/adapters/ai/` | AI 调用、外部 API、密钥操作 |
| `src/amarket/services/news/pusher.py` | 直接对外推送，错了误打扰用户 |
| `src/amarket/services/params/` | 参数变更影响全系统 |
| `src/amarket/adapters/notifiers/` | 推送渠道 |
| `config/` | 全局配置 |
| `.env.example` | 密钥模板 |
| `scripts/watchdog/` | 系统自愈逻辑 |
| `src/amarket/db/migrations/` | DB 迁移（不可逆操作） |

CODEOWNERS 已自动 request reviewer，必要时手动 @ 其他成员。

---

## 7. 编码规范（强制）

详见 [`CLAUDE.md`](CLAUDE.md) §"编码规范（强制）"。摘要：

1. **类型注解必加**（所有 public 函数 / 方法的参数和返回值）
2. **日志走 structlog**（禁止 `print()`、禁止标准库 `logging`）
3. **密钥禁止硬编码**（走 `.env`）
4. **配置走 YAML + Pydantic**（走 `config/*.yml`）
5. **依赖倒置**（Service 层只依赖 `adapters/*/base.py` 接口）
6. **AI 集成走统一接口**（Phase 1 `AIProvider` / Phase 2 `ClaudeAgentRunner`，禁止直接 `subprocess.run` 调 `claude` / 禁止直接 SDK 调用）
7. **测试优先**（写 Service 前先想清楚怎么测）
8. **`commit` 走规范**（见 §4）
9. **不允许 amend 已 push 的 commit**

Lint / 类型检查命令：

```bash
uv run ruff check .
uv run ruff format .
uv run mypy src/
```

---

## 8. 测试要求

| 阶段 | 要求 |
|------|------|
| 提交 PR 前 | 至少 `pytest -x` 通过 + 新增功能有单元测试 |
| Merge 到 main 前 | CI 全绿，覆盖率不低于 70% |
| 每个 milestone | 集成测试通过 + 人工 demo |

更多细节见 [Spec v3 §14 测试策略](docs/superpowers/specs/2026-06-19-spec1-v3-merged.md#14-测试策略)。

---

## 9. 文档协议（多 Session 知识沉淀）

每次开发 session（人 + AI 协作）**结束前**必须：

1. 更新 [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md)（"现在到哪了"快照）
2. 新建 `docs/sessions/YYYY-MM-DD-NN-<topic>.md`（本次日志）
3. 如有里程碑变化，更新 [`CHANGELOG.md`](CHANGELOG.md)
4. `git add` 相关文件 + `commit` 走规范
5. `git push origin <branch>`

**绝不允许**在没有走完 1-5 的情况下结束 session。即使时间紧也要把 1-3 至少快速 hash 完。

文档驻地：

| 想知道什么 | 去哪 |
|----------|------|
| 项目当前在哪个阶段 | `docs/PROJECT_STATE.md` |
| 历次 session 干了什么 | `docs/sessions/` |
| 当前 spec | `docs/superpowers/specs/2026-06-19-spec1-v3-merged.md` |
| 重大架构决策 | `docs/adr/`（按需新建） |
| 系统架构图 | `docs/ARCHITECTURE.md`（M2 交付后） |
| UML 时序图 | `docs/UML/`（M7 交付后） |
| Peersession 原始素材 | `docs/peersession-source/` |
| 实施计划 | `docs/superpowers/plans/`（按 spec 拆分） |

---

## 10. AI 协作伙伴（Claude）约定

Project_Amarket 是 **人 + AI 协作** 项目。AI 协作伙伴（Claude / Claude Code）作为团队一员，遵守下列约定：

1. **每次 session 启动** Claude 必须走 [`CLAUDE.md`](CLAUDE.md) 顶部的 Session 启动 Checklist
2. **每次 session 结束** Claude 必须走 Session 结束 Checklist（更新 PROJECT_STATE、写 session log、commit）
3. **遇到决策点主动询问** 用户 / 小组，不擅自定方向（架构 / 范围 / 接口）
4. **不绕过 PR 流程** 即便 Claude 也是按分支 → PR → review → merge 走
5. **不写未经审阅的 spec 改动** spec 改动要 PR 化让小组审

---

## 11. 合规与安全 reminder

- ❌ 不要把任何 API key / token / webhook 写进代码
- ❌ 不要 commit `.env`、`PAT.txt`、`data/`、`logs/`
- ❌ 不要在代码里加 **真实下单** 路径（即使是 stub 也不许）
- ❌ 不要在推送内容里写"立即买入 / 立即卖出"等明确操作指令
- ✅ 所有推送末尾固定附加："📌 本信息仅供个人/小组学习参考，不构成任何投资建议"
- ✅ 所有抓取遵守 robots.txt + < 1 req/s/source

---

## 12. 出现问题怎么办

| 问题 | 联系 / 操作 |
|------|-----------|
| CI 失败看不懂 | 在 PR 里 `@` 技术负责人 |
| 测试本地通过 CI 红 | 看 CI 日志；多半是依赖 / 时区 / 环境变量；问技术负责人 |
| 想改 spec 部分内容 | 提 `docs/<member>-spec-update` 分支 PR，至少产品 + 技术 2 人 review |
| 想改架构（如新增模块 / 改技术选型） | 先写 ADR（`docs/adr/YYYY-MM-DD-<topic>.md`），群里讨论；不要直接动手 |
| 紧急 bug（线上影响） | 直接在群里 @ 当值人；fix 分支直走 main hotfix |
| 安全问题（暴露密钥 / 误推送数据） | 立刻在群里说，**不要先 commit**；技术负责人决定撤回方式 |

---

## 13. License

待定（小组内部项目，暂未选择许可证；任何外部分发前必须先确认 LICENSE）。

---

**Last updated**: 2026-06-19  
**Maintainers**: 见 [`.github/CODEOWNERS`](.github/CODEOWNERS)
