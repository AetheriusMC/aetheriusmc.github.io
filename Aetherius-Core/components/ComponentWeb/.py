#!/usr/bin/env python3
"""
Aetherius组件标准启动脚本 - ComponentWeb
============================================

这是ComponentWeb组件的标准启动脚本，符合Aetherius组件规范。
所有组件都应在其根目录提供名为"start_component.py"的标准启动脚本。

组件启动脚本规范：
1. 脚本名称必须为 start_component.py
2. 脚本必须位于组件根目录
3. 脚本必须提供完整的组件启动功能
4. 脚本必须支持标准的启动参数
5. 脚本必须包含组件状态检查和健康监测
"""

import sys
import os
import subprocess
import signal
import time
import threading
from pathlib import Path
from typing import Optional
import argparse

# 组件信息
COMPONENT_NAME = "ComponentWeb"
COMPONENT_VERSION = "1.0.0"
COMPONENT_DESCRIPTION = "Aetherius Web管理界面组件"

# 路径配置
COMPONENT_ROOT = Path(__file__).parent
BACKEND_DIR = COMPONENT_ROOT / "backend"
FRONTEND_DIR = COMPONENT_ROOT / "frontend"

# 进程管理
backend_process: Optional[subprocess.Popen] = None
frontend_process: Optional[subprocess.Popen] = None

def print_banner():
    """打印组件启动横幅"""
    banner = f"""
╔═══════════════════════════════════════════════════════════════════╗
║                      Aetherius Component                         ║
║                                                                   ║
║  组件名称: {COMPONENT_NAME:<20} 版本: {COMPONENT_VERSION:<10}     ║
║  描述: {COMPONENT_DESCRIPTION:<30}                    ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
"""
    print(banner)

def check_dependencies():
    """检查组件依赖"""
    print("📋 检查组件依赖...")
    
    # 检查Python依赖
    requirements_file = BACKEND_DIR / "requirements.txt"
    if requirements_file.exists():
        print(f"✓ 找到后端依赖文件: {requirements_file}")
    else:
        print(f"⚠ 未找到后端依赖文件: {requirements_file}")
    
    # 检查Node.js依赖（如果有前端）
    package_json = FRONTEND_DIR / "package.json"
    if package_json.exists():
        print(f"✓ 找到前端依赖文件: {package_json}")
        node_modules = FRONTEND_DIR / "node_modules"
        if not node_modules.exists():
            print("⚠ 前端依赖未安装，请运行: npm install")
            return False
    
    return True

def install_dependencies():
    """安装组件依赖"""
    print("📦 安装组件依赖...")
    
    # 安装Python依赖
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", 
            str(BACKEND_DIR / "requirements.txt")
        ], check=True, cwd=BACKEND_DIR)
        print("✓ Python依赖安装完成")
    except subprocess.CalledProcessError as e:
        print(f"✗ Python依赖安装失败: {e}")
        return False
    
    # 安装Node.js依赖（如果有前端）
    package_json = FRONTEND_DIR / "package.json"
    if package_json.exists():
        try:
            subprocess.run(["npm", "install"], check=True, cwd=FRONTEND_DIR)
            print("✓ Node.js依赖安装完成")
        except subprocess.CalledProcessError as e:
            print(f"✗ Node.js依赖安装失败: {e}")
            return False
    
    return True

def start_backend():
    """启动后端服务"""
    global backend_process
    
    print("🚀 启动后端服务...")
    
    # 切换到后端目录
    os.chdir(BACKEND_DIR)
    
    # 启动后端
    try:
        # 设置Python路径
        env = os.environ.copy()
        env['PYTHONPATH'] = str(BACKEND_DIR)
        
        backend_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "app.main:create_app",
            "--factory",
            "--host", "0.0.0.0",
            "--port", "8080",
            "--reload"
        ], env=env)
        
        print(f"✓ 后端服务已启动 (PID: {backend_process.pid})")
        print("📡 后端服务地址: http://localhost:8080")
        return True
        
    except Exception as e:
        print(f"✗ 后端服务启动失败: {e}")
        return False

def start_frontend():
    """启动前端服务"""
    global frontend_process
    
    package_json = FRONTEND_DIR / "package.json"
    if not package_json.exists():
        print("ℹ 未找到前端配置，跳过前端启动")
        return True
    
    print("🎨 启动前端服务...")
    
    try:
        frontend_process = subprocess.Popen([
            "npm", "run", "dev"
        ], cwd=FRONTEND_DIR)
        
        print(f"✓ 前端服务已启动 (PID: {frontend_process.pid})")
        print("🌐 前端服务地址: http://localhost:3000")
        return True
        
    except Exception as e:
        print(f"✗ 前端服务启动失败: {e}")
        return False

def check_health():
    """检查组件健康状态"""
    import requests
    
    print("🏥 检查组件健康状态...")
    
    # 检查后端健康状态
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            print("✓ 后端服务健康")
        else:
            print(f"⚠ 后端服务异常: HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ 后端服务连接失败: {e}")
        return False
    
    # 检查前端健康状态（如果启动了前端）
    if frontend_process:
        try:
            response = requests.get("http://localhost:3000", timeout=5)
            if response.status_code == 200:
                print("✓ 前端服务健康")
            else:
                print(f"⚠ 前端服务异常: HTTP {response.status_code}")
        except Exception as e:
            print(f"⚠ 前端服务连接失败: {e}")
    
    return True

def stop_component():
    """停止组件"""
    global backend_process, frontend_process
    
    print("\n🛑 停止组件服务...")
    
    if backend_process:
        print("停止后端服务...")
        backend_process.terminate()
        try:
            backend_process.wait(timeout=10)
            print("✓ 后端服务已停止")
        except subprocess.TimeoutExpired:
            print("⚠ 后端服务强制终止")
            backend_process.kill()
    
    if frontend_process:
        print("停止前端服务...")
        frontend_process.terminate()
        try:
            frontend_process.wait(timeout=10)
            print("✓ 前端服务已停止")
        except subprocess.TimeoutExpired:
            print("⚠ 前端服务强制终止")
            frontend_process.kill()

def signal_handler(signum, frame):
    """信号处理器"""
    print(f"\n收到信号 {signum}，正在关闭组件...")
    stop_component()
    sys.exit(0)

def monitor_processes():
    """监控进程状态"""
    while True:
        time.sleep(30)  # 每30秒检查一次
        
        if backend_process and backend_process.poll() is not None:
            print("⚠ 后端服务进程意外退出")
            break
        
        if frontend_process and frontend_process.poll() is not None:
            print("⚠ 前端服务进程意外退出")
            # 前端进程退出不算严重错误，继续运行

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description=f"{COMPONENT_NAME} 组件启动脚本")
    parser.add_argument("--install-deps", action="store_true", help="安装依赖")
    parser.add_argument("--backend-only", action="store_true", help="仅启动后端")
    parser.add_argument("--frontend-only", action="store_true", help="仅启动前端")
    parser.add_argument("--check-health", action="store_true", help="检查健康状态")
    parser.add_argument("--version", action="store_true", help="显示版本信息")
    parser.add_argument("--no-frontend", action="store_true", help="不启动前端服务")
    
    args = parser.parse_args()
    
    if args.version:
        print(f"{COMPONENT_NAME} v{COMPONENT_VERSION}")
        print(f"描述: {COMPONENT_DESCRIPTION}")
        return
    
    print_banner()
    
    if args.install_deps:
        if not install_dependencies():
            sys.exit(1)
        return
    
    if args.check_health:
        if not check_health():
            sys.exit(1)
        return
    
    # 检查依赖
    if not check_dependencies():
        print("❌ 依赖检查失败，请使用 --install-deps 安装依赖")
        sys.exit(1)
    
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 根据参数决定启动模式
        start_backend_service = not args.frontend_only
        start_frontend_service = not args.backend_only and not args.no_frontend
        
        print(f"🎯 启动模式:")
        print(f"  后端服务: {'✓' if start_backend_service else '✗'}")
        print(f"  前端服务: {'✓' if start_frontend_service else '✗'}")
        print()
        
        # 启动后端
        if start_backend_service:
            if not start_backend():
                print("❌ 后端启动失败，退出")
                sys.exit(1)
            print("⏳ 等待后端服务稳定...")
            time.sleep(4)
        
        # 启动前端
        if start_frontend_service:
            if not start_frontend():
                print("⚠ 前端启动失败，但继续运行后端服务")
            else:
                print("⏳ 等待前端服务稳定...")
                time.sleep(3)
        
        # 等待服务完全启动
        if start_backend_service or start_frontend_service:
            time.sleep(2)
        
        # 健康检查
        if start_backend_service:
            print("🏥 执行健康检查...")
            health_ok = check_health()
            if not health_ok:
                print("⚠ 健康检查未完全通过，但服务可能仍在启动中")
        
        print("\n🎉 组件启动完成！")
        
        # 显示服务访问信息
        if start_backend_service:
            print("📡 后端服务: http://localhost:8080")
        if start_frontend_service:
            print("🌐 前端服务: http://localhost:3000")
        
        print("\n💡 提示:")
        print("  - 按 Ctrl+C 停止所有服务")
        print("  - 使用 --backend-only 仅启动后端")
        print("  - 使用 --frontend-only 仅启动前端")
        print("  - 使用 --no-frontend 启动后端但不启动前端")
        
        # 启动进程监控
        monitor_thread = threading.Thread(target=monitor_processes, daemon=True)
        monitor_thread.start()
        
        # 主循环
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 收到中断信号，正在关闭服务...")
            
    except Exception as e:
        print(f"❌ 组件启动失败: {e}")
        sys.exit(1)
    finally:
        stop_component()

if __name__ == "__main__":
    main()