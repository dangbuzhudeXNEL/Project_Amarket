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

# ----------------------- 当前 Milestone 进度 -----------------------
st.subheader("🎯 当前 Milestone")

m0_tasks = [
    ("M0-a", "项目骨架（pyproject.toml + src 包结构）", True),
    ("M0-b", "工具链（ruff + mypy + pytest + pre-commit）", True),
    ("M0-c", "CI（GitHub Actions）", True),
    ("M0-d", "配置 + 日志（app.yml + structlog）", True),
    ("M0-e", "数据库（SQLite + Alembic baseline）", True),
    ("M0-f", "FastAPI 入口（/healthz + /metrics）", True),
    ("M0-g", "Streamlit Hello World（本页面）", True),
    ("M0-h", "CLI 骨架（amarket healthcheck）", True),
    ("M0-i", "启动脚本（start.bat / start.sh）", True),
    ("M0-j", "Notifier 接口骨架（企微 + 飞书）", True),
    ("M0-k", "smoke 测试 + conftest", True),
    ("M0+", "通知预留：healthz 子检查 + Streamlit 测试 + CLI notify", True),
]

done = sum(1 for *_, completed in m0_tasks if completed)
total = len(m0_tasks)
st.progress(done / total, text=f"M0 进度 {done}/{total}")

for code, name, completed in m0_tasks:
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
