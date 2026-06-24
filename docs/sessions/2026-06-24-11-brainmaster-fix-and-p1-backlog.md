# Session 2026-06-24-11 — Brainmaster 真实环境 fix + Reviewer P1 backlog 全部清零

**Branch**: `main` (HEAD `8e644bc`)
**Duration**: ~5 小时
**核心成就**：让 AI 路径真跑通（修 Windows 子进程 2 个 bug）+ 收掉 reviewer 留下的全部 4 个 P1 backlog。M2 工程债务降到 0。

## 关键事件（按时间顺序）

### 1. 用户问 "哪部分是 AI"
诚实回答：**0 条**。所有 130 条都是 `processed_by='rule'`（之前 demo 用 `--no-ai`，且 API key 没配）。

### 2. 验证 Brainmaster 可用
`claude` CLI v2.1.143 在 PATH ✅。零 API key 路径理论上可用。

### 3. 第一次跑 5 条全失败
"agent did not update outputs file" — subprocess exit=0 但文件没写。

### 4. Debug 双 bug

**Bug #1: `--permission-mode acceptEdits` 缺失**
- Claude CLI v2.1+ 在 `-p` 非交互模式下 Write 工具需要 permission
- 默认 mode 要求用户交互确认，非交互模式静默失败

**Bug #2: Windows `.CMD` wrapper 多行中文 prompt 乱码**
- `shutil.which('claude')` 返回 `claude.CMD`（npm wrapper）
- cmd.exe 转发多行中文 + 反引号会被字符集转换乱码

### 5. 修复 + 验证
- 加 `--permission-mode acceptEdits` + prompt 走 stdin（不走 argv）
- 5 条全部 `processed_by=agent:news-classifier-realtime` ✅
- AI vs 规则对比明显优势：
  - 马克龙伊朗战争 → AI 关联能源/军工/黄金 + 5 个 A 股代码
  - 俄罗斯央行降息 → AI 识别俄国≠中国央行，imp 5→3
  - 广东省方案 → AI 识别区域政策非全国级
- 加 2 个 regression test 锁住
- PR #4 开 + CI 5/5 全绿 + merge

### 6. 收掉 reviewer P1 backlog（4 个 fix）

| ID | 问题 | 修复 |
|----|------|------|
| **P1-1** | `_has_any_analysis` provider-agnostic → rule 锁死 AI 升级 | 改 `_has_analysis_for_current_path`，AI 路径只看 agent:*/sdk:* 行 |
| **P1-2** | 同 news 升档双 alert → M4 双推 | 新 alert 高于已有时把旧 pending 标 `superseded`（升档 only） |
| **P1-3** | 黑名单新闻仍生成 alert | AlertService 加 `blacklist_keywords` + `from_config()` 自动加载 |
| **P1-5** | asyncio.gather 共享 session race 隐患 | `Session(engine)` 每 task 独立 + `expunge` 让 detached 对象可访问 |

每个 fix 都有 regression test。PR #5 开 + CI 5/5 全绿 + merge。

## 关键决策

1. **跑全 130 条 AI 推迟**：每条 ~40s subprocess，130 条 ~90 分钟。本 session 已 5h，留下次。
2. **P1-2 只升档 supersede 不降档**：避免误丢 P0 历史告警痕迹（reviewer 没明说，我们的设计选择）
3. **P1-3 黑名单只 skip alert 不删 analysis**：保留 news_analysis 行可审计
4. **P1-5 fallback 共享 session**：engine 抓不到时退回原行为，兼容现有测试

## 产出

### 新增 / 修改（src）
- `src/amarket/adapters/ai/claude_agent_runner.py`（PR #4：permission-mode + stdin + 强化 prompt）
- `src/amarket/services/news/analysis.py`（PR #5：P1-1 provider-aware + P1-5 独立 session）
- `src/amarket/services/news/alert.py`（PR #5：P1-2 supersede + P1-3 blacklist + from_config）
- `src/amarket/cli.py`（PR #5：1 行 `AlertService.from_config`）

### 新增 / 修改（tests）
- `tests/unit/test_ai_providers.py`（PR #4：+2 Brainmaster regression）
- `tests/unit/test_news_analysis.py`（PR #5：+5 P1-1/P1-5 regression）
- `tests/unit/test_news_alert.py`（PR #5：+6 P1-2/P1-3 regression）

### Commits（main 上）
- `52dfb18 fix(brainmaster): Claude CLI v2.1+ 非交互模式两个真实环境兼容性问题 (#4)`
- `8e644bc fix(M2): address reviewer P1 backlog (4 fixes — pre-M3) (#5)`

## 当前 git 状态

```
main 历史（干净）:
├── 8e644bc fix(M2) P1 backlog (#5)              ⭐ 本 session
├── 52dfb18 fix(brainmaster) (#4)                ⭐ 本 session
├── 14ec945 docs M2 (#3)
├── 1773bbd feat(M2) (#2)
├── 034bb6e docs deployment (#1)
├── c40088c CI hotfix
└── c5236b2 M1 merge
```

## 当前 DB 状态
- 130 条新闻 + 12 条 A 股指数 + 130 NewsEvent
- 130 NewsAnalysis（125 行 `rule` + **5 行 `agent:news-classifier-realtime`** ⭐ 真 AI 分析）
- 73 Alert（1 P0 + 1 P1 + 71 P2）

## 测试 / 覆盖率
- **207 tests / 87.95% coverage**
- 从 195 → +2 PR #4 + +10 PR #5 = 207
- ruff / mypy / pytest 全绿；CI 双 PR 都 5/5 通过

## 下次 Session 接力点

**用户选定 M3 — 静态 HTML POC 页面**（Spec v3 §10.1）：

5 个页面：
1. **首页** — 顶部状态栏 + 主要指数 + 重要新闻 + 板块趋势
2. **新闻流页** — 长列表，按时间/重要性排序
3. **详情页** — 单条新闻 + 完整 AI 分析
4. **板块热力图** — 14 个板块的热度可视化
5. **日报页** — 6 时段日报展示

**预估**：2-3 session。

**启动前要决定**：
- 技术选型（vanilla HTML + JS / 还是带框架）
- POC 放哪（`poc/` 目录）
- 数据源（fetch /api/news + /api/alerts / mock）
- 是否要 build step

**M3 启动 checklist**：
1. 开 `feat/m3-poc-pages` 分支
2. 用 `superpowers:brainstorming` 走一遍（新模块设计要走流程）
3. 按 spec §10.1 实现 5 个页面
4. 用 gstack 截图验收

## 一句话总结

> Session 11：从 demo 一个问题"哪部分是 AI"出发，修了 Windows Brainmaster 2 个真实环境 bug（让 AI 路径真跑通）+ 收掉 reviewer P1 backlog 全部 4 个。
> M2 工程债务清零，main 历史干净，进 M3 准备就绪。
