"""
Celery tasks for WebConsole backend.
"""

# Import actual functions from backup.py
from .backup import create_backup, restore_backup, cleanup_old_backups, check_backup_schedule

# Import base classes and utilities from base.py
from .base import BaseTask, CallbackTask, ProgressTask, task_with_retry, log_task_execution

# Import task instances from file.py
from .file import (
    file_cleanup_task,
    file_archive_task,
    file_extract_task,
    file_sync_task,
    file_validation_task
)

# Import task instances from maintenance.py
from .maintenance import (
    system_maintenance_task,
    database_maintenance_task,
    plugin_maintenance_task,
    scheduled_maintenance_task
)

# Import task instances from monitoring.py
from .monitoring import (
    performance_monitoring_task,
    system_health_check_task,
    dashboard_update_task,
    log_analysis_task,
    alert_task
)

# Import task instances from player.py
from .player import (
    player_activity_tracking_task,
    player_notification_task,
    player_behavior_analysis_task,
    player_moderation_task,
    player_data_sync_task,
    player_session_analysis_task
)

__all__ = [
    # Backup functions
    "create_backup",
    "restore_backup",
    "cleanup_old_backups",
    "check_backup_schedule",
    
    # Base classes and utilities
    "BaseTask",
    "CallbackTask", 
    "ProgressTask",
    "task_with_retry",
    "log_task_execution",
    
    # File task instances
    "file_cleanup_task",
    "file_archive_task",
    "file_extract_task",
    "file_sync_task",
    "file_validation_task",
    
    # Maintenance task instances
    "system_maintenance_task",
    "database_maintenance_task",
    "plugin_maintenance_task",
    "scheduled_maintenance_task",
    
    # Monitoring task instances
    "performance_monitoring_task",
    "system_health_check_task",
    "dashboard_update_task",
    "log_analysis_task",
    "alert_task",
    
    # Player task instances
    "player_activity_tracking_task",
    "player_notification_task",
    "player_behavior_analysis_task",
    "player_moderation_task",
    "player_data_sync_task",
    "player_session_analysis_task"
]