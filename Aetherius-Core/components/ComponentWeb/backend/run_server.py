#!/usr/bin/env python3
"""
Web组件后端服务器启动脚本
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 导入FastAPI应用
from app.main import create_app
import uvicorn

def main():
    """启动服务器"""
    # 创建应用
    app = create_app()
    
    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,  # 使用8080端口保持与前端配置一致
        reload=True,  # 保持自动重启功能
        reload_dirs=[str(current_dir / "app")],  # 只监视app目录避免不必要的重启
        reload_excludes=["*.log", "*.tmp", "__pycache__/*", "*.pyc"],  # 排除临时文件
        access_log=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()