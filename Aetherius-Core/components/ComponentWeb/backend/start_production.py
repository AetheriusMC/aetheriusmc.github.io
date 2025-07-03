#!/usr/bin/env python3
"""
Web组件后端生产环境启动脚本
- 禁用自动重启
- 优化性能设置
- 增强日志记录
"""

import sys
import os
import logging
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 导入FastAPI应用
from app.main import create_app
import uvicorn

def setup_production_logging():
    """设置生产环境日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/backend.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """启动生产环境服务器"""
    # 设置日志
    setup_production_logging()
    
    # 创建应用
    app = create_app()
    
    print("🚀 启动Aetherius Web组件生产环境服务器...")
    print("📍 地址: http://0.0.0.0:8080")
    print("🔒 模式: 生产环境 (自动重启已禁用)")
    print("📝 日志: logs/backend.log")
    
    # 启动服务器 - 生产环境配置
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        reload=False,  # 生产环境禁用自动重启
        access_log=True,
        log_level="info",
        workers=1,  # 单进程模式，适合WebSocket
        # 性能优化
        loop="asyncio",
        http="auto",
        # 安全设置
        server_header=False,
        date_header=True
    )

if __name__ == "__main__":
    main()