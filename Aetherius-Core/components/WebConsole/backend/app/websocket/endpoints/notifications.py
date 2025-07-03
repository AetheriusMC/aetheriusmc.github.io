"""
WebSocket endpoint for notifications and alerts.
Handles system-wide notifications, user-specific alerts, and real-time messaging.
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect
import logging
from ..manager import WebSocketManager, ConnectionType
from ...core.container import DIContainer
from ...core.aetherius_adapter import IAetheriusAdapter

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Notification types."""
    SYSTEM = "system"
    SECURITY = "security"
    PLAYER = "player"
    SERVER = "server"
    MAINTENANCE = "maintenance"
    ALERT = "alert"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationWebSocketHandler:
    """Handles WebSocket connections for notifications and alerts."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_subscriptions: Dict[str, Set[NotificationType]] = {}
        self.notification_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        
    async def handle_connection(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: str,
        container: DIContainer
    ):
        """Handle new notification WebSocket connection."""
        try:
            await websocket.accept()
            self.active_connections[connection_id] = websocket
            self.user_subscriptions[connection_id] = set(NotificationType)
            
            adapter = container.get(IAetheriusAdapter)
            ws_manager = container.get(WebSocketManager)
            
            logger.info(f"Notifications WebSocket connected: {connection_id}")
            
            # Send recent notification history
            await self._send_notification_history(connection_id)
            
            # Send connection confirmation
            await self._send_message(connection_id, {
                "type": "connection_established",
                "timestamp": datetime.utcnow().isoformat(),
                "subscriptions": list(self.user_subscriptions[connection_id])
            })
            
            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    await self._handle_message(connection_id, message, adapter, ws_manager)
                except WebSocketDisconnect:
                    break
                except json.JSONDecodeError:
                    await self._send_error(connection_id, "Invalid JSON format")
                except Exception as e:
                    logger.error(f"Error handling notification message: {e}")
                    await self._send_error(connection_id, f"Message handling error: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Notification WebSocket error: {e}")
        finally:
            await self._cleanup_connection(connection_id)
    
    async def _handle_message(
        self,
        connection_id: str,
        message: Dict[str, Any],
        adapter: IAetheriusAdapter,
        ws_manager: WebSocketManager
    ):
        """Handle incoming WebSocket messages."""
        message_type = message.get("type")
        
        if message_type == "subscribe":
            await self._handle_subscription(connection_id, message)
        elif message_type == "unsubscribe":
            await self._handle_unsubscription(connection_id, message)
        elif message_type == "mark_read":
            await self._handle_mark_read(connection_id, message)
        elif message_type == "get_history":
            await self._handle_get_history(connection_id, message)
        elif message_type == "send_notification":
            await self._handle_send_notification(connection_id, message, adapter, ws_manager)
        else:
            await self._send_error(connection_id, f"Unknown message type: {message_type}")
    
    async def _handle_subscription(self, connection_id: str, data: Dict[str, Any]):
        """Handle notification subscription request."""
        try:
            notification_types = data.get("notification_types", [])
            
            if not notification_types:
                self.user_subscriptions[connection_id] = set(NotificationType)
            else:
                valid_types = {nt for nt in notification_types if nt in NotificationType.__members__.values()}
                self.user_subscriptions[connection_id] = valid_types
            
            await self._send_message(connection_id, {
                "type": "subscription_updated",
                "subscriptions": list(self.user_subscriptions[connection_id]),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Updated subscriptions for {connection_id}: {self.user_subscriptions[connection_id]}")
            
        except Exception as e:
            logger.error(f"Error handling subscription: {e}")
            await self._send_error(connection_id, f"Subscription error: {str(e)}")
    
    async def _handle_unsubscription(self, connection_id: str, data: Dict[str, Any]):
        """Handle notification unsubscription request."""
        try:
            notification_types = data.get("notification_types", [])
            
            if connection_id in self.user_subscriptions:
                for nt in notification_types:
                    self.user_subscriptions[connection_id].discard(nt)
            
            await self._send_message(connection_id, {
                "type": "subscription_updated",
                "subscriptions": list(self.user_subscriptions.get(connection_id, [])),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error handling unsubscription: {e}")
            await self._send_error(connection_id, f"Unsubscription error: {str(e)}")
    
    async def _handle_mark_read(self, connection_id: str, data: Dict[str, Any]):
        """Handle mark notification as read request."""
        try:
            notification_ids = data.get("notification_ids", [])
            
            # Update notification read status in history
            for notification in self.notification_history:
                if notification.get("id") in notification_ids:
                    if "read_by" not in notification:
                        notification["read_by"] = []
                    if connection_id not in notification["read_by"]:
                        notification["read_by"].append(connection_id)
            
            await self._send_message(connection_id, {
                "type": "notifications_marked_read",
                "notification_ids": notification_ids,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error marking notifications as read: {e}")
            await self._send_error(connection_id, f"Mark read error: {str(e)}")
    
    async def _handle_get_history(self, connection_id: str, data: Dict[str, Any]):
        """Handle get notification history request."""
        try:
            limit = data.get("limit", 50)
            offset = data.get("offset", 0)
            notification_types = data.get("notification_types", [])
            
            filtered_history = self.notification_history
            
            # Filter by notification types if specified
            if notification_types:
                filtered_history = [
                    n for n in filtered_history 
                    if n.get("notification_type") in notification_types
                ]
            
            # Apply pagination
            paginated_history = filtered_history[offset:offset + limit]
            
            await self._send_message(connection_id, {
                "type": "notification_history",
                "notifications": paginated_history,
                "total": len(filtered_history),
                "limit": limit,
                "offset": offset,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting notification history: {e}")
            await self._send_error(connection_id, f"History error: {str(e)}")
    
    async def _handle_send_notification(
        self,
        connection_id: str,
        data: Dict[str, Any],
        adapter: IAetheriusAdapter,
        ws_manager: WebSocketManager
    ):
        """Handle send notification request (admin only)."""
        try:
            # Create notification
            notification = {
                "id": f"notif_{datetime.utcnow().timestamp()}",
                "title": data.get("title", ""),
                "message": data.get("message", ""),
                "notification_type": data.get("notification_type", NotificationType.INFO),
                "priority": data.get("priority", NotificationPriority.MEDIUM),
                "sender": connection_id,
                "timestamp": datetime.utcnow().isoformat(),
                "read_by": []
            }
            
            # Add to history
            await self._add_to_history(notification)
            
            # Broadcast to all subscribed connections
            await self._broadcast_notification(notification)
            
            await self._send_message(connection_id, {
                "type": "notification_sent",
                "notification_id": notification["id"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            await self._send_error(connection_id, f"Send notification error: {str(e)}")
    
    async def _send_notification_history(self, connection_id: str):
        """Send recent notification history to newly connected client."""
        try:
            recent_notifications = self.notification_history[-20:] if self.notification_history else []
            
            await self._send_message(connection_id, {
                "type": "notification_history",
                "notifications": recent_notifications,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error sending notification history: {e}")
    
    async def _add_to_history(self, notification: Dict[str, Any]):
        """Add notification to history with size limit."""
        self.notification_history.append(notification)
        
        # Maintain history size limit
        if len(self.notification_history) > self.max_history_size:
            self.notification_history = self.notification_history[-self.max_history_size:]
    
    async def _broadcast_notification(self, notification: Dict[str, Any]):
        """Broadcast notification to all subscribed connections."""
        notification_type = notification.get("notification_type")
        
        for connection_id, subscriptions in self.user_subscriptions.items():
            if notification_type in subscriptions and connection_id in self.active_connections:
                try:
                    await self._send_message(connection_id, {
                        "type": "notification",
                        "notification": notification
                    })
                except Exception as e:
                    logger.error(f"Error broadcasting to {connection_id}: {e}")
    
    async def broadcast_system_notification(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.SYSTEM,
        priority: NotificationPriority = NotificationPriority.MEDIUM
    ):
        """Broadcast system-wide notification."""
        notification = {
            "id": f"sys_{datetime.utcnow().timestamp()}",
            "title": title,
            "message": message,
            "notification_type": notification_type,
            "priority": priority,
            "sender": "system",
            "timestamp": datetime.utcnow().isoformat(),
            "read_by": []
        }
        
        await self._add_to_history(notification)
        await self._broadcast_notification(notification)
    
    async def _send_message(self, connection_id: str, message: Dict[str, Any]):
        """Send message to specific connection."""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                await self._cleanup_connection(connection_id)
    
    async def _send_error(self, connection_id: str, error_message: str):
        """Send error message to connection."""
        await self._send_message(connection_id, {
            "type": "error",
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _cleanup_connection(self, connection_id: str):
        """Clean up connection resources."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if connection_id in self.user_subscriptions:
            del self.user_subscriptions[connection_id]
        
        logger.info(f"Cleaned up notification connection: {connection_id}")


# Global handler instance
notification_handler = NotificationWebSocketHandler()