"""
Console management API endpoints.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from ...core.container import get_container
from ...core.aetherius_adapter import IAetheriusAdapter
from ...utils.security import get_current_user, require_permission
from ...websocket.manager import WebSocketManager
from ...websocket.models import (
    create_console_log_message, create_ws_message, WSMessageType, ConnectionType
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class ConsoleCommandRequest(BaseModel):
    """Console command request model."""
    command: str = Field(..., description="Command to execute")
    source: str = Field("web", description="Command source")


class ConsoleCommandResponse(BaseModel):
    """Console command response model."""
    success: bool = Field(..., description="Command execution success")
    command: str = Field(..., description="Executed command")
    output: Optional[str] = Field(None, description="Command output")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: str = Field(..., description="Execution timestamp")


class ConsoleLogEntry(BaseModel):
    """Console log entry model."""
    id: Optional[int] = Field(None, description="Log entry ID")
    timestamp: str = Field(..., description="Log timestamp")
    level: str = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    source: str = Field(..., description="Log source")


class ConsoleLogResponse(BaseModel):
    """Console log response model."""
    logs: List[ConsoleLogEntry] = Field(..., description="Log entries")
    total_count: int = Field(..., description="Total log entries")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")


class ConsoleStatusResponse(BaseModel):
    """Console status response model."""
    connected: bool = Field(..., description="Console connection status")
    last_activity: Optional[str] = Field(None, description="Last activity timestamp")
    command_history_count: int = Field(..., description="Number of commands in history")
    active_connections: int = Field(..., description="Number of active WebSocket connections")


class CommandHistoryEntry(BaseModel):
    """Command history entry model."""
    id: int = Field(..., description="Command ID")
    command: str = Field(..., description="Executed command")
    user: str = Field(..., description="User who executed the command")
    timestamp: str = Field(..., description="Execution timestamp")
    success: bool = Field(..., description="Command success status")
    output: Optional[str] = Field(None, description="Command output")


class CommandHistoryResponse(BaseModel):
    """Command history response model."""
    commands: List[CommandHistoryEntry] = Field(..., description="Command history")
    total_count: int = Field(..., description="Total commands")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")


# Dependency to get Aetherius adapter
async def get_aetherius_adapter() -> IAetheriusAdapter:
    """Get Aetherius adapter instance."""
    container = get_container()
    return await container.get_service(IAetheriusAdapter)


# Dependency to get WebSocket manager
async def get_websocket_manager() -> WebSocketManager:
    """Get WebSocket manager instance."""
    container = get_container()
    return await container.get_service(WebSocketManager)


@router.post("/command", response_model=ConsoleCommandResponse)
async def execute_command(
    request: ConsoleCommandRequest,
    background_tasks: BackgroundTasks,
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    ws_manager: WebSocketManager = Depends(get_websocket_manager),
    current_user: Dict[str, Any] = Depends(require_permission("console.execute"))
):
    """
    执行控制台命令。
    
    需要 'console.execute' 权限。命令结果会通过 WebSocket 实时广播。
    """
    try:
        # Log command execution attempt
        logger.info(f"User {current_user['username']} executing command: {request.command}")
        
        # Execute command through Aetherius adapter
        result = await adapter.send_command(request.command)
        
        # Create command log message for WebSocket
        command_log = create_console_log_message(
            level="INFO",
            message=f"[{current_user['username']}] > {request.command}",
            source="console"
        )
        
        # Broadcast command to console connections
        background_tasks.add_task(
            ws_manager.broadcast_to_type, 
            ConnectionType.CONSOLE, 
            command_log
        )
        
        # If command has output, broadcast it too
        if result.get("output"):
            output_log = create_console_log_message(
                level="INFO",
                message=result["output"],
                source="server"
            )
            background_tasks.add_task(
                ws_manager.broadcast_to_type,
                ConnectionType.CONSOLE,
                output_log
            )
        
        # If command failed, broadcast error
        if not result.get("success") and result.get("error"):
            error_log = create_console_log_message(
                level="ERROR",
                message=f"Command failed: {result['error']}",
                source="server"
            )
            background_tasks.add_task(
                ws_manager.broadcast_to_type,
                ConnectionType.CONSOLE,
                error_log
            )
        
        # TODO: Store command in history database
        
        return ConsoleCommandResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to execute command '{request.command}': {e}")
        raise HTTPException(status_code=500, detail=f"命令执行失败: {str(e)}")


@router.get("/logs", response_model=ConsoleLogResponse)
async def get_console_logs(
    page: int = 1,
    page_size: int = 100,
    level: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取控制台日志。
    
    支持分页、按级别筛选、按来源筛选和关键字搜索。
    """
    try:
        # TODO: Implement database log retrieval
        # For now, return empty response
        
        mock_logs = []
        
        # Generate some mock log entries for demonstration
        if not level and not source and not search:
            mock_logs = [
                ConsoleLogEntry(
                    id=1,
                    timestamp=datetime.now().isoformat(),
                    level="INFO",
                    message="Server started successfully",
                    source="server"
                ),
                ConsoleLogEntry(
                    id=2,
                    timestamp=datetime.now().isoformat(),
                    level="INFO", 
                    message="Player Steve joined the game",
                    source="server"
                ),
                ConsoleLogEntry(
                    id=3,
                    timestamp=datetime.now().isoformat(),
                    level="WARN",
                    message="Server overloaded! Can't keep up!",
                    source="server"
                )
            ]
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_logs = mock_logs[start_idx:end_idx]
        
        return ConsoleLogResponse(
            logs=paginated_logs,
            total_count=len(mock_logs),
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Failed to get console logs: {e}")
        raise HTTPException(status_code=500, detail=f"获取控制台日志失败: {str(e)}")


@router.get("/status", response_model=ConsoleStatusResponse)
async def get_console_status(
    ws_manager: WebSocketManager = Depends(get_websocket_manager),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取控制台状态。
    
    返回控制台连接状态、活动连接数等信息。
    """
    try:
        # Get WebSocket statistics
        ws_stats = ws_manager.get_connection_stats()
        
        # Get console-specific connection count
        console_connections = ws_stats.get("connections_by_type", {}).get("console", 0)
        
        return ConsoleStatusResponse(
            connected=True,  # Assuming always connected if API is working
            last_activity=datetime.now().isoformat(),
            command_history_count=0,  # TODO: Get from database
            active_connections=console_connections
        )
        
    except Exception as e:
        logger.error(f"Failed to get console status: {e}")
        raise HTTPException(status_code=500, detail=f"获取控制台状态失败: {str(e)}")


@router.get("/history", response_model=CommandHistoryResponse)
async def get_command_history(
    page: int = 1,
    page_size: int = 50,
    user: Optional[str] = None,
    search: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取命令历史记录。
    
    支持分页、按用户筛选和关键字搜索。
    """
    try:
        # TODO: Implement database command history retrieval
        
        # Mock command history for demonstration
        mock_commands = [
            CommandHistoryEntry(
                id=1,
                command="list",
                user="admin",
                timestamp=datetime.now().isoformat(),
                success=True,
                output="There are 3 of a max of 20 players online: Steve, Alex, Notch"
            ),
            CommandHistoryEntry(
                id=2,
                command="say Hello everyone!",
                user="admin",
                timestamp=datetime.now().isoformat(),
                success=True,
                output="[Server] Hello everyone!"
            ),
            CommandHistoryEntry(
                id=3,
                command="tp Steve 100 64 200",
                user="moderator",
                timestamp=datetime.now().isoformat(),
                success=True,
                output="Teleported Steve to 100.0, 64.0, 200.0"
            )
        ]
        
        # Apply user filter if specified
        if user:
            mock_commands = [cmd for cmd in mock_commands if cmd.user.lower() == user.lower()]
        
        # Apply search filter if specified
        if search:
            search_lower = search.lower()
            mock_commands = [
                cmd for cmd in mock_commands 
                if search_lower in cmd.command.lower() or 
                   (cmd.output and search_lower in cmd.output.lower())
            ]
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_commands = mock_commands[start_idx:end_idx]
        
        return CommandHistoryResponse(
            commands=paginated_commands,
            total_count=len(mock_commands),
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Failed to get command history: {e}")
        raise HTTPException(status_code=500, detail=f"获取命令历史失败: {str(e)}")


@router.delete("/history/{command_id}")
async def delete_command_history_entry(
    command_id: int,
    current_user: Dict[str, Any] = Depends(require_permission("console.manage"))
):
    """
    删除命令历史记录条目。
    
    需要 'console.manage' 权限。
    """
    try:
        # TODO: Implement database command history deletion
        
        logger.info(f"User {current_user['username']} deleted command history entry {command_id}")
        
        return {
            "success": True,
            "message": f"命令历史记录 {command_id} 已删除",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to delete command history entry {command_id}: {e}")
        raise HTTPException(status_code=500, detail=f"删除命令历史记录失败: {str(e)}")


@router.post("/clear-history")
async def clear_command_history(
    current_user: Dict[str, Any] = Depends(require_permission("console.manage"))
):
    """
    清空命令历史记录。
    
    需要 'console.manage' 权限。
    """
    try:
        # TODO: Implement database command history clearing
        
        logger.info(f"User {current_user['username']} cleared command history")
        
        return {
            "success": True,
            "message": "命令历史记录已清空",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to clear command history: {e}")
        raise HTTPException(status_code=500, detail=f"清空命令历史记录失败: {str(e)}")


@router.post("/clear-logs")
async def clear_console_logs(
    current_user: Dict[str, Any] = Depends(require_permission("console.manage"))
):
    """
    清空控制台日志。
    
    需要 'console.manage' 权限。
    """
    try:
        # TODO: Implement database log clearing
        
        logger.info(f"User {current_user['username']} cleared console logs")
        
        return {
            "success": True,
            "message": "控制台日志已清空",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to clear console logs: {e}")
        raise HTTPException(status_code=500, detail=f"清空控制台日志失败: {str(e)}")


@router.get("/autocomplete")
async def get_command_autocomplete(
    query: str,
    limit: int = 10,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取命令自动补全建议。
    
    基于查询字符串返回可能的命令建议。
    """
    try:
        # Common Minecraft server commands for autocomplete
        common_commands = [
            "ban", "ban-ip", "banlist", "clear", "clone", "defaultgamemode",
            "deop", "difficulty", "effect", "enchant", "execute", "experience",
            "fill", "function", "gamemode", "gamerule", "give", "help",
            "kick", "kill", "list", "locate", "me", "op", "pardon",
            "pardon-ip", "playsound", "reload", "replaceitem", "save-all",
            "save-off", "save-on", "say", "scoreboard", "seed", "setblock",
            "setidletimeout", "setworldspawn", "spawnpoint", "spreadplayers",
            "stop", "summon", "teleport", "tell", "tellraw", "time",
            "title", "tp", "trigger", "weather", "whitelist", "worldborder",
            "xp"
        ]
        
        # Filter commands based on query
        if query:
            suggestions = [
                cmd for cmd in common_commands 
                if cmd.startswith(query.lower())
            ]
        else:
            suggestions = common_commands
        
        # Limit results
        suggestions = suggestions[:limit]
        
        return {
            "suggestions": suggestions,
            "query": query,
            "count": len(suggestions)
        }
        
    except Exception as e:
        logger.error(f"Failed to get command autocomplete: {e}")
        raise HTTPException(status_code=500, detail=f"获取命令补全失败: {str(e)}")


@router.post("/broadcast")
async def broadcast_message(
    message: str,
    background_tasks: BackgroundTasks,
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    ws_manager: WebSocketManager = Depends(get_websocket_manager),
    current_user: Dict[str, Any] = Depends(require_permission("console.broadcast"))
):
    """
    广播消息到服务器。
    
    需要 'console.broadcast' 权限。使用 'say' 命令向所有玩家发送消息。
    """
    try:
        # Use 'say' command to broadcast message
        say_command = f"say {message}"
        result = await adapter.send_command(say_command)
        
        # Log the broadcast
        logger.info(f"User {current_user['username']} broadcasted message: {message}")
        
        # Create WebSocket message for broadcast
        broadcast_log = create_console_log_message(
            level="INFO",
            message=f"[{current_user['username']}] 广播: {message}",
            source="console"
        )
        
        # Broadcast to console connections
        background_tasks.add_task(
            ws_manager.broadcast_to_type,
            ConnectionType.CONSOLE,
            broadcast_log
        )
        
        return {
            "success": result.get("success", False),
            "message": "消息已广播",
            "broadcast_message": message,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to broadcast message: {e}")
        raise HTTPException(status_code=500, detail=f"广播消息失败: {str(e)}")