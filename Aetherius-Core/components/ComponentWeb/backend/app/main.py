"""
FastAPI Application Entry Point
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from contextlib import asynccontextmanager
from typing import Optional, List
from pathlib import Path
import uvicorn

from .core.client import CoreClient
from .core.api import CoreAPI
from .websocket.manager import WebSocketManager
from .services.realtime_service import RealtimeService
from .api import console, dashboard, players, files, proxy
from .utils.logging import setup_logging


def create_app(cors_origins: Optional[List[str]] = None, component_instance=None) -> FastAPI:
    """
    创建FastAPI应用实例
    
    Args:
        cors_origins: CORS允许的源列表
        component_instance: Web组件实例（用于核心集成）
    """
    # 默认CORS源
    if cors_origins is None:
        cors_origins = [
            "http://localhost:3000", 
            "http://127.0.0.1:3000",
            "https://reimagined-cod-q74g9xxg6v5v395v5-3000.app.github.dev",
            "*"  # 允许所有源，适用于开发环境
        ]
    
    # 全局实例
    core_client = CoreClient()
    websocket_manager = WebSocketManager()
    realtime_service = None  # Will be initialized after core is ready
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan events"""
        # Startup
        setup_logging()
        
        # 如果有组件实例，使用组件的核心连接
        if component_instance:
            app.state.component = component_instance
            app.state.core = component_instance.core_adapter
        else:
            # 独立运行时初始化核心客户端
            await core_client.initialize()
            app.state.core = core_client
        
        # 存储WebSocket管理器到应用状态
        app.state.websocket_manager = websocket_manager
        # 将应用实例传递给WebSocket管理器，以便代理可以访问核心
        websocket_manager._app = app
        
        # 初始化实时服务
        core_api = CoreAPI(app.state.core)
        realtime_service = RealtimeService(websocket_manager, core_api)
        app.state.realtime_service = realtime_service
        
        # 启动实时服务
        await realtime_service.start()
        
        yield
        
        # Shutdown
        # 停止实时服务
        if realtime_service:
            await realtime_service.stop()
        
        if not component_instance:
            # 只有独立运行时才清理核心客户端
            await core_client.cleanup()
        await websocket_manager.cleanup()

    # Create FastAPI application
    app = FastAPI(
        title="Aetherius Component: Web API",
        description="Web interface backend for Aetherius server management",
        version="0.1.0",
        lifespan=lifespan
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    app.include_router(console.router, prefix="/api/v1", tags=["console"])
    app.include_router(dashboard.router, prefix="/api/v1", tags=["dashboard"])
    app.include_router(players.router, prefix="/api/v1", tags=["players"])
    app.include_router(files.router, prefix="/api/v1", tags=["files"])
    app.include_router(proxy.router, prefix="/api/v1", tags=["proxy"])

    # Static files and frontend routes
    @app.get("/", response_class=HTMLResponse)
    async def read_root():
        """Main dashboard page"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Aetherius Web Console</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; margin-bottom: 30px; }
                .nav { display: flex; gap: 20px; margin: 20px 0; }
                .nav a { padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }
                .nav a:hover { background: #0056b3; }
                .status { padding: 15px; background: #e8f5e8; border-left: 4px solid #28a745; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Aetherius Web Console</h1>
                    <p>Minecraft服务器管理界面</p>
                </div>
                
                <div class="status">
                    <strong>✅ 组件状态:</strong> Component-Web 已启动并运行
                </div>
                
                <div class="nav">
                    <a href="/console">📟 控制台</a>
                    <a href="/dashboard">📊 仪表板</a>
                    <a href="/players">👥 玩家管理</a>
                    <a href="/files">📁 文件管理</a>
                    <a href="/docs">📚 API文档</a>
                </div>
                
                <h3>🎯 主要功能</h3>
                <ul>
                    <li><strong>实时控制台</strong> - 执行服务器命令和查看日志</li>
                    <li><strong>服务器监控</strong> - CPU、内存、TPS等性能指标</li>
                    <li><strong>玩家管理</strong> - 在线玩家列表和管理操作</li>
                    <li><strong>文件管理</strong> - 浏览和编辑服务器文件</li>
                    <li><strong>配置管理</strong> - 修改服务器配置</li>
                </ul>
                
                <h3>📡 API端点</h3>
                <ul>
                    <li><code>GET /api/v1/console/status</code> - 服务器状态</li>
                    <li><code>POST /api/v1/console/command</code> - 执行命令</li>
                    <li><code>GET /api/v1/players</code> - 玩家列表</li>
                    <li><code>GET /api/v1/files/list</code> - 文件列表</li>
                    <li><code>GET /api/v1/files/content</code> - 文件内容</li>
                    <li><code>POST /api/v1/files/save</code> - 保存文件</li>
                    <li><code>POST /api/v1/files/upload</code> - 上传文件</li>
                    <li><code>GET /api/v1/files/download</code> - 下载文件</li>
                    <li><code>POST /api/v1/files/operation</code> - 文件操作</li>
                    <li><code>POST /api/v1/files/search</code> - 搜索文件</li>
                    <li><code>GET /health</code> - 健康检查</li>
                </ul>
            </div>
            
            <script>
                // 简单的状态检查
                fetch('/health')
                    .then(response => response.json())
                    .then(data => {
                        console.log('Health status:', data);
                    })
                    .catch(error => {
                        console.error('Health check failed:', error);
                    });
            </script>
        </body>
        </html>
        """

    @app.get("/console", response_class=HTMLResponse)
    async def console_page():
        """Console page"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>控制台 - Aetherius Web Console</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: 'Courier New', monospace; margin: 0; background: #1a1a1a; color: #00ff00; }
                .container { padding: 20px; max-width: 1200px; margin: 0 auto; }
                .header { margin-bottom: 20px; padding: 15px; background: #2a2a2a; border-radius: 4px; }
                .console { background: #000; padding: 20px; border-radius: 4px; min-height: 400px; overflow-y: auto; }
                .input-area { margin-top: 20px; display: flex; gap: 10px; }
                .input-area input { flex: 1; padding: 10px; background: #2a2a2a; border: 1px solid #555; color: #00ff00; font-family: inherit; }
                .input-area button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
                .input-area button:hover { background: #0056b3; }
                .nav { margin-bottom: 20px; }
                .nav a { color: #00aaff; text-decoration: none; margin-right: 20px; }
                .nav a:hover { text-decoration: underline; }
                .log-line { margin: 2px 0; }
                .server-status { display: flex; gap: 20px; margin-bottom: 15px; }
                .status-item { padding: 5px 10px; background: #2a2a2a; border-radius: 4px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="nav">
                    <a href="/">🏠 首页</a>
                    <a href="/console">📟 控制台</a>
                    <a href="/dashboard">📊 仪表板</a>
                    <a href="/players">👥 玩家</a>
                    <a href="/docs">📚 API</a>
                </div>
                
                <div class="header">
                    <h1>📟 Aetherius 控制台</h1>
                    <div class="server-status" id="status">
                        <div class="status-item">状态: <span id="server-status">检查中...</span></div>
                        <div class="status-item">玩家: <span id="player-count">-</span></div>
                        <div class="status-item">TPS: <span id="tps">-</span></div>
                    </div>
                </div>
                
                <div class="console" id="console">
                    <div class="log-line">[INFO] Aetherius Web Console 已连接</div>
                    <div class="log-line">[INFO] 使用下方输入框发送服务器命令</div>
                    <div class="log-line">[INFO] 支持的命令: help, list, stop, say &lt;message&gt;</div>
                </div>
                
                <div class="input-area">
                    <input type="text" id="command-input" placeholder="输入服务器命令..." onkeypress="handleKeyPress(event)">
                    <button onclick="sendCommand()">发送</button>
                    <button onclick="clearConsole()">清空</button>
                </div>
            </div>
            
            <script>
                let consoleElement = document.getElementById('console');
                
                function addLogLine(message, type = 'info') {
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
                    
                    addLogLine(`> ${command}`, 'command');
                    
                    fetch('/api/v1/console/command', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ command: command })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            addLogLine(`[SUCCESS] ${data.message || '命令执行成功'}`, 'success');
                        } else {
                            addLogLine(`[ERROR] ${data.message || '命令执行失败'}`, 'error');
                        }
                    })
                    .catch(error => {
                        addLogLine(`[ERROR] 网络错误: ${error.message}`, 'error');
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
                
                function updateStatus() {
                    fetch('/api/v1/console/status')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('server-status').textContent = data.is_running ? '运行中' : '已停止';
                            document.getElementById('player-count').textContent = data.player_count || 0;
                            document.getElementById('tps').textContent = data.tps || '20.0';
                        })
                        .catch(error => {
                            document.getElementById('server-status').textContent = '连接错误';
                        });
                }
                
                // 初始化和定期更新
                updateStatus();
                setInterval(updateStatus, 5000);
                
                addLogLine('[INFO] 控制台界面已准备就绪');
            </script>
        </body>
        </html>
        """

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard_page():
        """Dashboard page"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>仪表板 - Aetherius Web Console</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; background: #f5f5f5; }
                .container { padding: 20px; max-width: 1200px; margin: 0 auto; }
                .nav { margin-bottom: 20px; padding: 15px; background: white; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .nav a { color: #007bff; text-decoration: none; margin-right: 20px; }
                .nav a:hover { text-decoration: underline; }
                .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .card h3 { margin-top: 0; color: #333; }
                .metric { display: flex; justify-content: space-between; margin: 10px 0; }
                .metric-value { font-weight: bold; color: #007bff; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="nav">
                    <a href="/">🏠 首页</a>
                    <a href="/console">📟 控制台</a>
                    <a href="/dashboard">📊 仪表板</a>
                    <a href="/players">👥 玩家</a>
                    <a href="/docs">📚 API</a>
                </div>
                
                <h1>📊 服务器仪表板</h1>
                
                <div class="cards">
                    <div class="card">
                        <h3>🖥️ 服务器状态</h3>
                        <div class="metric">
                            <span>运行状态:</span>
                            <span class="metric-value" id="server-status">检查中...</span>
                        </div>
                        <div class="metric">
                            <span>运行时间:</span>
                            <span class="metric-value" id="uptime">-</span>
                        </div>
                        <div class="metric">
                            <span>版本:</span>
                            <span class="metric-value" id="version">-</span>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>👥 玩家信息</h3>
                        <div class="metric">
                            <span>在线玩家:</span>
                            <span class="metric-value" id="online-players">-</span>
                        </div>
                        <div class="metric">
                            <span>最大玩家:</span>
                            <span class="metric-value" id="max-players">-</span>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>⚡ 性能指标</h3>
                        <div class="metric">
                            <span>TPS:</span>
                            <span class="metric-value" id="tps">-</span>
                        </div>
                        <div class="metric">
                            <span>CPU使用率:</span>
                            <span class="metric-value" id="cpu-usage">-</span>
                        </div>
                        <div class="metric">
                            <span>内存使用:</span>
                            <span class="metric-value" id="memory-usage">-</span>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>🌐 Web组件</h3>
                        <div class="metric">
                            <span>Web服务器:</span>
                            <span class="metric-value">运行中</span>
                        </div>
                        <div class="metric">
                            <span>端口:</span>
                            <span class="metric-value">8000</span>
                        </div>
                        <div class="metric">
                            <span>API版本:</span>
                            <span class="metric-value">v1</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                function updateDashboard() {
                    fetch('/api/v1/console/status')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('server-status').textContent = data.is_running ? '运行中' : '已停止';
                            document.getElementById('uptime').textContent = `${Math.floor(data.uptime / 3600)}小时`;
                            document.getElementById('version').textContent = data.version || 'Unknown';
                            document.getElementById('online-players').textContent = data.player_count || 0;
                            document.getElementById('max-players').textContent = data.max_players || 20;
                            document.getElementById('tps').textContent = data.tps || '20.0';
                            document.getElementById('cpu-usage').textContent = `${data.cpu_usage || 0}%`;
                            
                            const memory = data.memory_usage || {};
                            document.getElementById('memory-usage').textContent = `${memory.used || 0}MB / ${memory.max || 4096}MB`;
                        })
                        .catch(error => {
                            console.error('Failed to update dashboard:', error);
                        });
                }
                
                // 初始化和定期更新
                updateDashboard();
                setInterval(updateDashboard, 5000);
            </script>
        </body>
        </html>
        """

    @app.get("/players", response_class=HTMLResponse)
    async def players_page():
        """Players management page"""
        return r"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>玩家管理 - Aetherius Web Console</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; background: #f5f5f5; }
                .container { padding: 20px; max-width: 1200px; margin: 0 auto; }
                .nav { margin-bottom: 20px; padding: 15px; background: white; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .nav a { color: #007bff; text-decoration: none; margin-right: 20px; }
                .nav a:hover { text-decoration: underline; }
                .players-list { background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }
                .player-item { padding: 15px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
                .player-item:last-child { border-bottom: none; }
                .player-info { display: flex; align-items: center; gap: 15px; }
                .player-avatar { width: 32px; height: 32px; background: #ddd; border-radius: 4px; }
                .status-online { color: #28a745; }
                .status-offline { color: #6c757d; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="nav">
                    <a href="/">🏠 首页</a>
                    <a href="/console">📟 控制台</a>
                    <a href="/dashboard">📊 仪表板</a>
                    <a href="/players">👥 玩家</a>
                    <a href="/docs">📚 API</a>
                </div>
                
                <h1>👥 玩家管理</h1>
                
                <div class="players-list" id="players-list">
                    <div class="player-item">
                        <div class="player-info">
                            <div class="player-avatar"></div>
                            <div>
                                <div><strong>加载中...</strong></div>
                                <div class="status-offline">正在获取玩家列表</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                function updatePlayersList() {
                    fetch('/api/v1/players')
                        .then(response => response.json())
                        .then(data => {
                            const container = document.getElementById('players-list');
                            container.innerHTML = '';
                            
                            if (data.online_players && data.online_players.length > 0) {
                                data.online_players.forEach(player => {
                                    const item = document.createElement('div');
                                    item.className = 'player-item';
                                    item.innerHTML = `
                                        <div class="player-info">
                                            <div class="player-avatar"></div>
                                            <div>
                                                <div><strong>\${player.name || 'Unknown'}</strong></div>
                                                <div class="status-online">在线</div>
                                            </div>
                                        </div>
                                        <div>
                                            <span>等级: \${player.level || 0}</span>
                                        </div>
                                    `;
                                    container.appendChild(item);
                                });
                            } else {
                                container.innerHTML = `
                                    <div class="player-item">
                                        <div class="player-info">
                                            <div>当前没有在线玩家</div>
                                        </div>
                                    </div>
                                `;
                            }
                        })
                        .catch(error => {
                            console.error('Failed to load players:', error);
                            document.getElementById('players-list').innerHTML = `
                                <div class="player-item">
                                    <div class="player-info">
                                        <div style="color: red;">加载玩家列表失败</div>
                                    </div>
                                </div>
                            `;
                        });
                }
                
                // 初始化和定期更新
                updatePlayersList();
                setInterval(updatePlayersList, 10000);
            </script>
        </body>
        </html>
        """

    @app.get("/debug-frontend", response_class=HTMLResponse)
    async def debug_frontend_page():
        """Frontend WebSocket debug page"""
        with open("/workspaces/aetheriusmc.github.io/Aetherius-Core/debug_frontend.html", "r") as f:
            return HTMLResponse(f.read())

    @app.get("/debug-vue-connection", response_class=HTMLResponse)
    async def debug_vue_connection():
        """Debug Vue frontend connection status"""
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head><title>Vue前端连接诊断</title><meta charset="utf-8"></head>
        <body style="font-family: monospace; background: #1a1a1a; color: #00ff00; padding: 20px;">
            <h1>🔧 Vue前端连接状态诊断</h1>
            <div style="margin: 20px 0;">
                <button onclick="checkVueAppStatus()" style="padding: 8px 16px; background: #007bff; color: white; border: none;">检查Vue应用状态</button>
                <button onclick="testDirectConnection()" style="padding: 8px 16px; background: #28a745; color: white; border: none; margin-left: 10px;">测试直接连接</button>
            </div>
            <div id="status" style="background: #2a2a2a; padding: 15px; border-radius: 4px; margin: 10px 0;"></div>
            <div id="log" style="border: 1px solid #333; height: 400px; overflow-y: auto; padding: 10px; background: #000;"></div>
            
            <script>
                const statusDiv = document.getElementById('status');
                const logDiv = document.getElementById('log');
                
                function log(message, type = 'info') {
                    const timestamp = new Date().toLocaleTimeString();
                    const div = document.createElement('div');
                    div.style.color = type === 'error' ? '#ff6b6b' : 
                                     type === 'success' ? '#51cf66' : 
                                     type === 'warning' ? '#ffd43b' : '#00ff00';
                    div.textContent = `[${timestamp}] ${message}`;
                    logDiv.appendChild(div);
                    logDiv.scrollTop = logDiv.scrollHeight;
                }
                
                function updateStatus(message, type = 'info') {
                    statusDiv.innerHTML = `<span style="color: ${type === 'error' ? '#ff6b6b' : type === 'success' ? '#51cf66' : '#ffd43b'}">${message}</span>`;
                }
                
                async function checkVueAppStatus() {
                    log('检查Vue应用状态...', 'info');
                    updateStatus('正在检查Vue应用...', 'warning');
                    
                    try {
                        // 检查Vue前端是否可访问
                        const vueResponse = await fetch('http://localhost:3000');
                        if (vueResponse.ok) {
                            log('✅ Vue前端服务正常运行', 'success');
                            
                            // 尝试检查Vue应用的WebSocket连接信息
                            // 我们可以通过访问Vue应用来检查其连接状态
                            try {
                                // 检查是否有全局的Vue应用状态可以访问
                                const testFrame = document.createElement('iframe');
                                testFrame.src = 'http://localhost:3000';
                                testFrame.style.display = 'none';
                                document.body.appendChild(testFrame);
                                
                                log('📱 正在检查Vue应用的WebSocket状态...', 'info');
                                
                                setTimeout(() => {
                                    document.body.removeChild(testFrame);
                                    log('ℹ️ Vue应用检查完成，请检查浏览器控制台获取详细信息', 'info');
                                }, 3000);
                                
                            } catch (e) {
                                log(`⚠️ 无法直接访问Vue应用状态: ${e.message}`, 'warning');
                            }
                            
                            updateStatus('Vue应用正常，建议检查浏览器控制台', 'success');
                        } else {
                            log('❌ Vue前端服务异常', 'error');
                            updateStatus('Vue前端服务异常', 'error');
                        }
                    } catch (error) {
                        log(`❌ Vue前端连接失败: ${error.message}`, 'error');
                        updateStatus('Vue前端连接失败', 'error');
                    }
                }
                
                async function testDirectConnection() {
                    log('测试直接WebSocket连接...', 'info');
                    updateStatus('正在测试WebSocket连接...', 'warning');
                    
                    const wsUrl = 'ws://localhost:8080/api/v1/ws-proxy/console/ws';
                    log(`连接到: ${wsUrl}`, 'info');
                    
                    try {
                        const ws = new WebSocket(wsUrl);
                        
                        ws.onopen = () => {
                            log('✅ WebSocket连接成功', 'success');
                            updateStatus('WebSocket连接正常', 'success');
                            
                            // 发送测试命令
                            const testCmd = {
                                type: 'command',
                                command: 'test',
                                timestamp: new Date().toISOString()
                            };
                            ws.send(JSON.stringify(testCmd));
                            log('📤 发送测试命令', 'info');
                        };
                        
                        ws.onmessage = (event) => {
                            try {
                                const data = JSON.parse(event.data);
                                log(`📥 收到消息: ${data.type}`, 'success');
                            } catch (e) {
                                log(`📥 收到原始消息: ${event.data}`, 'info');
                            }
                        };
                        
                        ws.onclose = (event) => {
                            log(`🔌 连接关闭: code=${event.code}`, 'warning');
                        };
                        
                        ws.onerror = (error) => {
                            log(`❌ WebSocket错误: ${error}`, 'error');
                            updateStatus('WebSocket连接失败', 'error');
                        };
                        
                        // 5秒后关闭连接
                        setTimeout(() => {
                            if (ws.readyState === WebSocket.OPEN) {
                                ws.close();
                                log('🔌 测试完成，关闭连接', 'info');
                            }
                        }, 5000);
                        
                    } catch (error) {
                        log(`❌ WebSocket连接失败: ${error.message}`, 'error');
                        updateStatus('WebSocket连接失败', 'error');
                    }
                }
                
                // 页面加载时自动检查
                log('诊断工具已准备就绪', 'success');
                updateStatus('等待检查命令...', 'warning');
            </script>
        </body>
        </html>
        """)

    @app.get("/files", response_class=HTMLResponse)
    async def files_page():
        """File management page"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>文件管理 - Aetherius Web Console</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; background: #f5f5f5; }
                .container { padding: 20px; max-width: 1200px; margin: 0 auto; }
                .nav { margin-bottom: 20px; padding: 15px; background: white; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .nav a { color: #007bff; text-decoration: none; margin-right: 20px; }
                .nav a:hover { text-decoration: underline; }
                .file-browser { background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 20px; }
                .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }
                .feature-card { padding: 20px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #28a745; }
                .feature-card h3 { margin-top: 0; color: #1e7e34; }
                .demo-section { margin: 30px 0; padding: 20px; background: #e8f5e8; border-radius: 8px; }
                .api-link { display: inline-block; margin: 10px 10px 10px 0; padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; font-size: 14px; }
                .api-link:hover { background: #0056b3; text-decoration: none; color: white; }
                .status-indicator { display: inline-block; width: 12px; height: 12px; background: #28a745; border-radius: 50%; margin-right: 8px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="nav">
                    <a href="/">🏠 首页</a>
                    <a href="/console">📟 控制台</a>
                    <a href="/dashboard">📊 仪表板</a>
                    <a href="/players">👥 玩家</a>
                    <a href="/docs">📚 API</a>
                </div>
                
                <h1>📁 文件管理</h1>
                
                <div class="file-browser">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h2><span class="status-indicator"></span>文件管理功能已完成并可用！</h2>
                        <p style="color: #666; font-size: 16px;">通过API或前端界面管理服务器文件</p>
                    </div>
                    
                    <div class="feature-grid">
                        <div class="feature-card">
                            <h3>📂 文件浏览</h3>
                            <p>• 浏览服务器文件和目录结构</p>
                            <p>• 支持列表和网格两种视图模式</p>
                            <p>• 显示文件大小、修改时间和权限</p>
                            <p>• 面包屑导航和快速搜索</p>
                        </div>
                        
                        <div class="feature-card">
                            <h3>✏️ 文件编辑</h3>
                            <p>• Monaco编辑器支持语法高亮</p>
                            <p>• 支持多种文件格式和编码</p>
                            <p>• 自动检测文件类型</p>
                            <p>• 实时保存和备份功能</p>
                        </div>
                        
                        <div class="feature-card">
                            <h3>📤 文件操作</h3>
                            <p>• 上传单个或多个文件</p>
                            <p>• 下载文件到本地</p>
                            <p>• 创建新文件和文件夹</p>
                            <p>• 重命名、复制、移动、删除</p>
                        </div>
                        
                        <div class="feature-card">
                            <h3>🔍 高级功能</h3>
                            <p>• 全局文件搜索</p>
                            <p>• 批量文件操作</p>
                            <p>• 文件权限管理</p>
                            <p>• 安全路径限制</p>
                        </div>
                    </div>
                    
                    <div class="demo-section">
                        <h3>📡 API 端点</h3>
                        <p>完整的RESTful API支持程序化文件操作：</p>
                        <a href="/api/v1/files/list?path=." class="api-link">GET /api/v1/files/list</a>
                        <a href="/docs#operations-files-get_file_content_files_content_get" class="api-link">GET /api/v1/files/content</a>
                        <a href="/docs#operations-files-save_file_content_files_save_post" class="api-link">POST /api/v1/files/save</a>
                        <a href="/docs#operations-files-upload_file_files_upload_post" class="api-link">POST /api/v1/files/upload</a>
                        <a href="/docs#operations-files-download_file_files_download_get" class="api-link">GET /api/v1/files/download</a>
                        <a href="/docs#operations-files-file_operation_files_operation_post" class="api-link">POST /api/v1/files/operation</a>
                        <a href="/docs#operations-files-search_files_files_search_post" class="api-link">POST /api/v1/files/search</a>
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                        <p style="color: #666;">
                            访问 <a href="http://localhost:3000/files" target="_blank" style="color: #007bff;">Vue.js前端界面</a> 
                            获得完整的文件管理体验，或查看 
                            <a href="/docs" style="color: #007bff;">API文档</a> 
                            了解集成详情。
                        </p>
                    </div>
                </div>
            </div>
            
            <script>
                // 测试API连接
                fetch('/api/v1/files/list?path=.')
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            console.log('文件管理API测试成功:', data);
                        }
                    })
                    .catch(error => {
                        console.error('文件管理API测试失败:', error);
                    });
            </script>
        </body>
        </html>
        """

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        # 获取核心客户端状态
        core_connected = False
        websocket_connections = 0
        
        try:
            if component_instance:
                # 组件模式：检查组件状态
                core_connected = component_instance.is_enabled
                websocket_connections = 0  # 暂时返回0
            else:
                # 独立模式：检查核心客户端
                if hasattr(app.state, 'core'):
                    core_connected = await app.state.core.is_connected()
                if hasattr(app.state, 'websocket_manager'):
                    websocket_connections = app.state.websocket_manager.get_connection_count()
        except:
            pass
        
        return {
            "status": "healthy",
            "core_connected": core_connected,
            "websocket_connections": websocket_connections
        }
    
    return app


# 为向后兼容性创建默认应用实例
app = create_app()


# Development server
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,  # 使用8080端口保持与前端配置一致
        reload=True,  # 保持自动重启功能
        reload_excludes=["*.log", "*.tmp", "__pycache__/*", "*.pyc"],  # 排除临时文件
        log_level="info"
    )