"""
简化的控制台客户端实现
直接与Aetherius持久化控制台通信，无需导入Core模块
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class SimpleConsoleClient:
    """简化的控制台客户端"""
    
    def __init__(self, socket_path: str):
        self.socket_path = socket_path
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.running = True

    async def connect(self) -> bool:
        """连接到持久化控制台"""
        try:
            self.reader, self.writer = await asyncio.open_unix_connection(self.socket_path)
            logger.info("已连接到持久化控制台")
            return True
        except Exception as e:
            logger.error(f"连接到持久化控制台失败: {e}")
            return False

    async def disconnect(self) -> None:
        """断开连接"""
        self.running = False
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass

    async def send_command(self, command: str) -> Dict[str, Any]:
        """发送命令到服务器"""
        if not self.writer:
            return {"success": False, "error": "未连接到控制台"}

        try:
            message = {
                "type": "command",
                "command": command
            }

            data = json.dumps(message) + '\n'
            self.writer.write(data.encode())
            await self.writer.drain()

            # 等待响应
            response_data = await asyncio.wait_for(self.reader.readline(), timeout=5.0)
            response = json.loads(response_data.decode().strip())

            return response

        except asyncio.TimeoutError:
            logger.error("命令响应超时")
            return {"success": False, "error": "命令响应超时"}
        except Exception as e:
            logger.error(f"发送命令失败: {e}")
            return {"success": False, "error": str(e)}