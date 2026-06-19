#!/usr/bin/env bash
# Project_Amarket — Linux/macOS 一键启动脚本（同时拉起 FastAPI + Streamlit）
#
# Prereq:
#   - uv (Astral) 已安装并在 PATH
#   - `uv sync --dev` 已跑过

set -euo pipefail

# 切到脚本所在目录
cd "$(dirname "$0")"

echo
echo "=== Project_Amarket — starting FastAPI + Streamlit ==="
echo

# 0. 校验 uv
if ! command -v uv >/dev/null 2>&1; then
    echo "[ERROR] uv not found in PATH. Install via https://docs.astral.sh/uv/"
    exit 1
fi

# 1. 装/更新依赖
echo "[1/3] uv sync --dev"
uv sync --dev

# 2. 跑数据库迁移
echo
echo "[2/3] alembic upgrade head"
uv run alembic upgrade head || echo "[WARN] alembic upgrade failed; continuing"

# 3. 启动 FastAPI + Streamlit
echo
echo "[3/3] launching servers"

# 后台跑 uvicorn
uv run uvicorn amarket.main:app --host 127.0.0.1 --port 8080 --reload &
API_PID=$!

# 后台跑 streamlit
uv run streamlit run src/amarket/ui/app.py --server.port 8501 --server.headless true &
UI_PID=$!

echo
echo "API  pid=${API_PID}  → http://127.0.0.1:8080/docs"
echo "UI   pid=${UI_PID}   → http://127.0.0.1:8501"
echo "Healthz                 http://127.0.0.1:8080/healthz"
echo

# Ctrl-C / SIGTERM → 杀子进程
trap 'echo; echo "[stopping] killing ${API_PID} ${UI_PID}"; kill ${API_PID} ${UI_PID} 2>/dev/null || true; exit 0' INT TERM

# 等其中一个挂掉
wait -n
EXIT_CODE=$?

# 把另一个也杀掉
kill ${API_PID} ${UI_PID} 2>/dev/null || true
wait || true

exit ${EXIT_CODE}
