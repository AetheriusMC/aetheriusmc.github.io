"""
WebSocket routes for the WebConsole application.
Handles WebSocket connections and routing to appropriate handlers.
"""
import uuid
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from ..core.container import DIContainer, get_container
from ..utils.security import get_current_user
import logging
from .endpoints import console_handler, monitoring_handler, notification_handler

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


async def authenticate_websocket(websocket: WebSocket, token: str = None) -> Dict[str, Any]:
    """Authenticate WebSocket connection using token."""
    try:
        if not token:
            # Try to get token from query parameters
            token = websocket.query_params.get("token")
        
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required")
            raise HTTPException(status_code=401, detail="Authentication token required")
        
        # Verify the token
        payload = await verify_token(token)
        if not payload:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        return payload
    
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.websocket("/ws/console")
async def websocket_console_endpoint(
    websocket: WebSocket,
    container: DIContainer = Depends(get_container)
):
    """WebSocket endpoint for console communication."""
    connection_id = str(uuid.uuid4())
    
    try:
        # Authenticate the connection
        user_data = await authenticate_websocket(websocket)
        user_id = user_data.get("sub")
        
        logger.info(f"Console WebSocket connection authenticated: {connection_id} (user: {user_id})")
        
        # Handle the connection
        await console_handler.handle_connection(
            websocket=websocket,
            connection_id=connection_id,
            user_id=user_id,
            container=container
        )
        
    except Exception as e:
        logger.error(f"Console WebSocket error: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
        except:
            pass


@router.websocket("/ws/monitoring")
async def websocket_monitoring_endpoint(
    websocket: WebSocket,
    container: DIContainer = Depends(get_container)
):
    """WebSocket endpoint for monitoring and metrics."""
    connection_id = str(uuid.uuid4())
    
    try:
        # Authenticate the connection
        user_data = await authenticate_websocket(websocket)
        user_id = user_data.get("sub")
        
        logger.info(f"Monitoring WebSocket connection authenticated: {connection_id} (user: {user_id})")
        
        # Handle the connection
        await monitoring_handler.handle_connection(
            websocket=websocket,
            connection_id=connection_id,
            user_id=user_id,
            container=container
        )
        
    except Exception as e:
        logger.error(f"Monitoring WebSocket error: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
        except:
            pass


@router.websocket("/ws/notifications")
async def websocket_notifications_endpoint(
    websocket: WebSocket,
    container: DIContainer = Depends(get_container)
):
    """WebSocket endpoint for notifications and alerts."""
    connection_id = str(uuid.uuid4())
    
    try:
        # Authenticate the connection
        user_data = await authenticate_websocket(websocket)
        user_id = user_data.get("sub")
        
        logger.info(f"Notifications WebSocket connection authenticated: {connection_id} (user: {user_id})")
        
        # Handle the connection
        await notification_handler.handle_connection(
            websocket=websocket,
            connection_id=connection_id,
            user_id=user_id,
            container=container
        )
        
    except Exception as e:
        logger.error(f"Notifications WebSocket error: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
        except:
            pass


@router.websocket("/ws/general")
async def websocket_general_endpoint(
    websocket: WebSocket,
    container: DIContainer = Depends(get_container)
):
    """General WebSocket endpoint for miscellaneous real-time communication."""
    connection_id = str(uuid.uuid4())
    
    try:
        # Authenticate the connection
        user_data = await authenticate_websocket(websocket)
        user_id = user_data.get("sub")
        
        logger.info(f"General WebSocket connection authenticated: {connection_id} (user: {user_id})")
        
        await websocket.accept()
        
        # Simple echo/ping-pong for general communication
        while True:
            try:
                data = await websocket.receive_text()
                # Echo back the message with timestamp
                import json
                from datetime import datetime
                
                response = {
                    "type": "echo",
                    "original_message": data,
                    "timestamp": datetime.utcnow().isoformat(),
                    "connection_id": connection_id
                }
                
                await websocket.send_text(json.dumps(response))
                
            except Exception as e:
                logger.error(f"General WebSocket message error: {e}")
                break
                
    except Exception as e:
        logger.error(f"General WebSocket error: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
        except:
            pass


# Health check endpoint for WebSocket infrastructure
@router.get("/ws/health")
async def websocket_health_check():
    """Health check endpoint for WebSocket infrastructure."""
    return {
        "status": "healthy",
        "websocket_endpoints": [
            "/ws/console",
            "/ws/monitoring", 
            "/ws/notifications",
            "/ws/general"
        ],
        "handlers": {
            "console": len(console_handler.active_connections),
            "monitoring": len(monitoring_handler.active_connections),
            "notifications": len(notification_handler.active_connections)
        }
    }