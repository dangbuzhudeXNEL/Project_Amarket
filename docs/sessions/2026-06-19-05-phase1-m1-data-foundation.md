# Session 2026-06-19-05 — Phase 1 M1 实施（数据基座 + 3 源新闻 + 行情）

**Duration**: ~2.5 小时（含 spike + 实施 + 调坑 + 测试）
**Branch**: `feat/m0-project-skeleton`（M0 + M0+ + M1 同分支累计）
**Goal**: 完成 Phase 1 M1 — 把 11+ 张表 schema、3 个新闻源、akshare 行情源、Repos / API / Service / CLI / Streamlit viz 全跑通

## 关键产出
- **DB**：16 张业务表 + alembic auto-gen migration 应用成功
- **3 个新闻源**：东方财富 / 新浪 / 雅虎财经全部真实抓取通（首次 `amarket collect news --full` 100 条入库 / 3.1s）
- **行情源**：akshare 串行调通（绕过 mini_racer crash），首次 `amarket collect market` 6 个 A 股指数入库
- **Repos / API / Service / CLI / Streamlit** 全部对齐
- **91 tests passed / 90.14% coverage**

## 关键决策
- 在同一 `feat/m0-project-skeleton` 分支继续 M1（M0 + M1 一起合 PR），便于一次 review；不开新分支避免 rebase 麻烦
- 主源 = 东财（接口稳）；备 = 新浪 + 雅虎；Spec v3 写的财联社 / 同花顺 / 华尔街见闻 endpoint 暂未验证，留 M2+ 扩展

## 工程坑（修复 4 个）
1. alembic.ini 中文 em-dash → 改 ASCII（Windows cp1252 locale）
2. akshare mini_racer 并发 native crash → 串行调用
3. Windows console cp1252 输出 emoji 挂 → cli.py 入口 reconfigure stdout=utf-8
4. SQLite `:memory:` per-connection 隔离 → conftest 用 StaticPool

## 下一次 Session 接力点
- 用户决定 feat/m0-project-skeleton 分支 merge 策略
- 进入 Phase 1 M2：新闻去重 (URL/SimHash/events) + 一级 8 类 + 二级 14+ 标签 + 重要性/紧急度评分 + P0-P3 告警决策

## 一句话总结

> Session 04+05：M0 + M0+ + M1 全在同一 feature branch（3 commits）。**100 条真实新闻 + 6 个 A 股指数已入库**；91 tests / 90.14% 覆盖率。下次 session 决定怎么合 main，然后进 M2。
