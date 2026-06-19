# Project State

**Last Updated**: 2026-06-19 (Session 03 进行中)
**Updated By**: Claude (opus-4.7) + User
**Next Action Owner**: 👥 **小组**（审阅 Spec v3 + CONTRIBUTING + CODEOWNERS）

---

## 🎯 下次 Session 必读：3 件事

### 1. 当前阻塞在哪
**小组（含用户）需要审阅 Spec v3 + 新增的小组协作工件**（CONTRIBUTING.md / CODEOWNERS / PR 模板）后才能进入实施计划（writing-plans）或直接进入 Phase 1 M0。

### 2. 用户/小组决策后的分叉

| 反馈 | 下次 session 第一动作 |
|------|--------------------|
| "spec v3 OK 且小组工件 OK，进入 Phase 1 M0 实施" | 用户先填 GitHub CODEOWNERS 真实账号 / 创建企微&飞书 webhook / 决定 LLM key 选型，然后启动 M0 任务 |
| "spec v3 OK，先用 superpowers:writing-plans 出实施计划再 M0" | 调用 `superpowers:writing-plans` 把 Phase 1 M0-M6 拆成可执行的任务清单（每任务带验收 / 依赖 / 测试） |
| "spec v3 要改 X 部分" | 创建 `docs/<member>-spec-update-v3.1` 分支 → PR 修订 → 至少产品 + 技术 2 人 review |
| "先做其他事（如真实接 1 个新闻源做 spike）" | 按需进入 spike 工作（建议起 `spike/<topic>` 分支，写完后 review 经验再决定要不要纳入 spec） |

### 3. 严禁动作（在小组审阅前）
- ❌ 直接开始写 src/ 代码（绕过 M0 + 实施计划）
- ❌ 自行修改架构决策（任何变化要走 brainstorming/ADR 流程）
- ❌ 跳过 Session 启动 Checklist
- ❌ 引入任何形式的实盘下单代码（永远 ban）

---

## 当前阶段

- **Spec**: #1 v3 — A 股实时新闻分析与行情看板（小组联合版，融合 Peersession PRD）
- **Phase**: 🟡 **Spec v3 设计完成 + 小组协作工件就绪，等待小组审阅**
- **Milestone**: 尚未开始 Phase 1 M0
- **Sprint progress**: 0/6 Phase 1 milestones started（M0-M6）；0/3 Phase 2 milestones（M7-M9）
- **Session count**: 3 sessions
  - 2026-06-14 01: brainstorm + spec v1
  - 2026-06-14 02: 架构调整为 Brainmaster 模式 → spec v2
  - 2026-06-19 03: 融合 Peersession PRD → spec v3 + 小组协作工件（本次）

---

## 活跃任务

| ID | 任务 | Owner | 状态 |
|----|------|-------|------|
| - | 审阅 Spec v3（重点：§4 用户与场景 / §6 模块设计 / §7 数据模型 / §17 里程碑 / 附录 C v2→v3 映射） | **小组** | ⏳ pending |
| - | 审阅 CONTRIBUTING.md + CODEOWNERS + PR 模板 | **小组** | ⏳ pending |
| - | 填实 CODEOWNERS 中的 GitHub 账号占位符 | **用户** | ⏳ pending |
| - | 创建 GitHub 分支保护规则（main 需 PR + review） | **用户** | ⏳ pending |
| - | 决定下一步：进 writing-plans 还是直接 M0 | **小组** | ⏳ pending |
| - | 调用 superpowers:writing-plans 撰写 Phase 1 实施计划（spec 通过后） | claude | 📋 blocked |

---

## 最近 6 个关键决策（按时间倒序）

1. **2026-06-19 (本 session)**：**升格为小组联合项目** — 多人协作 + AI 协作伙伴 Claude；新增 CONTRIBUTING / CODEOWNERS / PR 模板；分支策略 + Code Review 流程上线
2. **2026-06-19 (本 session)**：**Spec v3 融合 Peersession PRD** — 以 Peersession 为 Phase 1 主线（三大模块 / 6 时段日报 / P0-P3 告警 / 看板 API / 参数配置），原 v2 内容降级为 Phase 2（Brainmaster AI / 信号交易）
3. **2026-06-19 (本 session)**：**永远不做实盘下单** — 显式禁令写入 spec / CLAUDE.md / CONTRIBUTING / README
4. **2026-06-19 (本 session)**：**AI 集成双路径** — Phase 1 走 SDK（需要 API key）；Phase 2 走 Brainmaster（零 API key）
5. **2026-06-14 (晚)**：采纳 Brainmaster 模式接入 AI（Phase 2 路径来源）
6. **2026-06-14**：采用"知识沉淀机制"支持多 session 开发

完整决策清单详见 spec v3 §3。

---

## 阻塞 / 待用户/小组输入

**硬阻塞**：小组审阅 Spec v3 + 小组协作工件

**软阻塞**（不影响进入 writing-plans，M0 实施前确认即可）：
- 填实 `.github/CODEOWNERS` 中的 GitHub 账号占位符
- 业务推送 + 告警的企微 / 飞书 webhook（用户/小组创建后填 `.env`）
- LLM API key 选型（Anthropic / DeepSeek 二选一或都配）
- 静态 POC 框架选型（默认原生 + Tailwind CDN）
- 代码许可证选择
- 数据库种子数据是否调整
- 验证 `claude --version` 在 Git Bash 中可调用（Phase 2 启动前）

---

## 下一步路径

### 立即（下次 session 开头）
1. 走 Session 启动 Checklist（CLAUDE.md 顶部）
2. 询问小组：spec v3 审阅结论？小组协作工件 OK 吗？
3. 根据反馈走相应分叉（见上面"下次 session 必读"）

### writing-plans 阶段（小组审阅通过后）
4. 调用 `superpowers:writing-plans` 撰写 Phase 1 实施计划
5. 实施计划按 M0-M6 拆解，每个任务有：
   - 验收标准
   - 依赖关系
   - 预计工时
   - 测试要求
   - 责任人（owner）
6. 小组审阅实施计划
7. 进入 Phase 1 M0 实施

### Phase 1 M0 启动 checklist（实施开始前）
- [ ] 用户验证 `claude --version` 在 PATH 里能调（M0 可暂时不需，Phase 2 才需要）
- [ ] 用户/小组创建 2 个企微机器人 + 1 个飞书机器人，把 webhook URL 写入 `.env`
- [ ] 用户配置至少 1 个 LLM API key（Anthropic 主或 DeepSeek 备）
- [ ] 选定代码许可证（或显式决定暂不加）
- [ ] CODEOWNERS 填实 GitHub 账号
- [ ] GitHub 分支保护规则配置好（main 需 PR + review）

---

## 重要环境/配置变化（按时间正序）

| 时间 | 变化 |
|------|------|
| 2026-06-14 上午 | 项目初始化：git init main / .gitignore / spec v1 写入 |
| 2026-06-14 上午 | PAT.txt 加入 .gitignore 保护 |
| 2026-06-14 上午 | spec v1 自审修订 |
| 2026-06-14 下午 | spec v1 新增 §16 多 Session 开发支持 |
| 2026-06-14 下午 | 知识沉淀工件 v1（CLAUDE.md / PROJECT_STATE.md / CHANGELOG.md / sessions/） |
| 2026-06-14 下午 | GitHub repo 创建 + 首推 |
| 2026-06-14 晚上 | **架构调整：采纳 Brainmaster 模式** → spec v2；新建 `.claude/agents/news-analyst.md` 和 `.claude/commands/test-premarket.md` |
| 2026-06-14 晚上 | `.gitignore` 修复 `*PAT*` 过宽 bug |
| **2026-06-19** | **Spec v3 融合 Peersession PRD**：写入 `docs/superpowers/specs/2026-06-19-spec1-v3-merged.md`（2391 行） |
| **2026-06-19** | **归档 Peersession 原始素材**：移至 `docs/peersession-source/` |
| **2026-06-19** | **小组协作工件**：新增 `CONTRIBUTING.md` / `.github/CODEOWNERS` / `.github/PULL_REQUEST_TEMPLATE.md` |
| **2026-06-19** | **CLAUDE.md / README.md** 更新反映 Phase 1/2 双阶段 + 小组联合定位 |

---

## 文档地图

| 文档 | 用途 |
|------|------|
| `CLAUDE.md` | 项目根入口，新 session 必读第一文件（已更新为 v3 + 小组联合） |
| `docs/PROJECT_STATE.md` | 本文件，项目"现在到哪了" |
| `docs/sessions/*.md` | 每次开发 session 的日志（已有 3 篇） |
| `docs/superpowers/specs/2026-06-19-spec1-v3-merged.md` | **当前 Spec v3** |
| `docs/superpowers/specs/2026-06-14-news-engine-design.md` | 上一版 Spec v2（历史） |
| `docs/peersession-source/` | Peersession 原始素材（小组成员 PRD + Timeline） |
| `docs/superpowers/plans/` | 实施计划（writing-plans 阶段后会有） |
| `docs/adr/` | 架构决策记录（按需创建，目前空） |
| `CHANGELOG.md` | 用户视角的"做了什么" |
| `CONTRIBUTING.md` | **小组协作规范**（分支 / PR / review / 编码标准） |
| `.github/CODEOWNERS` | 模块 owner（含占位符待填） |
| `.github/PULL_REQUEST_TEMPLATE.md` | PR 描述模板 |
| `.claude/agents/news-analyst.md` | Phase 2 Brainmaster：盘前新闻汇总 agent |
| `.claude/commands/test-premarket.md` | 用户可手动调的 slash command |
| `README.md` | 项目概览（GitHub 首页，已更新为小组联合） |
| `PAT.txt` | GitHub PAT，已 gitignore（**永不入库**） |

---

## 速查表

- **当前 spec**：`docs/superpowers/specs/2026-06-19-spec1-v3-merged.md` (v3, 2391 行)
- **当前 phase**：Phase 1（即将启动 M0）
- **当前 agent**（Phase 2 用）：`.claude/agents/news-analyst.md`
- **GitHub**：https://github.com/dangbuzhudeXNEL/Project_Amarket (PUBLIC)
- **本地路径**：`C:\AI\Claude\Project_Amarket`
- **PAT 位置（不入 git）**：`PAT.txt`
- **参考项目**：`C:\AI\Claude\Brainmaster`（同款 Brainmaster AI 集成模式）
- **本次 session commit**：（即将创建）

---

## 当下 Session 总结（2026-06-19, Session 03）

**输入**：用户告知 `Peersession/` 是小组成员做的，需要 merge 进当前项目，**以 Peersession 大纲为主**；同时告知"superpowers 不必每次都用，简单规划用原生工具"。

**产出**：
- 1 份完整 Spec v3 (2391 行)，融合 Peersession PRD + 原 v2 工程化内容
- 双 Phase 划分：Phase 1 = 三大模块（新闻 / 看板 / 参数配置）+ 6 时段日报 + P0-P3 告警 + 看板 API + 看板 POC；Phase 2 = 原 v2 内容（Brainmaster AI / 信号交易）
- 小组协作三件套：`CONTRIBUTING.md` / `.github/CODEOWNERS` / `.github/PULL_REQUEST_TEMPLATE.md`
- Peersession 原始素材归档到 `docs/peersession-source/`
- 更新 CLAUDE.md（项目身份卡 / 编码规范 / YAGNI / 协作模式 / 文档地图 / 链接）
- 更新 README.md（Phase 1/2 + 小组联合）
- 更新 CHANGELOG.md（即将做）
- 更新 PROJECT_STATE.md（本文件）

**关键决策**：
- 项目升格为小组联合项目
- 以 Peersession PRD 为 Phase 1 主线
- v2 内容降级为 Phase 2
- 不赶 Peersession Timeline 的 6.27 截止
- 永远不做实盘下单（显式禁令）
- Phase 1 AI 走 SDK；Phase 2 走 Brainmaster

**下次接力点**：小组审阅 Spec v3 + 小组协作工件 → 进入 writing-plans 或直接 Phase 1 M0。
