#!/bin/bash
# Skill Dashboard 本地服务器启动脚本
# 用法: ./start-dashboard.sh

PORT=18080
cd "$(dirname "$0")"

echo "🚀 启动 Skill Dashboard 服务器..."
echo "📍 地址: http://localhost:$PORT/skill-dashboard.html"
echo "🛑 按 Ctrl+C 停止"
echo ""

python3 -m http.server $PORT
