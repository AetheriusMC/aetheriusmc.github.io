#!/bin/bash

# 前端启动脚本 - 自动重启和错误处理
cd /workspaces/aetheriusmc.github.io/Aetherius-Core/components/ComponentWeb/frontend

echo "🚀 启动前端服务器..."

# 清理旧进程
echo "🧹 清理旧进程..."
pkill -f "vite\|vue\|npm.*dev" 2>/dev/null || true
sleep 2

# 释放端口
echo "🔓 释放3000端口..."
PORT_PID=$(lsof -ti:3000 2>/dev/null)
if [ ! -z "$PORT_PID" ]; then
    kill -9 $PORT_PID
    sleep 1
fi

# 清理缓存
echo "🗑️ 清理缓存..."
rm -rf node_modules/.vite dist .vite 2>/dev/null || true

# 检查node_modules
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖..."
    npm install
fi

# 启动开发服务器
echo "▶️ 启动开发服务器..."
export NODE_OPTIONS="--max_old_space_size=4096"
npm run dev