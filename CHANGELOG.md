# Changelog

All notable changes to **Project_Amarket** are documented here.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format and
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Each Spec corresponds to a major milestone. Within a Spec, M0-M6 are intermediate releases.

---

## [Unreleased] — Spec #1 进行中

### Added — Design Phase（2026-06-14）
- 项目初始化：git 仓库、`.gitignore`、文档目录结构
- Spec #1 设计文档完成：`docs/superpowers/specs/2026-06-14-news-engine-design.md`
  - 17 个章节 + 2 个附录，约 1500 行
  - 覆盖：架构、模块、数据模型、工作流、错误处理、测试、里程碑、多 session 支持
- 知识沉淀机制：
  - `CLAUDE.md` 项目记忆
  - `docs/PROJECT_STATE.md` 状态快照
  - `docs/sessions/` 历次 session 日志目录
  - `CHANGELOG.md` 本文件
- GitHub public repo 创建：`dangbuzhudeXNEL/Project_Amarket`

### Changed — Architecture Adjustment（2026-06-14, late）
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

### Pending — 接下来
- Spec v2 用户审阅
- `superpowers:writing-plans` 撰写实施计划
- M0：项目骨架（uv 项目、CI、SQLite、健康检查、Streamlit Hello World）
- M1：财联社单源端到端
- M2：4 源 + 去重 + 规则分类
- M3：`ClaudeAgentRunner` + news-analyst agent 端到端
- M4：APScheduler + 盘前推送
- M5：可观察性 + Streamlit UI
- M6：集成测试 + 文档 + 试运行

