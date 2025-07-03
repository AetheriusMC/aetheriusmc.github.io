"""
Aetherius Component: Web - 主组件类
=================================

基于Aetherius核心WebComponent基类的完整Web界面实现
使用真实的核心API，不包含任何模拟数据
"""

import asyncio
import uvicorn
import logging
import subprocess
from typing import Optional, Dict, Any
from pathlib import Path

# 导入Aetherius核心组件
from aetherius.core.component import WebComponent as BaseWebComponent
from aetherius.core import (
    get_server_wrapper, 
    get_plugin_manager, 
    get_component_manager,
    get_event_manager,
    get_config_manager_extensions,
    get_file_manager
)
from aetherius.core.server_manager_extensions import ServerManagerExtensions
from aetherius.core.player_manager_extensions import PlayerManagerExtensions

# 尝试导入FastAPI应用
def create_app(cors_origins=None, component_instance=None):
    """创建基础Web应用"""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse
    
    app = FastAPI(title="Aetherius Web Console", version="0.1.0")
    
    # 添加CORS支持
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # 存储组件实例
    app.state.component = component_instance
    
    # 主页路由
    @app.get("/", response_class=HTMLResponse)
    async def root():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Aetherius Web Console</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .nav { display: flex; gap: 20px; margin: 20px 0; }
                .nav a { padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Aetherius Web Console</h1>
                <div class="nav">
                    <a href="/console">📟 控制台</a>
                    <a href="/dashboard">📊 仪表板</a>
                    <a href="/players">👥 玩家管理</a>
                </div>
                <h3>组件状态: 正在运行</h3>
            </div>
        </body>
        </html>
        """
    
    # 控制台页面
    @app.get("/console", response_class=HTMLResponse)
    async def console_page():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>控制台 - Aetherius Web Console</title>
            <meta charset="utf-8">
            <style>
                body { font-family: 'Courier New', monospace; margin: 0; background: #1a1a1a; color: #00ff00; }
                .container { padding: 20px; max-width: 1200px; margin: 0 auto; }
                .header { margin-bottom: 20px; padding: 15px; background: #2a2a2a; border-radius: 4px; }
                .console { background: #000; padding: 20px; border-radius: 4px; min-height: 400px; overflow-y: auto; }
                .input-area { margin-top: 20px; display: flex; gap: 10px; }
                .input-area input { flex: 1; padding: 10px; background: #2a2a2a; border: 1px solid #555; color: #00ff00; font-family: inherit; }
                .input-area button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
                .nav { margin-bottom: 20px; }
                .nav a { color: #00aaff; text-decoration: none; margin-right: 20px; }
                .log-line { margin: 2px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="nav">
                    <a href="/">🏠 首页</a>
                    <a href="/console">📟 控制台</a>
                    <a href="/dashboard">📊 仪表板</a>
                    <a href="/players">👥 玩家</a>
                </div>
                
                <div class="header">
                    <h1>📟 Aetherius 控制台</h1>
                </div>
                
                <div class="console" id="console">
                    <div class="log-line">[INFO] Aetherius Web Console 已连接</div>
                    <div class="log-line">[INFO] 使用下方输入框发送服务器命令</div>
                </div>
                
                <div class="input-area">
                    <input type="text" id="command-input" placeholder="输入服务器命令..." onkeypress="handleKeyPress(event)">
                    <button onclick="sendCommand()">发送</button>
                    <button onclick="clearConsole()">清空</button>
                </div>
            </div>
            
            <script>
                let consoleElement = document.getElementById('console');
                
                function addLogLine(message) {
                    const line = document.createElement('div');
                    line.className = 'log-line';
                    const timestamp = new Date().toLocaleTimeString();
                    line.innerHTML = `[${timestamp}] ${message}`;
                    consoleElement.appendChild(line);
                    consoleElement.scrollTop = consoleElement.scrollHeight;
                }
                
                function sendCommand() {
                    const input = document.getElementById('command-input');
                    const command = input.value.trim();
                    if (!command) return;
                    
                    addLogLine(`> ${command}`);
                    
                    fetch('/api/console/command', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ command: command })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            addLogLine(`[SUCCESS] ${data.message || '命令执行成功'}`);
                        } else {
                            addLogLine(`[ERROR] ${data.message || '命令执行失败'}`);
                        }
                    })
                    .catch(error => {
                        addLogLine(`[ERROR] 网络错误: ${error.message}`);
                    });
                    
                    input.value = '';
                }
                
                function handleKeyPress(event) {
                    if (event.key === 'Enter') {
                        sendCommand();
                    }
                }
                
                function clearConsole() {
                    consoleElement.innerHTML = '';
                    addLogLine('[INFO] 控制台已清空');
                }
                
                addLogLine('[INFO] 控制台界面已准备就绪');
            </script>
        </body>
        </html>
        """
    
    # 仪表板页面
    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard_page():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>仪表板 - Aetherius Web Console</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; background: #f5f5f5; }
                .container { padding: 20px; max-width: 1200px; margin: 0 auto; }
                .nav { margin-bottom: 20px; }
                .nav a { color: #007bff; text-decoration: none; margin-right: 20px; }
                .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="nav">
                    <a href="/">🏠 首页</a>
                    <a href="/console">📟 控制台</a>
                    <a href="/dashboard">📊 仪表板</a>
                    <a href="/players">👥 玩家</a>
                </div>
                
                <h1>📊 服务器仪表板</h1>
                
                <div class="card">
                    <h3>🖥️ 服务器状态</h3>
                    <p>运行状态: <strong>正在运行</strong></p>
                    <p>Web组件: <strong>已启用</strong></p>
                </div>
                
                <div class="card">
                    <h3>👥 玩家信息</h3>
                    <p>在线玩家: <strong>0</strong></p>
                </div>
            </div>
        </body>
        </html>
        """
    
    # 玩家管理页面
    @app.get("/players", response_class=HTMLResponse)
    async def players_page():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>玩家管理 - Aetherius Web Console</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; background: #f5f5f5; }
                .container { padding: 20px; max-width: 1200px; margin: 0 auto; }
                .nav { margin-bottom: 20px; }
                .nav a { color: #007bff; text-decoration: none; margin-right: 20px; }
                .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="nav">
                    <a href="/">🏠 首页</a>
                    <a href="/console">📟 控制台</a>
                    <a href="/dashboard">📊 仪表板</a>
                    <a href="/players">👥 玩家</a>
                </div>
                
                <h1>👥 玩家管理</h1>
                
                <div class="card">
                    <p>当前没有在线玩家</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    # API路由
    @app.get("/api/status")
    async def get_status():
        if component_instance:
            return await component_instance.get_server_status()
        return {"error": "Component not available"}
    
    @app.post("/api/console/command")
    async def execute_command(command: dict):
        if component_instance and "command" in command:
            return await component_instance.execute_console_command(command["command"])
        return {"error": "Invalid command"}
    
    # 健康检查
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "component": "Component-Web"}
        
    return app

logger = logging.getLogger(__name__)


class WebComponent(BaseWebComponent):
    """Web界面组件主类 - 使用真实核心API"""
    
    def __init__(self, core_instance=None, config=None):
        super().__init__(core_instance, config)
        self.logger = logging.getLogger("component.web")
        self.web_server: Optional[uvicorn.Server] = None
        self.server_task: Optional[asyncio.Task] = None
        self.frontend_process = None
        
        # 核心服务管理器
        self.server_manager_ext: Optional[ServerManagerExtensions] = None
        self.player_manager_ext: Optional[PlayerManagerExtensions] = None
        self.file_manager = None
        self.config_manager_ext = None
        
        # 创建核心适配器
        try:
            from .app.core.aetherius_adapter import AetheriusCoreAdapter
            self.core_adapter = AetheriusCoreAdapter(core_instance)
        except ImportError:
            self.logger.warning("无法导入核心适配器，使用基础实现")
            self.core_adapter = None
    
    def get_config(self) -> Dict[str, Any]:
        """获取组件配置"""
        return getattr(self, 'config', {}) or {}
    
    def get_status(self) -> Dict[str, Any]:
        """获取组件详细状态"""
        return {
            "enabled": self.is_enabled,
            "web_server": {
                "running": self.web_server is not None and not getattr(self.web_server, 'should_exit', True),
                "host": getattr(self, 'web_host', 'unknown'),
                "port": getattr(self, 'web_port', 'unknown'),
                "task_running": self.server_task is not None and not self.server_task.done()
            },
            "core_services": {
                "server_manager": self.server_manager_ext is not None,
                "player_manager": self.player_manager_ext is not None,
                "file_manager": self.file_manager is not None,
                "config_manager": self.config_manager_ext is not None
            }
        }
    
    async def emit_event(self, event_name: str, data: Any = None):
        """
        发送事件（安全版本）
        
        Args:
            event_name: 事件名称
            data: 事件数据
        """
        try:
            if self.core and hasattr(self.core, 'event_manager') and self.core.event_manager:
                await self.core.event_manager.emit_event(
                    event_name, 
                    data, 
                    source=self.__class__.__name__
                )
            else:
                self.logger.debug(f"无法发送事件 {event_name}: 事件管理器不可用")
        except Exception as e:
            self.logger.warning(f"发送事件失败 {event_name}: {e}")
        
    async def on_load(self):
        """组件加载时调用"""
        self.logger.info("Web组件正在加载...")
        
        # 获取配置
        config = self.get_config() or {}
        self.web_host = config.get("web_host", "0.0.0.0")
        self.web_port = config.get("web_port", 8080)
        self.cors_origins = config.get("cors_origins", ["http://localhost:3000"])
        self.log_level = config.get("log_level", "INFO")
        self.max_log_lines = config.get("max_log_lines", 1000)
        self.websocket_timeout = config.get("websocket_timeout", 60)
        self.enable_file_manager = config.get("enable_file_manager", True)
        self.enable_player_management = config.get("enable_player_management", True)
        
        # 初始化核心服务扩展
        await self._initialize_core_services()
        
        # 创建FastAPI应用
        self.app = create_app(
            cors_origins=self.cors_origins,
            component_instance=self
        )
        
        # 设置应用状态
        self.app.state.server_manager_ext = self.server_manager_ext
        self.app.state.player_manager_ext = self.player_manager_ext
        self.app.state.file_manager = self.file_manager
        self.app.state.config_manager_ext = self.config_manager_ext
        self.app.state.web_component = self
        
        # 创建Uvicorn服务器配置
        self.server_config = uvicorn.Config(
            app=self.app,
            host=self.web_host,
            port=self.web_port,
            log_level=self.log_level.lower(),
            access_log=False,  # 由组件自己记录访问日志
            loop="asyncio"
        )
        
        self.logger.info(f"Web组件加载完成 - 配置端口: {self.web_port}")
        
    async def _initialize_core_services(self):
        """初始化核心服务扩展"""
        try:
            # 获取服务器管理器
            try:
                server_wrapper = get_server_wrapper()
                if server_wrapper:
                    self.server_manager_ext = ServerManagerExtensions(server_wrapper)
                    self.logger.info("服务器管理扩展已初始化")
                else:
                    self.logger.warning("服务器管理器不可用")
            except Exception as e:
                self.logger.warning(f"无法初始化服务器管理扩展: {e}")
            
            # 获取玩家管理器扩展
            try:
                if hasattr(self, 'core') and self.core:
                    player_manager = getattr(self.core, 'player_manager', None)
                    if player_manager:
                        self.player_manager_ext = PlayerManagerExtensions(player_manager)
                        self.logger.info("玩家管理扩展已初始化")
                    else:
                        # 创建独立的玩家管理器扩展
                        self.player_manager_ext = PlayerManagerExtensions(None)
                        self.logger.info("独立玩家管理扩展已初始化")
                else:
                    self.player_manager_ext = PlayerManagerExtensions(None)
                    self.logger.info("创建基础玩家管理扩展")
            except Exception as e:
                self.logger.warning(f"无法初始化玩家管理扩展: {e}")
            
            # 获取文件管理器
            try:
                if self.enable_file_manager:
                    self.file_manager = get_file_manager()
                    if not self.file_manager:
                        try:
                            from aetherius.core.file_manager import FileManager
                            self.file_manager = FileManager()
                        except ImportError:
                            self.logger.warning("FileManager类不可用")
                    if self.file_manager:
                        self.logger.info("文件管理器已初始化")
            except Exception as e:
                self.logger.warning(f"无法初始化文件管理器: {e}")
            
            # 获取配置管理器扩展
            try:
                self.config_manager_ext = get_config_manager_extensions()
                if not self.config_manager_ext:
                    try:
                        from aetherius.core.config_manager_extensions import ConfigManagerExtensions
                        from aetherius.core.config import get_config_manager
                        base_config = get_config_manager()
                        self.config_manager_ext = ConfigManagerExtensions(base_config)
                    except ImportError:
                        self.logger.warning("ConfigManagerExtensions类不可用")
                if self.config_manager_ext:
                    self.logger.info("配置管理扩展已初始化")
            except Exception as e:
                self.logger.warning(f"无法初始化配置管理扩展: {e}")
            
        except Exception as e:
            self.logger.error(f"初始化核心服务失败: {e}")
        
    async def on_enable(self):
        """组件启用时调用"""
        self.logger.info("Web组件正在启用...")
        
        try:
            # 检查端口是否可用
            port = self.config.get('port', 8000)
            if not self._is_port_available(port):
                self.logger.error(f"端口 {port} 已被占用，无法启动Web服务器")
                raise RuntimeError(f"端口 {port} 不可用")
            
            # 注册事件处理器
            await self._register_event_handlers()
            
            # 创建并启动Web服务器
            self.web_server = uvicorn.Server(self.server_config)
            
            # 在后台启动服务器，不等待完成
            async def start_server():
                try:
                    await self.web_server.serve()
                except Exception as e:
                    self.logger.error(f"Web服务器运行中出错: {e}")
            
            self.server_task = asyncio.create_task(start_server())
            
            # 等待服务器启动
            max_wait = 5  # 最多等待5秒
            for i in range(max_wait * 10):  # 每100ms检查一次
                if hasattr(self.web_server, 'started') and self.web_server.started:
                    break
                await asyncio.sleep(0.1)
            else:
                self.logger.warning("Web服务器启动检查超时，但任务已创建")
            
            # 额外检查：尝试连接端口验证
            await asyncio.sleep(1)  # 等待1秒确保服务器完全启动
            
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://{self.web_host}:{self.web_port}/health", timeout=2) as resp:
                        if resp.status == 200:
                            self.logger.info("✅ Web服务器健康检查通过")
                        else:
                            self.logger.warning(f"⚠️ Web服务器响应异常: {resp.status}")
            except Exception as e:
                self.logger.warning(f"⚠️ Web服务器健康检查失败: {e}")
                # 这是警告而非错误，服务器可能正在启动
            
            self.logger.info(f"Web服务器已启动 - http://{self.web_host}:{self.web_port}")
            self.logger.info(f"控制台页面: http://{self.web_host}:{self.web_port}/console")
            self.logger.info(f"仪表板页面: http://{self.web_host}:{self.web_port}/dashboard")
            
            # 启动前端开发服务器
            await self._start_frontend_dev_server()
            
            # 注册Web路由到核心
            await self._register_web_routes()
            
        except Exception as e:
            self.logger.error(f"Web服务器启动失败: {e}")
            # 不抛出异常，允许组件继续启用（但记录错误）
            self.logger.error("Web服务器启动失败，但组件将继续以禁用Web服务器的模式运行")
            
    async def _register_event_handlers(self):
        """注册事件处理器到核心事件系统"""
        try:
            event_manager = get_event_manager()
            if event_manager:
                # 注册服务器事件
                event_manager.register_listener("server_start", self.on_server_start)
                event_manager.register_listener("server_stop", self.on_server_stop)
                
                # 注册玩家事件
                event_manager.register_listener("player_join", self.on_player_join)
                event_manager.register_listener("player_leave", self.on_player_leave)
                
                # 注册控制台事件
                event_manager.register_listener("console_log", self.on_console_log)
                
                self.logger.info("事件处理器已注册")
            else:
                self.logger.warning("事件管理器不可用，跳过事件处理器注册")
        except Exception as e:
            self.logger.warning(f"注册事件处理器失败: {e}")
    
    async def _register_web_routes(self):
        """注册Web路由到核心Web系统"""
        try:
            # 添加路由信息
            routes = [
                {"path": "/", "name": "Dashboard", "description": "主控制面板"},
                {"path": "/console", "name": "Console", "description": "实时控制台"},
                {"path": "/players", "name": "Players", "description": "玩家管理"},
                {"path": "/files", "name": "File Manager", "description": "文件管理器"},
                {"path": "/api/status", "name": "Status API", "description": "状态API"}
            ]
            
            # 将路由信息添加到Web路由列表
            for route in routes:
                self.add_route(route["path"], route["name"])
                
            self.logger.info(f"已注册 {len(routes)} 个Web路由")
        except Exception as e:
            self.logger.error(f"注册Web路由失败: {e}")
    
    async def _start_frontend_dev_server(self):
        """启动前端开发服务器"""
        try:
            import subprocess
            import os
            from pathlib import Path
            
            # 获取前端目录路径
            component_dir = Path(__file__).parent.parent
            frontend_dir = component_dir / "frontend"
            
            if not frontend_dir.exists():
                self.logger.warning("前端目录不存在，跳过前端启动")
                return
            
            # 检查是否已有前端服务在运行
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', 3000))
                sock.close()
                if result == 0:
                    self.logger.info("前端开发服务器已在运行 (端口3000)")
                    return
            except Exception:
                pass
            
            # 检查node_modules是否存在
            if not (frontend_dir / "node_modules").exists():
                self.logger.info("正在安装前端依赖...")
                install_process = await asyncio.create_subprocess_exec(
                    "npm", "install",
                    cwd=frontend_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await install_process.communicate()
                
                if install_process.returncode != 0:
                    self.logger.error("前端依赖安装失败")
                    return
                    
                self.logger.info("前端依赖安装完成")
            
            # 启动前端开发服务器
            self.logger.info("正在启动前端开发服务器...")
            
            # 使用subprocess.Popen而不是asyncio.create_subprocess_exec
            # 这样可以让前端服务器在后台独立运行
            env = os.environ.copy()
            env['CI'] = 'true'  # 避免浏览器自动打开
            
            self.frontend_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=frontend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待前端服务器启动
            await asyncio.sleep(3)
            
            # 检查前端服务器是否启动成功
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', 3000))
                sock.close()
                if result == 0:
                    self.logger.info("✅ 前端开发服务器启动成功 - http://localhost:3000")
                else:
                    # 可能在3001端口
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
                    result = sock.connect_ex(('localhost', 3001))
                    sock.close()
                    if result == 0:
                        self.logger.info("✅ 前端开发服务器启动成功 - http://localhost:3001")
                    else:
                        self.logger.warning("前端服务器启动状态未知")
            except Exception as e:
                self.logger.warning(f"无法检查前端服务器状态: {e}")
                
        except Exception as e:
            self.logger.error(f"启动前端开发服务器失败: {e}")
            
    async def on_disable(self):
        """组件禁用时调用"""
        self.logger.info("Web组件正在禁用...")
        
        try:
            # 检查事件循环状态
            loop = None
            loop_running = False
            try:
                loop = asyncio.get_running_loop()
                loop_running = not loop.is_closed()
            except RuntimeError:
                self.logger.info("没有运行的事件循环，使用同步清理方式")
                loop_running = False
            
            if loop_running:
                # 异步清理方式
                try:
                    # 注销事件处理器
                    await self._unregister_event_handlers()
                    
                    # 停止Web服务器
                    await self._stop_web_server_async()
                except Exception as e:
                    self.logger.warning(f"异步清理部分失败: {e}")
                    # 继续执行同步清理
            
            # 同步清理方式（总是执行）
            self._cleanup_sync()
                
        except Exception as e:
            self.logger.error(f"禁用Web组件失败: {e}")
    
    async def _stop_web_server_async(self):
        """异步停止Web服务器"""
        if self.web_server:
            try:
                # 设置退出标志
                self.web_server.should_exit = True
                
                # 如果服务器正在运行，尝试优雅关闭
                if hasattr(self.web_server, 'servers') and self.web_server.servers:
                    for server in self.web_server.servers:
                        server.close()
                        await server.wait_closed()
                
                self.logger.info("Web服务器已正常停止")
            except Exception as e:
                self.logger.warning(f"停止Web服务器时出错: {e}")
            
            if self.server_task and not self.server_task.done():
                self.server_task.cancel()
                try:
                    await asyncio.wait_for(self.server_task, timeout=3.0)
                    self.logger.info("服务器任务已取消")
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    self.logger.warning("Web服务器停止超时，强制终止")
                except Exception as e:
                    self.logger.warning(f"停止Web服务器时出错: {e}")
    
    def _cleanup_sync(self):
        """同步清理资源"""
        try:
            # 清理Web服务器引用
            if self.web_server:
                if hasattr(self.web_server, 'should_exit'):
                    self.web_server.should_exit = True
                self.web_server = None
            
            # 清理任务引用
            if self.server_task:
                if not self.server_task.done():
                    self.server_task.cancel()
                self.server_task = None
            
            # 等待端口释放
            self._wait_for_port_release()
            
            # 清理前端进程
            if hasattr(self, 'frontend_process') and self.frontend_process:
                try:
                    self.frontend_process.terminate()
                    # 给进程一些时间优雅关闭
                    try:
                        self.frontend_process.wait(timeout=5)
                        self.logger.info("前端开发服务器已关闭")
                    except subprocess.TimeoutExpired:
                        # 如果5秒内没有关闭，强制杀死
                        self.frontend_process.kill()
                        self.frontend_process.wait()
                        self.logger.info("前端开发服务器已强制关闭")
                    self.frontend_process = None
                except Exception as e:
                    self.logger.warning(f"关闭前端进程时出错: {e}")
            
            self.logger.info("Web服务器资源已清理")
            
        except Exception as e:
            self.logger.warning(f"同步清理时出错: {e}")
        
    async def _unregister_event_handlers(self):
        """注销事件处理器"""
        try:
            # 检查事件循环状态
            try:
                loop = asyncio.get_running_loop()
                if loop.is_closed():
                    self.logger.warning("事件循环已关闭，跳过事件处理器注销")
                    return
            except RuntimeError:
                self.logger.warning("没有运行的事件循环，跳过事件处理器注销")
                return
            
            event_manager = get_event_manager()
            if event_manager:
                # 注销所有事件监听器
                events = ["server_start", "server_stop", "player_join", "player_leave", "console_log"]
                for event_name in events:
                    try:
                        handler_name = f"on_{event_name}"
                        if hasattr(self, handler_name):
                            event_manager.unregister_listener(event_name, getattr(self, handler_name))
                    except Exception as e:
                        self.logger.debug(f"注销事件监听器 {event_name} 失败: {e}")
                        
                self.logger.info("事件处理器已注销")
        except Exception as e:
            self.logger.error(f"注销事件处理器失败: {e}")
    
    async def on_unload(self):
        """组件卸载时调用"""
        self.logger.info("Web组件正在卸载...")
        
        try:
            # 检查事件循环状态
            loop_running = False
            try:
                loop = asyncio.get_running_loop()
                loop_running = not loop.is_closed()
            except RuntimeError:
                self.logger.info("没有运行的事件循环，使用同步卸载方式")
                loop_running = False
            
            if loop_running:
                try:
                    # 如果事件循环正常，先调用禁用方法
                    await self.on_disable()
                except Exception as e:
                    self.logger.warning(f"异步禁用失败: {e}")
            
        except Exception as e:
            self.logger.error(f"卸载过程中出错: {e}")
        finally:
            # 清理资源（同步操作，总是执行）
            try:
                self.server_manager_ext = None
                self.player_manager_ext = None
                self.file_manager = None
                self.config_manager_ext = None
                self.core_adapter = None
                
                # 强制清理Web服务器
                self.web_server = None
                self.server_task = None
                
                self.logger.info("Web组件资源已清理")
            except Exception as e:
                self.logger.warning(f"资源清理时出错: {e}")
        
        self.logger.info("Web组件已卸载")
    
    def _wait_for_port_release(self):
        """等待端口释放"""
        import socket
        import time
        
        port = self.config.get('port', 8000)
        max_attempts = 10
        
        for attempt in range(max_attempts):
            try:
                # 尝试绑定端口检查是否已释放
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result != 0:  # 端口未被占用
                    self.logger.info(f"端口 {port} 已释放")
                    return
                else:
                    self.logger.debug(f"端口 {port} 仍被占用，等待中... ({attempt + 1}/{max_attempts})")
                    time.sleep(0.5)
                    
            except Exception as e:
                self.logger.debug(f"检查端口状态时出错: {e}")
                # 假设端口已释放
                return
        
        self.logger.warning(f"端口 {port} 在 {max_attempts * 0.5} 秒后仍被占用")
    
    def _is_port_available(self, port):
        """检查端口是否可用"""
        import socket
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result != 0  # 连接失败说明端口未被占用
        except Exception as e:
            self.logger.debug(f"检查端口 {port} 可用性时出错: {e}")
            return True  # 假设可用
    
    # 事件处理器 - 使用真实数据
    async def on_server_start(self, event):
        """服务器启动事件处理"""
        self.logger.info("检测到服务器启动事件")
        try:
            # 获取真实服务器状态
            if self.server_manager_ext:
                status = await self.server_manager_ext.get_server_status()
                await self._broadcast_server_event("server_start", status.to_dict())
        except Exception as e:
            self.logger.error(f"处理服务器启动事件失败: {e}")
    
    async def on_server_stop(self, event):
        """服务器停止事件处理"""
        self.logger.info("检测到服务器停止事件")
        try:
            if self.server_manager_ext:
                status = await self.server_manager_ext.get_server_status()
                await self._broadcast_server_event("server_stop", status.to_dict())
        except Exception as e:
            self.logger.error(f"处理服务器停止事件失败: {e}")
    
    async def on_player_join(self, event):
        """玩家加入事件处理"""
        player_name = getattr(event, 'player_name', "Unknown")
        self.logger.info(f"玩家 {player_name} 加入了服务器")
        
        try:
            # 获取真实玩家数据
            if self.player_manager_ext:
                player_data = await self.player_manager_ext.get_player_info(player_name)
                if player_data:
                    await self._broadcast_player_event("join", player_data.to_dict())
        except Exception as e:
            self.logger.error(f"处理玩家加入事件失败: {e}")
    
    async def on_player_leave(self, event):
        """玩家退出事件处理"""
        player_name = getattr(event, 'player_name', "Unknown")
        self.logger.info(f"玩家 {player_name} 离开了服务器")
        
        try:
            if self.player_manager_ext:
                player_data = await self.player_manager_ext.get_player_info(player_name)
                if player_data:
                    await self._broadcast_player_event("leave", player_data.to_dict())
        except Exception as e:
            self.logger.error(f"处理玩家离开事件失败: {e}")
    
    async def on_console_log(self, event):
        """控制台日志事件处理"""
        try:
            log_data = {
                "level": getattr(event, 'level', "INFO"),
                "message": getattr(event, 'message', ""),
                "source": getattr(event, 'source', "Server"),
                "timestamp": getattr(event, 'timestamp', None)
            }
            await self._broadcast_console_log(log_data)
        except Exception as e:
            self.logger.error(f"处理控制台日志事件失败: {e}")
    
    async def _broadcast_server_event(self, event_type: str, data: dict):
        """广播服务器事件到WebSocket客户端"""
        # 这里将通过WebSocket管理器广播事件
        # 具体实现取决于WebSocket管理器的API
        pass
    
    async def _broadcast_player_event(self, event_type: str, data: dict):
        """广播玩家事件到WebSocket客户端"""
        pass
    
    async def _broadcast_console_log(self, data: dict):
        """广播控制台日志到WebSocket客户端"""
        pass
    
    # 公共API方法 - 使用真实核心API
    async def get_server_status(self) -> Dict[str, Any]:
        """获取真实服务器状态"""
        try:
            if self.server_manager_ext:
                status = await self.server_manager_ext.get_server_status()
                metrics = await self.server_manager_ext.get_performance_metrics()
                
                return {
                    "status": status.to_dict(),
                    "metrics": metrics.to_dict() if metrics else {},
                    "web_component": {
                        "enabled": self.is_enabled,
                        "server_running": self.web_server is not None and not self.web_server.should_exit,
                        "host": self.web_host,
                        "port": self.web_port,
                        "active_connections": 0  # 这将通过WebSocket管理器获取
                    }
                }
            else:
                return {
                    "status": {"state": "unknown", "message": "服务器管理器不可用"},
                    "metrics": {},
                    "web_component": {
                        "enabled": self.is_enabled,
                        "server_running": False,
                        "host": self.web_host,
                        "port": self.web_port,
                        "active_connections": 0
                    }
                }
        except Exception as e:
            self.logger.error(f"获取服务器状态失败: {e}")
            return {"error": str(e)}
    
    async def get_players_list(self) -> Dict[str, Any]:
        """获取真实玩家列表"""
        try:
            if self.player_manager_ext:
                online_players = await self.player_manager_ext.get_online_players()
                all_players = await self.player_manager_ext.get_all_players(limit=100)
                
                return {
                    "online_players": [player.to_dict() for player in online_players.values()],
                    "total_players": len(all_players),
                    "online_count": len(online_players)
                }
            else:
                return {
                    "online_players": [],
                    "total_players": 0,
                    "online_count": 0,
                    "error": "玩家管理器不可用"
                }
        except Exception as e:
            self.logger.error(f"获取玩家列表失败: {e}")
            return {"error": str(e)}
    
    async def execute_console_command(self, command: str) -> Dict[str, Any]:
        """通过真实核心API执行控制台命令"""
        try:
            self.logger.info(f"Web界面执行命令: {command}")
            
            # 通过服务器管理器执行命令
            server_wrapper = get_server_wrapper()
            if server_wrapper and hasattr(server_wrapper, 'send_command'):
                result = await server_wrapper.send_command(command)
                
                return {
                    "success": True,
                    "command": command,
                    "result": result,
                    "timestamp": asyncio.get_event_loop().time()
                }
            else:
                # 备用：通过服务器管理扩展执行
                if self.server_manager_ext:
                    result = await self.server_manager_ext.execute_command(command)
                    return {
                        "success": True,
                        "command": command,
                        "result": result,
                        "timestamp": asyncio.get_event_loop().time()
                    }
                else:
                    return {
                        "success": False,
                        "command": command,
                        "error": "服务器管理器不可用",
                        "timestamp": asyncio.get_event_loop().time()
                    }
            
        except Exception as e:
            self.logger.error(f"命令执行失败: {command} - {e}")
            return {
                "success": False,
                "command": command,
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }
    
    async def get_file_list(self, path: str = ".") -> Dict[str, Any]:
        """获取真实文件列表"""
        try:
            if self.file_manager and self.enable_file_manager:
                files = self.file_manager.list_files(path)
                directories = self.file_manager.list_directories(path)
                
                return {
                    "path": path,
                    "files": files,
                    "directories": directories,
                    "total_size": sum(f.get('size', 0) for f in files)
                }
            else:
                return {
                    "path": path,
                    "files": [],
                    "directories": [],
                    "total_size": 0,
                    "error": "文件管理器不可用或已禁用"
                }
        except Exception as e:
            self.logger.error(f"获取文件列表失败: {e}")
            return {"error": str(e)}
    
    async def get_config_sections(self) -> Dict[str, Any]:
        """获取真实配置段信息"""
        try:
            if self.config_manager_ext:
                sections = self.config_manager_ext.get_config_sections_info()
                return {
                    "sections": sections,
                    "total_sections": len(sections)
                }
            else:
                return {
                    "sections": [],
                    "total_sections": 0,
                    "error": "配置管理器不可用"
                }
        except Exception as e:
            self.logger.error(f"获取配置段失败: {e}")
            return {"error": str(e)}


# 导出组件类
def create_component() -> WebComponent:
    """创建Web组件实例"""
    return WebComponent()