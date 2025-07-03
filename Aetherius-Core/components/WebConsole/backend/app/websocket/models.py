"""
WebSocket message models and types.
"""

from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class WSMessageType(str, Enum):
    """WebSocket message types."""
    
    # Connection management
    PING = "ping"
    PONG = "pong"
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    
    # Console messages
    CONSOLE_LOG = "console_log"
    CONSOLE_COMMAND = "console_command"
    CONSOLE_COMMAND_RESULT = "console_command_result"
    
    # Server status
    SERVER_STATUS = "server_status"
    PERFORMANCE_UPDATE = "performance_update"
    
    # Player events
    PLAYER_JOIN = "player_join"
    PLAYER_LEAVE = "player_leave"
    PLAYER_CHAT = "player_chat"
    PLAYER_LIST_UPDATE = "player_list_update"
    
    # System events
    SERVER_START = "server_start"
    SERVER_STOP = "server_stop"
    SERVER_CRASH = "server_crash"
    
    # Dashboard updates
    DASHBOARD_UPDATE = "dashboard_update"
    
    # Notifications
    NOTIFICATION = "notification"
    ERROR = "error"
    WARNING = "warning"
    SUCCESS = "success"


class ConnectionType(str, Enum):
    """WebSocket connection types."""
    CONSOLE = "console"
    DASHBOARD = "dashboard"
    MONITORING = "monitoring"
    GENERAL = "general"


class WSMessage(BaseModel):
    """WebSocket message model."""
    
    type: WSMessageType = Field(..., description="Message type")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Message data")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Message timestamp")
    id: Optional[str] = Field(default=None, description="Message ID for tracking")
    connection_type: Optional[ConnectionType] = Field(default=None, description="Target connection type")
    
    class Config:
        use_enum_values = True


class ConsoleLogMessage(BaseModel):
    """Console log message data."""
    
    level: str = Field(..., description="Log level (INFO, WARN, ERROR, DEBUG)")
    message: str = Field(..., description="Log message")
    source: str = Field(default="server", description="Log source")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ConsoleCommandMessage(BaseModel):
    """Console command message data."""
    
    command: str = Field(..., description="Command to execute")
    user_id: Optional[str] = Field(default=None, description="User who sent the command")
    username: Optional[str] = Field(default=None, description="Username who sent the command")


class ConsoleCommandResultMessage(BaseModel):
    """Console command result message data."""
    
    command: str = Field(..., description="Executed command")
    success: bool = Field(..., description="Command success status")
    output: Optional[str] = Field(default=None, description="Command output")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ServerStatusMessage(BaseModel):
    """Server status message data."""
    
    status: str = Field(..., description="Server status (running, stopped, starting, stopping)")
    uptime: int = Field(default=0, description="Server uptime in seconds")
    online_players: int = Field(default=0, description="Number of online players")
    max_players: int = Field(default=20, description="Maximum players")
    version: str = Field(default="unknown", description="Server version")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class PerformanceUpdateMessage(BaseModel):
    """Performance update message data."""
    
    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_mb: float = Field(..., description="Memory usage in MB")
    uptime_seconds: float = Field(..., description="Uptime in seconds")
    tps: float = Field(default=20.0, description="Ticks per second")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class PlayerEventMessage(BaseModel):
    """Player event message data."""
    
    player: Dict[str, Any] = Field(..., description="Player information")
    event_type: str = Field(..., description="Event type (join, leave, chat)")
    message: Optional[str] = Field(default=None, description="Additional message (for chat events)")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class NotificationMessage(BaseModel):
    """Notification message data."""
    
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    level: str = Field(default="info", description="Notification level (info, warning, error, success)")
    duration: Optional[int] = Field(default=None, description="Auto-close duration in seconds")
    actions: Optional[list] = Field(default=None, description="Available actions")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class DashboardUpdateMessage(BaseModel):
    """Dashboard update message data."""
    
    server_status: Optional[ServerStatusMessage] = Field(default=None)
    performance: Optional[PerformanceUpdateMessage] = Field(default=None)
    player_count: Optional[int] = Field(default=None)
    recent_events: Optional[list] = Field(default=None)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# Helper functions for creating messages
def create_ws_message(
    message_type: WSMessageType, 
    data: Any = None, 
    connection_type: Optional[ConnectionType] = None,
    message_id: Optional[str] = None
) -> WSMessage:
    """Create a WebSocket message."""
    return WSMessage(
        type=message_type,
        data=data,
        connection_type=connection_type,
        id=message_id
    )


def create_console_log_message(level: str, message: str, source: str = "server") -> WSMessage:
    """Create a console log message."""
    data = ConsoleLogMessage(level=level, message=message, source=source).dict()
    return create_ws_message(WSMessageType.CONSOLE_LOG, data, ConnectionType.CONSOLE)


def create_server_status_message(
    status: str, 
    uptime: int = 0,
    online_players: int = 0,
    max_players: int = 20,
    version: str = "unknown"
) -> WSMessage:
    """Create a server status message."""
    data = ServerStatusMessage(
        status=status,
        uptime=uptime,
        online_players=online_players,
        max_players=max_players,
        version=version
    ).dict()
    return create_ws_message(WSMessageType.SERVER_STATUS, data, ConnectionType.DASHBOARD)


def create_performance_update_message(
    cpu_percent: float,
    memory_mb: float,
    uptime_seconds: float,
    tps: float = 20.0
) -> WSMessage:
    """Create a performance update message."""
    data = PerformanceUpdateMessage(
        cpu_percent=cpu_percent,
        memory_mb=memory_mb,
        uptime_seconds=uptime_seconds,
        tps=tps
    ).dict()
    return create_ws_message(WSMessageType.PERFORMANCE_UPDATE, data, ConnectionType.MONITORING)


def create_player_event_message(
    player: Dict[str, Any],
    event_type: str,
    message: Optional[str] = None
) -> WSMessage:
    """Create a player event message."""
    data = PlayerEventMessage(
        player=player,
        event_type=event_type,
        message=message
    ).dict()
    
    message_type_mapping = {
        "join": WSMessageType.PLAYER_JOIN,
        "leave": WSMessageType.PLAYER_LEAVE,
        "chat": WSMessageType.PLAYER_CHAT
    }
    
    ws_message_type = message_type_mapping.get(event_type, WSMessageType.PLAYER_JOIN)
    return create_ws_message(ws_message_type, data, ConnectionType.GENERAL)


def create_notification_message(
    title: str,
    message: str,
    level: str = "info",
    duration: Optional[int] = None,
    actions: Optional[list] = None
) -> WSMessage:
    """Create a notification message."""
    data = NotificationMessage(
        title=title,
        message=message,
        level=level,
        duration=duration,
        actions=actions
    ).dict()
    return create_ws_message(WSMessageType.NOTIFICATION, data, ConnectionType.GENERAL)


def create_dashboard_update_message(
    server_status: Optional[Dict[str, Any]] = None,
    performance: Optional[Dict[str, Any]] = None,
    player_count: Optional[int] = None,
    recent_events: Optional[list] = None
) -> WSMessage:
    """Create a dashboard update message."""
    data = DashboardUpdateMessage(
        server_status=ServerStatusMessage(**server_status) if server_status else None,
        performance=PerformanceUpdateMessage(**performance) if performance else None,
        player_count=player_count,
        recent_events=recent_events
    ).dict()
    return create_ws_message(WSMessageType.DASHBOARD_UPDATE, data, ConnectionType.DASHBOARD)


def create_error_message(message: str, details: Optional[str] = None) -> WSMessage:
    """Create an error message."""
    data = {
        "message": message,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    return create_ws_message(WSMessageType.ERROR, data, ConnectionType.GENERAL)