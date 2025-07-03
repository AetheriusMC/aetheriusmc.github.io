#!/usr/bin/env python3
"""
WebConsole组件独立启动脚本
在组件环境中启动，通过socket与Aetherius Core通信
支持前端和后端同时启动，以及重试机制
"""

import asyncio
import os
import sys
import signal
import logging
import subprocess
import time
import shutil
from pathlib import Path

# 添加当前目录到Python路径
component_root = Path(__file__).parent
sys.path.insert(0, str(component_root / "backend"))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(component_root / "logs" / "component.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class WebConsoleComponent:
    """WebConsole组件主类"""
    
    def __init__(self):
        self.app = None
        self.server = None
        self.frontend_process = None
        self.running = False
        self.max_retries = 3
        self.retry_delay = 5
        
    def check_prerequisites(self):
        """检查启动前置条件"""
        logger.info("Checking prerequisites...")
        
        # 检查Node.js和npm
        if not shutil.which("node"):
            logger.error("Node.js not found. Please install Node.js to run the frontend.")
            return False
            
        if not shutil.which("npm"):
            logger.error("npm not found. Please install npm to run the frontend.")
            return False
            
        # 检查前端依赖
        frontend_dir = component_root / "frontend"
        if not (frontend_dir / "node_modules").exists():
            logger.warning("Frontend dependencies not found. Installing...")
            try:
                subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
                logger.info("Frontend dependencies installed successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install frontend dependencies: {e}")
                return False
        
        return True
    
    async def start_frontend(self):
        """启动前端开发服务器"""
        try:
            logger.info("Starting frontend development server...")
            frontend_dir = component_root / "frontend"
            
            # 启动前端开发服务器
            self.frontend_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待前端服务器启动
            await asyncio.sleep(3)
            
            if self.frontend_process.poll() is None:
                logger.info("Frontend development server started successfully")
                return True
            else:
                stdout, stderr = self.frontend_process.communicate()
                logger.error(f"Frontend server failed to start: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start frontend: {e}")
            return False
    
    async def start_backend(self):
        """启动后端服务器"""
        try:
            logger.info("Starting backend server...")
            
            # 设置环境变量
            os.environ.setdefault("AETHERIUS_CONSOLE_SOCKET", 
                                str(Path(__file__).parent.parent.parent / "data" / "console" / "console.sock"))
            
            # 导入和创建FastAPI应用
            from app.main import create_app
            
            self.app = create_app()
            
            # 启动uvicorn服务器
            import uvicorn
            
            config = uvicorn.Config(
                app=self.app,
                host="0.0.0.0",
                port=8000,
                log_level="info",
                access_log=True,
                loop="asyncio"
            )
            
            self.server = uvicorn.Server(config)
            logger.info("Backend server starting on http://0.0.0.0:8000")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start backend: {e}")
            return False

    async def start_with_retry(self):
        """带重试机制的启动"""
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Starting WebConsole component (attempt {attempt}/{self.max_retries})...")
                
                # 检查前置条件
                if not self.check_prerequisites():
                    logger.error("Prerequisites check failed")
                    if attempt < self.max_retries:
                        logger.info(f"Retrying in {self.retry_delay} seconds...")
                        await asyncio.sleep(self.retry_delay)
                        continue
                    else:
                        raise RuntimeError("Prerequisites check failed after all retries")
                
                # 启动前端
                if not await self.start_frontend():
                    logger.error("Frontend startup failed")
                    if attempt < self.max_retries:
                        logger.info(f"Retrying in {self.retry_delay} seconds...")
                        await asyncio.sleep(self.retry_delay)
                        continue
                    else:
                        raise RuntimeError("Frontend startup failed after all retries")
                
                # 启动后端
                if not await self.start_backend():
                    logger.error("Backend startup failed")
                    if attempt < self.max_retries:
                        logger.info(f"Retrying in {self.retry_delay} seconds...")
                        await asyncio.sleep(self.retry_delay)
                        continue
                    else:
                        raise RuntimeError("Backend startup failed after all retries")
                
                # 启动成功
                self.running = True
                logger.info("WebConsole component started successfully!")
                logger.info("Frontend: http://localhost:3000")
                logger.info("Backend API: http://localhost:8000")
                
                # 启动后端服务器
                await self.server.serve()
                break
                
            except Exception as e:
                logger.error(f"Attempt {attempt} failed: {e}")
                
                # 清理资源
                await self.cleanup_failed_start()
                
                if attempt < self.max_retries:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error("All startup attempts failed")
                    raise

    async def cleanup_failed_start(self):
        """清理失败启动的资源"""
        try:
            if self.frontend_process and self.frontend_process.poll() is None:
                self.frontend_process.terminate()
                await asyncio.sleep(1)
                if self.frontend_process.poll() is None:
                    self.frontend_process.kill()
                    
            if self.server:
                await self.server.shutdown()
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def start(self):
        """启动WebConsole组件"""
        await self.start_with_retry()
            
    async def stop(self):
        """停止WebConsole组件"""
        try:
            logger.info("Stopping WebConsole component...")
            self.running = False
            
            # 停止前端进程
            if self.frontend_process and self.frontend_process.poll() is None:
                logger.info("Stopping frontend server...")
                self.frontend_process.terminate()
                await asyncio.sleep(2)
                if self.frontend_process.poll() is None:
                    logger.warning("Force killing frontend process...")
                    self.frontend_process.kill()
                logger.info("Frontend server stopped")
            
            # 停止后端服务器
            if self.server:
                logger.info("Stopping backend server...")
                await self.server.shutdown()
                logger.info("Backend server stopped")
                
            logger.info("WebConsole component stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping WebConsole component: {e}")

# 全局组件实例
component = WebConsoleComponent()

def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"Received signal {signum}, shutting down...")
    asyncio.create_task(component.stop())

async def main():
    """主函数"""
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="WebConsole Component Launcher")
    parser.add_argument("--frontend-only", action="store_true", help="Only start frontend")
    parser.add_argument("--backend-only", action="store_true", help="Only start backend")
    parser.add_argument("--max-retries", type=int, default=3, help="Maximum retry attempts")
    parser.add_argument("--retry-delay", type=int, default=5, help="Delay between retries (seconds)")
    parser.add_argument("--no-retry", action="store_true", help="Disable retry mechanism")
    args = parser.parse_args()
    
    # 应用参数
    if not args.no_retry:
        component.max_retries = args.max_retries
        component.retry_delay = args.retry_delay
    else:
        component.max_retries = 1
    
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 确保必要目录存在
        log_dir = component_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logger.info("=== WebConsole Component Launcher ===")
        logger.info(f"Frontend only: {args.frontend_only}")
        logger.info(f"Backend only: {args.backend_only}")
        logger.info(f"Max retries: {component.max_retries}")
        logger.info(f"Retry delay: {component.retry_delay}s")
        
        # 根据参数启动不同的服务
        if args.frontend_only:
            # 仅启动前端
            if component.check_prerequisites():
                if await component.start_frontend():
                    logger.info("Frontend started successfully. Press Ctrl+C to stop.")
                    # 保持运行
                    while component.frontend_process and component.frontend_process.poll() is None:
                        await asyncio.sleep(1)
                else:
                    logger.error("Failed to start frontend")
                    sys.exit(1)
            else:
                logger.error("Prerequisites check failed")
                sys.exit(1)
                
        elif args.backend_only:
            # 仅启动后端
            if await component.start_backend():
                logger.info("Backend started successfully. Press Ctrl+C to stop.")
                await component.server.serve()
            else:
                logger.error("Failed to start backend")
                sys.exit(1)
        else:
            # 启动完整组件（前端+后端）
            await component.start()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Component failed: {e}")
        sys.exit(1)
    finally:
        await component.stop()

if __name__ == "__main__":
    print("🚀 Starting WebConsole Component...")
    print("   Frontend: http://localhost:3000")
    print("   Backend:  http://localhost:8000")
    print("   Press Ctrl+C to stop")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✋ Shutdown requested by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)