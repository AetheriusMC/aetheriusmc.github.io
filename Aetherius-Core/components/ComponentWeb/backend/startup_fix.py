"""
Component-Web启动修复工具
解决组件启用但Web服务器未启动的问题
"""

import asyncio
import uvicorn
import logging
from pathlib import Path
import sys

# 添加项目路径
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

logger = logging.getLogger(__name__)

async def start_web_server_standalone():
    """独立启动Web服务器"""
    try:
        from app.main import create_app
        
        app = create_app(
            cors_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
            component_instance=None
        )
        
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True,
            reload=False
        )
        
        server = uvicorn.Server(config)
        logger.info("启动Web服务器...")
        await server.serve()
        
    except Exception as e:
        logger.error(f"启动Web服务器失败: {e}")
        raise

def check_component_integration():
    """检查组件集成状态"""
    try:
        # 检查Aetherius核心是否可用
        try:
            from aetherius.core.component import WebComponent
            logger.info("✅ Aetherius核心组件基类可用")
        except ImportError as e:
            logger.warning(f"❌ Aetherius核心组件基类不可用: {e}")
        
        # 检查扩展功能
        try:
            from aetherius.core.server_manager_extensions import ServerManagerExtensions
            logger.info("✅ 服务器管理扩展可用")
        except ImportError as e:
            logger.warning(f"❌ 服务器管理扩展不可用: {e}")
        
        # 检查FastAPI应用
        try:
            from app.main import create_app
            app = create_app()
            logger.info(f"✅ FastAPI应用创建成功: {app.title}")
        except Exception as e:
            logger.error(f"❌ FastAPI应用创建失败: {e}")
            
    except Exception as e:
        logger.error(f"组件集成检查失败: {e}")

async def fix_component_startup():
    """修复组件启动问题"""
    logger.info("🔧 开始修复组件启动问题...")
    
    # 1. 检查集成状态
    check_component_integration()
    
    # 2. 尝试启动Web服务器
    try:
        await start_web_server_standalone()
    except KeyboardInterrupt:
        logger.info("👋 用户终止，正在关闭服务器...")
    except Exception as e:
        logger.error(f"❌ 修复失败: {e}")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        asyncio.run(fix_component_startup())
    except KeyboardInterrupt:
        logger.info("程序已退出")