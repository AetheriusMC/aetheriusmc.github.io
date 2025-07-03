"""
Console WebSocket endpoint for real-time command execution and log streaming.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException

from ...core.container import get_container
from ...core.aetherius_adapter import IAetheriusAdapter
from ...utils.security import get_current_user
from ..manager import WebSocketManager
from ..models import (
    ConnectionType, WSMessage, WSMessageType,
    create_console_log_message, create_error_message,
    create_notification_message, create_ws_message
)

logger = logging.getLogger(__name__)


class ConsoleWebSocketHandler:
    """Handle console WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def handle_connection(
        self,
        websocket: WebSocket,
        user_id: str,
        ws_manager: WebSocketManager,
        adapter: IAetheriusAdapter
    ):
        """Handle a new console WebSocket connection."""
        try:
            # Accept the connection
            await websocket.accept()
            
            # Register connection with WebSocket manager
            connection_id = await ws_manager.add_connection(
                websocket=websocket,
                user_id=user_id,
                connection_type=ConnectionType.CONSOLE
            )
            
            # Store connection info
            self.active_connections[connection_id] = websocket
            self.user_sessions[connection_id] = {
                "user_id": user_id,
                "connected_at": datetime.now(),
                "command_count": 0
            }
            
            logger.info(f"Console WebSocket connected: {connection_id} (user: {user_id})")
            
            # Send welcome message
            welcome_msg = create_console_log_message(
                level="INFO",
                message="Console connected successfully",
                source="system"
            )
            await websocket.send_text(welcome_msg.json())
            
            # Listen for messages
            await self._handle_messages(connection_id, websocket, adapter, ws_manager)
            
        except WebSocketDisconnect:
            await self._cleanup_connection(connection_id, ws_manager)
        except Exception as e:
            logger.error(f"Console WebSocket error: {e}")
            await self._cleanup_connection(connection_id, ws_manager)
    
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
            logger.info(f"Console WebSocket disconnected: {connection_id}")
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
        
        session = self.user_sessions.get(connection_id, {})
        websocket = self.active_connections.get(connection_id)
        
        if not websocket:
            return
        
        if message_type == "execute_command":
            await self._handle_command_execution(connection_id, data, adapter, ws_manager)
        
        elif message_type == "subscribe_logs":
            await self._handle_log_subscription(connection_id, data, adapter)
        
        elif message_type == "get_history":
            await self._handle_history_request(connection_id, data, websocket)
        
        elif message_type == "ping":
            # Respond to ping with pong
            pong_msg = create_ws_message(WSMessageType.PONG, {"timestamp": datetime.now().isoformat()})
            await websocket.send_text(pong_msg.json())
        
        else:
            error_msg = create_error_message(f"Unknown message type: {message_type}")
            await websocket.send_text(error_msg.json())
    
    async def _handle_command_execution(
        self,
        connection_id: str,
        data: Dict[str, Any],
        adapter: IAetheriusAdapter,
        ws_manager: WebSocketManager
    ):
        """Handle command execution request."""
        command = data.get("command", "").strip()
        if not command:
            error_msg = create_error_message("Command cannot be empty")
            await self.active_connections[connection_id].send_text(error_msg.json())
            return
        
        session = self.user_sessions[connection_id]
        websocket = self.active_connections[connection_id]
        
        try:
            # Update session stats
            session["command_count"] += 1
            session["last_command"] = command
            session["last_command_time"] = datetime.now()
            
            # Log command execution
            command_log = create_console_log_message(
                level="INFO",
                message=f"[{session['user_id']}] > {command}",
                source="console"
            )
            
            # Broadcast command to all console connections
            await ws_manager.broadcast_to_type(ConnectionType.CONSOLE, command_log)
            
            # Execute command through adapter
            result = await adapter.send_command(command)
            
            if result.get("success"):
                # Send command output
                if result.get("output"):
                    output_log = create_console_log_message(
                        level="INFO",
                        message=result["output"],
                        source="server"
                    )
                    await ws_manager.broadcast_to_type(ConnectionType.CONSOLE, output_log)
                
                # Send success confirmation to the sender
                success_msg = create_ws_message(
                    WSMessageType.COMMAND_RESULT,
                    {
                        "success": True,
                        "command": command,
                        "output": result.get("output"),
                        "timestamp": datetime.now().isoformat()
                    }
                )
                await websocket.send_text(success_msg.json())
                
            else:
                # Send error response
                error_log = create_console_log_message(
                    level="ERROR", 
                    message=f"Command failed: {result.get('error', 'Unknown error')}",
                    source="server"
                )
                await ws_manager.broadcast_to_type(ConnectionType.CONSOLE, error_log)
                
                error_msg = create_ws_message(
                    WSMessageType.COMMAND_RESULT,
                    {
                        "success": False,
                        "command": command,
                        "error": result.get("error"),
                        "timestamp": datetime.now().isoformat()
                    }
                )
                await websocket.send_text(error_msg.json())
                
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            error_msg = create_error_message(f"Command execution failed: {str(e)}")
            await websocket.send_text(error_msg.json())
    
    async def _handle_log_subscription(
        self,
        connection_id: str,
        data: Dict[str, Any],
        adapter: IAetheriusAdapter
    ):
        """Handle log subscription request."""
        websocket = self.active_connections[connection_id]
        log_level = data.get("level", "INFO")
        
        try:
            # TODO: Implement log streaming from server
            # For now, send confirmation
            confirmation = create_ws_message(
                WSMessageType.LOG_SUBSCRIPTION,
                {
                    "subscribed": True,
                    "level": log_level,
                    "message": f"Subscribed to {log_level} level logs",
                    "timestamp": datetime.now().isoformat()
                }
            )
            await websocket.send_text(confirmation.json())
            
        except Exception as e:
            logger.error(f"Log subscription error: {e}")
            error_msg = create_error_message(f"Log subscription failed: {str(e)}")
            await websocket.send_text(error_msg.json())
    
    async def _handle_history_request(
        self,
        connection_id: str,
        data: Dict[str, Any],
        websocket: WebSocket
    ):
        """Handle command history request."""
        try:
            limit = data.get("limit", 50)
            
            # TODO: Get actual command history from database
            # For now, return mock history
            mock_history = [
                {
                    "id": i,
                    "command": f"example command {i}",
                    "user": "admin",
                    "timestamp": datetime.now().isoformat(),
                    "success": True
                }
                for i in range(1, min(limit + 1, 11))
            ]
            
            history_msg = create_ws_message(
                WSMessageType.COMMAND_HISTORY,
                {
                    "history": mock_history,
                    "total": len(mock_history),
                    "timestamp": datetime.now().isoformat()
                }
            )
            await websocket.send_text(history_msg.json())
            
        except Exception as e:
            logger.error(f"History request error: {e}")
            error_msg = create_error_message(f"History request failed: {str(e)}")
            await websocket.send_text(error_msg.json())
    
    async def _cleanup_connection(self, connection_id: str, ws_manager: WebSocketManager):
        """Clean up connection resources."""
        try:
            # Remove from WebSocket manager
            await ws_manager.remove_connection(connection_id)
            
            # Clean up local tracking
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
            
            if connection_id in self.user_sessions:
                session = self.user_sessions[connection_id]
                logger.info(f"Console session ended: {connection_id} "
                           f"(commands: {session.get('command_count', 0)})")
                del self.user_sessions[connection_id]
                
        except Exception as e:
            logger.error(f"Cleanup error for {connection_id}: {e}")


# Global handler instance
console_handler = ConsoleWebSocketHandler()


async def websocket_console(
    websocket: WebSocket,
    token: str,
    ws_manager: WebSocketManager = Depends(lambda: get_container().get_service(WebSocketManager)),
    adapter: IAetheriusAdapter = Depends(lambda: get_container().get_service(IAetheriusAdapter))
):
    """
    Console WebSocket endpoint.
    
    Provides real-time command execution and log streaming.
    Requires authentication token as query parameter.
    """
    try:
        # Authenticate user
        user = await get_current_user(token)
        if not user:
            await websocket.close(code=4001, reason="Authentication failed")
            return
        
        # Check console permissions
        user_permissions = user.get("permissions", [])
        if "console.execute" not in user_permissions:
            await websocket.close(code=4003, reason="Insufficient permissions")
            return
        
        # Handle the connection
        await console_handler.handle_connection(
            websocket=websocket,
            user_id=str(user["id"]),
            ws_manager=await ws_manager,
            adapter=await adapter
        )
        
    except Exception as e:
        logger.error(f"Console WebSocket endpoint error: {e}")
        try:
            await websocket.close(code=4000, reason="Internal server error")
        except:
            pass