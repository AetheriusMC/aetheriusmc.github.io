"""
Mock Aetherius Core Interfaces
==============================

模拟Aetherius核心接口用于开发和测试
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import asyncio


@dataclass
class ComponentInfo:
    """组件信息定义"""
    name: str
    display_name: str
    description: str
    version: str
    author: str
    website: str
    dependencies: List[str]
    soft_dependencies: List[str]
    aetherius_version: str
    category: str
    permissions: List[str]
    config_schema: Dict[str, Any]
    default_config: Dict[str, Any]


class MockCore:
    """模拟Aetherius核心"""
    
    def __init__(self):
        self.is_running = True
        self._event_handlers = {}
    
    async def execute_command(self, command: str) -> str:
        """执行命令"""
        print(f"[Mock Core] 执行命令: {command}")
        return f"Command '{command}' executed successfully"
    
    async def get_server_status(self) -> Dict[str, Any]:
        """获取服务器状态"""
        return {
            "running": True,
            "uptime": 3600,
            "version": "1.0.0-mock",
            "player_count": 2,
            "max_players": 20,
            "tps": 20.0,
            "cpu_usage": 15.5,
            "memory_used": 1024,
            "memory_max": 4096,
            "memory_percentage": 25.0
        }
    
    async def get_online_players(self) -> List[Dict[str, Any]]:
        """获取在线玩家"""
        return [
            {
                "uuid": "550e8400-e29b-41d4-a716-446655440000",
                "name": "TestPlayer1",
                "online": True,
                "ip_address": "127.0.0.1",
                "game_mode": "survival",
                "level": 42
            },
            {
                "uuid": "550e8400-e29b-41d4-a716-446655440001", 
                "name": "TestPlayer2",
                "online": True,
                "ip_address": "127.0.0.1",
                "game_mode": "creative",
                "level": 100
            }
        ]
    
    def emit_event(self, event_name: str, data: Dict[str, Any]):
        """触发事件"""
        print(f"[Mock Core] 触发事件: {event_name}, 数据: {data}")
        if event_name in self._event_handlers:
            for handler in self._event_handlers[event_name]:
                asyncio.create_task(handler(data))


class Component:
    """模拟组件基类"""
    
    def __init__(self, component_info: ComponentInfo):
        self.info = component_info
        self.core = MockCore()
        self.config = component_info.default_config.copy()
        self.is_enabled = False
        self._event_handlers = {}
    
    async def on_load(self):
        """组件加载"""
        pass
    
    async def on_enable(self):
        """组件启用"""
        self.is_enabled = True
    
    async def on_disable(self):
        """组件禁用"""
        self.is_enabled = False
    
    async def on_unload(self):
        """组件卸载"""
        pass


def event_handler(event_name: str):
    """事件处理器装饰器"""
    def decorator(func: Callable):
        func._event_name = event_name
        return func
    return decorator


class MockLogger:
    """模拟日志器"""
    
    def __init__(self, name: str):
        self.name = name
    
    def info(self, message: str, **kwargs):
        print(f"[{self.name}] INFO: {message}")
        if kwargs:
            print(f"    额外信息: {kwargs}")
    
    def error(self, message: str, **kwargs):
        print(f"[{self.name}] ERROR: {message}")
        if kwargs:
            print(f"    额外信息: {kwargs}")
    
    def warning(self, message: str, **kwargs):
        print(f"[{self.name}] WARNING: {message}")
        if kwargs:
            print(f"    额外信息: {kwargs}")
    
    def debug(self, message: str, **kwargs):
        print(f"[{self.name}] DEBUG: {message}")
        if kwargs:
            print(f"    额外信息: {kwargs}")


def get_logger(name: str) -> MockLogger:
    """获取模拟日志器"""
    return MockLogger(name)