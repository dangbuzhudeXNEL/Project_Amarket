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
  - 17 个章节 + 2 个附录，约 1400 行
  - 覆盖：架构、模块、数据模型、工作流、错误处理、测试、里程碑、多 session 支持
- 知识沉淀机制：
  - `CLAUDE.md` 项目记忆
  - `docs/PROJECT_STATE.md` 状态快照
  - `docs/sessions/` 历次 session 日志目录
  - `CHANGELOG.md` 本文件
- GitHub public repo 创建：`dangbuzhudeXNEL/Project_Amarket`

### Pending — 接下来
- Spec 用户审阅
- `superpowers:writing-plans` 撰写实施计划
- M0：项目骨架（uv 项目、CI、SQLite、健康检查、Streamlit Hello World）
- M1：财联社单源端到端
- M2：4 源 + 去重 + 规则分类
- M3：Claude 集成 + Prompt 缓存
- M4：APScheduler + 盘前推送
- M5：可观察性 + Streamlit UI
- M6：集成测试 + 文档 + 试运行
