"""
Monitoring WebSocket endpoint for real-time metrics and dashboard updates.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Set
from datetime import datetime, timedelta
from fastapi import WebSocket, WebSocketDisconnect, Depends

from ...core.container import get_container
from ...core.aetherius_adapter import IAetheriusAdapter
from ...utils.security import get_current_user
from ..manager import WebSocketManager
from ..models import (
    ConnectionType, WSMessage, WSMessageType,
    create_performance_update_message, create_dashboard_update_message,
    create_error_message, create_ws_message
)

logger = logging.getLogger(__name__)


class MonitoringWebSocketHandler:
    """Handle monitoring WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        self.metric_subscriptions: Dict[str, Set[str]] = {}  # connection_id -> set of metrics
        self.update_intervals: Dict[str, int] = {}  # connection_id -> interval in seconds
        self.background_tasks: Dict[str, asyncio.Task] = {}
    
    async def handle_connection(
        self,
        websocket: WebSocket,
        user_id: str,
        ws_manager: WebSocketManager,
        adapter: IAetheriusAdapter
    ):
        """Handle a new monitoring WebSocket connection."""
        try:
            # Accept the connection
            await websocket.accept()
            
            # Register connection with WebSocket manager
            connection_id = await ws_manager.add_connection(
                websocket=websocket,
                user_id=user_id,
                connection_type=ConnectionType.MONITORING
            )
            
            # Store connection info
            self.active_connections[connection_id] = websocket
            self.user_sessions[connection_id] = {
                "user_id": user_id,
                "connected_at": datetime.now(),
                "subscriptions": set(),
                "last_update": None
            }
            self.metric_subscriptions[connection_id] = set()
            self.update_intervals[connection_id] = 5  # Default 5 seconds
            
            logger.info(f"Monitoring WebSocket connected: {connection_id} (user: {user_id})")
            
            # Send initial dashboard data
            await self._send_initial_data(connection_id, adapter)
            
            # Start background metrics update task
            self.background_tasks[connection_id] = asyncio.create_task(
                self._metrics_update_loop(connection_id, adapter)
            )
            
            # Listen for messages
            await self._handle_messages(connection_id, websocket, adapter, ws_manager)
            
        except WebSocketDisconnect:
            await self._cleanup_connection(connection_id, ws_manager)
        except Exception as e:
            logger.error(f"Monitoring WebSocket error: {e}")
            await self._cleanup_connection(connection_id, ws_manager)
    
    async def _send_initial_data(self, connection_id: str, adapter: IAetheriusAdapter):
        """Send initial dashboard data to new connection."""
        try:
            websocket = self.active_connections[connection_id]
            
            # Get current server status and performance
            server_status = await adapter.get_server_status()
            performance_data = await adapter.get_performance_data()
            online_players = await adapter.get_online_players()
            
            # Create dashboard update message
            dashboard_data = {
                "server_status": server_status,
                "performance": performance_data,
                "player_count": len(online_players),
                "online_players": online_players[:10],  # First 10 players
                "timestamp": datetime.now().isoformat()
            }
            
            initial_msg = create_ws_message(
                WSMessageType.DASHBOARD_UPDATE,
                dashboard_data
            )
            
            await websocket.send_text(initial_msg.json())
            
        except Exception as e:
            logger.error(f"Failed to send initial data to {connection_id}: {e}")
    
    async def _handle_messages(
        self,
        connection_id: str,
        websocket: WebSocket,
        adapter: IAetheriusAdapter,
        ws_manager: WebSocketManager
    ):
        """Handle incoming WebSocket messages."""
        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                
                try:
                    message = json.loads(data)
                    await self._process_message(connection_id, message, adapter, ws_manager)
                except json.JSONDecodeError:
                    error_msg = create_error_message("Invalid JSON format")
                    await websocket.send_text(error_msg.json())
                except Exception as e:
                    error_msg = create_error_message(f"Message processing error: {str(e)}")
                    await websocket.send_text(error_msg.json())
                    
        except WebSocketDisconnect:
            logger.info(f"Monitoring WebSocket disconnected: {connection_id}")
            raise
        except Exception as e:
            logger.error(f"Message handling error for {connection_id}: {e}")
            raise
    
    async def _process_message(
        self,
        connection_id: str,
        message: Dict[str, Any],
        adapter: IAetheriusAdapter,
        ws_manager: WebSocketManager
    ):
        """Process a received WebSocket message."""
        message_type = message.get("type")
        data = message.get("data", {})
        
        websocket = self.active_connections.get(connection_id)
        if not websocket:
            return
        
        if message_type == "subscribe_metrics":
            await self._handle_metric_subscription(connection_id, data)
        
        elif message_type == "unsubscribe_metrics":
            await self._handle_metric_unsubscription(connection_id, data)
        
        elif message_type == "set_update_interval":
            await self._handle_update_interval(connection_id, data)
        
        elif message_type == "request_dashboard_refresh":
            await self._handle_dashboard_refresh(connection_id, adapter)
        
        elif message_type == "get_metric_history":
            await self._handle_metric_history(connection_id, data, adapter)
        
        elif message_type == "ping":
            # Respond to ping with pong
            pong_msg = create_ws_message(WSMessageType.PONG, {"timestamp": datetime.now().isoformat()})
            await websocket.send_text(pong_msg.json())
        
        else:
            error_msg = create_error_message(f"Unknown message type: {message_type}")
            await websocket.send_text(error_msg.json())
    
    async def _handle_metric_subscription(self, connection_id: str, data: Dict[str, Any]):
        """Handle metric subscription request."""
        metrics = data.get("metrics", [])
        websocket = self.active_connections[connection_id]
        
        try:
            # Add metrics to subscription
            self.metric_subscriptions[connection_id].update(metrics)
            self.user_sessions[connection_id]["subscriptions"].update(metrics)
            
            # Send confirmation
            confirmation = create_ws_message(
                WSMessageType.METRIC_SUBSCRIPTION,
                {
                    "subscribed_metrics": list(self.metric_subscriptions[connection_id]),
                    "message": f"Subscribed to {len(metrics)} metrics",
                    "timestamp": datetime.now().isoformat()
                }
            )
            await websocket.send_text(confirmation.json())
            
            logger.info(f"Connection {connection_id} subscribed to metrics: {metrics}")
            
        except Exception as e:
            logger.error(f"Metric subscription error: {e}")
            error_msg = create_error_message(f"Subscription failed: {str(e)}")
            await websocket.send_text(error_msg.json())
    
    async def _handle_metric_unsubscription(self, connection_id: str, data: Dict[str, Any]):
        """Handle metric unsubscription request."""
        metrics = data.get("metrics", [])
        websocket = self.active_connections[connection_id]
        
        try:
            # Remove metrics from subscription
            self.metric_subscriptions[connection_id].discard(*metrics)
            self.user_sessions[connection_id]["subscriptions"].discard(*metrics)
            
            # Send confirmation
            confirmation = create_ws_message(
                WSMessageType.METRIC_SUBSCRIPTION,
                {
                    "subscribed_metrics": list(self.metric_subscriptions[connection_id]),
                    "message": f"Unsubscribed from {len(metrics)} metrics",
                    "timestamp": datetime.now().isoformat()
                }
            )
            await websocket.send_text(confirmation.json())
            
        except Exception as e:
            logger.error(f"Metric unsubscription error: {e}")
            error_msg = create_error_message(f"Unsubscription failed: {str(e)}")
            await websocket.send_text(error_msg.json())
    
    async def _handle_update_interval(self, connection_id: str, data: Dict[str, Any]):
        """Handle update interval change."""
        interval = data.get("interval", 5)
        websocket = self.active_connections[connection_id]
        
        try:
            # Validate interval (1-60 seconds)
            interval = max(1, min(60, int(interval)))
            self.update_intervals[connection_id] = interval
            
            # Send confirmation
            confirmation = create_ws_message(
                WSMessageType.UPDATE_INTERVAL,
                {
                    "interval": interval,
                    "message": f"Update interval set to {interval} seconds",
                    "timestamp": datetime.now().isoformat()
                }
            )
            await websocket.send_text(confirmation.json())
            
        except Exception as e:
            logger.error(f"Update interval error: {e}")
            error_msg = create_error_message(f"Interval update failed: {str(e)}")
            await websocket.send_text(error_msg.json())
    
    async def _handle_dashboard_refresh(self, connection_id: str, adapter: IAetheriusAdapter):
        """Handle dashboard refresh request."""
        try:
            await self._send_initial_data(connection_id, adapter)
        except Exception as e:
            logger.error(f"Dashboard refresh error: {e}")
            websocket = self.active_connections[connection_id]
            error_msg = create_error_message(f"Dashboard refresh failed: {str(e)}")
            await websocket.send_text(error_msg.json())
    
    async def _handle_metric_history(self, connection_id: str, data: Dict[str, Any], adapter: IAetheriusAdapter):
        """Handle metric history request."""
        websocket = self.active_connections[connection_id]
        
        try:
            metric_name = data.get("metric", "cpu_percent")
            duration_hours = data.get("duration_hours", 1)
            interval_minutes = data.get("interval_minutes", 5)
            
            # TODO: Get actual metric history from database/monitoring system
            # For now, generate mock data
            
            import random
            
            # Generate time series data
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=duration_hours)
            
            history_data = []
            current_time = start_time
            
            while current_time <= end_time:
                if metric_name == "cpu_percent":
                    value = random.uniform(20.0, 80.0)
                elif metric_name == "memory_mb":
                    value = random.uniform(1000.0, 3000.0)
                elif metric_name == "tps":
                    value = random.uniform(18.0, 20.0)
                else:
                    value = random.uniform(0.0, 100.0)
                
                history_data.append({
                    "timestamp": current_time.isoformat(),
                    "value": round(value, 2)
                })
                
                current_time += timedelta(minutes=interval_minutes)
            
            history_msg = create_ws_message(
                WSMessageType.METRIC_HISTORY,
                {
                    "metric": metric_name,
                    "duration_hours": duration_hours,
                    "interval_minutes": interval_minutes,
                    "data": history_data,
                    "count": len(history_data),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            await websocket.send_text(history_msg.json())
            
        except Exception as e:
            logger.error(f"Metric history error: {e}")
            error_msg = create_error_message(f"History request failed: {str(e)}")
            await websocket.send_text(error_msg.json())
    
    async def _metrics_update_loop(self, connection_id: str, adapter: IAetheriusAdapter):
        """Background task to send periodic metric updates."""
        try:
            while connection_id in self.active_connections:
                interval = self.update_intervals.get(connection_id, 5)
                
                # Wait for the specified interval
                await asyncio.sleep(interval)
                
                # Check if connection still exists
                if connection_id not in self.active_connections:
                    break
                
                websocket = self.active_connections[connection_id]
                subscribed_metrics = self.metric_subscriptions.get(connection_id, set())
                
                if not subscribed_metrics:
                    continue
                
                try:
                    # Get performance data
                    performance_data = await adapter.get_performance_data()
                    
                    # Filter only subscribed metrics
                    filtered_data = {}
                    for metric in subscribed_metrics:
                        if metric in performance_data:
                            filtered_data[metric] = performance_data[metric]
                    
                    if filtered_data:
                        # Send performance update
                        update_msg = create_performance_update_message(
                            cpu_percent=filtered_data.get("cpu_percent", 0.0),
                            memory_mb=filtered_data.get("memory_mb", 0.0),
                            uptime_seconds=filtered_data.get("uptime_seconds", 0.0),
                            tps=filtered_data.get("tps", 20.0)
                        )
                        
                        await websocket.send_text(update_msg.json())
                        
                        # Update session info
                        self.user_sessions[connection_id]["last_update"] = datetime.now()
                
                except Exception as e:
                    logger.error(f"Metrics update error for {connection_id}: {e}")
                    # Don't break the loop for individual errors
                    continue
                    
        except asyncio.CancelledError:
            logger.info(f"Metrics update loop cancelled for {connection_id}")
        except Exception as e:
            logger.error(f"Metrics update loop error for {connection_id}: {e}")
    
    async def _cleanup_connection(self, connection_id: str, ws_manager: WebSocketManager):
        """Clean up connection resources."""
        try:
            # Cancel background task
            if connection_id in self.background_tasks:
                task = self.background_tasks[connection_id]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self.background_tasks[connection_id]
            
            # Remove from WebSocket manager
            await ws_manager.remove_connection(connection_id)
            
            # Clean up local tracking
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
            
            if connection_id in self.user_sessions:
                session = self.user_sessions[connection_id]
                logger.info(f"Monitoring session ended: {connection_id} "
                           f"(subscriptions: {len(session.get('subscriptions', []))})")
                del self.user_sessions[connection_id]
            
            if connection_id in self.metric_subscriptions:
                del self.metric_subscriptions[connection_id]
            
            if connection_id in self.update_intervals:
                del self.update_intervals[connection_id]
                
        except Exception as e:
            logger.error(f"Cleanup error for {connection_id}: {e}")


# Global handler instance
monitoring_handler = MonitoringWebSocketHandler()


async def websocket_monitoring(
    websocket: WebSocket,
    token: str,
    ws_manager: WebSocketManager = Depends(lambda: get_container().get_service(WebSocketManager)),
    adapter: IAetheriusAdapter = Depends(lambda: get_container().get_service(IAetheriusAdapter))
):
    """
    Monitoring WebSocket endpoint.
    
    Provides real-time metrics, dashboard updates, and system monitoring.
    Requires authentication token as query parameter.
    """
    try:
        # Authenticate user
        user = await get_current_user(token)
        if not user:
            await websocket.close(code=4001, reason="Authentication failed")
            return
        
        # Check monitoring permissions
        user_permissions = user.get("permissions", [])
        if "server.monitor" not in user_permissions:
            await websocket.close(code=4003, reason="Insufficient permissions")
            return
        
        # Handle the connection
        await monitoring_handler.handle_connection(
            websocket=websocket,
            user_id=str(user["id"]),
            ws_manager=await ws_manager,
            adapter=await adapter
        )
        
    except Exception as e:
        logger.error(f"Monitoring WebSocket endpoint error: {e}")
        try:
            await websocket.close(code=4000, reason="Internal server error")
        except:
            pass