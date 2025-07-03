#!/usr/bin/env python3
"""
持久化控制台守护进程
作为Minecraft服务器的父进程，保持stdin/stdout管道控制
完全避免RCON，使用纯粹的IO管道实现命令执行和响应捕获
"""

import asyncio
import json
import logging
import os
import signal
import socket
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class PersistentConsoleDaemon:
    """持久化控制台守护进程 - 作为服务器的父进程"""

    def __init__(self, server_jar_path: str, server_dir: str):
        self.server_jar_path = server_jar_path
        self.server_dir = Path(server_dir)

        # Unix socket服务器
        self.socket_path = str(Path("data/console/console.sock").absolute())
        self.server_socket: Optional[socket.socket] = None
        self.clients = []

        # 服务器进程管理
        self.server_process: Optional[asyncio.subprocess.Process] = None

        # 命令响应缓存
        self.command_responses: dict[str, str] = {}
        self.recent_commands: dict[str, float] = {}

        # 监控任务
        self.stdout_monitor_task: Optional[asyncio.Task] = None
        self.stderr_monitor_task: Optional[asyncio.Task] = None

        # 组件管理器
        self.component_manager = None
        self._init_component_manager()

        # 系统信息
        self.start_time = asyncio.get_event_loop().time()
        self.command_count = 0

        # 插件管理器
        self.plugin_manager = None
        self._init_plugin_manager()

    def _init_component_manager(self):
        """初始化组件管理器"""
        try:
            from types import SimpleNamespace

            from .component_manager import ComponentManager

            # 创建简单的核心实例
            mock_core = SimpleNamespace(
                event_manager=None,
                config_manager=None,
                logger=logger,
            )

            self.component_manager = ComponentManager(mock_core)
            logger.info("组件管理器初始化成功")
        except Exception as e:
            logger.error(f"组件管理器初始化失败: {e}")
            self.component_manager = None

    def _init_plugin_manager(self):
        """初始化插件管理器"""
        try:
            from ..api.plugin_manager import get_plugin_manager

            self.plugin_manager = get_plugin_manager()
            logger.info("插件管理器初始化成功")
        except Exception as e:
            logger.error(f"插件管理器初始化失败: {e}")
            self.plugin_manager = None

    async def start(self) -> None:
        """启动控制台守护进程和服务器"""
        logger.info("启动持久化控制台守护进程...")

        # 清理旧的socket文件
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)

        # 确保目录存在
        os.makedirs(os.path.dirname(self.socket_path), exist_ok=True)

        # 创建Unix socket服务器
        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(self.socket_path)
        self.server_socket.listen(5)
        self.server_socket.setblocking(False)

        # 设置信号处理
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # 启动Minecraft服务器
        await self._start_server()

        # 启动监控任务
        if self.server_process:
            self.stdout_monitor_task = asyncio.create_task(self._monitor_stdout())
            self.stderr_monitor_task = asyncio.create_task(self._monitor_stderr())

        # 启动客户端接受循环
        await self._accept_clients()

    async def _start_server(self) -> bool:
        """启动Minecraft服务器作为子进程"""
        try:
            # 构建启动命令
            cmd = [
                "java",
                "-Xms2G",
                "-Xmx4G",
                "-jar",
                self.server_jar_path,
                "--nogui"
            ]

            logger.info(f"启动服务器: {' '.join(cmd)}")
            logger.info(f"工作目录: {self.server_dir}")

            # 启动服务器进程
            self.server_process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.server_dir,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=os.setpgrp  # 进程组分离
            )

            logger.info(f"✅ 服务器进程已启动，PID: {self.server_process.pid}")
            return True

        except Exception as e:
            logger.error(f"❌ 启动服务器失败: {e}")
            return False

    async def _monitor_stdout(self) -> None:
        """监控服务器标准输出"""
        if not self.server_process or not self.server_process.stdout:
            return

        try:
            while self.server_process.returncode is None:
                line = await self.server_process.stdout.readline()
                if not line:
                    break

                line_str = line.decode('utf-8', errors='replace').strip()
                if line_str:
                    logger.info(f"服务器输出: {line_str}")

                    # 广播给所有客户端
                    await self._broadcast_log(line_str)

                    # 检查命令响应
                    await self._check_command_response(line_str)

        except Exception as e:
            logger.error(f"监控stdout时出错: {e}")

    async def _monitor_stderr(self) -> None:
        """监控服务器标准错误"""
        if not self.server_process or not self.server_process.stderr:
            return

        try:
            while self.server_process.returncode is None:
                line = await self.server_process.stderr.readline()
                if not line:
                    break

                line_str = line.decode('utf-8', errors='replace').strip()
                if line_str:
                    logger.warning(f"服务器错误: {line_str}")

                    # 广播给所有客户端
                    await self._broadcast_log(line_str, is_error=True)

        except Exception as e:
            logger.error(f"监控stderr时出错: {e}")

    async def _check_command_response(self, line: str) -> None:
        """检查是否是命令响应"""
        current_time = asyncio.get_event_loop().time()

        # 检查最近发送的命令
        for command, send_time in list(self.recent_commands.items()):
            # 只匹配最近10秒内发送的命令
            if current_time - send_time > 10.0:
                del self.recent_commands[command]
                continue

            # 检查是否匹配命令输出
            if self._is_command_response(command, line):
                self.command_responses[command] = line
                logger.info(f"匹配到命令 '{command}' 的响应: {line}")
                break

    def _is_command_response(self, command: str, line: str) -> bool:
        """检查日志行是否是指定命令的响应"""
        command_lower = command.lower().strip()
        line_lower = line.lower()

        # 常见命令的响应模式
        patterns = {
            "list": ["players online", "there are"],
            "time": ["the time is"],
            "difficulty": ["difficulty"],
            "weather": ["weather", "changing"],
            "help": ["help", "available commands"],
            "stop": ["stopping", "server"],
        }

        for cmd_pattern, response_patterns in patterns.items():
            if cmd_pattern in command_lower:
                for pattern in response_patterns:
                    if pattern in line_lower:
                        return True

        # 检查错误响应
        error_patterns = ["unknown command", "incorrect", "cannot", "failed", "error"]
        for pattern in error_patterns:
            if pattern in line_lower:
                return True

        return False

    async def _accept_clients(self) -> None:
        """接受客户端连接"""
        logger.info("开始接受客户端连接...")

        try:
            while True:
                # 等待客户端连接
                loop = asyncio.get_event_loop()
                client_socket, _ = await loop.sock_accept(self.server_socket)
                client_socket.setblocking(False)

                # 创建流
                reader, writer = await asyncio.open_connection(sock=client_socket)

                # 添加到客户端列表
                self.clients.append(writer)

                # 处理客户端
                asyncio.create_task(self._handle_client(reader, writer))

                logger.info(f"客户端已连接，当前连接数: {len(self.clients)}")

        except Exception as e:
            logger.error(f"接受客户端连接时出错: {e}")

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """处理单个客户端"""
        try:
            while True:
                # 读取客户端消息
                data = await reader.readline()
                if not data:
                    break

                try:
                    # 解析JSON消息
                    message = json.loads(data.decode().strip())
                    msg_type = message.get("type")

                    if msg_type == "command":
                        # 执行命令
                        command = message.get("command", "")
                        response = await self._execute_command(command)

                        # 添加响应类型标识
                        response["type"] = "response"

                        # 发送响应
                        response_data = json.dumps(response) + '\n'
                        writer.write(response_data.encode())
                        await writer.drain()

                except json.JSONDecodeError:
                    logger.error(f"无法解析客户端消息: {data}")
                except Exception as e:
                    logger.error(f"处理客户端消息时出错: {e}")

        except Exception as e:
            logger.error(f"处理客户端时出错: {e}")
        finally:
            # 移除客户端
            if writer in self.clients:
                self.clients.remove(writer)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _execute_command(self, command: str) -> dict:
        """执行命令 - 支持Minecraft命令和组件指令"""
        command = command.strip()

        # 检查是否是组件指令 (以$开头)
        if command.startswith('$'):
            return await self._execute_component_command(command[1:].strip())

        # 检查是否是Aetherius系统指令 (以!开头)
        if command.startswith('!'):
            return await self._execute_aetherius_command(command[1:].strip())

        # 默认处理Minecraft命令
        if not self.server_process or not self.server_process.stdin:
            return {
                "success": False,
                "error": "服务器进程未运行或stdin不可用",
                "output": ""
            }

        try:
            # 记录命令发送时间
            self.recent_commands[command] = asyncio.get_event_loop().time()

            # 发送命令到服务器stdin
            command_line = f"{command.strip()}\n"
            self.server_process.stdin.write(command_line.encode())
            await self.server_process.stdin.drain()

            logger.info(f"通过stdin发送命令: {command}")

            # 等待响应
            response = await self._wait_for_response(command, timeout=5.0)

            return {
                "success": True,
                "error": None,
                "output": response
            }

        except Exception as e:
            logger.error(f"执行命令失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    async def _wait_for_response(self, command: str, timeout: float = 5.0) -> str:
        """等待命令响应"""
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            if command in self.command_responses:
                response = self.command_responses[command]
                del self.command_responses[command]
                if command in self.recent_commands:
                    del self.recent_commands[command]
                return response

            await asyncio.sleep(0.1)

        # 超时清理
        if command in self.recent_commands:
            del self.recent_commands[command]

        return f"命令 '{command}' 已发送（未捕获到响应）"

    async def _broadcast_log(self, line: str, is_error: bool = False) -> None:
        """向所有客户端广播日志"""
        if not self.clients:
            return

        message = {
            "type": "log",
            "content": line,
            "is_error": is_error,
            "timestamp": asyncio.get_event_loop().time()
        }

        message_data = json.dumps(message) + '\n'

        # 移除已断开的客户端
        active_clients = []
        for client in self.clients:
            try:
                client.write(message_data.encode())
                await client.drain()
                active_clients.append(client)
            except Exception:
                try:
                    client.close()
                    await client.wait_closed()
                except Exception:
                    pass

        self.clients = active_clients

    def _signal_handler(self, signum: int, frame) -> None:
        """信号处理器"""
        logger.info(f"收到信号 {signum}，准备关闭...")
        asyncio.create_task(self._shutdown())

    async def _shutdown(self) -> None:
        """关闭守护进程和服务器"""
        logger.info("关闭控制台守护进程...")

        # 停止服务器
        if self.server_process and self.server_process.stdin:
            try:
                self.server_process.stdin.write(b"stop\n")
                await self.server_process.stdin.drain()
                # 等待服务器正常关闭
                await asyncio.wait_for(self.server_process.wait(), timeout=30.0)
            except asyncio.TimeoutError:
                logger.warning("服务器未在30秒内关闭，强制终止")
                self.server_process.terminate()
                await self.server_process.wait()
            except Exception as e:
                logger.error(f"关闭服务器时出错: {e}")

        # 关闭监控任务
        if self.stdout_monitor_task:
            self.stdout_monitor_task.cancel()
        if self.stderr_monitor_task:
            self.stderr_monitor_task.cancel()

        # 关闭所有客户端
        for client in self.clients:
            try:
                client.close()
                await client.wait_closed()
            except Exception:
                pass

        # 关闭socket
        if self.server_socket:
            self.server_socket.close()

        # 清理socket文件
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)

        logger.info("守护进程已关闭")

    async def _execute_component_command(self, command: str) -> dict:
        """执行组件指令"""
        if not command:
            return {
                "success": False,
                "error": "请指定组件命令",
                "output": "可用命令: help, list, scan, load <组件名>, enable <组件名>, disable <组件名>, reload <组件名>, info <组件名>"
            }

        try:
            if not self.component_manager:
                return {
                    "success": False,
                    "error": "组件管理器不可用",
                    "output": ""
                }

            # 解析命令
            parts = command.split()
            cmd = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []

            if cmd == "help":
                return await self._component_help()
            elif cmd == "list":
                return await self._component_list()
            elif cmd == "scan":
                return await self._component_scan()
            elif cmd == "load" and args:
                return await self._component_load(args[0])
            elif cmd == "enable" and args:
                return await self._component_enable(args[0])
            elif cmd == "disable" and args:
                return await self._component_disable(args[0])
            elif cmd == "reload" and args:
                return await self._component_reload(args[0])
            elif cmd == "info" and args:
                return await self._component_info(args[0])
            elif cmd == "status":
                return await self._component_status()
            else:
                return {
                    "success": False,
                    "error": f"未知的组件命令: {cmd}",
                    "output": "使用 '$help' 查看可用命令"
                }

        except Exception as e:
            logger.error(f"执行组件命令失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    async def _component_help(self) -> dict:
        """显示组件命令帮助"""
        help_text = """组件管理命令帮助:

可用命令:
  $help               显示此帮助信息
  $list               列出所有已加载的组件
  $scan               扫描并发现可用组件
  $load <组件名>       加载指定组件
  $enable <组件名>     启用指定组件
  $disable <组件名>    禁用指定组件
  $reload <组件名>     重载指定组件
  $info <组件名>       显示组件详细信息
  $status             显示组件系统状态

示例:
  $scan
  $load TestComponent
  $enable TestComponent
  $info TestComponent
  $disable TestComponent"""

        return {
            "success": True,
            "error": None,
            "output": help_text
        }

    async def _component_list(self) -> dict:
        """列出所有组件"""
        try:
            loaded_components = self.component_manager.list_loaded_components()
            enabled_components = self.component_manager.list_enabled_components()

            if not loaded_components:
                return {
                    "success": True,
                    "error": None,
                    "output": "未找到任何已加载的组件"
                }

            output_lines = ["已加载的组件:"]
            for component_name in loaded_components:
                status = "[启用]" if component_name in enabled_components else "[禁用]"
                output_lines.append(f"  {status} {component_name}")

            return {
                "success": True,
                "error": None,
                "output": "\n".join(output_lines)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    async def _component_scan(self) -> dict:
        """扫描组件"""
        try:
            discovered = await self.component_manager.scan_components()

            if not discovered:
                return {
                    "success": True,
                    "error": None,
                    "output": "未发现任何组件"
                }

            output = f"发现 {len(discovered)} 个组件:\n"
            for component_name in discovered:
                output += f"  - {component_name}\n"

            return {
                "success": True,
                "error": None,
                "output": output.strip()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    async def _component_load(self, component_name: str) -> dict:
        """加载组件"""
        try:
            result = await self.component_manager.load_component(component_name)

            if result:
                return {
                    "success": True,
                    "error": None,
                    "output": f"组件 {component_name} 加载成功"
                }
            else:
                return {
                    "success": False,
                    "error": "加载失败",
                    "output": f"组件 {component_name} 加载失败，请检查组件是否存在或有依赖问题"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    async def _component_enable(self, component_name: str) -> dict:
        """启用组件"""
        try:
            # 先检查是否已加载
            if not self.component_manager.is_loaded(component_name):
                # 尝试先加载
                load_result = await self.component_manager.load_component(component_name)
                if not load_result:
                    return {
                        "success": False,
                        "error": "组件未加载且加载失败",
                        "output": f"无法加载组件 {component_name}"
                    }

            result = await self.component_manager.enable_component(component_name)

            if result:
                return {
                    "success": True,
                    "error": None,
                    "output": f"组件 {component_name} 启用成功"
                }
            else:
                return {
                    "success": False,
                    "error": "启用失败",
                    "output": f"组件 {component_name} 启用失败"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    async def _component_disable(self, component_name: str) -> dict:
        """禁用组件"""
        try:
            result = await self.component_manager.disable_component(component_name)

            if result:
                return {
                    "success": True,
                    "error": None,
                    "output": f"组件 {component_name} 禁用成功"
                }
            else:
                return {
                    "success": False,
                    "error": "禁用失败",
                    "output": f"组件 {component_name} 禁用失败"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    async def _component_reload(self, component_name: str) -> dict:
        """重载组件"""
        try:
            result = await self.component_manager.reload_component(component_name)

            if result:
                return {
                    "success": True,
                    "error": None,
                    "output": f"组件 {component_name} 重载成功"
                }
            else:
                return {
                    "success": False,
                    "error": "重载失败",
                    "output": f"组件 {component_name} 重载失败"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    async def _component_info(self, component_name: str) -> dict:
        """显示组件信息"""
        try:
            component_info = self.component_manager.get_component_info(component_name)

            if not component_info:
                return {
                    "success": False,
                    "error": "组件未找到",
                    "output": f"组件 {component_name} 未找到或未加载"
                }

            info_dict = component_info.to_dict()
            output_lines = [f"组件信息: {component_name}"]
            for key, value in info_dict.items():
                output_lines.append(f"  {key}: {value}")

            # 添加状态信息
            is_loaded = self.component_manager.is_loaded(component_name)
            is_enabled = self.component_manager.is_enabled(component_name)
            output_lines.append(f"  状态: {'已加载' if is_loaded else '未加载'}, {'已启用' if is_enabled else '未启用'}")

            return {
                "success": True,
                "error": None,
                "output": "\n".join(output_lines)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    async def _component_status(self) -> dict:
        """显示组件系统状态"""
        try:
            status = self.component_manager.get_component_status()

            output_lines = ["组件系统状态:"]
            output_lines.append(f"  已加载组件: {status['total_loaded']}")
            output_lines.append(f"  已启用组件: {status['total_enabled']}")
            output_lines.append(f"  Web组件: {status['total_web_components']}")
            output_lines.append(f"  失败组件: {status['total_failed']}")

            if status['failed_components']:
                output_lines.append("  失败详情:")
                for name, error in status['failed_components'].items():
                    output_lines.append(f"    {name}: {error}")

            return {
                "success": True,
                "error": None,
                "output": "\n".join(output_lines)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    async def _execute_aetherius_command(self, command: str) -> dict:
        """执行Aetherius系统指令"""
        if not command:
            return {
                "success": False,
                "error": "请指定Aetherius命令",
                "output": "可用命令: help, status, server, info, config, plugins, uptime, quit"
            }

        try:
            # 增加命令计数
            self.command_count += 1

            # 解析命令
            parts = command.split()
            cmd = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []

            if cmd == "help":
                return await self._aetherius_help()
            elif cmd == "status":
                return await self._aetherius_status()
            elif cmd == "server":
                return await self._aetherius_server_info()
            elif cmd == "info":
                return await self._aetherius_system_info()
            elif cmd == "config":
                return await self._aetherius_config_info()
            elif cmd == "plugins":
                return await self._aetherius_plugins_info()
            elif cmd == "uptime":
                return await self._aetherius_uptime()
            elif cmd == "version":
                return await self._aetherius_version()
            elif cmd == "performance" or cmd == "perf":
                return await self._aetherius_performance()
            elif cmd == "quit" or cmd == "exit":
                return await self._aetherius_shutdown()
            elif cmd == "restart":
                return await self._aetherius_restart()
            else:
                return {
                    "success": False,
                    "error": f"未知的Aetherius命令: {cmd}",
                    "output": "使用 '!help' 查看可用命令"
                }

        except Exception as e:
            logger.error(f"执行Aetherius命令失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    async def _aetherius_help(self) -> dict:
        """显示Aetherius命令帮助"""
        help_text = """Aetherius系统命令帮助:

可用命令:
  !help               显示此帮助信息
  !status             显示系统状态
  !server             显示服务器详细信息
  !info               显示系统详细信息
  !config             显示配置信息
  !plugins            显示插件状态
  !uptime             显示运行时间
  !version            显示版本信息
  !performance        显示性能监控信息
  !restart            重启持久化控制台
  !quit               关闭持久化控制台

示例:
  !status
  !server
  !info
  !plugins
  !uptime"""

        return {
            "success": True,
            "error": None,
            "output": help_text
        }

    async def _aetherius_status(self) -> dict:
        """显示系统状态"""
        try:
            current_time = asyncio.get_event_loop().time()
            uptime_seconds = current_time - self.start_time

            # 计算友好的时间显示
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            seconds = int(uptime_seconds % 60)

            uptime_str = f"{hours}h {minutes}m {seconds}s"

            server_status = "运行中" if (self.server_process and self.server_process.returncode is None) else "未运行"
            client_count = len(self.clients)

            status_lines = [
                "Aetherius持久化控制台状态:",
                f"  运行时间: {uptime_str}",
                f"  执行命令数: {self.command_count}",
                f"  连接客户端: {client_count}",
                f"  服务器状态: {server_status}",
                f"  组件管理器: {'可用' if self.component_manager else '不可用'}",
                f"  插件管理器: {'可用' if self.plugin_manager else '不可用'}",
            ]

            if self.server_process:
                status_lines.append(f"  服务器PID: {self.server_process.pid}")

            return {
                "success": True,
                "error": None,
                "output": "\n".join(status_lines)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    async def _aetherius_server_info(self) -> dict:
        """显示服务器详细信息"""
        try:
            output_lines = ["服务器详细信息:"]

            if not self.server_process:
                output_lines.append("  状态: 未启动")
                output_lines.append(f"  JAR路径: {self.server_jar_path}")
                output_lines.append(f"  工作目录: {self.server_dir}")
            else:
                output_lines.append(f"  状态: {'运行中' if self.server_process.returncode is None else '已停止'}")
                output_lines.append(f"  PID: {self.server_process.pid}")
                output_lines.append(f"  JAR路径: {self.server_jar_path}")
                output_lines.append(f"  工作目录: {self.server_dir}")

                if self.server_process.returncode is not None:
                    output_lines.append(f"  退出码: {self.server_process.returncode}")

            # 监控任务状态
            output_lines.append(f"  stdout监控: {'活跃' if self.stdout_monitor_task and not self.stdout_monitor_task.done() else '非活跃'}")
            output_lines.append(f"  stderr监控: {'活跃' if self.stderr_monitor_task and not self.stderr_monitor_task.done() else '非活跃'}")

            return {
                "success": True,
                "error": None,
                "output": "\n".join(output_lines)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    async def _aetherius_system_info(self) -> dict:
        """显示系统详细信息"""
        try:
            import os
            import platform
            from pathlib import Path

            import psutil

            output_lines = ["Aetherius系统信息:"]

            # 基本系统信息
            output_lines.append(f"  平台: {platform.system()} {platform.release()}")
            output_lines.append(f"  Python版本: {platform.python_version()}")
            output_lines.append(f"  进程PID: {os.getpid()}")

            # 内存信息
            process = psutil.Process()
            memory_info = process.memory_info()
            output_lines.append(f"  内存使用: {memory_info.rss / 1024 / 1024:.1f} MB")

            # 文件描述符
            try:
                num_fds = process.num_fds()
                output_lines.append(f"  打开文件描述符: {num_fds}")
            except:
                pass  # Windows doesn't have num_fds

            # 工作目录
            output_lines.append(f"  工作目录: {Path.cwd()}")
            output_lines.append(f"  Socket路径: {self.socket_path}")

            # 系统组件状态
            output_lines.append("  系统组件:")
            output_lines.append(f"    组件管理器: {'✓' if self.component_manager else '✗'}")
            output_lines.append(f"    插件管理器: {'✓' if self.plugin_manager else '✗'}")

            return {
                "success": True,
                "error": None,
                "output": "\n".join(output_lines)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    async def _aetherius_config_info(self) -> dict:
        """显示配置信息"""
        try:
            output_lines = ["配置信息:"]
            output_lines.append(f"  服务器JAR: {self.server_jar_path}")
            output_lines.append(f"  服务器目录: {self.server_dir}")
            output_lines.append(f"  Socket路径: {self.socket_path}")

            # 尝试获取配置管理器信息
            try:
                from ..core.config import get_config_manager
                config_manager = get_config_manager()
                if config_manager:
                    output_lines.append("  配置管理器: 可用")
                else:
                    output_lines.append("  配置管理器: 不可用")
            except:
                output_lines.append("  配置管理器: 未初始化")

            return {
                "success": True,
                "error": None,
                "output": "\n".join(output_lines)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    async def _aetherius_plugins_info(self) -> dict:
        """显示插件信息"""
        try:
            output_lines = ["插件系统信息:"]

            if not self.plugin_manager:
                output_lines.append("  插件管理器: 不可用")
                return {
                    "success": True,
                    "error": None,
                    "output": "\n".join(output_lines)
                }

            output_lines.append("  插件管理器: 可用")

            # 尝试获取插件信息
            try:
                if hasattr(self.plugin_manager, "list_plugins"):
                    plugins = self.plugin_manager.list_plugins()
                    output_lines.append(f"  已加载插件: {len(plugins)}")

                    if plugins:
                        output_lines.append("  插件列表:")
                        for plugin_name in plugins:
                            is_enabled = (
                                self.plugin_manager.is_enabled(plugin_name)
                                if hasattr(self.plugin_manager, "is_enabled")
                                else False
                            )
                            status = "启用" if is_enabled else "禁用"
                            output_lines.append(f"    - {plugin_name} ({status})")
                else:
                    output_lines.append("  插件信息: 无法获取")

            except Exception as e:
                output_lines.append(f"  插件信息获取失败: {e}")

            return {
                "success": True,
                "error": None,
                "output": "\n".join(output_lines)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    async def _aetherius_uptime(self) -> dict:
        """显示运行时间"""
        try:
            current_time = asyncio.get_event_loop().time()
            uptime_seconds = current_time - self.start_time

            # 详细时间分解
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            seconds = int(uptime_seconds % 60)

            output_lines = ["运行时间信息:"]

            if days > 0:
                output_lines.append(f"  运行时间: {days}天 {hours}小时 {minutes}分钟 {seconds}秒")
            elif hours > 0:
                output_lines.append(f"  运行时间: {hours}小时 {minutes}分钟 {seconds}秒")
            elif minutes > 0:
                output_lines.append(f"  运行时间: {minutes}分钟 {seconds}秒")
            else:
                output_lines.append(f"  运行时间: {seconds}秒")

            output_lines.append(f"  启动时间: {self.start_time:.0f}")
            output_lines.append(f"  当前时间: {current_time:.0f}")
            output_lines.append(f"  总执行命令: {self.command_count}")

            return {
                "success": True,
                "error": None,
                "output": "\n".join(output_lines)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    async def _aetherius_version(self) -> dict:
        """显示版本信息"""
        try:
            import platform
            import sys

            output_lines = ["版本信息:"]
            output_lines.append("  Aetherius Core: 持久化控制台模式")
            output_lines.append(f"  Python: {sys.version}")
            output_lines.append(f"  平台: {platform.platform()}")

            # 尝试获取更多版本信息
            try:
                output_lines.append("  AsyncIO: 已支持")
            except:
                pass

            return {
                "success": True,
                "error": None,
                "output": "\n".join(output_lines)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    async def _aetherius_performance(self) -> dict:
        """显示性能监控信息"""
        try:
            import psutil

            output_lines = ["性能监控信息:"]

            # 进程信息
            process = psutil.Process()

            # CPU使用率
            cpu_percent = process.cpu_percent()
            output_lines.append(f"  CPU使用率: {cpu_percent:.1f}%")

            # 内存信息
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            output_lines.append(f"  内存使用: {memory_mb:.1f} MB")

            # 线程数
            num_threads = process.num_threads()
            output_lines.append(f"  线程数: {num_threads}")

            # 文件描述符（Unix/Linux）
            try:
                num_fds = process.num_fds()
                output_lines.append(f"  文件描述符: {num_fds}")
            except AttributeError:
                # Windows doesn't have num_fds
                pass

            # 系统整体信息
            cpu_count = psutil.cpu_count()
            output_lines.append(f"  系统CPU核心: {cpu_count}")

            memory = psutil.virtual_memory()
            total_memory_gb = memory.total / 1024 / 1024 / 1024
            output_lines.append(f"  系统总内存: {total_memory_gb:.1f} GB")

            return {
                "success": True,
                "error": None,
                "output": "\n".join(output_lines)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    async def _aetherius_shutdown(self) -> dict:
        """关闭持久化控制台"""
        try:
            logger.info("接收到关闭命令，准备关闭...")

            # 安排关闭任务
            asyncio.create_task(self._shutdown())

            return {
                "success": True,
                "error": None,
                "output": "持久化控制台正在关闭..."
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    async def _aetherius_restart(self) -> dict:
        """重启持久化控制台"""
        try:
            return {
                "success": False,
                "error": "重启功能暂未实现",
                "output": "请手动重启持久化控制台"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }


async def start_persistent_console(server_jar_path: str, server_dir: str) -> None:
    """启动持久化控制台守护进程"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建并启动守护进程
    daemon = PersistentConsoleDaemon(server_jar_path, server_dir)

    try:
        await daemon.start()
    except KeyboardInterrupt:
        logger.info("收到中断信号")
    except Exception as e:
        logger.error(f"守护进程异常: {e}")
    finally:
        await daemon._shutdown()


if __name__ == "__main__":
    # 服务器配置
    server_jar = "/workspaces/aetheriusmc.github.io/Aetherius-Core/server/server.jar"
    server_dir = "/workspaces/aetheriusmc.github.io/Aetherius-Core/server"

    asyncio.run(start_persistent_console(server_jar, server_dir))
