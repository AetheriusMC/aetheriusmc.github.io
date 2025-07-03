"""
Security middleware for WebConsole backend.
"""

import time
import uuid
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from ..core.config import settings
from ..utils.security import verify_jwt_token, get_current_user

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for authentication and authorization."""
    
    def __init__(self, app):
        super().__init__(app)
        self.security = HTTPBearer(auto_error=False)
        
        # Public endpoints that don't require authentication
        self.public_endpoints = {
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
        }
        
        # API endpoints that require authentication
        self.protected_patterns = [
            "/api/v1/",
            "/ws/"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security middleware."""
        start_time = time.time()
        request_id = None
        
        try:
            # Generate request ID
            request_id = str(uuid.uuid4())
            request.state.request_id = request_id
            logger.info(f"Processing request {request_id}: {request.method} {request.url}")
            
            # Check if endpoint requires authentication
            requires_auth = self.requires_authentication(request)
            logger.info(f"Request {request_id} requires authentication: {requires_auth}")
            
            if requires_auth:
                logger.info(f"Authenticating request {request_id}")
                await self.authenticate_request(request)
                logger.info(f"Request {request_id} authenticated successfully")
            
            # Process request
            logger.info(f"Calling next middleware for request {request_id}")
            response = await call_next(request)
            logger.info(f"Request {request_id} processed by downstream, adding headers")
            
            # Add security headers to response
            self.add_security_headers(response)
            
            # Add request ID to response
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except HTTPException as e:
            logger.warning(f"HTTP exception in security middleware for request {request_id}: {e}")
            raise
        except Exception as e:
            # Handle common connection errors gracefully
            error_msg = str(e).lower()
            if any(term in error_msg for term in ['endofstream', 'wouldblock', 'connection', 'disconnect']):
                logger.debug(f"Connection error in security middleware for request {request_id}: {e}")
                # Re-raise the original exception instead of wrapping it
                raise
            else:
                logger.exception(f"Unexpected error in security middleware for request {request_id}: {e}")
                raise HTTPException(status_code=500, detail="Internal security error")
        finally:
            # Log request processing time
            if request_id:
                process_time = time.time() - start_time
                logger.debug(f"Request {request_id} completed in {process_time:.3f}s")
    
    def requires_authentication(self, request: Request) -> bool:
        """Check if request requires authentication."""
        path = request.url.path
        
        # Check public endpoints
        if path in self.public_endpoints:
            return False
        
        # Check protected patterns
        for pattern in self.protected_patterns:
            if path.startswith(pattern):
                return True
        
        return False
    
    async def authenticate_request(self, request: Request) -> None:
        """Authenticate request using JWT token."""
        try:
            # Extract token from Authorization header or cookie
            token = await self.extract_token(request)
            
            if not token:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Verify token and get user
            user = await verify_jwt_token(token)
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or expired token"
                )
            
            # Check if user is active (safely handle missing attributes)
            is_active = getattr(user, 'is_active', True) or getattr(user, 'is_active_user', True)
            if not is_active:
                raise HTTPException(
                    status_code=403,
                    detail="Account is inactive or suspended"
                )
            
            # Store user in request state (safely handle missing attributes)
            request.state.user = user
            request.state.user_id = getattr(user, 'id', 'unknown')
            request.state.username = getattr(user, 'username', 'unknown')
            
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Authentication error: {e}")
            raise HTTPException(
                status_code=401,
                detail="Authentication failed"
            )
    
    async def extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request."""
        # Try Authorization header first
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            return authorization[7:]  # Remove "Bearer " prefix
        
        # Try cookie as fallback
        token = request.cookies.get("access_token")
        if token:
            return token
        
        # Try query parameter (for WebSocket)
        token = request.query_params.get("token")
        if token:
            return token
        
        return None
    
    def add_security_headers(self, response: Response) -> None:
        """Add security headers to response."""
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none';"
        )
        
        # Other security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Remove server information
        response.headers.pop("Server", None)