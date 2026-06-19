"""Streamlit 管理面板入口（M0 占位 Hello World）。

启动：
    uv run streamlit run src/amarket/ui/app.py --server.port 8501

后续 milestone:
- M3: 加入 Phase 1 三大模块查看页
- M5: 完整 5 页（总览 / 新闻 / 推送日志 / 配置 / 测试工具）+ 参数面板
"""

from __future__ import annotations

from typing import Any

import httpx
import streamlit as st

from amarket import __version__
from amarket.services.config_service import get_app_config

cfg = get_app_config()

st.set_page_config(
    page_title=f"Project_Amarket — {cfg.project_meta.current_phase} {cfg.project_meta.current_milestone}",
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

if st.button("🔄 刷新", type="primary"):
    st.rerun()

try:
    with httpx.Client(timeout=3.0) as client:
        resp = client.get(api_url)
    data: dict[str, Any] = resp.json()

    status = data.get("status", "unknown")
    if status == "healthy":
        st.success(f"✅ FastAPI 健康（HTTP {resp.status_code}）")
    elif status == "degraded":
        st.warning(f"⚠️ FastAPI 降级（HTTP {resp.status_code}）")
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
    ("M0-h", "CLI 骨架（amarket healthcheck）", False),
    ("M0-i", "启动脚本（start.bat / start.sh）", False),
    ("M0-j", "Notifier 接口骨架（企微 + 飞书）", False),
    ("M0-k", "smoke 测试 + conftest", False),
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

st.caption("📌 本系统仅用于个人 / 小组学习参考，不构成任何投资建议；**永远不做实盘下单**。")
