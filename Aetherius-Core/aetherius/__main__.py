#!/usr/bin/env python3
"""
Aetherius Core - 主入口点

当用户运行 `aetherius` 命令时的主入口
"""

import argparse
import asyncio
import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 延迟导入避免循环导入
def get_cli_main():
    from aetherius.cli.main import app as cli_app
    return cli_app

def get_aetherius_core():
    from aetherius.core.application import AetheriusCore
    return AetheriusCore


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog='aetherius',
        description='Aetherius Core - Minecraft Server Management Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  aetherius start                    # 启动 Aetherius Core 框架
  aetherius server start             # 启动 Minecraft 服务器
  aetherius server stop              # 停止 Minecraft 服务器
  aetherius server status            # 查看 Minecraft 服务器状态
  aetherius console                  # 启动交互式控制台
  aetherius cmd "say Hello World"    # 执行服务器命令
  aetherius config show             # 显示配置
  aetherius plugin list             # 插件管理
        """
    )

    # 全局选项
    parser.add_argument(
        '-c', '--config',
        type=Path,
        default='config/config.yaml',
        help='配置文件路径 (默认: config/config.yaml)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='详细输出'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='调试模式'
    )

    # 子命令
    subparsers = parser.add_subparsers(
        dest='command',
        help='可用命令',
        metavar='COMMAND'
    )

    # 核心系统命令
    start_parser = subparsers.add_parser('start', help='启动 Aetherius Core')
    start_parser.add_argument('--background', '-b', action='store_true', help='后台运行')

    # 服务器管理命令
    server_parser = subparsers.add_parser('server', help='Minecraft 服务器管理')
    server_subparsers = server_parser.add_subparsers(dest='server_action')

    start_parser = server_subparsers.add_parser('start', help='启动 Minecraft 服务器')
    start_parser.add_argument('--background', '-b', action='store_true', help='后台运行')
    start_parser.add_argument('--jar', '-j', help='服务器 JAR 文件路径')

    server_subparsers.add_parser('stop', help='停止服务器')
    server_subparsers.add_parser('restart', help='重启服务器')
    server_subparsers.add_parser('status', help='查看服务器状态')

    # 兼容的直接命令
    subparsers.add_parser('stop', help='停止服务器 (兼容命令)')
    subparsers.add_parser('restart', help='重启服务器 (兼容命令)')
    subparsers.add_parser('status', help='查看服务器状态 (兼容命令)')

    # 控制台命令
    console_parser = subparsers.add_parser('console', help='启动交互式控制台')

    # 命令执行
    cmd_parser = subparsers.add_parser('cmd', help='执行服务器命令')
    cmd_parser.add_argument('command', help='要执行的命令')
    cmd_parser.add_argument('--wait', '-w', action='store_true', help='等待命令完成')


    # 配置管理
    config_parser = subparsers.add_parser('config', help='配置管理')
    config_subparsers = config_parser.add_subparsers(dest='config_action')
    config_subparsers.add_parser('show', help='显示当前配置')
    config_subparsers.add_parser('validate', help='验证配置')
    config_subparsers.add_parser('init', help='初始化默认配置')

    # 插件管理
    plugin_parser = subparsers.add_parser('plugin', help='插件管理')
    plugin_subparsers = plugin_parser.add_subparsers(dest='plugin_action')
    plugin_subparsers.add_parser('list', help='列出所有插件')

    enable_parser = plugin_subparsers.add_parser('enable', help='启用插件')
    enable_parser.add_argument('name', help='插件名称')

    disable_parser = plugin_subparsers.add_parser('disable', help='禁用插件')
    disable_parser.add_argument('name', help='插件名称')

    # 组件管理 - 统一的指令集
    component_parser = subparsers.add_parser('component', help='组件管理')
    component_subparsers = component_parser.add_subparsers(dest='component_action')
    component_subparsers.add_parser('list', help='列出所有组件')
    component_subparsers.add_parser('scan', help='扫描并发现组件')
    component_subparsers.add_parser('load', help='加载所有组件')
    component_subparsers.add_parser('stats', help='显示组件统计信息')

    comp_enable_parser = component_subparsers.add_parser('enable', help='启用组件（使用标准启动脚本或组件管理器）')
    comp_enable_parser.add_argument('name', help='组件名称')

    comp_disable_parser = component_subparsers.add_parser('disable', help='禁用组件')
    comp_disable_parser.add_argument('name', help='组件名称')

    comp_reload_parser = component_subparsers.add_parser('reload', help='重载组件')
    comp_reload_parser.add_argument('name', help='组件名称')

    comp_info_parser = component_subparsers.add_parser('info', help='显示组件详细信息')
    comp_info_parser.add_argument('name', help='组件名称')

    # 兼容旧命令
    comp_start_parser = component_subparsers.add_parser('start', help='启动组件（兼容命令，等同于enable）')
    comp_start_parser.add_argument('name', help='组件名称')

    comp_stop_parser = component_subparsers.add_parser('stop', help='停止组件（兼容命令，等同于disable）')
    comp_stop_parser.add_argument('name', help='组件名称')

    # 系统管理
    system_parser = subparsers.add_parser('system', help='系统管理')
    system_subparsers = system_parser.add_subparsers(dest='system_action')
    system_subparsers.add_parser('info', help='显示系统信息')
    system_subparsers.add_parser('health', help='系统健康检查')
    system_subparsers.add_parser('logs', help='查看系统日志')

    return parser


async def handle_core_commands(args):
    """处理核心系统命令"""
    try:
        if args.command == 'start':
            print("🚀 启动 Aetherius Core...")
            AetheriusCore = get_aetherius_core()
            app = AetheriusCore()
            await app.run(args.config if args.config.exists() else None)

        elif args.command == 'server':
            if args.server_action == 'start':
                print("🎮 启动 Minecraft 服务器和持久化控制台...")
                from pathlib import Path

                from aetherius.core.persistent_console import start_persistent_console

                # 服务器配置
                server_jar = str(Path("server/server.jar").absolute())
                server_dir = str(Path("server").absolute())

                if args.jar:
                    server_jar = str(Path(args.jar).absolute())

                # 启动持久化控制台守护进程（包含服务器）
                await start_persistent_console(server_jar, server_dir)

            elif args.server_action == 'stop':
                print("🛑 停止 Minecraft 服务器...")
                from aetherius.core.server_state import get_server_state

                server_state = get_server_state()
                if server_state.is_server_running():
                    success = server_state.terminate_server()
                    if success:
                        print("✅ Minecraft 服务器已停止")
                    else:
                        print("❌ 停止服务器失败")
                else:
                    print("⚠️  服务器未运行")

            elif args.server_action == 'status':
                print("📊 检查 Minecraft 服务器状态...")
                from aetherius.core.server_state import get_server_state

                server_state = get_server_state()
                if server_state.is_server_running():
                    info = server_state.get_server_info()
                    if info:
                        print("✅ 服务器正在运行")
                        print(f"   PID: {info['pid']}")
                        print(f"   启动时间: {info['start_time']}")
                        print(f"   JAR路径: {info['jar_path']}")
                        print(f"   内存使用: {info['memory_usage']:.2f} MB")
                        print(f"   CPU使用率: {info['cpu_percent']:.2f}%")
                        print(f"   进程状态: {info['status']}")
                    else:
                        print("❌ 无法获取服务器信息")
                else:
                    print("🛑 服务器未运行")

            elif args.server_action == 'restart':
                print("🔄 重启 Minecraft 服务器...")
                from aetherius.core.server_state import get_server_state

                server_state = get_server_state()
                if server_state.is_server_running():
                    print("🛑 停止当前服务器...")
                    success = server_state.terminate_server()
                    if success:
                        print("✅ 服务器已停止")
                        # 等待一段时间后重新启动
                        import time
                        time.sleep(2)
                        print("🎮 重新启动服务器...")
                        # 重新调用启动逻辑
                        from aetherius.core.config_models import ServerConfig
                        from aetherius.core.server import ServerController

                        server_config = ServerConfig()
                        server = ServerController(server_config)
                        success = await server.start()
                        if success:
                            print("✅ Minecraft 服务器重启成功!")
                        else:
                            print("❌ Minecraft 服务器重启失败!")
                    else:
                        print("❌ 停止服务器失败，无法重启")
                else:
                    print("⚠️  服务器未运行，直接启动...")
                    # 直接启动服务器
                    from aetherius.core.config_models import ServerConfig
                    from aetherius.core.server import ServerController

                    server_config = ServerConfig()
                    server = ServerController(server_config)
                    success = await server.start()
                    if success:
                        print("✅ Minecraft 服务器启动成功!")
                    else:
                        print("❌ Minecraft 服务器启动失败!")

        elif args.command == 'console':
                print("🎮 连接到持久化控制台...")
                import os
                from pathlib import Path

                from aetherius.core.console_client import run_console_client

                socket_path = str(Path("data/console/console.sock").absolute())

                if not os.path.exists(socket_path):
                    print("⚠️  持久化控制台未运行")
                    print("💡 请先使用 'aetherius server start' 启动服务器和持久化控制台")

                    response = input("是否要启动服务器和持久化控制台? (y/N): ").strip().lower()
                    if response in ['y', 'yes']:
                        print("🎮 启动服务器和持久化控制台...")
                        from aetherius.core.persistent_console import (
                            start_persistent_console,
                        )

                        # 服务器配置
                        server_jar = str(Path("server/server.jar").absolute())
                        server_dir = str(Path("server").absolute())

                        # 启动持久化控制台守护进程（包含服务器）
                        await start_persistent_console(server_jar, server_dir)
                    else:
                        print("❌ 无法连接到持久化控制台")
                        return

                # 连接到持久化控制台
                try:
                    await run_console_client()
                except Exception as e:
                    print(f"❌ 控制台客户端运行失败: {e}")

        elif args.command == 'config':
            if args.config_action == 'show':
                from aetherius.core.config import ConfigManager, FileConfigSource
                config = ConfigManager()
                if args.config.exists():
                    config.add_source(FileConfigSource(args.config))
                    print("📋 当前配置:")
                    # 显示配置内容的逻辑
                else:
                    print(f"⚠️  配置文件不存在: {args.config}")

            elif args.config_action == 'init':
                print("🔧 初始化默认配置...")
                # 创建默认配置文件的逻辑

        elif args.command == 'system':
            if args.system_action == 'info':
                import sys
                print("ℹ️  Aetherius Core 系统信息")
                print("版本: 2.0.0")
                print(f"配置文件: {args.config}")
                print(f"工作目录: {Path.cwd()}")
                print(f"Python 版本: {sys.version}")

            elif args.system_action == 'health':
                print("🔍 系统健康检查")
                # 执行健康检查的逻辑

    except Exception as e:
        print(f"❌ 错误: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """主入口函数"""

    parser = create_parser()
    args = parser.parse_args()

    # 设置日志级别
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    elif args.verbose:
        import logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # 如果没有提供命令，显示帮助
    if not args.command:
        parser.print_help()
        return

    # 向后兼容的传统 CLI 命令 (cmd, stop, restart, status 等)
    # 这些命令使用现有的 CLI 系统
    if args.command in ['cmd', 'stop', 'restart', 'status']:
        try:
            cli_app = get_cli_main()
            # 构造正确的参数给 CLI 应用程序
            cli_args = ['server', args.command]
            if hasattr(args, 'jar_path') and args.jar_path:
                cli_args.extend(['--jar', args.jar_path])
            if hasattr(args, 'background') and args.background:
                cli_args.append('--background')
            cli_app(cli_args)
        except KeyboardInterrupt:
            print("\n👋 已取消")
        return

    # 组件管理命令 - 路由到统一的 CLI 应用
    if args.command == 'component':
        try:
            cli_app = get_cli_main()
            # 构造组件命令参数
            cli_args = ['component', args.component_action]

            # 如果有组件名称参数，添加它
            if hasattr(args, 'name') and args.name:
                cli_args.append(args.name)

            # 处理兼容命令的映射
            if args.component_action == 'start':
                cli_args[1] = 'enable'  # start -> enable
            elif args.component_action == 'stop':
                cli_args[1] = 'disable'  # stop -> disable

            cli_app(cli_args)
        except KeyboardInterrupt:
            print("\n👋 已取消")
        return

    # 核心系统命令和新功能
    try:
        asyncio.run(handle_core_commands(args))
    except KeyboardInterrupt:
        print("\n👋 已取消")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
