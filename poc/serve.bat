@echo off
REM POC 静态服务器 — Windows
cd /d %~dp0
echo Starting POC server at http://127.0.0.1:8090 ...
echo Press Ctrl+C to stop.
python -m http.server 8090
