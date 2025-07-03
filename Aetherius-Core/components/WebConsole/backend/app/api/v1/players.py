"""
Player management API endpoints.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field

from ...core.container import get_container
from ...core.aetherius_adapter import IAetheriusAdapter
from ...utils.security import get_current_user, require_permission
from ...websocket.manager import WebSocketManager
from ...websocket.models import create_player_event_message, create_notification_message
from ...tasks.player import (
    player_notification_task, player_behavior_analysis_task,
    player_moderation_task, player_data_sync_task
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class PlayerInfo(BaseModel):
    """Player information model."""
    uuid: str = Field(..., description="Player UUID")
    name: str = Field(..., description="Player name")
    online: bool = Field(..., description="Online status")
    last_seen: str = Field(..., description="Last seen timestamp")
    level: int = Field(default=0, description="Player level")
    experience: int = Field(default=0, description="Player experience points")
    health: float = Field(default=20.0, description="Player health")
    food_level: int = Field(default=20, description="Player food level")
    game_mode: str = Field(default="survival", description="Player game mode")
    location: Dict[str, Any] = Field(default_factory=dict, description="Player location")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="Player statistics")


class PlayersResponse(BaseModel):
    """Players list response model."""
    players: List[PlayerInfo] = Field(..., description="List of players")
    total_count: int = Field(..., description="Total number of players")
    online_count: int = Field(..., description="Number of online players")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")


class PlayerActionRequest(BaseModel):
    """Player action request model."""
    reason: Optional[str] = Field(None, description="Reason for the action")
    duration: Optional[int] = Field(None, description="Action duration in minutes")
    message: Optional[str] = Field(None, description="Message to send to player")


class PlayerActionResponse(BaseModel):
    """Player action response model."""
    success: bool = Field(..., description="Action success status")
    action: str = Field(..., description="Action performed")
    player: str = Field(..., description="Target player")
    reason: Optional[str] = Field(None, description="Action reason")
    message: str = Field(..., description="Result message")
    timestamp: str = Field(..., description="Action timestamp")


class PlayerNotificationRequest(BaseModel):
    """Player notification request model."""
    message: str = Field(..., description="Notification message")
    type: str = Field("info", description="Notification type (info, warning, error, success)")
    duration: Optional[int] = Field(None, description="Display duration in seconds")


class PlayerSearchRequest(BaseModel):
    """Player search request model."""
    query: str = Field(..., description="Search query")
    search_fields: List[str] = Field(default=["name", "uuid"], description="Fields to search in")
    online_only: bool = Field(False, description="Search only online players")


class PlayerStatistics(BaseModel):
    """Player statistics model."""
    blocks_broken: int = Field(default=0, description="Blocks broken")
    blocks_placed: int = Field(default=0, description="Blocks placed")
    distance_traveled: float = Field(default=0.0, description="Distance traveled")
    time_played: int = Field(default=0, description="Time played in ticks")
    deaths: int = Field(default=0, description="Number of deaths")
    mob_kills: int = Field(default=0, description="Mob kills")
    player_kills: int = Field(default=0, description="Player kills")


class PlayerBehaviorAnalysis(BaseModel):
    """Player behavior analysis model."""
    player: str = Field(..., description="Player identifier")
    analysis_period_hours: int = Field(..., description="Analysis period in hours")
    behavior_metrics: Dict[str, str] = Field(..., description="Behavior metrics")
    statistics: PlayerStatistics = Field(..., description="Player statistics")
    flags: List[str] = Field(..., description="Behavior flags")
    recommendations: List[str] = Field(..., description="Recommendations")
    timestamp: str = Field(..., description="Analysis timestamp")


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


@router.get("/", response_model=PlayersResponse)
async def get_players(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    online_only: bool = Query(False, description="Show only online players"),
    search: Optional[str] = Query(None, description="Search players by name or UUID"),
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取玩家列表。
    
    支持分页、在线筛选和搜索功能。
    """
    try:
        if online_only:
            # Get only online players
            players_data = await adapter.get_online_players()
        else:
            # TODO: Get all players from database
            # For now, just get online players
            players_data = await adapter.get_online_players()
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            players_data = [
                player for player in players_data
                if search_lower in player.get("name", "").lower() or
                   search_lower in player.get("uuid", "").lower()
            ]
        
        # Apply pagination
        total_count = len(players_data)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_players = players_data[start_idx:end_idx]
        
        # Convert to PlayerInfo models
        players = [PlayerInfo(**player) for player in paginated_players]
        
        # Count online players
        online_count = len([p for p in players_data if p.get("online", False)])
        
        return PlayersResponse(
            players=players,
            total_count=total_count,
            online_count=online_count,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Failed to get players: {e}")
        raise HTTPException(status_code=500, detail=f"获取玩家列表失败: {str(e)}")


@router.get("/{player_identifier}", response_model=PlayerInfo)
async def get_player(
    player_identifier: str,
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取指定玩家的详细信息。
    
    可以使用玩家名或 UUID 查询。
    """
    try:
        player_data = await adapter.get_player_info(player_identifier)
        
        if not player_data:
            raise HTTPException(status_code=404, detail=f"玩家 {player_identifier} 未找到")
        
        return PlayerInfo(**player_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get player {player_identifier}: {e}")
        raise HTTPException(status_code=500, detail=f"获取玩家信息失败: {str(e)}")


@router.post("/{player_identifier}/kick", response_model=PlayerActionResponse)
async def kick_player(
    player_identifier: str,
    request: PlayerActionRequest,
    background_tasks: BackgroundTasks,
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    ws_manager: WebSocketManager = Depends(get_websocket_manager),
    current_user: Dict[str, Any] = Depends(require_permission("player.moderate"))
):
    """
    踢出玩家。
    
    需要 'player.moderate' 权限。
    """
    try:
        # Execute kick action
        task_result = player_moderation_task.delay(
            action="kick",
            player_identifier=player_identifier,
            reason=request.reason or "No reason provided"
        )
        
        # Wait for task result (with timeout)
        result = task_result.get(timeout=10)
        
        if result.get("success"):
            # Send notification to admins
            notification = create_notification_message(
                title="玩家管理操作",
                message=f"玩家 {player_identifier} 已被 {current_user['username']} 踢出服务器",
                level="warning",
                duration=15
            )
            background_tasks.add_task(ws_manager.broadcast_to_all, notification)
        
        return PlayerActionResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to kick player {player_identifier}: {e}")
        raise HTTPException(status_code=500, detail=f"踢出玩家失败: {str(e)}")


@router.post("/{player_identifier}/ban", response_model=PlayerActionResponse)
async def ban_player(
    player_identifier: str,
    request: PlayerActionRequest,
    background_tasks: BackgroundTasks,
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    ws_manager: WebSocketManager = Depends(get_websocket_manager),
    current_user: Dict[str, Any] = Depends(require_permission("player.moderate"))
):
    """
    封禁玩家。
    
    需要 'player.moderate' 权限。
    """
    try:
        # Execute ban action
        task_result = player_moderation_task.delay(
            action="ban",
            player_identifier=player_identifier,
            reason=request.reason or "No reason provided"
        )
        
        # Wait for task result (with timeout)
        result = task_result.get(timeout=10)
        
        if result.get("success"):
            # Send notification to admins
            notification = create_notification_message(
                title="玩家管理操作",
                message=f"玩家 {player_identifier} 已被 {current_user['username']} 封禁",
                level="error",
                duration=20
            )
            background_tasks.add_task(ws_manager.broadcast_to_all, notification)
        
        return PlayerActionResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to ban player {player_identifier}: {e}")
        raise HTTPException(status_code=500, detail=f"封禁玩家失败: {str(e)}")


@router.post("/{player_identifier}/notify", response_model=Dict[str, Any])
async def notify_player(
    player_identifier: str,
    request: PlayerNotificationRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_permission("player.message"))
):
    """
    向玩家发送通知。
    
    需要 'player.message' 权限。
    """
    try:
        # Send notification to player
        task_result = player_notification_task.delay(
            player_identifier=player_identifier,
            message=request.message,
            notification_type=request.type
        )
        
        # Wait for task result (with timeout)
        result = task_result.get(timeout=10)
        
        logger.info(f"User {current_user['username']} sent notification to {player_identifier}: {request.message}")
        
        return {
            "success": result.get("success", False),
            "message": "通知已发送",
            "player": player_identifier,
            "notification": request.message,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to notify player {player_identifier}: {e}")
        raise HTTPException(status_code=500, detail=f"发送通知失败: {str(e)}")


@router.get("/{player_identifier}/analysis", response_model=Dict[str, Any])
async def analyze_player_behavior(
    player_identifier: str,
    analysis_period: int = Query(24, ge=1, le=168, description="Analysis period in hours"),
    current_user: Dict[str, Any] = Depends(require_permission("player.analyze"))
):
    """
    分析玩家行为模式。
    
    需要 'player.analyze' 权限。返回玩家的行为分析报告。
    """
    try:
        # Run behavior analysis
        task_result = player_behavior_analysis_task.delay(
            player_identifier=player_identifier,
            analysis_period_hours=analysis_period
        )
        
        # Wait for task result (with timeout)
        result = task_result.get(timeout=30)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "分析失败"))
        
        return result["analysis"]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze player {player_identifier}: {e}")
        raise HTTPException(status_code=500, detail=f"玩家行为分析失败: {str(e)}")


@router.post("/{player_identifier}/teleport")
async def teleport_player(
    player_identifier: str,
    x: float = Query(..., description="X coordinate"),
    y: float = Query(..., description="Y coordinate"),
    z: float = Query(..., description="Z coordinate"),
    world: str = Query("world", description="World name"),
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    current_user: Dict[str, Any] = Depends(require_permission("player.teleport"))
):
    """
    传送玩家到指定位置。
    
    需要 'player.teleport' 权限。
    """
    try:
        # Execute teleport command
        tp_command = f"tp {player_identifier} {x} {y} {z}"
        result = await adapter.send_command(tp_command)
        
        logger.info(f"User {current_user['username']} teleported {player_identifier} to {x}, {y}, {z}")
        
        return {
            "success": result.get("success", False),
            "message": f"玩家 {player_identifier} 已传送到 ({x}, {y}, {z})",
            "command": tp_command,
            "output": result.get("output"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to teleport player {player_identifier}: {e}")
        raise HTTPException(status_code=500, detail=f"传送玩家失败: {str(e)}")


@router.post("/{player_identifier}/gamemode")
async def change_player_gamemode(
    player_identifier: str,
    gamemode: str = Query(..., description="Game mode (survival, creative, adventure, spectator)"),
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    current_user: Dict[str, Any] = Depends(require_permission("player.gamemode"))
):
    """
    更改玩家游戏模式。
    
    需要 'player.gamemode' 权限。
    """
    try:
        # Validate gamemode
        valid_modes = ["survival", "creative", "adventure", "spectator", "0", "1", "2", "3"]
        if gamemode.lower() not in valid_modes:
            raise HTTPException(status_code=400, detail=f"无效的游戏模式: {gamemode}")
        
        # Execute gamemode command
        gamemode_command = f"gamemode {gamemode} {player_identifier}"
        result = await adapter.send_command(gamemode_command)
        
        logger.info(f"User {current_user['username']} changed {player_identifier} gamemode to {gamemode}")
        
        return {
            "success": result.get("success", False),
            "message": f"玩家 {player_identifier} 的游戏模式已更改为 {gamemode}",
            "command": gamemode_command,
            "output": result.get("output"),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to change gamemode for {player_identifier}: {e}")
        raise HTTPException(status_code=500, detail=f"更改游戏模式失败: {str(e)}")


@router.post("/{player_identifier}/give")
async def give_item_to_player(
    player_identifier: str,
    item: str = Query(..., description="Item name or ID"),
    count: int = Query(1, ge=1, le=64, description="Item count"),
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    current_user: Dict[str, Any] = Depends(require_permission("player.give"))
):
    """
    给予玩家物品。
    
    需要 'player.give' 权限。
    """
    try:
        # Execute give command
        give_command = f"give {player_identifier} {item} {count}"
        result = await adapter.send_command(give_command)
        
        logger.info(f"User {current_user['username']} gave {count} {item} to {player_identifier}")
        
        return {
            "success": result.get("success", False),
            "message": f"已给予玩家 {player_identifier} {count} 个 {item}",
            "command": give_command,
            "output": result.get("output"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to give item to {player_identifier}: {e}")
        raise HTTPException(status_code=500, detail=f"给予物品失败: {str(e)}")


@router.post("/search", response_model=PlayersResponse)
async def search_players(
    request: PlayerSearchRequest,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    搜索玩家。
    
    支持多字段搜索和高级筛选。
    """
    try:
        # Get players data
        if request.online_only:
            players_data = await adapter.get_online_players()
        else:
            # TODO: Get all players from database
            players_data = await adapter.get_online_players()
        
        # Apply search filters
        query_lower = request.query.lower()
        filtered_players = []
        
        for player in players_data:
            match_found = False
            for field in request.search_fields:
                field_value = str(player.get(field, "")).lower()
                if query_lower in field_value:
                    match_found = True
                    break
            
            if match_found:
                filtered_players.append(player)
        
        # Apply pagination
        total_count = len(filtered_players)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_players = filtered_players[start_idx:end_idx]
        
        # Convert to PlayerInfo models
        players = [PlayerInfo(**player) for player in paginated_players]
        
        # Count online players
        online_count = len([p for p in filtered_players if p.get("online", False)])
        
        return PlayersResponse(
            players=players,
            total_count=total_count,
            online_count=online_count,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Failed to search players: {e}")
        raise HTTPException(status_code=500, detail=f"搜索玩家失败: {str(e)}")


@router.post("/sync")
async def sync_player_data(
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_permission("player.manage")),
    player_identifier: Optional[str] = None
):
    """
    同步玩家数据。
    
    需要 'player.manage' 权限。如果不指定玩家，则同步所有在线玩家。
    """
    try:
        # Schedule player data sync task
        task_result = player_data_sync_task.delay(player_identifier)
        
        return {
            "success": True,
            "message": "玩家数据同步任务已启动",
            "task_id": task_result.id,
            "player": player_identifier or "all_online",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to sync player data: {e}")
        raise HTTPException(status_code=500, detail=f"同步玩家数据失败: {str(e)}")


@router.get("/stats/summary")
async def get_player_stats_summary(
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取玩家统计摘要。
    
    返回服务器玩家的总体统计信息。
    """
    try:
        # Get online players
        online_players = await adapter.get_online_players()
        
        # TODO: Get total players from database
        total_players = len(online_players)  # Placeholder
        
        # Calculate statistics
        total_playtime = sum(
            player.get("statistics", {}).get("time_played", 0) 
            for player in online_players
        )
        
        # Convert ticks to hours (20 ticks per second)
        total_playtime_hours = total_playtime / (20 * 3600) if total_playtime > 0 else 0
        
        return {
            "total_players": total_players,
            "online_players": len(online_players),
            "total_playtime_hours": round(total_playtime_hours, 2),
            "average_level": round(
                sum(player.get("level", 0) for player in online_players) / len(online_players)
                if online_players else 0, 1
            ),
            "most_active_players": [
                {
                    "name": player["name"],
                    "playtime_hours": round(
                        player.get("statistics", {}).get("time_played", 0) / (20 * 3600), 2
                    )
                }
                for player in sorted(
                    online_players,
                    key=lambda p: p.get("statistics", {}).get("time_played", 0),
                    reverse=True
                )[:5]
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get player stats summary: {e}")
        raise HTTPException(status_code=500, detail=f"获取玩家统计摘要失败: {str(e)}")