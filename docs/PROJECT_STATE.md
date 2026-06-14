# Project State

**Last Updated**: 2026-06-14 (Session 01 — brainstorm + spec)
**Updated By**: Claude (opus-4.7) + User

---

## 当前阶段

- **Spec**: #1 — 通用基础设施 + 新闻引擎 MVP
- **Phase**: 🟡 **Design complete, awaiting user spec review** → 然后进入 writing-plans 阶段
- **Milestone**: 尚未开始 M0
- **Sprint progress**: 0/7 milestones started

---

## 活跃任务

| ID | 任务 | Owner | 状态 |
|----|------|-------|------|
| - | 审阅 spec 文档（`docs/superpowers/specs/2026-06-14-news-engine-design.md`） | user | ⏳ pending |
| - | 创建 GitHub public repo 并 push | claude | 🔄 进行中 |
| - | 调用 superpowers:writing-plans 撰写实施计划（spec 通过后） | claude | 📋 待启动 |

---

## 最近 3 个关键决策（按时间倒序）

1. **2026-06-14**：采用"知识沉淀机制"支持多 session 开发 — 新增 CLAUDE.md / PROJECT_STATE.md / docs/sessions/ / CHANGELOG.md 四件套，定义 Session 启动/结束协议
2. **2026-06-14**：LLM 走用户本地 localhost 代理（Claude opus-4.7）+ DeepSeek 备用降级
3. **2026-06-14**：首期 MVP = Spec #1（基础设施 + 新闻引擎），其他 3 个 Spec 后续按序推进；4 个 Spec 串行而非并行

完整决策清单详见 spec 的 Section 3。

---

## 阻塞 / 待用户输入

无硬阻塞。下列事项可在 M0 实施过程中并行确认（参考 spec Section 17）：

- localhost 代理实际端口（M0 末填 `.env`）
- 业务推送 + 告警的企微机器人 webhook（用户创建后填 `.env`）
- 代码许可证选择
- 数据库种子数据是否调整

---

## 下一步

### 立即（本 session 末）
1. ⏳ 创建 GitHub `dangbuzhudeXNEL/Project_Amarket` public repo
2. ⏳ Push 当前所有 commits（spec、CLAUDE.md、PROJECT_STATE.md、CHANGELOG.md、session log）
3. ⏳ 写本次 session log
4. ⏳ 等待用户审阅 spec

### 用户审阅通过后（下次 session 开头）
5. 调用 `superpowers:writing-plans` 撰写 Spec #1 的实施计划（M0-M6 拆解为可执行任务）
6. 用户审阅实施计划
7. 进入 M0 实施

### M0 启动 checklist（实施开始前）
- [ ] 用户创建 2 个企微机器人，把 webhook URL 写入 `.env`
- [ ] 用户提供 localhost 代理端口
- [ ] 确认 Claude model id 字符串（`claude-opus-4-7` 或本地代理实际接受的名称）
- [ ] 选定代码许可证

---

## 重要环境/配置变化

| 时间 | 变化 |
|------|------|
| 2026-06-14 | 项目初始化：git init main / .gitignore / spec 写入 |
| 2026-06-14 | PAT.txt 加入 .gitignore 保护 |
| 2026-06-14 | spec 自审修订（修复模型 id 不一致等问题） |
| 2026-06-14 | spec 新增 Section 16 多 Session 开发支持 |

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
| `config/` | 配置文件（M0 实施时创建） |
| `src/amarket/` | 应用源码（M0 实施时创建） |
| `tests/` | 测试代码（M0 实施时创建） |

---

## 速查表

- **当前 spec**：`docs/superpowers/specs/2026-06-14-news-engine-design.md`
- **GitHub**：https://github.com/dangbuzhudeXNEL/Project_Amarket
- **本地路径**：`C:\AI\Claude\Project_Amarket`
- **PAT 位置（不入 git）**：`PAT.txt`
