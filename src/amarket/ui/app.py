"""Streamlit 管理面板入口（M0 占位 Hello World + 通知测试）。

启动：
    uv run streamlit run src/amarket/ui/app.py --server.port 8501

后续 milestone:
- M3: 加入 Phase 1 三大模块查看页
- M5: 完整 5 页（总览 / 新闻 / 推送日志 / 配置 / 测试工具）+ 参数面板
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx
import streamlit as st

from amarket import __version__
from amarket.services.config_service import get_app_config
from amarket.services.notify_test import send_test_message_sync
from amarket.services.observability import iter_notifiers, list_notifier_channels

cfg = get_app_config()

st.set_page_config(
    page_title=(
        f"Project_Amarket — {cfg.project_meta.current_phase} {cfg.project_meta.current_milestone}"
    ),
    page_icon="📈",
    layout="wide",
)

st.title("📈 Project_Amarket")
st.caption("A 股新闻分析 + 行情看板平台 — 小组联合项目（永不实盘）")

# ----------------------- 顶部状态卡 -----------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("版本", __version__)
col2.metric("Spec", cfg.project_meta.spec_version)
col3.metric("Phase", cfg.project_meta.current_phase)
col4.metric("Milestone", cfg.project_meta.current_milestone)

st.divider()

# ----------------------- 后端健康检查 -----------------------
st.subheader("🩺 后端健康")

api_url = f"http://{cfg.api.host}:{cfg.api.port}/healthz"
st.caption(f"目标：`{api_url}`")

refresh_col, _ = st.columns([1, 5])
with refresh_col:
    if st.button("🔄 刷新", type="primary", key="refresh_health"):
        st.rerun()

try:
    with httpx.Client(timeout=3.0) as client:
        resp = client.get(api_url)
    data: dict[str, Any] = resp.json()

    status = data.get("status", "unknown")
    if status == "healthy":
        st.success(f"✅ FastAPI 健康（HTTP {resp.status_code}）")
    elif status == "degraded":
        st.warning(f"⚠️ FastAPI 降级（HTTP {resp.status_code}）— 可能是 notifier 未配置或失败")
    else:
        st.error(f"❌ FastAPI 不健康（HTTP {resp.status_code}）")

    st.json(data, expanded=False)

except httpx.RequestError as exc:
    st.error(f"❌ 无法连接 FastAPI: {exc}")
    st.info(
        "👉 请先启动后端：`uv run uvicorn amarket.main:app --port 8080`\n\n"
        "或用一键脚本 `start.bat` (Windows) / `start.sh` (Linux/macOS)。"
    )

st.divider()

# ----------------------- 📬 通知测试 -----------------------
st.subheader("📬 通知测试")
st.caption(
    "配置 `.env` 中的 `WEWORK_BOT_WEBHOOK_URL` / `WEWORK_ALERT_BOT_WEBHOOK_URL` / "
    "`LARK_BOT_WEBHOOK_URL` 后，可一键发送测试消息验证通路。"
)

configured = dict(iter_notifiers())
all_channels = list_notifier_channels()

channel_descs = {
    "wework": ("企业微信（业务推送）", "WEWORK_BOT_WEBHOOK_URL"),
    "wework_alert": ("企业微信（告警专用）", "WEWORK_ALERT_BOT_WEBHOOK_URL"),
    "lark": ("飞书机器人", "LARK_BOT_WEBHOOK_URL"),
}

n_cols = st.columns(len(all_channels))
for idx, channel in enumerate(all_channels):
    desc, env_var = channel_descs[channel]
    with n_cols[idx]:
        st.markdown(f"**{desc}**")
        if channel in configured:
            health = configured[channel].health_check()
            icon = {"ok": "🟢", "degraded": "🟡", "down": "🔴", "disabled": "⚪"}.get(
                health.status, "❓"
            )
            st.markdown(f"{icon} `{health.status}`")
            if health.last_error:
                st.caption(f"上次错误：{health.last_error[:60]}")
            if st.button("🧪 发测试", key=f"test_{channel}"):
                with st.spinner(f"正在发送到 {desc}..."):
                    result = send_test_message_sync(channel)
                if result.ok:
                    st.success(f"✅ 已发送 @ {result.sent_at.strftime('%H:%M:%S UTC')}")
                else:
                    st.error(f"❌ {result.error}")
        else:
            st.markdown("⚪ `未配置`")
            st.caption(f"在 `.env` 设置 `{env_var}` 后重启 server 即可启用")

st.caption("📌 测试消息会自动附加合规声明（_本信息仅供个人/小组学习参考，不构成任何投资建议_）")

st.divider()

# ----------------------- 📊 主要指数快照（M1） -----------------------
st.subheader("📊 主要指数快照")
st.caption("数据来源：akshare（A 股主要指数日线）。刷新数据：`uv run amarket collect market`")

try:
    with httpx.Client(timeout=3.0) as client:
        resp = client.get(f"http://{cfg.api.host}:{cfg.api.port}/api/dashboard/market-status")
    indexes = resp.json().get("indexes", [])
except httpx.RequestError:
    indexes = []

if not indexes:
    st.info("尚无指数数据。请先跑 `uv run amarket collect market`。")
else:
    metric_cols = st.columns(min(len(indexes), 6))
    for idx, snap in enumerate(indexes[:6]):
        col = metric_cols[idx]
        change_pct = snap.get("change_pct")
        delta_str = f"{change_pct:+.2f}%" if isinstance(change_pct, int | float) else None
        col.metric(
            label=snap.get("name", snap["code"]),
            value=f"{snap['price']:.2f}",
            delta=delta_str,
        )

st.divider()

# ----------------------- 📰 最近新闻预览（M1） -----------------------
st.subheader("📰 最近新闻预览")
st.caption(
    "数据来源：东方财富 7x24 + 新浪财经 7x24 + 雅虎财经 RSS。刷新数据：`uv run amarket collect news`"
)

filter_col, _ = st.columns([2, 6])
source_filter = filter_col.selectbox(
    "按源筛选",
    options=["（全部）", "eastmoney", "sina", "yahoo"],
    index=0,
)
source_param = "" if source_filter == "（全部）" else f"?source={source_filter}&limit=20"
if not source_param:
    source_param = "?limit=20"

try:
    with httpx.Client(timeout=3.0) as client:
        resp = client.get(f"http://{cfg.api.host}:{cfg.api.port}/api/news{source_param}")
    news_data = resp.json()
    news_items = news_data.get("items", [])
    total = news_data.get("total", 0)
except httpx.RequestError:
    news_items = []
    total = 0

if not news_items:
    st.info("尚无新闻数据。请先跑 `uv run amarket collect news`。")
else:
    st.write(f"**显示 {len(news_items)} / {total} 条**")
    for item in news_items:
        with st.container():
            head_col, time_col = st.columns([5, 1])
            with head_col:
                title = item["title"]
                if item.get("url"):
                    st.markdown(f"**[{title}]({item['url']})**")
                else:
                    st.markdown(f"**{title}**")
                st.caption(f"📡 {item['source']}")
                if item.get("summary"):
                    st.write(item["summary"])
            with time_col:
                pub = item.get("published_at", "")[:19].replace("T", " ")
                st.caption(pub)
            st.divider()

st.divider()

# ----------------------- 当前 Milestone 进度 -----------------------
st.subheader("🎯 当前 Milestone")

milestones = [
    # M0 — 已完成
    ("M0", "项目骨架 + 工具链 + CI + DB + API/UI 入口 + Notifier 骨架", True),
    ("M0+", "通知预留 (healthz + Streamlit + CLI notify)", True),
    # M1 — 进行中（feature branch）
    ("M1-a", "完整 11+ 张表 SQLModel + Alembic migration", True),
    ("M1-b", "NewsSource 接口 + 3 个源 (东财 / 新浪 / 雅虎)", True),
    ("M1-c", "MarketDataSource + akshare 主要指数", True),
    ("M1-d", "Repository 层 (6 个 repo)", True),
    ("M1-e", "API endpoints (/api/news + /api/dashboard/*)", True),
    ("M1-f", "NewsCollector + CLI `amarket collect news/market`", True),
    ("M1-g", "集成测试 + Adapter 单元测试 (90.14% 覆盖率)", True),
    ("M1-h", "Streamlit 可视化 + 文档收尾 (本次提交)", True),
    # M2+ — 未开始
    ("M2", "新闻去重 + 8 类分类 + P0-P3 告警决策", False),
    ("M3", "完整看板 API + 静态 HTML POC", False),
    ("M4", "6 时段日报 + AI 分析 + 全渠道推送", False),
    ("M5", "参数配置模块 (版本/回滚/审计)", False),
    ("M6", "集成测试 + UML + 试运行", False),
]

done = sum(1 for *_, completed in milestones if completed)
total_m = len(milestones)
st.progress(done / total_m, text=f"Phase 1 进度 {done}/{total_m}")

for code, name, completed in milestones:
    icon = "✅" if completed else "⏳"
    st.write(f"{icon} **{code}** — {name}")

st.divider()

# ----------------------- 文档导航 -----------------------
st.subheader("📚 文档导航")
st.markdown(
    """
- [📐 Spec v3 — 当前设计](https://github.com/dangbuzhudeXNEL/Project_Amarket/blob/main/docs/superpowers/specs/2026-06-19-spec1-v3-merged.md)
- [📋 PROJECT_STATE — 项目"现在到哪了"](https://github.com/dangbuzhudeXNEL/Project_Amarket/blob/main/docs/PROJECT_STATE.md)
- [🧑‍💻 CONTRIBUTING — 小组协作规范](https://github.com/dangbuzhudeXNEL/Project_Amarket/blob/main/CONTRIBUTING.md)
- [🤖 CLAUDE.md — AI 协作约定](https://github.com/dangbuzhudeXNEL/Project_Amarket/blob/main/CLAUDE.md)
"""
)

st.caption(
    f"⏱️ 本页面渲染时间：{datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}　|　"
    "📌 本系统仅用于个人 / 小组学习参考，不构成任何投资建议；**永远不做实盘下单**。"
)
