"""
Player Management API Endpoints
===============================

REST endpoints for player data management and operations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator

from ..core.client import CoreClient
from ..core.api import CoreAPI
from ..models.api_models import Player
from ..utils.logging import get_logger
from ..utils.exceptions import CoreConnectionError, CoreAPIError

logger = get_logger(__name__)

router = APIRouter()

# Request/Response Models
class PlayerSearchParams(BaseModel):
    """Player search parameters"""
    query: Optional[str] = None
    online_only: bool = False
    game_mode: Optional[str] = None
    min_level: Optional[int] = None
    max_level: Optional[int] = None
    sort_by: str = "last_login"
    sort_order: str = "desc"
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_fields = ['name', 'level', 'last_login', 'experience', 'online']
        if v not in allowed_fields:
            raise ValueError(f'sort_by must be one of: {allowed_fields}')
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v


class PlayerOperation(BaseModel):
    """Player operation request"""
    action: str
    reason: Optional[str] = None
    duration: Optional[int] = None  # For temp bans in minutes
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ['kick', 'ban', 'tempban', 'unban', 'op', 'deop', 'teleport', 'heal']
        if v not in allowed_actions:
            raise ValueError(f'action must be one of: {allowed_actions}')
        return v


class BatchPlayerOperation(BaseModel):
    """Batch player operation request"""
    player_uuids: List[str]
    action: str
    reason: Optional[str] = None
    duration: Optional[int] = None
    
    @validator('player_uuids')
    def validate_uuids(cls, v):
        if len(v) == 0:
            raise ValueError('player_uuids cannot be empty')
        if len(v) > 50:  # Safety limit
            raise ValueError('Cannot operate on more than 50 players at once')
        return v


class PlayerResponse(BaseModel):
    """Extended player response with additional data"""
    uuid: str
    name: str
    online: bool
    last_login: Optional[str]
    last_logout: Optional[str]
    ip_address: Optional[str]
    game_mode: str
    level: int
    experience: int
    health: Optional[float] = None
    food_level: Optional[int] = None
    location: Optional[Dict[str, Any]] = None
    inventory_size: Optional[int] = None
    playtime_hours: Optional[float] = None
    is_op: bool = False
    is_banned: bool = False
    ban_reason: Optional[str] = None
    ban_expires: Optional[str] = None


class PlayerSearchResponse(BaseModel):
    """Player search response with pagination"""
    players: List[PlayerResponse]
    total_count: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


# Dependencies
async def get_core_api_from_app(request: Request) -> CoreAPI:
    """Dependency to get core API from app state"""
    core = request.app.state.core
    return CoreAPI(core)


@router.get("/players", response_model=PlayerSearchResponse)
async def search_players(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    query: Optional[str] = Query(None, description="Search query for player name"),
    online_only: bool = Query(False, description="Show only online players"),
    game_mode: Optional[str] = Query(None, description="Filter by game mode"),
    min_level: Optional[int] = Query(None, ge=0, description="Minimum player level"),
    max_level: Optional[int] = Query(None, ge=0, description="Maximum player level"),
    sort_by: str = Query("last_login", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order")
):
    """
    Search and list players with pagination and filtering
    
    Returns:
        Paginated list of players matching search criteria
    """
    try:
        logger.info("Searching players", query=query, page=page, per_page=per_page)
        
        # Get core API from app state
        core = request.app.state.core
        core_api = CoreAPI(core)
        
        # Build search parameters
        search_params = PlayerSearchParams(
            query=query,
            online_only=online_only,
            game_mode=game_mode,
            min_level=min_level,
            max_level=max_level,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Get players from core
        try:
            players_data = await core_api.search_players(
                search_params=search_params.dict(),
                page=page,
                per_page=per_page
            )
        except Exception as e:
            logger.warning("Failed to get real player data, using mock", error=str(e))
            # Mock data for development
            players_data = await _get_mock_players_data(search_params, page, per_page)
        
        return PlayerSearchResponse(**players_data)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except CoreConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Aetherius Core is not available"
        )
    
    except Exception as e:
        logger.error("Error searching players", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to search players"
        )


@router.get("/players/{player_identifier}", response_model=PlayerResponse)
async def get_player_details(
    player_identifier: str,
    request: Request
):
    """
    Get detailed information about a specific player
    
    Args:
        player_identifier: Player UUID or name
        
    Returns:
        Detailed player information
    """
    try:
        logger.info("Getting player details", player_identifier=player_identifier)
        
        # Get core API from app state
        core = request.app.state.core
        core_api = CoreAPI(core)
        
        # Get player data from core
        try:
            player_data = await core_api.get_player_details(player_identifier)
        except Exception as e:
            logger.warning("Failed to get real player data, using mock", error=str(e))
            # Mock data for development
            player_data = await _get_mock_player_details(player_identifier)
        
        if not player_data:
            raise HTTPException(status_code=404, detail="Player not found")
        
        return PlayerResponse(**player_data)
    
    except HTTPException:
        raise
    
    except CoreConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Aetherius Core is not available"
        )
    
    except Exception as e:
        logger.error("Error getting player details", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get player details"
        )


@router.post("/players/{player_identifier}/action")
async def execute_player_action(
    player_identifier: str,
    operation: PlayerOperation,
    request: Request
):
    """
    Execute an action on a specific player
    
    Args:
        player_identifier: Player UUID or name
        operation: Operation to perform
        
    Returns:
        Operation result
    """
    try:
        logger.info(
            "Executing player action",
            player_identifier=player_identifier,
            action=operation.action,
            reason=operation.reason
        )
        
        # Get core API from app state
        core = request.app.state.core
        core_api = CoreAPI(core)
        
        # Execute the operation
        result = await core_api.execute_player_action(
            player_identifier,
            operation.action,
            reason=operation.reason,
            duration=operation.duration
        )
        
        # Log the operation
        await _log_player_operation(
            player_identifier=player_identifier,
            action=operation.action,
            reason=operation.reason,
            result=result,
            operator="admin"  # TODO: Get from auth context
        )
        
        return {
            "success": result.get("success", True),
            "message": result.get("message", f"Action {operation.action} executed"),
            "timestamp": datetime.now().isoformat(),
            "player": player_identifier,
            "action": operation.action
        }
    
    except CoreConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Aetherius Core is not available"
        )
    
    except CoreAPIError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute action: {e.message}"
        )
    
    except Exception as e:
        logger.error("Error executing player action", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post("/players/batch-action")
async def execute_batch_player_action(
    operation: BatchPlayerOperation,
    request: Request
):
    """
    Execute an action on multiple players
    
    Args:
        operation: Batch operation to perform
        
    Returns:
        Batch operation results
    """
    try:
        logger.info(
            "Executing batch player action",
            player_count=len(operation.player_uuids),
            action=operation.action,
            reason=operation.reason
        )
        
        # Get core API from app state
        core = request.app.state.core
        core_api = CoreAPI(core)
        
        # Execute batch operation
        results = []
        success_count = 0
        
        for player_uuid in operation.player_uuids:
            try:
                result = await core_api.execute_player_action(
                    player_uuid,
                    operation.action,
                    reason=operation.reason,
                    duration=operation.duration
                )
                
                success = result.get("success", True)
                if success:
                    success_count += 1
                
                results.append({
                    "player_uuid": player_uuid,
                    "success": success,
                    "message": result.get("message", "Action executed"),
                    "error": result.get("error") if not success else None
                })
                
                # Log individual operation
                await _log_player_operation(
                    player_identifier=player_uuid,
                    action=operation.action,
                    reason=operation.reason,
                    result=result,
                    operator="admin",  # TODO: Get from auth context
                    is_batch=True
                )
                
            except Exception as e:
                logger.warning(f"Failed to execute action on player {player_uuid}", error=str(e))
                results.append({
                    "player_uuid": player_uuid,
                    "success": False,
                    "message": "Failed to execute action",
                    "error": str(e)
                })
        
        return {
            "success": success_count > 0,
            "total_players": len(operation.player_uuids),
            "successful_operations": success_count,
            "failed_operations": len(operation.player_uuids) - success_count,
            "results": results,
            "timestamp": datetime.now().isoformat(),
            "action": operation.action
        }
    
    except CoreConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Aetherius Core is not available"
        )
    
    except Exception as e:
        logger.error("Error executing batch player action", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/players/operations/history")
async def get_player_operations_history(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    player_identifier: Optional[str] = Query(None, description="Filter by player"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    operator: Optional[str] = Query(None, description="Filter by operator")
):
    """
    Get history of player operations
    
    Returns:
        Paginated list of player operations
    """
    try:
        logger.info("Getting player operations history", page=page, per_page=per_page)
        
        # TODO: Implement actual operation history from database
        # For now, return mock data
        
        mock_operations = [
            {
                "id": 1,
                "player_uuid": "550e8400-e29b-41d4-a716-446655440000",
                "player_name": "TestPlayer1",
                "action": "kick",
                "reason": "Spamming chat",
                "operator": "admin",
                "timestamp": "2024-01-15T10:30:00Z",
                "success": True,
                "is_batch": False
            },
            {
                "id": 2,
                "player_uuid": "550e8400-e29b-41d4-a716-446655440001",
                "player_name": "TestPlayer2",
                "action": "ban",
                "reason": "Griefing",
                "operator": "moderator",
                "timestamp": "2024-01-15T09:15:00Z",
                "success": True,
                "is_batch": False
            }
        ]
        
        # Apply filters
        filtered_ops = mock_operations
        if player_identifier:
            filtered_ops = [op for op in filtered_ops 
                          if player_identifier.lower() in op["player_name"].lower() 
                          or player_identifier in op["player_uuid"]]
        
        if action:
            filtered_ops = [op for op in filtered_ops if op["action"] == action]
        
        if operator:
            filtered_ops = [op for op in filtered_ops if op["operator"] == operator]
        
        # Pagination
        total_count = len(filtered_ops)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_operations = filtered_ops[start_idx:end_idx]
        
        return {
            "operations": page_operations,
            "total_count": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_count + per_page - 1) // per_page,
            "has_next": end_idx < total_count,
            "has_prev": page > 1
        }
    
    except Exception as e:
        logger.error("Error getting operations history", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get operations history"
        )


# Helper functions
async def _get_mock_players_data(search_params: PlayerSearchParams, page: int, per_page: int) -> Dict[str, Any]:
    """Generate mock player data for development"""
    import random
    from uuid import uuid4
    
    # Generate mock players
    mock_players = []
    for i in range(50):  # Total of 50 mock players
        player = PlayerResponse(
            uuid=str(uuid4()),
            name=f"Player{i+1}",
            online=random.choice([True, False]),
            last_login=f"2024-01-{random.randint(10, 15):02d}T{random.randint(8, 20):02d}:30:00Z",
            last_logout=f"2024-01-{random.randint(10, 15):02d}T{random.randint(8, 20):02d}:45:00Z",
            ip_address=f"192.168.1.{random.randint(10, 200)}" if random.choice([True, False]) else None,
            game_mode=random.choice(["survival", "creative", "adventure", "spectator"]),
            level=random.randint(1, 100),
            experience=random.randint(0, 10000),
            health=random.uniform(0, 20),
            food_level=random.randint(0, 20),
            location={
                "world": "world",
                "x": random.uniform(-1000, 1000),
                "y": random.uniform(0, 256),
                "z": random.uniform(-1000, 1000)
            },
            inventory_size=random.randint(0, 36),
            playtime_hours=random.uniform(1, 500),
            is_op=random.choice([True, False]) if random.random() < 0.1 else False,
            is_banned=random.choice([True, False]) if random.random() < 0.05 else False,
            ban_reason="Test ban reason" if random.random() < 0.05 else None
        )
        mock_players.append(player)
    
    # Apply filters
    filtered_players = mock_players
    
    if search_params.query:
        filtered_players = [p for p in filtered_players 
                          if search_params.query.lower() in p.name.lower()]
    
    if search_params.online_only:
        filtered_players = [p for p in filtered_players if p.online]
    
    if search_params.game_mode:
        filtered_players = [p for p in filtered_players if p.game_mode == search_params.game_mode]
    
    if search_params.min_level is not None:
        filtered_players = [p for p in filtered_players if p.level >= search_params.min_level]
    
    if search_params.max_level is not None:
        filtered_players = [p for p in filtered_players if p.level <= search_params.max_level]
    
    # Sort
    reverse = search_params.sort_order == "desc"
    if search_params.sort_by == "name":
        filtered_players.sort(key=lambda x: x.name, reverse=reverse)
    elif search_params.sort_by == "level":
        filtered_players.sort(key=lambda x: x.level, reverse=reverse)
    elif search_params.sort_by == "last_login":
        filtered_players.sort(key=lambda x: x.last_login or "", reverse=reverse)
    
    # Pagination
    total_count = len(filtered_players)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_players = filtered_players[start_idx:end_idx]
    
    return {
        "players": [p.dict() for p in page_players],
        "total_count": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": (total_count + per_page - 1) // per_page,
        "has_next": end_idx < total_count,
        "has_prev": page > 1
    }


async def _get_mock_player_details(player_identifier: str) -> Dict[str, Any]:
    """Generate mock player details"""
    import random
    from uuid import uuid4
    
    return {
        "uuid": str(uuid4()),
        "name": f"Player_{player_identifier}",
        "online": random.choice([True, False]),
        "last_login": "2024-01-15T10:30:00Z",
        "last_logout": "2024-01-15T12:30:00Z",
        "ip_address": "192.168.1.100",
        "game_mode": "survival",
        "level": random.randint(1, 100),
        "experience": random.randint(0, 10000),
        "health": 20.0,
        "food_level": 20,
        "location": {
            "world": "world",
            "x": 100.5,
            "y": 64.0,
            "z": -200.3
        },
        "inventory_size": 27,
        "playtime_hours": 125.5,
        "is_op": False,
        "is_banned": False,
        "ban_reason": None,
        "ban_expires": None
    }


async def _log_player_operation(
    player_identifier: str,
    action: str,
    reason: Optional[str],
    result: Dict[str, Any],
    operator: str,
    is_batch: bool = False
):
    """Log player operation for audit trail"""
    try:
        # TODO: Implement actual logging to database
        log_entry = {
            "player_identifier": player_identifier,
            "action": action,
            "reason": reason,
            "result": result,
            "operator": operator,
            "is_batch": is_batch,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("Player operation logged", **log_entry)
        
    except Exception as e:
        logger.error("Failed to log player operation", error=str(e), exc_info=True)