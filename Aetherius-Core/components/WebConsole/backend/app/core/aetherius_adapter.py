"""
Aetherius Core integration adapter.

This module provides the integration layer between WebConsole and Aetherius Core,
handling all communication with the core engine.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from abc import ABC, abstractmethod

# Type stubs for events (we'll use simple console client instead)
class BaseEvent:
    pass

AetheriusException = Exception

from ..core.config import settings
from ..core.container import singleton

logger = logging.getLogger(__name__)


class IAetheriusAdapter(ABC):
    """Aetherius adapter interface."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize adapter."""
        pass
    
    @abstractmethod
    async def get_server_status(self) -> Dict[str, Any]:
        """Get server status."""
        pass
    
    @abstractmethod
    async def send_command(self, command: str) -> Dict[str, Any]:
        """Send console command."""
        pass
    
    @abstractmethod
    async def get_online_players(self) -> List[Dict[str, Any]]:
        """Get online players."""
        pass
    
    @abstractmethod
    async def get_player_info(self, player_identifier: str) -> Optional[Dict[str, Any]]:
        """Get player information."""
        pass


@singleton
class AetheriusAdapter(IAetheriusAdapter):
    """Real Aetherius Core adapter implementation using console client."""
    
    def __init__(self):
        self.console_client: Optional[ConsoleClient] = None
        # 从环境变量获取socket路径
        self.socket_path = os.environ.get("AETHERIUS_CONSOLE_SOCKET", 
                                         "/workspaces/aetheriusmc.github.io/Aetherius-Core/data/console/console.sock")
        self.initialized = False
        self.event_callbacks: Dict[str, List[Callable]] = {}
        
        # Don't raise error here - we'll handle connection in initialize()
    
    async def initialize(self) -> None:
        """Initialize Aetherius Core adapter using console client."""
        try:
            # 使用简化的控制台客户端
            from .simple_console_client import SimpleConsoleClient
            
            socket_path = Path(self.socket_path)
            if not socket_path.exists():
                raise RuntimeError(f"Aetherius console socket not found at {self.socket_path}")
            
            # Create console client
            self.console_client = SimpleConsoleClient(str(socket_path))
            
            # Test connection
            connected = await self.console_client.connect()
            if not connected:
                raise RuntimeError("Failed to connect to Aetherius console")
            
            # Test basic command
            test_response = await self.console_client.send_command("!status")
            if not test_response.get("success"):
                logger.warning("Failed to test Aetherius console connection")
            else:
                logger.info("Successfully tested Aetherius console connection")
            
            self.initialized = True
            logger.info("Aetherius Core adapter initialized successfully via console client")
            
        except Exception as e:
            logger.error(f"Failed to initialize Aetherius Core adapter: {e}")
            raise
    
    async def dispose(self) -> None:
        """Dispose adapter."""
        if self.console_client:
            await self.console_client.disconnect()
        self.initialized = False
        logger.info("Aetherius Core adapter disposed")
    
    async def _register_event_listeners(self) -> None:
        """Register event listeners with Aetherius Core."""
        # Event listening through console client is simplified
        # We'll implement this when needed
        logger.info("Event listening via console client (simplified)")
    
    # Event handlers
    async def _on_server_start(self, event: BaseEvent) -> None:
        """Handle server start event."""
        await self._broadcast_event("server_start", {
            "status": "running",
            "timestamp": datetime.now().isoformat()
        })
    
    async def _on_server_stop(self, event: BaseEvent) -> None:
        """Handle server stop event."""
        await self._broadcast_event("server_stop", {
            "status": "stopped",
            "timestamp": datetime.now().isoformat()
        })
    
    async def _on_server_crash(self, event: BaseEvent) -> None:
        """Handle server crash event."""
        await self._broadcast_event("server_crash", {
            "status": "crashed",
            "error": getattr(event, 'error', 'Unknown error'),
            "timestamp": datetime.now().isoformat()
        })
    
    async def _on_player_join(self, event: BaseEvent) -> None:
        """Handle player join event."""
        await self._broadcast_event("player_join", {
            "player": getattr(event, 'player', {}),
            "timestamp": datetime.now().isoformat()
        })
    
    async def _on_player_leave(self, event: BaseEvent) -> None:
        """Handle player leave event."""
        await self._broadcast_event("player_leave", {
            "player": getattr(event, 'player', {}),
            "timestamp": datetime.now().isoformat()
        })
    
    async def _on_player_chat(self, event: BaseEvent) -> None:
        """Handle player chat event."""
        await self._broadcast_event("player_chat", {
            "player": getattr(event, 'player', {}),
            "message": getattr(event, 'message', ''),
            "timestamp": datetime.now().isoformat()
        })
    
    async def _on_console_log(self, event: BaseEvent) -> None:
        """Handle console log event."""
        await self._broadcast_event("console_log", {
            "level": getattr(event, 'level', 'INFO'),
            "message": getattr(event, 'message', ''),
            "source": getattr(event, 'source', 'server'),
            "timestamp": datetime.now().isoformat()
        })
    
    async def _on_performance_update(self, event: BaseEvent) -> None:
        """Handle performance update event."""
        await self._broadcast_event("performance_update", {
            "metrics": getattr(event, 'metrics', {}),
            "timestamp": datetime.now().isoformat()
        })
    
    async def _broadcast_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast event to registered callbacks."""
        callbacks = self.event_callbacks.get(event_type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, data)
                else:
                    callback(event_type, data)
            except Exception as e:
                logger.error(f"Error in event callback for {event_type}: {e}")
    
    def register_event_callback(self, event_type: str, callback: Callable) -> None:
        """Register event callback."""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)
    
    def unregister_event_callback(self, event_type: str, callback: Callable) -> None:
        """Unregister event callback."""
        if event_type in self.event_callbacks:
            try:
                self.event_callbacks[event_type].remove(callback)
            except ValueError:
                pass
    
    # Core API methods
    async def get_server_status(self) -> Dict[str, Any]:
        """Get server status from Aetherius Core via console."""
        if not self.initialized or not self.console_client:
            raise RuntimeError("Adapter not initialized")
        
        try:
            # Get status using Aetherius command
            response = await self.console_client.send_command("!status")
            
            if response.get("success"):
                # Parse the status output (simplified)
                return {
                    "status": "running",
                    "uptime": 0,  # Will be parsed from actual output
                    "version": "unknown",
                    "online_players": 0,
                    "max_players": 20,
                    "timestamp": datetime.now().isoformat(),
                    "raw_output": response.get("message", "")
                }
            else:
                return {
                    "status": "unknown",
                    "error": response.get("error", "Unknown error"),
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Failed to get server status: {e}")
            raise
    
    async def send_command(self, command: str) -> Dict[str, Any]:
        """Send console command to Aetherius Core via console client."""
        if not self.initialized or not self.console_client:
            raise RuntimeError("Adapter not initialized")
        
        try:
            # Send command (add / prefix for Minecraft commands if not already prefixed)
            if not command.startswith(('/', '!', '$')):
                command = f"/{command}"
            
            result = await self.console_client.send_command(command)
            return {
                "success": result.get("success", False),
                "command": command,
                "output": result.get("message", ""),
                "error": result.get("error"),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to send command '{command}': {e}")
            return {
                "success": False,
                "command": command,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def start_server(self) -> Dict[str, Any]:
        """Start server through Aetherius Core via console."""
        if not self.initialized or not self.console_client:
            raise RuntimeError("Adapter not initialized")
        
        try:
            result = await self.console_client.send_command("!server start")
            return {
                "success": result.get("success", False),
                "message": result.get("message", ""),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def stop_server(self) -> Dict[str, Any]:
        """Stop server through Aetherius Core."""
        if not self.initialized or not self.core_api:
            raise RuntimeError("Adapter not initialized")
        
        try:
            result = await self.core_api.server.stop()
            return {
                "success": result.get("success", False),
                "message": result.get("message", ""),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to stop server: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def restart_server(self) -> Dict[str, Any]:
        """Restart server through Aetherius Core."""
        if not self.initialized or not self.core_api:
            raise RuntimeError("Adapter not initialized")
        
        try:
            result = await self.core_api.server.restart()
            return {
                "success": result.get("success", False),
                "message": result.get("message", ""),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to restart server: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_online_players(self) -> List[Dict[str, Any]]:
        """Get online players from Aetherius Core via console."""
        if not self.initialized or not self.console_client:
            raise RuntimeError("Adapter not initialized")
        
        try:
            # Use Minecraft list command
            result = await self.console_client.send_command("/list")
            
            # For now, return simplified format
            # TODO: Parse actual player list from command output
            return []
        except Exception as e:
            logger.error(f"Failed to get online players: {e}")
            return []
    
    async def get_player_info(self, player_identifier: str) -> Optional[Dict[str, Any]]:
        """Get player information from Aetherius Core via console."""
        if not self.initialized or not self.console_client:
            raise RuntimeError("Adapter not initialized")
        
        try:
            # Simplified implementation for now
            return {
                "name": player_identifier,
                "uuid": "",
                "online": False,
                "last_seen": datetime.now().isoformat(),
                "level": 0,
                "experience": 0,
                "health": 20.0,
                "food_level": 20,
                "game_mode": "survival",
                "location": {},
                "statistics": {}
            }
        except Exception as e:
            logger.error(f"Failed to get player info for '{player_identifier}': {e}")
            return None
    
    async def kick_player(self, player_identifier: str, reason: str = "") -> Dict[str, Any]:
        """Kick player through Aetherius Core."""
        if not self.initialized or not self.core_api:
            raise RuntimeError("Adapter not initialized")
        
        try:
            result = await self.core_api.players.kick(player_identifier, reason)
            return {
                "success": result.get("success", False),
                "action": "kick",
                "player": player_identifier,
                "reason": reason,
                "message": result.get("message", ""),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to kick player '{player_identifier}': {e}")
            return {
                "success": False,
                "action": "kick",
                "player": player_identifier,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def ban_player(self, player_identifier: str, reason: str = "") -> Dict[str, Any]:
        """Ban player through Aetherius Core."""
        if not self.initialized or not self.core_api:
            raise RuntimeError("Adapter not initialized")
        
        try:
            result = await self.core_api.players.ban(player_identifier, reason)
            return {
                "success": result.get("success", False),
                "action": "ban",
                "player": player_identifier,
                "reason": reason,
                "message": result.get("message", ""),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to ban player '{player_identifier}': {e}")
            return {
                "success": False,
                "action": "ban",
                "player": player_identifier,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_performance_data(self) -> Dict[str, Any]:
        """Get performance data from Aetherius Core."""
        if not self.initialized or not self.core_api:
            raise RuntimeError("Adapter not initialized")
        
        try:
            performance = await self.core_api.monitoring.get_performance_data()
            return {
                "cpu_percent": performance.get("cpu_percent", 0.0),
                "memory_mb": performance.get("memory_mb", 0.0),
                "uptime_seconds": performance.get("uptime_seconds", 0.0),
                "tps": performance.get("tps", 20.0),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get performance data: {e}")
            return {
                "cpu_percent": 0.0,
                "memory_mb": 0.0,
                "uptime_seconds": 0.0,
                "tps": 20.0,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_plugins(self) -> List[Dict[str, Any]]:
        """Get plugins from Aetherius Core."""
        if not self.initialized or not self.core_api:
            raise RuntimeError("Adapter not initialized")
        
        try:
            plugins = await self.core_api.plugins.list()
            return [
                {
                    "name": plugin.get("name", ""),
                    "version": plugin.get("version", ""),
                    "description": plugin.get("description", ""),
                    "author": plugin.get("author", ""),
                    "enabled": plugin.get("enabled", False),
                    "loaded": plugin.get("loaded", False)
                }
                for plugin in plugins
            ]
        except Exception as e:
            logger.error(f"Failed to get plugins: {e}")
            return []
    
    async def get_components(self) -> List[Dict[str, Any]]:
        """Get components from Aetherius Core."""
        if not self.initialized or not self.core_api:
            raise RuntimeError("Adapter not initialized")
        
        try:
            components = await self.core_api.components.list()
            return [
                {
                    "name": component.get("name", ""),
                    "version": component.get("version", ""),
                    "description": component.get("description", ""),
                    "type": component.get("type", ""),
                    "enabled": component.get("enabled", False),
                    "loaded": component.get("loaded", False)
                }
                for component in components
            ]
        except Exception as e:
            logger.error(f"Failed to get components: {e}")
            return []