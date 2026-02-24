"""Caching layer for improved performance."""

from __future__ import annotations

import hashlib
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

T = TypeVar("T")


@dataclass
class CacheEntry:
    """A cached entry with expiration."""
    key: str
    value: Any
    created_at: float
    expires_at: float
    hits: int = 0


class CacheBackend(ABC):
    """Abstract interface for cache backends."""
    
    @abstractmethod
    def get(self, key: str) -> CacheEntry | None:
        """Get a cached entry."""
        pass
    
    @abstractmethod
    def set(self, entry: CacheEntry) -> None:
        """Set a cached entry."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a cached entry."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cached entries."""
        pass
    
    @abstractmethod
    def keys(self) -> list[str]:
        """Get all cache keys."""
        pass


class InMemoryCache(CacheBackend):
    """In-memory cache implementation."""
    
    def __init__(self) -> None:
        self._cache: dict[str, CacheEntry] = {}
    
    def get(self, key: str) -> CacheEntry | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        
        # Check expiration
        if time.time() > entry.expires_at:
            del self._cache[key]
            return None
        
        # Update hits
        entry.hits += 1
        return entry
    
    def set(self, entry: CacheEntry) -> None:
        self._cache[entry.key] = entry
    
    def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        self._cache.clear()
    
    def keys(self) -> list[str]:
        return list(self._cache.keys())


class Cache:
    """Cache manager with TTL support."""
    
    def __init__(
        self,
        backend: CacheBackend | None = None,
        default_ttl: int = 300,  # 5 minutes
    ) -> None:
        self.backend = backend or InMemoryCache()
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Any:
        """Get a value from cache."""
        entry = self.backend.get(key)
        if entry:
            return entry.value
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """Set a value in cache."""
        ttl = ttl if ttl is not None else self.default_ttl
        now = time.time()
        
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=now,
            expires_at=now + ttl,
        )
        self.backend.set(entry)
    
    def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        return self.backend.delete(key)
    
    def clear(self) -> None:
        """Clear all cached values."""
        self.backend.clear()
    
    def get_or_compute(
        self,
        key: str,
        compute_fn: Callable[[], T],
        ttl: int | None = None,
    ) -> T:
        """Get from cache or compute if not present."""
        value = self.get(key)
        if value is not None:
            return value
        
        # Compute the value
        value = compute_fn()
        
        # Store in cache
        self.set(key, value, ttl)
        
        return value
    
    def generate_key(self, *args: Any, **kwargs: Any) -> str:
        """Generate a cache key from arguments."""
        # Create a stable representation
        data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern."""
        count = 0
        for key in self.backend.keys():
            if pattern in key:
                if self.backend.delete(key):
                    count += 1
        return count


# Global cache instance
_global_cache: Cache | None = None


def get_cache() -> Cache:
    """Get the global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = Cache()
    return _global_cache


def set_cache(cache: Cache) -> None:
    """Set the global cache instance."""
    global _global_cache
    _global_cache = cache


def cache_result(ttl: int = 300):
    """Decorator to cache function results.
    
    Usage:
        @cache_result(ttl=60)
        def expensive_function(arg1, arg2):
            # ...
            return result
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            cache = get_cache()
            key = f"{func.__name__}:{cache.generate_key(*args, **kwargs)}"
            return cache.get_or_compute(key, lambda: func(*args, **kwargs), ttl)
        return wrapper  # type: ignore
    return decorator


class CachedAgentMixin:
    """Mixin to add caching to agents."""
    
    def __init__(self) -> None:
        self.cache = get_cache()
    
    def _get_cache_key(self, message: Any) -> str:
        """Generate cache key for a message."""
        data = json.dumps({
            "task_type": message.task_type,
            "content": message.content,
        }, sort_keys=True, default=str)
        return hashlib.sha256(data.encode()).hexdigest()[:16]
