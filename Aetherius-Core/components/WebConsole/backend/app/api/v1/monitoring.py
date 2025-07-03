"""
Monitoring and dashboard API endpoints.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field

from ...core.container import get_container
from ...core.aetherius_adapter import IAetheriusAdapter
from ...utils.security import get_current_user, require_permission
from ...websocket.manager import WebSocketManager
from ...websocket.models import create_notification_message
from ...tasks.monitoring import (
    performance_monitoring_task, system_health_check_task,
    dashboard_update_task, log_analysis_task, alert_task
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class SystemMetrics(BaseModel):
    """System metrics model."""
    timestamp: str = Field(..., description="Metrics timestamp")
    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_mb: float = Field(..., description="Memory usage in MB")
    memory_percent: float = Field(..., description="Memory usage percentage")
    disk_usage_mb: float = Field(..., description="Disk usage in MB")
    disk_percent: float = Field(..., description="Disk usage percentage")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    load_average: List[float] = Field(..., description="System load average")


class ServerMetrics(BaseModel):
    """Server performance metrics model."""
    timestamp: str = Field(..., description="Metrics timestamp")
    tps: float = Field(..., description="Ticks per second")
    online_players: int = Field(..., description="Number of online players")
    max_players: int = Field(..., description="Maximum players")
    chunks_loaded: int = Field(..., description="Number of loaded chunks")
    entities_count: int = Field(..., description="Total entities count")
    memory_used_mb: float = Field(..., description="Server memory usage in MB")
    memory_max_mb: float = Field(..., description="Maximum server memory in MB")


class DashboardStats(BaseModel):
    """Dashboard statistics model."""
    server_status: str = Field(..., description="Server status")
    uptime: str = Field(..., description="Server uptime")
    online_players: int = Field(..., description="Online players count")
    max_players: int = Field(..., description="Maximum players")
    tps: float = Field(..., description="Current TPS")
    cpu_usage: float = Field(..., description="CPU usage percentage")
    memory_usage: float = Field(..., description="Memory usage percentage")
    disk_usage: float = Field(..., description="Disk usage percentage")
    recent_events: List[Dict[str, Any]] = Field(..., description="Recent server events")
    alerts: List[Dict[str, Any]] = Field(..., description="Active alerts")


class HealthCheckResult(BaseModel):
    """Health check result model."""
    timestamp: str = Field(..., description="Check timestamp")
    overall_status: str = Field(..., description="Overall health status")
    services: Dict[str, Dict[str, Any]] = Field(..., description="Service health status")
    recommendations: List[str] = Field(..., description="Health recommendations")


class AlertRule(BaseModel):
    """Alert rule configuration model."""
    name: str = Field(..., description="Alert rule name")
    metric: str = Field(..., description="Metric to monitor")
    operator: str = Field(..., description="Comparison operator (>, <, >=, <=, ==)")
    threshold: float = Field(..., description="Alert threshold value")
    duration: int = Field(default=60, description="Duration before triggering (seconds)")
    severity: str = Field(default="warning", description="Alert severity")
    enabled: bool = Field(default=True, description="Rule enabled status")


class MetricsQuery(BaseModel):
    """Metrics query parameters model."""
    metrics: List[str] = Field(..., description="Metrics to query")
    start_time: Optional[str] = Field(None, description="Start time (ISO format)")
    end_time: Optional[str] = Field(None, description="End time (ISO format)")
    interval: str = Field("5m", description="Data interval")
    aggregation: str = Field("avg", description="Aggregation method")


# Dependency to get Aetherius adapter
async def get_aetherius_adapter() -> IAetheriusAdapter:
    """Get Aetherius adapter instance."""
    container = get_container()
    return await container.get_service(IAetheriusAdapter)


# Dependency to get WebSocket manager
async def get_websocket_manager() -> WebSocketManager:
    """Get WebSocket manager instance."""
    container = get_container()
    return await container.get_service(WebSocketManager)


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取仪表板统计信息。
    
    返回服务器概览数据，包括状态、性能指标和最近事件。
    """
    try:
        # Get server status
        server_status = await adapter.get_server_status()
        
        # Get performance data  
        performance = await adapter.get_performance_data()
        
        # Get online players
        online_players = await adapter.get_online_players()
        
        # Calculate uptime string
        uptime_seconds = server_status.get("uptime", 0)
        uptime_str = _format_uptime(uptime_seconds)
        
        # Mock recent events (TODO: implement event history)
        recent_events = [
            {
                "timestamp": datetime.now().isoformat(),
                "type": "player_join",
                "message": "Player Steve joined the game",
                "severity": "info"
            },
            {
                "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
                "type": "server_start",
                "message": "Server started successfully",
                "severity": "success"
            }
        ]
        
        # Mock alerts (TODO: implement alert system)
        alerts = []
        if performance.get("cpu_percent", 0) > 80:
            alerts.append({
                "id": "high_cpu",
                "message": "高 CPU 使用率",
                "severity": "warning",
                "timestamp": datetime.now().isoformat()
            })
        
        return DashboardStats(
            server_status=server_status.get("status", "unknown"),
            uptime=uptime_str,
            online_players=len(online_players),
            max_players=server_status.get("max_players", 20),
            tps=performance.get("tps", 20.0),
            cpu_usage=performance.get("cpu_percent", 0.0),
            memory_usage=_calculate_memory_percentage(performance.get("memory_mb", 0)),
            disk_usage=50.0,  # TODO: implement disk usage monitoring
            recent_events=recent_events,
            alerts=alerts
        )
        
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"获取仪表板数据失败: {str(e)}")


@router.get("/metrics/system", response_model=SystemMetrics)
async def get_system_metrics(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取系统性能指标。
    
    返回 CPU、内存、磁盘使用情况等系统级指标。
    """
    try:
        # TODO: Implement actual system metrics collection using psutil
        # For now, return mock data
        
        import random
        
        return SystemMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=random.uniform(20.0, 80.0),
            memory_mb=random.uniform(1000.0, 3000.0),
            memory_percent=random.uniform(25.0, 75.0),
            disk_usage_mb=random.uniform(5000.0, 15000.0),
            disk_percent=random.uniform(40.0, 70.0),
            uptime_seconds=random.uniform(3600.0, 360000.0),
            load_average=[random.uniform(0.5, 2.0) for _ in range(3)]
        )
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统指标失败: {str(e)}")


@router.get("/metrics/server", response_model=ServerMetrics)
async def get_server_metrics(
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取服务器性能指标。
    
    返回 TPS、玩家数、内存使用等服务器特定指标。
    """
    try:
        # Get performance data from adapter
        performance = await adapter.get_performance_data()
        server_status = await adapter.get_server_status()
        online_players = await adapter.get_online_players()
        
        # TODO: Get additional server metrics like chunks, entities
        import random
        
        return ServerMetrics(
            timestamp=datetime.now().isoformat(),
            tps=performance.get("tps", 20.0),
            online_players=len(online_players),
            max_players=server_status.get("max_players", 20),
            chunks_loaded=random.randint(500, 2000),
            entities_count=random.randint(100, 1000),
            memory_used_mb=performance.get("memory_mb", 0.0),
            memory_max_mb=4096.0  # TODO: get from server configuration
        )
        
    except Exception as e:
        logger.error(f"Failed to get server metrics: {e}")
        raise HTTPException(status_code=500, detail=f"获取服务器指标失败: {str(e)}")


@router.get("/health", response_model=HealthCheckResult)
async def get_health_status(
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_permission("server.monitor"))
):
    """
    获取系统健康状态。
    
    需要 'server.monitor' 权限。执行全面的健康检查。
    """
    try:
        # Schedule health check task
        task_result = system_health_check_task.delay()
        
        # Wait for result (with timeout)
        result = task_result.get(timeout=30)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail="健康检查执行失败")
        
        health_data = result["health"]
        
        # Generate recommendations based on health status
        recommendations = []
        if health_data["overall_status"] != "healthy":
            recommendations.append("建议检查系统资源使用情况")
            
        for service, status in health_data["services"].items():
            if status["status"] != "healthy":
                recommendations.append(f"检查 {service} 服务状态")
        
        return HealthCheckResult(
            timestamp=health_data["timestamp"],
            overall_status=health_data["overall_status"],
            services=health_data["services"],
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Failed to get health status: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@router.post("/alerts", response_model=Dict[str, Any])
async def create_alert(
    alert_type: str,
    message: str,
    background_tasks: BackgroundTasks,
    severity: str = "info",
    ws_manager: WebSocketManager = Depends(get_websocket_manager),
    current_user: Dict[str, Any] = Depends(require_permission("server.alert"))
):
    """
    创建系统警报。
    
    需要 'server.alert' 权限。发送警报通知到所有连接。
    """
    try:
        # Schedule alert task
        task_result = alert_task.delay(
            alert_type=alert_type,
            message=message,
            severity=severity
        )
        
        # Wait for result
        result = task_result.get(timeout=10)
        
        logger.info(f"User {current_user['username']} created alert: {alert_type} - {message}")
        
        return {
            "success": result.get("success", False),
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to create alert: {e}")
        raise HTTPException(status_code=500, detail=f"创建警报失败: {str(e)}")


@router.post("/update", response_model=Dict[str, Any])
async def trigger_dashboard_update(
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    触发仪表板数据更新。
    
    强制刷新仪表板数据并广播更新。
    """
    try:
        # Schedule dashboard update task
        task_result = dashboard_update_task.delay()
        
        logger.info(f"User {current_user['username']} triggered dashboard update")
        
        return {
            "success": True,
            "message": "仪表板更新已触发",
            "task_id": task_result.id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger dashboard update: {e}")
        raise HTTPException(status_code=500, detail=f"仪表板更新失败: {str(e)}")


@router.post("/metrics/query", response_model=Dict[str, Any])
async def query_metrics(
    query: MetricsQuery,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    查询历史性能指标。
    
    支持自定义时间范围和聚合方式的指标查询。
    """
    try:
        # TODO: Implement time-series metrics query
        # For now, return mock data
        
        import random
        from datetime import datetime, timedelta
        
        # Generate mock time series data
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()
        
        data_points = []
        current_time = start_time
        
        while current_time <= end_time:
            point = {
                "timestamp": current_time.isoformat(),
            }
            
            for metric in query.metrics:
                if metric == "cpu_percent":
                    point[metric] = random.uniform(20.0, 80.0)
                elif metric == "memory_mb":
                    point[metric] = random.uniform(1000.0, 3000.0)
                elif metric == "tps":
                    point[metric] = random.uniform(18.0, 20.0)
                else:
                    point[metric] = random.uniform(0.0, 100.0)
            
            data_points.append(point)
            current_time += timedelta(minutes=5)
        
        return {
            "success": True,
            "query": query.dict(),
            "data": data_points,
            "count": len(data_points),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to query metrics: {e}")
        raise HTTPException(status_code=500, detail=f"指标查询失败: {str(e)}")


@router.get("/logs/analysis", response_model=Dict[str, Any])
async def get_log_analysis(
    background_tasks: BackgroundTasks,
    hours: int = Query(24, ge=1, le=168, description="Analysis period in hours"),
    current_user: Dict[str, Any] = Depends(require_permission("server.monitor"))
):
    """
    获取日志分析报告。
    
    需要 'server.monitor' 权限。分析指定时间段内的服务器日志。
    """
    try:
        # TODO: Get actual log lines from log files
        # For now, use mock log data
        mock_log_lines = [
            "[INFO] Server started successfully",
            "[WARN] Can't keep up! Did the system time change?",
            "[ERROR] Failed to save player data",
            "[INFO] Player Steve joined the game",
            "[DEBUG] Chunk loading completed"
        ] * 100  # Simulate 500 log lines
        
        # Schedule log analysis task
        task_result = log_analysis_task.delay(mock_log_lines)
        
        # Wait for result
        result = task_result.get(timeout=30)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail="日志分析执行失败")
        
        return {
            "success": True,
            "analysis_period_hours": hours,
            "analysis": result["analysis"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze logs: {e}")
        raise HTTPException(status_code=500, detail=f"日志分析失败: {str(e)}")


@router.get("/events", response_model=Dict[str, Any])
async def get_recent_events(
    limit: int = Query(50, ge=1, le=500, description="Number of events to return"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取最近的服务器事件。
    
    返回最近发生的服务器事件列表，支持类型筛选。
    """
    try:
        # TODO: Implement actual event retrieval from database
        # For now, return mock events
        
        mock_events = []
        event_types = ["player_join", "player_leave", "server_start", "server_stop", "error", "warning"]
        
        for i in range(limit):
            event = {
                "id": i + 1,
                "timestamp": (datetime.now() - timedelta(minutes=i*2)).isoformat(),
                "type": random.choice(event_types),
                "message": f"Mock event message {i + 1}",
                "severity": random.choice(["info", "warning", "error", "success"]),
                "source": "server"
            }
            
            # Apply type filter
            if not event_type or event["type"] == event_type:
                mock_events.append(event)
        
        # Limit results
        mock_events = mock_events[:limit]
        
        return {
            "success": True,
            "events": mock_events,
            "total_count": len(mock_events),
            "filter": {"event_type": event_type, "limit": limit},
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent events: {e}")
        raise HTTPException(status_code=500, detail=f"获取事件列表失败: {str(e)}")


# Helper functions
def _format_uptime(uptime_seconds: int) -> str:
    """Format uptime seconds to human readable string."""
    if uptime_seconds < 60:
        return f"{uptime_seconds}秒"
    elif uptime_seconds < 3600:
        minutes = uptime_seconds // 60
        return f"{minutes}分钟"
    elif uptime_seconds < 86400:
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        return f"{hours}小时{minutes}分钟"
    else:
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        return f"{days}天{hours}小时"


def _calculate_memory_percentage(memory_mb: float, max_memory_mb: float = 4096.0) -> float:
    """Calculate memory usage percentage."""
    return (memory_mb / max_memory_mb) * 100.0 if max_memory_mb > 0 else 0.0