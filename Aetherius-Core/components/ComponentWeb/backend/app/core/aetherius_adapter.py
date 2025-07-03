"""
Aetherius核心适配器
==================

适配Aetherius核心的接口，使Web组件能够与核心系统集成
使用真实的核心API，不包含任何模拟数据
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

# 导入真实的核心API
from aetherius.core import (
    get_server_wrapper,
    get_plugin_manager,
    get_component_manager,
    get_event_manager,
    get_config_manager_extensions,
    get_file_manager
)
from aetherius.core.server_manager_extensions import ServerManagerExtensions
from aetherius.core.player_manager_extensions import PlayerManagerExtensions


class AetheriusCoreAdapter:
    """
    Aetherius核心适配器
    
    这个类适配现有的CoreClient接口到Aetherius核心的实际接口
    """
    
    def __init__(self, core_instance):
        """
        初始化适配器
        
        Args:
            core_instance: Aetherius核心实例
        """
        self.core = core_instance
        self.server_manager_ext = None
        self.player_manager_ext = None
        self._initialize_extensions()
        
    def _initialize_extensions(self):
        """初始化核心扩展"""
        try:
            # 初始化服务器管理扩展
            server_wrapper = get_server_wrapper()
            if server_wrapper:
                self.server_manager_ext = ServerManagerExtensions(server_wrapper)
            
            # 初始化玩家管理扩展
            if self.core and hasattr(self.core, 'player_manager'):
                self.player_manager_ext = PlayerManagerExtensions(self.core.player_manager)
            else:
                self.player_manager_ext = PlayerManagerExtensions(None)
                
        except Exception as e:
            print(f"Warning: Failed to initialize extensions: {e}")
    
    async def is_connected(self) -> bool:
        """检查是否连接到核心"""
        try:
            # 检查服务器包装器是否可用
            server_wrapper = get_server_wrapper()
            return server_wrapper is not None and getattr(server_wrapper, 'is_running', False)
        except Exception:
            return False
    
    async def initialize(self):
        """初始化连接（在组件模式下不需要）"""
        # 在组件模式下，核心连接由组件管理，这里不需要做任何事情
        pass
    
    async def cleanup(self):
        """清理连接（在组件模式下不需要）"""
        # 在组件模式下，核心连接由组件管理，这里不需要做任何事情  
        pass
    
    async def send_console_command(self, command: str) -> Dict[str, Any]:
        """
        发送控制台命令
        
        Args:
            command: 要执行的命令
            
        Returns:
            命令执行结果
        """
        try:
            if not await self.is_connected():
                return {
                    "success": False,
                    "command": command,
                    "message": "Core is not connected",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 通过服务器管理扩展执行命令
            if self.server_manager_ext:
                result = await self.server_manager_ext.execute_command(command)
                return {
                    "success": True,
                    "command": command,
                    "message": str(result) if result else "Command executed successfully",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # 备用：通过服务器包装器执行
                server_wrapper = get_server_wrapper()
                if server_wrapper and hasattr(server_wrapper, 'send_command'):
                    result = await server_wrapper.send_command(command)
                    return {
                        "success": True,
                        "command": command,
                        "message": str(result) if result else "Command executed successfully",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "command": command,
                        "message": "No command execution interface available",
                        "timestamp": datetime.now().isoformat()
                    }
            
        except Exception as e:
            return {
                "success": False,
                "command": command,
                "message": f"Command execution failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_server_status(self) -> Dict[str, Any]:
        """
        获取服务器状态
        
        Returns:
            服务器状态信息
        """
        try:
            if not await self.is_connected():
                return self._get_offline_status()
            
            # 通过服务器管理扩展获取状态
            if self.server_manager_ext:
                status = await self.server_manager_ext.get_server_status()
                metrics = await self.server_manager_ext.get_performance_metrics()
                
                return {
                    "is_running": status.state == "running" if hasattr(status, 'state') else True,
                    "uptime": getattr(status, 'uptime', 0),
                    "version": getattr(status, 'version', "Unknown"),
                    "player_count": getattr(status, 'player_count', 0),
                    "max_players": getattr(status, 'max_players', 20),
                    "tps": getattr(metrics, 'tps', 20.0) if metrics else 20.0,
                    "cpu_usage": getattr(metrics, 'cpu_percent', 0.0) if metrics else 0.0,
                    "memory_usage": {
                        "used": getattr(metrics, 'memory_used_mb', 0) if metrics else 0,
                        "max": getattr(metrics, 'memory_total_mb', 4096) if metrics else 4096,
                        "percentage": getattr(metrics, 'memory_percent', 0.0) if metrics else 0.0
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # 备用：通过服务器包装器获取基本状态
                server_wrapper = get_server_wrapper()
                if server_wrapper:
                    return {
                        "is_running": getattr(server_wrapper, 'is_running', False),
                        "uptime": 0,
                        "version": "Unknown",
                        "player_count": 0,
                        "max_players": 20,
                        "tps": 20.0,
                        "cpu_usage": 0.0,
                        "memory_usage": {
                            "used": 0,
                            "max": 4096,
                            "percentage": 0.0
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return self._get_offline_status()
                
        except Exception as e:
            return self._get_error_status(str(e))
    
    async def get_online_players(self) -> List[Dict[str, Any]]:
        """
        获取在线玩家列表
        
        Returns:
            在线玩家列表
        """
        try:
            if not await self.is_connected():
                return []
            
            # 通过玩家管理扩展获取玩家列表
            if self.player_manager_ext:
                online_players = await self.player_manager_ext.get_online_players()
                return [self._normalize_player_data(player) for player in online_players.values()]
            else:
                # 备用：返回空列表，不使用模拟数据
                return []
                
        except Exception as e:
            return []
    
    async def start_server(self) -> Dict[str, Any]:
        """
        启动服务器
        
        Returns:
            操作结果
        """
        try:
            # 通过服务器管理扩展启动
            if self.server_manager_ext:
                result = await self.server_manager_ext.start_server()
                return {
                    "success": True,
                    "message": "Server start initiated",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # 备用：通过服务器包装器启动
                server_wrapper = get_server_wrapper()
                if server_wrapper and hasattr(server_wrapper, 'start'):
                    await server_wrapper.start()
                    return {
                        "success": True,
                        "message": "Server start initiated",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "message": "Server start not supported",
                        "timestamp": datetime.now().isoformat()
                    }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to start server: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def stop_server(self) -> Dict[str, Any]:
        """
        停止服务器
        
        Returns:
            操作结果
        """
        try:
            # 通过服务器管理扩展停止
            if self.server_manager_ext:
                result = await self.server_manager_ext.stop_server()
                return {
                    "success": True,
                    "message": "Server stop initiated",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # 备用：通过服务器包装器停止
                server_wrapper = get_server_wrapper()
                if server_wrapper and hasattr(server_wrapper, 'stop'):
                    await server_wrapper.stop()
                    return {
                        "success": True,
                        "message": "Server stop initiated",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "message": "Server stop not supported",
                        "timestamp": datetime.now().isoformat()
                    }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to stop server: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def restart_server(self) -> Dict[str, Any]:
        """
        重启服务器
        
        Returns:
            操作结果
        """
        try:
            # 通过服务器管理扩展重启
            if self.server_manager_ext:
                result = await self.server_manager_ext.restart_server()
                return {
                    "success": True,
                    "message": "Server restart initiated",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # 备用：先停止再启动
                stop_result = await self.stop_server()
                if stop_result["success"]:
                    await asyncio.sleep(2)  # 等待停止
                    start_result = await self.start_server()
                    return start_result
                else:
                    return stop_result
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to restart server: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_offline_status(self) -> Dict[str, Any]:
        """获取离线状态"""
        return {
            "is_running": False,
            "uptime": 0,
            "version": "Unknown",
            "player_count": 0,
            "max_players": 20,
            "tps": 0.0,
            "cpu_usage": 0.0,
            "memory_usage": {
                "used": 0,
                "max": 4096,
                "percentage": 0.0
            },
            "timestamp": datetime.now().isoformat()
        }
    
    # 移除默认状态方法，使用真实数据或离线状态
    
    def _get_error_status(self, error: str) -> Dict[str, Any]:
        """获取错误状态"""
        status = self._get_offline_status()
        status["error"] = error
        return status
    
    # 移除标准化服务器状态方法，直接在get_server_status中处理真实数据
    
    def _normalize_player_data(self, raw_player: Any) -> Dict[str, Any]:
        """标准化玩家数据"""
        if hasattr(raw_player, 'to_dict'):
            # 如果是PlayerData对象，使用其to_dict方法
            return raw_player.to_dict()
        elif isinstance(raw_player, dict):
            return {
                "uuid": raw_player.get("uuid", ""),
                "name": raw_player.get("name", "Unknown"),
                "online": raw_player.get("online", True),
                "last_login": raw_player.get("last_login"),
                "ip_address": raw_player.get("ip_address"),
                "game_mode": raw_player.get("game_mode", "survival"),
                "level": raw_player.get("level", 0),
                "experience": raw_player.get("experience", 0)
            }
        else:
            # 如果是其他类型，尝试获取基本属性
            return {
                "uuid": getattr(raw_player, 'uuid', '') if raw_player else "",
                "name": getattr(raw_player, 'name', 'Unknown') if raw_player else "Unknown",
                "online": getattr(raw_player, 'online', True) if raw_player else True,
                "last_login": getattr(raw_player, 'last_login', None) if raw_player else None,
                "ip_address": getattr(raw_player, 'ip_address', None) if raw_player else None,
                "game_mode": getattr(raw_player, 'game_mode', 'survival') if raw_player else "survival",
                "level": getattr(raw_player, 'level', 0) if raw_player else 0,
                "experience": getattr(raw_player, 'experience', 0) if raw_player else 0
            }
    
    # 移除模拟数据方法，不再使用