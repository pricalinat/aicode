"""Cache strategies for different scenarios."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class CacheStrategy(ABC):
    """Base cache strategy."""
    
    @abstractmethod
    def get(self, key: str) -> Any:
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int) -> None:
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        pass


class LRUCache:
    """Least Recently Used cache."""
    
    def __init__(self, max_size: int = 100) -> None:
        self._cache: dict = {}
        self._order: list = []
        self._max_size = max_size
    
    def get(self, key: str) -> Any:
        if key in self._cache:
            self._order.remove(key)
            self._order.append(key)
            return self._cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        if key in self._cache:
            self._order.remove(key)
        elif len(self._cache) >= self._max_size:
            oldest = self._order.pop(0)
            del self._cache[oldest]
        
        self._cache[key] = value
        self._order.append(key)
    
    def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            self._order.remove(key)
            return True
        return False


class TTLCache:
    """Time-to-live cache."""
    
    def __init__(self, default_ttl: int = 300) -> None:
        import time
        self._cache: dict = {}
        self._expiry: dict = {}
        self._default_ttl = default_ttl
        self._time = time
    
    def get(self, key: str) -> Any:
        if key not in self._cache:
            return None
        
        if self._time.time() > self._expiry[key]:
            del self._cache[key]
            del self._expiry[key]
            return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        import time
        ttl = ttl or self._default_ttl
        self._cache[key] = value
        self._expiry[key] = time.time() + ttl
    
    def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            del self._expiry[key]
            return True
        return False


class LazyCache:
    """Lazy loading cache with cache-aside pattern."""
    
    def __init__(self, strategy: CacheStrategy) -> None:
        self._strategy = strategy
    
    def get_or_compute(self, key: str, factory: Callable[[], T], ttl: int = 300) -> T:
        value = self._strategy.get(key)
        if value is not None:
            return value
        
        value = factory()
        self._strategy.set(key, value, ttl)
        return value
