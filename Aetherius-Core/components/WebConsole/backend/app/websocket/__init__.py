"""
WebSocket management for WebConsole backend.
"""

from .manager import WebSocketManager, ConnectionType
from .models import WSMessage, WSMessageType

__all__ = [
    "WebSocketManager",
    "ConnectionType",
    "WSMessage",
    "WSMessageType"
]