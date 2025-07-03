"""
WebSocket Connection Manager
===========================

Manages WebSocket connections and message broadcasting.
"""

import asyncio
import json
from typing import List, Dict, Set, Any, Optional
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from app.utils.logging import get_logger
from app.utils.exceptions import WebSocketError

logger = get_logger(__name__)


class ConnectionType(Enum):
    """WebSocket connection types"""
    CONSOLE = "console"
    STATUS = "status"
    EVENTS = "events"
    DASHBOARD = "dashboard"


@dataclass
class WSConnection:
    """WebSocket connection information"""
    websocket: WebSocket
    connection_id: str
    connection_type: ConnectionType
    connected_at: datetime
    client_info: Optional[Dict[str, Any]] = None


@dataclass
class WSMessage:
    """WebSocket message structure"""
    type: str
    timestamp: datetime
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "type": self.type,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data
        }


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting"""
    
    def __init__(self):
        self.connections: Dict[str, WSConnection] = {}
        self.connections_by_type: Dict[ConnectionType, Set[str]] = {
            ConnectionType.CONSOLE: set(),
            ConnectionType.STATUS: set(),
            ConnectionType.EVENTS: set(),
            ConnectionType.DASHBOARD: set(),
        }
        self._lock = None  # Will be initialized when first used
        self._message_queue = None  # Will be initialized when first used
        self._queue_processor_task: Optional[asyncio.Task] = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure the manager is initialized with event loop"""
        if not self._initialized:
            self._lock = asyncio.Lock()
            self._message_queue = asyncio.Queue()
            self._initialized = True
            self._start_queue_processor()
    
    def _start_queue_processor(self):
        """Start the message queue processor"""
        if self._queue_processor_task is None or self._queue_processor_task.done():
            self._queue_processor_task = asyncio.create_task(self._process_message_queue())
    
    async def _process_message_queue(self):
        """Process messages from the queue"""
        while True:
            try:
                message_data = await self._message_queue.get()
                await self._broadcast_message(**message_data)
                self._message_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error processing message queue", error=str(e), exc_info=True)
    
    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        connection_type: ConnectionType,
        client_info: Optional[Dict[str, Any]] = None
    ):
        """
        Accept a new WebSocket connection
        
        Args:
            websocket: WebSocket connection
            connection_id: Unique connection identifier
            connection_type: Type of connection
            client_info: Optional client information
        """
        await self._ensure_initialized()
        
        try:
            await websocket.accept()
            
            async with self._lock:
                connection = WSConnection(
                    websocket=websocket,
                    connection_id=connection_id,
                    connection_type=connection_type,
                    connected_at=datetime.now(),
                    client_info=client_info or {}
                )
                
                self.connections[connection_id] = connection
                self.connections_by_type[connection_type].add(connection_id)
            
            logger.info(
                "WebSocket connection established",
                connection_id=connection_id,
                connection_type=connection_type.value,
                client_info=client_info
            )
            
            # Send welcome message
            await self.send_to_connection(
                connection_id,
                WSMessage(
                    type="connection_established",
                    timestamp=datetime.now(),
                    data={
                        "connection_id": connection_id,
                        "connection_type": connection_type.value,
                        "server_time": datetime.now().isoformat()
                    }
                )
            )
            
        except Exception as e:
            logger.error(
                "Failed to establish WebSocket connection",
                connection_id=connection_id,
                error=str(e),
                exc_info=True
            )
            raise WebSocketError(f"Failed to establish connection: {e}")
    
    async def disconnect(self, connection_id: str):
        """
        Remove a WebSocket connection
        
        Args:
            connection_id: Connection identifier to remove
        """
        await self._ensure_initialized()
        async with self._lock:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                
                # Remove from type-specific sets
                self.connections_by_type[connection.connection_type].discard(connection_id)
                
                # Remove from main connections dict
                del self.connections[connection_id]
                
                logger.info(
                    "WebSocket connection removed",
                    connection_id=connection_id,
                    connection_type=connection.connection_type.value
                )
    
    async def send_to_connection(self, connection_id: str, message: WSMessage):
        """
        Send message to a specific connection
        
        Args:
            connection_id: Target connection ID
            message: Message to send
        """
        if connection_id not in self.connections:
            logger.warning("Attempted to send to non-existent connection", connection_id=connection_id)
            return
        
        connection = self.connections[connection_id]
        try:
            await connection.websocket.send_json(message.to_dict())
            logger.debug(
                "Message sent to connection",
                connection_id=connection_id,
                message_type=message.type
            )
        except Exception as e:
            logger.error(
                "Failed to send message to connection",
                connection_id=connection_id,
                error=str(e),
                exc_info=True
            )
            # Remove dead connection
            await self.disconnect(connection_id)
    
    async def broadcast_to_type(self, connection_type: ConnectionType, message: WSMessage):
        """
        Broadcast message to all connections of a specific type
        
        Args:
            connection_type: Type of connections to broadcast to
            message: Message to broadcast
        """
        await self._ensure_initialized()
        # Queue the message for processing
        await self._message_queue.put({
            "connection_type": connection_type,
            "message": message
        })
    
    async def _broadcast_message(self, connection_type: ConnectionType, message: WSMessage):
        """
        Internal method to broadcast message
        
        Args:
            connection_type: Type of connections to broadcast to
            message: Message to broadcast
        """
        # Add type checking for debugging
        if not isinstance(message, WSMessage):
            logger.error(f"Invalid message type: {type(message)}, expected WSMessage. Message content: {message}")
            # Try to convert dict to WSMessage if possible
            if isinstance(message, dict) and "type" in message:
                try:
                    message = WSMessage(
                        type=message["type"],
                        timestamp=datetime.now(),
                        data=message.get("data", {})
                    )
                    logger.warning("Converted dict message to WSMessage")
                except Exception as e:
                    logger.error(f"Failed to convert dict to WSMessage: {e}")
                    return
            else:
                logger.error("Cannot convert message to WSMessage format")
                return
        
        connection_ids = list(self.connections_by_type[connection_type])
        
        if not connection_ids:
            logger.debug("No connections to broadcast to", connection_type=connection_type.value)
            return
        
        logger.debug(
            "Broadcasting message",
            connection_type=connection_type.value,
            connection_count=len(connection_ids),
            message_type=message.type
        )
        
        # Send to all connections concurrently
        tasks = [
            self.send_to_connection(conn_id, message)
            for conn_id in connection_ids
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self.connections)
    
    def get_connection_count_by_type(self, connection_type: ConnectionType) -> int:
        """Get number of connections by type"""
        return len(self.connections_by_type[connection_type])
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": self.get_connection_count(),
            "connections_by_type": {
                conn_type.value: len(conn_ids)
                for conn_type, conn_ids in self.connections_by_type.items()
            },
            "queue_size": self._message_queue.qsize() if self._message_queue else 0
        }
    
    async def cleanup(self):
        """Cleanup all connections and tasks"""
        logger.info("Starting WebSocket manager cleanup")
        
        if not self._initialized:
            return
        
        # Cancel queue processor
        if self._queue_processor_task and not self._queue_processor_task.done():
            self._queue_processor_task.cancel()
            try:
                await self._queue_processor_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        async with self._lock:
            connection_ids = list(self.connections.keys())
            for connection_id in connection_ids:
                try:
                    connection = self.connections[connection_id]
                    await connection.websocket.close()
                except Exception as e:
                    logger.warning(
                        "Error closing WebSocket connection",
                        connection_id=connection_id,
                        error=str(e)
                    )
            
            self.connections.clear()
            for conn_set in self.connections_by_type.values():
                conn_set.clear()
        
        logger.info("WebSocket manager cleanup completed")


# Convenience functions for common message types
def create_console_message(level: str, message: str, source: str = "Server") -> WSMessage:
    """Create a console log message"""
    return WSMessage(
        type="console_log",
        timestamp=datetime.now(),
        data={
            "level": level,
            "message": message,
            "source": source
        }
    )


def create_status_message(status_data: Dict[str, Any]) -> WSMessage:
    """Create a status update message"""
    return WSMessage(
        type="status_update",
        timestamp=datetime.now(),
        data=status_data
    )


def create_player_event_message(event_type: str, player_data: Dict[str, Any]) -> WSMessage:
    """Create a player event message"""
    return WSMessage(
        type="player_event",
        timestamp=datetime.now(),
        data={
            "event_type": event_type,
            "player": player_data
        }
    )


def create_performance_message(performance_data: Dict[str, Any]) -> WSMessage:
    """Create a performance update message"""
    return WSMessage(
        type="performance_update",
        timestamp=datetime.now(),
        data=performance_data
    )


def create_dashboard_summary_message(summary_data: Dict[str, Any]) -> WSMessage:
    """Create a dashboard summary message"""
    return WSMessage(
        type="dashboard_summary",
        timestamp=datetime.now(),
        data=summary_data
    )


def create_server_control_message(action: str, result: Dict[str, Any]) -> WSMessage:
    """Create a server control result message"""
    return WSMessage(
        type="server_control_result",
        timestamp=datetime.now(),
        data={
            "action": action,
            "result": result
        }
    )


def create_console_command_result_message(command: str, success: bool, output: str) -> WSMessage:
    """Create a console command result message"""
    return WSMessage(
        type="console_command_result",
        timestamp=datetime.now(),
        data={
            "command": command,
            "success": success,
            "output": output
        }
    )