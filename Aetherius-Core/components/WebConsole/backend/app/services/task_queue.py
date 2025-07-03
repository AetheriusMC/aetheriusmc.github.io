"""
Task queue service implementation using Celery.
"""

import asyncio
from typing import Any, Dict, Optional, Callable, List
from datetime import datetime, timedelta
import logging
from abc import ABC, abstractmethod
from enum import Enum

from celery import Celery
from celery.result import AsyncResult
from kombu import Queue

from ..core.config import settings
from ..core.container import singleton

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


class TaskPriority(Enum):
    """Task priority enumeration."""
    LOW = 0
    NORMAL = 5
    HIGH = 10
    CRITICAL = 15


class TaskResult:
    """Task result wrapper."""
    
    def __init__(self, task_id: str, celery_result: AsyncResult):
        self.task_id = task_id
        self._celery_result = celery_result
    
    @property
    def status(self) -> TaskStatus:
        """Get task status."""
        return TaskStatus(self._celery_result.status)
    
    @property
    def result(self) -> Any:
        """Get task result."""
        return self._celery_result.result
    
    @property
    def traceback(self) -> Optional[str]:
        """Get task traceback if failed."""
        return self._celery_result.traceback
    
    @property
    def info(self) -> Dict[str, Any]:
        """Get task info."""
        return self._celery_result.info
    
    def ready(self) -> bool:
        """Check if task is ready."""
        return self._celery_result.ready()
    
    def successful(self) -> bool:
        """Check if task was successful."""
        return self._celery_result.successful()
    
    def failed(self) -> bool:
        """Check if task failed."""
        return self._celery_result.failed()
    
    def revoke(self, terminate: bool = False) -> None:
        """Revoke task."""
        self._celery_result.revoke(terminate=terminate)


class ITaskQueueService(ABC):
    """Task queue service interface."""
    
    @abstractmethod
    async def enqueue_task(
        self, 
        task_name: str, 
        args: tuple = (), 
        kwargs: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        eta: Optional[datetime] = None,
        countdown: Optional[int] = None
    ) -> TaskResult:
        """Enqueue a task."""
        pass
    
    @abstractmethod
    async def get_task_result(self, task_id: str) -> TaskResult:
        """Get task result."""
        pass
    
    @abstractmethod
    async def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get active tasks."""
        pass


@singleton
class TaskQueueService(ITaskQueueService):
    """Celery-based task queue service."""
    
    def __init__(self):
        self.celery_app: Optional[Celery] = None
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize Celery application."""
        try:
            # Create Celery app
            self.celery_app = Celery(
                'webconsole',
                broker=settings.redis.celery_broker_url,
                backend=settings.redis.celery_backend_url,
                include=['app.tasks']  # Import task modules
            )
            
            # Configure Celery
            self.celery_app.conf.update(
                # Task settings
                task_serializer='json',
                result_serializer='json',
                accept_content=['json'],
                result_expires=3600,
                timezone='UTC',
                enable_utc=True,
                
                # Worker settings
                worker_prefetch_multiplier=1,
                task_acks_late=True,
                worker_max_tasks_per_child=1000,
                
                # Queue routing
                task_routes={
                    'app.tasks.backup.*': {'queue': 'backup'},
                    'app.tasks.monitoring.*': {'queue': 'monitoring'},
                    'app.tasks.file.*': {'queue': 'file_ops'},
                    'app.tasks.player.*': {'queue': 'player_ops'},
                },
                
                # Queue definitions
                task_default_queue='default',
                task_queues=(
                    Queue('default', routing_key='default'),
                    Queue('backup', routing_key='backup'),
                    Queue('monitoring', routing_key='monitoring'),
                    Queue('file_ops', routing_key='file_ops'),
                    Queue('player_ops', routing_key='player_ops'),
                    Queue('high_priority', routing_key='high_priority'),
                ),
                
                # Retry settings
                task_default_retry_delay=60,
                task_max_retries=3,
                
                # Beat schedule (for periodic tasks)
                beat_schedule={
                    'cleanup-old-logs': {
                        'task': 'app.tasks.maintenance.cleanup_old_logs',
                        'schedule': timedelta(hours=24),
                    },
                    'backup-check': {
                        'task': 'app.tasks.backup.check_backup_schedule',
                        'schedule': timedelta(hours=1),
                    },
                    'system-health-check': {
                        'task': 'app.tasks.monitoring.system_health_check',
                        'schedule': timedelta(minutes=5),
                    },
                },
            )
            
            self.initialized = True
            logger.info("Task queue service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize task queue service: {e}")
            raise
    
    async def dispose(self) -> None:
        """Dispose task queue service."""
        if self.celery_app:
            self.celery_app.close()
        self.initialized = False
        logger.info("Task queue service disposed")
    
    async def enqueue_task(
        self, 
        task_name: str, 
        args: tuple = (), 
        kwargs: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        eta: Optional[datetime] = None,
        countdown: Optional[int] = None,
        retry: bool = True,
        retry_policy: Optional[Dict[str, Any]] = None
    ) -> TaskResult:
        """Enqueue a task."""
        if not self.initialized:
            raise RuntimeError("Task queue service not initialized")
        
        kwargs = kwargs or {}
        
        try:
            # Determine queue based on priority
            queue = self._get_queue_for_priority(priority)
            
            # Prepare task options
            task_options = {
                'queue': queue,
                'priority': priority.value,
                'retry': retry,
            }
            
            if eta:
                task_options['eta'] = eta
            elif countdown:
                task_options['countdown'] = countdown
            
            if retry_policy:
                task_options['retry_policy'] = retry_policy
            
            # Send task
            celery_result = self.celery_app.send_task(
                task_name,
                args=args,
                kwargs=kwargs,
                **task_options
            )
            
            logger.info(f"Task enqueued: {task_name} with ID {celery_result.id}")
            return TaskResult(celery_result.id, celery_result)
            
        except Exception as e:
            logger.error(f"Failed to enqueue task {task_name}: {e}")
            raise
    
    async def get_task_result(self, task_id: str) -> TaskResult:
        """Get task result."""
        if not self.initialized:
            raise RuntimeError("Task queue service not initialized")
        
        celery_result = AsyncResult(task_id, app=self.celery_app)
        return TaskResult(task_id, celery_result)
    
    async def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get active tasks."""
        if not self.initialized:
            return []
        
        try:
            inspect = self.celery_app.control.inspect()
            active_tasks = inspect.active()
            
            if not active_tasks:
                return []
            
            # Flatten tasks from all workers
            all_tasks = []
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    task['worker'] = worker
                    all_tasks.append(task)
            
            return all_tasks
            
        except Exception as e:
            logger.error(f"Failed to get active tasks: {e}")
            return []
    
    async def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """Get scheduled tasks."""
        if not self.initialized:
            return []
        
        try:
            inspect = self.celery_app.control.inspect()
            scheduled_tasks = inspect.scheduled()
            
            if not scheduled_tasks:
                return []
            
            # Flatten tasks from all workers
            all_tasks = []
            for worker, tasks in scheduled_tasks.items():
                for task in tasks:
                    task['worker'] = worker
                    all_tasks.append(task)
            
            return all_tasks
            
        except Exception as e:
            logger.error(f"Failed to get scheduled tasks: {e}")
            return []
    
    async def revoke_task(self, task_id: str, terminate: bool = False) -> bool:
        """Revoke a task."""
        if not self.initialized:
            return False
        
        try:
            self.celery_app.control.revoke(task_id, terminate=terminate)
            logger.info(f"Task {task_id} revoked (terminate={terminate})")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke task {task_id}: {e}")
            return False
    
    async def purge_queue(self, queue_name: str = 'default') -> int:
        """Purge a queue."""
        if not self.initialized:
            return 0
        
        try:
            result = self.celery_app.control.purge()
            purged_count = sum(result.values()) if result else 0
            logger.info(f"Purged {purged_count} tasks from queue {queue_name}")
            return purged_count
        except Exception as e:
            logger.error(f"Failed to purge queue {queue_name}: {e}")
            return 0
    
    async def get_worker_stats(self) -> Dict[str, Any]:
        """Get worker statistics."""
        if not self.initialized:
            return {}
        
        try:
            inspect = self.celery_app.control.inspect()
            stats = inspect.stats()
            return stats or {}
        except Exception as e:
            logger.error(f"Failed to get worker stats: {e}")
            return {}
    
    def _get_queue_for_priority(self, priority: TaskPriority) -> str:
        """Get queue name based on priority."""
        if priority == TaskPriority.CRITICAL:
            return 'high_priority'
        return 'default'
    
    # Convenience methods for common task types
    async def enqueue_backup_task(
        self, 
        backup_type: str, 
        include_worlds: bool = True,
        include_plugins: bool = True
    ) -> TaskResult:
        """Enqueue backup task."""
        return await self.enqueue_task(
            'app.tasks.backup.create_backup',
            kwargs={
                'backup_type': backup_type,
                'include_worlds': include_worlds,
                'include_plugins': include_plugins
            },
            priority=TaskPriority.HIGH
        )
    
    async def enqueue_player_operation(
        self, 
        operation: str, 
        player_uuid: str, 
        **kwargs
    ) -> TaskResult:
        """Enqueue player operation task."""
        return await self.enqueue_task(
            'app.tasks.player.player_operation',
            kwargs={
                'operation': operation,
                'player_uuid': player_uuid,
                **kwargs
            },
            priority=TaskPriority.NORMAL
        )
    
    async def enqueue_file_operation(
        self, 
        operation: str, 
        file_path: str, 
        **kwargs
    ) -> TaskResult:
        """Enqueue file operation task."""
        return await self.enqueue_task(
            'app.tasks.file.file_operation',
            kwargs={
                'operation': operation,
                'file_path': file_path,
                **kwargs
            },
            priority=TaskPriority.NORMAL
        )
    
    async def enqueue_monitoring_task(
        self, 
        metric_type: str, 
        **kwargs
    ) -> TaskResult:
        """Enqueue monitoring task."""
        return await self.enqueue_task(
            'app.tasks.monitoring.collect_metrics',
            kwargs={
                'metric_type': metric_type,
                **kwargs
            },
            priority=TaskPriority.LOW
        )