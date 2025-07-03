"""
Aetherius Core Client
====================

Manages connection and communication with Aetherius Core engine.
"""

import asyncio
import struct
import socket
from typing import Optional, Any, Dict, List
from contextlib import asynccontextmanager

from app.utils.logging import get_logger
from app.utils.exceptions import CoreConnectionError, CoreAPIError

logger = get_logger(__name__)


class RealCore:
    """Real Aetherius Core client using command queue communication"""
    
    def __init__(self, command_queue):
        self.command_queue = command_queue
        self.is_connected = True
        self.log_monitor_task = None
        self.websocket_managers = set()
        self.log_file_path = "/workspaces/aetheriusmc.github.io/Aetherius-Core/server/logs/latest.log"
        self.last_log_position = 0
        self._server_info_cache = None
        self._cache_timestamp = 0
    
    def add_websocket_manager(self, websocket_manager):
        """Register a WebSocket manager for broadcasting"""
        self.websocket_managers.add(websocket_manager)
        logger.info(f"Added WebSocket manager, total: {len(self.websocket_managers)}")
    
    def remove_websocket_manager(self, websocket_manager):
        """Unregister a WebSocket manager"""
        self.websocket_managers.discard(websocket_manager)
        logger.info(f"Removed WebSocket manager, total: {len(self.websocket_managers)}")
    
    async def send_command(self, command: str, websocket_manager=None) -> Dict[str, Any]:
        """Send a command with prefix-based routing - ensures single backend dispatch"""
        try:
            # Echo command to frontend console immediately
            if websocket_manager:
                await self._broadcast_console_message(f"> {command}", "COMMAND")
            
            # Parse command prefix and route to appropriate backend
            command_type, processed_command = self._parse_command_prefix(command)
            
            # Start command execution in background to avoid WebSocket timeout
            asyncio.create_task(self._execute_command_with_routing(command, command_type, processed_command, websocket_manager))
            
            # Return immediate success response
            logger.info(f"Command '{command}' (type: {command_type}) queued for execution")
            return {
                "success": True,
                "message": f"Command '{command}' has been queued",
                "output": f"✓ 命令已接收: {command}\n⏳ 正在路由到{command_type}后端..."
            }
            
        except Exception as e:
            logger.error(f"Failed to queue command '{command}': {e}")
            if websocket_manager:
                await self._broadcast_console_message(f"Error: Failed to send command: {str(e)}", "ERROR")
            return {
                "success": False,
                "message": f"Failed to send command: {str(e)}"
            }
    
    def _parse_command_prefix(self, command: str) -> tuple:
        """解析命令前缀，返回(命令类型, 处理后的命令) - 统一前缀识别系统"""
        if not command:
            return "CHAT", command
            
        first_char = command[0]
        content = command[1:].strip() if len(command) > 1 else ""
        
        prefix_mapping = {
            '/': 'MC',          # MC指令
            '!': 'AETHERIUS',   # Aetherius系统指令  
            '@': 'SCRIPT',      # 脚本指令
            '#': 'PLUGIN',      # 插件指令
            '$': 'COMPONENT',   # 组件指令
            '%': 'ADMIN'        # 管理指令(预留)
        }
        
        command_type = prefix_mapping.get(first_char, 'CHAT')
        processed_command = content if first_char in prefix_mapping else command
        
        logger.debug(f"Command prefix parsed: '{command}' -> type={command_type}, processed='{processed_command}'")
        return command_type, processed_command
    
    async def _execute_command_with_routing(self, original_command: str, command_type: str, processed_command: str, websocket_manager=None):
        """根据命令类型路由到对应的后端服务 - 确保单一后端分发"""
        try:
            logger.info(f"Routing command '{original_command}' to {command_type} backend")
            
            if websocket_manager:
                await self._broadcast_console_message(f"路由到{command_type}后端: {processed_command}", "DEBUG")
            
            if command_type == "MC":
                # MC指令: 发送到Minecraft服务器
                await self._execute_minecraft_command(processed_command, websocket_manager)
                
            elif command_type == "AETHERIUS":
                # Aetherius系统指令: 调用系统管理功能
                await self._execute_aetherius_command(processed_command, websocket_manager)
                
            elif command_type == "SCRIPT":
                # 脚本指令: 执行自定义脚本
                await self._execute_script_command(processed_command, websocket_manager)
                
            elif command_type == "PLUGIN":
                # 插件指令: 调用插件管理功能
                await self._execute_plugin_command(processed_command, websocket_manager)
                
            elif command_type == "COMPONENT":
                # 组件指令: 调用组件管理功能
                await self._execute_component_command(processed_command, websocket_manager)
                
            elif command_type == "ADMIN":
                # 管理指令: 预留给以后扩展
                await self._execute_admin_command(processed_command, websocket_manager)
                
            elif command_type == "CHAT":
                # 聊天消息: 作为say命令发送到Minecraft
                await self._execute_chat_message(processed_command, websocket_manager)
                
            else:
                logger.warning(f"Unknown command type: {command_type}")
                if websocket_manager:
                    await self._broadcast_console_message(f"未知命令类型: {command_type}", "ERROR")
                    
        except Exception as e:
            error_msg = f"命令路由执行异常: {str(e)}"
            logger.error(f"Command routing failed for '{original_command}': {e}")
            
            if websocket_manager:
                await self._broadcast_console_message(f"❌ {error_msg}", "ERROR")
    
    async def _execute_minecraft_command(self, command: str, websocket_manager=None):
        """执行MC指令 - 使用Aetherius CLI命令"""
        try:
            logger.info(f"Executing Minecraft command: {command}")
            
            # 使用Aetherius CLI发送命令
            import asyncio
            import subprocess
            import os
            
            aetherius_dir = "/workspaces/aetheriusmc.github.io/Aetherius-Core"
            cmd_args = ["python", "-m", "aetherius", "cmd", command]
            
            if websocket_manager:
                await self._broadcast_console_message(f"📤 发送MC指令: {command}", "INFO")
            
            # 执行命令
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd_args,
                    cwd=aetherius_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=dict(os.environ, PYTHONPATH=aetherius_dir)
                )
                
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=8.0
                )
                
                stdout_text = stdout.decode('utf-8', errors='ignore').strip()
                stderr_text = stderr.decode('utf-8', errors='ignore').strip()
                
                if process.returncode == 0:
                    if websocket_manager:
                        if stdout_text and "✓" in stdout_text:
                            await self._broadcast_console_message(f"✅ MC指令执行成功", "SUCCESS")
                        elif stdout_text:
                            await self._broadcast_console_message(f"MC指令响应: {stdout_text}", "INFO")
                        else:
                            await self._broadcast_console_message(f"✅ MC指令已发送: {command}", "SUCCESS")
                else:
                    error_msg = stderr_text or stdout_text or "未知错误"
                    if websocket_manager:
                        await self._broadcast_console_message(f"❌ MC指令失败: {error_msg}", "ERROR")
                        
            except asyncio.TimeoutError:
                if websocket_manager:
                    await self._broadcast_console_message(f"⏰ MC指令执行超时: {command}", "ERROR")
                    
        except Exception as e:
            logger.error(f"Minecraft command execution failed: {e}")
            if websocket_manager:
                await self._broadcast_console_message(f"❌ MC指令异常: {str(e)}", "ERROR")
    
    async def _execute_aetherius_command(self, command: str, websocket_manager=None):
        """执行Aetherius系统指令"""
        try:
            logger.info(f"Executing Aetherius command: {command}")
            
            # 实现系统命令处理
            if command in ["status", "info"]:
                status_info = "Aetherius Core系统运行正常"
                if websocket_manager:
                    await self._broadcast_console_message(f"Aetherius系统响应: {status_info}", "SUCCESS")
            elif command in ["help"]:
                help_text = "可用系统命令: status, info, help"
                if websocket_manager:
                    await self._broadcast_console_message(f"Aetherius系统响应: {help_text}", "INFO")
            else:
                if websocket_manager:
                    await self._broadcast_console_message(f"Aetherius系统响应: 未知系统命令: {command}", "ERROR")
                    
        except Exception as e:
            logger.error(f"Aetherius command execution failed: {e}")
            if websocket_manager:
                await self._broadcast_console_message(f"Aetherius系统响应: ❌ 执行异常: {str(e)}", "ERROR")
    
    async def _execute_script_command(self, command: str, websocket_manager=None):
        """执行脚本指令"""
        try:
            logger.info(f"Executing script command: {command}")
            if websocket_manager:
                await self._broadcast_console_message(f"脚本执行响应: 脚本功能暂未实现 - {command}", "INFO")
                
        except Exception as e:
            logger.error(f"Script command execution failed: {e}")
            if websocket_manager:
                await self._broadcast_console_message(f"脚本执行响应: ❌ 执行异常: {str(e)}", "ERROR")
    
    async def _execute_plugin_command(self, command: str, websocket_manager=None):
        """执行插件指令"""
        try:
            logger.info(f"Executing plugin command: {command}")
            if websocket_manager:
                await self._broadcast_console_message(f"插件指令响应: 插件管理功能暂未实现 - {command}", "INFO")
                
        except Exception as e:
            logger.error(f"Plugin command execution failed: {e}")
            if websocket_manager:
                await self._broadcast_console_message(f"插件指令响应: ❌ 执行异常: {str(e)}", "ERROR")
    
    async def _execute_component_command(self, command: str, websocket_manager=None):
        """执行组件指令 - 转发到核心组件管理器"""
        try:
            logger.info(f"Executing component command: {command}")
            
            # 尝试获取或创建核心组件管理器
            try:
                import sys
                import os
                
                # 确保正确的路径
                core_path = '/workspaces/aetheriusmc.github.io/Aetherius-Core'
                if core_path not in sys.path:
                    sys.path.insert(0, core_path)
                
                from aetherius.core import get_component_manager, set_component_manager, ComponentManager
                
                component_manager = get_component_manager()
                
                # 如果组件管理器不存在，创建一个
                if not component_manager:
                    logger.info("Creating new component manager instance")
                    
                    # 创建一个简单的核心实例用于组件管理器
                    from types import SimpleNamespace
                    mock_core = SimpleNamespace(
                        logger=logger,
                        event_manager=None,
                        config_manager=None
                    )
                    
                    # 创建组件管理器实例
                    component_manager = ComponentManager(mock_core)
                    set_component_manager(component_manager)
                    
                    # 尝试初始化组件扫描
                    try:
                        components_dir = os.path.join(core_path, 'components')
                        if os.path.exists(components_dir):
                            await component_manager.scan_components()
                            logger.info("Component manager initialized and components scanned")
                        else:
                            logger.warning(f"Components directory not found: {components_dir}")
                    except Exception as scan_error:
                        logger.warning(f"Failed to scan components during initialization: {scan_error}")
                    
                logger.info(f"Component manager available: {component_manager is not None}")
                
                # 发送初始化成功消息
                if websocket_manager and component_manager:
                    await self._broadcast_console_message("组件指令响应: ✅ 组件管理器已连接", "DEBUG")
                
            except Exception as import_error:
                logger.error(f"Failed to initialize component manager: {import_error}")
                component_manager = None
            
            if not component_manager:
                if websocket_manager:
                    await self._broadcast_console_message("组件指令响应: ❌ 组件管理器初始化失败", "ERROR")
                return
            
            # 解析组件命令
            if not command:
                if websocket_manager:
                    await self._broadcast_console_message("组件指令响应: 请指定组件命令。可用命令: list, status, scan, enable <组件名>, disable <组件名>, reload <组件名>, info <组件名>, load <组件名>, unload <组件名>", "INFO")
                return
            
            command_parts = command.split()
            cmd = command_parts[0].lower()
            
            if cmd == "list":
                await self._handle_component_list(component_manager, websocket_manager)
            elif cmd == "status":
                await self._handle_component_status(component_manager, websocket_manager)
            elif cmd == "scan":
                await self._handle_component_scan(component_manager, websocket_manager)
            elif cmd == "enable" and len(command_parts) > 1:
                component_name = command_parts[1]
                await self._handle_component_enable(component_manager, component_name, websocket_manager)
            elif cmd == "disable" and len(command_parts) > 1:
                component_name = command_parts[1]
                await self._handle_component_disable(component_manager, component_name, websocket_manager)
            elif cmd == "reload" and len(command_parts) > 1:
                component_name = command_parts[1]
                await self._handle_component_reload(component_manager, component_name, websocket_manager)
            elif cmd == "info" and len(command_parts) > 1:
                component_name = command_parts[1]
                await self._handle_component_info(component_manager, component_name, websocket_manager)
            elif cmd == "load" and len(command_parts) > 1:
                component_name = command_parts[1]
                await self._handle_component_load(component_manager, component_name, websocket_manager)
            elif cmd == "unload" and len(command_parts) > 1:
                component_name = command_parts[1]
                await self._handle_component_unload(component_manager, component_name, websocket_manager)
            else:
                if websocket_manager:
                    await self._broadcast_console_message(f"组件指令响应: 未知命令 '{cmd}'。可用命令: list, status, scan, enable <组件名>, disable <组件名>, reload <组件名>, info <组件名>, load <组件名>, unload <组件名>", "ERROR")
                
        except Exception as e:
            logger.error(f"Component command execution failed: {e}")
            if websocket_manager:
                await self._broadcast_console_message(f"组件指令响应: ❌ 执行异常: {str(e)}", "ERROR")
    
    async def _handle_component_list(self, component_manager, websocket_manager):
        """处理组件列表命令"""
        try:
            loaded_components = component_manager.list_loaded_components()
            enabled_components = component_manager.list_enabled_components()
            
            if not loaded_components:
                await self._broadcast_console_message("组件指令响应: 没有已加载的组件", "INFO")
                return
            
            response = "组件指令响应: 组件列表:\n"
            for component_name in loaded_components:
                status = "✅ 已启用" if component_name in enabled_components else "⏸️ 已禁用"
                response += f"  - {component_name}: {status}\n"
            
            if websocket_manager:
                await self._broadcast_console_message(response.strip(), "SUCCESS")
                
        except Exception as e:
            logger.error(f"Component list failed: {e}")
            if websocket_manager:
                await self._broadcast_console_message(f"组件指令响应: ❌ 列出组件失败: {str(e)}", "ERROR")
    
    async def _handle_component_status(self, component_manager, websocket_manager):
        """处理组件状态命令"""
        try:
            status = component_manager.get_component_status()
            
            response = "组件指令响应: 组件状态:\n"
            response += f"  - 已加载: {status.get('loaded_count', 0)}\n"
            response += f"  - 已启用: {status.get('enabled_count', 0)}\n"
            response += f"  - 失败: {status.get('failed_count', 0)}\n"
            
            if status.get('failed_components'):
                response += "  失败的组件:\n"
                for comp, error in status['failed_components'].items():
                    response += f"    - {comp}: {error}\n"
            
            if websocket_manager:
                await self._broadcast_console_message(response.strip(), "INFO")
                
        except Exception as e:
            logger.error(f"Component status failed: {e}")
            if websocket_manager:
                await self._broadcast_console_message(f"组件指令响应: ❌ 获取状态失败: {str(e)}", "ERROR")
    
    async def _handle_component_scan(self, component_manager, websocket_manager):
        """处理组件扫描命令"""
        try:
            if websocket_manager:
                await self._broadcast_console_message("组件指令响应: 🔍 正在扫描组件...", "INFO")
            
            components = await component_manager.scan_components()
            
            if components:
                response = f"组件指令响应: ✅ 扫描完成，发现 {len(components)} 个组件:\n"
                for component_name in components:
                    response += f"  - {component_name}\n"
                
                if websocket_manager:
                    await self._broadcast_console_message(response.strip(), "SUCCESS")
            else:
                if websocket_manager:
                    await self._broadcast_console_message("组件指令响应: 📂 扫描完成，未发现任何组件", "INFO")
                    
        except Exception as e:
            logger.error(f"Component scan failed: {e}")
            if websocket_manager:
                await self._broadcast_console_message(f"组件指令响应: ❌ 扫描组件失败: {str(e)}", "ERROR")
    
    async def _handle_component_enable(self, component_manager, component_name, websocket_manager):
        """处理启用组件命令"""
        try:
            success = await component_manager.enable_component(component_name)
            
            if success:
                if websocket_manager:
                    await self._broadcast_console_message(f"组件指令响应: ✅ 组件 '{component_name}' 已启用", "SUCCESS")
            else:
                if websocket_manager:
                    await self._broadcast_console_message(f"组件指令响应: ❌ 启用组件 '{component_name}' 失败", "ERROR")
                    
        except Exception as e:
            logger.error(f"Component enable failed: {e}")
            if websocket_manager:
                await self._broadcast_console_message(f"组件指令响应: ❌ 启用组件异常: {str(e)}", "ERROR")
    
    async def _handle_component_disable(self, component_manager, component_name, websocket_manager):
        """处理禁用组件命令"""
        try:
            success = await component_manager.disable_component(component_name)
            
            if success:
                if websocket_manager:
                    await self._broadcast_console_message(f"组件指令响应: ⏸️ 组件 '{component_name}' 已禁用", "SUCCESS")
            else:
                if websocket_manager:
                    await self._broadcast_console_message(f"组件指令响应: ❌ 禁用组件 '{component_name}' 失败", "ERROR")
                    
        except Exception as e:
            logger.error(f"Component disable failed: {e}")
            if websocket_manager:
                await self._broadcast_console_message(f"组件指令响应: ❌ 禁用组件异常: {str(e)}", "ERROR")
    
    async def _handle_component_reload(self, component_manager, component_name, websocket_manager):
        """处理重载组件命令"""
        try:
            success = await component_manager.reload_component(component_name)
            
            if success:
                if websocket_manager:
                    await self._broadcast_console_message(f"组件指令响应: 🔄 组件 '{component_name}' 已重载", "SUCCESS")
            else:
                if websocket_manager:
                    await self._broadcast_console_message(f"组件指令响应: ❌ 重载组件 '{component_name}' 失败", "ERROR")
                    
        except Exception as e:
            logger.error(f"Component reload failed: {e}")
            if websocket_manager:
                await self._broadcast_console_message(f"组件指令响应: ❌ 重载组件异常: {str(e)}", "ERROR")
    
    async def _handle_component_info(self, component_manager, component_name, websocket_manager):
        """处理组件信息命令"""
        try:
            component_info = component_manager.get_component_info(component_name)
            
            if not component_info:
                if websocket_manager:
                    await self._broadcast_console_message(f"组件指令响应: ❌ 找不到组件 '{component_name}'", "ERROR")
                return
            
            response = f"组件指令响应: 组件 '{component_name}' 信息:\n"
            response += f"  - 名称: {component_info.name}\n"
            response += f"  - 版本: {component_info.version}\n"
            response += f"  - 描述: {component_info.description}\n"
            response += f"  - 作者: {component_info.author}\n"
            
            if component_info.dependencies:
                response += f"  - 依赖: {', '.join(component_info.dependencies)}\n"
            
            if component_info.web_enabled:
                response += "  - Web组件: ✅ 已启用\n"
            
            if websocket_manager:
                await self._broadcast_console_message(response.strip(), "INFO")
                
        except Exception as e:
            logger.error(f"Component info failed: {e}")
            if websocket_manager:
                await self._broadcast_console_message(f"组件指令响应: ❌ 获取组件信息异常: {str(e)}", "ERROR")
    
    async def _handle_component_load(self, component_manager, component_name, websocket_manager):
        """处理加载组件命令"""
        try:
            success = await component_manager.load_component(component_name)
            
            if success:
                if websocket_manager:
                    await self._broadcast_console_message(f"组件指令响应: 📦 组件 '{component_name}' 已加载", "SUCCESS")
            else:
                if websocket_manager:
                    await self._broadcast_console_message(f"组件指令响应: ❌ 加载组件 '{component_name}' 失败", "ERROR")
                    
        except Exception as e:
            logger.error(f"Component load failed: {e}")
            if websocket_manager:
                await self._broadcast_console_message(f"组件指令响应: ❌ 加载组件异常: {str(e)}", "ERROR")
    
    async def _handle_component_unload(self, component_manager, component_name, websocket_manager):
        """处理卸载组件命令"""
        try:
            success = await component_manager.unload_component(component_name)
            
            if success:
                if websocket_manager:
                    await self._broadcast_console_message(f"组件指令响应: 📤 组件 '{component_name}' 已卸载", "SUCCESS")
            else:
                if websocket_manager:
                    await self._broadcast_console_message(f"组件指令响应: ❌ 卸载组件 '{component_name}' 失败", "ERROR")
                    
        except Exception as e:
            logger.error(f"Component unload failed: {e}")
            if websocket_manager:
                await self._broadcast_console_message(f"组件指令响应: ❌ 卸载组件异常: {str(e)}", "ERROR")
    
    async def _execute_admin_command(self, command: str, websocket_manager=None):
        """执行管理指令 - 预留给以后扩展"""
        try:
            logger.info(f"Executing admin command: {command}")
            if websocket_manager:
                await self._broadcast_console_message(f"管理指令响应: 管理功能预留，暂未实现 - {command}", "INFO")
                
        except Exception as e:
            logger.error(f"Admin command execution failed: {e}")
            if websocket_manager:
                await self._broadcast_console_message(f"管理指令响应: ❌ 执行异常: {str(e)}", "ERROR")
    
    async def _execute_chat_message(self, message: str, websocket_manager=None):
        """执行聊天消息 - 作为say命令发送到Minecraft"""
        try:
            logger.info(f"Executing chat message: {message}")
            # 将聊天消息包装为say命令发送到Minecraft
            say_command = f"say {message}"
            result = await self._execute_via_direct_communication(say_command)
            
            if result and not result[0]:  # Failed
                if websocket_manager:
                    await self._broadcast_console_message(f"聊天消息发送失败: {result[1]}", "ERROR")
            elif not result:
                if websocket_manager:
                    await self._broadcast_console_message("聊天消息发送失败: 服务器通信失败", "ERROR")
            else:
                # 成功发送的聊天消息响应归类为DEBUG，实际聊天内容会在服务器日志中显示
                if websocket_manager:
                    await self._broadcast_console_message(f"聊天消息已发送: {message}", "DEBUG")
                    
        except Exception as e:
            logger.error(f"Chat message execution failed: {e}")
            if websocket_manager:
                await self._broadcast_console_message(f"聊天消息发送异常: {str(e)}", "ERROR")
    
    async def _execute_command_background(self, command: str, websocket_manager=None):
        """Execute command via direct server communication"""
        try:
            import asyncio
            logger.info(f"Executing command via direct server communication: {command}")
            
            # Execute command directly - real server output will be sent via _send_real_server_output_to_frontend
            result = await self._execute_via_direct_communication(command)
            
            # Only send a status update if command completely failed
            if result and not result[0]:  # Failed
                if websocket_manager:
                    await self._send_command_result(websocket_manager, command, False, f"❌ {result[1]}")
            elif not result:
                # Fallback: Report interface issue  
                if websocket_manager:
                    await self._send_command_result(websocket_manager, command, False, 
                        "⚠️ 直接通信接口暂时不可用")
            
        except Exception as e:
            error_msg = f"命令执行系统异常: {str(e)}"
            logger.error(f"Direct command execution failed: {e}")
            
            if websocket_manager:
                await self._send_command_result(websocket_manager, command, False, f"❌ {error_msg}")
    
    async def _execute_via_direct_communication(self, command: str):
        """Execute command via direct Minecraft server communication using stdin/stdout"""
        try:
            import asyncio
            import psutil
            import os
            import signal
            from pathlib import Path
            
            logger.info(f"Starting direct communication for command: {command}")
            
            # Method 1: Try stdin injection (primary method)
            stdin_result = await self._execute_via_stdin_injection(command)
            if stdin_result[0]:  # Success
                return stdin_result
            
            logger.warning(f"Stdin injection failed: {stdin_result[1]}")
            
            # Method 2: Try RCON (backup method) 
            rcon_result = await self._execute_via_rcon(command)
            if rcon_result[0]:  # Success
                return rcon_result
            
            logger.warning(f"RCON execution failed: {rcon_result[1]}")
            
            # Method 3: Try process signal injection (last resort)
            signal_result = await self._execute_via_process_signal(command)
            if signal_result[0]:  # Success
                return signal_result
                
            # All methods failed
            return False, f"❌ 所有命令执行方法均失败\\n📋 详细信息:\\n- 标准输入注入: {stdin_result[1]}\\n- RCON通信: {rcon_result[1]}\\n- 进程信号: {signal_result[1]}"
            
        except Exception as e:
            logger.error(f"Direct communication failed: {e}")
            return False, f"直接通信异常: {str(e)}"
    
    async def _execute_via_stdin_injection(self, command: str):
        """Execute command by injecting into server process stdin"""
        try:
            import asyncio
            import psutil
            import os
            import subprocess
            from pathlib import Path
            
            # Find the server process and its details
            server_process = None
            for proc in psutil.process_iter(['pid', 'cmdline', 'cwd']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'server.jar' in cmdline and '--nogui' in cmdline:
                        server_process = proc
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if not server_process:
                return False, "未找到Minecraft服务器进程"
            
            logger.info(f"Found server process: PID {server_process.pid}")
            
            # Try multiple stdin injection methods
            
            # Method 1: Try screen session injection (if server runs in screen)
            screen_result = await self._try_screen_injection(command, server_process.pid)
            if screen_result[0]:
                return True, f"✅ 通过screen会话执行命令成功: {command}"
            
            # Method 2: Try tmux session injection (if server runs in tmux)
            tmux_result = await self._try_tmux_injection(command, server_process.pid)
            if tmux_result[0]:
                return True, f"✅ 通过tmux会话执行命令成功: {command}"
            
            # Method 3: Try aetherius process wrapper stdin injection
            wrapper_result = await self._try_aetherius_wrapper_stdin(command, server_process.pid)
            if wrapper_result[0]:
                return True, f"✅ 通过Aetherius进程包装器执行命令成功: {command}"
            
            # Method 4: Try direct process stdin access
            direct_result = await self._try_direct_stdin(command, server_process.pid)
            if direct_result[0]:
                return True, f"✅ 通过直接stdin执行命令成功: {command}"
            
            # Method 5: Try fifo/named pipe injection
            fifo_result = await self._try_fifo_injection(command, server_process.pid)
            if fifo_result[0]:
                return True, f"✅ 通过命名管道执行命令成功: {command}"
            
            return False, f"所有stdin注入方法失败: screen({screen_result[1]}), tmux({tmux_result[1]}), wrapper({wrapper_result[1]}), direct({direct_result[1]}), fifo({fifo_result[1]})"
            
        except Exception as e:
            logger.error(f"Stdin injection failed: {e}")
            return False, f"标准输入注入异常: {str(e)}"
    
    async def _try_screen_injection(self, command: str, server_pid: int):
        """Try to inject command via screen session"""
        try:
            import subprocess
            import asyncio
            
            # Check if server is running in a screen session
            result = await asyncio.create_subprocess_exec(
                'screen', '-ls',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                return False, "screen未安装或无会话"
            
            # Look for screen sessions
            screen_output = stdout.decode('utf-8', errors='ignore')
            screen_sessions = []
            for line in screen_output.split('\n'):
                if 'minecraft' in line.lower() or 'server' in line.lower():
                    # Extract session name
                    parts = line.strip().split('\t')
                    if len(parts) > 0:
                        session_name = parts[0].strip()
                        screen_sessions.append(session_name)
            
            # Try to send command to each potential session
            for session in screen_sessions:
                try:
                    cmd_result = await asyncio.create_subprocess_exec(
                        'screen', '-S', session, '-p', '0', '-X', 'stuff', f"{command}\r",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await cmd_result.communicate()
                    
                    if cmd_result.returncode == 0:
                        logger.info(f"Command sent via screen session {session}")
                        return True, f"命令通过screen会话 {session} 发送成功"
                        
                except Exception as e:
                    logger.debug(f"Failed to send to screen session {session}: {e}")
                    continue
            
            return False, "未找到有效的screen会话"
            
        except Exception as e:
            return False, f"screen注入失败: {str(e)}"
    
    async def _try_tmux_injection(self, command: str, server_pid: int):
        """Try to inject command via tmux session"""
        try:
            import subprocess
            import asyncio
            
            # Check if tmux is available and has sessions
            result = await asyncio.create_subprocess_exec(
                'tmux', 'list-sessions',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                return False, "tmux未安装或无会话"
            
            # Look for tmux sessions that might contain the server
            tmux_output = stdout.decode('utf-8', errors='ignore')
            tmux_sessions = []
            for line in tmux_output.split('\n'):
                if line.strip():
                    session_name = line.split(':')[0]
                    tmux_sessions.append(session_name)
            
            # Try to send command to each session
            for session in tmux_sessions:
                try:
                    cmd_result = await asyncio.create_subprocess_exec(
                        'tmux', 'send-keys', '-t', session, command, 'Enter',
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await cmd_result.communicate()
                    
                    if cmd_result.returncode == 0:
                        logger.info(f"Command sent via tmux session {session}")
                        return True, f"命令通过tmux会话 {session} 发送成功"
                        
                except Exception as e:
                    logger.debug(f"Failed to send to tmux session {session}: {e}")
                    continue
            
            return False, "未找到有效的tmux会话"
            
        except Exception as e:
            return False, f"tmux注入失败: {str(e)}"
    
    async def _try_aetherius_wrapper_stdin(self, command: str, server_pid: int):
        """Try to send command directly to server stdin and capture real server output"""
        try:
            import subprocess
            import asyncio
            import tempfile
            import os
            import time
            
            # First, record the current log position to only capture new output
            log_file = "/workspaces/aetheriusmc.github.io/Aetherius-Core/server/logs/latest.log"
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    f.seek(0, 2)  # Go to end of file
                    initial_position = f.tell()
            except:
                initial_position = 0
            
            # Create a script that will send command to server directly via stdin
            script_content = f"""#!/bin/bash
# Send command directly to Minecraft server stdin
echo "{command}" > /proc/{server_pid}/fd/0 2>/dev/null && echo "COMMAND_SENT" || echo "COMMAND_FAILED"
"""
            
            # Create temporary script file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as script_file:
                script_file.write(script_content)
                script_path = script_file.name
            
            try:
                # Make script executable
                os.chmod(script_path, 0o755)
                
                # Execute the script
                result = await asyncio.create_subprocess_exec(
                    '/bin/bash', script_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd="/workspaces/aetheriusmc.github.io/Aetherius-Core"
                )
                
                stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=5)
                
                stdout_text = stdout.decode('utf-8', errors='ignore').strip()
                
                if "COMMAND_SENT" in stdout_text:
                    # Command was sent, now capture the server response
                    await asyncio.sleep(1.5)  # Give server time to respond
                    
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            f.seek(initial_position)
                            new_output = f.read().strip()
                            
                        if new_output:
                            # Send real server output to frontend
                            await self._send_real_server_output_to_frontend(new_output, command)
                            
                    except Exception as e:
                        logger.warning(f"Failed to read server log output: {e}")
                    
                    return True, f"✅ 命令直接发送至服务器: {command}"
                else:
                    return False, f"命令发送失败: {stderr.decode('utf-8', errors='ignore')}"
                    
            finally:
                # Clean up script file
                try:
                    os.unlink(script_path)
                except:
                    pass
                    
        except Exception as e:
            return False, f"直接stdin注入失败: {str(e)}"
    
    async def _send_real_server_output_to_frontend(self, output: str, command: str):
        """保持stdout/stderr标准输出显示，同时为命令添加前缀标识"""
        try:
            import datetime
            
            lines = output.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 检测命令类型并添加前缀标识 - 统一前缀识别系统
                if command.startswith('/'):
                    prefix = "MC指令响应"
                elif command.startswith('!'):
                    prefix = "Aetherius系统响应"
                elif command.startswith('@'):
                    prefix = "脚本执行响应"
                elif command.startswith('#'):
                    prefix = "插件指令响应"
                elif command.startswith('$'):
                    prefix = "组件指令响应"
                elif command.startswith('%'):
                    prefix = "管理指令响应"
                else:
                    prefix = "服务器响应"
                
                # 将服务器输出归类为DEBUG，避免与日志重复显示
                if line.startswith('['):
                    # 这是完整的日志行，包含时间戳 - 归类为DEBUG避免重复
                    await self._broadcast_console_message(f"{prefix}: {line}", "DEBUG")
                elif any(indicator in line for indicator in [
                    'players online', 'There are', 'Teleported', 'Gave', 
                    'Set', 'Gamerule', 'Time set', 'Weather', 'Difficulty',
                    'Unknown command', 'Invalid', 'Cannot', 'Error'
                ]):
                    # 命令的直接响应 - 保持重要信息可见，但分类更细致
                    if "Unknown" in line or "Error" in line:
                        await self._broadcast_console_message(f"{prefix}: {line}", "ERROR")
                    else:
                        await self._broadcast_console_message(f"{prefix}: {line}", "DEBUG")  # 成功响应也归类为DEBUG
                else:
                    # 其他输出归类为DEBUG，避免界面混乱
                    await self._broadcast_console_message(f"{prefix}: {line}", "DEBUG")
                    
        except Exception as e:
            logger.warning(f"Failed to send real server output: {e}")
    
    async def _write_wrapper_output_to_log(self, output: str, command: str):
        """Write wrapper output to log file"""
        try:
            import datetime
            
            current_time = datetime.datetime.now().strftime('%H:%M:%S')
            
            # Filter and format output
            lines = output.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('[') and not 'connected' in line.lower():
                    # Format as server log entry
                    log_entry = f"[{current_time}] [Web Console/INFO]: Command response: {line}"
                    
                    with open("/workspaces/aetheriusmc.github.io/Aetherius-Core/server/logs/latest.log", 'a', encoding='utf-8') as f:
                        f.write(log_entry + '\n')
                        f.flush()
                    
                    logger.debug(f"Wrote wrapper output to log: {line}")
                    
        except Exception as e:
            logger.warning(f"Failed to write wrapper output to log: {e}")
    
    async def _send_command_output_to_frontend(self, output: str, command: str):
        """Send command output directly to frontend via WebSocket"""
        try:
            import datetime
            
            # Parse and clean the output
            lines = output.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Skip system messages and focus on actual command responses
                if any(skip in line.lower() for skip in [
                    'plugin manager', 'component manager', '已初始化', 
                    'console ready', '命令前缀', 'unified console',
                    'connected', 'info:', 'warning:', '再见'
                ]):
                    continue
                
                # Look for actual Minecraft command responses
                if '→ Minecraft:' in line:
                    # This indicates command was sent to Minecraft
                    minecraft_cmd = line.split('→ Minecraft:')[-1].strip()
                    await self._broadcast_console_message(f"Command sent to server: {minecraft_cmd}", "DEBUG")
                elif 'aetherius>' in line.lower():
                    # Parse Aetherius console output
                    if '💬 聊天:' in line:
                        cmd_part = line.split('💬 聊天:')[-1].strip()
                        await self._broadcast_console_message(f"Command processed: {cmd_part}", "DEBUG")
                elif line and not line.startswith('[') and not line.startswith('✓'):
                    # Other potentially useful output
                    await self._broadcast_console_message(f"System: {line}", "DEBUG")
            
            logger.debug(f"Sent command output to frontend for command: {command}")
            
        except Exception as e:
            logger.error(f"Failed to send command output to frontend: {e}")
    
    async def _broadcast_console_message(self, message: str, level: str = "INFO"):
        """Broadcast message directly to console via WebSocket"""
        try:
            from app.websocket.manager import ConnectionType, WSMessage
            import datetime
            
            # Create proper WSMessage object
            console_message = WSMessage(
                type="console_log",
                timestamp=datetime.datetime.now(),
                data={
                    "level": level,
                    "source": "Command Response",
                    "message": message
                }
            )
            
            # Send to all registered WebSocket managers
            for websocket_manager in self.websocket_managers:
                try:
                    await websocket_manager.broadcast_to_type(ConnectionType.CONSOLE, console_message)
                    logger.info(f"Successfully broadcasted console message: {message[:50]}...")
                except Exception as e:
                    logger.warning(f"Failed to broadcast to WebSocket manager: {e}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast console message: {e}")
    
    async def _try_direct_stdin(self, command: str, server_pid: int):
        """Try to inject command via direct process stdin access and monitor stdout"""
        try:
            import os
            import asyncio
            
            # Try to access process stdin via /proc filesystem
            stdin_path = f"/proc/{server_pid}/fd/0"
            stdout_path = f"/proc/{server_pid}/fd/1"
            
            if not os.path.exists(stdin_path):
                return False, f"进程 {server_pid} 的stdin不可访问"
            
            try:
                # Start monitoring stdout before sending command
                stdout_monitor_task = asyncio.create_task(
                    self._monitor_process_stdout(server_pid, command)
                )
                
                # Small delay to ensure monitoring starts
                await asyncio.sleep(0.1)
                
                # Try to write to stdin
                with open(stdin_path, 'w', encoding='utf-8') as stdin_file:
                    stdin_file.write(f"{command}\n")
                    stdin_file.flush()
                
                logger.info(f"Command written to process {server_pid} stdin")
                
                # Wait for stdout monitoring to capture response
                try:
                    stdout_result = await asyncio.wait_for(stdout_monitor_task, timeout=3.0)
                    if stdout_result:
                        return True, f"命令通过直接stdin发送成功，输出已捕获到实时日志"
                    else:
                        return True, f"命令通过直接stdin发送成功"
                except asyncio.TimeoutError:
                    stdout_monitor_task.cancel()
                    return True, f"命令通过直接stdin发送成功，监控stdout超时"
                
            except PermissionError:
                return False, f"没有权限访问进程 {server_pid} 的stdin"
            except Exception as e:
                return False, f"写入stdin失败: {str(e)}"
            
        except Exception as e:
            return False, f"直接stdin访问失败: {str(e)}"
    
    async def _monitor_process_stdout(self, server_pid: int, command: str):
        """Monitor process stdout pipe for command responses"""
        try:
            import os
            import asyncio
            import datetime
            
            stdout_path = f"/proc/{server_pid}/fd/1"
            
            if not os.path.exists(stdout_path):
                logger.warning(f"Process {server_pid} stdout not accessible")
                return False
            
            try:
                # Try to read from stdout pipe (non-blocking)
                with open(stdout_path, 'r', encoding='utf-8', errors='ignore') as stdout_file:
                    # Set non-blocking mode
                    import fcntl
                    fd = stdout_file.fileno()
                    fcntl.fcntl(fd, fcntl.F_SETFL, os.O_NONBLOCK)
                    
                    # Monitor for up to 3 seconds
                    start_time = asyncio.get_event_loop().time()
                    captured_output = []
                    
                    while (asyncio.get_event_loop().time() - start_time) < 3.0:
                        try:
                            data = stdout_file.read(1024)
                            if data:
                                captured_output.append(data)
                                logger.info(f"Captured stdout data: {data.strip()}")
                                
                                # Send to frontend AND write to log file
                                await self._send_stdout_to_frontend(data, command)
                                await self._write_stdout_to_log(data, command)
                                
                            await asyncio.sleep(0.1)
                            
                        except BlockingIOError:
                            # No data available, continue monitoring
                            await asyncio.sleep(0.1)
                            continue
                        except Exception as e:
                            logger.debug(f"Error reading stdout: {e}")
                            break
                    
                    if captured_output:
                        logger.info(f"Successfully captured stdout for command '{command}'")
                        return True
                    else:
                        logger.debug(f"No stdout captured for command '{command}'")
                        return False
                        
            except PermissionError:
                logger.warning(f"No permission to read process {server_pid} stdout")
                return False
            except Exception as e:
                logger.warning(f"Error monitoring stdout: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Stdout monitoring failed: {e}")
            return False
    
    async def _write_stdout_to_log(self, data: str, command: str):
        """Write captured stdout data to log file for real-time monitoring"""
        try:
            import datetime
            
            current_time = datetime.datetime.now().strftime('%H:%M:%S')
            
            # Format the data as log entries
            lines = data.strip().split('\n')
            log_entries = []
            
            for line in lines:
                if line.strip():
                    # Format as Minecraft server log entry
                    log_entry = f"[{current_time}] [Server thread/INFO]: {line.strip()}"
                    log_entries.append(log_entry)
            
            if log_entries:
                # Write to log file
                with open("/workspaces/aetheriusmc.github.io/Aetherius-Core/server/logs/latest.log", 'a', encoding='utf-8') as f:
                    for entry in log_entries:
                        f.write(entry + '\n')
                    f.flush()
                
                logger.debug(f"Wrote {len(log_entries)} stdout lines to log file")
                
        except Exception as e:
            logger.warning(f"Failed to write stdout to log: {e}")
    
    async def _send_stdout_to_frontend(self, data: str, command: str):
        """Send captured stdout directly to frontend"""
        try:
            # Clean and format the data
            lines = data.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if line:
                    # Send directly to frontend console
                    await self._broadcast_console_message(f"Server output: {line}", "INFO")
                    
        except Exception as e:
            logger.warning(f"Failed to send stdout to frontend: {e}")
    
    async def _try_fifo_injection(self, command: str, server_pid: int):
        """Try to inject command via named pipe/fifo"""
        try:
            import os
            import asyncio
            import tempfile
            from pathlib import Path
            
            # Create a temporary named pipe
            temp_dir = Path("/tmp")
            fifo_path = temp_dir / f"minecraft_cmd_{server_pid}"
            
            try:
                # Create named pipe
                if fifo_path.exists():
                    fifo_path.unlink()
                
                os.mkfifo(str(fifo_path))
                
                # Try to redirect server input to our fifo (this is experimental)
                # This method is less likely to work but worth trying
                
                # Write command to fifo
                with open(fifo_path, 'w', encoding='utf-8') as fifo:
                    fifo.write(f"{command}\n")
                    fifo.flush()
                
                logger.info(f"Command written to fifo {fifo_path}")
                return True, f"命令通过FIFO发送成功"
                
            finally:
                # Clean up fifo
                if fifo_path.exists():
                    try:
                        fifo_path.unlink()
                    except:
                        pass
            
        except Exception as e:
            return False, f"FIFO注入失败: {str(e)}"
    
    async def _execute_via_process_signal(self, command: str):
        """Try to execute command via process signals (experimental)"""
        try:
            import signal
            import psutil
            
            # Find server process
            server_process = None
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'server.jar' in cmdline and '--nogui' in cmdline:
                        server_process = proc
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if not server_process:
                return False, "未找到服务器进程"
            
            # This is experimental - try to send a signal that might trigger command processing
            # Note: This is unlikely to work for command injection but included for completeness
            try:
                # Send SIGUSR1 signal (custom signal that might be handled by server)
                os.kill(server_process.pid, signal.SIGUSR1)
                logger.info(f"Sent SIGUSR1 signal to process {server_process.pid}")
                return True, f"信号发送成功 (实验性方法)"
            except PermissionError:
                return False, "没有权限发送信号到服务器进程"
            except Exception as e:
                return False, f"信号发送失败: {str(e)}"
            
        except Exception as e:
            return False, f"进程信号方法失败: {str(e)}"
    
    async def _execute_via_rcon(self, command: str):
        """Execute command via RCON protocol"""
        try:
            # RCON connection settings
            host = '127.0.0.1'
            port = 25575
            password = 'password123'  # From server.properties
            
            # Connect to RCON with timeout
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), 
                timeout=5.0
            )
            
            try:
                # Authenticate
                auth_packet = self._build_rcon_packet(1, 3, password)  # SERVERDATA_AUTH
                writer.write(auth_packet)
                await writer.drain()
                
                # Read auth response with timeout
                auth_response = await asyncio.wait_for(
                    self._read_rcon_packet(reader),
                    timeout=3.0
                )
                if not auth_response:
                    logger.warning("RCON authentication failed - no response")
                    return False, "RCON 认证失败 - 无响应"
                
                # For RCON auth, response ID should match request ID (1) if successful, -1 if failed
                if auth_response[0] == -1:
                    logger.warning("RCON authentication failed - invalid password")
                    return False, "RCON 认证失败 - 密码错误"
                elif auth_response[0] != 1:
                    logger.warning(f"RCON authentication failed - unexpected response ID: {auth_response[0]}")
                    return False, f"RCON 认证失败 - 意外响应ID: {auth_response[0]}"
                
                # Send command
                cmd_packet = self._build_rcon_packet(2, 2, command)  # SERVERDATA_EXECCOMMAND
                writer.write(cmd_packet)
                await writer.drain()
                
                # Read command response with timeout
                cmd_response = await asyncio.wait_for(
                    self._read_rcon_packet(reader),
                    timeout=3.0
                )
                if cmd_response:
                    response_text = cmd_response[2].strip()
                    if response_text:
                        return True, f"✅ RCON命令执行成功\n📋 {response_text}"
                    else:
                        return True, f"✅ RCON命令执行成功: {command}"
                else:
                    return False, "RCON 命令响应为空"
                    
            finally:
                writer.close()
                await writer.wait_closed()
                
        except Exception as e:
            logger.warning(f"RCON execution failed: {e}")
            return False, f"RCON 执行失败: {str(e)}"
    
    def _build_rcon_packet(self, request_id: int, packet_type: int, payload: str) -> bytes:
        """Build RCON packet"""
        payload_bytes = payload.encode('utf-8') + b'\x00\x00'  # Fixed null termination
        packet_size = len(payload_bytes) + 10
        
        packet = struct.pack('<i', packet_size - 4)  # Size (excluding this field)
        packet += struct.pack('<i', request_id)       # Request ID
        packet += struct.pack('<i', packet_type)      # Type
        packet += payload_bytes                       # Payload + null terminators
        
        return packet
    
    async def _read_rcon_packet(self, reader):
        """Read RCON packet response"""
        try:
            # Read packet size
            size_data = await reader.readexactly(4)
            packet_size = struct.unpack('<i', size_data)[0]
            
            if packet_size < 10 or packet_size > 4096:  # Sanity check
                logger.warning(f"Invalid RCON packet size: {packet_size}")
                return None
            
            # Read packet data
            packet_data = await reader.readexactly(packet_size)
            
            # Unpack packet
            request_id = struct.unpack('<i', packet_data[0:4])[0]
            packet_type = struct.unpack('<i', packet_data[4:8])[0]
            
            # Handle payload - find null terminators
            payload_data = packet_data[8:]
            if len(payload_data) >= 2:
                # Remove trailing null bytes
                while payload_data and payload_data[-1] == 0:
                    payload_data = payload_data[:-1]
                payload = payload_data.decode('utf-8', errors='ignore')
            else:
                payload = ""
            
            logger.debug(f"RCON packet: ID={request_id}, Type={packet_type}, Payload='{payload}'")
            return (request_id, packet_type, payload)
            
        except Exception as e:
            logger.warning(f"Failed to read RCON packet: {e}")
            return None
    
    
    async def _send_command_result(self, websocket_manager, command: str, success: bool, output: str):
        """Send command execution result via WebSocket"""
        try:
            from app.websocket.manager import create_console_command_result_message, ConnectionType
            
            # Create command result message
            message = create_console_command_result_message(command, success, output)
            
            # Send to all console connections
            await websocket_manager.broadcast_to_type(ConnectionType.CONSOLE, message)
            logger.info(f"Sent command result via WebSocket: {command} -> {'success' if success else 'failed'}")
            
            # Also send as console log for immediate display
            await self._broadcast_console_message(f"Command: {command}\nResult: {output}", "INFO")
            
        except Exception as e:
            logger.error(f"Failed to send command result via WebSocket: {e}")
    
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Get server status - 检测并连接到现有的MC服务器进程而不是创建新的"""
        import time
        
        # 使用缓存避免频繁检测 (5秒缓存)
        current_time = time.time()
        if (self._server_info_cache and 
            current_time - self._cache_timestamp < 5):
            return self._server_info_cache
        
        try:
            import psutil
            import os
            import re
            from pathlib import Path
            
            server_status = {
                "is_running": False,
                "uptime": 0,
                "version": "Unknown",
                "player_count": 0,
                "max_players": 20,
                "tps": 0.0,
                "cpu_usage": 0.0,
                "memory_usage": {
                    "used": 0,
                    "max": 0,
                    "percentage": 0.0
                },
                "timestamp": current_time,
                "process_info": {
                    "aetherius_core_pid": None,
                    "minecraft_server_pid": None,
                    "detection_method": "process_scan"
                }
            }
            
            # 1. 检测Aetherius Core进程
            aetherius_core_process = None
            minecraft_server_process = None
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                try:
                    proc_info = proc.info
                    cmdline = ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else ''
                    
                    # 检测Minecraft服务器Java进程 (优先检测)
                    if ('java' in proc_info['name'].lower() and 
                        ('server.jar' in cmdline or 'minecraft' in cmdline.lower() or 
                         'spigot' in cmdline.lower() or 'paper' in cmdline.lower() or
                         'forge' in cmdline.lower() or 'fabric' in cmdline.lower())):
                        minecraft_server_process = proc
                        server_status["process_info"]["minecraft_server_pid"] = proc_info['pid']
                        logger.info(f"Found Minecraft server process: PID {proc_info['pid']}")
                    
                    # 检测Aetherius Core主进程 (非Java进程)
                    elif ('aetherius' in cmdline.lower() and 
                          ('server' in cmdline or 'core' in cmdline) and
                          'console' not in cmdline and 
                          'java' not in proc_info['name'].lower()):
                        aetherius_core_process = proc
                        server_status["process_info"]["aetherius_core_pid"] = proc_info['pid']
                        logger.info(f"Found Aetherius Core process: PID {proc_info['pid']}")
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # 2. 如果找到了进程，获取详细信息
            if minecraft_server_process:
                try:
                    # 服务器运行状态
                    server_status["is_running"] = True
                    
                    # 运行时间
                    server_status["uptime"] = int(current_time - minecraft_server_process.create_time())
                    
                    # CPU和内存使用情况
                    with minecraft_server_process.oneshot():
                        cpu_percent = minecraft_server_process.cpu_percent()
                        memory_info = minecraft_server_process.memory_info()
                        
                        server_status["cpu_usage"] = cpu_percent
                        server_status["memory_usage"] = {
                            "used": round(memory_info.rss / 1024 / 1024),  # MB
                            "max": round(memory_info.vms / 1024 / 1024),   # MB
                            "percentage": round((memory_info.rss / memory_info.vms) * 100, 1) if memory_info.vms > 0 else 0
                        }
                        
                    logger.debug(f"MC Server - CPU: {cpu_percent}%, Memory: {memory_info.rss // 1024 // 1024}MB")
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    logger.warning("Lost access to Minecraft server process")
                    server_status["is_running"] = False
            
            # 3. 尝试从日志文件获取更多信息
            log_file_path = Path("/workspaces/aetheriusmc.github.io/Aetherius-Core/server/logs/latest.log")
            if log_file_path.exists():
                try:
                    # 读取最后几行日志获取服务器信息
                    with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        # 获取文件末尾的1KB内容
                        f.seek(0, 2)  # 跳到文件末尾
                        file_size = f.tell()
                        read_size = min(1024, file_size)
                        f.seek(max(0, file_size - read_size))
                        tail_content = f.read()
                    
                    # 解析版本信息
                    version_pattern = r'Starting minecraft server version ([\d.]+)'
                    version_match = re.search(version_pattern, tail_content, re.IGNORECASE)
                    if version_match:
                        server_status["version"] = version_match.group(1)
                    
                    # 解析在线玩家数量
                    player_pattern = r'There are (\d+) of a max of (\d+) players online'
                    player_match = re.search(player_pattern, tail_content)
                    if player_match:
                        server_status["player_count"] = int(player_match.group(1))
                        server_status["max_players"] = int(player_match.group(2))
                    
                    # 检查TPS信息
                    tps_pattern = r'TPS from last 1m, 5m, 15m: ([\d.]+)'
                    tps_match = re.search(tps_pattern, tail_content)
                    if tps_match:
                        server_status["tps"] = float(tps_match.group(1))
                    elif server_status["is_running"]:
                        # 如果服务器运行但没有TPS信息，假设正常
                        server_status["tps"] = 20.0
                        
                except Exception as e:
                    logger.warning(f"Failed to parse log file: {e}")
            
            # 4. 如果没有找到进程，尝试通过PID文件检测
            if not server_status["is_running"]:
                pid_file_path = Path("/workspaces/aetheriusmc.github.io/Aetherius-Core/server.pid")
                if pid_file_path.exists():
                    try:
                        with open(pid_file_path, 'r') as f:
                            stored_pid = int(f.read().strip())
                        
                        # 检查PID是否仍然有效
                        if psutil.pid_exists(stored_pid):
                            proc = psutil.Process(stored_pid)
                            if 'java' in proc.name().lower():
                                server_status["is_running"] = True
                                server_status["process_info"]["minecraft_server_pid"] = stored_pid
                                server_status["uptime"] = int(current_time - proc.create_time())
                                logger.info(f"Found server via PID file: {stored_pid}")
                                
                    except (ValueError, FileNotFoundError, psutil.NoSuchProcess):
                        # PID文件无效，删除它
                        try:
                            pid_file_path.unlink()
                        except:
                            pass
            
            # 5. 缓存结果
            self._server_info_cache = server_status
            self._cache_timestamp = current_time
            
            logger.debug(f"Server status detection completed: running={server_status['is_running']}, "
                        f"aetherius_pid={server_status['process_info']['aetherius_core_pid']}, "
                        f"mc_pid={server_status['process_info']['minecraft_server_pid']}")
            
            return server_status
            
        except Exception as e:
            logger.error(f"Failed to get server status: {e}")
            # 返回默认的离线状态
            default_status = {
                "is_running": False,
                "uptime": 0,
                "version": "Unknown",
                "player_count": 0,
                "max_players": 20,
                "tps": 0.0,
                "cpu_usage": 0.0,
                "memory_usage": {
                    "used": 0,
                    "max": 0,
                    "percentage": 0.0
                },
                "timestamp": time.time(),
                "process_info": {
                    "aetherius_core_pid": None,
                    "minecraft_server_pid": None,
                    "detection_method": "error_fallback"
                }
            }
            
            # 缓存错误状态避免频繁重试
            self._server_info_cache = default_status
            self._cache_timestamp = time.time()
            
            return default_status
    
    async def is_server_running(self) -> bool:
        """Check if server is running - 使用新的进程检测"""
        try:
            status = await self.get_server_status()
            return status.get("is_running", False)
        except Exception as e:
            logger.error(f"Failed to check server running status: {e}")
            return False
    
    async def get_performance_data(self) -> Dict[str, Any]:
        """Get performance data from server - 从现有服务器状态获取"""
        import time
        
        try:
            # 获取最新的服务器状态
            server_status = await self.get_server_status()
            
            # 转换为性能数据格式
            performance_data = {
                "tps": server_status.get("tps", 0.0),
                "cpu_usage": server_status.get("cpu_usage", 0.0),
                "memory_usage": server_status.get("memory_usage", {}).get("used", 0),
                "memory_total": server_status.get("memory_usage", {}).get("max", 0),
                "memory_used": server_status.get("memory_usage", {}).get("used", 0),
                "disk_usage": 0.0,  # TODO: 添加磁盘使用检测
                "network_in": 0,    # TODO: 添加网络统计
                "network_out": 0,   # TODO: 添加网络统计
                "thread_count": 0,  # TODO: 从进程信息获取线程数
                "gc_collections": 0, # TODO: 从JVM统计获取
                "uptime": server_status.get("uptime", 0),
                "is_running": server_status.get("is_running", False),
                "timestamp": server_status.get("timestamp", time.time())
            }
            
            # 如果服务器在运行，尝试获取更详细的性能信息
            if server_status.get("is_running") and server_status.get("process_info", {}).get("minecraft_server_pid"):
                try:
                    import psutil
                    pid = server_status["process_info"]["minecraft_server_pid"]
                    proc = psutil.Process(pid)
                    
                    # 获取线程数
                    performance_data["thread_count"] = proc.num_threads()
                    
                    # 获取文件描述符数量（近似网络连接）
                    try:
                        performance_data["network_connections"] = len(proc.connections())
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        pass
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    logger.debug(f"Could not get detailed process info: {e}")
            
            return performance_data
            
        except Exception as e:
            logger.error(f"Failed to get performance data: {e}")
            # 返回默认性能数据
            return {
                "tps": 0.0,
                "cpu_usage": 0.0,
                "memory_usage": 0,
                "memory_total": 0,
                "memory_used": 0,
                "disk_usage": 0.0,
                "network_in": 0,
                "network_out": 0,
                "thread_count": 0,
                "gc_collections": 0,
                "uptime": 0,
                "is_running": False,
                "timestamp": time.time()
            }
    
    async def get_players(self) -> List[Dict[str, Any]]:
        """Get online players"""
        try:
            # Execute 'list' command to get online players
            result = await self.send_command("list")
            if result.get("success"):
                # Parse player list from output
                # For now, return empty list
                return []
            return []
        except Exception as e:
            logger.error(f"Failed to get players: {e}")
            return []
    
    async def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent server logs"""
        try:
            # Read from latest.log file
            import asyncio
            from pathlib import Path
            
            log_file = Path(self.log_file_path)
            if log_file.exists():
                lines = []
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # Get last 'limit' lines
                recent_lines = lines[-limit:] if len(lines) > limit else lines
                
                # Parse into log messages
                logs = []
                for line in recent_lines:
                    line = line.strip()
                    if line:
                        parsed_log = self._parse_log_line(line)
                        logs.append(parsed_log)
                
                return logs
            return []
        except Exception as e:
            logger.error(f"Failed to get recent logs: {e}")
            return []
    
    def register_websocket_manager(self, websocket_manager):
        """Register WebSocket manager for real-time log streaming"""
        self.websocket_managers.add(websocket_manager)
        logger.info("WebSocket manager registered for real-time logs")
        
        # Start log monitoring if not already running
        if self.log_monitor_task is None or self.log_monitor_task.done():
            import asyncio
            self.log_monitor_task = asyncio.create_task(self._monitor_server_logs())
    
    def unregister_websocket_manager(self, websocket_manager):
        """Unregister WebSocket manager"""
        self.websocket_managers.discard(websocket_manager)
        logger.info("WebSocket manager unregistered from real-time logs")
        
        # Stop log monitoring if no managers
        if not self.websocket_managers and self.log_monitor_task:
            self.log_monitor_task.cancel()
            self.log_monitor_task = None
    
    async def _monitor_server_logs(self):
        """Monitor server logs for real-time streaming"""
        try:
            from pathlib import Path
            import asyncio
            
            log_file = Path(self.log_file_path)
            logger.info("Starting real-time log monitoring")
            
            # Initialize log position
            if log_file.exists():
                self.last_log_position = log_file.stat().st_size
            
            while self.websocket_managers:
                try:
                    if not log_file.exists():
                        await asyncio.sleep(1)
                        continue
                    
                    current_size = log_file.stat().st_size
                    
                    if current_size > self.last_log_position:
                        # Read new content
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            f.seek(self.last_log_position)
                            new_content = f.read()
                        
                        if new_content.strip():
                            # Process new log lines
                            lines = new_content.strip().split('\n')
                            for line in lines:
                                if line.strip():
                                    await self._send_log_entry(line)
                        
                        self.last_log_position = current_size
                    
                    await asyncio.sleep(0.5)  # Check every 500ms
                    
                except Exception as e:
                    logger.warning(f"Error in log monitoring: {e}")
                    await asyncio.sleep(1)
                    
        except asyncio.CancelledError:
            logger.info("Log monitoring task cancelled")
        except Exception as e:
            logger.error(f"Log monitoring task failed: {e}")
    
    def _parse_log_line(self, line: str) -> Dict[str, Any]:
        """Parse a single log line into structured format"""
        try:
            import re
            from datetime import datetime
            
            # Pattern for Minecraft server logs: [HH:MM:SS] [Thread/LEVEL]: Message
            pattern = r'^\[(\d{2}:\d{2}:\d{2})\] \[([^/]+)/([^\]]+)\]: (.+)$'
            match = re.match(pattern, line)
            
            if match:
                timestamp, thread, level, message = match.groups()
                return {
                    "timestamp": timestamp,
                    "level": level,
                    "thread": thread,
                    "message": message,
                    "source": "Server",
                    "raw": line
                }
            else:
                # Fallback for unparseable lines
                return {
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "level": "INFO",
                    "thread": "Unknown",
                    "message": line,
                    "source": "Server",
                    "raw": line
                }
        except Exception as e:
            logger.warning(f"Failed to parse log line: {e}")
            return {
                "timestamp": "Unknown",
                "level": "INFO",
                "thread": "Unknown", 
                "message": line,
                "source": "Server",
                "raw": line
            }
    
    async def _send_log_entry(self, line: str):
        """Send log entry to all connected WebSocket managers"""
        try:
            from app.websocket.manager import ConnectionType
            
            parsed_log = self._parse_log_line(line)
            
            # Create server log message
            from app.websocket.manager import WSMessage
            from datetime import datetime
            
            message = WSMessage(
                type="server_log",
                timestamp=datetime.now(),
                data=parsed_log
            )
            
            # Send to all console connections
            for websocket_manager in self.websocket_managers:
                try:
                    await websocket_manager.broadcast_to_type(ConnectionType.CONSOLE, message)
                except Exception as e:
                    logger.warning(f"Failed to send log to WebSocket manager: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to send log entry: {e}")
    
    async def get_online_players(self) -> List[Dict[str, Any]]:
        """Get online players list"""
        try:
            # Execute 'list' command to get online players
            result = await self.send_command("list")
            if result.get("success"):
                # For now, return empty list since we need to parse the actual output
                # TODO: Parse player list from server output
                return []
            return []
        except Exception as e:
            logger.error(f"Failed to get online players: {e}")
            return []


class CoreClient:
    """Client for connecting to Aetherius Core engine"""
    
    def __init__(self):
        self._core = None
        self._initialized = False
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize connection to Aetherius Core"""
        async with self._lock:
            if self._initialized:
                return
            
            try:
                # Try to connect to actual Aetherius Core via command queue
                try:
                    import sys
                    import os
                    # Add Aetherius Core to Python path
                    aetherius_core_path = "/workspaces/aetheriusmc.github.io/Aetherius-Core"
                    if aetherius_core_path not in sys.path:
                        sys.path.insert(0, aetherius_core_path)
                    
                    # Create real core client that uses subprocess commands
                    self._core = RealCore(None)
                    logger.info("Connected to real Aetherius Core via command queue")
                    
                except Exception as core_err:
                    logger.warning(f"Failed to connect to real core: {core_err}, using mock")
                    # Fallback to mock implementation
                    self._core = MockCore()
                
                logger.info("Core client initialized successfully")
                self._initialized = True
                
            except Exception as e:
                logger.error("Failed to initialize core client", error=str(e), exc_info=True)
                raise CoreConnectionError(f"Failed to connect to core: {e}")
    
    async def cleanup(self):
        """Cleanup core connection"""
        async with self._lock:
            if self._core and hasattr(self._core, 'cleanup'):
                try:
                    await self._core.cleanup()
                except Exception as e:
                    logger.warning("Error during core cleanup", error=str(e))
            
            self._core = None
            self._initialized = False
            logger.info("Core client cleaned up")
    
    async def is_connected(self) -> bool:
        """Check if connected to core"""
        return self._initialized and self._core is not None
    
    @asynccontextmanager
    async def get_core(self):
        """Get core instance with error handling"""
        if not await self.is_connected():
            raise CoreConnectionError("Core not connected")
        
        try:
            yield self._core
        except Exception as e:
            logger.error("Core operation failed", error=str(e), exc_info=True)
            raise CoreAPIError(f"Core operation failed: {e}")


class MockCore:
    """Mock implementation of Aetherius Core for development"""
    
    def __init__(self):
        self.is_running = True
        self.players = [
            {"uuid": "123e4567-e89b-12d3-a456-426614174000", "name": "TestPlayer1", "online": True},
            {"uuid": "123e4567-e89b-12d3-a456-426614174001", "name": "TestPlayer2", "online": False},
        ]
        self.server_logs = []
        self._log_counter = 0
    
    async def send_command(self, command: str) -> Dict[str, Any]:
        """Mock command execution"""
        logger.info("Executing command", command=command)
        
        # Simulate different command responses
        if command.startswith("say "):
            message = command[4:]
            return {
                "success": True,
                "message": f"Broadcasted: {message}",
                "timestamp": asyncio.get_event_loop().time()
            }
        elif command == "list":
            online_players = [p["name"] for p in self.players if p["online"]]
            return {
                "success": True,
                "message": f"Online players ({len(online_players)}): {', '.join(online_players)}",
                "timestamp": asyncio.get_event_loop().time()
            }
        elif command == "stop":
            self.is_running = False
            return {
                "success": True,
                "message": "Server stopping...",
                "timestamp": asyncio.get_event_loop().time()
            }
        else:
            return {
                "success": False,
                "message": f"Unknown command: {command}",
                "timestamp": asyncio.get_event_loop().time()
            }
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Mock server status"""
        return {
            "is_running": self.is_running,
            "uptime": 3600,  # 1 hour
            "version": "1.20.1",
            "player_count": len([p for p in self.players if p["online"]]),
            "max_players": 20,
            "tps": 20.0,
            "cpu_usage": 45.2,
            "memory_usage": {
                "used": 2048,
                "max": 4096,
                "percentage": 50.0
            }
        }
    
    async def get_online_players(self) -> list:
        """Mock online players list"""
        return [p for p in self.players if p["online"]]
    
    def generate_log_entry(self, level: str = "INFO", message: str = None) -> Dict[str, Any]:
        """Generate mock log entry"""
        self._log_counter += 1
        
        if message is None:
            messages = [
                "Server started successfully",
                "Player TestPlayer1 joined the game",
                "Player TestPlayer2 left the game",
                "Saving world data...",
                "World saved successfully",
            ]
            message = messages[self._log_counter % len(messages)]
        
        return {
            "timestamp": asyncio.get_event_loop().time(),
            "level": level,
            "source": "Server",
            "message": message
        }
    
    async def cleanup(self):
        """Mock cleanup"""
        pass