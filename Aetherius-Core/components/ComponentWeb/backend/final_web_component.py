"""
最终适配的Web组件实现
"""

import logging
import asyncio
from typing import Optional

# 直接使用Component基类
from aetherius.core.component import Component

logger = logging.getLogger(__name__)


class WebComponent(Component):
    """Web界面组件"""
    
    def __init__(self, core_instance=None, config=None):
        super().__init__(core_instance, config)
        self.logger = logging.getLogger("component.web")
        self.web_server = None
        self.server_task = None
    
    def get_config(self) -> dict:
        """获取组件配置"""
        return getattr(self, 'config', {}) or {}
    
    async def emit_event(self, event_name: str, data = None):
        """
        发送事件（安全版本）
        
        Args:
            event_name: 事件名称
            data: 事件数据
        """
        try:
            if self.core and hasattr(self.core, 'event_manager') and self.core.event_manager:
                await self.core.event_manager.emit_event(
                    event_name, 
                    data, 
                    source=self.__class__.__name__
                )
            else:
                self.logger.debug(f"无法发送事件 {event_name}: 事件管理器不可用")
        except Exception as e:
            self.logger.warning(f"发送事件失败 {event_name}: {e}")
        
    async def on_load(self):
        """组件加载时调用"""
        self.logger.info("Web组件正在加载...")
        
        # 获取配置
        config = self.get_config() or {}
        self.web_host = config.get("web_host", "0.0.0.0")
        self.web_port = config.get("web_port", 8000)
        self.cors_origins = config.get("cors_origins", ["http://localhost:3000"])
        
        self.logger.info(f"Web组件加载完成 - 配置端口: {self.web_port}")
        
    async def on_enable(self):
        """组件启用时调用"""
        self.logger.info("Web组件正在启用...")
        self.logger.info(f"Web服务器模拟启动 - http://{self.web_host}:{self.web_port}")
        
    async def on_disable(self):
        """组件禁用时调用"""
        self.logger.info("Web组件正在禁用...")
        self.logger.info("Web服务器模拟停止")
        
    async def on_unload(self):
        """组件卸载时调用"""
        self.logger.info("Web组件正在卸载...")
        await self.on_disable()
        self.logger.info("Web组件已卸载")
    
    def get_web_status(self) -> dict:
        """获取Web组件状态"""
        return {
            "enabled": self.is_enabled,
            "server_running": self.web_server is not None,
            "host": getattr(self, 'web_host', '0.0.0.0'),
            "port": getattr(self, 'web_port', 8000),
            "active_connections": 0
        }
    
    async def execute_console_command(self, command: str) -> dict:
        """执行控制台命令（供Web API调用）"""
        try:
            self.logger.info(f"Web界面模拟执行命令: {command}")
            
            return {
                "success": True,
                "command": command,
                "result": f"模拟执行命令: {command}",
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            self.logger.error(f"命令执行失败: {command} - {e}")
            return {
                "success": False,
                "command": command,
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }


# 导出组件类，而不是实例创建函数
WebComponentClass = WebComponent