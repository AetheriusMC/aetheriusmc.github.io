"""
Base model classes and database configuration.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import String, DateTime, Boolean, Text, JSON, func, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""
    
    # Allow unmapped annotations for backward compatibility
    __allow_unmapped__ = True
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower()
    
    # Common columns for all models
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Primary key UUID"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record last update timestamp"
    )
    
    # Soft delete support
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Soft delete timestamp"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Active status flag"
    )
    
    # Metadata fields
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
        comment="Additional metadata in JSON format"
    )
    
    def to_dict(self, exclude: Optional[set] = None) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        exclude = exclude or set()
        result = {}
        
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif isinstance(value, uuid.UUID):
                    value = str(value)
                result[column.name] = value
        
        return result
    
    def update_from_dict(self, data: Dict[str, Any], exclude: Optional[set] = None) -> None:
        """Update model instance from dictionary."""
        exclude = exclude or {'id', 'created_at', 'updated_at'}
        
        for key, value in data.items():
            if key not in exclude and hasattr(self, key):
                setattr(self, key, value)
    
    def soft_delete(self) -> None:
        """Perform soft delete by setting deleted_at timestamp."""
        self.deleted_at = datetime.utcnow()
        self.is_active = False
    
    def restore(self) -> None:
        """Restore soft-deleted record."""
        self.deleted_at = None
        self.is_active = True
    
    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted."""
        return self.deleted_at is not None
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"


class TimestampMixin:
    """Mixin for models that only need timestamp fields."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin for models that support soft delete."""
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    
    def soft_delete(self) -> None:
        """Perform soft delete."""
        self.deleted_at = datetime.utcnow()
        self.is_active = False
    
    def restore(self) -> None:
        """Restore soft-deleted record."""
        self.deleted_at = None
        self.is_active = True
    
    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted."""
        return self.deleted_at is not None


class MetadataMixin:
    """Mixin for models that support additional metadata."""
    
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        "metadata",
        JSON,
        nullable=True
    )
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value."""
        if self.metadata_ is None:
            self.metadata_ = {}
        self.metadata_[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        if self.metadata_ is None:
            return default
        return self.metadata_.get(key, default)
    
    def remove_metadata(self, key: str) -> None:
        """Remove metadata key."""
        if self.metadata_ and key in self.metadata_:
            del self.metadata_[key]