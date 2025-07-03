"""
Mock Aetherius adapter for development and testing.

This adapter provides simulated responses for development when Aetherius Core
is not available, allowing frontend development and testing.
"""

import asyncio
import random
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
import logging

from .aetherius_adapter import IAetheriusAdapter
from ..core.container import singleton

logger = logging.getLogger(__name__)


@singleton
class MockAetheriusAdapter(IAetheriusAdapter):
    """Mock Aetherius adapter for development."""
    
    def __init__(self):
        self.initialized = False
        self.server_running = True
        self.start_time = datetime.now()
        self.mock_players = self._generate_mock_players()
        self.command_history = []
        self.event_callbacks: Dict[str, List[Callable]] = {}
        
        # Background task for simulating events
        self._event_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> None:
        """Initialize mock adapter."""
        self.initialized = True
        
        # Start background event simulation
        self._event_task = asyncio.create_task(self._simulate_events())
        
        logger.info("Mock Aetherius adapter initialized for development")
    
    async def dispose(self) -> None:
        """Dispose mock adapter."""
        if self._event_task:
            self._event_task.cancel()
            try:
                await self._event_task
            except asyncio.CancelledError:
                pass
        
        self.initialized = False
        logger.info("Mock Aetherius adapter disposed")
    
    def _generate_mock_players(self) -> List[Dict[str, Any]]:
        """Generate mock player data."""
        players = []
        player_names = [
            "Steve", "Alex", "Notch", "Herobrine", "TestPlayer1", 
            "DevUser", "AdminPlayer", "GuestUser", "ProBuilder", "RedstoneEngineer"
        ]
        
        for i, name in enumerate(player_names):
            online = random.choice([True, False]) if i > 2 else True  # First 3 always online
            
            players.append({
                "uuid": f"550e8400-e29b-41d4-a716-44665544{i:04d}",
                "name": name,
                "online": online,
                "last_seen": datetime.now().isoformat() if online else 
                           (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat(),
                "level": random.randint(1, 50),
                "experience": random.randint(0, 100000),
                "health": random.uniform(15.0, 20.0),
                "food_level": random.randint(15, 20),
                "game_mode": random.choice(["survival", "creative", "adventure", "spectator"]),
                "location": {
                    "world": "world",
                    "x": random.uniform(-1000, 1000),
                    "y": random.uniform(1, 256),
                    "z": random.uniform(-1000, 1000)
                },
                "statistics": {
                    "blocks_broken": random.randint(100, 10000),
                    "blocks_placed": random.randint(50, 5000),
                    "distance_traveled": random.uniform(1000, 50000),
                    "time_played": random.randint(3600, 360000),  # 1 hour to 100 hours
                    "deaths": random.randint(0, 20),
                    "mob_kills": random.randint(10, 1000)
                }
            })
        
        return players
    
    async def _simulate_events(self) -> None:
        """Simulate random server events."""
        while True:
            try:
                await asyncio.sleep(random.uniform(5, 15))  # Random interval between events
                
                if not self.initialized:
                    break
                
                # Simulate different types of events
                event_type = random.choice([
                    "console_log", "player_join", "player_leave", 
                    "performance_update", "player_chat"
                ])
                
                if event_type == "console_log":
                    await self._simulate_console_log()
                elif event_type == "player_join" and random.random() < 0.3:
                    await self._simulate_player_join()
                elif event_type == "player_leave" and random.random() < 0.2:
                    await self._simulate_player_leave()
                elif event_type == "performance_update":
                    await self._simulate_performance_update()
                elif event_type == "player_chat" and random.random() < 0.4:
                    await self._simulate_player_chat()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event simulation: {e}")
    
    async def _simulate_console_log(self) -> None:
        """Simulate console log messages."""
        log_messages = [
            "Server tick completed in 45ms",
            "Saved the game",
            "Chunk [10, 5] loaded",
            "Player movement processed",
            "Memory usage: 1.2GB / 4.0GB",
            "Plugin XYZ processed 15 events",
            "Network packet received",
            "Garbage collector run completed"
        ]
        
        levels = ["INFO", "DEBUG", "WARN"]
        
        await self._broadcast_event("console_log", {
            "level": random.choice(levels),
            "message": random.choice(log_messages),
            "source": "server",
            "timestamp": datetime.now().isoformat()
        })
    
    async def _simulate_player_join(self) -> None:
        """Simulate player join event."""
        offline_players = [p for p in self.mock_players if not p["online"]]
        if offline_players:
            player = random.choice(offline_players)
            player["online"] = True
            player["last_seen"] = datetime.now().isoformat()
            
            await self._broadcast_event("player_join", {
                "player": player,
                "timestamp": datetime.now().isoformat()
            })
    
    async def _simulate_player_leave(self) -> None:
        """Simulate player leave event."""
        online_players = [p for p in self.mock_players if p["online"]]
        if len(online_players) > 1:  # Keep at least one player online
            player = random.choice(online_players)
            player["online"] = False
            player["last_seen"] = datetime.now().isoformat()
            
            await self._broadcast_event("player_leave", {
                "player": player,
                "timestamp": datetime.now().isoformat()
            })
    
    async def _simulate_performance_update(self) -> None:
        """Simulate performance update event."""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        await self._broadcast_event("performance_update", {
            "metrics": {
                "cpu_percent": random.uniform(20.0, 80.0),
                "memory_mb": random.uniform(1000.0, 3000.0),
                "uptime_seconds": uptime,
                "tps": random.uniform(18.0, 20.0)
            },
            "timestamp": datetime.now().isoformat()
        })
    
    async def _simulate_player_chat(self) -> None:
        """Simulate player chat event."""
        online_players = [p for p in self.mock_players if p["online"]]
        if online_players:
            player = random.choice(online_players)
            messages = [
                "Hello everyone!",
                "Has anyone seen my diamonds?",
                "Working on a new build",
                "Nice weather today",
                "Anyone want to trade?",
                "Found a cool cave system",
                "Building a castle",
                "Thanks for the help!"
            ]
            
            await self._broadcast_event("player_chat", {
                "player": player,
                "message": random.choice(messages),
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
                logger.error(f"Error in mock event callback for {event_type}: {e}")
    
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
    
    # Mock API implementations
    async def get_server_status(self) -> Dict[str, Any]:
        """Get mock server status."""
        uptime = int((datetime.now() - self.start_time).total_seconds())
        online_count = len([p for p in self.mock_players if p["online"]])
        
        return {
            "status": "running" if self.server_running else "stopped",
            "uptime": uptime,
            "version": "1.20.1",
            "online_players": online_count,
            "max_players": 20,
            "timestamp": datetime.now().isoformat()
        }
    
    async def send_command(self, command: str) -> Dict[str, Any]:
        """Send mock console command."""
        self.command_history.append({
            "command": command,
            "timestamp": datetime.now().isoformat()
        })
        
        # Simulate command responses
        if command.startswith("say "):
            message = command[4:]
            output = f"[Server] {message}"
        elif command == "list":
            online_players = [p["name"] for p in self.mock_players if p["online"]]
            output = f"There are {len(online_players)} of a max of 20 players online: {', '.join(online_players)}"
        elif command == "stop":
            self.server_running = False
            output = "Stopping the server"
        elif command == "start":
            self.server_running = True
            output = "Starting the server"
        elif command.startswith("tp "):
            output = f"Teleported player"
        else:
            output = f"Command '{command}' executed successfully"
        
        # Simulate console log for command
        await self._broadcast_event("console_log", {
            "level": "INFO",
            "message": f"Console command: {command}",
            "source": "console",
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "command": command,
            "output": output,
            "timestamp": datetime.now().isoformat()
        }
    
    async def start_server(self) -> Dict[str, Any]:
        """Start mock server."""
        self.server_running = True
        self.start_time = datetime.now()
        
        await self._broadcast_event("server_start", {
            "status": "running",
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "message": "Server started successfully",
            "timestamp": datetime.now().isoformat()
        }
    
    async def stop_server(self) -> Dict[str, Any]:
        """Stop mock server."""
        self.server_running = False
        
        await self._broadcast_event("server_stop", {
            "status": "stopped",
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "message": "Server stopped successfully",
            "timestamp": datetime.now().isoformat()
        }
    
    async def restart_server(self) -> Dict[str, Any]:
        """Restart mock server."""
        await self.stop_server()
        await asyncio.sleep(2)  # Simulate restart delay
        await self.start_server()
        
        return {
            "success": True,
            "message": "Server restarted successfully",
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_online_players(self) -> List[Dict[str, Any]]:
        """Get mock online players."""
        return [player for player in self.mock_players if player["online"]]
    
    async def get_player_info(self, player_identifier: str) -> Optional[Dict[str, Any]]:
        """Get mock player information."""
        # Search by name or UUID
        for player in self.mock_players:
            if player["name"].lower() == player_identifier.lower() or player["uuid"] == player_identifier:
                return player
        return None
    
    async def kick_player(self, player_identifier: str, reason: str = "") -> Dict[str, Any]:
        """Mock kick player."""
        player = await self.get_player_info(player_identifier)
        if player and player["online"]:
            player["online"] = False
            player["last_seen"] = datetime.now().isoformat()
            
            await self._broadcast_event("player_leave", {
                "player": player,
                "reason": "kicked",
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "action": "kick",
                "player": player_identifier,
                "reason": reason,
                "message": f"Player {player_identifier} kicked successfully",
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "success": False,
            "action": "kick",
            "player": player_identifier,
            "error": "Player not found or not online",
            "timestamp": datetime.now().isoformat()
        }
    
    async def ban_player(self, player_identifier: str, reason: str = "") -> Dict[str, Any]:
        """Mock ban player."""
        player = await self.get_player_info(player_identifier)
        if player:
            if player["online"]:
                player["online"] = False
                player["last_seen"] = datetime.now().isoformat()
            
            # Mark as banned (in real implementation, this would be stored)
            player["banned"] = True
            player["ban_reason"] = reason
            
            return {
                "success": True,
                "action": "ban",
                "player": player_identifier,
                "reason": reason,
                "message": f"Player {player_identifier} banned successfully",
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "success": False,
            "action": "ban",
            "player": player_identifier,
            "error": "Player not found",
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_performance_data(self) -> Dict[str, Any]:
        """Get mock performance data."""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "cpu_percent": random.uniform(30.0, 70.0),
            "memory_mb": random.uniform(1200.0, 2800.0),
            "uptime_seconds": uptime,
            "tps": random.uniform(19.0, 20.0),
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_plugins(self) -> List[Dict[str, Any]]:
        """Get mock plugins."""
        return [
            {
                "name": "EssentialsX",
                "version": "2.19.0",
                "description": "Essential commands and features",
                "author": "EssentialsX Team",
                "enabled": True,
                "loaded": True
            },
            {
                "name": "WorldEdit",
                "version": "7.2.10",
                "description": "World editing plugin",
                "author": "sk89q",
                "enabled": True,
                "loaded": True
            },
            {
                "name": "Vault",
                "version": "1.7.3",
                "description": "Economy and permissions API",
                "author": "milkbowl",
                "enabled": True,
                "loaded": True
            },
            {
                "name": "TestPlugin",
                "version": "1.0.0",
                "description": "Test plugin for development",
                "author": "Developer",
                "enabled": False,
                "loaded": False
            }
        ]
    
    async def get_components(self) -> List[Dict[str, Any]]:
        """Get mock components."""
        return [
            {
                "name": "webconsole",
                "version": "2.0.0",
                "description": "Web Console Component",
                "type": "web_management",
                "enabled": True,
                "loaded": True
            },
            {
                "name": "backup",
                "version": "1.5.0",
                "description": "Backup Management Component",
                "type": "utility",
                "enabled": True,
                "loaded": True
            },
            {
                "name": "monitoring",
                "version": "1.2.0",
                "description": "System Monitoring Component",
                "type": "monitoring",
                "enabled": False,
                "loaded": False
            }
        ]