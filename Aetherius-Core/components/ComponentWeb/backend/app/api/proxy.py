"""
WebSocket Proxy Router
======================

提供WebSocket代理功能，解决GitHub Codespaces等环境的端口映射问题
"""

import asyncio
import json
from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse

from ..utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.websocket("/ws-proxy/{target_path:path}")
async def websocket_proxy(websocket: WebSocket, target_path: str):
    """
    WebSocket代理端点
    
    将WebSocket连接代理到目标路径，解决端口映射问题
    """
    connection_id = f"proxy-{id(websocket)}"
    
    try:
        await websocket.accept()
        logger.info(f"WebSocket代理连接已建立: {target_path}", extra={"connection_id": connection_id})
        
        # 获取WebSocket管理器
        ws_manager = websocket.app.state.websocket_manager
        
        # 根据目标路径确定连接类型
        if target_path.startswith("console"):
            from ..websocket.manager import ConnectionType
            connection_type = ConnectionType.CONSOLE
        elif target_path.startswith("dashboard"):
            from ..websocket.manager import ConnectionType
            connection_type = ConnectionType.DASHBOARD
        else:
            connection_type = None
        
        if connection_type:
            # 直接注册连接到WebSocket管理器，不重复接受
            await ws_manager._ensure_initialized()
            
            from ..websocket.manager import WSConnection
            from datetime import datetime
            
            async with ws_manager._lock:
                connection = WSConnection(
                    websocket=websocket,
                    connection_id=connection_id,
                    connection_type=connection_type,
                    connected_at=datetime.now(),
                    client_info={
                        "user_agent": websocket.headers.get("user-agent"),
                        "origin": websocket.headers.get("origin"),
                        "proxied": True,
                        "target_path": target_path
                    }
                )
                
                ws_manager.connections[connection_id] = connection
                ws_manager.connections_by_type[connection_type].add(connection_id)
            
            # 发送欢迎消息
            await websocket.send_json({
                "type": "connection_established",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "connection_id": connection_id,
                    "connection_type": connection_type.value,
                    "server_time": datetime.now().isoformat()
                }
            })
            
            # Register for real-time logs if this is a console connection
            if connection_type == ConnectionType.CONSOLE:
                try:
                    # Get core instance and register WebSocket manager for real-time logs
                    core = None
                    if hasattr(websocket, 'app') and websocket.app:
                        core = getattr(websocket.app.state, 'core', None)
                    
                    if core and hasattr(core, '_core') and hasattr(core._core, 'register_websocket_manager'):
                        core._core.register_websocket_manager(ws_manager)
                        logger.info("Registered WebSocket manager for real-time server logs")
                except Exception as e:
                    logger.warning(f"Failed to register for real-time logs: {e}")
            
            try:
                while True:
                    # 接收来自客户端的消息
                    data = await websocket.receive_json()
                    logger.debug(f"代理收到消息: {data}", extra={"connection_id": connection_id})
                    
                    # 处理消息（这里可以添加消息转换逻辑）
                    from ..websocket.manager import ConnectionType
                    if connection_type == ConnectionType.CONSOLE:
                        await handle_console_message(ws_manager, connection_id, data, websocket)
                    elif connection_type == ConnectionType.DASHBOARD:
                        await handle_dashboard_message(ws_manager, connection_id, data, websocket)
                        
            except WebSocketDisconnect:
                logger.info(f"WebSocket代理连接已断开: {target_path}", extra={"connection_id": connection_id})
        else:
            # 处理未知类型的连接
            await websocket.send_json({
                "type": "error",
                "message": f"不支持的代理路径: {target_path}"
            })
            await websocket.close(code=1000)
            
    except Exception as e:
        logger.error(f"WebSocket代理错误: {e}", extra={"connection_id": connection_id}, exc_info=True)
        try:
            await websocket.close(code=1011)
        except:
            pass
    finally:
        # 清理连接
        try:
            ws_manager = websocket.app.state.websocket_manager
            await ws_manager.disconnect(connection_id)
            
            # Unregister from real-time logs if this was a console connection
            if 'connection_type' in locals() and connection_type == ConnectionType.CONSOLE:
                try:
                    core = None
                    if hasattr(websocket, 'app') and websocket.app:
                        core = getattr(websocket.app.state, 'core', None)
                    
                    if core and hasattr(core, '_core') and hasattr(core._core, 'unregister_websocket_manager'):
                        core._core.unregister_websocket_manager(ws_manager)
                        logger.info("Unregistered WebSocket manager from real-time server logs")
                except Exception as e:
                    logger.warning(f"Failed to unregister from real-time logs: {e}")
        except:
            pass


async def handle_console_message(ws_manager, connection_id: str, data: Dict[str, Any], websocket=None):
    """处理控制台消息"""
    from ..websocket.manager import WSMessage
    from datetime import datetime
    
    message_type = data.get("type")
    
    if message_type == "command":
        # 处理命令
        from ..core.api import CoreAPI
        
        # 尝试获取核心实例
        core = None
        try:
            # 从WebSocket应用状态获取核心实例
            if hasattr(websocket, 'app') and websocket.app:
                core = getattr(websocket.app.state, 'core', None)
                logger.debug(f"Found core from websocket.app.state: {core}")
            elif hasattr(ws_manager, '_app') and ws_manager._app:
                core = getattr(ws_manager._app.state, 'core', None)
                logger.debug(f"Found core from ws_manager._app.state: {core}")
        except Exception as e:
            logger.warning(f"Error getting core instance: {e}")
        
        if core:
            logger.info(f"Found core instance: {type(core).__name__}")
            core_api = CoreAPI(core)
            command = data.get("command", "").strip()
            
            if command:
                try:
                    result = await core_api.send_console_command(command, ws_manager)
                    
                    # 发送命令回显
                    await ws_manager.send_to_connection(
                        connection_id,
                        WSMessage(
                            type="console_log",
                            timestamp=datetime.now(),
                            data={
                                "level": "COMMAND",
                                "source": "Client",
                                "message": f"> {command}"
                            }
                        )
                    )
                    
                    # 发送命令结果
                    level = "INFO" if result.get("success") else "ERROR"
                    await ws_manager.send_to_connection(
                        connection_id,
                        WSMessage(
                            type="console_log",
                            timestamp=datetime.now(),
                            data={
                                "level": level,
                                "source": "Server",
                                "message": result.get("message", "")
                            }
                        )
                    )
                    
                except Exception as e:
                    await ws_manager.send_to_connection(
                        connection_id,
                        WSMessage(
                            type="console_log",
                            timestamp=datetime.now(),
                            data={
                                "level": "ERROR",
                                "source": "Proxy",
                                "message": f"命令执行失败: {str(e)}"
                            }
                        )
                    )
        else:
            # 模拟响应（当核心不可用时）
            logger.warning(f"No core instance found - using mock response. websocket app: {hasattr(websocket, 'app') if websocket else 'No websocket'}")
            await ws_manager.send_to_connection(
                connection_id,
                WSMessage(
                    type="console_log",
                    timestamp=datetime.now(),
                    data={
                        "level": "WARN",
                        "source": "Proxy",
                        "message": "核心服务不可用，这是模拟响应"
                    }
                )
            )
    
    elif message_type == "ping":
        # 处理ping
        await ws_manager.send_to_connection(
            connection_id,
            WSMessage(
                type="pong",
                timestamp=datetime.now(),
                data={}
            )
        )


async def handle_dashboard_message(ws_manager, connection_id: str, data: Dict[str, Any], websocket=None):
    """处理仪表板消息"""
    from ..websocket.manager import WSMessage
    from datetime import datetime
    
    message_type = data.get("type")
    
    if message_type == "get_status":
        # 返回模拟状态数据
        await ws_manager.send_to_connection(
            connection_id,
            WSMessage(
                type="dashboard_summary",
                timestamp=datetime.now(),
                data={
                    "server_status": {
                        "is_running": False,
                        "uptime": 0,
                        "version": "1.20.1",
                        "player_count": 0,
                        "max_players": 20,
                        "tps": 20.0,
                        "cpu_usage": 0.0,
                        "memory_usage": {
                            "used": 0,
                            "max": 2048,
                            "percentage": 0.0
                        }
                    },
                    "online_players": [],
                    "recent_logs": []
                }
            )
        )
    
    elif message_type == "ping":
        # 处理ping
        await ws_manager.send_to_connection(
            connection_id,
            WSMessage(
                type="pong",
                timestamp=datetime.now(),
                data={}
            )
        )


@router.get("/ws-test")
async def websocket_test():
    """WebSocket测试页面"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket代理测试</title>
        <meta charset="utf-8">
    </head>
    <body>
        <h1>WebSocket代理测试</h1>
        <div id="status">正在连接...</div>
        <div id="messages" style="border: 1px solid #ccc; height: 300px; overflow-y: scroll; padding: 10px; margin: 10px 0;"></div>
        <input type="text" id="messageInput" placeholder="输入消息..." style="width: 70%;">
        <button onclick="sendMessage()">发送</button>
        
        <script>
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/api/v1/ws-proxy/console/ws`;
            console.log('连接到:', wsUrl);
            
            const ws = new WebSocket(wsUrl);
            const statusDiv = document.getElementById('status');
            const messagesDiv = document.getElementById('messages');
            
            ws.onopen = function() {
                statusDiv.textContent = '已连接';
                addMessage('系统', '连接已建立');
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                addMessage('服务器', JSON.stringify(data, null, 2));
            };
            
            ws.onclose = function() {
                statusDiv.textContent = '连接已关闭';
                addMessage('系统', '连接已关闭');
            };
            
            ws.onerror = function(error) {
                statusDiv.textContent = '连接错误';
                addMessage('错误', error.toString());
            };
            
            function addMessage(sender, message) {
                const div = document.createElement('div');
                div.innerHTML = `<strong>${sender}:</strong> <pre>${message}</pre>`;
                messagesDiv.appendChild(div);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
            
            function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                if (message) {
                    const data = {
                        type: 'command',
                        command: message,
                        timestamp: new Date().toISOString()
                    };
                    ws.send(JSON.stringify(data));
                    addMessage('客户端', JSON.stringify(data, null, 2));
                    input.value = '';
                }
            }
            
            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        </script>
    </body>
    </html>
    """)