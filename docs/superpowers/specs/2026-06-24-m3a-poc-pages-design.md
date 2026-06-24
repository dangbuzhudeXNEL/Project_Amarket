# Spec — M3a POC 前端页面设计（静态 HTML，mock 数据驱动）

**Status**: Draft v1
**Date**: 2026-06-24
**Author**: Claude（在 Session 12 brainstorming 产出）
**Reviewer**: 项目负责人
**Related**:
- 上游：[Spec #1 v3 §10.1 看板首页布局 + §10.2 API 端点 + §17.1 M3 里程碑](2026-06-19-spec1-v3-merged.md)
- 后续：M3b POC → API 联通设计（待出）；M5 真实参数模块设计（待出）

---

## 0. TL;DR

本 spec 描述 Phase 1 M3 拆分后的 **M3a — 静态 HTML POC 页面**。M3a 用 mock JSON 数据驱动 6 个页面（5 个 OKX 暗色金融风 + 1 个赛博朋克参数空壳），不依赖后端 API；M3b 阶段会接入真实 `/api/*`。

**核心承诺**：M3b 接 API 时，每页只改一行 `fetch()` URL，其他代码 zero change。

---

## 1. 背景与拆分动机

### 1.1 上游里程碑定义（spec v3 §17.1 原文）

> **M3：看板 API + 静态 POC 前端**
> 关键交付：`/api/dashboard/*` `/api/news` `/api/alerts` 完整、`SectorTrendService` 计算、静态 HTML POC（首页 + 新闻流 + 板块热力图 + 详情页 + 日报页）
> 完成判定：浏览器打开 POC 能在 5 分钟内完整演示；API 文档（Swagger）齐全。

### 1.2 为什么拆 M3a / M3b

M3 同时包含两个独立子系统：

| 子系统 | 工作量 | 跨依赖 |
|--------|--------|--------|
| 看板 / 告警 API + SectorTrendService | 后端 Python，~2-3 大模块 + 单测 | 依赖 NewsRepo / AlertRepo / MarketSnapshotRepo |
| 6 个静态 HTML 页面 | 前端 HTML/CSS/JS，UI 设计 + ECharts | 依赖任何能返回正确 schema 的数据源 |

**拆分逻辑**：前端可以用一份 JSON dump 当数据源独立开发；后端有了前端的 schema 倒推会更稳；前端早出能让小组成员、产品负责人提前看到效果给反馈。

**M3a 范围**：6 个静态 HTML 页面 + 一次性 DB dump 脚本 + python http.server 启动方式。
**M3b 范围**（出独立 spec）：补齐 dashboard/sectors/alerts 等 API + SectorTrendService + 前端 fetch URL 切换 + 加 30s 自动刷新。

---

## 2. 目标与非目标

### 2.1 目标

1. 浏览器打开 `http://127.0.0.1:8090` 能在 **5 分钟内完整 demo** 6 个页面（spec §17.1 完成判定）
2. 设计风格：**5 个核心页面统一 OKX 暗色金融风**（dark base + 蓝青强调 + 红绿涨跌色 + 卡片化）
3. 参数页：**赛博朋克实验风**（霓虹 cyan/magenta + 等宽字体 + 辉光效果），与主站形成"管理后台 / hacker 区"的视觉对比
4. 数据从 DB dump 出真实 130 条新闻 / 73 alerts / 12 行情快照，保证真实分布
5. 0 build step、0 npm install、0 注册账号、零 API key
6. **M3b 接 API 时改动 ≤ 6 行**（每页 1 行 fetch URL）

### 2.2 非目标（M3a 不做）

- ❌ 任何后端代码（FastAPI router、Service、Repo）
- ❌ 任何 SectorTrendService 计算逻辑（M3b 干）
- ❌ 任何 API 端点定义实现（M3b 干）
- ❌ 移动端 / 平板适配（桌面 ≥ 1280px 唯一目标）
- ❌ 用户认证 / 权限（Phase 1 单角色，参数页只是空壳）
- ❌ 真实数据刷新（M3a 数据是快照，M3b 才会有 30s polling）
- ❌ 国际化 / 多语言（中文唯一）
- ❌ Streamlit 面板（仍由 M0+ 的现状继续，不动）
- ❌ 任何 SPA 框架（违反"静态 HTML POC"定义）
- ❌ params 页的真实交互（M5 真实参数模块时再做）

---

## 3. 页面清单

6 个 HTML 文件，前 5 个 OKX 风，最后 1 个赛博朋克。

| # | 文件 | 标题 | 主题 | spec v3 §10.1 对应 |
|---|------|------|------|-------------------|
| 1 | `index.html` | 首页 Dashboard | OKX | 整体 9 区域 |
| 2 | `news.html` | 新闻流 | OKX | 区域 ③ 单独成页 |
| 3 | `news-detail.html` | 新闻详情 | OKX | 单条新闻 + AI 分析 |
| 4 | `sectors.html` | 板块热力图 | OKX | 区域 ⑤ 单独成页 |
| 5 | `reports.html` | 6 时段日报 | OKX | 区域 ⑨ 单独成页 |
| 6 | `params.html` | 参数配置（空壳） | 赛博朋克 | 非 spec §10.1 范围，M5 真实，M3a 提前占位 |

### 3.1 index.html — Dashboard 首页

**目的**：一屏看完整体市况、最重要的新闻、热点板块、告警。

**布局**（按 spec §10.1）：

```
┌────────────────────────────────────────────────────────────────────┐
│ Topbar: Logo │ Nav (首页/新闻流/板块/日报/参数)│ 刷新toggle │ 时间 │
├────────────────────────────────────────────────────────────────────┤
│ ① 市场状态栏（横向滚动条 / 11 个指数 + 外汇 + 大宗）              │
├────────────────────────────────────────────────────────────────────┤
│ ② 今日核心结论（来源：盘前日报 / M3a 暂时占位 / 一条 callout）    │
├──────────────────────────┬─────────────────────────────────────────┤
│ ③ 实时新闻流（左 6/12）   │ ④ P0/P1 重要新闻卡片（右 6/12 上半）   │
│                          │                                         │
│ 时间 ｜ 来源 ｜ 标题      │ ┌─ P0 (红) ─┐  ┌─ P0 (红) ─┐         │
│ 分类标签 ｜ 重要性 ｜情绪 │ │  ...     │  │  ...      │         │
│ [板块×3] [标的×2]         │ └──────────┘  └───────────┘         │
│                          │                                         │
│ [筛选: 来源/分类/情绪/    │ ⑤ 板块热力图（top 14 板块）             │
│  重要性 multi-select]    │     ECharts treemap，颜色按涨跌幅       │
│                          │                                         │
│ [虚拟滚动 / 显示前 30]    │ ⑥ 新闻影响板块榜（top 10 文本表）       │
│                          │ ⑦ 个股异动榜（top 10）                  │
│                          │ ⑧ 突发告警区（置顶 P0 / P1 时间线）     │
├──────────────────────────┴─────────────────────────────────────────┤
│ ⑨ 日报入口（6 时段卡片：盘前/早盘/午间/尾盘/收盘/晚间，灰=未生成） │
└────────────────────────────────────────────────────────────────────┘
```

**数据源**：
- `assets/data/dashboard.json` (聚合)
- `assets/data/news.json` (取前 30 条到区域 ③)
- `assets/data/alerts.json` (取 P0 / P1 到区域 ④/⑧)
- `assets/data/sectors.json` (区域 ⑤/⑥)

**交互**：
- 顶部导航跳转其他页（HTML link，无 SPA）
- 新闻条点击 → 跳 `news-detail.html?id={news_id}`
- 板块格子点击 → 跳 `sectors.html#{sector_name}`
- 日报卡片点击 → 跳 `reports.html?kind={kind}`
- 筛选器：纯前端 Alpine `x-model` 过滤
- 刷新 toggle：M3a 仅 UI 占位（不实际 poll），M3b 接 setInterval

### 3.2 news.html — 新闻流

**目的**：长列表 + 多维度筛选，给"我要找 X 主题新闻"的场景。

**布局**：

```
┌────────────────────────────────────────────────────────────────────┐
│ Topbar (同 index)                                                  │
├──────────┬─────────────────────────────────────────────────────────┤
│ 左侧栏    │ 主区域                                                 │
│ 240px    │                                                         │
│          │ ┌─ 筛选 bar：来源 ▾ 分类 ▾ 情绪 ▾ 重要性 ▾ 时段 ▾  搜索 │
│ 来源     │ │  已选: [央行官网] [宏观政策]  清空                    │
│ □ 央行   │ └─────────────────────────────────────────────────────┐ │
│ □ 同花顺 │                                                       │ │
│ □ 财联社 │ 共 87 条结果 / 按 时间▾ 重要性 情绪 排序                │ │
│ ...      │                                                       │ │
│          │ ┌──────────────────────────────────────────────────┐  │ │
│ 分类     │ │ 2026-06-24 13:42  央行官网                      │  │ │
│ □ 宏观   │ │ 央行降准 0.25%                            ★★★★★  │  │ │
│ □ 行业   │ │ [宏观政策] [货币政策] 情绪: 强利多 |紧急度 5|置信 5│  │ │
│ □ 公司   │ │ 影响板块: 券商 0.9, 地产链 0.7  |标的: 中国平安 │  │ │
│ ...      │ └──────────────────────────────────────────────────┘  │ │
│          │ ...（虚拟滚动加载更多）                                │ │
│ 情绪      │                                                       │ │
│ ...      │                                                       │ │
└──────────┴───────────────────────────────────────────────────────────┘
```

**数据源**：`assets/data/news.json`（全量 130 条 → 前端筛选）

**交互**：
- 左侧 checkbox 多选筛选
- 顶部排序切换
- 点条目 → `news-detail.html?id={id}`
- 长列表用纯 CSS `overflow-y: auto` + Alpine `x-show` 过滤（130 条不需要虚拟滚动）

### 3.3 news-detail.html — 新闻详情

**目的**：单条新闻 + 完整 AI 分析 + 原文链接 + 相关新闻。

**布局**：

```
┌────────────────────────────────────────────────────────────────────┐
│ Topbar                                                              │
├────────────────────────────────────────────────────────────────────┤
│ ← 返回新闻流                                                        │
│                                                                     │
│ ╔════════════════════════════════════════════════════════════════╗ │
│ ║ 央行降准 0.25%                                                  ║ │
│ ║ 2026-06-24 13:42 · 央行官网 · 原文链接 →                        ║ │
│ ║ [宏观政策] [货币政策]                                           ║ │
│ ╚════════════════════════════════════════════════════════════════╝ │
│                                                                     │
│ ┌── 摘要 ────────────────────────────────────────────────────────┐ │
│ │ 央行宣布 ...                                                   │ │
│ └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌── AI 分析（agent:news-classifier-realtime / Brainmaster）─────┐ │
│ │ 重要性 ★★★★★    紧急度 5    情绪 强利多    置信度 5            │ │
│ │ 影响时长 即时    操作建议 关注                                  │ │
│ │ 影响板块: 券商 0.9 · 地产链 0.7 · 房地产 0.6                    │ │
│ │ 关联标的: 中国平安 (601318) · 招商银行 (600036)                 │ │
│ │ 告警等级: P0    已推送: ✓                                       │ │
│ │ 分析理由: ...                                                   │ │
│ └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌── 相关新闻（同事件 news_event_id）─────────────────────────────┐ │
│ │ - 同事件下另外 N 条                                             │ │
│ └────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

**数据源**：`assets/data/news-detail-{id}.json`（dump 5 条样本，URL 参数取 id）

**交互**：
- URL 形如 `news-detail.html?id=12345`，Alpine 取 `URLSearchParams` 拼 fetch 路径
- 不存在的 id → 显示 "新闻不存在，[返回列表]"
- 原文链接 → `target="_blank" rel="noopener"`

### 3.4 sectors.html — 板块热力图

**目的**：14 个板块的热度可视化（涨跌幅 + 新闻热度）+ 联动新闻。

**布局**：

```
┌────────────────────────────────────────────────────────────────────┐
│ Topbar                                                              │
├────────────────────────────────────────────────────────────────────┤
│ 板块热力图  ｜ 时间窗口: [1h 4h 1d] ｜ 维度: [涨跌幅▾ 新闻热度]    │
├────────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────────┐  │
│ │ ECharts Treemap（14 板块，按市值或新闻数权重，颜色按涨跌幅）  │  │
│ │ ┌───────────┐ ┌────────┐ ┌─────┐                            │  │
│ │ │  券商     │ │ 半导体 │ │银行 │  ← hover 显示详情 tooltip   │  │
│ │ │  +3.2%    │ │ +1.1%  │ │ -0.5│                            │  │
│ │ │  18 条新闻│ │ 12 条  │ │ 8 条│                            │  │
│ │ └───────────┘ └────────┘ └─────┘                            │  │
│ │ ...                                                          │  │
│ └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│ 选中板块: 券商                                                      │
│ ┌── 该板块最近新闻（top 20）──────────────────────────────────┐    │
│ │ 时间 | 标题 | 重要性 | 情绪 | 权重                          │    │
│ └─────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────┘
```

**数据源**：`assets/data/sectors.json` + `assets/data/news.json`（按 related_sectors 过滤）

**交互**：
- ECharts `treemap` series，颜色映射 -3% → 红 / 0% → 灰 / +3% → 绿
- 格子点击 → 下半部分加载该板块相关新闻
- 时间窗口切换：M3a UI 占位（数据不分窗口），M3b 接 API 时支持
- 维度切换：M3a 数据按 mock 给两套权重，前端切换即可

### 3.5 reports.html — 6 时段日报

**目的**：展示日报内容。

**布局**：

```
┌────────────────────────────────────────────────────────────────────┐
│ Topbar                                                              │
├────────────────────────────────────────────────────────────────────┤
│ 日报 ｜ 日期: 2026-06-24 ▾ ｜ [盘前] [早盘] [午间] [尾盘] [收盘]  │
│                                                       [晚间]        │
├────────────────────────────────────────────────────────────────────┤
│ 当前: 盘前日报 · 生成于 07:58:14 · agent:daily-report-writer       │
│                                                                     │
│ ╔════════════════════════════════════════════════════════════════╗ │
│ ║ ## 隔夜美股                                                     ║ │
│ ║ - 道指 +0.5%，纳斯达克 +1.2%                                    ║ │
│ ║ - 半导体板块领涨，AMD +3%                                       ║ │
│ ║                                                                ║ │
│ ║ ## 政策面                                                       ║ │
│ ║ - 央行降准 0.25%                                                ║ │
│ ║ ...                                                            ║ │
│ ╚════════════════════════════════════════════════════════════════╝ │
│ （Markdown 渲染：marked.js CDN）                                    │
└────────────────────────────────────────────────────────────────────┘
```

**数据源**：`assets/data/reports.json`（M3a 给 1 份盘前日报 mock；其他 5 时段为 null → 显示"未生成"）

**交互**：
- 日期选择器：M3a 仅当天可选
- 时段 tab 切换
- 未生成时段 → 灰禁用 + "等待 M4 调度"
- M5 会加"重新推送"按钮

### 3.6 params.html — 参数配置（赛博朋克空壳）

**目的**：占位 + 赛博朋克实验。M5 才真正实现。

**布局**：

```
┌────────────────────────────────────────────────────────────────────┐
│ ▓▓▓ A M A R K E T   C O N S O L E ▓▓▓                  [scan-line]│
├────────────────────────────────────────────────────────────────────┤
│ > params.config_manager v0.0.1_alpha                               │
│ > 加载中... ████████████░░░░ 75%                                   │
│                                                                     │
│ ┌──[ DATA SOURCES ]──────────────────────────────────────────────┐│
│ │   sources.ths.enabled            = TRUE      ░ EDIT             ││
│ │   sources.eastmoney.enabled      = TRUE      ░ EDIT             ││
│ │   sources.yahoo.enabled          = FALSE     ░ EDIT             ││
│ │   news.realtime_poll_seconds     = 60        ░ EDIT             ││
│ └────────────────────────────────────────────────────────────────┘│
│                                                                     │
│ ┌──[ KEYWORDS ]──────────────────────────────────────────────────┐│
│ │   keywords.涨停.weight           = 0.8       ░ EDIT             ││
│ │   keywords.降准.weight           = 1.0       ░ EDIT             ││
│ └────────────────────────────────────────────────────────────────┘│
│                                                                     │
│ > [ROLLBACK]  [DIFF]  [AUDIT_LOG]                                   │
│ > █ system standby — M5 will activate                              │
└────────────────────────────────────────────────────────────────────┘
```

**视觉**：
- 深紫 / 黑底（`#0a0014` / `#14082c`）
- 霓虹 cyan (#00f5ff) 主字 + magenta (#ff006e) 强调 + 电黄 (#fcff00) 警示
- 等宽字体（JetBrains Mono / Fira Code via CDN）
- CSS `text-shadow` 模拟辉光
- CSS animation: scan-line 缓慢上下移、光标闪烁
- "EDIT" 按钮点了显示 toast "M5 will unlock this"

**数据源**：`assets/data/params.json`（手写 ~15 个参数样本，纯 read-only 展示）

**交互**：
- 任何 EDIT / ROLLBACK 等按钮点击 → toast "Coming in M5"
- 仅作风格 demo

---

## 4. 技术栈与依赖

### 4.1 核心栈（全部 CDN，0 build，0 npm）

| 库 | 版本 | CDN | 用途 | 协议 |
|----|------|-----|------|------|
| Tailwind CSS | 3.x | `https://cdn.tailwindcss.com` | 原子化 CSS + 暗色 token | MIT |
| Alpine.js | 3.x | `https://unpkg.com/alpinejs@3` | 轻量响应式（filter/tab/poll toggle） | MIT |
| ECharts | 5.x | `https://cdn.jsdelivr.net/npm/echarts@5` | treemap 热力图 + sparkline | Apache 2.0 |
| Marked.js | latest | `https://cdn.jsdelivr.net/npm/marked` | 日报 Markdown 渲染（reports.html 用） | MIT |

### 4.2 字体（Google Fonts CDN）

每个 HTML 在 `<head>` 引入：

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap">
```

`params.html` 额外加 Orbitron：

```html
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&display=swap">
```

| 用途 | 字体 |
|------|------|
| OKX 正文 | Inter（fallback: system-ui, -apple-system, "Segoe UI", Roboto） |
| OKX 数字 | JetBrains Mono（fallback: "SF Mono", Menlo, Consolas） |
| 赛博朋克 标题 | Orbitron（fallback: monospace） |
| 赛博朋克 正文 | JetBrains Mono |

国内可换 `fonts.googleapis.cn` 镜像；或脱机方案下载到 `assets/vendor/fonts/`。

### 4.3 后续脱离 CDN 的迁移路径

如果未来要离线 / 加速 / 不依赖外网，把 4 个 JS / 1 个 CSS 下载到 `poc/assets/vendor/` 修改引用即可。M3a 不做。

---

## 5. 目录结构

```
poc/                              # 🆕 项目根新增（spec §15 已预留）
├── README.md                     # 启动说明 + 浏览器要求 + 截图
├── serve.bat                     # Windows 启动脚本
├── serve.sh                      # Linux/macOS 启动脚本
│
├── index.html                    # ① 首页 dashboard
├── news.html                     # ② 新闻流
├── news-detail.html              # ③ 新闻详情（?id=...）
├── sectors.html                  # ④ 板块热力图
├── reports.html                  # ⑤ 6 时段日报
├── params.html                   # ⑥ 参数空壳（赛博朋克）
│
├── assets/
│   ├── css/
│   │   ├── theme-okx.css         # OKX 配色 + 共享组件类
│   │   └── theme-cyberpunk.css   # 赛博朋克专属（params.html 引入）
│   ├── js/
│   │   ├── shared.js             # fetch wrapper / 数字格式化 / 时间格式化 / 颜色映射
│   │   ├── nav.js                # 顶部 nav 渲染（自动高亮当前页 by location.pathname）
│   │   └── pages/                # 每页一个文件（按需切分）
│   │       ├── index.js
│   │       ├── news.js
│   │       ├── news-detail.js
│   │       ├── sectors.js
│   │       ├── reports.js
│   │       └── params.js
│   └── data/                     # ← M3b 时这层被绕开（fetch URL 换 /api/*）
│       ├── dashboard.json
│       ├── news.json
│       ├── news-detail-12345.json (5 条样本)
│       ├── news-detail-12346.json
│       ├── news-detail-12347.json
│       ├── news-detail-12348.json
│       ├── news-detail-12349.json
│       ├── alerts.json
│       ├── sectors.json
│       ├── reports.json
│       └── params.json
│
└── (无 node_modules、无 dist、无 build)

scripts/
└── dump_poc_fixtures.py          # 🆕 一次性 DB → poc/assets/data/*.json
```

**根目录变化**：仅增加顶层 `poc/` 目录。其他目录不动。

---

## 6. 视觉设计系统

### 6.1 OKX 暗色主题（theme-okx.css）

#### 配色 token

```css
:root[data-theme="okx"] {
  /* 背景层 */
  --bg-base: #0c0d0f;          /* 页面底色 */
  --bg-card: #16181c;          /* 卡片底色 */
  --bg-hover: #1f2227;         /* hover 加深 */
  --bg-input: #1a1c20;         /* input / select 底色 */

  /* 边框 */
  --border-default: #2a2d33;
  --border-focus: #4a4d55;

  /* 文字 */
  --text-primary: #e8e9ea;     /* 标题、主要内容 */
  --text-secondary: #9a9ba0;   /* 次要信息 */
  --text-muted: #5f6063;       /* 时间戳、辅助说明 */

  /* 品牌强调 */
  --accent: #00b4d8;           /* 链接、active tab、focus ring */
  --accent-hover: #0091ad;

  /* 涨跌色 */
  --up: #14b143;               /* 涨 / 利好 / P3 绿 */
  --up-soft: rgba(20, 177, 67, 0.12);
  --down: #ef454a;             /* 跌 / 利空 / P0 红 */
  --down-soft: rgba(239, 69, 74, 0.12);

  /* 告警等级 */
  --p0: #ef454a;
  --p1: #f7931a;
  --p2: #00b4d8;
  --p3: #14b143;

  /* 情绪色（与告警一致 + neutral） */
  --sentiment-strong-bull: #14b143;
  --sentiment-bull: #5fb985;
  --sentiment-neutral: #9a9ba0;
  --sentiment-bear: #f08585;
  --sentiment-strong-bear: #ef454a;
}
```

#### 共享组件类

```css
/* 卡片 */
.card { background: var(--bg-card); border: 1px solid var(--border-default); border-radius: 8px; padding: 16px; }
.card:hover { background: var(--bg-hover); }

/* 数字 */
.num { font-family: 'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace; font-variant-numeric: tabular-nums; }
.num-up { color: var(--up); }
.num-down { color: var(--down); }

/* 标签 */
.tag { display: inline-block; padding: 2px 8px; font-size: 12px; border-radius: 4px; background: var(--bg-hover); color: var(--text-secondary); }
.tag-p0 { background: var(--down-soft); color: var(--p0); }
.tag-p1 { background: rgba(247, 147, 26, 0.12); color: var(--p1); }

/* 表格 */
table.data-grid { width: 100%; }
table.data-grid th { color: var(--text-muted); font-weight: 400; text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--border-default); }
table.data-grid td { padding: 10px 12px; border-bottom: 1px solid var(--border-default); }
table.data-grid tr:hover { background: var(--bg-hover); }
```

#### 排版

| 元素 | 字体 | 字号 | 颜色 |
|------|------|------|------|
| H1 (页面标题) | Inter 600 | 24px | --text-primary |
| H2 (区域标题) | Inter 500 | 16px | --text-primary |
| 正文 | Inter 400 | 14px | --text-primary |
| 次要 | Inter 400 | 13px | --text-secondary |
| 时间戳 | JetBrains Mono 400 | 12px | --text-muted |
| 数字（涨跌幅 / 价格） | JetBrains Mono 500 | 14-16px | --num-up / --num-down |

### 6.2 赛博朋克主题（theme-cyberpunk.css）

#### 配色 token

```css
:root[data-theme="cyberpunk"] {
  --bg-base: #0a0014;          /* 深紫近黑 */
  --bg-card: #14082c;          /* 卡片紫 */
  --bg-glow-card: rgba(0, 245, 255, 0.04);  /* 霓虹底辉 */

  --border-neon: #00f5ff;
  --border-glow: 0 0 8px rgba(0, 245, 255, 0.5);

  --text-primary: #00f5ff;     /* 霓虹 cyan */
  --text-magenta: #ff006e;     /* 强调 magenta */
  --text-yellow: #fcff00;      /* 警告 yellow */
  --text-green: #39ff14;       /* OK green */
  --text-dim: #5a3d80;         /* 次要 */

  --scan-line: rgba(0, 245, 255, 0.03);
}
```

#### 关键效果

- **辉光**：所有 `--text-primary` 文字加 `text-shadow: 0 0 4px currentColor`
- **扫描线**：`body::before { content: ''; position: fixed; inset: 0; background: repeating-linear-gradient(transparent 0, transparent 2px, var(--scan-line) 2px, var(--scan-line) 3px); pointer-events: none; z-index: 9999; }`
- **光标**：`.cursor::after { content: '█'; animation: blink 1s infinite; }`
- **进度条**：纯 CSS 用块字符 `█░` 绘
- **边框**：`border: 1px solid var(--border-neon); box-shadow: var(--border-glow);`

#### 排版

| 元素 | 字体 | 颜色 |
|------|------|------|
| 标题 | Orbitron 700 | --text-primary（带辉光） |
| 正文 / 数据 | JetBrains Mono 400 | --text-primary |
| 强调 | JetBrains Mono 700 | --text-magenta |
| 警告 | JetBrains Mono 700 | --text-yellow |

---

## 7. Mock 数据系统

### 7.1 dump_poc_fixtures.py（一次性脚本）

**路径**：`scripts/dump_poc_fixtures.py`

**功能**：连接 `data/amarket.db`（SQLite），通过现有 Repo 读出 NewsItem / Alert / MarketSnapshot / NewsAnalysis，按 spec §10.3 的 DTO schema dump 成 JSON 文件到 `poc/assets/data/`。

**用法**：
```bash
uv run python scripts/dump_poc_fixtures.py            # 全量 dump
uv run python scripts/dump_poc_fixtures.py --limit 50 # 限制新闻条数
uv run python scripts/dump_poc_fixtures.py --pretty   # 美化 JSON 缩进
```

**输出文件**：
- `dashboard.json` — 聚合：market_status + top_sectors + p0_alerts + p1_alerts + latest_news[:30] + today_reports
- `news.json` — 全量 NewsItem + NewsAnalysis JOIN（130 条）
- `news-detail-{id}.json` — 5 条 detail 样本（含完整 AI 分析 + related_news）
- `alerts.json` — 73 条 Alert
- `sectors.json` — 14 个板块的 mock 涨跌幅 + 新闻数（M3a 涨跌幅手造，M3b 接 SectorTrendService 时换真）
- `reports.json` — 1 份盘前日报 mock + 5 个 null 占位
- `params.json` — 手写 15 个示例参数（不从 DB 来，DB 还没 params 表）

**实现要点**：
- 用 SQLModel session 而不是直连 SQLite
- 序列化通过 Pydantic `model_dump_json()`
- 时间字段统一 ISO 8601 + 时区（`+08:00`）

### 7.2 JSON schema 与 spec §10.3 DTO 对齐

**所有 JSON 文件字段命名、类型与 spec §10.3 已定义 DTO 一致**，确保 M3b 接 API 时前端无感切换。

举例（与 spec §10.3 一致）：

```json
// news.json 数组中每条 = NewsCardDTO
[
  {
    "news_id": 12345,
    "title": "央行降准 0.25%",
    "summary": "...",
    "source": "央行官网",
    "url": "https://...",
    "published_at": "2026-06-19T08:30:00+08:00",
    "primary_category": "宏观政策",
    "tags": ["货币政策"],
    "sentiment": "强利多",
    "importance": 5,
    "urgency": 5,
    "confidence": 5,
    "impact_horizon": "即时",
    "action_hint": "关注",
    "related_sectors": [{"name": "券商", "weight": 0.9}],
    "related_symbols": [{"code": "601318", "name": "中国平安"}],
    "alert_level": "P0",
    "pushed": true
  }
]
```

### 7.3 sectors.json 临时 schema（M3b 会标准化）

```json
{
  "as_of": "2026-06-24T10:30:00+08:00",
  "window": "1d",
  "sectors": [
    {
      "name": "券商",
      "change_pct": 3.2,
      "news_count_24h": 18,
      "market_cap_weight": 0.08,
      "top_symbols": [{"code": "600030", "name": "中信证券"}]
    }
  ]
}
```

---

## 8. 导航与跨页面体验

### 8.1 顶部 nav（5 个 OKX 页面共享）

```
┌────────────────────────────────────────────────────────────────────┐
│ [Amarket]  首页 │ 新闻流 │ 板块 │ 日报 │ 参数        🔄 14:23:11   │
└────────────────────────────────────────────────────────────────────┘
```

- 通过 `assets/js/nav.js` 在页加载时注入到所有 5 OKX 页面顶部
- 当前页高亮（`location.pathname` 匹配）
- 点 "参数" 跳到赛博朋克 params.html（视觉风格切换为预期内）
- 右侧 "🔄 自动刷新" toggle（M3a 仅 UI / M3b 实接 setInterval polling）
- 右侧时钟（纯前端 `new Date()` 每秒 tick）

### 8.2 params.html 不复用 nav.js

赛博朋克页面 **不引入** `assets/js/nav.js`（避免被注入 OKX 风 nav），用自己的 ASCII 风 nav：

```
> back_to://amarket  | console.params v0.0.1_alpha
```

点 `back_to://amarket` 跳回 `index.html`（视觉风格回到 OKX，是预期行为）。

### 8.3 主题切换机制

每个 HTML 的 `<body>` 元素显式设 `data-theme` 属性：

- index/news/news-detail/sectors/reports：`<body data-theme="okx">`
- params：`<body data-theme="cyberpunk">`

两个 CSS 文件用 `:root[data-theme="okx"]` / `:root[data-theme="cyberpunk"]` 选择器隔离 token，不会互相污染。OKX 5 页只引 `theme-okx.css`，params 只引 `theme-cyberpunk.css`。

---

## 9. 错误处理与边界

| 场景 | 处理 |
|------|------|
| `fetch()` 失败（JSON 404 / 网络断） | 页面顶部红色 banner: "数据加载失败，请检查 dump 脚本是否跑过 / serve 是否启动" + 错误详情 |
| JSON 解析错误 | banner: "数据格式错误，请重跑 dump_poc_fixtures.py" |
| 数据为空（数组 0 条） | 各模块显示占位插画 + "暂无数据" 文案 |
| news-detail.html `?id=` 不存在 | "新闻不存在 [返回新闻流]" |
| news-detail.html 缺 `?id=` 参数 | "请从新闻流页面进入 [返回新闻流]" |
| sectors 数据空 | treemap 区域空白 + "暂无板块数据" |
| reports 某时段为 null | 该 tab 灰禁用 + "[等待 M4 调度生成]" |
| 浏览器太窄（< 1280） | 显示 banner: "桌面优先版，建议宽度 ≥ 1280px" + 不强制阻止 |
| 旧浏览器不支持 ES6 / fetch | 不兼容，README 写明要 Chrome/Edge/Firefox 最新 |

---

## 10. 测试与验收

### 10.1 测试

M3a 是纯前端 POC，**不引入单元测试**。验证靠：

1. **手动 demo checklist**（README 附）
2. **gstack 截图**（每页一张关键截图，提交到 PR 描述）

### 10.2 验收 checklist（PR review 时跑）

- [ ] `serve.bat` 启动后 `http://127.0.0.1:8090` 打开 index.html 无 console error
- [ ] 6 个页面互相跳转 nav 工作
- [ ] index.html 9 个区域全部填了数据（mock）
- [ ] news.html 筛选器至少 4 个维度生效
- [ ] news-detail.html `?id=12345` 显示完整 AI 分析
- [ ] news-detail.html `?id=99999`（不存在）显示友好错误
- [ ] sectors.html ECharts treemap 渲染 14 个板块，颜色按涨跌
- [ ] sectors.html 点格子能切换下方新闻列表
- [ ] reports.html 盘前日报 Markdown 正常渲染
- [ ] reports.html 其他 5 个时段显示"未生成"
- [ ] params.html 赛博朋克风正常，扫描线 + 辉光 + 等宽字体可见
- [ ] params.html 任何按钮点击 → toast "Coming in M5"
- [ ] 全部 6 页面在 1280×800 / 1920×1080 两种分辨率正常
- [ ] 全部 6 页面 Lighthouse Performance ≥ 80（POC 不强求 90）
- [ ] dump 脚本支持 `--limit` `--pretty` 参数
- [ ] dump 脚本对空 DB 友好（不崩，给空数组）

### 10.3 gstack 自动截图（可选）

写一个 `scripts/screenshot_poc.py`（不强制 M3a 交付）用 gstack 跑 6 个页面，把截图存到 `poc/screenshots/`，用于 PR 描述展示。M3a 可只手工截图。

---

## 11. PR 切分与里程碑

### 11.1 PR1 — 框架 + 核心 3 页 + 全量数据 dump

**Branch**: `feat/m3a-poc-frame-and-core`
**Scope**:
- `poc/` 目录创建
- `serve.bat` / `serve.sh` / `README.md`
- `assets/css/theme-okx.css` 完整
- `assets/js/shared.js` + `assets/js/nav.js`（nav.js 内置 5+1 个页面链接，但 PR1 时 sectors/reports/params 链接点击会落到 404；PR2 补齐 HTML）
- `index.html` 完整（其内 nav.js 注入的 4 个链接里：news / news-detail 可用，sectors / reports 404；params 链接渲染但点击 404）
- `news.html` 完整
- `news-detail.html` 完整
- `scripts/dump_poc_fixtures.py` 完整 **（一次生成所有 6 类 JSON：dashboard / news / news-detail-* / alerts / sectors / reports / params）**
- `assets/data/*.json` **全量** dump

**Acceptance**：3 个核心页能跑、能跳转、能筛选、能看详情；nav 上 sectors/reports/params 链接展示但点了 404（PR2 修）。

### 11.2 PR2 — 剩余 3 页 + 赛博朋克主题

**Branch**: `feat/m3a-poc-rest-and-cyberpunk`
**Scope**:
- `sectors.html` 完整（含 ECharts treemap + 联动新闻列表）
- `reports.html` 完整（含 marked.js Markdown 渲染）
- `params.html` 完整（赛博朋克风格）
- `assets/css/theme-cyberpunk.css` 完整
- nav.js 链接 404 修复（这 3 个 .html 现在存在）
- 不动 `scripts/dump_poc_fixtures.py`（PR1 已 dump 完所有 JSON）

**Acceptance**：6 页全部跑通；params 风格明显与前 5 页分明；treemap / Markdown 渲染正常。

### 11.3 M3a 完成判定

两个 PR 都合并到 main + CI 绿 + 截图 demo 完成 + PROJECT_STATE.md 更新 + session 日志 + git tag `phase1-m3a`。

---

## 12. M3b 边界（不在本 spec，但要明确预留）

M3b 干这些（出独立 spec）：

| 任务 | 改动 |
|------|------|
| 实现 `/api/dashboard/summary` | 新建 `src/amarket/api/dashboard.py` |
| 实现 `/api/dashboard/sectors` | 新建 `SectorTrendService` |
| 实现 `/api/dashboard/alerts` | 复用现有 AlertRepo |
| 实现 `/api/news/{id}` | 扩展现有 `/api/news` |
| 实现 `/api/reports` | 复用现有 ReportRepo（M4 才填数据） |
| 前端 fetch URL 切换 | 每页 1 行：`/assets/data/X.json` → `/api/X` |
| 前端 30s 自动 polling | shared.js 加 `startAutoRefresh(intervalMs)` |
| FastAPI mount poc/ 为 static | `app.mount("/poc", StaticFiles(directory="poc"), name="poc")` |
| Swagger 文档完善 | FastAPI 自动 |

---

## 13. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| CDN 被墙 / 抖动 | 中 | 大（页面打不开） | README 注明国内可换 unpkg.com → cdn.bootcss.com / npmmirror.com；脱机方案是 `assets/vendor/` 落地 |
| Tailwind CDN 编译大（首次 1-3s） | 高 | 小（仅首次） | 接受；M3b 可换 `tailwindcss-cli` 预编译 |
| ECharts 加载慢（300KB+） | 中 | 中 | M3b 评估 lightweight-charts 替代 |
| dump 脚本对空 DB 崩溃 | 低 | 中 | 写脚本时显式处理空 → 给空数组而非崩 |
| OKX 风与赛博朋克在 nav 跳转时风格突变让人困惑 | 中 | 小 | nav.js 在 params 链上加 ⚡ icon 提示；README 说明 |
| ECharts treemap 中文标签溢出 | 中 | 小 | 用 `truncate` + tooltip 全名 |
| 130 条新闻 + 筛选纯前端可能卡 | 低 | 小 | Alpine `x-show` 不删 DOM，可能慢；监测时再换 `x-if` 或虚拟滚动 |
| 用户看到赛博朋克觉得"不专业" | 低 | 小 | params 是后端管理面，与主站隔离；M5 真做时可改回主题，本 spec 只验证视觉技术可行 |

---

## 14. 未来扩展（仅记录，不在 M3a 干）

- M3b：API 联通 + 自动刷新
- M4：reports.html 接真实 6 时段日报（M4 才生成）
- M5：params.html 替换为真实参数模块（覆盖赛博朋克版）
- M6：UML 时序图 + ARCHITECTURE.md 提及 POC
- Phase 2：可能整体迁移到 Vue/React + Vite（不一定，看效果）

---

## 15. 待小组确认事项

无硬阻塞。Spec 已涵盖所有澄清问题，技术决策已由开发者（Claude）拍板，仅以下为可选反馈：

- 是否需要在 README 加 GIF demo？（M3a 完成后补，不在初版 PR）
- 是否需要 `screenshot_poc.py` gstack 脚本？（M3a 可选，不交付不影响验收）
- params.html 的赛博朋克风若小组觉得过头，M5 可改回主站风格——本 spec 仅作风格验证。

---

## 16. 附录 A：mock 数据示例片段

略，见 `poc/assets/data/*.json` dump 产物。Schema 一律以 spec v3 §10.3 DTO 为准。

## 17. 附录 B：相关链接

- Spec v3：`docs/superpowers/specs/2026-06-19-spec1-v3-merged.md`
- PROJECT_STATE：`docs/PROJECT_STATE.md`
- Tailwind 文档：https://tailwindcss.com/docs
- Alpine.js 文档：https://alpinejs.dev
- ECharts 示例：https://echarts.apache.org/examples

---

**End of Spec**
