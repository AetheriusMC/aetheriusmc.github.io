"""
WebSocket endpoints for real-time communication.
"""

from .console import console_handler
from .monitoring import monitoring_handler
from .notifications import notification_handler

__all__ = [
    "console_handler",
    "monitoring_handler", 
    "notification_handler"
]