"""
Security utilities for authentication and authorization.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging

from ..core.config import settings
from ..core.container import get_container

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.security.jwt_expiration_hours)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.security.jwt_secret_key,
        algorithm=settings.security.jwt_algorithm
    )
    
    return encoded_jwt


def create_refresh_token(user_id: str) -> str:
    """Create refresh token for user."""
    data = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=30)  # Refresh tokens last 30 days
    }
    
    return jwt.encode(
        data,
        settings.security.jwt_secret_key,
        algorithm=settings.security.jwt_algorithm
    )


async def verify_jwt_token(token: str) -> Optional["User"]:
    """Verify JWT token and return user."""
    try:
        payload = jwt.decode(
            token,
            settings.security.jwt_secret_key,
            algorithms=[settings.security.jwt_algorithm]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        # TODO: Get user from database when UserService is implemented
        # For now, return a mock user object
        class MockUser:
            def __init__(self, user_id: str):
                self.id = user_id
                self.username = f"user_{user_id}"
                self.is_active = True
                self.is_active_user = True
        
        return MockUser(user_id)
        
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None


async def get_current_user(token: str = None) -> Optional["User"]:
    """Get current user from token."""
    if not token:
        return None
    return await verify_jwt_token(token)


def require_permission(permission: str):
    """Decorator to require specific permission for endpoint access."""
    def decorator(func):
        # For now, return the function as-is (placeholder implementation)
        return func
    return decorator


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def generate_session_token() -> str:
    """Generate a secure session token."""
    import secrets
    return secrets.token_urlsafe(32)


def generate_api_key() -> str:
    """Generate a secure API key."""
    import secrets
    return f"ak_{secrets.token_urlsafe(32)}"


def is_strong_password(password: str) -> tuple[bool, list[str]]:
    """Check if password meets security requirements."""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations."""
    import re
    
    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')
    
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed_file"
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_length = 255 - len(ext) - 1 if ext else 255
        filename = name[:max_name_length] + ('.' + ext if ext else '')
    
    return filename


def is_safe_path(path: str, base_path: str) -> bool:
    """Check if path is safe (within base_path and no directory traversal)."""
    import os
    
    try:
        # Resolve both paths
        resolved_path = os.path.realpath(os.path.join(base_path, path))
        resolved_base = os.path.realpath(base_path)
        
        # Check if resolved path is within base path
        return resolved_path.startswith(resolved_base)
        
    except (OSError, ValueError):
        return False


def mask_sensitive_data(data: Dict[str, Any], sensitive_keys: set = None) -> Dict[str, Any]:
    """Mask sensitive data in dictionary."""
    if sensitive_keys is None:
        sensitive_keys = {
            'password', 'secret', 'token', 'key', 'private',
            'credentials', 'auth', 'session', 'cookie'
        }
    
    masked_data = {}
    
    for key, value in data.items():
        key_lower = key.lower()
        
        # Check if key contains sensitive information
        is_sensitive = any(sensitive_key in key_lower for sensitive_key in sensitive_keys)
        
        if is_sensitive:
            if isinstance(value, str) and value:
                masked_data[key] = "***"
            else:
                masked_data[key] = "[MASKED]"
        elif isinstance(value, dict):
            masked_data[key] = mask_sensitive_data(value, sensitive_keys)
        elif isinstance(value, list):
            masked_data[key] = [
                mask_sensitive_data(item, sensitive_keys) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            masked_data[key] = value
    
    return masked_data


class SecurityAuditLogger:
    """Security event audit logger."""
    
    def __init__(self):
        self.logger = logging.getLogger("security_audit")
    
    def log_login_attempt(self, username: str, success: bool, ip_address: str, user_agent: str = None):
        """Log login attempt."""
        event = "LOGIN_SUCCESS" if success else "LOGIN_FAILURE"
        self.logger.info(
            f"{event} - User: {username}, IP: {ip_address}, UserAgent: {user_agent}"
        )
    
    def log_permission_check(self, user_id: str, permission: str, granted: bool, resource: str = None):
        """Log permission check."""
        event = "PERMISSION_GRANTED" if granted else "PERMISSION_DENIED"
        self.logger.info(
            f"{event} - User: {user_id}, Permission: {permission}, Resource: {resource}"
        )
    
    def log_security_event(self, event_type: str, user_id: str = None, details: Dict[str, Any] = None):
        """Log general security event."""
        details_str = f", Details: {details}" if details else ""
        self.logger.warning(
            f"SECURITY_EVENT - Type: {event_type}, User: {user_id}{details_str}"
        )


# Global security audit logger
security_audit = SecurityAuditLogger()