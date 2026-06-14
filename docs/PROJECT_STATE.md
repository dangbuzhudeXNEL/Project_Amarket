# Project State

**Last Updated**: 2026-06-14 (Session 01 — brainstorm + spec + Brainmaster pattern adoption)
**Updated By**: Claude (opus-4.7) + User

---

## 当前阶段

- **Spec**: #1 — 通用基础设施 + 新闻引擎 MVP
- **Phase**: 🟡 **Design v2 complete (Brainmaster pattern adopted), awaiting user spec review** → 然后进入 writing-plans 阶段
- **Milestone**: 尚未开始 M0
- **Sprint progress**: 0/7 milestones started

---

## 活跃任务

| ID | 任务 | Owner | 状态 |
|----|------|-------|------|
| - | 审阅 spec v2（已加入 Brainmaster 模式） | user | ⏳ pending |
| - | 调用 superpowers:writing-plans 撰写实施计划（spec 通过后） | claude | 📋 待启动 |

---

## 最近 4 个关键决策（按时间倒序）

1. **2026-06-14 (晚)**：**采纳 Brainmaster 模式**接入 AI — Python `subprocess` 调 `claude` CLI，agent 定义在 `.claude/agents/*.md`，输出走 JSON 文件。**完全不需要 API key**。原设计中的 Anthropic SDK 路径降级为可选 Tier 2 fallback（MVP 不启用）。
2. **2026-06-14**：采用"知识沉淀机制"支持多 session 开发
3. **2026-06-14**：首期 MVP = Spec #1（基础设施 + 新闻引擎）
4. **2026-06-14**：4 个 Spec 串行交付而非并行

完整决策清单详见 spec 的 Section 3。

---

## 阻塞 / 待用户输入

无硬阻塞。下列事项可在 M0 实施过程中并行确认（参考 spec Section 17）：

- 验证 `claude --version` 在 Git Bash 中可调用（用户已用 Claude Code，应该 OK）
- 业务推送 + 告警的企微机器人 webhook（用户创建后填 `.env`）
- 代码许可证选择
- 数据库种子数据是否调整

---

## 下一步

### 立即（本 session 末）
1. ⏳ Commit + push 架构调整变更
2. ⏳ 更新 session log
3. ⏳ 等待用户审阅 spec v2

### 用户审阅通过后（下次 session 开头）
4. 调用 `superpowers:writing-plans` 撰写 Spec #1 的实施计划（M0-M6 拆解为可执行任务）
5. 用户审阅实施计划
6. 进入 M0 实施

### M0 启动 checklist（实施开始前）
- [ ] 用户验证 `claude --version` 在 PATH 里
- [ ] 用户创建 2 个企微机器人，把 webhook URL 写入 `.env`
- [ ] 选定代码许可证

---

## 重要环境/配置变化

| 时间 | 变化 |
|------|------|
| 2026-06-14 | 项目初始化：git init main / .gitignore / spec 写入 |
| 2026-06-14 | PAT.txt 加入 .gitignore 保护 |
| 2026-06-14 | spec 自审修订（修复模型 id 不一致等问题） |
| 2026-06-14 | spec 新增 Section 16 多 Session 开发支持 |
| 2026-06-14 | 知识沉淀工件 v1（CLAUDE.md / PROJECT_STATE.md / CHANGELOG.md / sessions/） |
| 2026-06-14 | GitHub repo 创建 + 首推 |
| 2026-06-14 | **架构调整：采纳 Brainmaster 模式** — Spec §3/5/7/8/11/12/13/17 重写；新建 `.claude/agents/news-analyst.md` 和 `.claude/commands/test-premarket.md` |

---

## 文档地图

| 文档 | 用途 |
|------|------|
| `CLAUDE.md` | 项目根入口，新 session 必读 |
| `docs/PROJECT_STATE.md` | 本文件，项目"现在到哪了" |
| `docs/sessions/*.md` | 每次开发 session 的日志 |
| `docs/superpowers/specs/` | 设计文档 |
| `docs/superpowers/plans/` | 实施计划（writing-plans 阶段后会有） |
| `docs/adr/` | 架构决策记录（按需创建） |
| `CHANGELOG.md` | 用户视角的"做了什么" |
| `.claude/agents/` | **Brainmaster 模式：Claude Code agent 定义** |
| `.claude/commands/` | 用户可手动调用的 slash commands |
| `config/` | 配置文件（M0 实施时创建） |
| `src/amarket/` | 应用源码（M0 实施时创建） |
| `tests/` | 测试代码（M0 实施时创建） |

---

## 速查表

- **当前 spec**：`docs/superpowers/specs/2026-06-14-news-engine-design.md`
- **当前 agent**：`.claude/agents/news-analyst.md`
- **测试 command**：`.claude/commands/test-premarket.md`
- **GitHub**：https://github.com/dangbuzhudeXNEL/Project_Amarket
- **本地路径**：`C:\AI\Claude\Project_Amarket`
- **PAT 位置（不入 git）**：`PAT.txt`
- **参考项目**：`C:\AI\Claude\Brainmaster`（同款 AI 集成模式）
