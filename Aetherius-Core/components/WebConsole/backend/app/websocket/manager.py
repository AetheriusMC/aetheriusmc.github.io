"""
WebSocket connection manager for real-time communication.
"""

import asyncio
import json
import logging
from typing import Dict, List, Set, Optional, Any, Callable
from collections import defaultdict, deque
from datetime import datetime
import weakref

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from .models import WSMessage, WSMessageType, ConnectionType, create_ws_message
from ..core.config import settings
from ..core.container import singleton

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """Represents a WebSocket connection with metadata."""
    
    def __init__(
        self,
        websocket: WebSocket,
        connection_id: str,
        connection_type: ConnectionType = ConnectionType.GENERAL,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.websocket = websocket
        self.connection_id = connection_id
        self.connection_type = connection_type
        self.user_id = user_id
        self.metadata = metadata or {}
        self.connected_at = datetime.now()
        self.last_activity = datetime.now()
        self.message_count = 0
        self.is_active = True
        
        # Message queue for this connection
        self.message_queue: deque = deque(maxlen=settings.websocket.message_queue_size)
    
    async def send_message(self, message: WSMessage) -> bool:
        """Send message to this connection."""
        if not self.is_active:
            return False
        
        try:
            await self.websocket.send_text(message.json())
            self.message_count += 1
            self.last_activity = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Failed to send message to connection {self.connection_id}: {e}")
            self.is_active = False
            return False
    
    async def send_json(self, data: Dict[str, Any]) -> bool:
        """Send JSON data to this connection."""
        if not self.is_active:
            return False
        
        try:
            await self.websocket.send_json(data)
            self.message_count += 1
            self.last_activity = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Failed to send JSON to connection {self.connection_id}: {e}")
            self.is_active = False
            return False
    
    async def receive_message(self) -> Optional[WSMessage]:
        """Receive message from this connection."""
        try:
            data = await self.websocket.receive_text()
            self.last_activity = datetime.now()
            
            # Parse as WebSocket message
            message_data = json.loads(data)
            return WSMessage(**message_data)
            
        except WebSocketDisconnect:
            self.is_active = False
            return None
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Invalid message format from connection {self.connection_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error receiving message from connection {self.connection_id}: {e}")
            self.is_active = False
            return None
    
    async def close(self, code: int = 1000, reason: str = "Connection closed") -> None:
        """Close this connection."""
        try:
            if self.is_active:
                await self.websocket.close(code=code, reason=reason)
        except Exception as e:
            logger.error(f"Error closing connection {self.connection_id}: {e}")
        finally:
            self.is_active = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert connection to dictionary."""
        return {
            "connection_id": self.connection_id,
            "connection_type": self.connection_type.value,
            "user_id": self.user_id,
            "connected_at": self.connected_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "message_count": self.message_count,
            "is_active": self.is_active,
            "metadata": self.metadata
        }


@singleton
class WebSocketManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.connections_by_type: Dict[ConnectionType, Set[str]] = defaultdict(set)
        self.connections_by_user: Dict[str, Set[str]] = defaultdict(set)
        
        # Event handlers
        self.message_handlers: Dict[WSMessageType, List[Callable]] = defaultdict(list)
        
        # Statistics
        self.total_connections = 0
        self.total_messages_sent = 0
        self.total_messages_received = 0
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # Message history for new connections
        self.message_history: Dict[ConnectionType, deque] = {
            connection_type: deque(maxlen=100) 
            for connection_type in ConnectionType
        }
    
    async def initialize(self) -> None:
        """Initialize WebSocket manager."""
        # Start background tasks
        self._cleanup_task = asyncio.create_task(self._cleanup_inactive_connections())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_task_loop())
        
        logger.info("WebSocket manager initialized")
    
    async def dispose(self) -> None:
        """Dispose WebSocket manager."""
        # Cancel background tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        
        # Close all connections
        for connection in list(self.connections.values()):
            await connection.close(code=1001, reason="Server shutdown")
        
        self.connections.clear()
        self.connections_by_type.clear()
        self.connections_by_user.clear()
        
        logger.info("WebSocket manager disposed")
    
    async def add_connection(
        self,
        websocket: WebSocket,
        connection_id: str,
        connection_type: ConnectionType = ConnectionType.GENERAL,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> WebSocketConnection:
        """Add a new WebSocket connection."""
        
        # Check connection limits
        if len(self.connections) >= settings.websocket.max_connections:
            await websocket.close(code=1013, reason="Connection limit reached")
            raise RuntimeError("Maximum connections reached")
        
        # Create connection object
        connection = WebSocketConnection(
            websocket=websocket,
            connection_id=connection_id,
            connection_type=connection_type,
            user_id=user_id,
            metadata=metadata
        )
        
        # Store connection
        self.connections[connection_id] = connection
        self.connections_by_type[connection_type].add(connection_id)
        
        if user_id:
            self.connections_by_user[user_id].add(connection_id)
        
        self.total_connections += 1
        
        # Send recent message history to new connection
        await self._send_message_history(connection)
        
        logger.info(f"WebSocket connection added: {connection_id} (type: {connection_type.value}, user: {user_id})")
        
        return connection
    
    async def remove_connection(self, connection_id: str) -> None:
        """Remove a WebSocket connection."""
        connection = self.connections.get(connection_id)
        if not connection:
            return
        
        # Remove from indexes
        self.connections_by_type[connection.connection_type].discard(connection_id)
        
        if connection.user_id:
            self.connections_by_user[connection.user_id].discard(connection_id)
            # Clean up empty user set
            if not self.connections_by_user[connection.user_id]:
                del self.connections_by_user[connection.user_id]
        
        # Remove from main connections dict
        del self.connections[connection_id]
        
        logger.info(f"WebSocket connection removed: {connection_id}")
    
    async def send_message_to_connection(
        self, 
        connection_id: str, 
        message: WSMessage
    ) -> bool:
        """Send message to specific connection."""
        connection = self.connections.get(connection_id)
        if not connection or not connection.is_active:
            return False
        
        success = await connection.send_message(message)
        if success:
            self.total_messages_sent += 1
        else:
            # Mark for cleanup if send failed
            await self.remove_connection(connection_id)
        
        return success
    
    async def send_json_to_connection(
        self, 
        connection_id: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Send JSON data to specific connection."""
        connection = self.connections.get(connection_id)
        if not connection or not connection.is_active:
            return False
        
        success = await connection.send_json(data)
        if success:
            self.total_messages_sent += 1
        else:
            # Mark for cleanup if send failed
            await self.remove_connection(connection_id)
        
        return success
    
    async def broadcast_to_type(
        self, 
        connection_type: ConnectionType, 
        message: WSMessage
    ) -> int:
        """Broadcast message to all connections of specific type."""
        connection_ids = list(self.connections_by_type[connection_type])
        successful_sends = 0
        failed_connections = []
        
        for connection_id in connection_ids:
            connection = self.connections.get(connection_id)
            if not connection or not connection.is_active:
                failed_connections.append(connection_id)
                continue
            
            success = await connection.send_message(message)
            if success:
                successful_sends += 1
                self.total_messages_sent += 1
            else:
                failed_connections.append(connection_id)
        
        # Clean up failed connections
        for connection_id in failed_connections:
            await self.remove_connection(connection_id)
        
        # Store in message history
        self.message_history[connection_type].append(message)
        
        return successful_sends
    
    async def broadcast_to_user(
        self, 
        user_id: str, 
        message: WSMessage
    ) -> int:
        """Broadcast message to all connections of specific user."""
        connection_ids = list(self.connections_by_user.get(user_id, set()))
        successful_sends = 0
        failed_connections = []
        
        for connection_id in connection_ids:
            connection = self.connections.get(connection_id)
            if not connection or not connection.is_active:
                failed_connections.append(connection_id)
                continue
            
            success = await connection.send_message(message)
            if success:
                successful_sends += 1
                self.total_messages_sent += 1
            else:
                failed_connections.append(connection_id)
        
        # Clean up failed connections
        for connection_id in failed_connections:
            await self.remove_connection(connection_id)
        
        return successful_sends
    
    async def broadcast_to_all(self, message: WSMessage) -> int:
        """Broadcast message to all connections."""
        connection_ids = list(self.connections.keys())
        successful_sends = 0
        failed_connections = []
        
        for connection_id in connection_ids:
            connection = self.connections.get(connection_id)
            if not connection or not connection.is_active:
                failed_connections.append(connection_id)
                continue
            
            success = await connection.send_message(message)
            if success:
                successful_sends += 1
                self.total_messages_sent += 1
            else:
                failed_connections.append(connection_id)
        
        # Clean up failed connections
        for connection_id in failed_connections:
            await self.remove_connection(connection_id)
        
        # Store in all message histories
        for connection_type in ConnectionType:
            self.message_history[connection_type].append(message)
        
        return successful_sends
    
    async def handle_message(
        self, 
        connection_id: str, 
        message: WSMessage
    ) -> None:
        """Handle incoming message from connection."""
        self.total_messages_received += 1
        
        # Update connection activity
        connection = self.connections.get(connection_id)
        if connection:
            connection.last_activity = datetime.now()
        
        # Handle specific message types
        if message.type == WSMessageType.PING:
            # Respond with pong
            pong_message = create_ws_message(WSMessageType.PONG, {"timestamp": datetime.now().isoformat()})
            await self.send_message_to_connection(connection_id, pong_message)
            return
        
        # Call registered handlers
        handlers = self.message_handlers.get(message.type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(connection_id, message)
                else:
                    handler(connection_id, message)
            except Exception as e:
                logger.error(f"Error in message handler for {message.type}: {e}")
    
    def register_message_handler(
        self, 
        message_type: WSMessageType, 
        handler: Callable
    ) -> None:
        """Register message handler."""
        self.message_handlers[message_type].append(handler)
    
    def unregister_message_handler(
        self, 
        message_type: WSMessageType, 
        handler: Callable
    ) -> None:
        """Unregister message handler."""
        if handler in self.message_handlers[message_type]:
            self.message_handlers[message_type].remove(handler)
    
    async def _send_message_history(self, connection: WebSocketConnection) -> None:
        """Send recent message history to new connection."""
        history = self.message_history.get(connection.connection_type, deque())
        
        for message in list(history)[-10:]:  # Send last 10 messages
            await connection.send_message(message)
    
    async def _cleanup_inactive_connections(self) -> None:
        """Background task to cleanup inactive connections."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                current_time = datetime.now()
                inactive_connections = []
                
                for connection_id, connection in self.connections.items():
                    # Check if connection is inactive (no activity for 5 minutes)
                    time_since_activity = current_time - connection.last_activity
                    if time_since_activity.total_seconds() > 300 or not connection.is_active:
                        inactive_connections.append(connection_id)
                
                # Clean up inactive connections
                for connection_id in inactive_connections:
                    connection = self.connections.get(connection_id)
                    if connection:
                        await connection.close(code=1001, reason="Inactive connection")
                        await self.remove_connection(connection_id)
                
                if inactive_connections:
                    logger.info(f"Cleaned up {len(inactive_connections)} inactive connections")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in connection cleanup task: {e}")
    
    async def _heartbeat_task_loop(self) -> None:
        """Background task to send heartbeat messages."""
        while True:
            try:
                await asyncio.sleep(settings.websocket.heartbeat_interval)
                
                # Send ping to all connections
                ping_message = create_ws_message(
                    WSMessageType.PING, 
                    {"timestamp": datetime.now().isoformat()}
                )
                
                await self.broadcast_to_all(ping_message)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat task: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        active_connections = len([c for c in self.connections.values() if c.is_active])
        
        connections_by_type = {
            connection_type.value: len(connection_ids)
            for connection_type, connection_ids in self.connections_by_type.items()
        }
        
        return {
            "total_connections": self.total_connections,
            "active_connections": active_connections,
            "connections_by_type": connections_by_type,
            "unique_users": len(self.connections_by_user),
            "total_messages_sent": self.total_messages_sent,
            "total_messages_received": self.total_messages_received
        }
    
    def get_active_connections(self) -> List[Dict[str, Any]]:
        """Get list of active connections."""
        return [
            connection.to_dict()
            for connection in self.connections.values()
            if connection.is_active
        ]