# M3a-PR1 Implementation Plan — Framework + Core 3 Pages + Full Mock Dump

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付 M3a 第一个 PR — POC 框架 + 核心 3 页（index/news/news-detail）+ 一次性 dump 全部 7 类 mock JSON。

**Architecture:** 静态 HTML POC，每页自包含。Tailwind + Alpine.js + ECharts via CDN，0 build / 0 npm install。Python 脚本 `scripts/dump_poc_fixtures.py` 从现有 SQLite (`data/amarket.db`) 通过 Repo 读出数据，序列化为 JSON 写到 `poc/assets/data/`。前端 `fetch()` 路径设计与 spec v3 §10.3 DTO 对齐，确保 M3b 接 API 时只改 fetch URL。

**Tech Stack:** Python 3.12 (uv) + SQLModel + Pydantic（dump script）; HTML5 + Tailwind 3 CDN + Alpine.js 3 CDN + ECharts 5 CDN（前端）；pytest（dump script 单测）；`python -m http.server`（启动方式）。

**Spec Reference:** `docs/superpowers/specs/2026-06-24-m3a-poc-pages-design.md` （PR1 范围见 §11.1）

---

## File Structure

### 新增（PR1）

```
poc/                                # 项目根新目录
├── README.md                       # 启动说明 + 浏览器要求
├── serve.bat                       # Windows: python -m http.server 8090 --directory poc
├── serve.sh                        # Linux/macOS 同上
│
├── index.html                      # 首页 dashboard (OKX)
├── news.html                       # 新闻流 (OKX)
├── news-detail.html                # 新闻详情 (OKX) — 用 ?id= 参数
│
├── assets/
│   ├── css/
│   │   └── theme-okx.css           # OKX 配色 token + 共享组件类
│   ├── js/
│   │   ├── shared.js               # fetch 包装 / 格式化器 / 颜色映射
│   │   └── nav.js                  # 顶部 nav 注入（5+1 链接，PR1 时部分 404 接受）
│   └── data/                       # PR1 dump 全部 7 类 JSON
│       ├── dashboard.json
│       ├── news.json
│       ├── news-detail-{id}.json   # 5 条样本
│       ├── alerts.json
│       ├── sectors.json            # PR1 dump 占位数据（M3b 接 SectorTrendService 时换）
│       ├── reports.json            # PR1 dump 1 条 + 5 个 null 占位
│       └── params.json             # 脚本内手写 15 个示例
│
scripts/
└── dump_poc_fixtures.py            # 一次性 DB → JSON 脚本

tests/unit/
└── test_dump_poc_fixtures.py       # dump script 单测（用 tmp SQLite + 种子数据）
```

### 修改（PR1）

| 文件 | 修改 |
|------|------|
| `.gitignore` | 验证已 ignore `data/` 和 `__pycache__`；如已有则不改 |
| 无其他 src/* 修改 | M3a 不动后端 |

### 不动（PR2 才碰）

- `sectors.html` / `reports.html` / `params.html` （PR2）
- `assets/css/theme-cyberpunk.css` （PR2）
- 所有 `src/amarket/*.py` 后端代码（M3b）

---

## Task 1: 创建 poc/ 目录骨架 + serve 脚本 + README

**Files:**
- Create: `poc/README.md`
- Create: `poc/serve.bat`
- Create: `poc/serve.sh`
- Create: `poc/assets/css/.gitkeep`、`poc/assets/js/.gitkeep`、`poc/assets/data/.gitkeep`

- [ ] **Step 1: 创建目录结构**

```bash
cd C:\AI\Claude\Project_Amarket
mkdir -p poc/assets/css poc/assets/js poc/assets/data
```

Windows 用 Bash 工具（git bash）执行上面命令。

- [ ] **Step 2: 写 poc/serve.bat**

文件内容：

```batch
@echo off
REM POC 静态服务器 — Windows
cd /d %~dp0
echo Starting POC server at http://127.0.0.1:8090 ...
echo Press Ctrl+C to stop.
python -m http.server 8090
```

- [ ] **Step 3: 写 poc/serve.sh**

文件内容：

```bash
#!/usr/bin/env bash
# POC 静态服务器 — Linux / macOS
cd "$(dirname "$0")"
echo "Starting POC server at http://127.0.0.1:8090 ..."
echo "Press Ctrl+C to stop."
python3 -m http.server 8090
```

chmod 不重要，git 提交后 Windows 用户用 .bat，Unix 用户 `bash serve.sh` 也能跑。

- [ ] **Step 4: 写 poc/README.md**

文件内容：

````markdown
# POC — Amarket Dashboard 静态原型

5 个 OKX 暗色金融风页面 + 1 个赛博朋克参数空壳。Mock JSON 数据驱动，0 build，0 npm install。

## 启动

### 1. 准备数据（首次或想刷新数据时跑）

```bash
cd ..
uv run python scripts/dump_poc_fixtures.py
```

把 `data/amarket.db` 的真实数据 dump 到 `poc/assets/data/*.json`。

### 2. 启动 HTTP 服务

**Windows**：双击 `serve.bat` 或命令行
```cmd
serve.bat
```

**Linux / macOS**：
```bash
bash serve.sh
```

服务起在 `http://127.0.0.1:8090`。

### 3. 浏览器打开

打开 http://127.0.0.1:8090/index.html

## 页面清单（PR1 范围）

- `index.html` — 首页 dashboard（9 个区域）
- `news.html` — 新闻流（带筛选）
- `news-detail.html?id={news_id}` — 单条新闻详情

PR2 会补上 `sectors.html` / `reports.html` / `params.html`。

## 浏览器要求

Chrome / Edge / Firefox 最新版。**桌面优先**（建议宽度 ≥ 1280px）。

## 技术栈（全部 CDN，全部 MIT/Apache 开源）

- Tailwind CSS 3
- Alpine.js 3
- ECharts 5
- Marked.js（reports 页用）
- Google Fonts: Inter / JetBrains Mono / Orbitron

## 故障排查

- **页面空白 / 红 banner "数据加载失败"** → 跑一次 dump 脚本（步骤 1）
- **CDN 加载慢 / 失败** → 国内可换 `unpkg.com` → `npmmirror.com`；脱机方案下载到 `assets/vendor/`
- **端口 8090 被占用** → 改 serve 脚本里端口号
````

- [ ] **Step 5: 提交**

```bash
git add poc/README.md poc/serve.bat poc/serve.sh poc/assets/css/.gitkeep poc/assets/js/.gitkeep poc/assets/data/.gitkeep
git commit -m "feat(m3a): poc directory skeleton + serve scripts + README"
```

---

## Task 2: 写 theme-okx.css（OKX 暗色配色 token + 共享组件类）

**Files:**
- Create: `poc/assets/css/theme-okx.css`

- [ ] **Step 1: 写 CSS 文件全部内容**

完整内容（直接写入 `poc/assets/css/theme-okx.css`）：

```css
/* OKX 暗色金融风 — M3a POC theme */

:root[data-theme="okx"] {
  /* 背景层 */
  --bg-base: #0c0d0f;
  --bg-card: #16181c;
  --bg-hover: #1f2227;
  --bg-input: #1a1c20;

  /* 边框 */
  --border-default: #2a2d33;
  --border-focus: #4a4d55;

  /* 文字 */
  --text-primary: #e8e9ea;
  --text-secondary: #9a9ba0;
  --text-muted: #5f6063;

  /* 品牌强调 */
  --accent: #00b4d8;
  --accent-hover: #0091ad;

  /* 涨跌 */
  --up: #14b143;
  --up-soft: rgba(20, 177, 67, 0.12);
  --down: #ef454a;
  --down-soft: rgba(239, 69, 74, 0.12);

  /* 告警等级 */
  --p0: #ef454a;
  --p1: #f7931a;
  --p2: #00b4d8;
  --p3: #14b143;

  /* 情绪 */
  --sentiment-strong-bull: #14b143;
  --sentiment-bull: #5fb985;
  --sentiment-neutral: #9a9ba0;
  --sentiment-bear: #f08585;
  --sentiment-strong-bear: #ef454a;
}

* { box-sizing: border-box; }

html, body {
  margin: 0;
  padding: 0;
  background: var(--bg-base);
  color: var(--text-primary);
  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  min-height: 100vh;
}

a { color: var(--accent); text-decoration: none; }
a:hover { color: var(--accent-hover); }

/* === 顶部 nav === */

.topbar {
  display: flex;
  align-items: center;
  height: 56px;
  padding: 0 24px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-default);
  position: sticky;
  top: 0;
  z-index: 100;
}
.topbar .logo {
  font-weight: 600;
  font-size: 16px;
  margin-right: 32px;
  color: var(--text-primary);
}
.topbar .nav-items {
  display: flex;
  gap: 4px;
  flex: 1;
}
.topbar .nav-link {
  padding: 8px 16px;
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 14px;
}
.topbar .nav-link:hover { background: var(--bg-hover); color: var(--text-primary); }
.topbar .nav-link.active { background: var(--bg-hover); color: var(--accent); }
.topbar .nav-link.cyber { color: var(--text-muted); font-family: 'JetBrains Mono', monospace; }
.topbar .nav-link.cyber::before { content: '⚡ '; }
.topbar .topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
  color: var(--text-muted);
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
}

/* === 通用卡片 === */

.card {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  padding: 16px;
}
.card-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 12px;
}

/* === 数字 / 涨跌色 === */

.num {
  font-family: 'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace;
  font-variant-numeric: tabular-nums;
}
.num-up { color: var(--up); }
.num-down { color: var(--down); }
.num-neutral { color: var(--text-secondary); }

/* === 标签 === */

.tag {
  display: inline-block;
  padding: 2px 8px;
  font-size: 11px;
  border-radius: 4px;
  background: var(--bg-hover);
  color: var(--text-secondary);
  font-weight: 500;
  margin-right: 4px;
}
.tag-p0 { background: var(--down-soft); color: var(--p0); }
.tag-p1 { background: rgba(247, 147, 26, 0.12); color: var(--p1); }
.tag-p2 { background: rgba(0, 180, 216, 0.12); color: var(--p2); }
.tag-p3 { background: var(--up-soft); color: var(--p3); }

.sent-strong-bull { color: var(--sentiment-strong-bull); }
.sent-bull { color: var(--sentiment-bull); }
.sent-neutral { color: var(--sentiment-neutral); }
.sent-bear { color: var(--sentiment-bear); }
.sent-strong-bear { color: var(--sentiment-strong-bear); }

/* === 重要性 ★ === */

.stars { color: var(--p1); letter-spacing: 1px; }
.stars-empty { color: var(--text-muted); }

/* === 表格 === */

table.data-grid { width: 100%; border-collapse: collapse; }
table.data-grid th {
  color: var(--text-muted);
  font-weight: 400;
  text-align: left;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-default);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
table.data-grid td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-default);
  font-size: 14px;
}
table.data-grid tr:hover td { background: var(--bg-hover); }

/* === 输入控件 === */

input[type="text"], input[type="search"], select {
  background: var(--bg-input);
  border: 1px solid var(--border-default);
  color: var(--text-primary);
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 13px;
  font-family: inherit;
  outline: none;
}
input:focus, select:focus { border-color: var(--accent); }

button.btn {
  background: var(--bg-hover);
  border: 1px solid var(--border-default);
  color: var(--text-primary);
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  font-family: inherit;
}
button.btn:hover { background: var(--border-default); }
button.btn.btn-primary { background: var(--accent); color: var(--bg-base); border-color: var(--accent); }
button.btn.btn-primary:hover { background: var(--accent-hover); border-color: var(--accent-hover); }

/* === Banner / Toast === */

.banner {
  padding: 12px 20px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 13px;
}
.banner-error { background: var(--down-soft); color: var(--down); border-left: 3px solid var(--down); }
.banner-warn { background: rgba(247, 147, 26, 0.12); color: var(--p1); border-left: 3px solid var(--p1); }
.banner-info { background: rgba(0, 180, 216, 0.12); color: var(--accent); border-left: 3px solid var(--accent); }

/* === 滚动条（暗色风）=== */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: var(--bg-hover); border-radius: 5px; }
::-webkit-scrollbar-thumb:hover { background: var(--border-default); }

/* === 工具类 === */

.text-secondary { color: var(--text-secondary); }
.text-muted { color: var(--text-muted); }
.text-up { color: var(--up); }
.text-down { color: var(--down); }
.bg-card { background: var(--bg-card); }
.flex { display: flex; }
.flex-col { display: flex; flex-direction: column; }
.gap-4 { gap: 16px; }
.gap-2 { gap: 8px; }
.gap-1 { gap: 4px; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.flex-1 { flex: 1; }
.w-full { width: 100%; }
.mt-2 { margin-top: 8px; }
.mt-4 { margin-top: 16px; }
.mb-2 { margin-bottom: 8px; }
.mb-4 { margin-bottom: 16px; }
.p-4 { padding: 16px; }
.p-6 { padding: 24px; }
.hidden { display: none; }

/* 主区域 layout */

.page-shell {
  max-width: 1920px;
  margin: 0 auto;
  padding: 24px;
}

.grid-cols-12 { display: grid; grid-template-columns: repeat(12, 1fr); gap: 16px; }
.col-span-6 { grid-column: span 6; }
.col-span-4 { grid-column: span 4; }
.col-span-8 { grid-column: span 8; }
.col-span-12 { grid-column: span 12; }

/* 长列表滚动区 */
.scroll-area {
  max-height: 700px;
  overflow-y: auto;
  border: 1px solid var(--border-default);
  border-radius: 8px;
  background: var(--bg-card);
}
```

- [ ] **Step 2: 提交**

```bash
git add poc/assets/css/theme-okx.css
git commit -m "feat(m3a): OKX dark theme CSS (tokens + shared components)"
```

---

## Task 3: 写 shared.js（fetch + 格式化器）

**Files:**
- Create: `poc/assets/js/shared.js`

- [ ] **Step 1: 写 shared.js 全部内容**

完整内容：

```javascript
/* shared.js — POC 通用工具函数，所有页面引入 */

(function (global) {
  'use strict';

  /**
   * fetch JSON 数据，统一错误处理。
   * 返回 Promise<data> 或 throw Error。
   *
   * M3b 接 API 时，调用方把 url 从 '/assets/data/X.json' 换成 '/api/X' 即可。
   */
  async function fetchJSON(url) {
    const res = await fetch(url, { headers: { Accept: 'application/json' } });
    if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText} loading ${url}`);
    return res.json();
  }

  /** 格式化数字：1234.5 → '1,234.50' */
  function formatNumber(n, digits = 2) {
    if (n == null || isNaN(n)) return '-';
    return Number(n).toLocaleString('zh-CN', {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
  }

  /** 格式化涨跌幅：3.2 → '+3.20%'（带正负号 + 颜色 class） */
  function formatChangePct(pct) {
    if (pct == null || isNaN(pct)) return { text: '-', cls: 'num-neutral' };
    const sign = pct >= 0 ? '+' : '';
    return {
      text: `${sign}${pct.toFixed(2)}%`,
      cls: pct > 0 ? 'num-up' : pct < 0 ? 'num-down' : 'num-neutral',
    };
  }

  /** ISO 时间 → '2026-06-24 13:42:15' */
  function formatDateTime(iso) {
    if (!iso) return '-';
    const d = new Date(iso);
    if (isNaN(d.getTime())) return iso;
    const pad = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ` +
           `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  }

  /** ISO 时间 → '13:42' */
  function formatTime(iso) {
    if (!iso) return '-';
    const d = new Date(iso);
    if (isNaN(d.getTime())) return '-';
    const pad = (n) => String(n).padStart(2, '0');
    return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }

  /** ISO 时间 → '14分钟前' / '2小时前' / '昨天 13:42' */
  function timeAgo(iso) {
    if (!iso) return '-';
    const d = new Date(iso);
    if (isNaN(d.getTime())) return '-';
    const seconds = Math.floor((Date.now() - d.getTime()) / 1000);
    if (seconds < 60) return `${seconds}秒前`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}分钟前`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}小时前`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}天前`;
    return formatDateTime(iso);
  }

  /** 重要性分数 → ★ 字符串 */
  function stars(score) {
    if (!score) return '';
    const n = Math.max(0, Math.min(5, Math.round(score)));
    return '★'.repeat(n) + '☆'.repeat(5 - n);
  }

  /** 情绪 → CSS class */
  function sentimentClass(sentiment) {
    const map = {
      '强利多': 'sent-strong-bull',
      '利多': 'sent-bull',
      '中性': 'sent-neutral',
      '利空': 'sent-bear',
      '强利空': 'sent-strong-bear',
    };
    return map[sentiment] || 'sent-neutral';
  }

  /** alert level → tag class */
  function alertTagClass(level) {
    return level ? `tag tag-${level.toLowerCase()}` : 'tag';
  }

  /** 显示页面顶部错误 banner */
  function showBanner(msg, type = 'error') {
    let el = document.getElementById('global-banner');
    if (!el) {
      el = document.createElement('div');
      el.id = 'global-banner';
      el.className = `banner banner-${type}`;
      const main = document.querySelector('.page-shell') || document.body;
      main.insertBefore(el, main.firstChild);
    } else {
      el.className = `banner banner-${type}`;
    }
    el.textContent = msg;
  }

  /** URL ?id=X 取 query 参数 */
  function getQueryParam(name) {
    return new URLSearchParams(location.search).get(name);
  }

  /** 时钟（每秒 tick），返回停止函数 */
  function startClock(targetEl) {
    function update() {
      if (!targetEl) return;
      const d = new Date();
      const pad = (n) => String(n).padStart(2, '0');
      targetEl.textContent = `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
    }
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }

  /** 桌面宽度检测，<1280 显示警告 banner（不强制阻止） */
  function checkViewport() {
    if (window.innerWidth < 1280) {
      showBanner('POC 为桌面优先版，建议宽度 ≥ 1280px', 'warn');
    }
  }

  global.Amarket = {
    fetchJSON, formatNumber, formatChangePct, formatDateTime, formatTime,
    timeAgo, stars, sentimentClass, alertTagClass, showBanner,
    getQueryParam, startClock, checkViewport,
  };
})(window);
```

- [ ] **Step 2: 提交（暂不 commit，先合到 Task 4 nav.js 一起提交）**

不动 git，跟 Task 4 一起 commit。

---

## Task 4: 写 nav.js（顶部 nav 注入）

**Files:**
- Create: `poc/assets/js/nav.js`

- [ ] **Step 1: 写 nav.js 全部内容**

```javascript
/* nav.js — 顶部 nav 自动注入。OKX 5 页用，params.html 不引用此文件。 */

(function () {
  'use strict';

  const NAV_ITEMS = [
    { href: 'index.html', label: '首页', match: ['index.html', '/'] },
    { href: 'news.html', label: '新闻流', match: ['news.html', 'news-detail.html'] },
    { href: 'sectors.html', label: '板块', match: ['sectors.html'] },
    { href: 'reports.html', label: '日报', match: ['reports.html'] },
    { href: 'params.html', label: '参数', match: ['params.html'], cyber: true },
  ];

  function isActive(item) {
    const path = location.pathname.split('/').pop() || 'index.html';
    return item.match.some((m) => path === m || (m === '/' && path === ''));
  }

  function render() {
    const mount = document.getElementById('topbar-mount');
    if (!mount) return;
    const itemsHtml = NAV_ITEMS.map((item) => {
      const cls = ['nav-link'];
      if (isActive(item)) cls.push('active');
      if (item.cyber) cls.push('cyber');
      return `<a href="${item.href}" class="${cls.join(' ')}">${item.label}</a>`;
    }).join('');
    mount.innerHTML = `
      <div class="topbar">
        <div class="logo">Amarket</div>
        <div class="nav-items">${itemsHtml}</div>
        <div class="topbar-right">
          <label class="flex items-center gap-1" style="cursor:pointer">
            <input type="checkbox" id="auto-refresh-toggle" disabled title="M3b 才接 polling">
            <span>🔄 自动刷新（M3b）</span>
          </label>
          <span id="topbar-clock">--:--:--</span>
        </div>
      </div>
    `;
    const clockEl = document.getElementById('topbar-clock');
    if (clockEl && window.Amarket) window.Amarket.startClock(clockEl);
  }

  document.addEventListener('DOMContentLoaded', render);
})();
```

- [ ] **Step 2: 提交 shared.js + nav.js**

```bash
git add poc/assets/js/shared.js poc/assets/js/nav.js
git commit -m "feat(m3a): shared.js + nav.js (fetch wrapper + top nav injection)"
```

---

## Task 5: dump_poc_fixtures.py 骨架 + CLI

**Files:**
- Create: `scripts/dump_poc_fixtures.py`
- Create: `tests/unit/test_dump_poc_fixtures.py`

- [ ] **Step 1: 写最小 dump 脚本骨架 + CLI**

完整内容（`scripts/dump_poc_fixtures.py`）：

```python
"""一次性 dump 脚本：从 data/amarket.db 读出数据，输出到 poc/assets/data/*.json。

用法：
    uv run python scripts/dump_poc_fixtures.py
    uv run python scripts/dump_poc_fixtures.py --limit 50
    uv run python scripts/dump_poc_fixtures.py --pretty
    uv run python scripts/dump_poc_fixtures.py --db custom.db --out custom/data

M3b 接入 API 后此脚本仅用于本地 debug，不再是前端数据源。
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlmodel import Session, create_engine

from amarket.adapters.market_sources.base import MAJOR_A_SHARE_INDEXES
from amarket.domain.models import Alert, NewsAnalysis, NewsItem, NewsSource
from amarket.repositories.alert_repo import AlertRepo
from amarket.repositories.market_snapshot_repo import MarketSnapshotRepo
from amarket.repositories.news_analysis_repo import NewsAnalysisRepo
from amarket.repositories.news_repo import NewsRepo

DEFAULT_DB = "sqlite:///data/amarket.db"
DEFAULT_OUT = Path("poc/assets/data")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Dump amarket DB → POC mock JSON files.")
    p.add_argument("--db", default=DEFAULT_DB, help="SQLAlchemy URL (default: %(default)s)")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output dir (default: %(default)s)")
    p.add_argument("--limit", type=int, default=300, help="Max news items to dump")
    p.add_argument("--detail-samples", type=int, default=5, help="How many news-detail-*.json to dump")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON with indent=2")
    return p.parse_args()


def write_json(path: Path, data: Any, *, pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    indent = 2 if pretty else None
    text = json.dumps(data, ensure_ascii=False, indent=indent, default=_json_default)
    path.write_text(text, encoding="utf-8")
    print(f"  ✓ wrote {path} ({len(text):,} bytes)")


def _json_default(o: Any) -> Any:
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(f"unserializable: {type(o).__name__}")


def main() -> int:
    args = parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    print(f"Connecting to {args.db} ...")
    engine = create_engine(args.db)

    with Session(engine) as session:
        print("\n=== Dumping dashboard.json ===")
        write_json(out / "dashboard.json", dump_dashboard(session, news_limit=30), pretty=args.pretty)

        print("\n=== Dumping news.json ===")
        write_json(out / "news.json", dump_news(session, limit=args.limit), pretty=args.pretty)

        print(f"\n=== Dumping news-detail-*.json (top {args.detail_samples}) ===")
        for nid in dump_news_details(session, out, limit=args.detail_samples, pretty=args.pretty):
            print(f"  ✓ news-detail-{nid}.json")

        print("\n=== Dumping alerts.json ===")
        write_json(out / "alerts.json", dump_alerts(session), pretty=args.pretty)

        print("\n=== Dumping sectors.json (M3a placeholder, M3b 接 SectorTrendService) ===")
        write_json(out / "sectors.json", dump_sectors_placeholder(), pretty=args.pretty)

        print("\n=== Dumping reports.json (M3a placeholder, M4 真填) ===")
        write_json(out / "reports.json", dump_reports_placeholder(), pretty=args.pretty)

        print("\n=== Dumping params.json (handwritten, M5 真填) ===")
        write_json(out / "params.json", dump_params_handwritten(), pretty=args.pretty)

    print("\n✅ All done.")
    return 0


# ---- 各 dump 函数（占位实现，下个 task 填充）---- #

def dump_dashboard(session: Session, *, news_limit: int) -> dict[str, Any]:
    return {}

def dump_news(session: Session, *, limit: int) -> list[dict[str, Any]]:
    return []

def dump_news_details(session: Session, out: Path, *, limit: int, pretty: bool) -> list[int]:
    return []

def dump_alerts(session: Session) -> list[dict[str, Any]]:
    return []

def dump_sectors_placeholder() -> dict[str, Any]:
    return {}

def dump_reports_placeholder() -> dict[str, Any]:
    return {}

def dump_params_handwritten() -> list[dict[str, Any]]:
    return []


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: 写测试骨架 — 单测 tmp DB 跑通空 dump**

完整内容（`tests/unit/test_dump_poc_fixtures.py`）：

```python
"""dump_poc_fixtures 单元测试 — 用 tmp SQLite + 种子数据。"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine

# 把 scripts/ 加入 sys.path 以便 import dump_poc_fixtures
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import dump_poc_fixtures as dpf  # noqa: E402

from amarket.domain.enums import (  # noqa: E402
    ActionHint,
    AlertLevel,
    ImpactHorizon,
    NewsCategory,
    Sentiment,
    SourcePriority,
)
from amarket.domain.models import (  # noqa: E402
    Alert,
    MarketSnapshot,
    NewsAnalysis,
    NewsItem,
    NewsSource,
)


@pytest.fixture
def tmp_engine(tmp_path: Path):
    """tmp SQLite + 全表创建。"""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def seeded_session(tmp_engine):
    """种入：1 source + 3 news + 2 analysis + 1 alert + 2 market_snapshot。"""
    with Session(tmp_engine) as s:
        src = NewsSource(code="ths", name="同花顺", priority=SourcePriority.HIGH, enabled=True)
        s.add(src)
        s.commit()
        s.refresh(src)

        n1 = NewsItem(
            source_id=src.id,
            source_msg_id="msg-1",
            title="央行降准 0.25%",
            summary="央行宣布降准...",
            url="https://example.com/n1",
            published_at=datetime(2026, 6, 24, 8, 30, tzinfo=UTC),
        )
        n2 = NewsItem(
            source_id=src.id,
            source_msg_id="msg-2",
            title="某公司发布业绩预告",
            summary="预增 50%",
            url="https://example.com/n2",
            published_at=datetime(2026, 6, 24, 9, 0, tzinfo=UTC),
        )
        n3 = NewsItem(
            source_id=src.id,
            source_msg_id="msg-3",
            title="盘后新闻 3",
            summary=None,
            url=None,
            published_at=datetime(2026, 6, 24, 15, 30, tzinfo=UTC),
        )
        s.add_all([n1, n2, n3])
        s.commit()
        for n in (n1, n2, n3):
            s.refresh(n)

        a1 = NewsAnalysis(
            news_id=n1.id,
            primary_category=NewsCategory.MACRO,
            tags=["货币政策"],
            related_sectors=[{"name": "券商", "weight": 0.9}],
            related_symbols=[{"code": "601318", "name": "中国平安"}],
            sentiment=Sentiment.STRONG_BULL,
            importance_score=5,
            urgency_score=5,
            confidence_score=5,
            impact_horizon=ImpactHorizon.IMMEDIATE,
            action_hint=ActionHint.WATCH,
            ai_reasoning="降准利好金融板块",
            processed_by="agent:news-classifier-realtime",
        )
        a2 = NewsAnalysis(
            news_id=n2.id,
            primary_category=NewsCategory.COMPANY,
            tags=["业绩预告"],
            sentiment=Sentiment.BULL,
            importance_score=3,
            urgency_score=3,
            confidence_score=4,
            processed_by="rule",
        )
        s.add_all([a1, a2])
        s.commit()
        s.refresh(a1)

        alert = Alert(
            news_id=n1.id,
            level=AlertLevel.P0,
            trigger_reason="importance=5 + sentiment=strong_bull",
            analysis_id=a1.id,
            status="pushed",
            created_at=datetime(2026, 6, 24, 8, 31, tzinfo=UTC),
            pushed_at=datetime(2026, 6, 24, 8, 31, 5, tzinfo=UTC),
        )
        s.add(alert)

        ms1 = MarketSnapshot(
            ts=datetime(2026, 6, 24, 10, 0, tzinfo=UTC),
            asset_kind="index",
            code="sh000001",
            name="上证指数",
            price=3200.5,
            change_pct=0.5,
            change_abs=15.9,
            extra_json={"source": "akshare"},
        )
        ms2 = MarketSnapshot(
            ts=datetime(2026, 6, 24, 10, 0, tzinfo=UTC),
            asset_kind="index",
            code="sz399001",
            name="深证成指",
            price=10500.0,
            change_pct=-0.3,
            change_abs=-31.5,
            extra_json={"source": "akshare"},
        )
        s.add_all([ms1, ms2])
        s.commit()

        yield s, {"src_id": src.id, "news_ids": [n1.id, n2.id, n3.id], "alert_id": alert.id}


# ===== Task 5 测试 — 骨架可调用 =====

def test_main_creates_empty_jsons(tmp_path, monkeypatch, tmp_engine):
    """空 DB 也能跑完不崩，输出 7 类 JSON 文件。"""
    out = tmp_path / "data"
    monkeypatch.setattr(
        "sys.argv",
        ["dump_poc_fixtures.py", "--db", str(tmp_engine.url), "--out", str(out)],
    )
    rc = dpf.main()
    assert rc == 0
    for name in ("dashboard", "news", "alerts", "sectors", "reports", "params"):
        assert (out / f"{name}.json").exists(), f"{name}.json missing"
```

- [ ] **Step 3: 跑测试，验证骨架可调用**

```bash
uv run pytest tests/unit/test_dump_poc_fixtures.py -v
```

Expected: 1 test PASSED（all dump_* 返回空 / 空 list / 空 dict 都 OK）。

- [ ] **Step 4: 提交**

```bash
git add scripts/dump_poc_fixtures.py tests/unit/test_dump_poc_fixtures.py
git commit -m "feat(m3a): dump_poc_fixtures.py skeleton + CLI + smoke test"
```

---

## Task 6: 实现 dump_dashboard / dump_news / dump_news_details

**Files:**
- Modify: `scripts/dump_poc_fixtures.py`
- Modify: `tests/unit/test_dump_poc_fixtures.py`

- [ ] **Step 1: 写测试 — 期望 dump_news 返回 NewsCardDTO 增强字段**

往 `tests/unit/test_dump_poc_fixtures.py` 末尾追加：

```python
# ===== Task 6 测试 =====

def test_dump_news_returns_enriched_dto(seeded_session):
    session, ids = seeded_session
    result = dpf.dump_news(session, limit=10)
    assert len(result) == 3, "should dump all 3 seeded news"
    # 按 published_at 倒序：n3 最新
    titles = [r["title"] for r in result]
    assert titles[0] == "盘后新闻 3"
    # 第一个 news (n1) 是降准，有完整 AI 分析
    rec = next(r for r in result if r["title"] == "央行降准 0.25%")
    assert rec["primary_category"] == "宏观"
    assert rec["sentiment"] == "强利多"
    assert rec["importance"] == 5
    assert rec["urgency"] == 5
    assert rec["confidence"] == 5
    assert rec["impact_horizon"] == "即时"
    assert rec["action_hint"] == "关注"
    assert rec["alert_level"] == "P0"
    assert rec["pushed"] is True
    assert rec["related_sectors"] == [{"name": "券商", "weight": 0.9}]
    assert rec["related_symbols"] == [{"code": "601318", "name": "中国平安"}]
    assert rec["source"] == "同花顺"


def test_dump_news_handles_no_analysis(seeded_session):
    """没分析的 news（n3）应该字段为 None / [] 但不崩。"""
    session, _ = seeded_session
    result = dpf.dump_news(session, limit=10)
    rec = next(r for r in result if r["title"] == "盘后新闻 3")
    assert rec["primary_category"] is None
    assert rec["sentiment"] is None
    assert rec["importance"] is None
    assert rec["alert_level"] is None
    assert rec["related_sectors"] == []


def test_dump_dashboard_aggregates(seeded_session):
    session, _ = seeded_session
    result = dpf.dump_dashboard(session, news_limit=10)
    assert "market_status" in result
    assert "latest_news" in result
    assert "p0_alerts" in result
    assert "p1_alerts" in result
    assert "today_conclusion" in result
    assert "today_reports" in result
    # market_status.indexes 至少包含 sh000001 / sz399001
    codes = [idx["code"] for idx in result["market_status"]["indexes"]]
    assert "sh000001" in codes
    assert "sz399001" in codes
    # P0 alerts 至少有种子的 1 条
    assert len(result["p0_alerts"]) >= 1


def test_dump_news_details_writes_per_id_files(seeded_session, tmp_path):
    session, ids = seeded_session
    ids_written = dpf.dump_news_details(session, tmp_path, limit=2, pretty=False)
    assert len(ids_written) == 2
    for nid in ids_written:
        f = tmp_path / f"news-detail-{nid}.json"
        assert f.exists()
        data = json.loads(f.read_text(encoding="utf-8"))
        assert data["news_id"] == nid
        assert "related_news" in data  # 详情比列表多 related_news
```

- [ ] **Step 2: 跑测试验证 FAIL**

```bash
uv run pytest tests/unit/test_dump_poc_fixtures.py -v -k "test_dump_news_returns_enriched_dto or test_dump_news_handles_no_analysis or test_dump_dashboard_aggregates or test_dump_news_details_writes_per_id_files"
```

Expected: 4 FAILED（dump_* 全返回空）。

- [ ] **Step 3: 实现 dump_news + dump_news_details + dump_dashboard**

把 `scripts/dump_poc_fixtures.py` 中的三个 placeholder 函数替换为真实实现。完整替换段：

```python
def _news_to_card(
    session: Session,
    news: NewsItem,
    source: NewsSource,
    analysis: NewsAnalysis | None,
    alert: Alert | None,
) -> dict[str, Any]:
    """NewsItem + JOIN → 富 DTO（超过 NewsCardDTO，含 spec §10.3 全部字段）。"""
    return {
        "news_id": news.id,
        "title": news.title,
        "summary": news.summary,
        "source": source.name,
        "source_code": source.code,
        "source_priority": source.priority.value,
        "url": news.url,
        "published_at": news.published_at,
        "fetched_at": news.fetched_at,
        "primary_category": analysis.primary_category.value if analysis else None,
        "tags": analysis.tags if analysis else [],
        "sentiment": analysis.sentiment.value if analysis else None,
        "importance": analysis.importance_score if analysis else None,
        "urgency": analysis.urgency_score if analysis else None,
        "confidence": analysis.confidence_score if analysis else None,
        "impact_horizon": analysis.impact_horizon.value if analysis else None,
        "action_hint": analysis.action_hint.value if analysis else None,
        "related_sectors": analysis.related_sectors if analysis else [],
        "related_symbols": analysis.related_symbols if analysis else [],
        "alert_level": alert.level.value if alert else None,
        "pushed": (alert.status == "pushed") if alert else False,
        "processed_by": analysis.processed_by if analysis else None,
    }


def _highest_alert(alerts: list[Alert]) -> Alert | None:
    if not alerts:
        return None
    priority = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    return sorted(alerts, key=lambda a: priority.get(a.level.value, 99))[0]


def dump_news(session: Session, *, limit: int) -> list[dict[str, Any]]:
    repo = NewsRepo(session)
    analysis_repo = NewsAnalysisRepo(session)
    alert_repo = AlertRepo(session)

    rows = repo.list_recent(limit=limit)
    result: list[dict[str, Any]] = []
    for news, src in rows:
        assert news.id is not None
        analyses = analysis_repo.list_for_news(news_id=news.id)
        # 优先取 agent:*/sdk:* 分析，无则 rule
        analyses_sorted = sorted(
            analyses,
            key=lambda a: (0 if a.processed_by.startswith(("agent:", "sdk:")) else 1, -(a.id or 0)),
        )
        ana = analyses_sorted[0] if analyses_sorted else None
        alerts = alert_repo.list_for_news(news_id=news.id, limit=10)
        alt = _highest_alert(alerts)
        result.append(_news_to_card(session, news, src, ana, alt))
    return result


def dump_news_details(session: Session, out: Path, *, limit: int, pretty: bool) -> list[int]:
    """Dump top N news 的详情（含 related_news 同事件其他 news）到独立文件。"""
    repo = NewsRepo(session)
    analysis_repo = NewsAnalysisRepo(session)
    alert_repo = AlertRepo(session)

    rows = repo.list_recent(limit=limit)
    written: list[int] = []
    for news, src in rows:
        assert news.id is not None
        analyses = analysis_repo.list_for_news(news_id=news.id)
        analyses_sorted = sorted(
            analyses,
            key=lambda a: (0 if a.processed_by.startswith(("agent:", "sdk:")) else 1, -(a.id or 0)),
        )
        ana = analyses_sorted[0] if analyses_sorted else None
        alerts = alert_repo.list_for_news(news_id=news.id, limit=10)
        alt = _highest_alert(alerts)
        card = _news_to_card(session, news, src, ana, alt)

        related: list[dict[str, Any]] = []
        if news.event_id is not None:
            from sqlmodel import select
            stmt = (
                select(NewsItem, NewsSource)
                .join(NewsSource, NewsItem.source_id == NewsSource.id)  # type: ignore[arg-type]
                .where(NewsItem.event_id == news.event_id)
                .where(NewsItem.id != news.id)
                .limit(10)
            )
            for r_news, r_src in session.exec(stmt):
                related.append({
                    "news_id": r_news.id,
                    "title": r_news.title,
                    "source": r_src.name,
                    "published_at": r_news.published_at,
                    "url": r_news.url,
                })
        card["related_news"] = related
        card["ai_reasoning"] = ana.ai_reasoning if ana else None
        card["risk_notes"] = ana.risk_notes if ana else None
        card["content"] = news.content  # 详情多带正文

        write_json(out / f"news-detail-{news.id}.json", card, pretty=pretty)
        written.append(news.id)
    return written


def dump_dashboard(session: Session, *, news_limit: int) -> dict[str, Any]:
    market_repo = MarketSnapshotRepo(session)
    alert_repo = AlertRepo(session)

    # market_status —— 拿 11 个 A 股指数最新
    latest = market_repo.latest_for_codes(list(MAJOR_A_SHARE_INDEXES.keys()))
    indexes = []
    for code, name in MAJOR_A_SHARE_INDEXES.items():
        snap = latest.get(code)
        if snap is None:
            continue
        extra = snap.extra_json if isinstance(snap.extra_json, dict) else {}
        indexes.append({
            "code": code,
            "name": snap.name or name,
            "price": snap.price,
            "change_pct": snap.change_pct,
            "change_abs": snap.change_abs,
            "prev_close": extra.get("prev_close"),
            "volume": snap.volume,
            "turnover": snap.turnover,
            "source": str(extra.get("source", "akshare")),
            "fetched_at": snap.ts,
        })

    # latest_news
    latest_news = dump_news(session, limit=news_limit)

    # P0 / P1 alerts
    p0 = alert_repo.list_recent(levels=None, status=None, limit=100)
    p0_list = [_alert_to_dict(session, a) for a in p0 if a.level.value == "P0"][:10]
    p1_list = [_alert_to_dict(session, a) for a in p0 if a.level.value == "P1"][:10]

    return {
        "as_of": datetime.now(UTC),
        "market_status": {"indexes": indexes, "fx": [], "commodities": [], "refreshed_at": datetime.now(UTC)},
        "today_conclusion": "（M3a 占位 — M4 接盘前日报）",
        "latest_news": latest_news,
        "p0_alerts": p0_list,
        "p1_alerts": p1_list,
        "top_sectors": [],  # M3b 接 SectorTrendService
        "top_movers": [],   # M3b 接
        "today_reports": {  # M4 真填
            "premarket": None,
            "morning": None,
            "noon": None,
            "afternoon": None,
            "close": None,
            "evening": None,
        },
    }


def _alert_to_dict(session: Session, alert: Alert) -> dict[str, Any]:
    title = source_name = category = None
    if alert.news_id is not None:
        news = session.get(NewsItem, alert.news_id)
        if news is not None:
            title = news.title
            src = session.get(NewsSource, news.source_id)
            if src is not None:
                source_name = src.name
    if alert.analysis_id is not None:
        ana = session.get(NewsAnalysis, alert.analysis_id)
        if ana is not None:
            category = ana.primary_category.value
    return {
        "alert_id": alert.id,
        "news_id": alert.news_id,
        "level": alert.level.value,
        "trigger_reason": alert.trigger_reason,
        "analysis_id": alert.analysis_id,
        "status": alert.status,
        "created_at": alert.created_at,
        "pushed_at": alert.pushed_at,
        "news_title": title,
        "news_source": source_name,
        "primary_category": category,
    }
```

- [ ] **Step 4: 跑测试验证 4 个新测试 PASS**

```bash
uv run pytest tests/unit/test_dump_poc_fixtures.py -v
```

Expected: 5/5 PASS（含 Task 5 的 empty test）。

- [ ] **Step 5: 提交**

```bash
git add scripts/dump_poc_fixtures.py tests/unit/test_dump_poc_fixtures.py
git commit -m "feat(m3a): dump_news + dump_news_details + dump_dashboard (TDD)"
```

---

## Task 7: 实现 dump_alerts / dump_sectors / dump_reports / dump_params

**Files:**
- Modify: `scripts/dump_poc_fixtures.py`
- Modify: `tests/unit/test_dump_poc_fixtures.py`

- [ ] **Step 1: 写测试**

往 `tests/unit/test_dump_poc_fixtures.py` 追加：

```python
def test_dump_alerts_returns_list_with_news_join(seeded_session):
    session, _ = seeded_session
    result = dpf.dump_alerts(session)
    assert isinstance(result, list)
    assert len(result) >= 1
    rec = result[0]
    assert rec["level"] in ("P0", "P1", "P2", "P3")
    assert rec["news_title"] == "央行降准 0.25%"
    assert rec["news_source"] == "同花顺"
    assert rec["primary_category"] == "宏观"


def test_dump_sectors_placeholder_has_14_sectors():
    result = dpf.dump_sectors_placeholder()
    assert "sectors" in result
    assert "as_of" in result
    assert "window" in result
    assert len(result["sectors"]) == 14, "应有 14 个 A 股主板块"
    for sec in result["sectors"]:
        assert "name" in sec
        assert "change_pct" in sec
        assert "news_count_24h" in sec


def test_dump_reports_placeholder_has_6_kinds():
    result = dpf.dump_reports_placeholder()
    assert "today" in result
    assert "reports_by_kind" in result
    assert set(result["reports_by_kind"].keys()) == {
        "premarket", "morning", "noon", "afternoon", "close", "evening",
    }
    # 盘前应有 mock 内容，其余为 None
    assert result["reports_by_kind"]["premarket"] is not None
    assert result["reports_by_kind"]["premarket"]["markdown"].startswith("##")


def test_dump_params_handwritten_has_15():
    result = dpf.dump_params_handwritten()
    assert isinstance(result, list)
    assert len(result) >= 10, "至少 10 个示例参数"
    for p in result:
        assert "key" in p
        assert "value" in p
        assert "scope" in p
        assert "description" in p
```

- [ ] **Step 2: 跑测试验证 FAIL**

```bash
uv run pytest tests/unit/test_dump_poc_fixtures.py -v
```

Expected: 4 新测试 FAIL。

- [ ] **Step 3: 实现 4 个 dump 函数**

替换 `scripts/dump_poc_fixtures.py` 中的 4 个 placeholder：

```python
def dump_alerts(session: Session) -> list[dict[str, Any]]:
    repo = AlertRepo(session)
    alerts = repo.list_recent(limit=200)
    return [_alert_to_dict(session, a) for a in alerts]


# 14 个 A 股主板块 + mock 涨跌幅（M3a 占位，M3b 接 SectorTrendService 时换真实数据）
_SECTORS_14 = [
    "券商", "银行", "保险", "半导体", "新能源", "医药", "白酒",
    "地产链", "煤炭", "钢铁", "军工", "通信", "传媒", "AI",
]


def dump_sectors_placeholder() -> dict[str, Any]:
    import random
    rng = random.Random(20260624)  # 固定种子，dump 可重现
    return {
        "as_of": datetime.now(UTC),
        "window": "1d",
        "sectors": [
            {
                "name": name,
                "change_pct": round(rng.uniform(-3.5, 4.0), 2),
                "news_count_24h": rng.randint(2, 25),
                "market_cap_weight": round(rng.uniform(0.02, 0.12), 3),
                "top_symbols": [],  # M3b 接真实数据
            }
            for name in _SECTORS_14
        ],
    }


def dump_reports_placeholder() -> dict[str, Any]:
    premarket_md = """## 隔夜美股
- 道指 +0.5%，纳斯达克 +1.2%
- 半导体板块领涨，AMD +3%

## 政策面
- 央行降准 0.25%（M3a mock）

## 今日关注
- 关注券商板块走势
- 半导体补涨机会
"""
    return {
        "today": datetime.now(UTC).date().isoformat(),
        "reports_by_kind": {
            "premarket": {
                "report_id": 1,
                "kind": "premarket",
                "status": "completed",
                "markdown": premarket_md,
                "generated_by": "agent:daily-report-writer (mock)",
                "generated_at": datetime.now(UTC),
            },
            "morning": None,
            "noon": None,
            "afternoon": None,
            "close": None,
            "evening": None,
        },
    }


def dump_params_handwritten() -> list[dict[str, Any]]:
    return [
        {"key": "sources.ths.enabled", "value": True, "scope": "global", "description": "同花顺新闻源启用", "sensitive": False},
        {"key": "sources.eastmoney.enabled", "value": True, "scope": "global", "description": "东方财富启用", "sensitive": False},
        {"key": "sources.yahoo.enabled", "value": False, "scope": "global", "description": "Yahoo 财经启用", "sensitive": False},
        {"key": "news.realtime_poll_seconds", "value": 60, "scope": "global", "description": "新闻轮询间隔（秒）", "sensitive": False},
        {"key": "news.batch_size", "value": 50, "scope": "global", "description": "一次拉取上限", "sensitive": False},
        {"key": "keywords.涨停.weight", "value": 0.8, "scope": "global", "description": "关键词「涨停」权重", "sensitive": False},
        {"key": "keywords.降准.weight", "value": 1.0, "scope": "global", "description": "关键词「降准」权重", "sensitive": False},
        {"key": "keywords.IPO.weight", "value": 0.5, "scope": "global", "description": "关键词「IPO」权重", "sensitive": False},
        {"key": "ai.provider", "value": "agent", "scope": "global", "description": "AI provider: agent / anthropic / deepseek / rule", "sensitive": False},
        {"key": "ai.timeout_seconds", "value": 45, "scope": "global", "description": "单条 AI 分析超时", "sensitive": False},
        {"key": "alerts.p0_min_importance", "value": 5, "scope": "global", "description": "P0 告警最低重要性", "sensitive": False},
        {"key": "alerts.p1_min_importance", "value": 4, "scope": "global", "description": "P1 告警最低重要性", "sensitive": False},
        {"key": "alerts.cooldown_minutes", "value": 15, "scope": "global", "description": "同主题告警冷却时长", "sensitive": False},
        {"key": "scheduler.market_data_minutes", "value": 5, "scope": "global", "description": "行情快照刷新间隔", "sensitive": False},
        {"key": "scheduler.report_premarket_cron", "value": "0 8 * * 1-5", "scope": "global", "description": "盘前日报 cron", "sensitive": False},
    ]
```

- [ ] **Step 4: 跑全部测试**

```bash
uv run pytest tests/unit/test_dump_poc_fixtures.py -v
```

Expected: 9/9 PASS。

- [ ] **Step 5: 提交**

```bash
git add scripts/dump_poc_fixtures.py tests/unit/test_dump_poc_fixtures.py
git commit -m "feat(m3a): dump_alerts + sectors/reports/params placeholders"
```

---

## Task 8: 跑真实 dump + 提交 JSON 数据 + 验证 schema

**Files:**
- Create: `poc/assets/data/*.json` (脚本生成)

- [ ] **Step 1: 跑 dump 脚本**

```bash
cd C:\AI\Claude\Project_Amarket
uv run python scripts/dump_poc_fixtures.py --pretty
```

Expected: 终端打印 7 类 JSON 文件路径，全部 `✓ wrote`。

- [ ] **Step 2: 人工肉眼检查 dump 出来的文件**

```bash
ls poc/assets/data/
```

应该看到：dashboard.json / news.json / news-detail-*.json (5 个) / alerts.json / sectors.json / reports.json / params.json。

打开 `poc/assets/data/news.json`，确认前 2 条结构合理（含 primary_category / sentiment / importance / related_sectors 等字段）。

打开 `poc/assets/data/dashboard.json`，确认 market_status.indexes 有 6 个左右（取决于 DB 里有多少种 index）。

- [ ] **Step 3: 提交 dump 出来的 JSON 数据**

```bash
git add poc/assets/data/
git commit -m "feat(m3a): commit initial mock JSON dump (130 news + 73 alerts + indexes)"
```

> **注意**：`.gitignore` 已 ignore `data/` (DB 数据库)；但 `poc/assets/data/` 是不同路径，不受 `data/` 规则影响。如果担心被误 ignore，跑 `git check-ignore -v poc/assets/data/news.json` 验证应输出空。

---

## Task 9: 实现 index.html — Dashboard 首页

**Files:**
- Create: `poc/index.html`
- Create: `poc/assets/js/pages/index.js`

- [ ] **Step 1: 写 index.html 框架（HTML5 + head + body + nav mount + Alpine x-data 根）**

完整文件 `poc/index.html`：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Amarket — Dashboard</title>

  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap">

  <!-- Tailwind (POC 用 CDN；M3b 可换预编译) -->
  <script src="https://cdn.tailwindcss.com"></script>

  <!-- 项目 theme CSS -->
  <link rel="stylesheet" href="assets/css/theme-okx.css">

  <!-- Alpine.js & ECharts -->
  <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>

  <!-- 项目 JS -->
  <script src="assets/js/shared.js"></script>
  <script src="assets/js/nav.js"></script>
  <script defer src="assets/js/pages/index.js"></script>
</head>
<body data-theme="okx">

  <!-- 顶部 nav 注入点 -->
  <div id="topbar-mount"></div>

  <main class="page-shell" x-data="indexPage()" x-init="init()">

    <!-- 全局 error banner 由 shared.js showBanner() 注入 -->

    <!-- ① 市场状态栏 -->
    <section class="card mb-4">
      <div class="flex gap-4" style="overflow-x:auto">
        <template x-for="idx in marketStatus.indexes" :key="idx.code">
          <div class="flex flex-col" style="min-width:140px">
            <span class="text-muted" style="font-size:11px" x-text="idx.name"></span>
            <span class="num" style="font-size:18px;font-weight:500" x-text="fmt.num(idx.price)"></span>
            <span class="num" :class="fmt.pctClass(idx.change_pct)" x-text="fmt.pctText(idx.change_pct)"></span>
          </div>
        </template>
        <div x-show="!marketStatus.indexes.length" class="text-muted">暂无行情数据</div>
      </div>
    </section>

    <!-- ② 今日核心结论 -->
    <section class="card mb-4">
      <div class="card-title">今日核心结论</div>
      <p x-text="data.today_conclusion || '（M4 接盘前日报后填充）'"></p>
    </section>

    <!-- ③ 实时新闻流 (左 6/12) ＋ ④/⑤/⑥/⑦/⑧ (右 6/12) -->
    <div class="grid-cols-12">

      <section class="col-span-6 card">
        <div class="card-title flex justify-between items-center">
          <span>实时新闻流</span>
          <span class="text-muted" style="font-size:11px" x-text="`共 ${filteredNews.length} 条`"></span>
        </div>
        <!-- 筛选 -->
        <div class="flex gap-2 mb-2" style="flex-wrap:wrap">
          <select x-model="filter.category" class="text-xs">
            <option value="">全部分类</option>
            <template x-for="c in categories" :key="c">
              <option :value="c" x-text="c"></option>
            </template>
          </select>
          <select x-model="filter.sentiment" class="text-xs">
            <option value="">全部情绪</option>
            <option value="强利多">强利多</option>
            <option value="利多">利多</option>
            <option value="中性">中性</option>
            <option value="利空">利空</option>
            <option value="强利空">强利空</option>
          </select>
          <select x-model.number="filter.minImportance" class="text-xs">
            <option :value="0">所有重要性</option>
            <option :value="3">≥ 3</option>
            <option :value="4">≥ 4</option>
            <option :value="5">= 5</option>
          </select>
          <button @click="resetFilter()" class="btn">清空</button>
        </div>
        <!-- 新闻列表 -->
        <div class="scroll-area" style="max-height:600px">
          <template x-for="item in filteredNews.slice(0, 30)" :key="item.news_id">
            <a :href="`news-detail.html?id=${item.news_id}`" style="display:block;padding:12px;border-bottom:1px solid var(--border-default)">
              <div class="flex justify-between items-center mb-2">
                <span class="num text-muted" style="font-size:11px" x-text="fmt.timeAgo(item.published_at)"></span>
                <div class="flex gap-1 items-center">
                  <span class="tag" x-show="item.alert_level" :class="fmt.alertClass(item.alert_level)" x-text="item.alert_level"></span>
                  <span class="text-muted" style="font-size:11px" x-text="item.source"></span>
                </div>
              </div>
              <div style="color:var(--text-primary);font-weight:500;margin-bottom:4px" x-text="item.title"></div>
              <div class="flex gap-1 items-center" style="font-size:11px">
                <span class="tag" x-show="item.primary_category" x-text="item.primary_category"></span>
                <span class="stars" x-show="item.importance" x-text="fmt.stars(item.importance)"></span>
                <span x-show="item.sentiment" :class="fmt.sentClass(item.sentiment)" x-text="item.sentiment"></span>
              </div>
            </a>
          </template>
          <div x-show="!filteredNews.length" class="p-4 text-muted">暂无符合筛选的新闻</div>
        </div>
      </section>

      <div class="col-span-6 flex flex-col gap-4">

        <!-- ④ P0/P1 重要新闻卡 -->
        <section class="card">
          <div class="card-title">P0 / P1 重要新闻</div>
          <div class="flex flex-col gap-2">
            <template x-for="alert in importantAlerts.slice(0, 6)" :key="alert.alert_id">
              <a :href="`news-detail.html?id=${alert.news_id}`" class="card" style="background:var(--bg-hover);padding:12px">
                <div class="flex justify-between items-center mb-2">
                  <span class="tag" :class="fmt.alertClass(alert.level)" x-text="alert.level"></span>
                  <span class="num text-muted" style="font-size:11px" x-text="fmt.timeAgo(alert.created_at)"></span>
                </div>
                <div style="font-weight:500" x-text="alert.news_title || '(无标题)'"></div>
                <div class="text-muted mt-2" style="font-size:11px" x-text="alert.trigger_reason"></div>
              </a>
            </template>
            <div x-show="!importantAlerts.length" class="text-muted">当前无 P0/P1 告警</div>
          </div>
        </section>

        <!-- ⑤ 板块热力图（mini，sectors.html 全屏版 PR2 出） -->
        <section class="card">
          <div class="card-title">板块热力图</div>
          <div id="sector-heatmap" style="width:100%;height:260px"></div>
          <div class="text-muted mt-2" style="font-size:11px">点击 <a href="sectors.html">→ 看完整版（PR2）</a></div>
        </section>

        <!-- ⑥ 新闻影响板块榜 -->
        <section class="card">
          <div class="card-title">新闻影响板块榜</div>
          <table class="data-grid">
            <thead><tr><th>板块</th><th style="text-align:right">新闻数</th><th style="text-align:right">涨跌</th></tr></thead>
            <tbody>
              <template x-for="sec in topSectors" :key="sec.name">
                <tr>
                  <td x-text="sec.name"></td>
                  <td style="text-align:right" class="num" x-text="sec.news_count_24h"></td>
                  <td style="text-align:right" class="num" :class="fmt.pctClass(sec.change_pct)" x-text="fmt.pctText(sec.change_pct)"></td>
                </tr>
              </template>
            </tbody>
          </table>
        </section>

        <!-- ⑦ 个股异动榜（M3a 暂空，M3b 接） -->
        <section class="card">
          <div class="card-title">个股异动榜</div>
          <div class="text-muted">（M3b 接 /api/dashboard/movers）</div>
        </section>

        <!-- ⑧ 突发告警时间线 -->
        <section class="card">
          <div class="card-title">突发告警</div>
          <div class="flex flex-col gap-2" style="max-height:300px;overflow-y:auto">
            <template x-for="alert in allAlerts.slice(0, 10)" :key="alert.alert_id">
              <div class="flex gap-2 items-center" style="padding:6px 0;border-bottom:1px solid var(--border-default)">
                <span class="tag" :class="fmt.alertClass(alert.level)" x-text="alert.level"></span>
                <span class="num text-muted" style="font-size:11px;min-width:80px" x-text="fmt.time(alert.created_at)"></span>
                <a :href="`news-detail.html?id=${alert.news_id}`" style="flex:1" x-text="alert.news_title || alert.trigger_reason"></a>
              </div>
            </template>
            <div x-show="!allAlerts.length" class="text-muted">无告警</div>
          </div>
        </section>

      </div>
    </div>

    <!-- ⑨ 日报入口 -->
    <section class="card mt-4">
      <div class="card-title">日报入口</div>
      <div class="grid-cols-12" style="gap:8px">
        <template x-for="kind in ['premarket','morning','noon','afternoon','close','evening']" :key="kind">
          <a :href="`reports.html?kind=${kind}`" class="col-span-4 card" :style="reports[kind] ? '' : 'opacity:0.4;pointer-events:none'">
            <div style="font-size:11px" class="text-muted" x-text="kindLabels[kind]"></div>
            <div class="mt-2" x-text="reports[kind] ? '✓ 已生成' : '— 未生成'"></div>
          </a>
        </template>
      </div>
    </section>

  </main>

</body>
</html>
```

- [ ] **Step 2: 写 index 页面 JS（Alpine x-data + 数据加载 + heatmap）**

完整文件 `poc/assets/js/pages/index.js`：

```javascript
/* index.js — Dashboard 首页 Alpine x-data */

function indexPage() {
  const A = window.Amarket;
  return {
    data: {},
    marketStatus: { indexes: [] },
    news: [],
    allAlerts: [],
    importantAlerts: [],
    topSectors: [],
    reports: {},
    kindLabels: {
      premarket: '盘前', morning: '早盘', noon: '午间',
      afternoon: '尾盘', close: '收盘', evening: '晚间',
    },
    filter: { category: '', sentiment: '', minImportance: 0 },
    categories: [],
    fmt: {
      num: (n) => A.formatNumber(n),
      pctText: (p) => A.formatChangePct(p).text,
      pctClass: (p) => A.formatChangePct(p).cls,
      time: A.formatTime,
      timeAgo: A.timeAgo,
      stars: A.stars,
      sentClass: A.sentimentClass,
      alertClass: A.alertTagClass,
    },
    async init() {
      A.checkViewport();
      try {
        const [dashboard, news, alerts, sectors] = await Promise.all([
          A.fetchJSON('assets/data/dashboard.json'),
          A.fetchJSON('assets/data/news.json'),
          A.fetchJSON('assets/data/alerts.json'),
          A.fetchJSON('assets/data/sectors.json'),
        ]);
        this.data = dashboard;
        this.marketStatus = dashboard.market_status || { indexes: [] };
        this.reports = dashboard.today_reports || {};
        this.news = news;
        this.allAlerts = alerts;
        this.importantAlerts = alerts.filter((a) => a.level === 'P0' || a.level === 'P1');
        this.topSectors = sectors.sectors.slice().sort((a, b) => b.news_count_24h - a.news_count_24h).slice(0, 10);
        // 收集所有 categories（去重）
        const catSet = new Set(news.map((n) => n.primary_category).filter(Boolean));
        this.categories = Array.from(catSet).sort();
        this.$nextTick(() => this.renderHeatmap(sectors));
      } catch (e) {
        A.showBanner(`数据加载失败：${e.message}。请跑 \`uv run python scripts/dump_poc_fixtures.py\``);
      }
    },
    get filteredNews() {
      return this.news.filter((n) => {
        if (this.filter.category && n.primary_category !== this.filter.category) return false;
        if (this.filter.sentiment && n.sentiment !== this.filter.sentiment) return false;
        if (this.filter.minImportance && (n.importance || 0) < this.filter.minImportance) return false;
        return true;
      });
    },
    resetFilter() {
      this.filter = { category: '', sentiment: '', minImportance: 0 };
    },
    renderHeatmap(sectorsData) {
      const el = document.getElementById('sector-heatmap');
      if (!el) return;
      const chart = echarts.init(el, null, { renderer: 'canvas' });
      const items = sectorsData.sectors.map((s) => ({
        name: `${s.name}\n${s.change_pct >= 0 ? '+' : ''}${s.change_pct}%`,
        value: Math.abs(s.change_pct) + 1,
        itemStyle: {
          color: s.change_pct >= 0 ? '#14b143' : '#ef454a',
          opacity: Math.min(1, 0.4 + Math.abs(s.change_pct) / 4),
        },
      }));
      chart.setOption({
        backgroundColor: 'transparent',
        series: [{
          type: 'treemap',
          data: items,
          roam: false,
          nodeClick: false,
          breadcrumb: { show: false },
          label: { show: true, color: '#fff', fontSize: 12 },
          itemStyle: { borderColor: '#0c0d0f', borderWidth: 2 },
        }],
      });
      window.addEventListener('resize', () => chart.resize());
    },
  };
}
```

- [ ] **Step 3: 启动服务，浏览器开 http://127.0.0.1:8090/ 验证**

```bash
cd poc && python -m http.server 8090
```

Open `http://127.0.0.1:8090/index.html` 在浏览器。验证：
- 顶部 nav 出现，"首页" 高亮
- ① 市场状态栏出现 6 个左右指数（涨绿跌红）
- ② 今日核心结论显示占位
- ③ 新闻流出现 30 条，可筛选
- ④ P0/P1 卡片有内容（DB 里有 1 P0 + 1 P1）
- ⑤ ECharts treemap 渲染 14 个板块（颜色按涨跌）
- ⑥ 板块榜表格有 10 行
- ⑦ "M3b 接" 占位
- ⑧ 告警时间线有内容
- ⑨ 日报 6 卡片，仅"盘前"亮起

- [ ] **Step 4: 提交**

```bash
git add poc/index.html poc/assets/js/pages/index.js
git commit -m "feat(m3a): index.html — Dashboard 首页（9 区域 + ECharts heatmap）"
```

---

## Task 10: 实现 news.html — 新闻流

**Files:**
- Create: `poc/news.html`
- Create: `poc/assets/js/pages/news.js`

- [ ] **Step 1: 写 news.html**

完整文件 `poc/news.html`：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Amarket — 新闻流</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap">
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="assets/css/theme-okx.css">
  <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
  <script src="assets/js/shared.js"></script>
  <script src="assets/js/nav.js"></script>
  <script defer src="assets/js/pages/news.js"></script>
</head>
<body data-theme="okx">
  <div id="topbar-mount"></div>

  <main class="page-shell" x-data="newsPage()" x-init="init()">

    <div class="flex gap-4">

      <!-- 左侧筛选 -->
      <aside class="card" style="width:240px;flex-shrink:0;max-height:90vh;overflow-y:auto;position:sticky;top:80px">

        <div class="card-title">来源</div>
        <template x-for="src in sourceOptions" :key="src">
          <label class="flex items-center gap-2 mb-2" style="cursor:pointer">
            <input type="checkbox" :value="src" x-model="filter.sources">
            <span x-text="src"></span>
          </label>
        </template>

        <div class="card-title mt-4">分类</div>
        <template x-for="cat in categoryOptions" :key="cat">
          <label class="flex items-center gap-2 mb-2" style="cursor:pointer">
            <input type="checkbox" :value="cat" x-model="filter.categories">
            <span x-text="cat"></span>
          </label>
        </template>

        <div class="card-title mt-4">情绪</div>
        <template x-for="sent in ['强利多','利多','中性','利空','强利空']" :key="sent">
          <label class="flex items-center gap-2 mb-2" style="cursor:pointer">
            <input type="checkbox" :value="sent" x-model="filter.sentiments">
            <span :class="fmt.sentClass(sent)" x-text="sent"></span>
          </label>
        </template>

        <div class="card-title mt-4">最低重要性</div>
        <select x-model.number="filter.minImportance" class="w-full">
          <option :value="0">不限</option>
          <option :value="3">≥ 3 星</option>
          <option :value="4">≥ 4 星</option>
          <option :value="5">= 5 星</option>
        </select>

        <button @click="resetFilter()" class="btn w-full mt-4">清空筛选</button>
      </aside>

      <!-- 主区域 -->
      <div class="flex-1">

        <!-- 顶部 toolbar：搜索 + 排序 + 计数 -->
        <div class="card mb-4 flex gap-4 items-center">
          <input type="search" placeholder="搜索标题..." x-model="filter.search" class="flex-1">
          <select x-model="filter.sortBy">
            <option value="time">时间排序</option>
            <option value="importance">重要性排序</option>
            <option value="sentiment">情绪排序</option>
          </select>
          <span class="text-muted" x-text="`共 ${filteredNews.length} 条`"></span>
        </div>

        <!-- 已选筛选 -->
        <div x-show="hasActiveFilters" class="mb-4 flex gap-2 items-center" style="flex-wrap:wrap">
          <span class="text-muted" style="font-size:11px">已选：</span>
          <template x-for="src in filter.sources" :key="src">
            <span class="tag" style="cursor:pointer" @click="filter.sources = filter.sources.filter(s => s !== src)" x-text="src + ' ×'"></span>
          </template>
          <template x-for="cat in filter.categories" :key="cat">
            <span class="tag" style="cursor:pointer" @click="filter.categories = filter.categories.filter(c => c !== cat)" x-text="cat + ' ×'"></span>
          </template>
          <template x-for="sent in filter.sentiments" :key="sent">
            <span class="tag" :class="fmt.sentClass(sent)" style="cursor:pointer" @click="filter.sentiments = filter.sentiments.filter(s => s !== sent)" x-text="sent + ' ×'"></span>
          </template>
        </div>

        <!-- 新闻列表 -->
        <div class="card" style="padding:0">
          <template x-for="item in sortedNews" :key="item.news_id">
            <a :href="`news-detail.html?id=${item.news_id}`" style="display:block;padding:14px 18px;border-bottom:1px solid var(--border-default)">
              <div class="flex justify-between items-center mb-2">
                <div class="flex gap-2 items-center">
                  <span class="num text-muted" style="font-size:12px" x-text="fmt.dateTime(item.published_at)"></span>
                  <span class="text-muted" style="font-size:12px" x-text="item.source"></span>
                </div>
                <div class="flex gap-1">
                  <span class="tag" x-show="item.alert_level" :class="fmt.alertClass(item.alert_level)" x-text="item.alert_level"></span>
                </div>
              </div>
              <div style="font-size:15px;font-weight:500;margin-bottom:8px" x-text="item.title"></div>
              <div class="flex gap-2 items-center" style="font-size:12px;flex-wrap:wrap">
                <span class="tag" x-show="item.primary_category" x-text="item.primary_category"></span>
                <template x-for="t in (item.tags || []).slice(0, 3)" :key="t">
                  <span class="tag" x-text="t"></span>
                </template>
                <span class="stars" x-show="item.importance" x-text="fmt.stars(item.importance)"></span>
                <span x-show="item.sentiment" :class="fmt.sentClass(item.sentiment)" x-text="item.sentiment"></span>
                <span x-show="item.related_sectors && item.related_sectors.length" class="text-muted">
                  · 影响：<template x-for="sec in item.related_sectors.slice(0,3)" :key="sec.name"><span x-text="sec.name + ' '"></span></template>
                </span>
              </div>
            </a>
          </template>
          <div x-show="!filteredNews.length" class="p-6 text-muted" style="text-align:center">无符合筛选的新闻</div>
        </div>
      </div>
    </div>
  </main>
</body>
</html>
```

- [ ] **Step 2: 写 news.js**

完整文件 `poc/assets/js/pages/news.js`：

```javascript
/* news.js — 新闻流页 */

function newsPage() {
  const A = window.Amarket;
  return {
    news: [],
    sourceOptions: [],
    categoryOptions: [],
    filter: {
      sources: [], categories: [], sentiments: [],
      minImportance: 0, search: '', sortBy: 'time',
    },
    fmt: {
      dateTime: A.formatDateTime,
      stars: A.stars,
      sentClass: A.sentimentClass,
      alertClass: A.alertTagClass,
    },
    async init() {
      A.checkViewport();
      try {
        this.news = await A.fetchJSON('assets/data/news.json');
        this.sourceOptions = Array.from(new Set(this.news.map((n) => n.source).filter(Boolean))).sort();
        this.categoryOptions = Array.from(new Set(this.news.map((n) => n.primary_category).filter(Boolean))).sort();
      } catch (e) {
        A.showBanner(`数据加载失败：${e.message}`);
      }
    },
    get hasActiveFilters() {
      return this.filter.sources.length || this.filter.categories.length ||
             this.filter.sentiments.length || this.filter.minImportance ||
             this.filter.search;
    },
    get filteredNews() {
      return this.news.filter((n) => {
        if (this.filter.sources.length && !this.filter.sources.includes(n.source)) return false;
        if (this.filter.categories.length && !this.filter.categories.includes(n.primary_category)) return false;
        if (this.filter.sentiments.length && !this.filter.sentiments.includes(n.sentiment)) return false;
        if (this.filter.minImportance && (n.importance || 0) < this.filter.minImportance) return false;
        if (this.filter.search) {
          const q = this.filter.search.toLowerCase();
          if (!(n.title || '').toLowerCase().includes(q) &&
              !(n.summary || '').toLowerCase().includes(q)) return false;
        }
        return true;
      });
    },
    get sortedNews() {
      const arr = this.filteredNews.slice();
      if (this.filter.sortBy === 'importance') {
        arr.sort((a, b) => (b.importance || 0) - (a.importance || 0));
      } else if (this.filter.sortBy === 'sentiment') {
        const order = { '强利空': -2, '利空': -1, '中性': 0, '利多': 1, '强利多': 2 };
        arr.sort((a, b) => (order[b.sentiment] ?? 0) - (order[a.sentiment] ?? 0));
      } else {
        arr.sort((a, b) => new Date(b.published_at) - new Date(a.published_at));
      }
      return arr;
    },
    resetFilter() {
      this.filter = {
        sources: [], categories: [], sentiments: [],
        minImportance: 0, search: '', sortBy: 'time',
      };
    },
  };
}
```

- [ ] **Step 3: 浏览器验证**

打开 `http://127.0.0.1:8090/news.html`：
- 顶部 nav "新闻流" 高亮
- 左侧 5 个筛选维度（来源 / 分类 / 情绪 / 重要性 / 搜索）都可勾
- 选 1 个分类 → 列表实时过滤
- 顶部 toolbar 排序切换生效
- 已选筛选 chip 显示，点 × 移除
- 每条新闻有时间 + 来源 + 标题 + 分类 + 标签 + ★ + 情绪 + 影响板块
- 点条目跳详情页（详情页是 Task 11，目前会 404，下个 task 修）

- [ ] **Step 4: 提交**

```bash
git add poc/news.html poc/assets/js/pages/news.js
git commit -m "feat(m3a): news.html — 新闻流（侧栏筛选 + 排序 + 搜索）"
```

---

## Task 11: 实现 news-detail.html — 新闻详情

**Files:**
- Create: `poc/news-detail.html`
- Create: `poc/assets/js/pages/news-detail.js`

- [ ] **Step 1: 写 news-detail.html**

完整文件 `poc/news-detail.html`：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Amarket — 新闻详情</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap">
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="assets/css/theme-okx.css">
  <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
  <script src="assets/js/shared.js"></script>
  <script src="assets/js/nav.js"></script>
  <script defer src="assets/js/pages/news-detail.js"></script>
</head>
<body data-theme="okx">
  <div id="topbar-mount"></div>

  <main class="page-shell" x-data="newsDetailPage()" x-init="init()" style="max-width:960px">

    <!-- 错误状态：缺 id 或 id 不存在 -->
    <div x-show="error" class="banner banner-error">
      <span x-text="error"></span>
      <a href="news.html" class="ml-2">← 返回新闻流</a>
    </div>

    <div x-show="!error && news">

      <a href="news.html" class="text-secondary" style="display:inline-block;margin-bottom:16px">← 返回新闻流</a>

      <!-- 标题区 -->
      <section class="card mb-4">
        <h1 style="font-size:24px;font-weight:600;margin:0 0 12px" x-text="news.title"></h1>
        <div class="flex gap-4 items-center mb-2" style="font-size:13px">
          <span class="num text-muted" x-text="fmt.dateTime(news.published_at)"></span>
          <span class="text-muted" x-text="news.source"></span>
          <a x-show="news.url" :href="news.url" target="_blank" rel="noopener" class="text-secondary">原文链接 →</a>
        </div>
        <div class="flex gap-1" x-show="news.primary_category || news.tags?.length">
          <span class="tag" x-show="news.primary_category" x-text="news.primary_category"></span>
          <template x-for="t in (news.tags || [])" :key="t">
            <span class="tag" x-text="t"></span>
          </template>
        </div>
      </section>

      <!-- 摘要 -->
      <section class="card mb-4" x-show="news.summary">
        <div class="card-title">摘要</div>
        <p x-text="news.summary"></p>
      </section>

      <!-- 正文 -->
      <section class="card mb-4" x-show="news.content">
        <div class="card-title">正文</div>
        <pre style="white-space:pre-wrap;font-family:inherit" x-text="news.content"></pre>
      </section>

      <!-- AI 分析 -->
      <section class="card mb-4" x-show="news.processed_by">
        <div class="card-title">AI 分析 — <span class="text-muted" x-text="news.processed_by"></span></div>

        <div class="grid-cols-12 mb-4">
          <div class="col-span-4">
            <div class="text-muted" style="font-size:11px">重要性</div>
            <div class="stars" style="font-size:18px" x-text="fmt.stars(news.importance)"></div>
          </div>
          <div class="col-span-4">
            <div class="text-muted" style="font-size:11px">紧急度</div>
            <div class="num" style="font-size:18px" x-text="news.urgency || '-'"></div>
          </div>
          <div class="col-span-4">
            <div class="text-muted" style="font-size:11px">置信度</div>
            <div class="num" style="font-size:18px" x-text="news.confidence || '-'"></div>
          </div>
          <div class="col-span-4 mt-2">
            <div class="text-muted" style="font-size:11px">情绪</div>
            <div :class="fmt.sentClass(news.sentiment)" style="font-size:16px" x-text="news.sentiment || '-'"></div>
          </div>
          <div class="col-span-4 mt-2">
            <div class="text-muted" style="font-size:11px">影响时长</div>
            <div x-text="news.impact_horizon || '-'"></div>
          </div>
          <div class="col-span-4 mt-2">
            <div class="text-muted" style="font-size:11px">操作建议</div>
            <div x-text="news.action_hint || '-'"></div>
          </div>
        </div>

        <div x-show="news.related_sectors?.length" class="mb-2">
          <div class="text-muted" style="font-size:11px">影响板块</div>
          <div class="flex gap-2 mt-2" style="flex-wrap:wrap">
            <template x-for="sec in news.related_sectors" :key="sec.name">
              <span class="tag" x-text="`${sec.name} ${(sec.weight*100).toFixed(0)}%`"></span>
            </template>
          </div>
        </div>

        <div x-show="news.related_symbols?.length" class="mb-2">
          <div class="text-muted" style="font-size:11px">关联标的</div>
          <div class="flex gap-2 mt-2" style="flex-wrap:wrap">
            <template x-for="sym in news.related_symbols" :key="sym.code">
              <span class="tag num" x-text="`${sym.code} ${sym.name}`"></span>
            </template>
          </div>
        </div>

        <div x-show="news.alert_level" class="mt-4">
          <span class="tag" :class="fmt.alertClass(news.alert_level)" x-text="news.alert_level"></span>
          <span x-show="news.pushed" class="text-up ml-2">已推送 ✓</span>
        </div>

        <div x-show="news.ai_reasoning" class="mt-4">
          <div class="text-muted" style="font-size:11px;margin-bottom:4px">分析理由</div>
          <p x-text="news.ai_reasoning"></p>
        </div>

        <div x-show="news.risk_notes" class="mt-4">
          <div class="text-muted" style="font-size:11px;margin-bottom:4px">风险提示</div>
          <p x-text="news.risk_notes"></p>
        </div>
      </section>

      <!-- 相关新闻 -->
      <section class="card mb-4" x-show="news.related_news?.length">
        <div class="card-title">相关新闻（同事件）</div>
        <template x-for="rel in news.related_news" :key="rel.news_id">
          <a :href="`news-detail.html?id=${rel.news_id}`" style="display:block;padding:8px 0;border-bottom:1px solid var(--border-default)">
            <div class="flex gap-2 items-center">
              <span class="num text-muted" style="font-size:11px" x-text="fmt.dateTime(rel.published_at)"></span>
              <span class="text-muted" style="font-size:11px" x-text="rel.source"></span>
            </div>
            <div x-text="rel.title"></div>
          </a>
        </template>
      </section>

    </div>
  </main>
</body>
</html>
```

- [ ] **Step 2: 写 news-detail.js**

完整文件 `poc/assets/js/pages/news-detail.js`：

```javascript
/* news-detail.js — 单条新闻详情 */

function newsDetailPage() {
  const A = window.Amarket;
  return {
    news: null,
    error: '',
    fmt: {
      dateTime: A.formatDateTime,
      stars: A.stars,
      sentClass: A.sentimentClass,
      alertClass: A.alertTagClass,
    },
    async init() {
      A.checkViewport();
      const id = A.getQueryParam('id');
      if (!id) {
        this.error = '请从新闻流页面进入（缺少 id 参数）';
        return;
      }
      try {
        this.news = await A.fetchJSON(`assets/data/news-detail-${id}.json`);
        document.title = `Amarket — ${this.news.title}`;
      } catch (e) {
        if (e.message.includes('404')) {
          this.error = `新闻 #${id} 不存在`;
        } else {
          this.error = `加载失败：${e.message}`;
        }
      }
    },
  };
}
```

- [ ] **Step 3: 浏览器验证**

打开 `http://127.0.0.1:8090/news.html`，**点任意一条新闻** → 跳到详情页。

如果 dump 出来的 5 条 news-detail 不一定能命中所有新闻，先在 URL 直接试已 dump 的 id：

```
http://127.0.0.1:8090/news-detail.html?id=<刚刚 dump 的某个 news_id>
```

（看 `poc/assets/data/news-detail-*.json` 文件名取 id）

验证：
- 标题、时间、来源、原文链接显示
- AI 分析区域显示 6 个评分指标
- 影响板块和关联标的以 tag 显示
- 告警等级 + "已推送 ✓"
- 相关新闻区域（若有 event_id）

点不存在的 ID：`?id=999999` → 显示友好错误 banner + 返回链接。
不带 id：直接打开 news-detail.html → 显示"缺少 id 参数"错误。

- [ ] **Step 4: 提交**

```bash
git add poc/news-detail.html poc/assets/js/pages/news-detail.js
git commit -m "feat(m3a): news-detail.html — 单条新闻 + 完整 AI 分析"
```

---

## Task 12: 集成验证 + 截图 + 开 PR

**Files:**
- Modify: 无（仅验证 + 推送 + PR）

- [ ] **Step 1: 全 pytest 跑通**

```bash
cd C:\AI\Claude\Project_Amarket
uv run pytest -x
```

Expected: 全绿（207 之前 + 9 新增 = 216 tests）。

- [ ] **Step 2: ruff + mypy 检查**

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/ scripts/
```

Expected: 全绿。

如果 ruff/mypy 报错，修 → 跑通 → 提交一个 `chore(m3a): ruff/mypy fix` commit。

- [ ] **Step 3: gstack 截图（每页一张）**

启动 POC 服务（另一个终端）：

```bash
cd poc && python -m http.server 8090
```

用 gstack 截图 3 个页面（保存到 `poc/screenshots/`，给 PR 描述用）：

```
gstack 打开 http://127.0.0.1:8090/index.html，截图保存到 C:\AI\Claude\Project_Amarket\poc\screenshots\index.png
gstack 打开 http://127.0.0.1:8090/news.html，截图保存到 C:\AI\Claude\Project_Amarket\poc\screenshots\news.png
gstack 打开 http://127.0.0.1:8090/news-detail.html?id=<已 dump 的某个 id>，截图保存到 C:\AI\Claude\Project_Amarket\poc\screenshots\detail.png
```

> 注：`poc/screenshots/` 暂不 commit 到仓库（除非 PR 需要），上传到 PR 描述。或 commit 进去也 OK。

- [ ] **Step 4: 推送 + 开 PR**

```bash
cd C:\AI\Claude\Project_Amarket
git push -u origin feat/m3a-poc-frame-and-core
gh pr create --title "feat(M3a-PR1): POC 框架 + 核心 3 页 + 全量 mock dump" --body "$(cat <<'EOF'
## Summary

Phase 1 M3a 第一个 PR — 5 OKX 主页中的 3 页 + dump 脚本 + 全量 mock JSON。

实现内容（spec §11.1）：
- `poc/` 目录骨架 + serve.bat / serve.sh / README.md
- `assets/css/theme-okx.css`（OKX 配色 token + 共享组件类）
- `assets/js/shared.js`（fetch 包装 / 格式化器）+ `assets/js/nav.js`（顶部 nav 注入）
- `index.html` — Dashboard 首页（9 区域，含 ECharts treemap 板块热力图 mini 版）
- `news.html` — 新闻流（5 维度筛选 + 3 种排序 + 搜索）
- `news-detail.html` — 单条新闻 + 完整 AI 分析（含影响板块 / 关联标的 / 分析理由 / 风险提示）
- `scripts/dump_poc_fixtures.py` — DB → 7 类 JSON（dashboard / news / news-detail-{id} ×5 / alerts / sectors / reports / params）
- 全量 mock JSON dump 已提交到 `poc/assets/data/`

启动：

```bash
cd poc && python -m http.server 8090
# 浏览器开 http://127.0.0.1:8090/
```

刷新数据：

```bash
uv run python scripts/dump_poc_fixtures.py --pretty
```

## Test plan

- [x] 9 个 dump 脚本单元测试全部 PASS
- [x] ruff / mypy / 全量 pytest 全绿
- [ ] reviewer 浏览器打开 http://127.0.0.1:8090/index.html — 9 个区域填了数据
- [ ] reviewer 在 news.html 用 5 个筛选维度过滤 → 计数实时变化
- [ ] reviewer 点 news 条目跳详情，AI 分析 6 个指标显示
- [ ] reviewer ?id=999999 → 友好错误
- [ ] reviewer 截图 3 张（截图见 PR 描述贴）

## Scope 边界

- ❌ 本 PR 不含 `sectors.html` / `reports.html` / `params.html` —— PR2 出
- ❌ 不含赛博朋克 theme CSS —— PR2 出
- ❌ 不动后端 API —— M3b 出

## Next steps

PR2: 剩余 3 页 + cyberpunk theme（`feat/m3a-poc-rest-and-cyberpunk` 分支）

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

PR URL 会输出，记下来。

- [ ] **Step 5: 等 CI 跑绿后 self-merge（按项目惯例）**

```bash
gh pr checks  # 等 CI 全绿
gh pr merge --squash --delete-branch  # squash merge
```

- [ ] **Step 6: 更新 PROJECT_STATE.md 标记 M3a-PR1 完成（在 main 上）**

切回 main + pull + 改 PROJECT_STATE.md。这步留给 session 结束 checklist 一起做。

---

## Self-Review

### 1. Spec 覆盖

| Spec §11.1 PR1 项 | 任务 |
|------------------|------|
| poc/ 目录 | Task 1 |
| serve.bat / serve.sh / README.md | Task 1 |
| theme-okx.css 完整 | Task 2 |
| shared.js + nav.js | Task 3 + 4 |
| index.html 完整 | Task 9 |
| news.html 完整 | Task 10 |
| news-detail.html 完整 | Task 11 |
| dump_poc_fixtures.py 完整 | Task 5 + 6 + 7 |
| assets/data/*.json 全量 dump | Task 8 |
| 验收 + PR | Task 12 |

✅ 覆盖率 100%。

### 2. Placeholder 扫描

无 "TBD" / "TODO" / "适当 X 处理" / "类似 Task N"。所有代码完整。

### 3. 类型一致性

- `dump_poc_fixtures.py` 中 `_news_to_card` / `_alert_to_dict` / `_highest_alert` 函数签名前后引用一致
- Alpine `fmt` 对象在 3 个页面中字段一致（dateTime / stars / sentClass / alertClass）— 已统一通过 `shared.js` 暴露
- JSON 字段名（news_id / alert_id / level 等）从 dump 到前端一致

✅ 通过

### 4. 已知小风险

- Tailwind CDN 首次加载 1-3s（POC 接受）
- ECharts 包大（~300KB），首次加载有感（POC 接受）
- gstack 截图 Task 12 不强制（如失败可手工截）

---

**End of Plan**
