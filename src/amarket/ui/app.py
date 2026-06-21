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

# ----------------------- 🚨 P0-P3 告警（M2-i） -----------------------
st.subheader("🚨 P0-P3 告警（最近 50 条）")
st.caption(
    "基于 NewsAnalysis 自动决策：P0 黑天鹅/重大政策 / P1 即时推送 / P2 30min 汇总 / P3 仅入库"
)

alert_filter_col, _ = st.columns([2, 6])
alert_level_filter = alert_filter_col.selectbox(
    "等级筛选",
    options=["（全部 P0-P2）", "P0", "P1", "P2"],
    index=0,
)
alert_query = ""
if alert_level_filter not in {"（全部 P0-P2）"}:
    alert_query = f"?level={alert_level_filter}&limit=50"
else:
    alert_query = "?limit=50"

try:
    with httpx.Client(timeout=3.0) as client:
        resp = client.get(f"http://{cfg.api.host}:{cfg.api.port}/api/alerts{alert_query}")
    alerts_data = resp.json()
    alerts = alerts_data.get("items", [])
    alerts_total = alerts_data.get("total", 0)
except httpx.RequestError:
    alerts = []
    alerts_total = 0

if not alerts:
    st.info("尚无告警。先跑 `uv run amarket analyze news` 触发 NewsAnalysis → AlertService 决策。")
else:
    st.write(f"**显示 {len(alerts)} / {alerts_total} 条告警**")
    # 统计每个 level 的数量
    level_counts: dict[str, int] = {}
    for a in alerts:
        level_counts[a["level"]] = level_counts.get(a["level"], 0) + 1
    summary_parts = [f"**{lv}: {n}**" for lv, n in sorted(level_counts.items())]
    st.write(" ｜ ".join(summary_parts))

    for a in alerts[:20]:  # 只展示 top 20 避免过长
        level = a["level"]
        level_color = {"P0": "🔴", "P1": "🟠", "P2": "🟡"}.get(level, "⚪")
        with st.container():
            head, time_col = st.columns([5, 1])
            with head:
                title_display = a.get("news_title") or f"news_id={a.get('news_id')}"
                st.markdown(f"{level_color} **{level}** | {title_display}")
                cat = a.get("primary_category") or "?"
                src = a.get("news_source") or "?"
                st.caption(f"📡 {src}　|　🏷 {cat}　|　💡 {a.get('trigger_reason', '')}")
            with time_col:
                created = (a.get("created_at") or "")[:19].replace("T", " ")
                st.caption(created)
            st.divider()

st.divider()

# ----------------------- 📰 最近新闻预览（M1 + M2-i 升级） -----------------------
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

                # 分析 badges 行（M2-i 升级）
                badges: list[str] = [f"📡 {item['source']}"]
                if item.get("alert_level"):
                    lv = item["alert_level"]
                    badges.append({"P0": "🔴 P0", "P1": "🟠 P1", "P2": "🟡 P2"}.get(lv, lv))
                if item.get("primary_category"):
                    badges.append(f"🏷 {item['primary_category']}")
                if item.get("sentiment"):
                    s = item["sentiment"]
                    sent_icon = {
                        "强利多": "🚀",
                        "利多": "⬆",
                        "中性": "➡",
                        "利空": "⬇",
                        "强利空": "💥",
                        "不确定": "❓",
                    }.get(s, "")
                    badges.append(f"{sent_icon} {s}")
                if item.get("importance"):
                    badges.append(f"⭐ imp={item['importance']}")
                if item.get("urgency"):
                    badges.append(f"⚡ urg={item['urgency']}")
                if item.get("tags"):
                    tags_str = " ".join(f"`{t}`" for t in item["tags"][:3])
                    badges.append(tags_str)
                st.caption("　|　".join(badges))

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
    # M1 — 已完成
    ("M1", "数据基座（16 表 + 3 新闻源 + akshare + Repo + API + viz）", True),
    # M2 — 进行中
    ("M2-a", "规则配置 YAML（keywords / sectors / classification）", True),
    ("M2-g", "AI 双路径架构（Brainmaster + SDK FallbackChain）", True),
    ("M2-b", "NewsDeduper（URL / 标题 / SimHash 三层 + events 聚合）", True),
    ("M2-c", "NewsClassifier（一级 8 类 + 二级 14 板块 + 标的）", True),
    ("M2-d", "SimpleRuleScorer（importance / urgency / sentiment）", True),
    ("M2-e", "NewsAnalysis 编排服务（写 news_analysis 表）", True),
    ("M2-f", "AlertService（P0-P3 决策 + alerts 表）", True),
    ("M2-h", "API 升级（/api/news 带分析字段 + /api/alerts）", True),
    ("M2-i", "Dashboard 升级（告警区 + 新闻分析 badges）", True),
    ("M2-j", "集成测试（130 条真新闻喂进 pipeline）", False),
    # M3+
    ("M3", "静态 HTML POC 看板", False),
    ("M4", "真实推送 + APScheduler 调度", False),
    ("M5", "6 时段自动日报", False),
    ("M6", "参数配置模块（版本/回滚/审计）", False),
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
