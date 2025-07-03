"""
Rate limiting middleware for WebConsole backend.
"""

import time
import asyncio
from typing import Dict, Tuple, Optional
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter implementation."""
    
    def __init__(self, rate: int, period: int, burst: int = None):
        """
        Initialize rate limiter.
        
        Args:
            rate: Number of requests per period
            period: Time period in seconds
            burst: Maximum burst size (defaults to rate)
        """
        self.rate = rate
        self.period = period
        self.burst = burst or rate
        self.tokens: Dict[str, Tuple[float, int]] = {}
        self.lock = asyncio.Lock()
    
    async def is_allowed(self, key: str) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed for the given key.
        
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        async with self.lock:
            now = time.time()
            
            if key not in self.tokens:
                # First request for this key
                self.tokens[key] = (now, self.burst - 1)
                return True, {
                    "remaining": self.burst - 1,
                    "reset_time": int(now + self.period),
                    "retry_after": None
                }
            
            last_update, tokens = self.tokens[key]
            
            # Calculate tokens to add based on time passed
            time_passed = now - last_update
            tokens_to_add = int(time_passed * self.rate / self.period)
            
            # Update token count
            new_tokens = min(self.burst, tokens + tokens_to_add)
            
            if new_tokens > 0:
                # Request is allowed
                self.tokens[key] = (now, new_tokens - 1)
                return True, {
                    "remaining": new_tokens - 1,
                    "reset_time": int(now + self.period),
                    "retry_after": None
                }
            else:
                # Request is rate limited
                retry_after = self.period / self.rate
                return False, {
                    "remaining": 0,
                    "reset_time": int(now + self.period),
                    "retry_after": int(retry_after)
                }
    
    def cleanup_old_entries(self, max_age: int = 3600):
        """Remove old entries to prevent memory leaks."""
        now = time.time()
        cutoff = now - max_age
        
        keys_to_remove = [
            key for key, (last_update, _) in self.tokens.items()
            if last_update < cutoff
        ]
        
        for key in keys_to_remove:
            del self.tokens[key]


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app):
        super().__init__(app)
        
        # Parse rate limit settings
        self.default_limiter = self._parse_rate_limit(settings.rate_limit.default)
        self.auth_limiter = self._parse_rate_limit(settings.rate_limit.authenticated)
        
        # Paths exempt from rate limiting
        self.exempt_paths = {
            "/health",
            "/metrics"
        }
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_task())
    
    def _parse_rate_limit(self, rate_string: str) -> RateLimiter:
        """Parse rate limit string like '100/minute' into RateLimiter."""
        try:
            rate_part, period_part = rate_string.split('/')
            rate = int(rate_part)
            
            period_mapping = {
                'second': 1,
                'minute': 60,
                'hour': 3600,
                'day': 86400
            }
            
            period = period_mapping.get(period_part, 60)  # Default to minute
            burst = min(rate * 2, settings.rate_limit.burst)  # Allow burst
            
            return RateLimiter(rate, period, burst)
        except Exception as e:
            logger.warning(f"Invalid rate limit format '{rate_string}': {e}")
            # Fallback to default
            return RateLimiter(100, 60, 50)
    
    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiting middleware."""
        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Determine rate limiter based on authentication
        user_id = getattr(request.state, "user_id", None)
        limiter = self.auth_limiter if user_id else self.default_limiter
        
        # Create rate limit key
        key = self._get_rate_limit_key(request, user_id)
        
        # Check rate limit
        is_allowed, rate_info = await limiter.is_allowed(key)
        
        if not is_allowed:
            # Add rate limit headers
            headers = {
                "X-RateLimit-Limit": str(limiter.rate),
                "X-RateLimit-Remaining": str(rate_info["remaining"]),
                "X-RateLimit-Reset": str(rate_info["reset_time"]),
                "Retry-After": str(rate_info["retry_after"])
            }
            
            logger.warning(
                f"Rate limit exceeded for {key} "
                f"(Path: {request.url.path}, Method: {request.method})"
            )
            
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers=headers
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful response
        response.headers["X-RateLimit-Limit"] = str(limiter.rate)
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset_time"])
        
        return response
    
    def _get_rate_limit_key(self, request: Request, user_id: Optional[str]) -> str:
        """Generate rate limit key for request."""
        if user_id:
            # Use user ID for authenticated requests
            return f"user:{user_id}"
        else:
            # Use IP address for anonymous requests
            client_ip = self._get_client_ip(request)
            return f"ip:{client_ip}"
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    async def _cleanup_task(self):
        """Background task to cleanup old rate limit entries."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                self.default_limiter.cleanup_old_entries()
                self.auth_limiter.cleanup_old_entries()
                logger.debug("Rate limiter cleanup completed")
            except Exception as e:
                logger.error(f"Rate limiter cleanup error: {e}")