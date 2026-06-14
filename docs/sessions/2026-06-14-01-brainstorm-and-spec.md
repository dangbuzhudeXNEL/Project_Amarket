# Session 2026-06-14-01 — Brainstorm + Spec #1 Design

**Duration**: ~3 小时（含跨多轮迭代）
**Participants**: User + Claude (model: opus-4.7, 1M context, via local proxy)
**Goal**: 从 0 到 1 把"A股量化 + 新闻系统"的需求梳清楚，输出第一份可执行的 spec

---

## 本次目标

- [x] 用 brainstorming 流程理清产品定位、范围、约束
- [x] 把"5 个子系统的大平台"拆解为 4 个 Spec，确定先做哪个
- [x] 完成 Spec #1（基础设施 + 新闻引擎）的完整设计文档
- [x] 文档自审 + 修订
- [x] 建立多 session 开发知识沉淀机制
- [x] 创建 GitHub repo 并 push

---

## 实际进展

### 1. Brainstorming（用 superpowers:brainstorming 技能）
通过 8 轮一问一答澄清了核心地基决策：

| 维度 | 决策 |
|------|------|
| 项目定位 | 个人自用 + 学习，预留 group use 扩展 |
| 交易模式 | 信号 + 模拟，BrokerAdapter 预留实盘 |
| 部署形态 | 本地 Windows 服务 + 微信/钉钉 push |
| 数据源 | 免费源（akshare/efinance）+ Yahoo Finance + RSS |
| 新闻源 | 财联社 + 东财 7x24 + 新浪 7x24 + 华尔街见闻 |
| LLM | Claude opus-4.7（走本地 localhost 代理）+ DeepSeek 备 |
| 盘前节奏 | 工作日 08:30 一次集中推送 |
| Breaking 判定 | 纯规则（高优来源 + 关键词命中） |
| 推送渠道 | 企业微信群机器人（主）+ Telegram Bot 预留 |
| UI 框架 | Streamlit 极简面板 + 业务/UI 分层 |

### 2. 项目分解
将整体平台拆为 4 个 Spec（串行交付）：
1. **Spec #1** 通用基础设施 + 新闻引擎（本次设计）
2. **Spec #2** 行情数据基座 + 回测引擎
3. **Spec #3** BrokerAdapter + AI 选股策略
4. **Spec #4** 资产配置 + AI Feedback

### 3. Spec #1 设计文档
完成 17 章 + 2 附录的完整设计：
- 系统分层架构图（UI / API / Service / Adapter / Repository）
- 7 张 SQL 表的详细 DDL
- 3 个关键工作流（盘前 / breaking / AI 降级）
- 完整配置文件示例（7 个 YAML）
- 故障隔离矩阵 + Prometheus metrics + `/healthz`
- 测试策略（13 个关键测试场景）
- 完整项目结构树
- 7 个里程碑（M0-M6，总计 3-4 周半工时）

### 4. 自审修订
发现并修复：
- 模型 ID 不一致（统一为 `claude-opus-4-7`）
- 新闻源 API endpoint 描述过于确定（改为"M1/M2 调研确认"）
- 周末新闻轮询未定义（新增 weekend_archive_poll 任务）
- chinese-calendar "2024 末"描述过时（改为"PyPI 年度更新"）
- 外部 watchdog 归属不清（明确为 `scripts/watchdog/` 独立脚本）

### 5. 多 Session 开发知识沉淀
新增架构组件：
- `CLAUDE.md` 项目根入口（自动加载）
- `docs/PROJECT_STATE.md` 状态快照
- `docs/sessions/*.md` 时间序列日志
- `CHANGELOG.md` 变更历史
- Session 启动/结束两套协议

### 6. GitHub 化
- 创建 public repo `dangbuzhudeXNEL/Project_Amarket`
- Push 所有 commits

---

## 关键决策

1. **决策**：4 个 Spec 串行而非并行交付
   **理由**：避免一次性吃太大；每个 Spec 独立闭环可上线；前 Spec 的基础设施被后 Spec 复用

2. **决策**：UI 用 Streamlit 起步，业务/UI 严格分层
   **理由**：Streamlit 1-2 天能搭出；分层后未来切换 React 不需改业务代码

3. **决策**：LLM 走用户本地 localhost 代理而非 Anthropic 官方 API
   **理由**：用户已有 Claude Code 订阅，本地代理零边际成本；架构上抽象 `LLMProvider` 接口，未来换 API 0 改动

4. **决策**：Breaking 判定 MVP 走纯规则不走 AI
   **理由**：延迟低（无 LLM 调用）、可预测、成本 0；规则不够精准时再演进到混合模式

5. **决策**：必须做多 session 知识沉淀机制
   **理由**：用户明确说"会是多 session 开发"，没有这套机制下次 session 会从零开始

---

## 产出（文件 / commits）

### 新增文件
- `.gitignore`
- `docs/superpowers/specs/2026-06-14-news-engine-design.md`（约 1400 行）
- `CLAUDE.md`
- `docs/PROJECT_STATE.md`
- `CHANGELOG.md`
- `docs/sessions/2026-06-14-01-brainstorm-and-spec.md`（本文件）
- `README.md`

### Commits（本 session 末汇总）
- `b0ab46f` docs: add Spec #1 design (infrastructure + news engine)
- `26c0d86` docs(spec1): self-review fixes for consistency and clarity
- 接下来：`session: brainstorm + Spec #1 design + multi-session sinking` 一个综合 commit

---

## 阻塞 / 待解

无硬阻塞，但需用户在下次 session 或 M0 启动前确认：

1. 用户审阅 spec 是否通过
2. localhost 代理实际端口（M0 末填 .env）
3. 企微机器人 webhook（M0 末填 .env）
4. 代码许可证选择

---

## 下一次 Session 接力点

**首要任务**：
1. 用户审阅 spec → 通过后调用 `superpowers:writing-plans` 撰写 Spec #1 实施计划

**先读**：
1. `CLAUDE.md`
2. `docs/PROJECT_STATE.md`
3. 本 session log
4. `docs/superpowers/specs/2026-06-14-news-engine-design.md`（如果是新 Claude 实例）

**然后开始**：根据用户审阅反馈，要么修订 spec，要么直接进入 writing-plans 阶段。

---

## 用到的 Skill

- `superpowers:using-superpowers` — 启动技能体系
- `superpowers:brainstorming` — 需求探索、设计推演、文档生成、自审、用户审核流程
- （下次 session 即将用）`superpowers:writing-plans` — 设计转实施计划

---

## 备注

- 项目 PAT 在 `PAT.txt`（已加入 .gitignore，绝不入库）
- 用户的 GitHub：`dangbuzhudeXNEL`
- 用户的开发环境：Windows + Git Bash + Claude Code + 本地 LLM 代理
