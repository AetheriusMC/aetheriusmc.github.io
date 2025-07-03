"""
Custom Exception Classes
"""

from fastapi import HTTPException
from typing import Any, Dict, Optional


class WebComponentException(Exception):
    """Base exception for web component"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class CoreConnectionError(WebComponentException):
    """Exception for core connection issues"""
    pass


class CoreAPIError(WebComponentException):
    """Exception for core API call failures"""
    pass


class WebSocketError(WebComponentException):
    """Exception for WebSocket related issues"""
    pass


class ValidationError(WebComponentException):
    """Exception for data validation failures"""
    pass


# HTTP Exception wrappers
def create_http_exception(
    status_code: int,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """Create HTTP exception with structured error response"""
    return HTTPException(
        status_code=status_code,
        detail={
            "error": message,
            "details": details or {},
            "status_code": status_code
        }
    )


def core_not_available_exception():
    """Exception for when core is not available"""
    return create_http_exception(
        503,
        "Aetherius Core is not available",
        {"reason": "Core connection not established"}
    )


def invalid_command_exception(command: str):
    """Exception for invalid commands"""
    return create_http_exception(
        400,
        "Invalid command",
        {"command": command, "reason": "Command validation failed"}
    )


def permission_denied_exception(action: str):
    """Exception for permission denied"""
    return create_http_exception(
        403,
        "Permission denied",
        {"action": action, "reason": "Insufficient privileges"}
    )


def handle_api_errors(func):
    """Decorator to handle API errors consistently"""
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            # Convert other exceptions to HTTP exceptions
            raise create_http_exception(
                500,
                "Internal server error",
                {"error": str(e), "type": type(e).__name__}
            )
    
    return wrapper