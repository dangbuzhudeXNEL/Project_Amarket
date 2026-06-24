#!/usr/bin/env bash
# POC 静态服务器 — Linux / macOS
cd "$(dirname "$0")"
echo "Starting POC server at http://127.0.0.1:8090 ..."
echo "Press Ctrl+C to stop."
python3 -m http.server 8090
