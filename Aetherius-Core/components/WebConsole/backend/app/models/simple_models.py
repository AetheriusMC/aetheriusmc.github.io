"""
Simplified models for initial migration.
"""

from typing import Optional
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, Integer, Float, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models."""
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)
    avatar: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ServerConfig(Base):
    """Server configuration model."""
    __tablename__ = "server_configs"
    
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    data_type: Mapped[str] = mapped_column(String(20), default="string", nullable=False)
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class BackupRecord(Base):
    """Backup record model."""
    __tablename__ = "backup_records"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    backup_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    compression: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    retention_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ConsoleLog(Base):
    """Console log model."""
    __tablename__ = "console_logs"
    
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    level: Mapped[str] = mapped_column(String(10), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    thread: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    logger_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    stack_trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class SystemMetrics(Base):
    """System metrics model."""
    __tablename__ = "system_metrics"
    
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cpu_usage: Mapped[float] = mapped_column(Float, nullable=False)
    memory_usage: Mapped[float] = mapped_column(Float, nullable=False)
    disk_usage: Mapped[float] = mapped_column(Float, nullable=False)
    network_rx: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    network_tx: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    active_connections: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mspt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    players_online: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chunks_loaded: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    entities_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class PlayerSession(Base):
    """Player session model."""
    __tablename__ = "player_sessions"
    
    player_uuid: Mapped[str] = mapped_column(String(36), nullable=False)
    username: Mapped[str] = mapped_column(String(16), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    login_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    logout_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    session_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    disconnect_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class AuditLog(Base):
    """Audit log model."""
    __tablename__ = "audit_logs"
    
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Notification(Base):
    """Notification model."""
    __tablename__ = "notifications"
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(String(20), nullable=False)
    priority: Mapped[str] = mapped_column(String(10), default="medium", nullable=False)
    sender_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    target_user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    is_global: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class APIKey(Base):
    """API key model."""
    __tablename__ = "api_keys"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    prefix: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rate_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)