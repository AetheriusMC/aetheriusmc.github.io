"""
System settings and configuration models.
"""

from typing import Optional, Any, Dict
from datetime import datetime
import enum

from sqlalchemy import Column, String, Text, Boolean, JSON, DateTime, Enum, Float, Integer, UniqueConstraint, Index
from sqlalchemy.orm import Mapped
from sqlalchemy.sql import func

from .base import Base


class SettingType(enum.Enum):
    """Setting type enumeration."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    TEXT = "text"
    PASSWORD = "password"
    URL = "url"
    EMAIL = "email"


class SettingCategory(enum.Enum):
    """Setting category enumeration."""
    GENERAL = "general"
    SECURITY = "security"
    AUTHENTICATION = "authentication"
    WEBSOCKET = "websocket"
    DATABASE = "database"
    CACHE = "cache"
    LOGGING = "logging"
    MONITORING = "monitoring"
    FEATURES = "features"
    BACKUP = "backup"
    NOTIFICATION = "notification"
    INTEGRATION = "integration"
    UI = "ui"
    CUSTOM = "custom"


class SystemSetting(Base):
    """System setting model for dynamic configuration."""
    
    __tablename__ = "systemsetting"
    
    # Setting identification
    key: str = Column(String(255), unique=True, nullable=False, index=True)
    name: str = Column(String(255), nullable=False)
    description: Optional[str] = Column(Text, nullable=True)
    
    # Setting categorization
    category: SettingCategory = Column(Enum(SettingCategory), nullable=False, index=True)
    subcategory: Optional[str] = Column(String(100), nullable=True)
    
    # Setting value and type
    value: Optional[str] = Column(Text, nullable=True)
    default_value: Optional[str] = Column(Text, nullable=True)
    setting_type: SettingType = Column(Enum(SettingType), nullable=False)
    
    # Setting properties
    is_required: bool = Column(Boolean, default=False, nullable=False)
    is_encrypted: bool = Column(Boolean, default=False, nullable=False)
    is_system: bool = Column(Boolean, default=False, nullable=False)  # System settings cannot be deleted
    is_public: bool = Column(Boolean, default=True, nullable=False)   # Public settings visible to all users
    
    # Validation and constraints
    validation_regex: Optional[str] = Column(String(500), nullable=True)
    min_value: Optional[float] = Column(Float, nullable=True)
    max_value: Optional[float] = Column(Float, nullable=True)
    allowed_values: Optional[str] = Column(Text, nullable=True)  # JSON array of allowed values
    
    # UI properties
    display_order: int = Column(Integer, default=0, nullable=False)
    ui_component: Optional[str] = Column(String(50), nullable=True)  # input, select, textarea, etc.
    ui_options: Optional[Dict[str, Any]] = Column(JSON, nullable=True)
    
    # Change tracking
    changed_by: Optional[str] = Column(String(255), nullable=True)
    changed_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    change_reason: Optional[str] = Column(Text, nullable=True)
    
    # Restart requirement
    requires_restart: bool = Column(Boolean, default=False, nullable=False)
    restart_component: Optional[str] = Column(String(100), nullable=True)  # Which component needs restart
    
    # Database constraints
    __table_args__ = (
        Index('idx_setting_category_order', 'category', 'display_order'),
        Index('idx_setting_system_public', 'is_system', 'is_public'),
        Index('idx_setting_changed', 'changed_at'),
    )
    
    def get_typed_value(self) -> Any:
        """Get value converted to appropriate type."""
        if self.value is None:
            return self.get_default_value()
        
        try:
            if self.setting_type == SettingType.STRING:
                return str(self.value)
            elif self.setting_type == SettingType.INTEGER:
                return int(self.value)
            elif self.setting_type == SettingType.FLOAT:
                return float(self.value)
            elif self.setting_type == SettingType.BOOLEAN:
                return self.value.lower() in ('true', '1', 'yes', 'on')
            elif self.setting_type == SettingType.JSON:
                import json
                return json.loads(self.value)
            elif self.setting_type in (SettingType.TEXT, SettingType.PASSWORD, SettingType.URL, SettingType.EMAIL):
                return str(self.value)
            else:
                return self.value
        except (ValueError, TypeError, json.JSONDecodeError):
            return self.get_default_value()
    
    def get_default_value(self) -> Any:
        """Get default value converted to appropriate type."""
        if self.default_value is None:
            return None
        
        try:
            if self.setting_type == SettingType.STRING:
                return str(self.default_value)
            elif self.setting_type == SettingType.INTEGER:
                return int(self.default_value)
            elif self.setting_type == SettingType.FLOAT:
                return float(self.default_value)
            elif self.setting_type == SettingType.BOOLEAN:
                return self.default_value.lower() in ('true', '1', 'yes', 'on')
            elif self.setting_type == SettingType.JSON:
                import json
                return json.loads(self.default_value)
            elif self.setting_type in (SettingType.TEXT, SettingType.PASSWORD, SettingType.URL, SettingType.EMAIL):
                return str(self.default_value)
            else:
                return self.default_value
        except (ValueError, TypeError, json.JSONDecodeError):
            return None
    
    def set_value(self, value: Any, changed_by: Optional[str] = None, change_reason: Optional[str] = None) -> None:
        """Set setting value with change tracking."""
        if self.setting_type == SettingType.JSON:
            import json
            self.value = json.dumps(value) if value is not None else None
        elif self.setting_type == SettingType.BOOLEAN:
            self.value = str(bool(value)).lower()
        else:
            self.value = str(value) if value is not None else None
        
        self.changed_by = changed_by
        self.changed_at = datetime.utcnow()
        self.change_reason = change_reason
    
    def validate_value(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate setting value."""
        if self.is_required and (value is None or value == ""):
            return False, "Value is required"
        
        if value is None:
            return True, None
        
        # Type validation
        try:
            if self.setting_type == SettingType.INTEGER:
                int_value = int(value)
                if self.min_value is not None and int_value < self.min_value:
                    return False, f"Value must be at least {self.min_value}"
                if self.max_value is not None and int_value > self.max_value:
                    return False, f"Value must be at most {self.max_value}"
            elif self.setting_type == SettingType.FLOAT:
                float_value = float(value)
                if self.min_value is not None and float_value < self.min_value:
                    return False, f"Value must be at least {self.min_value}"
                if self.max_value is not None and float_value > self.max_value:
                    return False, f"Value must be at most {self.max_value}"
            elif self.setting_type == SettingType.JSON:
                import json
                json.loads(str(value))
            elif self.setting_type == SettingType.EMAIL:
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, str(value)):
                    return False, "Invalid email format"
            elif self.setting_type == SettingType.URL:
                import re
                url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
                if not re.match(url_pattern, str(value)):
                    return False, "Invalid URL format"
        except (ValueError, TypeError, json.JSONDecodeError):
            return False, f"Invalid value for type {self.setting_type.value}"
        
        # Regex validation
        if self.validation_regex:
            import re
            if not re.match(self.validation_regex, str(value)):
                return False, "Value does not match required pattern"
        
        # Allowed values validation
        if self.allowed_values:
            try:
                import json
                allowed = json.loads(self.allowed_values)
                if str(value) not in allowed:
                    return False, f"Value must be one of: {', '.join(allowed)}"
            except json.JSONDecodeError:
                pass
        
        return True, None
    
    def reset_to_default(self, changed_by: Optional[str] = None) -> None:
        """Reset setting to default value."""
        self.set_value(self.get_default_value(), changed_by, "Reset to default")
    
    @property
    def has_changed(self) -> bool:
        """Check if setting has been changed from default."""
        return self.value != self.default_value
    
    @property
    def is_editable(self) -> bool:
        """Check if setting can be edited."""
        return not self.is_system or not self.is_required
    
    def to_dict(self, include_value: bool = True, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert setting to dictionary."""
        data = {
            'id': self.id,
            'key': self.key,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'subcategory': self.subcategory,
            'setting_type': self.setting_type.value,
            'is_required': self.is_required,
            'is_system': self.is_system,
            'is_public': self.is_public,
            'display_order': self.display_order,
            'ui_component': self.ui_component,
            'ui_options': self.ui_options,
            'requires_restart': self.requires_restart,
            'restart_component': self.restart_component,
            'has_changed': self.has_changed,
            'is_editable': self.is_editable,
            'changed_at': self.changed_at.isoformat() if self.changed_at else None,
            'changed_by': self.changed_by,
        }
        
        if include_value:
            if self.is_encrypted and not include_sensitive:
                data['value'] = '***' if self.value else None
            else:
                data['value'] = self.get_typed_value()
            data['default_value'] = self.get_default_value()
        
        # Add validation info
        if self.min_value is not None:
            data['min_value'] = self.min_value
        if self.max_value is not None:
            data['max_value'] = self.max_value
        if self.allowed_values:
            try:
                import json
                data['allowed_values'] = json.loads(self.allowed_values)
            except json.JSONDecodeError:
                pass
        
        return data
    
    def __repr__(self) -> str:
        return f"<SystemSetting(key='{self.key}', category='{self.category.value}')>"