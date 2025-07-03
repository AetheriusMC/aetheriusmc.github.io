"""
组件管理API端点
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Any
import logging
import os
import json
import subprocess
from datetime import datetime

from ...utils.security import verify_jwt_token
from ...models.simple_models import User

router = APIRouter()
logger = logging.getLogger(__name__)
security = HTTPBearer()

# 认证依赖
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """获取当前用户（简化版）"""
    try:
        user = await verify_jwt_token(credentials.credentials)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# 模拟组件管理器（在实际项目中应该从Aetherius核心导入）
class ComponentManager:
    def __init__(self):
        self.components_dir = "/workspaces/aetheriusmc.github.io/Aetherius-Core/components"
        self.components_cache = {}
        self._scan_components()
    
    def _scan_components(self):
        """扫描可用组件"""
        try:
            if not os.path.exists(self.components_dir):
                os.makedirs(self.components_dir, exist_ok=True)
                
            # 扫描组件目录
            for item in os.listdir(self.components_dir):
                component_path = os.path.join(self.components_dir, item)
                if os.path.isdir(component_path):
                    self._load_component_info(item, component_path)
                    
        except Exception as e:
            logger.error(f"组件扫描失败: {e}")
    
    def _load_component_info(self, name: str, path: str):
        """加载组件信息"""
        try:
            # 查找组件配置文件
            config_files = ['component.json', 'manifest.json', 'config.json']
            component_info = {
                'name': name,
                'path': path,
                'enabled': False,
                'version': '1.0.0',
                'description': f'{name} 组件',
                'type': 'unknown',
                'dependencies': [],
                'status': 'stopped'
            }
            
            for config_file in config_files:
                config_path = os.path.join(path, config_file)
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config_data = json.load(f)
                            component_info.update(config_data)
                        break
                    except Exception as e:
                        logger.warning(f"无法读取组件配置 {config_path}: {e}")
            
            # 检查组件是否启用（查看进程或配置文件）
            component_info['enabled'] = self._check_component_enabled(name, path)
            component_info['status'] = 'running' if component_info['enabled'] else 'stopped'
            
            self.components_cache[name] = component_info
            
        except Exception as e:
            logger.error(f"加载组件 {name} 信息失败: {e}")
    
    def _check_component_enabled(self, name: str, path: str) -> bool:
        """检查组件是否启用"""
        try:
            # 检查是否有对应的启动脚本在运行
            startup_files = ['start.py', 'main.py', 'app.py']
            for startup_file in startup_files:
                startup_path = os.path.join(path, startup_file)
                if os.path.exists(startup_path):
                    # 简单检查：如果是WebConsole组件且当前在运行，则认为已启用
                    if name == 'WebConsole':
                        return True
            return False
        except Exception:
            return False
    
    def get_components(self) -> List[Dict[str, Any]]:
        """获取所有组件"""
        self._scan_components()  # 刷新组件信息
        return list(self.components_cache.values())
    
    def get_component(self, name: str) -> Dict[str, Any]:
        """获取指定组件"""
        if name not in self.components_cache:
            raise HTTPException(status_code=404, detail=f"组件 {name} 不存在")
        return self.components_cache[name]
    
    def enable_component(self, name: str) -> bool:
        """启用组件"""
        try:
            component = self.get_component(name)
            component_path = component['path']
            
            # 查找启动脚本
            startup_files = ['start.py', 'main.py', 'app.py']
            for startup_file in startup_files:
                startup_path = os.path.join(component_path, startup_file)
                if os.path.exists(startup_path):
                    # 在后台启动组件
                    logger.info(f"启用组件 {name}: {startup_path}")
                    # 这里应该集成到Aetherius核心的组件管理系统
                    # 目前只是模拟
                    self.components_cache[name]['enabled'] = True
                    self.components_cache[name]['status'] = 'running'
                    return True
            
            raise HTTPException(status_code=400, detail=f"组件 {name} 没有找到启动脚本")
            
        except Exception as e:
            logger.error(f"启用组件 {name} 失败: {e}")
            raise HTTPException(status_code=500, detail=f"启用组件失败: {str(e)}")
    
    def disable_component(self, name: str) -> bool:
        """禁用组件"""
        try:
            component = self.get_component(name)
            
            # 这里应该停止组件进程
            logger.info(f"禁用组件 {name}")
            # 目前只是模拟
            self.components_cache[name]['enabled'] = False
            self.components_cache[name]['status'] = 'stopped'
            return True
            
        except Exception as e:
            logger.error(f"禁用组件 {name} 失败: {e}")
            raise HTTPException(status_code=500, detail=f"禁用组件失败: {str(e)}")
    
    def restart_component(self, name: str) -> bool:
        """重启组件"""
        try:
            self.disable_component(name)
            return self.enable_component(name)
        except Exception as e:
            logger.error(f"重启组件 {name} 失败: {e}")
            raise HTTPException(status_code=500, detail=f"重启组件失败: {str(e)}")
    
    def get_component_logs(self, name: str, lines: int = 100) -> List[str]:
        """获取组件日志"""
        try:
            component = self.get_component(name)
            log_paths = [
                os.path.join(component['path'], 'logs', f'{name.lower()}.log'),
                os.path.join(component['path'], f'{name.lower()}.log'),
                os.path.join('/workspaces/aetheriusmc.github.io/Aetherius-Core/logs', f'{name.lower()}.log')
            ]
            
            for log_path in log_paths:
                if os.path.exists(log_path):
                    with open(log_path, 'r', encoding='utf-8') as f:
                        all_lines = f.readlines()
                        return [line.strip() for line in all_lines[-lines:]]
            
            return [f"未找到组件 {name} 的日志文件"]
            
        except Exception as e:
            logger.error(f"获取组件 {name} 日志失败: {e}")
            return [f"获取日志失败: {str(e)}"]

# 全局组件管理器实例
component_manager = ComponentManager()

@router.get("/components")
async def list_components(current_user: User = Depends(get_current_user)):
    """获取所有组件列表"""
    try:
        components = component_manager.get_components()
        return {"components": components}
    except Exception as e:
        logger.error(f"获取组件列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取组件列表失败: {str(e)}")

@router.get("/components/{component_name}")
async def get_component_detail(component_name: str, current_user: User = Depends(get_current_user)):
    """获取组件详细信息"""
    try:
        component = component_manager.get_component(component_name)
        return {"component": component}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取组件 {component_name} 详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取组件详情失败: {str(e)}")

@router.post("/components/{component_name}/enable")
async def enable_component(
    component_name: str, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """启用组件"""
    try:
        logger.info(f"用户 {current_user.username} 尝试启用组件 {component_name}")
        
        def enable_task():
            try:
                component_manager.enable_component(component_name)
                logger.info(f"组件 {component_name} 启用成功")
            except Exception as e:
                logger.error(f"后台启用组件 {component_name} 失败: {e}")
        
        background_tasks.add_task(enable_task)
        
        return {
            "message": f"组件 {component_name} 启用请求已提交",
            "status": "processing"
        }
    except Exception as e:
        logger.error(f"启用组件 {component_name} 失败: {e}")
        raise HTTPException(status_code=500, detail=f"启用组件失败: {str(e)}")

@router.post("/components/{component_name}/disable")
async def disable_component(
    component_name: str, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """禁用组件"""
    try:
        logger.info(f"用户 {current_user.username} 尝试禁用组件 {component_name}")
        
        def disable_task():
            try:
                component_manager.disable_component(component_name)
                logger.info(f"组件 {component_name} 禁用成功")
            except Exception as e:
                logger.error(f"后台禁用组件 {component_name} 失败: {e}")
        
        background_tasks.add_task(disable_task)
        
        return {
            "message": f"组件 {component_name} 禁用请求已提交",
            "status": "processing"
        }
    except Exception as e:
        logger.error(f"禁用组件 {component_name} 失败: {e}")
        raise HTTPException(status_code=500, detail=f"禁用组件失败: {str(e)}")

@router.post("/components/{component_name}/restart")
async def restart_component(
    component_name: str, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """重启组件"""
    try:
        logger.info(f"用户 {current_user.username} 尝试重启组件 {component_name}")
        
        def restart_task():
            try:
                component_manager.restart_component(component_name)
                logger.info(f"组件 {component_name} 重启成功")
            except Exception as e:
                logger.error(f"后台重启组件 {component_name} 失败: {e}")
        
        background_tasks.add_task(restart_task)
        
        return {
            "message": f"组件 {component_name} 重启请求已提交",
            "status": "processing"
        }
    except Exception as e:
        logger.error(f"重启组件 {component_name} 失败: {e}")
        raise HTTPException(status_code=500, detail=f"重启组件失败: {str(e)}")

@router.get("/components/{component_name}/logs")
async def get_component_logs(
    component_name: str, 
    lines: int = 100,
    current_user: User = Depends(get_current_user)
):
    """获取组件日志"""
    try:
        logs = component_manager.get_component_logs(component_name, lines)
        return {
            "component": component_name,
            "logs": logs,
            "lines": len(logs),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取组件 {component_name} 日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取组件日志失败: {str(e)}")

@router.get("/components/status/summary")
async def get_components_summary(current_user: User = Depends(get_current_user)):
    """获取组件状态摘要"""
    try:
        components = component_manager.get_components()
        
        total = len(components)
        enabled = len([c for c in components if c.get('enabled', False)])
        disabled = total - enabled
        
        return {
            "total": total,
            "enabled": enabled,
            "disabled": disabled,
            "components_overview": [
                {
                    "name": c['name'],
                    "enabled": c.get('enabled', False),
                    "status": c.get('status', 'unknown'),
                    "type": c.get('type', 'unknown')
                }
                for c in components
            ]
        }
    except Exception as e:
        logger.error(f"获取组件摘要失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取组件摘要失败: {str(e)}")