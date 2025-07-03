"""
Dashboard API endpoints.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


class ServerStatus(BaseModel):
    """Server status model."""
    status: str
    uptime: int
    version: str
    online_players: int
    max_players: int
    tps: float
    cpu_usage: float
    memory_usage: Dict[str, Any]
    timestamp: str


class PerformanceMetrics(BaseModel):
    """Performance metrics model."""
    cpu_percent: float
    memory_mb: float
    uptime_seconds: float
    tps: float
    timestamp: str


@router.get("/status", response_model=ServerStatus)
async def get_server_status():
    """Get current server status."""
    logger.info("Server status request")
    
    # TODO: Get actual server status from Aetherius Core
    return ServerStatus(
        status="running",
        uptime=3600,
        version="1.20.1",
        online_players=5,
        max_players=20,
        tps=19.8,
        cpu_usage=45.2,
        memory_usage={
            "used": 2048,
            "max": 4096,
            "percentage": 50.0
        },
        timestamp=datetime.now().isoformat()
    )


@router.get("/metrics", response_model=PerformanceMetrics)
async def get_performance_metrics():
    """Get current performance metrics."""
    logger.info("Performance metrics request")
    
    # TODO: Get actual metrics from Aetherius Core
    return PerformanceMetrics(
        cpu_percent=45.2,
        memory_mb=2048.0,
        uptime_seconds=3600.0,
        tps=19.8,
        timestamp=datetime.now().isoformat()
    )


@router.websocket("/ws")
async def dashboard_websocket(websocket: WebSocket):
    """Dashboard WebSocket endpoint for real-time updates."""
    await websocket.accept()
    logger.info("Dashboard WebSocket connection established")
    
    try:
        while True:
            # Send periodic updates
            status = {
                "type": "status_update",
                "data": {
                    "status": "running",
                    "online_players": 5,
                    "tps": 19.8,
                    "cpu_usage": 45.2,
                    "memory_usage": {
                        "percentage": 50.0
                    }
                },
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send_json(status)
            await asyncio.sleep(5)  # Send updates every 5 seconds
            
    except WebSocketDisconnect:
        logger.info("Dashboard WebSocket connection closed")
    except Exception as e:
        logger.error(f"Dashboard WebSocket error: {e}")
        await websocket.close()