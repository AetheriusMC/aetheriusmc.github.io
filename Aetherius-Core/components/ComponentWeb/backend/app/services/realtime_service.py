"""
Real-time Data Service
=====================

Service for pushing real-time data updates to WebSocket clients.
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.core.api import CoreAPI
from app.websocket.manager import (
    WebSocketManager, 
    ConnectionType, 
    create_performance_message,
    create_dashboard_summary_message,
    create_status_message
)
from app.utils.logging import get_logger

logger = get_logger(__name__)


class RealtimeService:
    """Service for real-time data updates"""
    
    def __init__(self, websocket_manager: WebSocketManager, core_api: CoreAPI):
        self.ws_manager = websocket_manager
        self.core_api = core_api
        self._running = False
        self._tasks: Dict[str, asyncio.Task] = {}
        self._update_intervals = {
            "performance": 5.0,  # 5 seconds
            "status": 10.0,      # 10 seconds  
            "summary": 30.0,     # 30 seconds
        }
    
    async def start(self):
        """Start all real-time update tasks"""
        if self._running:
            logger.warning("RealtimeService is already running")
            return
        
        self._running = True
        logger.info("Starting RealtimeService")
        
        # Start individual update tasks
        self._tasks["performance"] = asyncio.create_task(self._performance_update_loop())
        self._tasks["status"] = asyncio.create_task(self._status_update_loop())
        self._tasks["summary"] = asyncio.create_task(self._summary_update_loop())
        
        logger.info("RealtimeService started successfully")
    
    async def stop(self):
        """Stop all real-time update tasks"""
        if not self._running:
            return
        
        self._running = False
        logger.info("Stopping RealtimeService")
        
        # Cancel all tasks
        for task_name, task in self._tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.debug(f"Task {task_name} cancelled successfully")
                except Exception as e:
                    logger.warning(f"Error stopping task {task_name}", error=str(e))
        
        self._tasks.clear()
        logger.info("RealtimeService stopped")
    
    async def _performance_update_loop(self):
        """Loop for sending performance updates"""
        logger.info("Starting performance update loop")
        
        while self._running:
            try:
                # Check if there are dashboard connections
                if self.ws_manager.get_connection_count_by_type(ConnectionType.DASHBOARD) > 0:
                    try:
                        # Get current performance data
                        performance = await self.core_api.get_current_performance()
                        
                        # Broadcast to all dashboard connections
                        await self.ws_manager.broadcast_to_type(
                            ConnectionType.DASHBOARD,
                            create_performance_message(performance)
                        )
                        
                        logger.debug("Performance update sent to dashboard clients")
                        
                    except Exception as e:
                        logger.warning("Failed to send performance update", error=str(e))
                
                # Wait for next update
                await asyncio.sleep(self._update_intervals["performance"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in performance update loop", error=str(e), exc_info=True)
                await asyncio.sleep(self._update_intervals["performance"])
    
    async def _status_update_loop(self):
        """Loop for sending status updates"""
        logger.info("Starting status update loop")
        
        while self._running:
            try:
                # Check if there are status connections
                if self.ws_manager.get_connection_count_by_type(ConnectionType.STATUS) > 0:
                    try:
                        # Get server status
                        status = await self.core_api.get_server_status()
                        
                        # Broadcast to all status connections
                        await self.ws_manager.broadcast_to_type(
                            ConnectionType.STATUS,
                            create_status_message(status)
                        )
                        
                        logger.debug("Status update sent to status clients")
                        
                    except Exception as e:
                        logger.warning("Failed to send status update", error=str(e))
                
                # Wait for next update
                await asyncio.sleep(self._update_intervals["status"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in status update loop", error=str(e), exc_info=True)
                await asyncio.sleep(self._update_intervals["status"])
    
    async def _summary_update_loop(self):
        """Loop for sending dashboard summary updates"""
        logger.info("Starting summary update loop")
        
        while self._running:
            try:
                # Check if there are dashboard connections
                if self.ws_manager.get_connection_count_by_type(ConnectionType.DASHBOARD) > 0:
                    try:
                        # Get server status and players
                        status_task = self.core_api.get_server_status()
                        players_task = self.core_api.get_online_players()
                        
                        status, players = await asyncio.gather(
                            status_task,
                            players_task,
                            return_exceptions=True
                        )
                        
                        # Handle errors gracefully
                        if isinstance(status, Exception):
                            status = {"is_running": False, "uptime": 0}
                        if isinstance(players, Exception):
                            players = []
                        
                        summary_data = {
                            "server_status": status,
                            "online_players": players,
                            "player_count": len(players),
                            "uptime": status.get("uptime", 0),
                            "version": status.get("version", "Unknown"),
                            "is_running": status.get("is_running", False)
                        }
                        
                        # Broadcast to all dashboard connections
                        await self.ws_manager.broadcast_to_type(
                            ConnectionType.DASHBOARD,
                            create_dashboard_summary_message(summary_data)
                        )
                        
                        logger.debug("Summary update sent to dashboard clients")
                        
                    except Exception as e:
                        logger.warning("Failed to send summary update", error=str(e))
                
                # Wait for next update
                await asyncio.sleep(self._update_intervals["summary"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in summary update loop", error=str(e), exc_info=True)
                await asyncio.sleep(self._update_intervals["summary"])
    
    def set_update_interval(self, update_type: str, interval: float):
        """
        Set update interval for a specific update type
        
        Args:
            update_type: Type of update ("performance", "status", "summary")
            interval: Update interval in seconds
        """
        if update_type in self._update_intervals:
            self._update_intervals[update_type] = interval
            logger.info(f"Updated {update_type} interval to {interval}s")
        else:
            logger.warning(f"Unknown update type: {update_type}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "running": self._running,
            "active_tasks": len([t for t in self._tasks.values() if not t.done()]),
            "update_intervals": self._update_intervals,
            "connection_stats": self.ws_manager.get_connection_stats()
        }
    
    async def force_update(self, update_type: str = "all"):
        """
        Force an immediate update
        
        Args:
            update_type: Type of update to force ("performance", "status", "summary", "all")
        """
        logger.info(f"Forcing {update_type} update")
        
        try:
            if update_type in ["performance", "all"]:
                if self.ws_manager.get_connection_count_by_type(ConnectionType.DASHBOARD) > 0:
                    performance = await self.core_api.get_current_performance()
                    await self.ws_manager.broadcast_to_type(
                        ConnectionType.DASHBOARD,
                        create_performance_message(performance)
                    )
            
            if update_type in ["status", "all"]:
                if self.ws_manager.get_connection_count_by_type(ConnectionType.STATUS) > 0:
                    status = await self.core_api.get_server_status()
                    await self.ws_manager.broadcast_to_type(
                        ConnectionType.STATUS,
                        create_status_message(status)
                    )
            
            if update_type in ["summary", "all"]:
                if self.ws_manager.get_connection_count_by_type(ConnectionType.DASHBOARD) > 0:
                    status_task = self.core_api.get_server_status()
                    players_task = self.core_api.get_online_players()
                    
                    status, players = await asyncio.gather(
                        status_task,
                        players_task,
                        return_exceptions=True
                    )
                    
                    if isinstance(status, Exception):
                        status = {"is_running": False}
                    if isinstance(players, Exception):
                        players = []
                    
                    summary_data = {
                        "server_status": status,
                        "online_players": players,
                        "player_count": len(players)
                    }
                    
                    await self.ws_manager.broadcast_to_type(
                        ConnectionType.DASHBOARD,
                        create_dashboard_summary_message(summary_data)
                    )
            
            logger.info(f"Force {update_type} update completed")
            
        except Exception as e:
            logger.error(f"Error during force {update_type} update", error=str(e), exc_info=True)