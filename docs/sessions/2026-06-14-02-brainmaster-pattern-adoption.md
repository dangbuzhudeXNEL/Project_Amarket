# Session 2026-06-14-02 — Brainmaster Pattern Adoption (Architecture Shift)

**Duration**: ~1 小时
**Participants**: User + Claude (model: opus-4.7, 1M context)
**Goal**: 重写 Spec #1 的 LLM 集成部分，从"Anthropic SDK + localhost proxy"改为"Brainmaster 模式：subprocess + Claude CLI agent"

---

## 本次目标

- [x] 调研隔壁 Brainmaster 项目 (`C:\AI\Claude\Brainmaster`) 的 AI 集成模式
- [x] 设计 Project_Amarket 的对等架构
- [x] 重写 Spec #1 相关章节（§3/§5/§7/§8/§11/§12/§13/§17）
- [x] 创建 `.claude/agents/news-analyst.md`
- [x] 创建 `.claude/commands/test-premarket.md`
- [x] 同步更新 CLAUDE.md / PROJECT_STATE.md / CHANGELOG.md / README.md
- [x] Commit + push 到 GitHub

---

## 关键决策

### 决策：采纳 Brainmaster 模式

**触发**：用户指出我设计的"Anthropic SDK + localhost proxy"方式不对，他们隔壁项目 Brainmaster 是用本地 Claude Code 直接作为 LLM 后端，**不需要 API key**。

**调研发现**（看 `C:\AI\Claude\Brainmaster\dashboard\scheduler.py` + `.claude/agents/*.md`）：

Brainmaster 模式 = "Claude Code as LLM Backend"
1. Python 用 `subprocess.run(["claude", "--agent", <name>, "-p", <prompt>])` 触发
2. Agent 定义在 `.claude/agents/<name>.md`（YAML frontmatter + Markdown body）
3. Agent 自己用 `Write` 工具写 JSON 到约定路径
4. Python 跑前后对比文件 mtime + `json.loads()` 校验，没写文件视为 `degraded`
5. **完全不需要 API key**，复用用户的 Claude Code 订阅
6. Agent 可以声明 MCP 工具（yahoo-finance, akshare, tavily 等），数据源直接给 AI 用

**采纳理由**：
- ✅ 零 API 成本（vs. 我原设计要么收费 Anthropic API 要么需 proxy）
- ✅ 与隔壁项目模式一致（用户已经在用、有信心）
- ✅ Spec #2 行情数据接入时可直接用 akshare MCP（不用 Python 包装）
- ✅ 每次 AI 输出都是 JSON 文件，天然审计/回放/重处理
- ⚠️ 唯一劣势：subprocess 启动 5-10 秒延迟，但 breaking news 已经定为纯规则（不调 AI），所以无影响

### 决策：保留 LLMProvider SDK 作为可选 Tier 2 fallback

**理由**：极端场景（Claude CLI 不可用 / 崩了），架构上不应锁死单一路径。但 MVP 默认 `fallback.enabled=false`，**不安装 `anthropic` 依赖**。

---

## 实际进展

### 1. 调研 Brainmaster 模式（30 分钟）

读取了：
- `dashboard/ai_analyzer.py` — 误以为是主路径，结果是 Tier 2 fallback 的 LLMClient 实现
- `dashboard/scheduler.py` — 发现了 `_run_agent_with_verification()` 和 `_run_claude_agent()` — **真正的主路径**
- `dashboard/agent_reader.py` — 揭示了"Agent 写 JSON / Python 读 JSON"的契约
- `dashboard/config.py` — `CLAUDE_CLI_PATH = os.getenv("CLAUDE_CLI_PATH", "claude")`
- `.claude/agents/stocking-agent.md` — 真实 agent 定义样本（model/tools/MCPs/maxTurns/输出契约）
- `.claude/commands/morning-briefing.md` — slash command 样本

### 2. Spec 大改（30+ 分钟）

修改了 spec 的 **9 个章节** 共 ~50 处编辑：

| 章节 | 改动 |
|------|------|
| §3 决策表 | LLM 行整体重写，新增"AI 模型"行（每个 agent 自声明 model） |
| §2.1 In Scope | AI 增强描述改为 "Claude Code agent 模式" |
| §5.1.4 AIService | 从"LLM 调用"改为"agent 编排 + 输出校验" |
| §5.2.2 ClaudeAgentRunner | **新增** subprocess 封装 + 校验逻辑 |
| §5.2.3 LLMProvider | 降级为可选 Tier 2 fallback |
| §5.3 Claude Code Agents | **新增章节** — agent 清单、`news-analyst` 模板、slash commands |
| §5.4 Repository 层 | `NewsRepo` 新增 `export_raw_for_date()` 方法（导出供 agent 读） |
| §7.1 盘前推送流程 | AI 调用步骤改为 agent runner 路径 |
| §7.3 AI 工作流 | 完全重写：subprocess → 校验 → 降级链 |
| §8.1 配置清单 | `llm.yml` 标注为可选，新增 `agents.yml` |
| §8.2 配置示例 | 替换为 `agents.yml`（主）+ 标注 `llm.yml`（可选） |
| §8.3 .env.example | 移除 `ANTHROPIC_API_KEY` 必填，标注为可选 |
| §11 项目结构 | 新增 `.claude/agents/`、`.claude/commands/`、`data/news/raw/`、`data/news/summaries/`；`config/agents.yml`；改 `src/.../adapters/llm/` → `adapters/ai/` |
| §12.1 生产依赖 | 移除 `anthropic` |
| §12.2 可选依赖 | **新增** Tier 2 LLM SDK 部分（`anthropic`, `openai`） |
| §13 M3 里程碑 | 改名 "AI 增强（Brainmaster 模式）" + 验收标准重写 |
| §17 待用户确认 | 已确认表 +1 行（LLM 集成模式）；待确认表移除 localhost 代理端口和 LLM key 行；新增 Claude CLI 可调用验证 |

### 3. 创建 Claude Code 工件

- **`.claude/agents/news-analyst.md`** (sonnet, 30 turns) — 完整 agent 定义：
  - 输入：`data/news/raw/<date>/*.json`
  - 输出：`data/news/summaries/<date>-premarket.json`（严格 schema）
  - 工具仅 `Read, Write, Glob, Grep`（无 Bash、无 MCP，权限最小化）
  - 工作流 5 步：读 / 分类 / Markdown 摘要 / highlights / 写文件
  - 异常处理 4 种场景 + 严格禁止清单

- **`.claude/commands/test-premarket.md`** — 用户手动测试 slash command

### 4. 同步更新所有知识工件

- `CLAUDE.md`：更新"AI 集成模式"段、新增"AI 集成走 ClaudeAgentRunner"规范、YAGNI 列表加入"不直接调 Anthropic SDK"
- `README.md`：技术栈段更新、项目结构图加入 `.claude/`
- `docs/PROJECT_STATE.md`：决策列表前置、活跃任务更新、新增此次架构变化记录
- `CHANGELOG.md`：新增 "Changed — Architecture Adjustment" 段

---

## 产出（文件 / commits）

### 修改
- `docs/superpowers/specs/2026-06-14-news-engine-design.md` (~50 处修改)
- `CLAUDE.md`
- `README.md`
- `docs/PROJECT_STATE.md`
- `CHANGELOG.md`

### 新增
- `.claude/agents/news-analyst.md`
- `.claude/commands/test-premarket.md`
- `docs/sessions/2026-06-14-02-brainmaster-pattern-adoption.md`（本文件）

### Commits
- (即将创建) `arch(spec1): adopt Brainmaster pattern for AI integration`

---

## 阻塞 / 待解

无新阻塞。

需用户确认（不影响进入下一阶段）：
1. Spec v2 审阅是否通过
2. `claude --version` 在 Git Bash 可调用（M0 启动时验证即可）

---

## 下一次 Session 接力点

**首要任务**：
1. 等待用户审阅 Spec v2
2. 通过后调用 `superpowers:writing-plans` 撰写 Spec #1 实施计划（M0-M6 详细任务清单）

**先读**：
1. `CLAUDE.md`
2. `docs/PROJECT_STATE.md`
3. 本文件
4. `docs/superpowers/specs/2026-06-14-news-engine-design.md`（重点看 §5.2.2 ClaudeAgentRunner 和 §5.3 Claude Code Agents 是新内容）
5. `.claude/agents/news-analyst.md`（理解 agent 契约）

**然后开始**：根据用户反馈进入 writing-plans 阶段。

---

## 学到的经验

1. **遇到不熟悉的领域先看现有项目**：Brainmaster 已经验证了这个模式，少踩很多坑
2. **不要自己脑补 API key 需求**：用户提示 "我没给 brainmaster API key" 时应该立刻去看代码而不是自己假设
3. **subprocess + 文件契约**比 SDK + 内存对象更适合"AI 工作负载"：
   - 天然支持审计、回放、异步、断点续传
   - Agent 失败的"半完成状态"通过 mtime + JSON 校验可清晰判定
   - Python 主进程更简单，AI 工作负载完全隔离

---

## 用到的 Skill / 工具

- `Read` / `Glob` / `Grep` — 大量调研 Brainmaster 代码
- `Edit` — spec 重写
- `Write` — 新建 agent + command 定义
- `Bash` — git 操作
