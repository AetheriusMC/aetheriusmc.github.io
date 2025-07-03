"""
Custom middleware for the application
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logging import get_logger
from app.utils.exceptions import WebComponentException

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request
        start_time = time.time()
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            request_id=request_id,
            client_ip=request.client.host if request.client else None
        )
        
        try:
            response = await call_next(request)
            
            # Log successful response
            process_time = time.time() - start_time
            logger.info(
                "Request completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=f"{process_time:.3f}s",
                request_id=request_id
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            # Log slow requests
            if process_time > 1.0:
                logger.warning(
                    "Slow request detected",
                    method=request.method,
                    url=str(request.url),
                    process_time=f"{process_time:.3f}s",
                    request_id=request_id
                )
            
            return response
            
        except Exception as exc:
            # Log error
            process_time = time.time() - start_time
            logger.error(
                "Request failed",
                method=request.method,
                url=str(request.url),
                error=str(exc),
                process_time=f"{process_time:.3f}s",
                request_id=request_id,
                exc_info=True
            )
            
            # Handle custom exceptions
            if isinstance(exc, WebComponentException):
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": exc.message,
                        "details": exc.details,
                        "request_id": request_id
                    },
                    headers={"X-Request-ID": request_id}
                )
            
            # Re-raise for FastAPI's exception handlers
            raise exc


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.requests = {}  # {client_ip: [timestamp, ...]}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                timestamp for timestamp in self.requests[client_ip]
                if timestamp > minute_ago
            ]
        else:
            self.requests[client_ip] = []
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.calls_per_minute:
            logger.warning(
                "Rate limit exceeded",
                client_ip=client_ip,
                requests_count=len(self.requests[client_ip]),
                limit=self.calls_per_minute
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "details": {
                        "limit": self.calls_per_minute,
                        "window": "1 minute"
                    }
                }
            )
        
        # Record request
        self.requests[client_ip].append(current_time)
        
        return await call_next(request)