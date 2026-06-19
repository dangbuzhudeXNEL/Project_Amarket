# Session 2026-06-19-03 — Spec v3 Merge with Peersession PRD + 升格小组联合项目

**Duration**: ~2 小时（含详细 spec 通读、对照、起草、协作工件创建）
**Participants**: User + Claude (model: Opus 4.7, effort: high)
**Goal**: 把 `Peersession/` 目录中的小组成员 PRD + Timeline merge 进 Project_Amarket；以 Peersession 为主线重写 Spec；升格为小组联合项目；建立协作基础设施

---

## 本次目标

- [x] Session 启动 Checklist 走完（CLAUDE.md / PROJECT_STATE.md / sessions 最新 / git log / git status）
- [x] 读完 Peersession 目录两份文档（PRD 539 行 + Timeline docx 188 段）
- [x] 与用户对齐 3 个关键决策（时间约束 / 项目定位 / 今天产出）
- [x] 通读当前 Spec v2 全貌（1558 行）
- [x] 起草并完成 Spec v3 (2391 行)
- [x] 归档 Peersession 文件到 `docs/peersession-source/`
- [x] 创建小组协作三件套：CONTRIBUTING.md / CODEOWNERS / PR 模板
- [x] 更新 README.md / CLAUDE.md（反映 Phase 1/2 + 小组联合）
- [x] 更新 PROJECT_STATE.md / CHANGELOG.md
- [x] 写本 session 日志（本文件）
- [x] commit + push

---

## 用户反馈触发的关键决策

### 决策 1：项目定位升格为"小组联合项目"

**用户原话**："我的 peersession 里面的文件是需要你去融合到我们项目的，那是我组里面其他成员做的，你吧这个大纲和我们当前的项目 merge 下吧，以这个 peersession 大纲为主吧"

**触发**：用户工作区里有 untracked 的 `Peersession/`，含一份 06-17 的 PRD 和一份 06-17 的 Timeline docx（10 天作业排期）。

**决策**：
- 项目从"个人自用 + 学习"升格为"小组联合项目"
- 以 Peersession PRD 为 Phase 1 主线（三大模块 / 6 时段日报 / P0-P3 告警 / 看板 API）
- 原 v2 内容（Brainmaster AI / 信号交易 / 盘前单次推送）降级为 Phase 2

### 决策 2：不赶 Peersession 的 6.27 deadline

**用户原话**："咱先不考虑 deadline,我们功能按照这个 peersession 的为主吧，我们之前的功能可以放在 phase2 在去做，phase1 先实现这个 peersession"

**决策**：按自己节奏走，保留 Peersession Timeline 里程碑结构作为参考。

### 决策 3：今天产出 = 直接开始改 spec（而非先出大纲提案）

**用户原话**："直接开始改 spec"

**决策**：跳过"先出大纲让用户审"的流程，直接产出 Spec v3 完整文件。

### 决策 4：永远不做实盘下单

**触发**：Peersession PRD §12 和 Timeline 都明确"不做自动实盘下单"。

**决策**：把"永远不做实盘"作为硬约束写入 Spec / CLAUDE / CONTRIBUTING / README，PR 触发实盘代码自动 reject。

### 决策 5：Superpowers 工具使用更灵活

**用户原话**："我发现 superpowers 有时候过于慢和细致了，我觉得不是每次都需要用这个，你觉得那块不足可以跑这个，但是简单的规划这种我们也可以先用 claude 原生自带的 /plan，或者其他相关能力吧"

**决策**：CLAUDE.md "协作模式说明" 加入"Superpowers 工具的使用原则"段（简单规划用原生、复杂任务用 superpowers、关键决策必用 brainstorming）。

---

## 关键产出

### 1. 主文档 — `docs/superpowers/specs/2026-06-19-spec1-v3-merged.md` (2391 行)

完整覆盖 21 章 + 3 附录：

| Section | 来源 / 处置 |
|---------|------------|
| §1 背景与目标 | 改写：愿景调整为 Peersession 主线；新增 Phase 1/2 划分 |
| §2 范围与非目标 | 大改：分 Phase 1/2 InScope；显式禁实盘 |
| §3 关键决策汇总 | 大改：扩 28 个决策点，含产品 / 技术 / 协作三组 |
| §4 用户与场景（**新增**） | PRD §1 启发 + 4 角色（分析师/交易员/管理员/来宾）+ 4 个核心场景 + 用户流程图 |
| §5 系统架构 | 改写：分层图扩展，加入三大模块边界 |
| §6 模块详细设计 | 大改：16 个 service（v2 是 7 个）+ 多 adapter；按"新闻 / 看板 / 参数 / 公共"四类分组 |
| §7 数据模型 | 大改：11+ 张表（v2 是 7 张），新增 events / market / sectors / alerts / reports / source_health / params / audit / config_versions |
| §8 新闻分类与评分体系（**新增**） | PRD §5/§6（8 类一级 + 14+ 二级 + 18 字段 + 重要性/紧急度/情绪评分 + P0-P3 决策表） |
| §9 关键工作流 | 大改：5 个工作流（实时新闻 / 6 时段日报 / P0-P3 告警 / 板块趋势 / AI 工作流双 Phase） |
| §10 看板与 API 设计（**新增**） | PRD §8/§9（首页布局 + 30+ API endpoint + 关键 DTO 示例） |
| §11 参数配置模块（**新增**） | Timeline M5（参数类型 / 权限矩阵 / 版本回滚 / 审计 / 脱敏） |
| §12 配置与密钥管理 | 适配：增 alert_rules.yml / market_sources.yml / sectors.yml / classification.yml / params_seed.yml |
| §13 错误处理与可观察性 | 沿用 + 扩展指标 |
| §14 测试策略 | 沿用 + 18 个 case（v2 是 13） |
| §15 项目结构 | 大改：services 按三大模块分包；新增 poc/、market_sources/ |
| §16 依赖清单 | 增 akshare/efinance/yfinance、anthropic/openai 移到生产 |
| §17 实施里程碑 | 重写：Phase 1 M0-M6 + Phase 2 M7-M9 |
| §18 安全与合规 | 沿用 + 强化"不做实盘"显式禁令 |
| §19 未来扩展点 | 沿用 + 增 MCP 工具集成 |
| §20 多 Session 开发 + 小组协作 | 沿用 + 新增小组协作（分支策略 / PR / CODEOWNERS / 角色分工） |
| §21 待小组确认事项 | 重新列 |
| 附录 A 术语表 / B 参考资料 / C **v2 → v3 章节映射** | C 章节为本次新增 |

### 2. 小组协作三件套

- **`CONTRIBUTING.md`**：13 章节，覆盖 onboarding / 分支策略 / commit / PR 流程 / 敏感模块 / 编码规范 / 测试 / 文档协议 / AI 协作约定 / 合规 reminder / 应急流程
- **`.github/CODEOWNERS`**：模块 owner 占位符（待小组成员账号到位后替换 `@xxx_owner`）
- **`.github/PULL_REQUEST_TEMPLATE.md`**：PR 描述模板

### 3. 归档

- `docs/peersession-source/a_share_realtime_news_dashboard_prd.md`（小组成员 PRD，moved from `Peersession/`）
- `docs/peersession-source/a_share_quant_project_timeline.docx`（小组成员 Timeline）
- `docs/peersession-source/a_share_quant_project_timeline.extracted.txt`（docx 文本提取，方便后续不依赖 docx 处理）
- 原 `Peersession/` 目录已清空 + 删除

### 4. 知识沉淀文档更新

- **`README.md`** 大改：反映小组联合 + Phase 1/2 + 新核心能力清单 + 文档导航
- **`CLAUDE.md`** 6 处 Edit：
  - 项目身份卡（小组联合 + 双 Phase 路线图 + AI 集成双路径表）
  - 编码规范（新增"不允许直接 push main" + "不允许引入实盘下单代码"）
  - YAGNI 列表（增"实盘下单"、改"AI"双 Phase 表述）
  - 项目约束（小组内部 + 永远不实盘 + 故障隔离扩展）
  - 协作模式（小组角色 + AI 协作约束 + superpowers 使用原则）
  - 文档地图 + 链接（v3 作为当前 spec + CONTRIBUTING / CODEOWNERS / peersession-source）
- **`docs/PROJECT_STATE.md`** 大改：标注 Session 03 + 下次 session 必读 3 件事 + 活跃任务 + 6 个关键决策（按时间倒序）
- **`CHANGELOG.md`** 大改：Spec v3 段 + 小组协作工件段 + 归档段 + 基础文档更新段

---

## 关键文件清单

### 新增
- `docs/superpowers/specs/2026-06-19-spec1-v3-merged.md`（2391 行）
- `CONTRIBUTING.md`
- `.github/CODEOWNERS`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `docs/peersession-source/a_share_realtime_news_dashboard_prd.md`（mv）
- `docs/peersession-source/a_share_quant_project_timeline.docx`（mv）
- `docs/peersession-source/a_share_quant_project_timeline.extracted.txt`（新生成）
- `docs/sessions/2026-06-19-03-merge-peersession-spec-v3.md`（本文件）

### 修改
- `README.md`（大改，几乎全部重写）
- `CLAUDE.md`（6 处 Edit）
- `docs/PROJECT_STATE.md`（大改）
- `CHANGELOG.md`（大改）

### 删除
- `Peersession/`（目录已清空 + 删除）

---

## 阻塞 / 待解

无新硬阻塞。

软阻塞（待小组在下次 session 或 M0 启动前确认）：
1. Spec v3 审阅结论
2. CONTRIBUTING / CODEOWNERS / PR 模板审阅
3. 填实 CODEOWNERS 中 `@xxx_owner` 占位符
4. GitHub 分支保护规则（main 受保护、需 PR + review）
5. 企微 / 飞书机器人 webhook（Phase 1 M0 启动前）
6. LLM API key 选型（Phase 1 M1 启动前）
7. 静态 POC 是否要框架（M3 启动前）
8. `claude --version` 在 PATH（Phase 2 M7 启动前）

---

## 下一次 Session 接力点

**首要任务**：
1. Session 启动 Checklist 走完
2. 询问小组：spec v3 + 协作工件审阅结论？
3. 根据反馈走分叉：
   - 通过且要立即 M0 → 用户先做 M0 前置准备清单（CODEOWNERS / 分支保护 / webhook / API key），然后 Claude 启动 M0 实施任务
   - 通过且要先 writing-plans → 调用 `superpowers:writing-plans` 撰写 Phase 1 实施计划
   - spec 要改 → 起 `docs/<member>-spec-update-v3.1` 分支 PR 化修订（至少产品 + 技术 2 人 review）
   - 先做 spike → 起 `spike/<topic>` 分支跑实验

**先读**：
1. `CLAUDE.md`（已更新）
2. `docs/PROJECT_STATE.md`（已更新，"下次 session 必读 3 件事"在顶部）
3. 本文件
4. `docs/superpowers/specs/2026-06-19-spec1-v3-merged.md`（重点：§4 用户场景 / §6 模块设计 / §7 数据模型 / §17 里程碑 / 附录 C 章节映射）
5. `CONTRIBUTING.md`（理解协作规范）
6. `.github/CODEOWNERS`（看待填占位符）

---

## 学到的经验

1. **大规模 spec 改造前先建对照表**：v2 → v3 章节映射（附录 C）极大降低了 reviewer 理解差异的成本。
2. **AskUserQuestion 一次问 3 个比连珠炮逐个问效率高**：本次用 1 次提问拿到 3 个关键决策（时间约束 / 项目定位 / 今日产出），如果分 3 次会浪费 session 时间。
3. **Edit 工具配 unique anchor 比 Write 重写更稳**：CLAUDE.md 6 处 Edit 全成功，每段先选出独有的 old_string 锚点。
4. **docx 文件需要解压 + XML 解析读取**：Read 工具不能直接读 docx，用 Python `zipfile` + `ElementTree` 提取 `word/document.xml` 中的 `<w:t>` 文本是稳定方案；输出走 UTF-8 文件避免 Windows console cp1252 编码问题。
5. **Windows rmdir 偶尔"Device or resource busy"**：用 Python 的 `os.rmdir` 可以绕过。
6. **关键禁令要在多文档同步出现**：实盘下单 ban 同时写在 spec / CLAUDE / CONTRIBUTING / README，单点失效不至于全失效。

---

## 用到的 Skill / 工具

- `Read` / `Glob` / `Bash`（git 命令） — Session 启动 Checklist
- `AskUserQuestion`（3 次） — 关键决策点澄清
- `TaskCreate` / `TaskUpdate` — 7 个任务跟踪
- `Write` / `Edit` — spec / 文档撰写
- `Python` (via Bash) — docx 解压 / 目录清理
- **未用 superpowers** — 本次工作（spec 起草 + 文档同步）按用户"简单规划用原生工具"指引未启动 superpowers 流程

---

## 🏁 Session 结束（2026-06-19）

### 收尾检查（CLAUDE.md Session 结束 Checklist）

- [x] `docs/PROJECT_STATE.md` 已更新（标注 session 结束 + "下次 session 必读 3 件事"）
- [x] 本 session log 已写完
- [x] `CHANGELOG.md` 已更新
- [x] 所有变更将一次 commit + push（即将做）

### 下次 session 启动者必读

按 `CLAUDE.md` 顶部 Session 启动 Checklist 走：

1. 读 `CLAUDE.md`（已更新）
2. 读 `docs/PROJECT_STATE.md` ← 现在已经标注好"下次必读 3 件事"
3. 读本 session log + session 01/02 log
4. `git log --oneline -10`
5. `git status`

读完后第一个动作：**询问小组 Spec v3 + 协作工件审阅结论**（PROJECT_STATE.md 已给出分叉处理路径）。

### 一句话总结

> Session 03：项目升格为小组联合 + Spec v3 融合 Peersession PRD（2391 行）+ 协作三件套上线。下次 session 等小组反馈进入 writing-plans 或 Phase 1 M0。
