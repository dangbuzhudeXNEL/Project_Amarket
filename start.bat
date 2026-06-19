@echo off
REM Project_Amarket — Windows 一键启动脚本（同时拉起 FastAPI + Streamlit）
REM
REM Prereq:
REM   - uv (Astral) 已安装并在 PATH
REM   - `uv sync --dev` 已跑过

setlocal

REM 切到脚本所在目录
cd /d "%~dp0"

echo.
echo === Project_Amarket — starting FastAPI + Streamlit ===
echo.

REM 0. 校验 uv
where uv >NUL 2>&1
if errorlevel 1 (
    echo [ERROR] uv not found in PATH. Install via https://docs.astral.sh/uv/
    exit /b 1
)

REM 1. 装/更新依赖
echo [1/3] uv sync --dev
call uv sync --dev || (echo [ERROR] uv sync failed & exit /b 1)

REM 2. 跑数据库迁移
echo.
echo [2/3] alembic upgrade head
call uv run alembic upgrade head || (echo [WARN] alembic upgrade failed; continuing anyway)

REM 3. 启动 FastAPI + Streamlit（各自新窗口）
echo.
echo [3/3] launching servers
start "amarket-api" cmd /k "uv run uvicorn amarket.main:app --host 127.0.0.1 --port 8080 --reload"
start "amarket-ui"  cmd /k "uv run streamlit run src/amarket/ui/app.py --server.port 8501 --server.headless true"

echo.
echo Done. Open:
echo   - API docs : http://127.0.0.1:8080/docs
echo   - Healthz  : http://127.0.0.1:8080/healthz
echo   - UI       : http://127.0.0.1:8501
echo.

endlocal
