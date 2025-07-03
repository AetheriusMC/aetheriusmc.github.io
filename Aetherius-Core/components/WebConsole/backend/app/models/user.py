"""
User and authentication related models.
"""

from typing import List, Optional, Set
from typing import TYPE_CHECKING
from datetime import datetime
import enum

from sqlalchemy import (
    Column, String, Boolean, DateTime, Enum, Text, Integer,
    ForeignKey, Table, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from passlib.context import CryptContext

from .base import Base


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserStatus(enum.Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class RoleType(enum.Enum):
    """Role type enumeration."""
    SYSTEM = "system"
    CUSTOM = "custom"


# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', String, ForeignKey('user.id'), primary_key=True),
    Column('role_id', String, ForeignKey('userrole.id'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), server_default=func.now()),
    Column('assigned_by', String, ForeignKey('user.id'), nullable=True)
)

# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', String, ForeignKey('userrole.id'), primary_key=True),
    Column('permission_id', String, ForeignKey('permission.id'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), server_default=func.now())
)


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "user"
    
    # Basic user information
    username: str = Column(String(50), unique=True, nullable=False, index=True)
    email: str = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password: str = Column(String(255), nullable=False)
    
    # User profile
    first_name: Optional[str] = Column(String(100), nullable=True)
    last_name: Optional[str] = Column(String(100), nullable=True)
    display_name: Optional[str] = Column(String(100), nullable=True)
    avatar_url: Optional[str] = Column(String(500), nullable=True)
    timezone: str = Column(String(50), default="UTC", nullable=False)
    locale: str = Column(String(10), default="en", nullable=False)
    
    # Account status
    status: UserStatus = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    email_verified: bool = Column(Boolean, default=False, nullable=False)
    email_verified_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    
    # Security settings
    require_password_change: bool = Column(Boolean, default=False, nullable=False)
    password_changed_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    last_login_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    last_login_ip: Optional[str] = Column(String(45), nullable=True)  # IPv6 support
    failed_login_attempts: int = Column(Integer, default=0, nullable=False)
    locked_until: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    
    # Two-factor authentication
    tfa_enabled: bool = Column(Boolean, default=False, nullable=False)
    tfa_secret: Optional[str] = Column(String(32), nullable=True)
    backup_codes: Optional[str] = Column(Text, nullable=True)  # JSON encoded
    
    # Relationships
    roles: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin"
    )
    
    sessions: Mapped[List["UserSession"]] = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Database constraints
    __table_args__ = (
        Index('idx_user_email_status', 'email', 'status'),
        Index('idx_user_username_status', 'username', 'status'),
        Index('idx_user_last_login', 'last_login_at'),
    )
    
    def set_password(self, password: str) -> None:
        """Set user password with hashing."""
        self.hashed_password = pwd_context.hash(password)
        self.password_changed_at = datetime.utcnow()
        self.require_password_change = False
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(password, self.hashed_password)
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has specific role."""
        return any(role.name == role_name for role in self.roles)
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has specific permission."""
        for role in self.roles:
            if role.has_permission(permission_name):
                return True
        return False
    
    def get_permissions(self) -> Set[str]:
        """Get all user permissions from roles."""
        permissions = set()
        for role in self.roles:
            permissions.update(perm.name for perm in role.permissions)
        return permissions
    
    def is_account_locked(self) -> bool:
        """Check if account is locked."""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    def lock_account(self, duration_minutes: int = 30) -> None:
        """Lock user account for specified duration."""
        from datetime import timedelta
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
    
    def unlock_account(self) -> None:
        """Unlock user account."""
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def record_login(self, ip_address: Optional[str] = None) -> None:
        """Record successful login."""
        self.last_login_at = datetime.utcnow()
        self.last_login_ip = ip_address
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def record_failed_login(self, max_attempts: int = 5) -> None:
        """Record failed login attempt."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.lock_account()
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.display_name or self.username
    
    @property
    def is_active_user(self) -> bool:
        """Check if user is active."""
        return (
            self.status == UserStatus.ACTIVE and
            self.is_active and
            not self.is_account_locked()
        )
    
    def __repr__(self) -> str:
        return f"<User(username='{self.username}', email='{self.email}')>"


class UserRole(Base):
    """Role model for role-based access control."""
    
    __tablename__ = "userrole"
    
    # Role information
    name: str = Column(String(50), unique=True, nullable=False, index=True)
    display_name: str = Column(String(100), nullable=False)
    description: Optional[str] = Column(Text, nullable=True)
    
    # Role properties
    role_type: RoleType = Column(Enum(RoleType), default=RoleType.CUSTOM, nullable=False)
    is_default: bool = Column(Boolean, default=False, nullable=False)
    priority: int = Column(Integer, default=0, nullable=False)  # Higher priority = more important
    
    # Relationships
    users: Mapped[List[User]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )
    
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin"
    )
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if role has specific permission."""
        return any(perm.name == permission_name for perm in self.permissions)
    
    def add_permission(self, permission: "Permission") -> None:
        """Add permission to role."""
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, permission: "Permission") -> None:
        """Remove permission from role."""
        if permission in self.permissions:
            self.permissions.remove(permission)
    
    def __repr__(self) -> str:
        return f"<UserRole(name='{self.name}')>"


class Permission(Base):
    """Permission model for granular access control."""
    
    __tablename__ = "permission"
    
    # Permission information
    name: str = Column(String(100), unique=True, nullable=False, index=True)
    display_name: str = Column(String(100), nullable=False)
    description: Optional[str] = Column(Text, nullable=True)
    
    # Permission categorization
    category: str = Column(String(50), nullable=False, index=True)
    resource: str = Column(String(50), nullable=False)
    action: str = Column(String(50), nullable=False)
    
    # Permission properties
    is_system: bool = Column(Boolean, default=False, nullable=False)
    requires_2fa: bool = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    roles: Mapped[List[UserRole]] = relationship(
        "UserRole",
        secondary=role_permissions,
        back_populates="permissions"
    )
    
    # Database constraints
    __table_args__ = (
        UniqueConstraint('resource', 'action', name='uq_permission_resource_action'),
        Index('idx_permission_category', 'category'),
        Index('idx_permission_resource', 'resource'),
    )
    
    def __repr__(self) -> str:
        return f"<Permission(name='{self.name}')>"


class UserSession(Base):
    """User session model for session management."""
    
    __tablename__ = "usersession"
    
    # Session information
    user_id: str = Column(String, ForeignKey('user.id'), nullable=False, index=True)
    session_token: str = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token: Optional[str] = Column(String(255), unique=True, nullable=True)
    
    # Session metadata
    ip_address: Optional[str] = Column(String(45), nullable=True)
    user_agent: Optional[str] = Column(Text, nullable=True)
    device_fingerprint: Optional[str] = Column(String(255), nullable=True)
    
    # Session timing
    expires_at: datetime = Column(DateTime(timezone=True), nullable=False)
    last_activity: datetime = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Session status
    is_active: bool = Column(Boolean, default=True, nullable=False)
    revoked_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    revoked_reason: Optional[str] = Column(String(100), nullable=True)
    
    # Relationships
    user: Mapped[User] = relationship("User", back_populates="sessions")
    
    # Database constraints
    __table_args__ = (
        Index('idx_session_user_active', 'user_id', 'is_active'),
        Index('idx_session_expires', 'expires_at'),
        Index('idx_session_activity', 'last_activity'),
    )
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if session is valid."""
        return self.is_active and not self.is_expired and self.revoked_at is None
    
    def revoke(self, reason: str = "manual") -> None:
        """Revoke session."""
        self.is_active = False
        self.revoked_at = datetime.utcnow()
        self.revoked_reason = reason
    
    def extend(self, hours: int = 24) -> None:
        """Extend session expiration."""
        from datetime import timedelta
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def __repr__(self) -> str:
        return f"<UserSession(user_id='{self.user_id}', active={self.is_active})>"