"""
Base task classes and utilities.
"""

import logging
from typing import Any, Dict, Optional
from celery import Task
from celery.exceptions import Retry

logger = logging.getLogger(__name__)


class BaseTask(Task):
    """Base task class for all Celery tasks."""
    
    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: Dict[str, Any]) -> None:
        """Called on task success."""
        logger.info(f"Task {self.name} ({task_id}) completed successfully")
    
    def on_failure(
        self, 
        exc: Exception, 
        task_id: str, 
        args: tuple, 
        kwargs: Dict[str, Any], 
        einfo: Any
    ) -> None:
        """Called on task failure."""
        logger.error(f"Task {self.name} ({task_id}) failed: {exc}")


class CallbackTask(BaseTask):
    """Base task class with callback support."""
    
    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: Dict[str, Any]) -> None:
        """Called on task success."""
        logger.info(f"Task {self.name} ({task_id}) completed successfully")
    
    def on_failure(
        self, 
        exc: Exception, 
        task_id: str, 
        args: tuple, 
        kwargs: Dict[str, Any], 
        einfo: Any
    ) -> None:
        """Called on task failure."""
        logger.error(f"Task {self.name} ({task_id}) failed: {exc}")
    
    def on_retry(
        self, 
        exc: Exception, 
        task_id: str, 
        args: tuple, 
        kwargs: Dict[str, Any], 
        einfo: Any
    ) -> None:
        """Called on task retry."""
        logger.warning(f"Task {self.name} ({task_id}) retrying: {exc}")


class ProgressTask(CallbackTask):
    """Task class with progress tracking support."""
    
    def update_progress(self, current: int, total: int, message: str = "") -> None:
        """Update task progress."""
        progress = {
            'current': current,
            'total': total,
            'percent': int((current / total) * 100) if total > 0 else 0,
            'message': message
        }
        
        self.update_state(
            state='PROGRESS',
            meta=progress
        )
        
        logger.debug(f"Task {self.name} progress: {progress['percent']}% - {message}")


def task_with_retry(
    max_retries: int = 3,
    default_retry_delay: int = 60,
    autoretry_for: tuple = (Exception,)
):
    """Decorator for tasks with retry configuration."""
    def decorator(func):
        func.max_retries = max_retries
        func.default_retry_delay = default_retry_delay
        func.autoretry_for = autoretry_for
        return func
    return decorator


def log_task_execution(func):
    """Decorator for logging task execution."""
    def wrapper(self, *args, **kwargs):
        task_id = self.request.id
        logger.info(f"Starting task {func.__name__} ({task_id}) with args={args}, kwargs={kwargs}")
        
        try:
            result = func(self, *args, **kwargs)
            logger.info(f"Task {func.__name__} ({task_id}) completed successfully")
            return result
        except Exception as e:
            logger.error(f"Task {func.__name__} ({task_id}) failed: {e}")
            raise
    
    return wrapper