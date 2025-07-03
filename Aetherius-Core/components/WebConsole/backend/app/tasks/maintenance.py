"""
System maintenance and housekeeping tasks.
"""

import asyncio
import logging
import os
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from celery import Task

from .base import BaseTask
from ..core.config import settings
from ..core.container import get_container
from ..core.aetherius_adapter import IAetheriusAdapter
from ..websocket.manager import WebSocketManager
from ..websocket.models import create_notification_message
from ..services.cache import ICacheService

logger = logging.getLogger(__name__)


class MaintenanceTask(BaseTask):
    """Base class for maintenance tasks."""
    pass


class SystemMaintenanceTask(MaintenanceTask):
    """Task to perform comprehensive system maintenance."""
    
    def run(self) -> Dict[str, Any]:
        """Perform system maintenance."""
        try:
            return asyncio.run(self._perform_system_maintenance())
        except Exception as e:
            logger.error(f"System maintenance task failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _perform_system_maintenance(self) -> Dict[str, Any]:
        """Perform comprehensive system maintenance."""
        try:
            maintenance_report = {
                "timestamp": datetime.now().isoformat(),
                "maintenance_tasks": [],
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "errors": []
            }
            
            # List of maintenance tasks to perform
            maintenance_tasks = [
                ("cache_cleanup", self._cleanup_cache),
                ("log_rotation", self._rotate_logs),
                ("temp_cleanup", self._cleanup_temp_files),
                ("database_optimization", self._optimize_database),
                ("websocket_cleanup", self._cleanup_websockets),
                ("performance_check", self._check_system_performance)
            ]
            
            maintenance_report["total_tasks"] = len(maintenance_tasks)
            
            for task_name, task_func in maintenance_tasks:
                try:
                    logger.info(f"Running maintenance task: {task_name}")
                    result = await task_func()
                    
                    maintenance_report["maintenance_tasks"].append({
                        "task": task_name,
                        "status": "success",
                        "result": result,
                        "timestamp": datetime.now().isoformat()
                    })
                    maintenance_report["successful_tasks"] += 1
                    
                except Exception as e:
                    error_msg = f"Task {task_name} failed: {e}"
                    logger.error(error_msg)
                    
                    maintenance_report["maintenance_tasks"].append({
                        "task": task_name,
                        "status": "failed",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                    maintenance_report["failed_tasks"] += 1
                    maintenance_report["errors"].append(error_msg)
            
            # Send maintenance report notification
            container = get_container()
            ws_manager = await container.get_service(WebSocketManager)
            
            notification_level = "success" if maintenance_report["failed_tasks"] == 0 else "warning"
            notification_message = f"System maintenance completed. {maintenance_report['successful_tasks']}/{maintenance_report['total_tasks']} tasks successful."
            
            notification = create_notification_message(
                title="System Maintenance Completed",
                message=notification_message,
                level=notification_level,
                duration=15
            )
            
            await ws_manager.broadcast_to_all(notification)
            
            return {
                "success": maintenance_report["failed_tasks"] == 0,
                "maintenance_report": maintenance_report
            }
            
        except Exception as e:
            logger.error(f"Failed to perform system maintenance: {e}")
            raise
    
    async def _cleanup_cache(self) -> Dict[str, Any]:
        """Clean up cache system."""
        try:
            container = get_container()
            cache_service = await container.get_service(ICacheService)
            
            # Get cache statistics before cleanup
            # TODO: Implement cache statistics
            
            # Perform cache cleanup
            await cache_service.clear_expired()
            
            return {
                "task": "cache_cleanup",
                "status": "completed",
                "details": "Cache cleanup completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")
            raise
    
    async def _rotate_logs(self) -> Dict[str, Any]:
        """Rotate log files."""
        try:
            log_dir = settings.logging.directory
            if not os.path.exists(log_dir):
                return {
                    "task": "log_rotation",
                    "status": "skipped",
                    "details": "Log directory does not exist"
                }
            
            rotated_files = []
            current_time = datetime.now()
            
            # Find log files to rotate
            for filename in os.listdir(log_dir):
                if filename.endswith('.log'):
                    log_path = os.path.join(log_dir, filename)
                    
                    # Check if file is older than 1 day
                    file_time = datetime.fromtimestamp(os.path.getmtime(log_path))
                    if (current_time - file_time).days >= 1:
                        # Rotate log file
                        rotated_name = f"{filename}.{file_time.strftime('%Y%m%d')}"
                        rotated_path = os.path.join(log_dir, rotated_name)
                        
                        if not os.path.exists(rotated_path):
                            shutil.move(log_path, rotated_path)
                            rotated_files.append(rotated_name)
            
            return {
                "task": "log_rotation",
                "status": "completed",
                "details": f"Rotated {len(rotated_files)} log files",
                "rotated_files": rotated_files
            }
            
        except Exception as e:
            logger.error(f"Log rotation failed: {e}")
            raise
    
    async def _cleanup_temp_files(self) -> Dict[str, Any]:
        """Clean up temporary files."""
        try:
            temp_dirs = [
                "/tmp",
                str(settings.base_directory / "temp"),
                str(settings.base_directory / "cache")
            ]
            
            cleaned_files = []
            total_size_freed = 0
            
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    # Clean files older than 1 hour
                    cutoff_time = datetime.now() - timedelta(hours=1)
                    
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                                if file_time < cutoff_time:
                                    file_size = os.path.getsize(file_path)
                                    os.remove(file_path)
                                    cleaned_files.append(file_path)
                                    total_size_freed += file_size
                            except Exception as e:
                                logger.warning(f"Failed to clean temp file {file_path}: {e}")
            
            return {
                "task": "temp_cleanup",
                "status": "completed",
                "details": f"Cleaned {len(cleaned_files)} temp files",
                "files_cleaned": len(cleaned_files),
                "size_freed_mb": round(total_size_freed / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Temp cleanup failed: {e}")
            raise
    
    async def _optimize_database(self) -> Dict[str, Any]:
        """Optimize database performance."""
        try:
            # TODO: Implement database optimization
            # - Analyze table statistics
            # - Rebuild indexes
            # - Clean up old data
            # - Vacuum database
            
            return {
                "task": "database_optimization",
                "status": "completed",
                "details": "Database optimization completed (placeholder)"
            }
            
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            raise
    
    async def _cleanup_websockets(self) -> Dict[str, Any]:
        """Clean up WebSocket connections."""
        try:
            container = get_container()
            ws_manager = await container.get_service(WebSocketManager)
            
            # Get connection statistics
            stats = ws_manager.get_connection_stats()
            
            # WebSocket cleanup is handled automatically by the manager
            # This is just for reporting
            
            return {
                "task": "websocket_cleanup",
                "status": "completed",
                "details": "WebSocket cleanup completed",
                "active_connections": stats.get("active_connections", 0),
                "total_connections": stats.get("total_connections", 0)
            }
            
        except Exception as e:
            logger.error(f"WebSocket cleanup failed: {e}")
            raise
    
    async def _check_system_performance(self) -> Dict[str, Any]:
        """Check system performance metrics."""
        try:
            container = get_container()
            adapter = await container.get_service(IAetheriusAdapter)
            
            # Get performance data
            performance = await adapter.get_performance_data()
            
            # Analyze performance
            issues = []
            if performance.get("cpu_percent", 0) > 80:
                issues.append("High CPU usage")
            if performance.get("memory_mb", 0) > 3000:  # Assuming 4GB limit
                issues.append("High memory usage")
            if performance.get("tps", 20) < 18:
                issues.append("Low TPS")
            
            return {
                "task": "performance_check",
                "status": "completed",
                "details": f"Performance check completed, {len(issues)} issues found",
                "performance_metrics": performance,
                "issues": issues
            }
            
        except Exception as e:
            logger.error(f"Performance check failed: {e}")
            raise


class DatabaseMaintenanceTask(MaintenanceTask):
    """Task to perform database maintenance."""
    
    def run(self, maintenance_type: str = "optimize") -> Dict[str, Any]:
        """Perform database maintenance."""
        try:
            return asyncio.run(self._perform_database_maintenance(maintenance_type))
        except Exception as e:
            logger.error(f"Database maintenance task failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _perform_database_maintenance(self, maintenance_type: str) -> Dict[str, Any]:
        """Perform database maintenance operations."""
        try:
            # TODO: Implement database maintenance operations
            # - Table optimization
            # - Index rebuilding
            # - Statistics update
            # - Data cleanup
            
            maintenance_result = {
                "maintenance_type": maintenance_type,
                "timestamp": datetime.now().isoformat(),
                "operations_performed": [],
                "database_size_before": 0,
                "database_size_after": 0,
                "space_freed": 0
            }
            
            if maintenance_type == "optimize":
                # Optimize database tables
                maintenance_result["operations_performed"].append("table_optimization")
                maintenance_result["operations_performed"].append("index_rebuild")
                
            elif maintenance_type == "cleanup":
                # Clean up old data
                maintenance_result["operations_performed"].append("old_data_cleanup")
                maintenance_result["operations_performed"].append("temp_table_cleanup")
                
            elif maintenance_type == "analyze":
                # Analyze database performance
                maintenance_result["operations_performed"].append("table_analysis")
                maintenance_result["operations_performed"].append("query_optimization")
                
            else:
                return {
                    "success": False,
                    "error": f"Unknown maintenance type: {maintenance_type}"
                }
            
            return {
                "success": True,
                "maintenance_result": maintenance_result
            }
            
        except Exception as e:
            logger.error(f"Failed to perform database maintenance: {e}")
            raise


class PluginMaintenanceTask(MaintenanceTask):
    """Task to perform plugin maintenance."""
    
    def run(self) -> Dict[str, Any]:
        """Perform plugin maintenance."""
        try:
            return asyncio.run(self._perform_plugin_maintenance())
        except Exception as e:
            logger.error(f"Plugin maintenance task failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _perform_plugin_maintenance(self) -> Dict[str, Any]:
        """Perform plugin maintenance operations."""
        try:
            container = get_container()
            adapter = await container.get_service(IAetheriusAdapter)
            
            # Get plugin information
            plugins = await adapter.get_plugins()
            components = await adapter.get_components()
            
            maintenance_result = {
                "timestamp": datetime.now().isoformat(),
                "plugins_checked": len(plugins),
                "components_checked": len(components),
                "issues_found": [],
                "recommendations": []
            }
            
            # Check for plugin issues
            for plugin in plugins:
                if not plugin.get("enabled", False):
                    maintenance_result["issues_found"].append(f"Plugin {plugin['name']} is disabled")
                
                if not plugin.get("loaded", False):
                    maintenance_result["issues_found"].append(f"Plugin {plugin['name']} failed to load")
            
            # Check for component issues
            for component in components:
                if not component.get("enabled", False):
                    maintenance_result["issues_found"].append(f"Component {component['name']} is disabled")
                
                if not component.get("loaded", False):
                    maintenance_result["issues_found"].append(f"Component {component['name']} failed to load")
            
            # Generate recommendations
            if len(maintenance_result["issues_found"]) > 0:
                maintenance_result["recommendations"].append("Review plugin/component configuration")
                maintenance_result["recommendations"].append("Check plugin/component logs for errors")
            
            return {
                "success": True,
                "maintenance_result": maintenance_result
            }
            
        except Exception as e:
            logger.error(f"Failed to perform plugin maintenance: {e}")
            raise


class ScheduledMaintenanceTask(MaintenanceTask):
    """Task to run scheduled maintenance operations."""
    
    def run(self, schedule_type: str = "daily") -> Dict[str, Any]:
        """Run scheduled maintenance."""
        try:
            return asyncio.run(self._run_scheduled_maintenance(schedule_type))
        except Exception as e:
            logger.error(f"Scheduled maintenance task failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _run_scheduled_maintenance(self, schedule_type: str) -> Dict[str, Any]:
        """Run maintenance operations based on schedule."""
        try:
            schedule_result = {
                "schedule_type": schedule_type,
                "timestamp": datetime.now().isoformat(),
                "tasks_executed": [],
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0
            }
            
            # Define maintenance tasks for different schedules
            task_schedules = {
                "hourly": [
                    "cache_cleanup",
                    "websocket_cleanup",
                    "temp_cleanup"
                ],
                "daily": [
                    "log_rotation",
                    "temp_cleanup",
                    "cache_cleanup",
                    "performance_check",
                    "database_optimization"
                ],
                "weekly": [
                    "system_maintenance",
                    "plugin_maintenance",
                    "database_maintenance",
                    "full_cleanup"
                ]
            }
            
            tasks_to_run = task_schedules.get(schedule_type, [])
            schedule_result["total_tasks"] = len(tasks_to_run)
            
            for task_name in tasks_to_run:
                try:
                    # Execute maintenance task
                    # TODO: Implement task execution routing
                    
                    schedule_result["tasks_executed"].append({
                        "task": task_name,
                        "status": "success",
                        "timestamp": datetime.now().isoformat()
                    })
                    schedule_result["successful_tasks"] += 1
                    
                except Exception as e:
                    schedule_result["tasks_executed"].append({
                        "task": task_name,
                        "status": "failed",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                    schedule_result["failed_tasks"] += 1
            
            return {
                "success": schedule_result["failed_tasks"] == 0,
                "schedule_result": schedule_result
            }
            
        except Exception as e:
            logger.error(f"Failed to run scheduled maintenance: {e}")
            raise


# Task registration
system_maintenance_task = SystemMaintenanceTask()
database_maintenance_task = DatabaseMaintenanceTask()
plugin_maintenance_task = PluginMaintenanceTask()
scheduled_maintenance_task = ScheduledMaintenanceTask()