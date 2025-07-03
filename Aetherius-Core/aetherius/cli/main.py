"""Main CLI application for Aetherius."""

import asyncio
import logging
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Optional

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.text import Text

from ..components import ComponentManager
from ..core import (
    LogLineEvent,
    PlayerChatEvent,
    PlayerDeathEvent,
    PlayerJoinEvent,
    PlayerLeaveEvent,
    ServerCrashEvent,
    ServerStartedEvent,
    ServerStoppedEvent,
    get_event_manager,
    on_event,
)
from ..core.config import get_config_manager
from ..core.server import ServerController, ServerState
from ..plugins import PluginManager

app = typer.Typer(
    name="aetherius",
    help="Aetherius - A lightweight, high-performance Minecraft server management engine",
    no_args_is_help=True,
)
server_app = typer.Typer(help="Server management commands")
events_app = typer.Typer(help="Event system management commands")
plugin_app = typer.Typer(help="Plugin management commands")
component_app = typer.Typer(help="Component management commands")
app.add_typer(server_app, name="server")
app.add_typer(events_app, name="events")
app.add_typer(plugin_app, name="plugin")
app.add_typer(component_app, name="component")

console = Console()

# Global state
_config: Optional[Any] = None
_server_wrapper: Optional[ServerController] = None
_plugin_manager: Optional[PluginManager] = None
_component_manager: Optional[ComponentManager] = None


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


def get_config() -> Any:
    """Get or load configuration."""
    global _config
    if _config is None:
        _config = get_config_manager()
        # Use the new ConfigManager API
        try:
            log_level = _config.get('logging.level', 'INFO')
        except:
            log_level = 'INFO'
        setup_logging(log_level)
    return _config


def get_server_wrapper() -> ServerController:
    """Get or create server wrapper."""
    global _server_wrapper
    if _server_wrapper is None:
        config = get_config()
        # Create a simple server config for now
        from ..core.config_models import ServerConfig
        server_config = ServerConfig()
        _server_wrapper = ServerController(server_config)

        # Set the global server wrapper for plugins
        # from ..core import set_server_wrapper
        # set_server_wrapper(_server_wrapper)

        # Set up enhanced event-based log handlers
        setup_event_handlers()

    return _server_wrapper


def get_plugin_manager() -> PluginManager:
    """Get or create plugin manager."""
    global _plugin_manager
    if _plugin_manager is None:
        config = get_config()
        # PluginManager expects a core_api parameter, but we don't have it in CLI context
        # For now, pass None and handle it properly later
        _plugin_manager = PluginManager(None)

        # Set the global plugin manager
        # from ..core import set_plugin_manager
        # set_plugin_manager(_plugin_manager)

    return _plugin_manager


def get_component_manager():
    """Get or create component manager - 使用与控制台相同的组件管理器."""
    global _component_manager
    if _component_manager is None:
        try:
            # 尝试使用控制台相同的组件管理器初始化逻辑
            from ..core.component_manager import (
                get_component_manager as get_core_component_manager,
            )

            _component_manager = get_core_component_manager()
            if _component_manager is None:
                # 创建一个简单的核心实例，与控制台逻辑保持一致
                from types import SimpleNamespace

                from ..core.component_manager import (
                    ComponentManager as CoreComponentManager,
                )

                try:
                    from ..core import get_config_manager, get_event_manager
                    event_manager = get_event_manager()
                    config_manager = get_config_manager()
                except:
                    event_manager = None
                    config_manager = None

                mock_core = SimpleNamespace(
                    event_manager=event_manager,
                    config_manager=config_manager,
                    logger=logging.getLogger("aetherius.core"),
                )
                _component_manager = CoreComponentManager(mock_core)
        except Exception:
            # 如果无法使用核心组件管理器，回退到原有的
            from ..components.loader import ComponentManager
            _component_manager = ComponentManager(None)

    return _component_manager


def _find_component_start_script(component_name: str) -> Optional[Path]:
    """查找组件的标准启动脚本（与控制台逻辑相同）"""

    # 可能的组件路径
    component_paths = [
        # 如果当前就在组件目录内
        Path("start_component.py"),  # 当前目录就是组件目录
        Path(f"../Component{component_name}/start_component.py"),  # 从其他组件目录切换
        # 相对于当前工作目录
        Path(f"components/{component_name}/start_component.py"),
        Path(f"components/Component{component_name}/start_component.py"),
        # 相对于Aetherius根目录
        Path("../components") / component_name / "start_component.py",
        Path("../components") / f"Component{component_name}" / "start_component.py",
        # 从更深层目录向上查找
        Path("../../components") / component_name / "start_component.py",
        Path("../../components") / f"Component{component_name}" / "start_component.py",
        # 绝对路径
        Path("/workspaces/aetheriusmc.github.io/Aetherius-Core/components") / component_name / "start_component.py",
        Path("/workspaces/aetheriusmc.github.io/Aetherius-Core/components") / f"Component{component_name}" / "start_component.py",
        # 当前目录的components路径
        Path.cwd() / "components" / component_name / "start_component.py",
        Path.cwd() / "components" / f"Component{component_name}" / "start_component.py",
        # 尝试从父目录查找
        Path.cwd().parent / "components" / component_name / "start_component.py",
        Path.cwd().parent / "components" / f"Component{component_name}" / "start_component.py",
    ]

    for path in component_paths:
        if path.exists() and path.is_file():
            console.print(f"[green]✓ 找到组件启动脚本: {path}[/green]")
            return path

    console.print(f"[yellow]⚠ 未找到组件 {component_name} 的标准启动脚本 (start_component.py)[/yellow]")
    return None


def _start_component_with_script(component_name: str, script_path: Path):
    """使用标准启动脚本启动组件（与控制台逻辑相同）"""

    def run_component():
        try:
            console.print(f"[cyan]正在启动组件 {component_name}...[/cyan]")
            console.print("[magenta]╭─── 组件启动日志 ───╮[/magenta]")

            # 使用Popen以便实时获取输出 - 默认启动所有服务
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            # 实时读取并显示输出
            start_time = time.time()
            timeout = 60  # 60秒超时
            component_ready = False  # 组件完成标志

            while True:
                # 检查进程是否结束
                if process.poll() is not None:
                    break

                # 读取输出
                output = process.stdout.readline()
                if output:
                    output = output.strip()
                    if output:
                        console.print(f"[dim]│ {output}[/dim]")

                        # 检查是否包含完成标志
                        if any(keyword in output.lower() for keyword in
                               ["started", "ready", "running", "启动完成", "服务就绪", "* Running on"]):
                            component_ready = True

                # 检查超时
                if time.time() - start_time > timeout:
                    console.print("[yellow]⚠ 组件启动超时，但将在后台继续运行[/yellow]")
                    break

                # 如果组件就绪，等待一会儿再结束
                if component_ready:
                    time.sleep(2)  # 等待2秒确保输出完整
                    break

                time.sleep(0.1)  # 短暂休眠避免占用过多CPU

            console.print("[magenta]╰─── 组件启动完成 ───╯[/magenta]")

            # 检查进程最终状态
            if process.poll() is None:
                console.print(f"[green]✓ 组件 {component_name} 已在后台启动[/green]")
            else:
                return_code = process.poll()
                if return_code == 0:
                    console.print(f"[green]✓ 组件 {component_name} 启动成功[/green]")
                else:
                    console.print(f"[red]✗ 组件 {component_name} 启动失败 (退出码: {return_code})[/red]")

        except Exception as e:
            console.print(f"[red]✗ 启动组件失败: {e}[/red]")

    # 在独立线程中运行，避免阻塞主线程
    thread = threading.Thread(target=run_component, daemon=True)
    thread.start()
    thread.join()  # 等待完成


def _enable_component_fallback(component_name: str):
    """使用组件管理器启用组件的回退方法"""
    component_manager = get_component_manager()

    async def enable_component():
        # 检查组件管理器是否有所需方法
        if hasattr(component_manager, 'list_components'):
            # 自动加载组件（如果需要）
            if not component_manager.list_components():
                if hasattr(component_manager, 'load_all_components'):
                    await component_manager.load_all_components()

        # 启用组件
        if hasattr(component_manager, 'enable_component'):
            success = await component_manager.enable_component(component_name)
            if success:
                console.print(f"[green]✓[/green] 已启用组件: {component_name}")
            else:
                console.print(f"[red]✗[/red] 启用组件失败: {component_name}")
                raise typer.Exit(1)
        else:
            console.print("[yellow]组件管理器不支持启用功能[/yellow]")
            raise typer.Exit(1)

    asyncio.run(enable_component())


def setup_event_handlers() -> None:
    """Setup event handlers for enhanced CLI output."""

    @on_event(PlayerJoinEvent)
    async def handle_player_join(event: PlayerJoinEvent):
        ip_info = f" from {event.ip_address}" if event.ip_address else ""
        console.print(
            f"[green]✓[/green] [bold]{event.player_name}[/bold] joined the server{ip_info}"
        )

    @on_event(PlayerLeaveEvent)
    async def handle_player_leave(event: PlayerLeaveEvent):
        reason_info = f" ({event.leave_reason})" if event.leave_reason else ""
        console.print(
            f"[yellow]✗[/yellow] [bold]{event.player_name}[/bold] left the server{reason_info}"
        )

    @on_event(PlayerChatEvent)
    async def handle_player_chat(event: PlayerChatEvent):
        console.print(
            f"[blue]💬[/blue] [bold cyan]{event.player_name}[/bold cyan]: {event.message}"
        )

    @on_event(PlayerDeathEvent)
    async def handle_player_death(event: PlayerDeathEvent):
        death_msg = event.death_message or "died"
        killer_info = f" by {event.killer}" if event.killer else ""
        console.print(
            f"[red]💀[/red] [bold]{event.player_name}[/bold] {death_msg}{killer_info}"
        )

    @on_event(ServerStartedEvent)
    async def handle_server_started(event: ServerStartedEvent):
        startup_time = getattr(event, "startup_time", 0)
        if startup_time:
            console.print(
                f"[green]🚀 Server started successfully![/green] [dim](took {startup_time:.1f}s)[/dim]"
            )
        else:
            console.print("[green]🚀 Server started successfully![/green]")

    @on_event(ServerStoppedEvent)
    async def handle_server_stopped(event: ServerStoppedEvent):
        uptime_str = f"{event.uptime:.1f}s" if event.uptime else "unknown"
        console.print(
            f"[yellow]🛑 Server stopped[/yellow] [dim](uptime: {uptime_str})[/dim]"
        )

    @on_event(ServerCrashEvent)
    async def handle_server_crash(event: ServerCrashEvent):
        restart_info = " [Auto-restart enabled]" if event.will_restart else ""
        console.print(
            f"[red bold]💥 Server crashed![/red bold] [dim](exit code: {event.exit_code}){restart_info}[/dim]"
        )

    @on_event(LogLineEvent)
    async def handle_log_line(event: LogLineEvent):
        # Only show important log lines to avoid spam
        if event.level in ["WARN", "ERROR"]:
            level_color = "yellow" if event.level == "WARN" else "red"
            console.print(
                f"[{level_color}][{event.level}][/{level_color}] {event.message}"
            )
        elif "advancement" in event.message.lower():
            console.print(f"[gold]🏆[/gold] {event.message}")


@server_app.command("start")
def server_start(
    jar_path: Optional[str] = typer.Option(
        None, "--jar", "-j", help="Path to server JAR file"
    ),
    background: bool = typer.Option(
        True,
        "--background/--foreground",
        "-b/-f",
        help="Run server in background (default) or foreground",
    ),
) -> None:
    """Start the Minecraft server."""
    config = get_config()

    # Override JAR path if provided
    if jar_path:
        # For now, we'll need to recreate the server with new config
        # This is a simplified approach
        pass

    server = get_server_wrapper()

    if server.state == ServerState.RUNNING:
        console.print("[yellow]Server is already running![/yellow]")
        return

    console.print("[blue]Starting Minecraft server...[/blue]")

    async def start_server():
        success = await server.start()
        if success:
            console.print("[green]✓ Server started successfully![/green]")

            if background:
                console.print(
                    "[dim]Server is running in background. Use 'aetherius console' to monitor or 'aetherius server stop' to stop.[/dim]"
                )
            else:
                console.print(
                    "\n[dim]Server is running in foreground. Press Ctrl+C to stop.[/dim]"
                )

                try:
                    # Keep the CLI running while server is active
                    while server.state == ServerState.RUNNING:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    console.print("\n[yellow]Stopping server...[/yellow]")
                    await server.stop()
                    console.print("[green]✓ Server stopped.[/green]")
        else:
            console.print("[red]✗ Failed to start server![/red]")
            raise typer.Exit(1)

    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        if not background:
            console.print("\n[yellow]Interrupted by user[/yellow]")


@server_app.command("stop")
def server_stop(
    force: bool = typer.Option(
        False, "--force", "-f", help="Force kill the server process"
    )
) -> None:
    """Stop the Minecraft server."""
    from ..core.server_state import get_server_state

    server = get_server_wrapper()
    server_state = get_server_state()

    if server.state != ServerState.RUNNING:
        console.print("[yellow]Server is not running![/yellow]")
        return

    console.print("[blue]Stopping Minecraft server...[/blue]")

    async def stop_server():
        # Try to stop via our wrapper first
        if server.process is not None:
            if force:
                # Force kill the process
                server.process.kill()
                await server.process.wait()
                success = True
            else:
                success = await server.stop()
        else:
            # Server is running but not in our process, use state management to stop
            success = server_state.terminate_server(force=force)

        if success:
            console.print("[green]✓ Server stopped successfully![/green]")
        else:
            console.print("[red]✗ Failed to stop server![/red]")
            raise typer.Exit(1)

    try:
        asyncio.run(stop_server())
    except KeyboardInterrupt:
        console.print("\n[yellow]Force stopping server...[/yellow]")
        server_state.terminate_server(force=True)


@server_app.command("restart")
def server_restart() -> None:
    """Restart the Minecraft server."""
    server = get_server_wrapper()

    console.print("[blue]Restarting Minecraft server...[/blue]")

    async def restart_server():
        success = await server.restart()
        if success:
            console.print("[green]✓ Server restarted successfully![/green]")
            console.print("\n[dim]Server is now running. Press Ctrl+C to stop.[/dim]")

            try:
                # Keep the CLI running while server is active
                while server.state == ServerState.RUNNING:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopping server...[/yellow]")
                await server.stop()
                console.print("[green]✓ Server stopped.[/green]")
        else:
            console.print("[red]✗ Failed to restart server![/red]")
            raise typer.Exit(1)

    try:
        asyncio.run(restart_server())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")


@server_app.command("status")
def server_status() -> None:
    """Show server status."""
    from ..core.server_state import get_server_state

    server = get_server_wrapper()
    server_state = get_server_state()

    if server.state == ServerState.RUNNING:
        status_text = Text("RUNNING", style="green bold")

        # Get detailed server info from state
        server_info = server_state.get_server_info()
        if server_info:
            pid_info = f"PID: {server_info['pid']}"
            memory_info = f"Memory: {server_info['memory_usage']:.1f} MB"
            cpu_info = f"CPU: {server_info['cpu_percent']:.1f}%"
            start_time = server_info["start_time"]
        else:
            pid_info = (
                f"PID: {server.process.pid}" if server.process else "PID: Unknown"
            )
            memory_info = ""
            cpu_info = ""
            start_time = ""
    else:
        status_text = Text("STOPPED", style="red bold")
        pid_info = ""
        memory_info = ""
        cpu_info = ""
        start_time = ""

    panel_content = f"Status: {status_text}\n"
    if pid_info:
        panel_content += f"{pid_info}\n"
    if memory_info:
        panel_content += f"{memory_info}\n"
    if cpu_info:
        panel_content += f"{cpu_info}\n"
    if start_time:
        panel_content += f"Started: {start_time}\n"

    config = get_config()
    jar_path = config.get('server.jar_path', 'server/server.jar')
    panel_content += f"JAR: {jar_path}\n"
    from pathlib import Path
    panel_content += f"Working Dir: {Path.cwd()}"

    console.print(Panel(panel_content, title="Server Status", expand=False))


@app.command("cmd")
def send_command(
    command_parts: list[str] = typer.Argument(
        ..., help="Command and arguments to send to the server"
    )
) -> None:
    """Send a command to the running server.

    Examples:
        aetherius cmd list
        aetherius cmd give player minecraft:diamond 64
        aetherius cmd tp player1 100 64 200
        aetherius cmd say "Hello World"
    """
    server = get_server_wrapper()

    if server.state != ServerState.RUNNING:
        console.print("[red]Server is not running![/red]")
        raise typer.Exit(1)

    # Join all command parts into a single command string
    command = " ".join(command_parts)

    async def send_cmd():
        # Use the command queue approach with output capture
        try:
            # Add command to queue and wait for result
            from ..core.command_queue import get_command_queue

            command_queue = get_command_queue()

            console.print(f"[blue]Sending command:[/blue] {command}")
            command_id = command_queue.add_command(command, timeout=30.0)
            result = await command_queue.wait_for_completion(command_id, timeout=30.0)

            if result["status"] == "completed" and result["success"]:
                console.print("[green]✓ Command executed successfully[/green]")

                # Display captured output if available
                if result.get("output"):
                    console.print("[cyan]Server response:[/cyan]")
                    console.print(f"[dim]{result['output']}[/dim]")
                else:
                    console.print("[dim]No output captured for this command[/dim]")
            elif result["status"] == "timeout":
                console.print(f"[red]✗ Command timed out:[/red] {command}")
                raise typer.Exit(1)
            else:
                console.print(f"[red]✗ Command failed:[/red] {command}")
                if result.get("error"):
                    console.print(f"[red]Error:[/red] {result['error']}")
                raise typer.Exit(1)

        except Exception as e:
            console.print(f"[red]✗ Error sending command:[/red] {e}")
            console.print(
                "[yellow]Note: Cross-process command execution is experimental.[/yellow]"
            )
            console.print(
                "[dim]Try using the console mode for interactive command execution.[/dim]"
            )
            raise typer.Exit(1)

    asyncio.run(send_cmd())


@app.command("console")
def console_mode(
    console_type: str
    | None = typer.Option(
        None,
        "--type",
        "-t",
        help="Console type: 'enhanced', 'improved', 'stable', 'fallback', or 'info' for capabilities",
    ),
    no_server_check: bool = typer.Option(
        False,
        "--no-server-check",
        help="Skip server running check (useful for testing)",
    ),
) -> None:
    """Enter interactive console mode with real-time display and history."""
    server = get_server_wrapper()

    # Check server status unless explicitly skipped
    if not no_server_check and server.state != ServerState.RUNNING:
        console.print("[red]Server is not running! Start the server first.[/red]")
        console.print("[dim]Or use --no-server-check to start console anyway.[/dim]")
        raise typer.Exit(1)

    # Create command handler for the console
    async def command_handler(command: str) -> None:
        """Handle commands sent from the console."""
        if server.state == ServerState.RUNNING:
            try:
                if server.process is not None:
                    # Direct command if server is in same process
                    success = await server.send_command(command)
                    if not success:
                        raise Exception("Failed to send command to server")
                else:
                    # For cross-process, use command queue
                    from ..core.command_queue import get_command_queue

                    command_queue = get_command_queue()

                    command_id = command_queue.add_command(command, timeout=10.0)
                    result = await command_queue.wait_for_completion(
                        command_id, timeout=10.0
                    )

                    if result["status"] != "completed" or not result["success"]:
                        error_msg = result.get("error", "Unknown error")
                        raise Exception(f"Command failed: {error_msg}")
            except Exception as e:
                raise Exception(f"Error executing command: {str(e)}")
        else:
            raise Exception("Server is not running")

    # Start the console using the console manager
    async def start_console_async():
        from .console_manager import start_console

        await start_console(server, command_handler, console_type)

    try:
        asyncio.run(start_console_async())
    except KeyboardInterrupt:
        console.print("\n[yellow]Console interrupted by user[/yellow]")


@app.command("console-info")
def console_info() -> None:
    """Show terminal capabilities and console options."""
    from .console_manager import ConsoleManager

    server = get_server_wrapper()
    manager = ConsoleManager(server)

    info_text = manager.get_capabilities_info()
    console.print(Panel(info_text, title="Terminal Capabilities", expand=False))

    console.print("\n[bold]Console Options:[/bold]")
    console.print("• [cyan]aetherius console[/cyan] - Auto-detect best console")
    console.print(
        "• [cyan]aetherius console --type enhanced[/cyan] - Force enhanced console (experimental)"
    )
    console.print(
        "• [cyan]aetherius console --type improved[/cyan] - Force improved console (advanced)"
    )
    console.print(
        "• [cyan]aetherius console --type stable[/cyan] - Force stable console (recommended)"
    )
    console.print(
        "• [cyan]aetherius console --type fallback[/cyan] - Force fallback console"
    )
    console.print(
        "• [cyan]aetherius console --no-server-check[/cyan] - Start without server"
    )


def show_event_stats() -> None:
    """Show event statistics."""
    event_manager = get_event_manager()
    stats = event_manager.get_event_stats()

    if not stats:
        console.print("[yellow]No events have been fired yet.[/yellow]")
        return

    from rich.table import Table

    table = Table(title="Event Statistics")
    table.add_column("Event Type", style="cyan")
    table.add_column("Count", justify="right", style="magenta")

    for event_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        table.add_row(event_type, str(count))

    console.print(table)


def show_console_help() -> None:
    """Show console help."""
    help_text = """
[bold]Console Commands:[/bold]
• [cyan]stats[/cyan] - Show event statistics
• [cyan]help[/cyan] - Show this help message
• [cyan]exit/quit[/cyan] - Exit console mode

[bold]Server Commands:[/bold]
• [green]list[/green] - List online players
• [green]say <message>[/green] - Broadcast message
• [green]tp <player1> <player2>[/green] - Teleport player
• [green]gamemode <mode> <player>[/green] - Change gamemode
• [green]weather <clear|rain|thunder>[/green] - Change weather
• [green]time set <day|night|time>[/green] - Set time

[dim]Commands now provide real-time feedback and output capture[/dim]
[dim]Events are displayed in real-time with colored indicators[/dim]
"""
    console.print(Panel(help_text, title="Console Help", expand=False))


@events_app.command("stats")
def events_stats() -> None:
    """Show event system statistics."""
    show_event_stats()


@events_app.command("listeners")
def events_listeners() -> None:
    """Show registered event listeners."""
    event_manager = get_event_manager()
    listeners = event_manager.get_listeners()

    if not listeners:
        console.print("[yellow]No event listeners registered.[/yellow]")
        return

    from rich.table import Table

    table = Table(title="Registered Event Listeners")
    table.add_column("Event Type", style="cyan")
    table.add_column("Function", style="yellow")
    table.add_column("Priority", style="magenta")
    table.add_column("Async", style="green")

    # Group listeners by event type
    from collections import defaultdict

    listeners_by_type = defaultdict(list)

    for listener in listeners:
        event_type_name = listener.event_type.__name__
        listeners_by_type[event_type_name].append(listener)

    for event_type, type_listeners in sorted(listeners_by_type.items()):
        for i, listener in enumerate(type_listeners):
            event_name = event_type if i == 0 else ""
            function_name = listener.callback.__name__
            priority = listener.priority.name
            is_async = "Yes" if listener.is_async else "No"

            table.add_row(event_name, function_name, priority, is_async)

    console.print(table)


@events_app.command("test")
def events_test(
    event_type: str = typer.Argument(help="Event type to test (e.g., player_join)"),
) -> None:
    """Test firing a specific event type."""
    from ..core.events import EVENT_TYPES

    if event_type not in EVENT_TYPES:
        console.print(f"[red]Unknown event type: {event_type}[/red]")
        console.print(f"Available types: {', '.join(EVENT_TYPES.keys())}")
        raise typer.Exit(1)

    event_class = EVENT_TYPES[event_type]

    # Create a test event with dummy data
    test_data = {}
    if event_type == "player_join":
        test_data = {"player_name": "TestPlayer", "ip_address": "127.0.0.1"}
    elif event_type == "player_leave":
        test_data = {"player_name": "TestPlayer", "leave_reason": "Test"}
    elif event_type == "player_chat":
        test_data = {"player_name": "TestPlayer", "message": "Hello World!"}
    elif event_type == "player_death":
        test_data = {
            "player_name": "TestPlayer",
            "death_message": "fell from a high place",
        }
    elif event_type == "server_started":
        test_data = {"pid": 12345, "startup_time": 5.2}

    try:
        test_event = event_class(**test_data)

        async def fire_test_event():
            from ..core.event_manager import fire_event

            await fire_event(test_event)
            console.print(
                f"[green]✓[/green] Test event '{event_type}' fired successfully"
            )

        asyncio.run(fire_test_event())

    except Exception as e:
        console.print(f"[red]Error firing test event: {e}[/red]")


# Plugin management commands
@plugin_app.command("list")
def plugin_list() -> None:
    """List all loaded plugins."""
    plugin_manager = get_plugin_manager()

    # Try to auto-load plugins if none are loaded
    if not plugin_manager.list_plugins():

        async def auto_load():
            await plugin_manager.load_all_plugins()
            await plugin_manager.enable_all_plugins()

        asyncio.run(auto_load())

    plugins = plugin_manager.list_plugins()

    if not plugins:
        console.print(
            "[yellow]No plugins found. Run 'aetherius plugin load' first.[/yellow]"
        )
        return

    from rich.table import Table

    table = Table(title="Loaded Plugins")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Description", style="dim")

    for plugin_name in plugins:
        info = plugin_manager.get_plugin_info(plugin_name)
        status = "Enabled" if plugin_manager.is_enabled(plugin_name) else "Disabled"
        status_style = "green" if plugin_manager.is_enabled(plugin_name) else "red"

        table.add_row(
            plugin_name,
            info.version if info else "Unknown",
            f"[{status_style}]{status}[/{status_style}]",
            info.description if info else "No description",
        )

    console.print(table)


@plugin_app.command("load")
def plugin_load() -> None:
    """Load all plugins from the plugins directory."""
    plugin_manager = get_plugin_manager()

    async def load_plugins():
        console.print("[blue]Loading plugins...[/blue]")
        loaded = await plugin_manager.load_all_plugins()
        console.print(f"[green]✓[/green] Loaded {loaded} plugins")

        # Also enable all loaded plugins
        if loaded > 0:
            enabled = await plugin_manager.enable_all_plugins()
            console.print(f"[green]✓[/green] Enabled {enabled} plugins")

    asyncio.run(load_plugins())


@plugin_app.command("enable")
def plugin_enable(name: str = typer.Argument(help="Plugin name to enable")) -> None:
    """Enable a specific plugin."""
    plugin_manager = get_plugin_manager()

    async def enable_plugin():
        # Auto-load plugins if needed
        if not plugin_manager.list_plugins():
            await plugin_manager.load_all_plugins()

        success = await plugin_manager.enable_plugin(name)
        if success:
            console.print(f"[green]✓[/green] Enabled plugin: {name}")
        else:
            console.print(f"[red]✗[/red] Failed to enable plugin: {name}")
            raise typer.Exit(1)

    asyncio.run(enable_plugin())


@plugin_app.command("disable")
def plugin_disable(name: str = typer.Argument(help="Plugin name to disable")) -> None:
    """Disable a specific plugin."""
    plugin_manager = get_plugin_manager()

    async def disable_plugin():
        # Auto-load plugins if needed
        if not plugin_manager.list_plugins():
            await plugin_manager.load_all_plugins()
            await plugin_manager.enable_all_plugins()

        success = await plugin_manager.disable_plugin(name)
        if success:
            console.print(f"[green]✓[/green] Disabled plugin: {name}")
        else:
            console.print(f"[red]✗[/red] Failed to disable plugin: {name}")
            raise typer.Exit(1)

    asyncio.run(disable_plugin())


@plugin_app.command("reload")
def plugin_reload(name: str = typer.Argument(help="Plugin name to reload")) -> None:
    """Reload a specific plugin."""
    plugin_manager = get_plugin_manager()

    async def reload_plugin():
        success = await plugin_manager.reload_plugin(name)
        if success:
            console.print(f"[green]✓[/green] Reloaded plugin: {name}")
        else:
            console.print(f"[red]✗[/red] Failed to reload plugin: {name}")
            raise typer.Exit(1)

    asyncio.run(reload_plugin())


@plugin_app.command("info")
def plugin_info(
    name: str = typer.Argument(help="Plugin name to show info for"),
) -> None:
    """Show detailed information about a plugin."""
    plugin_manager = get_plugin_manager()

    # Auto-load plugins if needed
    if not plugin_manager.list_plugins():

        async def auto_load():
            await plugin_manager.load_all_plugins()
            await plugin_manager.enable_all_plugins()

        asyncio.run(auto_load())

    if not plugin_manager.is_loaded(name):
        console.print(f"[red]Plugin '{name}' is not loaded.[/red]")
        raise typer.Exit(1)

    info = plugin_manager.get_plugin_info(name)
    plugin = plugin_manager.get_plugin(name)

    if not info:
        console.print(f"[red]No information available for plugin '{name}'.[/red]")
        raise typer.Exit(1)

    # Create info panel
    info_text = f"""[bold]Name:[/bold] {info.name}
[bold]Version:[/bold] {info.version}
[bold]Author:[/bold] {info.author}
[bold]Description:[/bold] {info.description}

[bold]Status:[/bold] {"[green]Enabled[/green]" if plugin_manager.is_enabled(name) else "[red]Disabled[/red]"}
[bold]API Version:[/bold] {info.api_version}
"""

    if info.website:
        info_text += f"[bold]Website:[/bold] {info.website}\n"

    if info.depends:
        info_text += f"[bold]Dependencies:[/bold] {', '.join(info.depends)}\n"

    if info.soft_depends:
        info_text += f"[bold]Soft Dependencies:[/bold] {', '.join(info.soft_depends)}\n"

    console.print(Panel(info_text, title=f"Plugin: {name}", expand=False))


@plugin_app.command("stats")
def plugin_stats() -> None:
    """Show plugin system statistics."""
    plugin_manager = get_plugin_manager()

    # Auto-load plugins if needed
    if not plugin_manager.list_plugins():

        async def auto_load():
            await plugin_manager.load_all_plugins()
            await plugin_manager.enable_all_plugins()

        asyncio.run(auto_load())

    stats = plugin_manager.get_plugin_stats()

    stats_text = f"""[bold]Total Plugins:[/bold] {stats['total']}
[bold]Enabled:[/bold] [green]{stats['enabled']}[/green]
[bold]Disabled:[/bold] [red]{stats['disabled']}[/red]
"""

    console.print(Panel(stats_text, title="Plugin Statistics", expand=False))


# Component management commands
@component_app.command("list")
def component_list() -> None:
    """List all loaded components."""
    component_manager = get_component_manager()

    # 尝试获取组件列表，适配不同的组件管理器API
    components = []
    
    # 尝试不同的方法获取组件列表
    if hasattr(component_manager, 'list_components'):
        components = component_manager.list_components()
    elif hasattr(component_manager, 'list_loaded_components'):
        components = component_manager.list_loaded_components()
    elif hasattr(component_manager, '_components'):
        components = list(component_manager._components.keys())
    
    # 如果没有组件，尝试自动加载
    if not components:
        if hasattr(component_manager, 'load_all_components'):
            async def auto_load():
                await component_manager.load_all_components()
                if hasattr(component_manager, 'enable_all_components'):
                    await component_manager.enable_all_components()
            asyncio.run(auto_load())
            
            # 重新获取组件列表
            if hasattr(component_manager, 'list_components'):
                components = component_manager.list_components()
            elif hasattr(component_manager, 'list_loaded_components'):
                components = component_manager.list_loaded_components()
            elif hasattr(component_manager, '_components'):
                components = list(component_manager._components.keys())

    if not components:
        console.print(
            "[yellow]No components found. Run 'aetherius component load' first.[/yellow]"
        )
        return

    from rich.table import Table

    table = Table(title="Loaded Components")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Dependencies", style="yellow")
    table.add_column("Description", style="dim")

    for component_name in components:
        # 适配不同的API获取组件信息
        info = None
        if hasattr(component_manager, 'get_component_info'):
            info = component_manager.get_component_info(component_name)
        
        # 适配不同的API检查组件状态
        is_enabled = False
        if hasattr(component_manager, 'is_enabled'):
            is_enabled = component_manager.is_enabled(component_name)
        elif hasattr(component_manager, '_enabled_components'):
            is_enabled = component_name in component_manager._enabled_components
        
        status = "Enabled" if is_enabled else "Disabled"
        status_style = "green" if is_enabled else "red"

        deps = "None"
        if info and hasattr(info, 'depends') and info.depends:
            deps = ", ".join(info.depends)

        table.add_row(
            component_name,
            info.version if info and hasattr(info, 'version') else "Unknown",
            f"[{status_style}]{status}[/{status_style}]",
            deps,
            info.description if info and hasattr(info, 'description') else "No description",
        )

    console.print(table)


@component_app.command("load")
def component_load() -> None:
    """Load all components from the components directory."""
    component_manager = get_component_manager()

    async def load_components():
        console.print("[blue]Loading components...[/blue]")
        try:
            loaded = await component_manager.load_all_components()
            console.print(f"[green]✓[/green] Loaded {loaded} components")

            # Also enable all loaded components
            if loaded > 0:
                enabled = await component_manager.enable_all_components()
                console.print(f"[green]✓[/green] Enabled {enabled} components")
        except ValueError as e:
            console.print(f"[red]✗[/red] Failed to load components: {e}")
            raise typer.Exit(1)

    asyncio.run(load_components())


@component_app.command("enable")
def component_enable(
    name: str = typer.Argument(help="Component name to enable"),
) -> None:
    """Enable a specific component - 使用标准启动脚本或组件管理器."""
    try:
        # 首先查找组件标准启动脚本（与控制台逻辑一致）
        component_script_path = _find_component_start_script(name)

        if component_script_path:
            # 使用标准启动脚本启用组件
            console.print(f"[cyan]使用标准启动脚本启用组件 {name}...[/cyan]")
            _start_component_with_script(name, component_script_path)
        else:
            # 回退到组件管理器方法
            console.print("[yellow]未找到标准启动脚本，使用组件管理器启用...[/yellow]")
            _enable_component_fallback(name)

    except Exception as e:
        console.print(f"[red]✗[/red] 启用组件失败: {e}")
        raise typer.Exit(1)


@component_app.command("disable")
def component_disable(
    name: str = typer.Argument(help="Component name to disable"),
) -> None:
    """Disable a specific component."""
    component_manager = get_component_manager()

    async def disable_component():
        # Auto-load components if needed
        if not component_manager.list_components():
            await component_manager.load_all_components()
            await component_manager.enable_all_components()

        success = await component_manager.disable_component(name)
        if success:
            console.print(f"[green]✓[/green] Disabled component: {name}")
        else:
            console.print(f"[red]✗[/red] Failed to disable component: {name}")
            raise typer.Exit(1)

    asyncio.run(disable_component())


@component_app.command("reload")
def component_reload(
    name: str = typer.Argument(help="Component name to reload"),
) -> None:
    """Reload a specific component."""
    component_manager = get_component_manager()

    async def reload_component():
        success = await component_manager.reload_component(name)
        if success:
            console.print(f"[green]✓[/green] Reloaded component: {name}")
        else:
            console.print(f"[red]✗[/red] Failed to reload component: {name}")
            raise typer.Exit(1)

    asyncio.run(reload_component())


@component_app.command("info")
def component_info(
    name: str = typer.Argument(help="Component name to show info for"),
) -> None:
    """Show detailed information about a component."""
    component_manager = get_component_manager()

    # Auto-load components if needed
    if not component_manager.list_components():

        async def auto_load():
            await component_manager.load_all_components()
            await component_manager.enable_all_components()

        asyncio.run(auto_load())

    if not component_manager.is_loaded(name):
        console.print(f"[red]Component '{name}' is not loaded.[/red]")
        raise typer.Exit(1)

    info = component_manager.get_component_info(name)
    component = component_manager.get_component(name)

    if not info:
        console.print(f"[red]No information available for component '{name}'.[/red]")
        raise typer.Exit(1)

    # Create info panel
    info_text = f"""[bold]Name:[/bold] {info.name}
[bold]Version:[/bold] {info.version}
[bold]Author:[/bold] {info.author}
[bold]Description:[/bold] {info.description}

[bold]Status:[/bold] {"[green]Enabled[/green]" if component_manager.is_enabled(name) else "[red]Disabled[/red]"}
[bold]API Version:[/bold] {info.api_version}
"""

    if info.website:
        info_text += f"[bold]Website:[/bold] {info.website}\n"

    if info.depends:
        info_text += f"[bold]Hard Dependencies:[/bold] {', '.join(info.depends)}\n"

    if info.soft_depends:
        info_text += f"[bold]Soft Dependencies:[/bold] {', '.join(info.soft_depends)}\n"

    if info.load_before:
        info_text += f"[bold]Load Before:[/bold] {', '.join(info.load_before)}\n"

    if info.requires_packages:
        info_text += (
            f"[bold]Required Packages:[/bold] {', '.join(info.requires_packages)}\n"
        )

    console.print(Panel(info_text, title=f"Component: {name}", expand=False))


@component_app.command("stats")
def component_stats() -> None:
    """Show component system statistics."""
    component_manager = get_component_manager()

    # Auto-load components if needed
    if not component_manager.list_components():

        async def auto_load():
            await component_manager.load_all_components()
            await component_manager.enable_all_components()

        asyncio.run(auto_load())

    stats = component_manager.get_component_stats()

    stats_text = f"""[bold]Total Components:[/bold] {stats['total']}
[bold]Enabled:[/bold] [green]{stats['enabled']}[/green]
[bold]Disabled:[/bold] [red]{stats['disabled']}[/red]
"""

    console.print(Panel(stats_text, title="Component Statistics", expand=False))


@component_app.command("scan")
def component_scan() -> None:
    """Scan and discover components."""
    component_manager = get_component_manager()

    try:
        # 检查组件管理器是否支持扫描功能
        if hasattr(component_manager, "scan_components"):
            console.print("[cyan]正在扫描组件...[/cyan]")

            # 处理异步/同步方法
            import inspect

            if inspect.iscoroutinefunction(component_manager.scan_components):
                # 异步方法
                async def scan_async():
                    try:
                        discovered = await component_manager.scan_components()
                        console.print(f"[green]✓ 发现 {len(discovered)} 个组件[/green]")
                        for component_name in discovered:
                            console.print(f"  - {component_name}")
                        return discovered
                    except Exception as e:
                        console.print(f"[red]✗ 扫描失败: {e}[/red]")
                        raise typer.Exit(1)

                asyncio.run(scan_async())
            else:
                # 同步方法
                discovered = component_manager.scan_components()
                console.print(f"[green]✓ 发现 {len(discovered)} 个组件[/green]")
                for component_name in discovered:
                    console.print(f"  - {component_name}")
        else:
            console.print("[yellow]组件管理器不支持扫描功能[/yellow]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]扫描组件失败: {e}[/red]")
        raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show version and exit"),
) -> None:
    """Aetherius - A lightweight, high-performance Minecraft server management engine."""
    if version:
        from .. import __version__

        console.print(f"Aetherius {__version__}")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        console.print("Use --help for usage information.")
        raise typer.Exit()


if __name__ == "__main__":
    app()
