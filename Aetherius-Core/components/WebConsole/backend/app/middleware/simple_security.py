"""
Simple security middleware for WebConsole backend.
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class SimpleSecurityMiddleware(BaseHTTPMiddleware):
    """Simple security middleware without authentication (for debugging)."""
    
    def __init__(self, app):
        super().__init__(app)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through simple security middleware."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        try:
            # Process request without any authentication
            response = await call_next(request)
            
            # Add basic security headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            
            return response
            
        except Exception as e:
            # Log but don't interfere with normal error handling
            logger.debug(f"Request {request_id} error: {e}")
            raise