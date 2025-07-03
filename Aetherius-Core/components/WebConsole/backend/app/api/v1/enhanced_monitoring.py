"""
Enhanced monitoring API endpoints for multi-dimensional performance tracking.
Implements advanced dashboard features with real-time metrics and alerting.
"""

import logging
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field

from ...core.container import get_container
from ...core.aetherius_adapter import IAetheriusAdapter
from ...utils.security import get_current_user, require_permission
from ...websocket.manager import WebSocketManager
from ...websocket.models import create_notification_message

logger = logging.getLogger(__name__)

router = APIRouter()


# Enhanced Models for Multi-dimensional Monitoring
class SystemResourceMetrics(BaseModel):
    """System resource metrics with detailed breakdown."""
    timestamp: str = Field(..., description="Metrics timestamp")
    cpu: Dict[str, Any] = Field(..., description="CPU metrics")
    memory: Dict[str, Any] = Field(..., description="Memory metrics")
    disk: Dict[str, Any] = Field(..., description="Disk metrics")
    network: Dict[str, Any] = Field(..., description="Network metrics")
    processes: Dict[str, Any] = Field(..., description="Process metrics")


class JavaVMMetrics(BaseModel):
    """Java Virtual Machine performance metrics."""
    timestamp: str = Field(..., description="Metrics timestamp")
    heap_memory: Dict[str, Any] = Field(..., description="Heap memory usage")
    non_heap_memory: Dict[str, Any] = Field(..., description="Non-heap memory usage")
    garbage_collection: Dict[str, Any] = Field(..., description="GC statistics")
    thread_info: Dict[str, Any] = Field(..., description="Thread information")
    class_loading: Dict[str, Any] = Field(..., description="Class loading stats")


class MinecraftServerMetrics(BaseModel):
    """Minecraft server specific metrics."""
    timestamp: str = Field(..., description="Metrics timestamp")
    tps: float = Field(..., description="Ticks per second")
    mspt: float = Field(..., description="Milliseconds per tick")
    online_players: int = Field(..., description="Online players count")
    max_players: int = Field(..., description="Maximum players")
    world_stats: Dict[str, Any] = Field(..., description="World statistics")
    plugin_stats: Dict[str, Any] = Field(..., description="Plugin statistics")
    chunk_stats: Dict[str, Any] = Field(..., description="Chunk loading stats")


class PerformanceBaseline(BaseModel):
    """Performance baseline configuration."""
    metric_name: str = Field(..., description="Metric name")
    baseline_value: float = Field(..., description="Expected baseline value")
    tolerance_percent: float = Field(default=10.0, description="Tolerance percentage")
    measurement_window: int = Field(default=300, description="Measurement window in seconds")
    enabled: bool = Field(default=True, description="Baseline monitoring enabled")


class AlertRule(BaseModel):
    """Enhanced alert rule configuration."""
    id: Optional[str] = Field(None, description="Rule ID")
    name: str = Field(..., description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    metric_name: str = Field(..., description="Metric to monitor")
    operator: str = Field(..., description="Comparison operator")
    threshold: float = Field(..., description="Alert threshold")
    duration: int = Field(default=60, description="Duration before triggering")
    severity: str = Field(default="warning", description="Alert severity")
    enabled: bool = Field(default=True, description="Rule enabled status")
    notification_channels: List[str] = Field(default=[], description="Notification channels")
    cooldown_seconds: int = Field(default=300, description="Cooldown between alerts")


class DashboardWidget(BaseModel):
    """Dashboard widget configuration."""
    id: str = Field(..., description="Widget ID")
    type: str = Field(..., description="Widget type")
    title: str = Field(..., description="Widget title")
    position: Dict[str, int] = Field(..., description="Widget position")
    size: Dict[str, int] = Field(..., description="Widget size")
    config: Dict[str, Any] = Field(..., description="Widget configuration")
    enabled: bool = Field(default=True, description="Widget enabled status")


class DashboardLayout(BaseModel):
    """Dashboard layout configuration."""
    user_id: str = Field(..., description="User ID")
    layout_name: str = Field(..., description="Layout name")
    widgets: List[DashboardWidget] = Field(..., description="Dashboard widgets")
    refresh_interval: int = Field(default=30, description="Refresh interval in seconds")
    theme: str = Field(default="auto", description="Dashboard theme")


# Dependency functions
async def get_aetherius_adapter() -> IAetheriusAdapter:
    """Get Aetherius adapter instance."""
    container = get_container()
    return await container.get_service(IAetheriusAdapter)


async def get_websocket_manager() -> WebSocketManager:
    """Get WebSocket manager instance."""
    container = get_container()
    return await container.get_service(WebSocketManager)


@router.get("/metrics/system", response_model=SystemResourceMetrics)
async def get_system_resource_metrics(
    current_user: Dict[str, Any] = Depends(require_permission("server.monitor"))
):
    """
    获取详细的系统资源指标。
    
    返回 CPU、内存、磁盘、网络等系统级别的详细监控数据。
    需要 'server.monitor' 权限。
    """
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        cpu_freq = psutil.cpu_freq()
        cpu_stats = psutil.cpu_stats()
        
        cpu_metrics = {
            "usage_percent": psutil.cpu_percent(interval=1),
            "usage_per_core": cpu_percent,
            "core_count": psutil.cpu_count(logical=False),
            "logical_count": psutil.cpu_count(logical=True),
            "frequency": {
                "current": cpu_freq.current if cpu_freq else 0,
                "min": cpu_freq.min if cpu_freq else 0,
                "max": cpu_freq.max if cpu_freq else 0
            },
            "stats": {
                "ctx_switches": cpu_stats.ctx_switches,
                "interrupts": cpu_stats.interrupts,
                "soft_interrupts": cpu_stats.soft_interrupts
            }
        }
        
        # Memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        memory_metrics = {
            "virtual": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "free": memory.free,
                "percent": memory.percent,
                "buffers": getattr(memory, 'buffers', 0),
                "cached": getattr(memory, 'cached', 0)
            },
            "swap": {
                "total": swap.total,
                "used": swap.used,
                "free": swap.free,
                "percent": swap.percent
            }
        }
        
        # Disk metrics
        disk_partitions = psutil.disk_partitions()
        disk_metrics = {
            "partitions": [],
            "io_stats": {}
        }
        
        for partition in disk_partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_metrics["partitions"].append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": (usage.used / usage.total) * 100
                })
            except PermissionError:
                continue
        
        # Disk I/O statistics
        try:
            disk_io = psutil.disk_io_counters()
            if disk_io:
                disk_metrics["io_stats"] = {
                    "read_count": disk_io.read_count,
                    "write_count": disk_io.write_count,
                    "read_bytes": disk_io.read_bytes,
                    "write_bytes": disk_io.write_bytes,
                    "read_time": disk_io.read_time,
                    "write_time": disk_io.write_time
                }
        except Exception:
            disk_metrics["io_stats"] = {}
        
        # Network metrics
        network_stats = psutil.net_io_counters()
        network_connections = len(psutil.net_connections())
        
        network_metrics = {
            "interfaces": {},
            "connections": network_connections,
            "total_stats": {
                "bytes_sent": network_stats.bytes_sent,
                "bytes_recv": network_stats.bytes_recv,
                "packets_sent": network_stats.packets_sent,
                "packets_recv": network_stats.packets_recv,
                "errin": network_stats.errin,
                "errout": network_stats.errout,
                "dropin": network_stats.dropin,
                "dropout": network_stats.dropout
            }
        }
        
        # Per-interface network stats
        try:
            net_io_per_nic = psutil.net_io_counters(pernic=True)
            for interface, stats in net_io_per_nic.items():
                network_metrics["interfaces"][interface] = {
                    "bytes_sent": stats.bytes_sent,
                    "bytes_recv": stats.bytes_recv,
                    "packets_sent": stats.packets_sent,
                    "packets_recv": stats.packets_recv
                }
        except Exception:
            pass
        
        # Process metrics
        processes = list(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']))
        java_processes = [p for p in processes if 'java' in p.info['name'].lower()]
        
        process_metrics = {
            "total_count": len(processes),
            "java_processes": len(java_processes),
            "top_cpu": sorted(processes, key=lambda x: x.info['cpu_percent'] or 0, reverse=True)[:5],
            "top_memory": sorted(processes, key=lambda x: x.info['memory_percent'] or 0, reverse=True)[:5]
        }
        
        return SystemResourceMetrics(
            timestamp=datetime.now().isoformat(),
            cpu=cpu_metrics,
            memory=memory_metrics,
            disk=disk_metrics,
            network=network_metrics,
            processes=process_metrics
        )
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统指标失败: {str(e)}")


@router.get("/metrics/jvm", response_model=JavaVMMetrics)
async def get_jvm_metrics(
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    current_user: Dict[str, Any] = Depends(require_permission("server.monitor"))
):
    """
    获取Java虚拟机性能指标。
    
    返回JVM堆内存、垃圾回收、线程等详细信息。
    需要 'server.monitor' 权限。
    """
    try:
        # TODO: Get actual JVM metrics from Aetherius Core
        # For now, return mock data with realistic values
        
        import random
        
        # Mock heap memory data
        heap_max = 4096 * 1024 * 1024  # 4GB
        heap_used = random.uniform(1024 * 1024 * 1024, 3072 * 1024 * 1024)  # 1-3GB
        
        heap_memory = {
            "max": heap_max,
            "used": heap_used,
            "committed": heap_max * 0.8,
            "available": heap_max - heap_used,
            "percent": (heap_used / heap_max) * 100,
            "regions": {
                "eden": {"used": heap_used * 0.4, "max": heap_max * 0.6},
                "survivor": {"used": heap_used * 0.1, "max": heap_max * 0.1},
                "old_gen": {"used": heap_used * 0.5, "max": heap_max * 0.8}
            }
        }
        
        # Mock non-heap memory
        non_heap_memory = {
            "metaspace": {"used": 128 * 1024 * 1024, "max": 256 * 1024 * 1024},
            "code_cache": {"used": 32 * 1024 * 1024, "max": 64 * 1024 * 1024},
            "compressed_class": {"used": 16 * 1024 * 1024, "max": 32 * 1024 * 1024}
        }
        
        # Mock GC statistics
        garbage_collection = {
            "collectors": {
                "G1_Young": {
                    "collections": random.randint(100, 1000),
                    "collection_time": random.randint(500, 5000),
                    "avg_time": random.uniform(5.0, 50.0)
                },
                "G1_Old": {
                    "collections": random.randint(5, 50),
                    "collection_time": random.randint(100, 1000),
                    "avg_time": random.uniform(20.0, 200.0)
                }
            },
            "total_collections": random.randint(105, 1050),
            "total_time": random.randint(600, 6000),
            "gc_overhead": random.uniform(2.0, 8.0)
        }
        
        # Mock thread information
        thread_info = {
            "active_count": random.randint(20, 80),
            "daemon_count": random.randint(15, 25),
            "peak_count": random.randint(50, 100),
            "started_count": random.randint(200, 1000),
            "deadlocked": 0,
            "states": {
                "runnable": random.randint(5, 15),
                "blocked": random.randint(0, 5),
                "waiting": random.randint(10, 30),
                "timed_waiting": random.randint(5, 20)
            }
        }
        
        # Mock class loading
        class_loading = {
            "loaded_count": random.randint(5000, 15000),
            "unloaded_count": random.randint(100, 1000),
            "total_loaded": random.randint(10000, 50000)
        }
        
        return JavaVMMetrics(
            timestamp=datetime.now().isoformat(),
            heap_memory=heap_memory,
            non_heap_memory=non_heap_memory,
            garbage_collection=garbage_collection,
            thread_info=thread_info,
            class_loading=class_loading
        )
        
    except Exception as e:
        logger.error(f"Failed to get JVM metrics: {e}")
        raise HTTPException(status_code=500, detail=f"获取JVM指标失败: {str(e)}")


@router.get("/metrics/minecraft", response_model=MinecraftServerMetrics)
async def get_minecraft_metrics(
    adapter: IAetheriusAdapter = Depends(get_aetherius_adapter),
    current_user: Dict[str, Any] = Depends(require_permission("server.monitor"))
):
    """
    获取Minecraft服务器特定指标。
    
    返回TPS、玩家数、世界统计等游戏相关监控数据。
    需要 'server.monitor' 权限。
    """
    try:
        # Get basic server data
        server_status = await adapter.get_server_status()
        performance_data = await adapter.get_performance_data()
        online_players = await adapter.get_online_players()
        
        # TODO: Get detailed Minecraft metrics from Aetherius Core
        # For now, enhance with mock detailed data
        
        import random
        
        world_stats = {
            "worlds": {
                "world": {
                    "chunks_loaded": random.randint(500, 2000),
                    "entities": random.randint(100, 1000),
                    "tile_entities": random.randint(50, 500),
                    "players": len([p for p in online_players if p.get("world") == "world"])
                },
                "world_nether": {
                    "chunks_loaded": random.randint(50, 200),
                    "entities": random.randint(10, 100),
                    "tile_entities": random.randint(5, 50),
                    "players": len([p for p in online_players if p.get("world") == "world_nether"])
                },
                "world_the_end": {
                    "chunks_loaded": random.randint(10, 100),
                    "entities": random.randint(5, 50),
                    "tile_entities": random.randint(1, 10),
                    "players": len([p for p in online_players if p.get("world") == "world_the_end"])
                }
            },
            "total_chunks": random.randint(600, 2500),
            "total_entities": random.randint(150, 1200)
        }
        
        plugin_stats = {
            "enabled_count": random.randint(10, 30),
            "disabled_count": random.randint(0, 5),
            "plugins": [
                {"name": "EssentialsX", "enabled": True, "version": "2.19.0"},
                {"name": "WorldEdit", "enabled": True, "version": "7.2.0"},
                {"name": "LuckPerms", "enabled": True, "version": "5.4.0"}
            ]
        }
        
        chunk_stats = {
            "loading_rate": random.uniform(0.5, 5.0),
            "unloading_rate": random.uniform(0.2, 2.0),
            "generation_rate": random.uniform(0.1, 1.0),
            "cache_hit_rate": random.uniform(85.0, 95.0)
        }
        
        # Calculate MSPT from TPS
        tps = performance_data.get("tps", 20.0)
        mspt = (1000.0 / tps) if tps > 0 else 50.0
        
        return MinecraftServerMetrics(
            timestamp=datetime.now().isoformat(),
            tps=tps,
            mspt=mspt,
            online_players=len(online_players),
            max_players=server_status.get("max_players", 20),
            world_stats=world_stats,
            plugin_stats=plugin_stats,
            chunk_stats=chunk_stats
        )
        
    except Exception as e:
        logger.error(f"Failed to get Minecraft metrics: {e}")
        raise HTTPException(status_code=500, detail=f"获取Minecraft指标失败: {str(e)}")


@router.post("/dashboard/layout", response_model=Dict[str, Any])
async def save_dashboard_layout(
    layout: DashboardLayout,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    保存用户仪表板布局配置。
    
    允许用户自定义仪表板组件的位置和配置。
    """
    try:
        # TODO: Save layout to database
        # For now, just validate and return success
        
        # Validate user owns this layout
        if layout.user_id != str(current_user["id"]):
            raise HTTPException(status_code=403, detail="无权限修改此布局")
        
        # Validate widget configurations
        valid_widget_types = ["metric_chart", "server_status", "player_list", "resource_usage", "alerts"]
        for widget in layout.widgets:
            if widget.type not in valid_widget_types:
                raise HTTPException(status_code=400, detail=f"无效的组件类型: {widget.type}")
        
        logger.info(f"User {current_user['username']} saved dashboard layout: {layout.layout_name}")
        
        return {
            "success": True,
            "message": "仪表板布局已保存",
            "layout_name": layout.layout_name,
            "widget_count": len(layout.widgets),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to save dashboard layout: {e}")
        raise HTTPException(status_code=500, detail=f"保存布局失败: {str(e)}")


@router.get("/dashboard/layout/{layout_name}", response_model=DashboardLayout)
async def get_dashboard_layout(
    layout_name: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取用户仪表板布局配置。
    
    返回指定名称的仪表板布局配置。
    """
    try:
        # TODO: Load layout from database
        # For now, return a default layout
        
        default_widgets = [
            DashboardWidget(
                id="server_status",
                type="server_status",
                title="服务器状态",
                position={"x": 0, "y": 0},
                size={"width": 6, "height": 4},
                config={"show_uptime": True, "show_players": True}
            ),
            DashboardWidget(
                id="cpu_chart",
                type="metric_chart",
                title="CPU使用率",
                position={"x": 6, "y": 0},
                size={"width": 6, "height": 4},
                config={"metric": "cpu_percent", "chart_type": "line", "timeframe": "1h"}
            ),
            DashboardWidget(
                id="memory_chart",
                type="metric_chart", 
                title="内存使用",
                position={"x": 0, "y": 4},
                size={"width": 6, "height": 4},
                config={"metric": "memory_percent", "chart_type": "area", "timeframe": "1h"}
            ),
            DashboardWidget(
                id="tps_chart",
                type="metric_chart",
                title="TPS监控",
                position={"x": 6, "y": 4},
                size={"width": 6, "height": 4},
                config={"metric": "tps", "chart_type": "line", "timeframe": "30m"}
            )
        ]
        
        return DashboardLayout(
            user_id=str(current_user["id"]),
            layout_name=layout_name,
            widgets=default_widgets,
            refresh_interval=30,
            theme="auto"
        )
        
    except Exception as e:
        logger.error(f"Failed to get dashboard layout: {e}")
        raise HTTPException(status_code=500, detail=f"获取布局失败: {str(e)}")


@router.post("/alerts/rules", response_model=Dict[str, Any])
async def create_alert_rule(
    rule: AlertRule,
    background_tasks: BackgroundTasks,
    ws_manager: WebSocketManager = Depends(get_websocket_manager),
    current_user: Dict[str, Any] = Depends(require_permission("server.alert"))
):
    """
    创建新的警报规则。
    
    需要 'server.alert' 权限。创建基于指标的自动警报规则。
    """
    try:
        # TODO: Save alert rule to database
        # For now, validate and return success
        
        # Validate operator
        valid_operators = [">", "<", ">=", "<=", "==", "!="]
        if rule.operator not in valid_operators:
            raise HTTPException(status_code=400, detail=f"无效的操作符: {rule.operator}")
        
        # Validate severity
        valid_severities = ["info", "warning", "error", "critical"]
        if rule.severity not in valid_severities:
            raise HTTPException(status_code=400, detail=f"无效的严重级别: {rule.severity}")
        
        # Generate rule ID
        import uuid
        rule_id = str(uuid.uuid4())
        
        logger.info(f"User {current_user['username']} created alert rule: {rule.name}")
        
        # Send notification
        notification = create_notification_message(
            title="警报规则已创建",
            message=f"警报规则 '{rule.name}' 已成功创建",
            level="success"
        )
        await ws_manager.broadcast_to_user(str(current_user["id"]), notification)
        
        return {
            "success": True,
            "rule_id": rule_id,
            "message": "警报规则已创建",
            "rule_name": rule.name,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to create alert rule: {e}")
        raise HTTPException(status_code=500, detail=f"创建警报规则失败: {str(e)}")


@router.get("/performance/baseline", response_model=List[PerformanceBaseline])
async def get_performance_baselines(
    current_user: Dict[str, Any] = Depends(require_permission("server.monitor"))
):
    """
    获取性能基线配置。
    
    返回系统性能基线设置，用于异常检测。
    需要 'server.monitor' 权限。
    """
    try:
        # TODO: Load baselines from database
        # For now, return default baselines
        
        default_baselines = [
            PerformanceBaseline(
                metric_name="cpu_percent",
                baseline_value=40.0,
                tolerance_percent=15.0,
                measurement_window=300,
                enabled=True
            ),
            PerformanceBaseline(
                metric_name="memory_percent",
                baseline_value=60.0,
                tolerance_percent=10.0,
                measurement_window=600,
                enabled=True
            ),
            PerformanceBaseline(
                metric_name="tps",
                baseline_value=19.5,
                tolerance_percent=5.0,
                measurement_window=180,
                enabled=True
            ),
            PerformanceBaseline(
                metric_name="mspt",
                baseline_value=45.0,
                tolerance_percent=20.0,
                measurement_window=300,
                enabled=True
            )
        ]
        
        return default_baselines
        
    except Exception as e:
        logger.error(f"Failed to get performance baselines: {e}")
        raise HTTPException(status_code=500, detail=f"获取性能基线失败: {str(e)}")


@router.post("/performance/analyze", response_model=Dict[str, Any])
async def analyze_performance_trends(
    background_tasks: BackgroundTasks,
    hours: int = Query(24, ge=1, le=168, description="Analysis period in hours"),
    current_user: Dict[str, Any] = Depends(require_permission("server.monitor"))
):
    """
    分析性能趋势和异常。
    
    基于历史数据分析性能模式，检测异常和趋势。
    需要 'server.monitor' 权限。
    """
    try:
        # TODO: Implement actual performance trend analysis
        # For now, return mock analysis results
        
        import random
        
        analysis_results = {
            "analysis_period": f"{hours} hours",
            "timestamp": datetime.now().isoformat(),
            "overall_health": random.choice(["excellent", "good", "fair", "poor"]),
            "trends": {
                "cpu_trend": random.choice(["stable", "increasing", "decreasing", "volatile"]),
                "memory_trend": random.choice(["stable", "increasing", "decreasing"]),
                "tps_trend": random.choice(["stable", "degrading", "improving"]),
                "player_activity": random.choice(["low", "moderate", "high", "peak"])
            },
            "anomalies": [
                {
                    "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "metric": "cpu_percent",
                    "value": 95.2,
                    "severity": "high",
                    "description": "CPU使用率异常高峰"
                },
                {
                    "timestamp": (datetime.now() - timedelta(hours=6)).isoformat(),
                    "metric": "tps",
                    "value": 12.5,
                    "severity": "medium",
                    "description": "TPS显著下降"
                }
            ],
            "recommendations": [
                "考虑在高峰时段增加服务器资源",
                "检查可能导致TPS下降的插件",
                "监控内存使用模式，防止内存泄漏"
            ],
            "statistics": {
                "avg_cpu": random.uniform(30.0, 60.0),
                "max_cpu": random.uniform(70.0, 95.0),
                "avg_memory": random.uniform(40.0, 80.0),
                "avg_tps": random.uniform(18.0, 20.0),
                "min_tps": random.uniform(10.0, 18.0)
            }
        }
        
        logger.info(f"User {current_user['username']} requested performance analysis for {hours} hours")
        
        return {
            "success": True,
            "analysis": analysis_results
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze performance: {e}")
        raise HTTPException(status_code=500, detail=f"性能分析失败: {str(e)}")