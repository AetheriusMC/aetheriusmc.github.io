"""
Logging middleware for WebConsole backend.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logging middleware for request/response logging."""
    
    def __init__(self, app):
        super().__init__(app)
        
        # Paths to exclude from logging
        self.exclude_paths = {
            "/health",
            "/metrics",
            "/favicon.ico"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through logging middleware."""
        start_time = time.time()
        
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Extract request information
        client_ip = self.get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")
        request_id = getattr(request.state, "request_id", "unknown")
        user_id = getattr(request.state, "user_id", None)
        username = getattr(request.state, "username", None)
        
        # Log request start
        logger.info(
            f"Request started - {request.method} {request.url.path} "
            f"from {client_ip} (User: {username or 'anonymous'}, ID: {request_id})"
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log successful response
            logger.info(
                f"Request completed - {request.method} {request.url.path} "
                f"Status: {response.status_code} "
                f"Time: {process_time:.3f}s "
                f"User: {username or 'anonymous'} "
                f"ID: {request_id}"
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Calculate processing time for error case
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed - {request.method} {request.url.path} "
                f"Error: {str(e)} "
                f"Time: {process_time:.3f}s "
                f"User: {username or 'anonymous'} "
                f"ID: {request_id}",
                exc_info=True
            )
            
            # Re-raise the exception
            raise
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the list
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"