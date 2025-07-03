"""
Monitoring and performance tracking tasks.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from celery import Task

from .base import BaseTask
from ..core.config import settings
from ..core.container import get_container
from ..core.aetherius_adapter import IAetheriusAdapter
from ..websocket.manager import WebSocketManager
from ..websocket.models import create_performance_update_message, create_dashboard_update_message

logger = logging.getLogger(__name__)


class MonitoringTask(BaseTask):
    """Base class for monitoring tasks."""
    pass


class PerformanceMonitoringTask(MonitoringTask):
    """Task to collect and broadcast performance metrics."""
    
    def run(self) -> Dict[str, Any]:
        """Collect performance metrics."""
        try:
            return asyncio.run(self._collect_performance_metrics())
        except Exception as e:
            logger.error(f"Performance monitoring task failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect performance metrics from Aetherius Core."""
        try:
            container = get_container()
            adapter = await container.get_service(IAetheriusAdapter)
            ws_manager = await container.get_service(WebSocketManager)
            
            # Get performance data
            performance_data = await adapter.get_performance_data()
            
            # Create WebSocket message
            performance_message = create_performance_update_message(
                cpu_percent=performance_data.get("cpu_percent", 0.0),
                memory_mb=performance_data.get("memory_mb", 0.0),
                uptime_seconds=performance_data.get("uptime_seconds", 0.0),
                tps=performance_data.get("tps", 20.0)
            )
            
            # Broadcast to monitoring connections
            from ..websocket.models import ConnectionType
            await ws_manager.broadcast_to_type(ConnectionType.MONITORING, performance_message)
            
            return {
                "success": True,
                "metrics": performance_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to collect performance metrics: {e}")
            raise


class SystemHealthCheckTask(MonitoringTask):
    """Task to perform system health checks."""
    
    def run(self) -> Dict[str, Any]:
        """Perform system health check."""
        try:
            return asyncio.run(self._perform_health_check())
        except Exception as e:
            logger.error(f"Health check task failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive system health check."""
        try:
            container = get_container()
            adapter = await container.get_service(IAetheriusAdapter)
            
            health_status = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "healthy",
                "services": {}
            }
            
            # Check server status
            try:
                server_status = await adapter.get_server_status()
                health_status["services"]["server"] = {
                    "status": "healthy" if server_status.get("status") == "running" else "unhealthy",
                    "details": server_status
                }
            except Exception as e:
                health_status["services"]["server"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["overall_status"] = "degraded"
            
            # Check performance metrics
            try:
                performance = await adapter.get_performance_data()
                cpu_healthy = performance.get("cpu_percent", 0) < 90
                memory_healthy = performance.get("memory_mb", 0) < 3500  # Assuming 4GB limit
                tps_healthy = performance.get("tps", 20) > 15
                
                perf_status = "healthy" if all([cpu_healthy, memory_healthy, tps_healthy]) else "warning"
                health_status["services"]["performance"] = {
                    "status": perf_status,
                    "details": performance
                }
                
                if perf_status != "healthy" and health_status["overall_status"] == "healthy":
                    health_status["overall_status"] = "warning"
                    
            except Exception as e:
                health_status["services"]["performance"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["overall_status"] = "degraded"
            
            # Check WebSocket manager
            try:
                ws_manager = await container.get_service(WebSocketManager)
                ws_stats = ws_manager.get_connection_stats()
                health_status["services"]["websocket"] = {
                    "status": "healthy",
                    "details": ws_stats
                }
            except Exception as e:
                health_status["services"]["websocket"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["overall_status"] = "degraded"
            
            return {
                "success": True,
                "health": health_status
            }
            
        except Exception as e:
            logger.error(f"Failed to perform health check: {e}")
            raise


class DashboardUpdateTask(MonitoringTask):
    """Task to update dashboard with latest information."""
    
    def run(self) -> Dict[str, Any]:
        """Update dashboard data."""
        try:
            return asyncio.run(self._update_dashboard())
        except Exception as e:
            logger.error(f"Dashboard update task failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _update_dashboard(self) -> Dict[str, Any]:
        """Collect and broadcast dashboard update."""
        try:
            container = get_container()
            adapter = await container.get_service(IAetheriusAdapter)
            ws_manager = await container.get_service(WebSocketManager)
            
            # Collect dashboard data
            server_status = await adapter.get_server_status()
            performance_data = await adapter.get_performance_data()
            online_players = await adapter.get_online_players()
            
            # Create dashboard update message
            dashboard_message = create_dashboard_update_message(
                server_status=server_status,
                performance=performance_data,
                player_count=len(online_players),
                recent_events=[]  # TODO: Implement event history
            )
            
            # Broadcast to dashboard connections
            from ..websocket.models import ConnectionType
            await ws_manager.broadcast_to_type(ConnectionType.DASHBOARD, dashboard_message)
            
            return {
                "success": True,
                "dashboard_data": {
                    "server_status": server_status,
                    "performance": performance_data,
                    "player_count": len(online_players)
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}")
            raise


class LogAnalysisTask(MonitoringTask):
    """Task to analyze server logs for issues."""
    
    def run(self, log_lines: List[str]) -> Dict[str, Any]:
        """Analyze log lines for patterns and issues."""
        try:
            return self._analyze_logs(log_lines)
        except Exception as e:
            logger.error(f"Log analysis task failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _analyze_logs(self, log_lines: List[str]) -> Dict[str, Any]:
        """Analyze log lines for issues and patterns."""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_lines": len(log_lines),
            "error_count": 0,
            "warning_count": 0,
            "critical_issues": [],
            "performance_issues": [],
            "player_issues": [],
            "patterns": {}
        }
        
        error_patterns = [
            r"ERROR",
            r"SEVERE",
            r"FATAL",
            r"Exception",
            r"OutOfMemoryError",
            r"StackOverflowError"
        ]
        
        warning_patterns = [
            r"WARN",
            r"WARNING",
            r"deprecated",
            r"timeout",
            r"failed to"
        ]
        
        performance_patterns = [
            r"can't keep up",
            r"server overloaded",
            r"tick took",
            r"memory usage",
            r"garbage collect"
        ]
        
        import re
        
        for line in log_lines:
            line_lower = line.lower()
            
            # Count errors and warnings
            for pattern in error_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    analysis["error_count"] += 1
                    if "critical" in line_lower or "fatal" in line_lower:
                        analysis["critical_issues"].append(line)
                    break
            
            for pattern in warning_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    analysis["warning_count"] += 1
                    break
            
            # Check for performance issues
            for pattern in performance_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    analysis["performance_issues"].append(line)
                    break
            
            # Check for player-related issues
            if any(keyword in line_lower for keyword in ["player", "kicked", "banned", "timeout"]):
                if any(issue in line_lower for issue in ["kicked", "banned", "timeout", "disconnect"]):
                    analysis["player_issues"].append(line)
        
        # Calculate severity
        if analysis["error_count"] > 10 or analysis["critical_issues"]:
            analysis["severity"] = "high"
        elif analysis["warning_count"] > 20 or analysis["performance_issues"]:
            analysis["severity"] = "medium"
        else:
            analysis["severity"] = "low"
        
        return {
            "success": True,
            "analysis": analysis
        }


class AlertTask(MonitoringTask):
    """Task to send alerts based on monitoring data."""
    
    def run(self, alert_type: str, message: str, severity: str = "info") -> Dict[str, Any]:
        """Send alert notification."""
        try:
            return asyncio.run(self._send_alert(alert_type, message, severity))
        except Exception as e:
            logger.error(f"Alert task failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_alert(self, alert_type: str, message: str, severity: str) -> Dict[str, Any]:
        """Send alert to all relevant connections."""
        try:
            container = get_container()
            ws_manager = await container.get_service(WebSocketManager)
            
            # Create notification message
            from ..websocket.models import create_notification_message
            
            notification = create_notification_message(
                title=f"System Alert - {alert_type.title()}",
                message=message,
                level=severity,
                duration=30 if severity == "error" else 10
            )
            
            # Broadcast to all connections
            await ws_manager.broadcast_to_all(notification)
            
            logger.info(f"Alert sent: {alert_type} - {message} (severity: {severity})")
            
            return {
                "success": True,
                "alert_type": alert_type,
                "message": message,
                "severity": severity,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            raise


# Task registration
performance_monitoring_task = PerformanceMonitoringTask()
system_health_check_task = SystemHealthCheckTask()
dashboard_update_task = DashboardUpdateTask()
log_analysis_task = LogAnalysisTask()
alert_task = AlertTask()