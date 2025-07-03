"""
Server process controller for managing Minecraft server instances with a robust state machine.
"""

import asyncio
import logging
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional

import psutil

from .config_models import ServerConfig
from .event_manager import fire_event, get_event_manager
from .events_base import (
    ServerCrashEvent,
    ServerLogEvent,
    ServerStartedEvent,
    ServerStateChangedEvent,
    ServerStoppedEvent,
)
from .server_state import get_server_state

logger = logging.getLogger(__name__)


class ServerState(Enum):
    """Represents the lifecycle state of the server."""

    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    CRASHED = auto()


class ServerController:
    """
    Manages a Minecraft server process using a robust asynchronous state machine.
    This class handles starting, stopping, I/O, and health monitoring.
    """

    def __init__(self, config: ServerConfig):
        self.config = config
        self.process: Optional[asyncio.subprocess.Process] = None
        self._state: ServerState = ServerState.STOPPED
        self._tasks: list[asyncio.Task] = []
        self._psutil_process: psutil.Process | None = None
        self.event_manager = get_event_manager()
        self.persistent_state = get_server_state()
        self._start_time: Optional[float] = None

    @property
    def state(self) -> ServerState:
        """Get the current state of the server."""
        return self._state

    def _change_state(self, new_state: ServerState):
        """Atomically change the server state and fire an event."""
        if self._state == new_state:
            return

        old_state = self._state
        self._state = new_state
        logger.info(f"Server state changed from {old_state.name} to {new_state.name}")
        asyncio.create_task(
            fire_event(
                ServerStateChangedEvent(old_state=old_state, new_state=new_state)
            )
        )

    async def start(self) -> bool:
        """Start the Minecraft server process."""
        if self.state not in [ServerState.STOPPED, ServerState.CRASHED]:
            logger.warning(f"Cannot start server from state {self.state.name}")
            return False

        self._change_state(ServerState.STARTING)

        jar_path = Path(self.config.jar_path)
        if not jar_path.exists():
            logger.error(f"Server JAR not found: {jar_path}")
            self._change_state(ServerState.STOPPED)
            return False

        cmd = [
            "java",
            *self.config.jvm_args,
            "-jar",
            str(jar_path.resolve()),
            "--nogui",
        ]
        work_dir = jar_path.parent

        try:
            import time
            self._start_time = time.time()
            
            import os
            
            # 在新的进程组中启动服务器，防止控制台关闭时影响服务器
            def preexec_fn():
                # 创建新的进程组，使服务器独立于控制台进程
                os.setpgrp()
            
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir,
                preexec_fn=preexec_fn,
            )
            
            # 创建命名管道用于跨进程命令发送
            import os
            import stat
            self.command_pipe_path = f"/tmp/aetherius_server_{self.process.pid}.pipe"
            
            try:
                if os.path.exists(self.command_pipe_path):
                    os.unlink(self.command_pipe_path)
                os.mkfifo(self.command_pipe_path)
                
                # 启动命名管道监听器
                self._tasks.append(asyncio.create_task(self._listen_command_pipe()))
                
            except Exception as e:
                logger.warning(f"无法创建命名管道: {e}")
            self._psutil_process = psutil.Process(self.process.pid)
            logger.info(f"Server process started with PID: {self.process.pid}")

            # Record server start in persistent state
            self.persistent_state.set_server_started(
                pid=self.process.pid,
                jar_path=str(jar_path.resolve()),
                working_directory=str(work_dir.resolve())
            )

            self._tasks.append(asyncio.create_task(self._read_stdout()))
            self._tasks.append(asyncio.create_task(self._read_stderr()))
            self._tasks.append(asyncio.create_task(self._monitor_process()))
            self._tasks.append(asyncio.create_task(self._process_command_queue()))

            # Transition to RUNNING state is handled by log parser or a timeout
            # For now, we'll transition after a short delay for simplicity
            await asyncio.sleep(1)  # Represents time waiting for "Done" log message
            self._change_state(ServerState.RUNNING)
            
            startup_time = time.time() - self._start_time
            await fire_event(ServerStartedEvent(pid=self.process.pid, startup_time=startup_time))
            return True

        except (Exception, psutil.Error) as e:
            logger.error(f"Failed to start server process: {e}")
            self._change_state(ServerState.CRASHED)
            return False

    async def restart(self) -> bool:
        """Restart the Minecraft server process."""
        if self.state == ServerState.RUNNING:
            stop_success = await self.stop()
            if not stop_success:
                return False
        
        # Wait a moment before restarting
        await asyncio.sleep(2)
        
        return await self.start()

    async def stop(self, timeout: float = 30.0) -> bool:
        """Stop the Minecraft server process gracefully."""
        if self.state not in [ServerState.RUNNING, ServerState.STARTING]:
            logger.warning(f"Cannot stop server from state {self.state.name}")
            return False

        self._change_state(ServerState.STOPPING)

        try:
            if self.process and self.process.stdin:
                self.process.stdin.write(b"stop\n")
                await self.process.stdin.drain()

            await asyncio.wait_for(self.process.wait(), timeout=timeout)
            logger.info("Server stopped gracefully.")

        except asyncio.TimeoutError:
            logger.warning(
                f"Server did not stop gracefully within {timeout}s. Killing."
            )
            self.process.kill()
            await self.process.wait()
        except Exception as e:
            logger.error(f"Error during graceful stop: {e}. Killing process.")
            self.process.kill()
            await self.process.wait()
        finally:
            await self._cleanup_tasks()
            exit_code = self.process.returncode if self.process else -1
            self._change_state(ServerState.STOPPED)
            # Clear persistent state when server stops
            self.persistent_state.set_server_stopped()
            
            # Calculate uptime
            import time
            uptime = time.time() - self._start_time if self._start_time else 0.0
            
            await fire_event(ServerStoppedEvent(exit_code=exit_code, uptime=uptime))
            self.process = None
            self._psutil_process = None
            self._start_time = None
        return True

    async def send_command(self, command: str) -> bool:
        """Send a command to the server's stdin."""
        if (
            self.state != ServerState.RUNNING
            or not self.process
            or not self.process.stdin
        ):
            logger.error(f"Cannot send command in state {self.state.name}")
            return False

        try:
            command_bytes = f"{command.strip()}\n".encode()
            self.process.stdin.write(command_bytes)
            await self.process.stdin.drain()
            logger.debug(f"Sent command: {command}")
            return True
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            logger.error(f"Failed to send command '{command}': {e}")
            await self._handle_crash()
            return False

    async def execute_command_with_result(self, command: str, timeout: float = 30.0) -> dict:
        """
        Execute a command and capture its output from server logs.
        
        Args:
            command: The command to execute
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with success, output, error, and execution_time
        """
        import time
        
        start_time = time.time()
        
        # 跨进程模式：通过PID管理和日志监控
        if not (self.state == ServerState.RUNNING and self.process and self.process.stdin):
            # 尝试跨进程发送命令
            return await self._execute_cross_process_command(command, timeout, start_time)
        
        try:
            # 主要方式：直接IO管道 + 日志监控
            return await self._execute_with_log_monitoring(command, timeout, start_time)
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error executing command '{command}': {e}")
            
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "execution_time": execution_time,
            }

    async def _execute_with_log_monitoring(self, command: str, timeout: float, start_time: float) -> dict:
        """通过IO管道发送命令并监控日志获取输出"""
        import asyncio
        
        # 设置日志监控
        command_output = []
        command_sent_time = None
        
        def log_handler(event):
            nonlocal command_output, command_sent_time
            if command_sent_time and hasattr(event, 'message'):
                # 捕获命令执行后的日志输出
                if time.time() - command_sent_time < 5.0:  # 5秒内的日志
                    command_output.append(event.message)
        
        # 注册临时日志监听器
        self.event_manager.register_listener("ServerLogEvent", log_handler)
        
        try:
            # 发送命令
            command_sent_time = time.time()
            success = await self.send_command(command)
            
            if not success:
                return {
                    "success": False,
                    "error": "Failed to send command to server",
                    "output": "",
                    "execution_time": time.time() - start_time,
                }
            
            # 等待日志输出
            await asyncio.sleep(2.0)  # 等待2秒收集日志
            
            # 处理收集到的日志
            output = self._parse_command_output(command, command_output)
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "error": None,
                "output": output if output else f"命令 '{command}' 已发送至服务器",
                "execution_time": execution_time,
            }
            
        finally:
            # 清理日志监听器
            try:
                self.event_manager.unregister_listener("ServerLogEvent", log_handler)
            except:
                pass

    async def _execute_cross_process_command(self, command: str, timeout: float, start_time: float) -> dict:
        """跨进程命令执行"""
        try:
            from .command_queue import get_command_queue
            
            command_queue = get_command_queue()
            command_id = command_queue.add_command(command)
            result = await command_queue.wait_for_completion(command_id, timeout)
            
            execution_time = time.time() - start_time
            
            return {
                "success": result.get("status") == "completed",
                "error": result.get("error"),
                "output": result.get("output", ""),
                "execution_time": execution_time,
            }
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": f"跨进程命令执行失败: {e}",
                "output": "",
                "execution_time": execution_time,
            }

    def _parse_command_output(self, command: str, log_lines: list) -> str:
        """解析命令输出日志"""
        if not log_lines:
            return ""
        
        # 根据命令类型解析相应的输出
        if command == "list":
            # 查找玩家列表输出
            for line in log_lines:
                if "players online:" in line.lower():
                    return line.strip()
        elif command.startswith("time query"):
            # 查找时间查询输出
            for line in log_lines:
                if "time is" in line.lower() or "daytime" in line.lower():
                    return line.strip()
        elif command == "difficulty":
            # 查找难度输出
            for line in log_lines:
                if "difficulty" in line.lower():
                    return line.strip()
        elif command.startswith("weather"):
            # 查找天气输出
            for line in log_lines:
                if "weather" in line.lower() or "clear" in line.lower() or "rain" in line.lower():
                    return line.strip()
        
        # 返回最后几行相关的日志
        relevant_lines = [line for line in log_lines if line.strip()]
        return "\n".join(relevant_lines[-3:]) if relevant_lines else ""

    async def _read_stdout(self):
        """Continuously read and process stdout from the server."""
        while self.process and self.process.stdout and not self.process.stdout.at_eof():
            try:
                line_bytes = await self.process.stdout.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode("utf-8", errors="replace").strip()
                if line:
                    await fire_event(ServerLogEvent(level="INFO", message=line, line=line))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error reading stdout: {e}")
                break

    async def _read_stderr(self):
        """Continuously read and process stderr from the server."""
        while self.process and self.process.stderr and not self.process.stderr.at_eof():
            try:
                line_bytes = await self.process.stderr.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode("utf-8", errors="replace").strip()
                if line:
                    await fire_event(ServerLogEvent(level="ERROR", message=line, line=line))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error reading stderr: {e}")
                break

    async def _monitor_process(self):
        """Wait for the process to exit and handle the result."""
        if not self.process:
            return
        exit_code = await self.process.wait()
        logger.info(f"Server process exited with code: {exit_code}")

        if self.state not in [ServerState.STOPPING, ServerState.STOPPED]:
            await self._handle_crash(exit_code)

    async def _handle_crash(self, exit_code: int = -1):
        """Handle an unexpected server crash."""
        self._change_state(ServerState.CRASHED)
        await self._cleanup_tasks()
        await fire_event(ServerCrashEvent(
            exit_code=exit_code, 
            error_output="Server process terminated unexpectedly", 
            will_restart=False
        ))

        # Optional: Implement auto-restart logic here
        # if self.config.auto_restart:
        #     logger.info(f"Auto-restarting in {self.config.restart_delay} seconds...")
        #     await asyncio.sleep(self.config.restart_delay)
        #     await self.start()

    async def _cleanup_tasks(self):
        """Cancel and clean up all background tasks."""
        # Get current task to avoid cancelling ourselves
        current_task = asyncio.current_task()
        
        # Cancel all other tasks except the current one
        tasks_to_cancel = []
        for task in self._tasks:
            if not task.done() and task != current_task:
                task.cancel()
                tasks_to_cancel.append(task)
        
        # Wait for tasks to complete/cancel
        if tasks_to_cancel:
            await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
        
        self._tasks.clear()

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics using psutil."""
        if not self._psutil_process or not self._psutil_process.is_running():
            return {}
        try:
            with self._psutil_process.oneshot():
                return {
                    "cpu_percent": self._psutil_process.cpu_percent(),
                    "memory_mb": self._psutil_process.memory_info().rss / (1024 * 1024),
                    "threads": self._psutil_process.num_threads(),
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {}

    async def _process_command_queue(self):
        """处理命令队列中的命令"""
        try:
            from .command_queue import get_command_queue
            
            command_queue = get_command_queue()
            
            while self.state == ServerState.RUNNING:
                try:
                    # 检查待处理的命令
                    pending_commands = command_queue.get_pending_commands()
                    
                    for command_data in pending_commands:
                        command_id = command_data["id"]
                        command = command_data["command"]
                        
                        logger.info(f"处理队列命令: {command} (ID: {command_id})")
                        
                        try:
                            # 通过IO管道发送命令
                            success = await self.send_command(command)
                            
                            if success:
                                # 等待一段时间收集日志输出
                                await asyncio.sleep(1.0)
                                
                                # 标记命令完成（简化版本，实际的输出会通过日志事件处理）
                                command_queue.mark_command_completed(
                                    command_id,
                                    success=True,
                                    output=f"命令 '{command}' 已通过IO管道执行"
                                )
                            else:
                                command_queue.mark_command_completed(
                                    command_id,
                                    success=False,
                                    error="命令发送失败"
                                )
                                
                        except Exception as e:
                            logger.error(f"执行队列命令 {command} 失败: {e}")
                            command_queue.mark_command_completed(
                                command_id,
                                success=False,
                                error=str(e)
                            )
                    
                    # 清理旧文件
                    command_queue.cleanup_old_files(max_age_seconds=300)
                    
                    # 短暂等待后继续检查队列
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"命令队列处理错误: {e}")
                    await asyncio.sleep(1.0)
                    
        except ImportError:
            logger.warning("命令队列模块不可用，跳过队列处理")
        except asyncio.CancelledError:
            logger.info("命令队列处理任务已取消")
        except Exception as e:
            logger.error(f"命令队列处理器启动失败: {e}")

    async def _listen_command_pipe(self):
        """监听命名管道中的命令"""
        try:
            while self.state == ServerState.RUNNING:
                try:
                    # 以非阻塞方式打开命名管道
                    import os
                    import select
                    
                    # 等待管道有数据可读
                    if os.path.exists(self.command_pipe_path):
                        pipe_fd = os.open(self.command_pipe_path, os.O_RDONLY | os.O_NONBLOCK)
                        
                        try:
                            # 使用select等待数据
                            ready, _, _ = select.select([pipe_fd], [], [], 1.0)
                            
                            if ready:
                                data = os.read(pipe_fd, 1024)
                                if data:
                                    command = data.decode('utf-8').strip()
                                    if command:
                                        logger.info(f"从命名管道接收到命令: {command}")
                                        # 发送命令到服务器stdin
                                        await self.send_command(command)
                        finally:
                            os.close(pipe_fd)
                    
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"命名管道监听错误: {e}")
                    await asyncio.sleep(1.0)
                    
        except asyncio.CancelledError:
            logger.info("命名管道监听器已取消")
        except Exception as e:
            logger.error(f"命名管道监听器错误: {e}")
        finally:
            # 清理命名管道
            try:
                if hasattr(self, 'command_pipe_path') and os.path.exists(self.command_pipe_path):
                    os.unlink(self.command_pipe_path)
            except Exception:
                pass
