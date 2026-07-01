# Session 2026-06-30-14 — PR #17 post-M3b polish + Brainmaster agent B demo

**Branches**: `fix/poc-script-load-order` (merged as PR #17) → `main` → `docs/session-14-wrap` (this wrap)
**Duration**: 分散在 3 天（2026-06-25 尾巴 → 6/26 → 6/27 → 6/30；主动作 ~2h）
**核心成就**：三件事
1. 用 gstack 浏览器 dogfood 发现 3 个 M3a/M3b pre-existing 问题 → PR #17 一并修完 merge
2. 手动跑完整 pipeline（`collect market` + `collect news` + `dedupe` + `analyze`）验证 M3b 端到端可用
3. 实测 Brainmaster agent 路径（`analyze news --reanalyze --limit 20`）为 M4 调度设计提供量化数据

## 关键事件

### 阶段 A — gstack 浏览器 dogfood + PR #17

1. **Session 启动**：CLAUDE.md → PROJECT_STATE → 上一篇 session 13 log → git log → gh pr list
2. **用户提出"我看下现在什么样子"** → 用 gstack skill 启无头浏览器 + FastAPI + curl smoke
3. **发现问题 1**：index.html 空白，console 报 `Alpine Expression Error: indexPage is not defined` 一大串
   - 根因：Alpine 和 page JS 都用 `defer`；按 HTML 规范同为 defer 时按 document order 执行，Alpine 声明在前 → 立即 `Alpine.start()` → x-data 评估失败
   - 修：去掉 6 个 POC HTML 里 page JS 的 `defer`（Alpine 保留）
4. **用户提出"具体 AI 分析看不到"** → 发现 `/api/news/{id}` 只返回 `NewsCardDTO` 8 字段，缺 `ai_reasoning / related_sectors / related_symbols / risk_notes / content / related_news / 6 评分` 等 11 个 detail 字段
   - 修：新增 `NewsDetailDTO` + `RelatedNewsDTO` DTO；`/api/news/{id}` 返回 detail；列表保持 card 轻量；`_latest_analysis_for` 优先取 agent/sdk 分析
5. **附带发现**：sectors 页面所有 change_pct=null 时显示 `+null%` + 假绿色（视觉误导）
   - 修：null 时显示 `—` + 中性灰 + tooltip 写明 `M4 接调度后填充`
6. **PR #17 开 + 扩展** → CI 5/5 → **squash merge 到 main (`f96b944`)**
7. **验证**：news-detail 页 #39/#191 展示完整 AI 分析（agent 深度分析质量：影响板块带权重、具体标的、AI 推理、风险提示）；sectors 视觉修好

### 阶段 B — 数据陈旧发现 + 手动 refresh

8. **用户观察"数据好像没有更新"** — 发现 DB 数据停留在 6/19 落库时间
9. **说明**：M3b 只做读端点，采集/分析没自动调度（M4 的核心交付）
10. **手动跑完整 pipeline 演示**（6/26 22:44）：
    - `uv run amarket collect market` → +6 快照（今日大跌 -2 ~ -4%）
    - `uv run amarket collect news --full` → 100 条新闻（eastmoney 50 + sina 30 + yahoo 20）
    - `uv run amarket dedupe news` → 99 新 events
    - `uv run amarket analyze news --no-ai` → 50 rule 分析 + 23 P2 alerts
11. Dashboard 刷新后新数据全上：230 news / 96 alerts / 22:46 数据时间

### 阶段 C — Brainmaster agent B demo

12. **用户问 A（开 M4） vs B（agent demo）方向选择** → Claude 推荐先 B（5 min sunk cost、高信号、给 M4 决策数据）
13. **确认 agent 路径**：`claude` CLI 在 PATH ✓，`news-classifier-realtime.md` agent 定义存在 ✓，无 API key → 直接走 Brainmaster
14. **跑 B**（6/30 22:35）：`uv run amarket analyze news --reanalyze --limit 20 --concurrency 5`
    - 结果：**AI 成功率 90%**（18/20），2 条 JSON parse 失败降级到 rule
    - 单条 ~15s，总 ~90s
    - 新增 2 P1 + 5 P2 alerts；1 次 `alert.superseded`
15. **质量抽查**：
    - #191 洪水 → agent 识别 **农业 60% / 保险 50% / 水利建设 50% / 水务 40%** + 中国人保/太保 + "危机趋于缓解 → 情绪中性" + 情景升级风险
    - #192 IPO 双增 → agent 识别 **半导体 80% / 券商投行 75% / 生物医药 60% / 新材料 60% / 高端装备 60%** + 引用 +35% / +88% 数据 + 流动性分流风险
16. Dashboard 刷新后：P0/P1 面板从 2 → 4（新增伊朗锡里克港 P1 + 特朗普综合要闻 P1）

### 阶段 D — M4 拆分决策 + Session wrap

17. **讨论 M4 范围**：
    - **M4-mini**：APScheduler + 行情/新闻调度 + SectorTrendService 写表（无外部依赖，1 session）
    - **M4-full**：追加 6 时段 ReportService + NewsPusher 真推送（需要 webhook + LLM 决策）
    - 决策：先做 M4-mini（避免被外部配置阻塞），M4-full 等 webhook 齐再动
18. **用户请求 session wrap** → 开 `docs/session-14-wrap` 分支，更新 PROJECT_STATE + CHANGELOG + 本日志 → 收尾 PR

## 关键决策

1. **PR #17 一次修完 3 个问题不拆** — 都是 M3a/M3b post-merge 发现的小问题，一个 PR 更清晰；code review 已够严格（inline diff review + CI 5/5）
2. **`/api/news/{id}` 单独用 `NewsDetailDTO`，列表继续用 `NewsCardDTO`** — 列表要轻，详情要全；不共享 DTO
3. **`_latest_analysis_for` 优先取 agent/sdk 而非 rule** — 深度分析优先展示；这个也影响 `/api/dashboard/summary` 的 `latest_news` 质量
4. **M4 拆 M4-mini / M4-full** — 避免因为 webhook / API key 依赖阻塞进度；mini 完成后 dashboard 已经自动化，M4-full 可以等 owner 给外部依赖
5. **Brainmaster 主 AI 路径 + SDK fallback** — Session 14 实测 90% 成功率、单条 15s、零 API key，进一步验证 spec v3 §12.2 决策
6. **保留 rule 降级链** — 10% AI parse 失败率决定了必须保留 rule 兜底（M2 已建，M4 不要去掉）

## 产出

### 修改（PR #17，3 commits）
- `poc/{index,news,news-detail,sectors,reports,params}.html` — 6 个 HTML 去掉 page JS `defer`
- `src/amarket/domain/schemas.py` — 加 `NewsDetailDTO` + `RelatedNewsDTO`；`__all__` 从 17 → 19
- `src/amarket/api/news.py` — `_to_detail` 新 helper + `_related_news_for` join + `_latest_analysis_for` 排序改成 agent/sdk 优先；`get_news` 返回 `NewsDetailDTO`
- `poc/assets/js/pages/sectors.js` — null change_pct/market_cap_weight 优雅降级 label + color + tooltip
- `tests/unit/test_api_news_dashboard.py` — 新增 `test_api_news_get_by_id_returns_detail_fields` 覆盖 11 个 detail-only 字段

### 数据变化（B demo）
- 6/26 手动 refresh：DB 从 130 news → 230 news / 12 → 18 market / 73 → 96 alerts
- 6/30 agent demo：+18 agent 分析 + 2 P1 + 5 P2 alerts → 最终 203 analyses（180 rule + 23 agent）/ 103 alerts

### Commits（main 上 2 个新的：PR #17 + 本 session wrap）
- `f96b944 fix(poc): post-M3b polish — Alpine load order + full news-detail AI + sectors null UX (#17)`
- (本 session wrap PR — 待 merge)

### Docs
- `docs/PROJECT_STATE.md` — 全面更新（session 14 状态 + M4 拆分 + DB 现状 + 阻塞更新）
- `CHANGELOG.md` — 加 Session 14 大段
- `docs/sessions/2026-06-30-14-post-m3b-polish-and-agent-demo.md`（本文件）

## 当前 git 状态

```
main 历史（干净）:
├── f96b944 fix(poc): post-M3b polish (#17)         ⭐ Session 14 早期
├── 799dc57 feat(m3b): Dashboard API + frontend (#16)   ← Session 13 尾
├── eeb4f5d docs(readme): M3a status sync (#15)
├── 1b97b34 docs: session 12 final wrap (#14)
├── caf4c82 feat(M3a-PR2) (#13)
└── ...
```

## 当前 DB / POC 数据状态

- **DB**：230 NewsItem + 229 NewsEvent + 203 NewsAnalysis（180 rule + 23 agent）+ 103 Alert（1 P0 + 3 P1 + 99 P2）+ 18 MarketSnapshot
- **POC**：6 个页面同源 mount 到 `/poc`，fetch `/api/*` 真数据，polling toggle 可点，news-detail 完整 AI 分析可见

## 测试 / 覆盖率
- **253 tests / 87.97% coverage**（+1 detail 字段测试）
- ruff / ruff format / mypy 全绿；CI 5/5 通过

## 下次 Session 接力点

**直接开 M4-mini — 调度自动化，无外部依赖**：

范围：
- APScheduler 集成 FastAPI lifespan
- 行情快照调度（交易时段每 5min）
- 新闻轮询调度（每 60s）→ dedupe → analyze（Brainmaster）
- SectorTrendService 写表调度（每 15min）→ sectors 页 change_pct 真有值
- `/api/dashboard/scheduler-status` 端点

预估：1 session。

**M4-mini 启动 checklist**：
1. 开 `feat/m4-mini-scheduler` 分支
2. 进 `superpowers:writing-plans` 写 M4-mini plan（spec v3 §6.1.7/§17.1 已定义，无需 brainstorm）
3. 实施 + 验证 + PR + merge
4. 讨论 M4-full 依赖（webhook / 日报 AI 决策）

## 一句话总结

> Session 14：gstack 浏览器 dogfood 揪出 3 个 pre-existing UX/API 问题 → PR #17 打包修完 merge → 手动跑完整 pipeline 验证 M3b → Brainmaster agent 实测 90% 成功率 + 深度分析质量（次生板块识别 + 情景风险提示） → 用 B 的数据把 M4 拆成 mini (无依赖) / full (需 webhook)。
> 下次直接开 M4-mini，1 session 让 dashboard 完全自动化。
