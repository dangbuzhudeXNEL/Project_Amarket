# Session 2026-06-19-06 — M0/M1 合主线 + M2-a/M2-g 双路径 AI

**Branch**: `feat/m2-news-processing`（基于已合并的 main）
**Duration**: ~1.5 小时（含 merge main + M2-a + M2-g + 测试）

## 关键事件
1. **`feat/m0-project-skeleton` 合入 main** — M0 + M0+ + M1 三个 commit 一起合并 (`c5236b2`)
2. **新开 `feat/m2-news-processing` 分支** — 正式遵守 PR 流程
3. **M2-a 完成** — 3 个规则 YAML（关键词 / 板块 / 分类）
4. **M2-g 完成** — Brainmaster + SDK 双路径 AI 架构（用户特别要求提前到 M2）

## M2-g 双路径 AI 设计核心

```
Service 层 (NewsAnalysis)
    ↓ 只 import AIProvider Protocol
    ↓
FallbackChainProvider (factory)
    ├─ Tier 1: ClaudeAgentRunner (Brainmaster, 零 API key)
    │       ↓ subprocess(claude --agent news-classifier-realtime -p ...)
    │       → data/ai/outputs/<news_id>.json
    ├─ Tier 2: AnthropicSDKProvider (走 API key)
    └─ Tier 3: DeepSeekSDKProvider (OpenAI 兼容协议)
    ↓ 全部失败
SimpleRuleScorer (M2-d 实施)
```

任一 Tier 失败自动切下一个。Service 一行代码不变。

## 关键决策
- **Brainmaster 从 Phase 2 提前到 M2**：用户原话"我们当前先用本地的 claude code，也兼容加其他模型 API 的方式去做"
- **三层 fallback 用 `FallbackChainProvider` 组合**：避免每个 Service 都写降级代码
- **agent 输入/输出走文件**：`data/ai/inputs/<news_id>.json` + `data/ai/outputs/<news_id>.json`，天然支持审计 / 回放 / 重处理

## 产出
- 3 个 YAML 配置（keywords / sectors / classification）
- 5 个 src/adapters/ai/* 文件（base / claude_agent_runner / sdk_providers / factory + __init__）
- 1 个 agent 定义（news-classifier-realtime.md）
- 1 个配置文件（agents.yml）
- 1 个测试文件（20 个新 case）
- **111 tests passed / 87.70% coverage**

## 下次 Session 接力点
**Phase 1 M2 剩余子任务**（按依赖排序）：
- M2-b NewsDeduper（三层去重 + events 聚合）
- M2-c NewsClassifier（用 M2-a 规则做一级 / 二级分类 + 板块 / 标的关联）
- M2-d SimpleRuleScorer（重要性 / 紧急度 / 情绪规则评分）
- M2-e NewsAnalysis service（编排 Classifier → AIProvider 或 Scorer → 写 news_analysis 表）
- M2-f AlertService（P0-P3 决策表 + alerts 表写入）
- M2-h API 升级（/api/news 返回带分析字段 + /api/alerts）
- M2-i Dashboard 升级（新闻列表显示标签/评分/告警等级）
- M2-j 集成测试（把 M1 抓的 100 条真新闻喂进 pipeline）
- M2-k 收尾 commit

预估 2-3 个 session 完成 M2 全部 b/c/d/e/f/h/i/j/k。

## 一句话总结

> Session 06：M0/M1 入主线 + M2 开场（规则文件 + AI 双路径架构）。下次 session 进 NewsDeduper → Classifier → Scorer → AlertService，真实把 100 条新闻跑过完整 pipeline。
