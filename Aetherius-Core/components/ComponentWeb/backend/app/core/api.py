"""
Core API Wrapper
================

High-level API wrapper for Aetherius Core operations.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from app.core.client import CoreClient
from app.utils.logging import get_logger
from app.utils.exceptions import CoreAPIError

logger = get_logger(__name__)


class CoreAPI:
    """High-level API wrapper for core operations"""
    
    def __init__(self, core_client_or_adapter):
        """
        初始化CoreAPI
        
        Args:
            core_client_or_adapter: CoreClient实例（独立模式）或适配器实例（组件模式）
        """
        self.client = core_client_or_adapter
    
    async def send_console_command(self, command: str, websocket_manager=None) -> Dict[str, Any]:
        """
        Send a command to the server console
        
        Args:
            command: Console command to execute
            websocket_manager: WebSocket manager for sending real-time results
            
        Returns:
            Command execution result
        """
        if not command or not command.strip():
            raise CoreAPIError("Command cannot be empty")
        
        command = command.strip()
        logger.info("Sending console command", command=command)
        
        # 检查是否为适配器模式
        if hasattr(self.client, 'send_console_command'):
            # 适配器模式（组件集成）
            result = await self.client.send_console_command(command)
        else:
            # 传统CoreClient模式（独立运行）
            async with self.client.get_core() as core:
                result = await core.send_command(command, websocket_manager)
                
                result = {
                    "command": command,
                    "success": result.get("success", False),
                    "message": result.get("message", ""),
                    "timestamp": datetime.now().isoformat(),
                    "execution_time": result.get("timestamp", 0)
                }
        
        logger.info(
            "Console command executed",
            command=command,
            success=result.get("success", False),
            message=result.get("message", "")
        )
        
        return result
    
    async def get_server_status(self) -> Dict[str, Any]:
        """
        Get current server status
        
        Returns:
            Server status information
        """
        # 检查是否为适配器模式
        if hasattr(self.client, 'get_server_status'):
            # 适配器模式（组件集成）
            return await self.client.get_server_status()
        else:
            # 传统CoreClient模式（独立运行）
            async with self.client.get_core() as core:
                status = await core.get_server_status()
                
                return {
                    "is_running": status.get("is_running", False),
                    "uptime": status.get("uptime", 0),
                    "version": status.get("version", "Unknown"),
                    "player_count": status.get("player_count", 0),
                    "max_players": status.get("max_players", 20),
                    "tps": status.get("tps", 0.0),
                    "cpu_usage": status.get("cpu_usage", 0.0),
                    "memory_usage": status.get("memory_usage", {}),
                    "timestamp": datetime.now().isoformat()
                }
    
    async def get_online_players(self) -> List[Dict[str, Any]]:
        """
        Get list of online players
        
        Returns:
            List of online player information
        """
        # 检查是否为适配器模式
        if hasattr(self.client, 'get_online_players'):
            # 适配器模式（组件集成）
            return await self.client.get_online_players()
        else:
            # 传统CoreClient模式（独立运行）
            async with self.client.get_core() as core:
                players = await core.get_online_players()
                
                return [
                    {
                        "uuid": player.get("uuid", ""),
                        "name": player.get("name", "Unknown"),
                        "online": player.get("online", False),
                        "last_login": player.get("last_login"),
                        "ip_address": player.get("ip_address"),
                        "game_mode": player.get("game_mode", "survival"),
                        "level": player.get("level", 0),
                        "experience": player.get("experience", 0)
                    }
                    for player in players
                ]
    
    async def start_server(self) -> Dict[str, Any]:
        """
        Start the server using Aetherius CLI command
        
        Returns:
            Operation result
        """
        # 检查是否为适配器模式
        if hasattr(self.client, 'start_server'):
            # 适配器模式（组件集成）
            return await self.client.start_server()
        else:
            # 使用Aetherius CLI命令启动服务器
            import subprocess
            import asyncio
            
            try:
                logger.info("Starting server using Aetherius CLI command")
                
                # 使用异步运行Aetherius命令
                process = await asyncio.create_subprocess_exec(
                    'python', '-m', 'aetherius', 'server', 'start',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd='/workspaces/aetheriusmc.github.io/Aetherius-Core'
                )
                
                stdout, stderr = await process.communicate()
                
                success = process.returncode == 0
                message = stdout.decode() if success else stderr.decode()
                
                return {
                    "success": success,
                    "message": message.strip() or ("Server start command executed" if success else "Failed to start server"),
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error("Failed to start server via Aetherius CLI", error=str(e))
                return {
                    "success": False,
                    "message": f"Failed to execute start command: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
    
    async def stop_server(self) -> Dict[str, Any]:
        """
        Stop the server using Aetherius CLI command
        
        Returns:
            Operation result
        """
        # 检查是否为适配器模式
        if hasattr(self.client, 'stop_server'):
            # 适配器模式（组件集成）
            return await self.client.stop_server()
        else:
            # 使用Aetherius CLI命令停止服务器
            import subprocess
            import asyncio
            
            try:
                logger.info("Stopping server using Aetherius CLI command")
                
                # 使用异步运行Aetherius命令
                process = await asyncio.create_subprocess_exec(
                    'python', '-m', 'aetherius', 'server', 'stop',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd='/workspaces/aetheriusmc.github.io/Aetherius-Core'
                )
                
                stdout, stderr = await process.communicate()
                
                success = process.returncode == 0
                message = stdout.decode() if success else stderr.decode()
                
                return {
                    "success": success,
                    "message": message.strip() or ("Server stop command executed" if success else "Failed to stop server"),
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error("Failed to stop server via Aetherius CLI", error=str(e))
                return {
                    "success": False,
                    "message": f"Failed to execute stop command: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
    
    async def restart_server(self) -> Dict[str, Any]:
        """
        Restart the server using Aetherius CLI command
        
        Returns:
            Operation result
        """
        # 检查是否为适配器模式
        if hasattr(self.client, 'restart_server'):
            # 适配器模式（组件集成）
            return await self.client.restart_server()
        else:
            # 使用Aetherius CLI命令重启服务器
            import subprocess
            import asyncio
            
            try:
                logger.info("Restarting server using Aetherius CLI command")
                
                # 使用异步运行Aetherius命令
                process = await asyncio.create_subprocess_exec(
                    'python', '-m', 'aetherius', 'server', 'restart',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd='/workspaces/aetheriusmc.github.io/Aetherius-Core'
                )
                
                stdout, stderr = await process.communicate()
                
                success = process.returncode == 0
                message = stdout.decode() if success else stderr.decode()
                
                return {
                    "success": success,
                    "message": message.strip() or ("Server restart command executed" if success else "Failed to restart server"),
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error("Failed to restart server via Aetherius CLI", error=str(e))
                return {
                    "success": False,
                    "message": f"Failed to execute restart command: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
    
    async def kick_player(self, player_name: str, reason: str = "Kicked by admin") -> Dict[str, Any]:
        """
        Kick a player from the server
        
        Args:
            player_name: Name of the player to kick
            reason: Reason for kicking
            
        Returns:
            Operation result
        """
        command = f"kick {player_name} {reason}"
        return await self.send_console_command(command)
    
    async def ban_player(self, player_name: str, reason: str = "Banned by admin") -> Dict[str, Any]:
        """
        Ban a player from the server
        
        Args:
            player_name: Name of the player to ban
            reason: Reason for banning
            
        Returns:
            Operation result
        """
        command = f"ban {player_name} {reason}"
        return await self.send_console_command(command)
    
    async def op_player(self, player_name: str) -> Dict[str, Any]:
        """
        Give operator privileges to a player
        
        Args:
            player_name: Name of the player
            
        Returns:
            Operation result
        """
        command = f"op {player_name}"
        return await self.send_console_command(command)
    
    async def deop_player(self, player_name: str) -> Dict[str, Any]:
        """
        Remove operator privileges from a player
        
        Args:
            player_name: Name of the player
            
        Returns:
            Operation result
        """
        command = f"deop {player_name}"
        return await self.send_console_command(command)
    
    async def get_current_performance(self) -> Dict[str, Any]:
        """
        Get current server performance metrics
        
        Returns:
            Current performance data
        """
        # 检查是否为适配器模式
        if hasattr(self.client, 'get_current_performance'):
            # 适配器模式（组件集成）
            return await self.client.get_current_performance()
        else:
            # 传统CoreClient模式（独立运行）
            async with self.client.get_core() as core:
                perf = await core.get_performance_data()
                
                return {
                    "tps": perf.get("tps", 20.0),
                    "cpu_usage": perf.get("cpu_usage", 0.0),
                    "memory_usage": perf.get("memory_usage", 0.0),
                    "memory_total": perf.get("memory_total", 4096),
                    "memory_used": perf.get("memory_used", 0),
                    "disk_usage": perf.get("disk_usage", 0.0),
                    "network_in": perf.get("network_in", 0),
                    "network_out": perf.get("network_out", 0),
                    "thread_count": perf.get("thread_count", 0),
                    "gc_collections": perf.get("gc_collections", 0),
                    "timestamp": datetime.now().isoformat()
                }
    
    async def get_metrics_history(self, hours: int = 1) -> List[Dict[str, Any]]:
        """
        Get historical performance metrics
        
        Args:
            hours: Number of hours of history to retrieve
            
        Returns:
            List of historical performance data points
        """
        # 检查是否为适配器模式
        if hasattr(self.client, 'get_metrics_history'):
            # 适配器模式（组件集成）
            return await self.client.get_metrics_history(hours)
        else:
            # 传统CoreClient模式（独立运行）
            async with self.client.get_core() as core:
                try:
                    metrics = await core.get_metrics_history(hours)
                    return metrics
                except Exception as e:
                    logger.warning("Failed to get metrics history from core", error=str(e))
                    # 如果核心不支持历史数据，返回空列表让调用者处理
                    raise e
    
    async def search_players(self, search_params: Dict[str, Any], page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        Search players with pagination and filtering
        
        Args:
            search_params: Search and filter parameters
            page: Page number (1-based)
            per_page: Items per page
            
        Returns:
            Paginated player search results
        """
        # 检查是否为适配器模式
        if hasattr(self.client, 'search_players'):
            # 适配器模式（组件集成）
            return await self.client.search_players(search_params, page, per_page)
        else:
            # 传统CoreClient模式（独立运行）
            async with self.client.get_core() as core:
                try:
                    results = await core.search_players(search_params, page, per_page)
                    return results
                except Exception as e:
                    logger.warning("Failed to search players from core", error=str(e))
                    # 如果核心不支持搜索，让调用者处理
                    raise e
    
    async def get_player_details(self, player_identifier: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific player
        
        Args:
            player_identifier: Player UUID or name
            
        Returns:
            Detailed player information
        """
        # 检查是否为适配器模式
        if hasattr(self.client, 'get_player_details'):
            # 适配器模式（组件集成）
            return await self.client.get_player_details(player_identifier)
        else:
            # 传统CoreClient模式（独立运行）
            async with self.client.get_core() as core:
                try:
                    player_data = await core.get_player_details(player_identifier)
                    return player_data
                except Exception as e:
                    logger.warning("Failed to get player details from core", error=str(e))
                    raise e
    
    async def execute_player_action(
        self, 
        player_identifier: str, 
        action: str, 
        reason: str = None, 
        duration: int = None
    ) -> Dict[str, Any]:
        """
        Execute an action on a player
        
        Args:
            player_identifier: Player UUID or name
            action: Action to execute
            reason: Reason for the action
            duration: Duration for temporary actions (minutes)
            
        Returns:
            Action execution result
        """
        # 检查是否为适配器模式
        if hasattr(self.client, 'execute_player_action'):
            # 适配器模式（组件集成）
            return await self.client.execute_player_action(
                player_identifier, action, reason, duration
            )
        else:
            # 传统CoreClient模式（独立运行）
            async with self.client.get_core() as core:
                try:
                    # Map actions to console commands
                    command = self._build_player_command(action, player_identifier, reason, duration)
                    result = await core.send_command(command)
                    
                    return {
                        "success": result.get("success", True),
                        "message": result.get("message", f"Executed {action} on {player_identifier}"),
                        "timestamp": datetime.now().isoformat(),
                        "command": command
                    }
                except Exception as e:
                    logger.error("Failed to execute player action", error=str(e))
                    return {
                        "success": False,
                        "message": f"Failed to execute {action}: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }
    
    def _build_player_command(self, action: str, player_identifier: str, reason: str = None, duration: int = None) -> str:
        """
        Build console command for player action
        
        Args:
            action: Action type
            player_identifier: Player UUID or name
            reason: Action reason
            duration: Duration in minutes
            
        Returns:
            Console command string
        """
        reason_text = reason or "No reason provided"
        
        command_map = {
            "kick": f"kick {player_identifier} {reason_text}",
            "ban": f"ban {player_identifier} {reason_text}",
            "tempban": f"tempban {player_identifier} {duration or 60}m {reason_text}",
            "unban": f"pardon {player_identifier}",
            "op": f"op {player_identifier}",
            "deop": f"deop {player_identifier}",
            "teleport": f"tp {player_identifier} spawn",
            "heal": f"heal {player_identifier}"
        }
        
        return command_map.get(action, f"say Unknown action: {action}")
    
    async def get_player_statistics(self, player_identifier: str) -> Dict[str, Any]:
        """
        Get player statistics and analytics
        
        Args:
            player_identifier: Player UUID or name
            
        Returns:
            Player statistics
        """
        # 检查是否为适配器模式
        if hasattr(self.client, 'get_player_statistics'):
            # 适配器模式（组件集成）
            return await self.client.get_player_statistics(player_identifier)
        else:
            # 传统CoreClient模式（独立运行）
            async with self.client.get_core() as core:
                try:
                    stats = await core.get_player_statistics(player_identifier)
                    return stats
                except Exception as e:
                    logger.warning("Failed to get player statistics from core", error=str(e))
                    # Return mock statistics
                    return {
                        "blocks_broken": 0,
                        "blocks_placed": 0,
                        "distance_traveled": 0.0,
                        "time_played": 0,
                        "deaths": 0,
                        "mob_kills": 0,
                        "player_kills": 0,
                        "items_crafted": 0,
                        "items_used": 0,
                        "damage_dealt": 0.0,
                        "damage_taken": 0.0
                    }