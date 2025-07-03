"""
控制台客户端
连接到持久化控制台守护进程的客户端
"""

import asyncio
import json
import logging
import os
import signal
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ConsoleClient:
    """控制台客户端"""

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

    async def send_command(self, command: str) -> dict[str, Any]:
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

            # 使用一个短暂的等待来让响应通过listen_messages处理
            # 不直接读取响应，避免与listen_messages冲突
            await asyncio.sleep(0.1)
            
            return {"success": True, "message": "命令已发送"}

        except Exception as e:
            logger.error(f"发送命令失败: {e}")
            return {"success": False, "error": str(e)}

    async def listen_messages(self) -> None:
        """监听服务器消息"""
        if not self.reader:
            return

        try:
            while self.running:
                try:
                    data = await asyncio.wait_for(self.reader.readline(), timeout=1.0)
                    if not data:
                        break

                    try:
                        message = json.loads(data.decode().strip())
                        msg_type = message.get("type")
                        
                        if msg_type == "log":
                            content = message.get("content", "")
                            is_error = message.get("is_error", False)

                            if is_error:
                                print(f"[错误] {content}")
                            else:
                                print(f"[日志] {content}")
                        
                        elif msg_type == "response":
                            # 处理命令响应
                            success = message.get("success", False)
                            output = message.get("output", "")
                            error = message.get("error", "")
                            
                            if success:
                                print("  ✓ 执行成功")
                                if output:
                                    print(f"  ← 响应:\n{output}")
                            else:
                                print(f"  ✗ 执行失败: {error}")
                                if output:
                                    print(f"  详情: {output}")

                    except json.JSONDecodeError:
                        continue

                except asyncio.TimeoutError:
                    continue

        except Exception as e:
            logger.error(f"监听消息时出错: {e}")


async def run_console_client() -> None:
    """运行控制台客户端"""
    socket_path = str(Path("data/console/console.sock").absolute())

    if not os.path.exists(socket_path):
        print("❌ 无法连接到持久化控制台")
        print("💡 请先使用 'aetherius server start' 启动服务器和持久化控制台")
        return

    client = ConsoleClient(socket_path)

    if not await client.connect():
        print("❌ 无法连接到持久化控制台")
        return

    print()
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║                                                                   ║")
    print("║    █████╗ ███████╗████████╗██╗  ██╗███████╗██████╗ ██╗██╗   ██╗███║")
    print("║   ██╔══██╗██╔════╝╚══██╔══╝██║  ██║██╔════╝██╔══██╗██║██║   ██║██╔║")
    print("║   ███████║█████╗     ██║   ███████║█████╗  ██████╔╝██║██║   ██║███║")
    print("║   ██╔══██║██╔══╝     ██║   ██╔══██║██╔══╝  ██╔══██╗██║██║   ██║╚══║")
    print("║   ██║  ██║███████╗   ██║   ██║  ██║███████╗██║  ██║██║╚██████╔╝███║")
    print("║   ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝ ╚═════╝ ╚══║")
    print("║                                                                   ║")
    print("║                    持久化控制台客户端                              ║")
    print("║                                                                   ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print()
    print("✓ Aetherius 持久化控制台")
    print()
    print("✅ 已连接到持久化控制台")
    print("💡 提示:")
    print("   / - Minecraft命令 (例: /help, /list, /stop)")
    print("   $ - 组件管理命令 (例: $help, $list, $enable Web)")
    print("   ! - Aetherius系统命令 (例: !help, !status, !info)")
    print("   输入 'quit' 或 'exit' 断开连接")
    print("💡 持久化控制台将继续在后台运行，您可以随时重新连接")
    print()

    # 启动消息监听任务
    listen_task = asyncio.create_task(client.listen_messages())

    # 设置信号处理
    def signal_handler():
        print("\n🔌 正在断开连接...")
        asyncio.create_task(client.disconnect())

    if hasattr(signal, 'SIGINT'):
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGINT, signal_handler)

    try:
        while client.running:
            try:
                # 读取用户输入
                line = await asyncio.to_thread(input, "Aetherius> ")
                line = line.strip()

                if not line:
                    continue

                if line.lower() in ['quit', 'exit']:
                    print("断开连接中...")
                    break

                # 处理命令
                if line.startswith('/'):
                    # Minecraft命令
                    command = line[1:]  # 移除 / 前缀
                    print(f"→ Minecraft: /{command}")
                    await client.send_command(command)

                elif line.startswith('!'):
                    # Aetherius命令
                    command = line[1:]
                    print(f"→ Aetherius: !{command}")
                    await client.send_command(line)

                elif line.startswith('$'):
                    # 组件命令
                    command = line[1:]
                    print(f"→ Component: ${command}")
                    await client.send_command(line)

                else:
                    print("提示: 使用 / 前缀执行Minecraft命令，使用 ! 前缀执行Aetherius系统命令，使用 $ 前缀执行组件命令")

            except EOFError:
                print("\n输入结束，断开连接...")
                break
            except KeyboardInterrupt:
                print("\n🔌 正在断开连接...")
                break
            except Exception as e:
                logger.error(f"处理输入时出错: {e}")

    finally:
        listen_task.cancel()
        await client.disconnect()
        print("🔌 已断开与持久化控制台的连接")
