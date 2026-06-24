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
