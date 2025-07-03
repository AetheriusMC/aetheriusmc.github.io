"""
Server management API endpoints.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from ...core.container import get_container
from ...core.aetherius_adapter import IAetheriusAdapter
from ...utils.security import get_current_user, require_permission
from ...tasks.backup import create_backup
from ...tasks.maintenance import system_maintenance_task
from ...websocket.manager import WebSocketManager
from ...websocket.models import create_notification_message, create_server_status_message

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class ServerStatusResponse(BaseModel):
    """Server status response model."""
    status: str = Field(..., description="Server status")
    uptime: int = Field(..., description="Server uptime in seconds")
    version: str = Field(..., description="Server version")
    online_players: int = Field(..., description="Number of online players")
    max_players: int = Field(..., description="Maximum players")
    timestamp: str = Field(..., description="Status timestamp")


class ServerActionRequest(BaseModel):
    """Server action request model."""
    reason: Optional[str] = Field(None, description="Reason for the action")
    force: bool = Field(False, description="Force the action")


class ServerActionResponse(BaseModel):
    """Server action response model."""
    success: bool = Field(..., description="Action success status")
    message: str = Field(..., description="Action result message")
    timestamp: str = Field(..., description="Action timestamp")


class ServerPerformanceResponse(BaseModel):
    """Server performance response model."""
    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_mb: float = Field(..., description="Memory usage in MB")
    uptime_seconds: float = Field(..., description="Uptime in seconds")
    tps: float = Field(..., description="Ticks per second")
    timestamp: str = Field(..., description="Performance timestamp")


class PluginInfo(BaseModel):
    """Plugin information model."""
    name: str = Field(..., description="Plugin name")
    version: str = Field(..., description="Plugin version")
    description: str = Field(..., description="Plugin description")
    author: str = Field(..., description="Plugin author")
    enabled: bool = Field(..., description="Plugin enabled status")
    loaded: bool = Field(..., description="Plugin loaded status")


class ComponentInfo(BaseModel):
    """Component information model."""
    name: str = Field(..., description="Component name")
    version: str = Field(..., description="Component version")
    description: str = Field(..., description="Component description")
    type: str = Field(..., description="Component type")
    enabled: bool = Field(..., description="Component enabled status")
    loaded: bool = Field(..., description="Component loaded status")


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


@router.get("/status", response_model=ServerStatusResponse)
async def get_server_status(
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取服务器状态信息。
    
    返回当前服务器的运行状态、在线玩家数、运行时间等信息。
    """
    try:
        status_data = await adapter.get_server_status()
        return ServerStatusResponse(**status_data)
    except Exception as e:
        logger.error(f"Failed to get server status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get server status: {str(e)}")


@router.post("/start", response_model=ServerActionResponse)
async def start_server(
    request: ServerActionRequest,
    background_tasks: BackgroundTasks,
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    ws_manager: WebSocketManager = Depends(get_websocket_manager),
    current_user: Dict[str, Any] = Depends(require_permission("server.control"))
):
    """
    启动服务器。
    
    需要 'server.control' 权限。启动成功后会通过 WebSocket 广播状态更新。
    """
    try:
        result = await adapter.start_server()
        
        if result.get("success"):
            # Broadcast server start notification
            notification = create_notification_message(
                title="服务器启动",
                message=f"服务器已成功启动。操作员: {current_user.get('username', 'Unknown')}",
                level="success",
                duration=10
            )
            background_tasks.add_task(ws_manager.broadcast_to_all, notification)
            
            # Broadcast server status update
            status_message = create_server_status_message(
                status="running",
                uptime=0,
                online_players=0,
                max_players=20,
                version="unknown"
            )
            background_tasks.add_task(ws_manager.broadcast_to_all, status_message)
        
        return ServerActionResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start server: {str(e)}")


@router.post("/stop", response_model=ServerActionResponse)
async def stop_server(
    request: ServerActionRequest,
    background_tasks: BackgroundTasks,
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    ws_manager: WebSocketManager = Depends(get_websocket_manager),
    current_user: Dict[str, Any] = Depends(require_permission("server.control"))
):
    """
    停止服务器。
    
    需要 'server.control' 权限。可以提供停止原因，支持强制停止。
    """
    try:
        result = await adapter.stop_server()
        
        if result.get("success"):
            # Broadcast server stop notification
            reason_text = f"原因: {request.reason}" if request.reason else ""
            notification = create_notification_message(
                title="服务器停止",
                message=f"服务器已停止。操作员: {current_user.get('username', 'Unknown')} {reason_text}",
                level="warning",
                duration=15
            )
            background_tasks.add_task(ws_manager.broadcast_to_all, notification)
            
            # Broadcast server status update
            status_message = create_server_status_message(
                status="stopped",
                uptime=0,
                online_players=0,
                max_players=20,
                version="unknown"
            )
            background_tasks.add_task(ws_manager.broadcast_to_all, status_message)
        
        return ServerActionResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to stop server: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop server: {str(e)}")


@router.post("/restart", response_model=ServerActionResponse)
async def restart_server(
    request: ServerActionRequest,
    background_tasks: BackgroundTasks,
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    ws_manager: WebSocketManager = Depends(get_websocket_manager),
    current_user: Dict[str, Any] = Depends(require_permission("server.control"))
):
    """
    重启服务器。
    
    需要 'server.control' 权限。会先停止服务器，然后重新启动。
    """
    try:
        result = await adapter.restart_server()
        
        if result.get("success"):
            # Broadcast server restart notification
            reason_text = f"原因: {request.reason}" if request.reason else ""
            notification = create_notification_message(
                title="服务器重启",
                message=f"服务器正在重启。操作员: {current_user.get('username', 'Unknown')} {reason_text}",
                level="info",
                duration=15
            )
            background_tasks.add_task(ws_manager.broadcast_to_all, notification)
        
        return ServerActionResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to restart server: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restart server: {str(e)}")


@router.get("/performance", response_model=ServerPerformanceResponse)
async def get_server_performance(
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取服务器性能数据。
    
    返回 CPU 使用率、内存使用量、TPS 等性能指标。
    """
    try:
        performance_data = await adapter.get_performance_data()
        return ServerPerformanceResponse(**performance_data)
    except Exception as e:
        logger.error(f"Failed to get server performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get server performance: {str(e)}")


@router.get("/plugins", response_model=List[PluginInfo])
async def get_plugins(
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取服务器插件列表。
    
    返回所有已安装插件的信息，包括状态、版本等。
    """
    try:
        plugins_data = await adapter.get_plugins()
        return [PluginInfo(**plugin) for plugin in plugins_data]
    except Exception as e:
        logger.error(f"Failed to get plugins: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get plugins: {str(e)}")


@router.get("/components", response_model=List[ComponentInfo])
async def get_components(
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取 Aetherius 组件列表。
    
    返回所有已安装 Aetherius 组件的信息。
    """
    try:
        components_data = await adapter.get_components()
        return [ComponentInfo(**component) for component in components_data]
    except Exception as e:
        logger.error(f"Failed to get components: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get components: {str(e)}")


@router.post("/backup", response_model=Dict[str, Any])
async def create_backup(
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_permission("server.backup"))
):
    """
    创建服务器备份。
    
    需要 'server.backup' 权限。备份操作在后台异步执行。
    """
    try:
        # Schedule backup task
        task_result = create_backup.delay(
            backup_type="manual",
            description=f"Manual backup by {current_user.get('username', 'Unknown')}"
        )
        
        return {
            "success": True,
            "message": "备份任务已启动",
            "task_id": task_result.id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create backup: {str(e)}")


@router.post("/maintenance", response_model=Dict[str, Any])
async def run_maintenance(
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_permission("server.maintenance"))
):
    """
    执行系统维护。
    
    需要 'server.maintenance' 权限。维护操作在后台异步执行。
    """
    try:
        # Schedule maintenance task
        task_result = system_maintenance_task.delay()
        
        return {
            "success": True,
            "message": "系统维护任务已启动",
            "task_id": task_result.id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to run maintenance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run maintenance: {str(e)}")


@router.get("/health")
async def health_check():
    """
    健康检查端点。
    
    用于监控服务状态，无需身份验证。
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "webconsole-api"
    }