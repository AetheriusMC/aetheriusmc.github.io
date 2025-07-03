"""
Audit logging models for tracking user actions and system events.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import enum

from sqlalchemy import Column, String, DateTime, Enum, Text, JSON, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class AuditEventType(enum.Enum):
    """Audit event type enumeration."""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    
    # Authorization events
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    
    # Server management events
    SERVER_START = "server_start"
    SERVER_STOP = "server_stop"
    SERVER_RESTART = "server_restart"
    COMMAND_EXECUTED = "command_executed"
    
    # Player management events
    PLAYER_KICKED = "player_kicked"
    PLAYER_BANNED = "player_banned"
    PLAYER_UNBANNED = "player_unbanned"
    PLAYER_OP = "player_op"
    PLAYER_DEOP = "player_deop"
    
    # File management events
    FILE_VIEWED = "file_viewed"
    FILE_EDITED = "file_edited"
    FILE_UPLOADED = "file_uploaded"
    FILE_DOWNLOADED = "file_downloaded"
    FILE_DELETED = "file_deleted"
    
    # Configuration events
    CONFIG_CHANGED = "config_changed"
    SETTING_CHANGED = "setting_changed"
    
    # Plugin/Component events
    PLUGIN_INSTALLED = "plugin_installed"
    PLUGIN_ENABLED = "plugin_enabled"
    PLUGIN_DISABLED = "plugin_disabled"
    PLUGIN_UNINSTALLED = "plugin_uninstalled"
    COMPONENT_ENABLED = "component_enabled"
    COMPONENT_DISABLED = "component_disabled"
    
    # System events
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    SYSTEM_ERROR = "system_error"
    SECURITY_ALERT = "security_alert"
    
    # User management events
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_SUSPENDED = "user_suspended"
    USER_ACTIVATED = "user_activated"


class AuditSeverity(enum.Enum):
    """Audit event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditOutcome(enum.Enum):
    """Audit event outcome."""
    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"
    ERROR = "error"


class AuditLog(Base):
    """Audit log model for security and compliance tracking."""
    
    __tablename__ = "auditlog"
    
    # Event identification
    event_type: AuditEventType = Column(Enum(AuditEventType), nullable=False, index=True)
    event_category: str = Column(String(50), nullable=False, index=True)
    event_description: str = Column(Text, nullable=False)
    
    # Event outcome and severity
    outcome: AuditOutcome = Column(Enum(AuditOutcome), nullable=False, index=True)
    severity: AuditSeverity = Column(Enum(AuditSeverity), default=AuditSeverity.MEDIUM, nullable=False)
    
    # Actor information (who performed the action)
    user_id: Optional[str] = Column(String, ForeignKey('user.id'), nullable=True, index=True)
    username: Optional[str] = Column(String(50), nullable=True)  # Denormalized for performance
    session_id: Optional[str] = Column(String, nullable=True)
    
    # Source information
    ip_address: Optional[str] = Column(String(45), nullable=True, index=True)
    user_agent: Optional[str] = Column(Text, nullable=True)
    source_system: str = Column(String(50), default="webconsole", nullable=False)
    
    # Target information (what was affected)
    target_type: Optional[str] = Column(String(50), nullable=True, index=True)
    target_id: Optional[str] = Column(String(255), nullable=True, index=True)
    target_name: Optional[str] = Column(String(255), nullable=True)
    
    # Event details
    details: Optional[Dict[str, Any]] = Column(JSON, nullable=True)
    before_state: Optional[Dict[str, Any]] = Column(JSON, nullable=True)
    after_state: Optional[Dict[str, Any]] = Column(JSON, nullable=True)
    
    # Request information
    request_id: Optional[str] = Column(String(50), nullable=True, index=True)
    correlation_id: Optional[str] = Column(String(50), nullable=True, index=True)
    
    # Timing information
    event_timestamp: datetime = Column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
        index=True
    )
    duration_ms: Optional[int] = Column(nullable=True)  # Event duration in milliseconds
    
    # Error information
    error_code: Optional[str] = Column(String(50), nullable=True)
    error_message: Optional[str] = Column(Text, nullable=True)
    stack_trace: Optional[str] = Column(Text, nullable=True)
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", lazy="select")
    
    # Database constraints and indexes
    __table_args__ = (
        Index('idx_audit_event_timestamp', 'event_timestamp'),
        Index('idx_audit_user_timestamp', 'user_id', 'event_timestamp'),
        Index('idx_audit_event_type_timestamp', 'event_type', 'event_timestamp'),
        Index('idx_audit_target_type_timestamp', 'target_type', 'event_timestamp'),
        Index('idx_audit_outcome_severity', 'outcome', 'severity'),
        Index('idx_audit_ip_timestamp', 'ip_address', 'event_timestamp'),
        Index('idx_audit_correlation', 'correlation_id'),
    )
    
    @classmethod
    def create_event(
        cls,
        event_type: AuditEventType,
        event_description: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        target_name: Optional[str] = None,
        outcome: AuditOutcome = AuditOutcome.SUCCESS,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        duration_ms: Optional[int] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> "AuditLog":
        """Create an audit log entry."""
        
        # Determine event category from event type
        event_category = cls._get_event_category(event_type)
        
        return cls(
            event_type=event_type,
            event_category=event_category,
            event_description=event_description,
            outcome=outcome,
            severity=severity,
            user_id=user_id,
            username=username,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            details=details or {},
            before_state=before_state,
            after_state=after_state,
            request_id=request_id,
            correlation_id=correlation_id,
            duration_ms=duration_ms,
            error_code=error_code,
            error_message=error_message
        )
    
    @staticmethod
    def _get_event_category(event_type: AuditEventType) -> str:
        """Get event category from event type."""
        category_mapping = {
            # Authentication
            AuditEventType.LOGIN_SUCCESS: "authentication",
            AuditEventType.LOGIN_FAILURE: "authentication",
            AuditEventType.LOGOUT: "authentication",
            AuditEventType.PASSWORD_CHANGE: "authentication",
            AuditEventType.ACCOUNT_LOCKED: "authentication",
            AuditEventType.ACCOUNT_UNLOCKED: "authentication",
            
            # Authorization
            AuditEventType.PERMISSION_GRANTED: "authorization",
            AuditEventType.PERMISSION_DENIED: "authorization",
            AuditEventType.ROLE_ASSIGNED: "authorization",
            AuditEventType.ROLE_REMOVED: "authorization",
            
            # Server management
            AuditEventType.SERVER_START: "server_management",
            AuditEventType.SERVER_STOP: "server_management",
            AuditEventType.SERVER_RESTART: "server_management",
            AuditEventType.COMMAND_EXECUTED: "server_management",
            
            # Player management
            AuditEventType.PLAYER_KICKED: "player_management",
            AuditEventType.PLAYER_BANNED: "player_management",
            AuditEventType.PLAYER_UNBANNED: "player_management",
            AuditEventType.PLAYER_OP: "player_management",
            AuditEventType.PLAYER_DEOP: "player_management",
            
            # File management
            AuditEventType.FILE_VIEWED: "file_management",
            AuditEventType.FILE_EDITED: "file_management",
            AuditEventType.FILE_UPLOADED: "file_management",
            AuditEventType.FILE_DOWNLOADED: "file_management",
            AuditEventType.FILE_DELETED: "file_management",
            
            # Configuration
            AuditEventType.CONFIG_CHANGED: "configuration",
            AuditEventType.SETTING_CHANGED: "configuration",
            
            # Plugins/Components
            AuditEventType.PLUGIN_INSTALLED: "plugin_management",
            AuditEventType.PLUGIN_ENABLED: "plugin_management",
            AuditEventType.PLUGIN_DISABLED: "plugin_management",
            AuditEventType.PLUGIN_UNINSTALLED: "plugin_management",
            AuditEventType.COMPONENT_ENABLED: "component_management",
            AuditEventType.COMPONENT_DISABLED: "component_management",
            
            # System
            AuditEventType.BACKUP_CREATED: "system",
            AuditEventType.BACKUP_RESTORED: "system",
            AuditEventType.SYSTEM_ERROR: "system",
            AuditEventType.SECURITY_ALERT: "security",
            
            # User management
            AuditEventType.USER_CREATED: "user_management",
            AuditEventType.USER_UPDATED: "user_management",
            AuditEventType.USER_DELETED: "user_management",
            AuditEventType.USER_SUSPENDED: "user_management",
            AuditEventType.USER_ACTIVATED: "user_management",
        }
        
        return category_mapping.get(event_type, "other")
    
    def add_detail(self, key: str, value: Any) -> None:
        """Add detail to the audit log."""
        if self.details is None:
            self.details = {}
        self.details[key] = value
    
    def set_error(self, error_code: str, error_message: str, stack_trace: Optional[str] = None) -> None:
        """Set error information."""
        self.outcome = AuditOutcome.ERROR
        self.error_code = error_code
        self.error_message = error_message
        self.stack_trace = stack_trace
    
    def set_target(self, target_type: str, target_id: str, target_name: Optional[str] = None) -> None:
        """Set target information."""
        self.target_type = target_type
        self.target_id = target_id
        self.target_name = target_name
    
    @property
    def is_security_event(self) -> bool:
        """Check if this is a security-related event."""
        security_events = {
            AuditEventType.LOGIN_FAILURE,
            AuditEventType.ACCOUNT_LOCKED,
            AuditEventType.PERMISSION_DENIED,
            AuditEventType.SECURITY_ALERT
        }
        return self.event_type in security_events
    
    @property
    def is_high_risk(self) -> bool:
        """Check if this is a high-risk event."""
        return self.severity in (AuditSeverity.HIGH, AuditSeverity.CRITICAL)
    
    def __repr__(self) -> str:
        return (
            f"<AuditLog(event_type='{self.event_type.value}', "
            f"user='{self.username}', outcome='{self.outcome.value}')>"
        )