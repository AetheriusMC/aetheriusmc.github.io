"""
Cache service implementation using Redis.
"""

import json
import pickle
from typing import Any, Optional, Union, Dict, List
from datetime import timedelta
import asyncio
import logging
from abc import ABC, abstractmethod

import redis.asyncio as redis
from redis.asyncio import Redis

from ..core.config import settings
from ..core.container import singleton

logger = logging.getLogger(__name__)


class ICacheService(ABC):
    """Cache service interface."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    @abstractmethod
    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache keys matching pattern."""
        pass


@singleton
class CacheService(ICacheService):
    """Redis-based cache service implementation."""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
        self.connected = False
        self.default_ttl = settings.redis.default_ttl
        self.key_prefix = "webconsole:"
        self._connection_pool = None
        self._memory_cache: Dict[str, Any] = {}  # Fallback memory cache
    
    async def initialize(self) -> None:
        """Initialize Redis connection."""
        try:
            # Create connection pool
            self._connection_pool = redis.ConnectionPool.from_url(
                settings.redis.cache_url,
                encoding="utf-8",
                decode_responses=False,  # We handle encoding manually
                max_connections=20,
                retry_on_timeout=True
            )
            
            # Create Redis client
            self.redis = redis.Redis(connection_pool=self._connection_pool)
            
            # Test connection
            await self.redis.ping()
            self.connected = True
            
            logger.info("Cache service initialized successfully")
            
        except Exception as e:
            logger.warning(f"Redis not available, falling back to memory cache: {e}")
            self.connected = False
            self.redis = None
            # Initialize in-memory cache as fallback
            self._memory_cache = {}
            logger.info("Cache service initialized with memory fallback")
    
    async def dispose(self) -> None:
        """Dispose cache service."""
        if self.redis:
            await self.redis.close()
        if self._connection_pool:
            await self._connection_pool.disconnect()
        self.connected = False
        logger.info("Cache service disposed")
    
    def _make_key(self, key: str) -> str:
        """Create prefixed cache key."""
        return f"{self.key_prefix}{key}"
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage."""
        if isinstance(value, (str, int, float, bool)):
            return json.dumps(value).encode('utf-8')
        else:
            # Use pickle for complex objects
            return pickle.dumps(value)
    
    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            # Try JSON first (for simple types)
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            return pickle.loads(data)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if self.connected and self.redis:
            try:
                cache_key = self._make_key(key)
                data = await self.redis.get(cache_key)
                
                if data is None:
                    return None
                
                return self._deserialize_value(data)
                
            except Exception as e:
                logger.error(f"Redis cache get error for key '{key}': {e}")
                # Fall back to memory cache
        
        # Use memory cache as fallback
        cache_key = self._make_key(key)
        return self._memory_cache.get(cache_key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        if self.connected and self.redis:
            try:
                cache_key = self._make_key(key)
                serialized_value = self._serialize_value(value)
                expire_time = ttl or self.default_ttl
                
                await self.redis.setex(cache_key, expire_time, serialized_value)
                return True
                
            except Exception as e:
                logger.error(f"Redis cache set error for key '{key}': {e}")
                # Fall back to memory cache
        
        # Use memory cache as fallback
        cache_key = self._make_key(key)
        self._memory_cache[cache_key] = value
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        cache_key = self._make_key(key)
        deleted = False
        
        if self.connected and self.redis:
            try:
                result = await self.redis.delete(cache_key)
                deleted = result > 0
            except Exception as e:
                logger.error(f"Redis cache delete error for key '{key}': {e}")
        
        # Also delete from memory cache
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]
            deleted = True
            
        return deleted
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        cache_key = self._make_key(key)
        
        if self.connected and self.redis:
            try:
                result = await self.redis.exists(cache_key)
                return result > 0
            except Exception as e:
                logger.error(f"Redis cache exists error for key '{key}': {e}")
        
        # Check memory cache
        return cache_key in self._memory_cache
    
    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache keys matching pattern."""
        deleted = 0
        
        if self.connected and self.redis:
            try:
                if pattern:
                    search_pattern = self._make_key(pattern)
                else:
                    search_pattern = f"{self.key_prefix}*"
                
                # Get all matching keys
                keys = []
                async for key in self.redis.scan_iter(match=search_pattern):
                    keys.append(key)
                
                if keys:
                    deleted += await self.redis.delete(*keys)
                    
            except Exception as e:
                logger.error(f"Redis cache clear error with pattern '{pattern}': {e}")
        
        # Clear from memory cache
        if pattern:
            search_pattern = self._make_key(pattern).replace("*", "")
            keys_to_delete = [k for k in self._memory_cache.keys() if k.startswith(search_pattern)]
        else:
            keys_to_delete = [k for k in self._memory_cache.keys() if k.startswith(self.key_prefix)]
        
        for key in keys_to_delete:
            del self._memory_cache[key]
            deleted += 1
        
        if deleted > 0:
            logger.info(f"Cleared {deleted} cache keys with pattern '{pattern}'")
        
        return deleted
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment numeric value in cache."""
        cache_key = self._make_key(key)
        
        if self.connected and self.redis:
            try:
                result = await self.redis.incrby(cache_key, amount)
                return result
            except Exception as e:
                logger.error(f"Redis cache increment error for key '{key}': {e}")
        
        # Use memory cache
        current = self._memory_cache.get(cache_key, 0)
        if isinstance(current, (int, float)):
            new_value = current + amount
            self._memory_cache[cache_key] = new_value
            return new_value
        
        return None
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for key."""
        if not self.connected:
            return False
        
        try:
            cache_key = self._make_key(key)
            result = await self.redis.expire(cache_key, ttl)
            return result
            
        except Exception as e:
            logger.error(f"Cache expire error for key '{key}': {e}")
            return False
    
    async def ttl(self, key: str) -> Optional[int]:
        """Get time to live for key."""
        if not self.connected:
            return None
        
        try:
            cache_key = self._make_key(key)
            result = await self.redis.ttl(cache_key)
            return result if result >= 0 else None
            
        except Exception as e:
            logger.error(f"Cache TTL error for key '{key}': {e}")
            return None
    
    # Hash operations
    async def hset(self, key: str, field: str, value: Any) -> bool:
        """Set hash field."""
        if not self.connected:
            return False
        
        try:
            cache_key = self._make_key(key)
            serialized_value = self._serialize_value(value)
            result = await self.redis.hset(cache_key, field, serialized_value)
            return result > 0
            
        except Exception as e:
            logger.error(f"Cache hset error for key '{key}', field '{field}': {e}")
            return False
    
    async def hget(self, key: str, field: str) -> Optional[Any]:
        """Get hash field."""
        if not self.connected:
            return None
        
        try:
            cache_key = self._make_key(key)
            data = await self.redis.hget(cache_key, field)
            
            if data is None:
                return None
            
            return self._deserialize_value(data)
            
        except Exception as e:
            logger.error(f"Cache hget error for key '{key}', field '{field}': {e}")
            return None
    
    async def hgetall(self, key: str) -> Dict[str, Any]:
        """Get all hash fields."""
        if not self.connected:
            return {}
        
        try:
            cache_key = self._make_key(key)
            data = await self.redis.hgetall(cache_key)
            
            result = {}
            for field, value in data.items():
                if isinstance(field, bytes):
                    field = field.decode('utf-8')
                result[field] = self._deserialize_value(value)
            
            return result
            
        except Exception as e:
            logger.error(f"Cache hgetall error for key '{key}': {e}")
            return {}
    
    # List operations
    async def lpush(self, key: str, *values: Any) -> int:
        """Push values to left of list."""
        if not self.connected:
            return 0
        
        try:
            cache_key = self._make_key(key)
            serialized_values = [self._serialize_value(v) for v in values]
            result = await self.redis.lpush(cache_key, *serialized_values)
            return result
            
        except Exception as e:
            logger.error(f"Cache lpush error for key '{key}': {e}")
            return 0
    
    async def rpop(self, key: str) -> Optional[Any]:
        """Pop value from right of list."""
        if not self.connected:
            return None
        
        try:
            cache_key = self._make_key(key)
            data = await self.redis.rpop(cache_key)
            
            if data is None:
                return None
            
            return self._deserialize_value(data)
            
        except Exception as e:
            logger.error(f"Cache rpop error for key '{key}': {e}")
            return None
    
    async def llen(self, key: str) -> int:
        """Get list length."""
        if not self.connected:
            return 0
        
        try:
            cache_key = self._make_key(key)
            result = await self.redis.llen(cache_key)
            return result
            
        except Exception as e:
            logger.error(f"Cache llen error for key '{key}': {e}")
            return 0


# Caching decorators
def cached(ttl: int = None, key_prefix: str = ""):
    """Decorator for caching function results."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            import hashlib
            
            key_parts = [key_prefix, func.__name__]
            if args:
                key_parts.append(str(hash(args)))
            if kwargs:
                key_parts.append(str(hash(tuple(sorted(kwargs.items())))))
            
            cache_key = ":".join(filter(None, key_parts))
            
            # Try to get from cache first
            from ..core.container import get_container
            container = get_container()
            cache_service = await container.get_service(CacheService)
            
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            await cache_service.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def cache_invalidate(key_pattern: str):
    """Decorator for invalidating cache on function execution."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # Invalidate cache
            from ..core.container import get_container
            container = get_container()
            cache_service = await container.get_service(CacheService)
            await cache_service.clear(key_pattern)
            
            return result
        
        return wrapper
    return decorator