"""
Console API Endpoints
=====================

WebSocket and REST endpoints for server console functionality.
"""

import uuid
import asyncio
from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from ..core.client import CoreClient
from ..core.api import CoreAPI
from ..websocket.manager import WebSocketManager, ConnectionType, create_console_message
from ..models.api_models import ConsoleCommand, CommandResponse
from ..utils.logging import get_logger
from ..utils.exceptions import CoreConnectionError, CoreAPIError

logger = get_logger(__name__)

router = APIRouter()

# Dependencies
async def get_core_from_app(request) -> Any:
    """Dependency to get core from app state"""
    return request.app.state.core

async def get_websocket_manager_from_app(request) -> WebSocketManager:
    """Dependency to get WebSocket manager from app state"""
    return request.app.state.websocket_manager

async def get_core_api(request) -> CoreAPI:
    """Dependency to get core API"""
    core = request.app.state.core
    return CoreAPI(core)


@router.websocket("/console/ws")
async def console_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time console communication
    
    Handles:
    - Real-time server log streaming
    - Command execution from web interface
    - Bidirectional communication with the client
    """
    connection_id = str(uuid.uuid4())
    
    # Get dependencies from app state
    ws_manager = websocket.app.state.websocket_manager
    core = websocket.app.state.core
    core_api = CoreAPI(core)
    
    try:
        # Establish WebSocket connection
        await ws_manager.connect(
            websocket=websocket,
            connection_id=connection_id,
            connection_type=ConnectionType.CONSOLE,
            client_info={
                "user_agent": websocket.headers.get("user-agent"),
                "origin": websocket.headers.get("origin")
            }
        )
        
        # Register WebSocket manager with core client for command broadcasting
        if hasattr(core, 'add_websocket_manager'):
            core.add_websocket_manager(ws_manager)
            logger.info("Registered WebSocket manager with core client")
        
        logger.info("Console WebSocket connection established", connection_id=connection_id)
        
        # Start background task to send real-time server logs
        log_task = asyncio.create_task(send_realtime_logs(ws_manager, connection_id, core))
        
        # Start heartbeat task to keep connection alive
        heartbeat_task = asyncio.create_task(send_heartbeat(ws_manager, connection_id))
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_json()
                
                logger.debug("Received WebSocket message", connection_id=connection_id, data=data)
                
                message_type = data.get("type")
                
                if message_type == "command":
                    # Handle command execution
                    command = data.get("command", "").strip()
                    
                    if not command:
                        await ws_manager.send_to_connection(
                            connection_id,
                            create_console_message("ERROR", "Empty command received")
                        )
                        continue
                    
                    try:
                        # 发送命令开始执行的确认消息（调试信息）
                        await ws_manager.send_to_connection(
                            connection_id,
                            create_console_message("DEBUG", f"执行命令: {command}")
                        )
                        
                        # Execute command directly through core client with WebSocket manager
                        if hasattr(core, 'send_command'):
                            # 使用异步超时包装命令执行，防止连接断开
                            result = await asyncio.wait_for(
                                core.send_command(command, ws_manager),
                                timeout=30.0  # 30秒超时
                            )
                        else:
                            # Fallback to core API
                            result = await asyncio.wait_for(
                                core_api.send_console_command(command),
                                timeout=30.0
                            )
                        
                        # 命令执行完成后发送状态消息（调试信息）
                        await ws_manager.send_to_connection(
                            connection_id,
                            create_console_message("DEBUG", f"命令执行完成: {command}")
                        )
                        
                    except asyncio.TimeoutError:
                        await ws_manager.send_to_connection(
                            connection_id,
                            create_console_message("ERROR", f"命令执行超时: {command}")
                        )
                    except CoreAPIError as e:
                        await ws_manager.send_to_connection(
                            connection_id,
                            create_console_message("ERROR", f"Command failed: {e.message}")
                        )
                    except Exception as e:
                        logger.error("Error executing command", command=command, error=str(e), exc_info=True)
                        await ws_manager.send_to_connection(
                            connection_id,
                            create_console_message("ERROR", f"Internal error: {str(e)}")
                        )
                
                elif message_type == "ping":
                    # Handle ping/pong for connection keepalive
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": data.get("timestamp")
                    })
                
                else:
                    logger.warning("Unknown message type", message_type=message_type, connection_id=connection_id)
                    await ws_manager.send_to_connection(
                        connection_id,
                        create_console_message("WARN", f"Unknown message type: {message_type}")
                    )
        
        except WebSocketDisconnect:
            logger.info("Console WebSocket disconnected", connection_id=connection_id)
        
        finally:
            # Cancel background tasks
            log_task.cancel()
            heartbeat_task.cancel()
            try:
                await log_task
            except asyncio.CancelledError:
                pass
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
    
    except Exception as e:
        logger.error("Console WebSocket error", connection_id=connection_id, error=str(e), exc_info=True)
    
    finally:
        # Unregister WebSocket manager from core client
        if hasattr(core, 'remove_websocket_manager'):
            core.remove_websocket_manager(ws_manager)
            logger.info("Unregistered WebSocket manager from core client")
        
        # Clean up connection
        await ws_manager.disconnect(connection_id)
        logger.info("Console WebSocket cleanup completed", connection_id=connection_id)


async def send_heartbeat(ws_manager: WebSocketManager, connection_id: str):
    """
    发送心跳消息保持连接活跃
    
    Args:
        ws_manager: WebSocket管理器实例
        connection_id: 目标连接ID
    """
    try:
        while True:
            await asyncio.sleep(25)  # 每25秒发送一次心跳
            
            await ws_manager.send_to_connection(
                connection_id,
                {
                    "type": "heartbeat",
                    "level": "DEBUG",
                    "timestamp": int(asyncio.get_event_loop().time() * 1000),
                    "status": "connected"
                }
            )
            
    except asyncio.CancelledError:
        logger.debug("Heartbeat sender cancelled", connection_id=connection_id)
    except Exception as e:
        logger.error("Error in heartbeat sender", connection_id=connection_id, error=str(e))


async def send_realtime_logs(ws_manager: WebSocketManager, connection_id: str, core):
    """
    Send real-time server logs from Minecraft server
    
    Args:
        ws_manager: WebSocket manager instance
        connection_id: Target connection ID
        core: Core client instance
    """
    try:
        logger.info("Starting real-time log streaming", connection_id=connection_id)
        
        # 发送连接建立消息
        await ws_manager.send_to_connection(
            connection_id,
            create_console_message("INFO", "Console connection established")
        )
        
        # 如果核心客户端支持日志流，启用它
        if hasattr(core, 'start_log_streaming'):
            await core.start_log_streaming(ws_manager, connection_id)
        elif hasattr(core, 'get_recent_logs'):
            # 获取最近的日志作为初始内容
            try:
                recent_logs = await core.get_recent_logs(limit=20)
                for log_entry in recent_logs:
                    await ws_manager.send_to_connection(
                        connection_id,
                        {
                            "type": "server_log",
                            "timestamp": log_entry.get("timestamp", ""),
                            "data": {
                                "level": log_entry.get("level", "INFO"),
                                "source": log_entry.get("source", "Server"),
                                "message": log_entry.get("message", ""),
                                "thread": log_entry.get("thread", ""),
                                "raw": log_entry.get("raw", "")
                            }
                        }
                    )
                    await asyncio.sleep(0.1)  # 小延迟避免消息过快
            except Exception as e:
                logger.warning("Failed to get recent logs", error=str(e))
        
        # 保持连接活跃，等待日志推送
        while True:
            await asyncio.sleep(30)  # 每30秒检查一次连接状态
            
            # 发送状态信息
            await ws_manager.send_to_connection(
                connection_id,
                create_console_message("DEBUG", "Log streaming active")
            )
    
    except asyncio.CancelledError:
        logger.debug("Real-time log sender cancelled", connection_id=connection_id)
    except Exception as e:
        logger.error("Error in real-time log sender", connection_id=connection_id, error=str(e))


@router.post("/console/command", response_model=CommandResponse)
async def execute_console_command(
    command_data: ConsoleCommand,
    request: Request
):
    """
    Execute a console command via REST API
    
    Args:
        command_data: Command to execute
        
    Returns:
        Command execution result
    """
    try:
        logger.info("Executing console command via REST", command=command_data.command)
        
        # Get core API from app state
        core = request.app.state.core
        core_api = CoreAPI(core)
        result = await core_api.send_console_command(command_data.command)
        
        return CommandResponse(**result)
    
    except CoreConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Aetherius Core is not available"
        )
    
    except CoreAPIError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Command execution failed: {e.message}"
        )
    
    except Exception as e:
        logger.error("Unexpected error in command execution", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/console/status")
async def get_console_status(request: Request):
    """
    Get current console/server status
    
    Returns:
        Current server status and console connection info
    """
    try:
        # Get core API from app state
        core = request.app.state.core
        core_api = CoreAPI(core)
        
        # Get real server status
        status = await core_api.get_server_status()
        
        # Get WebSocket connection count
        ws_manager = request.app.state.websocket_manager
        console_connections = ws_manager.get_connection_count_by_type(ConnectionType.CONSOLE)
        
        return {
            "server_status": status,
            "console_connections": console_connections,
            "core_connected": await core.is_connected() if hasattr(core, 'is_connected') else True,
            "timestamp": status.get("timestamp", "")
        }
    
    except Exception as e:
        logger.error("Error getting console status", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get console status"
        )


@router.get("/console/history")
async def get_console_history(
    request: Request,
    limit: int = 100
):
    """
    Get recent console output history from actual server logs
    
    Args:
        limit: Maximum number of log entries to return
        
    Returns:
        List of recent console log entries
    """
    try:
        # Get core API from app state
        core = request.app.state.core
        core_api = CoreAPI(core)
        
        # Try to get real log history from core
        try:
            if hasattr(core, 'get_recent_logs'):
                logs = await core.get_recent_logs(limit=limit)
                formatted_history = []
                
                for log_entry in logs:
                    formatted_history.append({
                        "timestamp": log_entry.get("timestamp", ""),
                        "level": log_entry.get("level", "INFO"),
                        "source": log_entry.get("source", "Server"),
                        "message": log_entry.get("message", ""),
                        "thread": log_entry.get("thread", ""),
                        "raw": log_entry.get("raw", "")
                    })
                
                return {
                    "history": formatted_history,
                    "total": len(formatted_history),
                    "limit": limit,
                    "source": "real"
                }
            else:
                # 如果核心不支持日志历史，返回基础状态信息
                status = await core_api.get_server_status()
                basic_history = [
                    {
                        "timestamp": status.get("timestamp", ""),
                        "level": "INFO",
                        "source": "System",
                        "message": f"Server status: {'Running' if status.get('is_running', False) else 'Stopped'}"
                    },
                    {
                        "timestamp": status.get("timestamp", ""),
                        "level": "INFO", 
                        "source": "System",
                        "message": f"Players online: {status.get('player_count', 0)}/{status.get('max_players', 20)}"
                    },
                    {
                        "timestamp": status.get("timestamp", ""),
                        "level": "INFO",
                        "source": "System", 
                        "message": f"TPS: {status.get('tps', 0)}"
                    }
                ]
                
                return {
                    "history": basic_history,
                    "total": len(basic_history),
                    "limit": limit,
                    "source": "status"
                }
                
        except Exception as core_error:
            logger.warning("Failed to get logs from core", error=str(core_error))
            
            # 返回连接状态信息
            return {
                "history": [
                    {
                        "timestamp": "",
                        "level": "WARN",
                        "source": "Console",
                        "message": "Unable to retrieve server logs - core connection unavailable"
                    }
                ],
                "total": 1,
                "limit": limit,
                "source": "error"
            }
    
    except Exception as e:
        logger.error("Error retrieving console history", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve console history"
        )