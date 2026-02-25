"""Cache Manager for LLM Agent Systems.

Provides intelligent caching for LLM responses, tool results, and intermediate data.
"""

from __future__ import annotations

import uuid
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class CacheLevel(Enum):
    """Cache storage levels."""
    MEMORY = "memory"
    DISK = "disk"
    DISTRIBUTED = "distributed"


class CacheStrategy(Enum):
    """Cache strategies."""
    LRU = "lru"           # Least recently used
    LFU = "lfu"           # Least frequently used
    TTL = "ttl"           # Time to live
    INVALIDATE = "invalidate"


@dataclass
class CacheEntry:
    """A cache entry."""
    key: str = ""
    value: Any = None
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0

    # Metadata
    ttl_seconds: int = 3600
    tags: list[str] = field(default_factory=list)

    # Stats
    size_bytes: int = 0

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl_seconds

    def hit(self) -> None:
        """Record a cache hit."""
        self.last_accessed = datetime.now()
        self.access_count += 1


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class CacheManager:
    """Intelligent cache manager.

    Features:
    - Multi-level caching (memory, disk)
    - LRU/LFU/TTL eviction
    - Tag-based invalidation
    - Statistics tracking
    """

    def __init__(
        self,
        max_memory_mb: int = 100,
        default_ttl_seconds: int = 3600,
        strategy: CacheStrategy = CacheStrategy.LRU,
    ) -> None:
        """Initialize cache manager.

        Args:
            max_memory_mb: Maximum memory in MB
            default_ttl_seconds: Default time to live
            strategy: Eviction strategy
        """
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl_seconds = default_ttl_seconds
        self.strategy = strategy

        self._cache: dict[str, CacheEntry] = {}
        self._stats = CacheStats()
        self._by_tag: dict[str, set[str]] = {}

    def _generate_key(self, data: Any) -> str:
        """Generate cache key from data."""
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        entry = self._cache.get(key)

        if entry is None:
            self._stats.misses += 1
            return None

        if entry.is_expired():
            self.invalidate(key)
            self._stats.misses += 1
            return None

        entry.hit()
        self._stats.hits += 1
        return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """Set value in cache."""
        # Check memory limit
        self._evict_if_needed()

        entry = CacheEntry(
            key=key,
            value=value,
            ttl_seconds=ttl_seconds or self.default_ttl_seconds,
            tags=tags or [],
        )

        # Estimate size
        try:
            entry.size_bytes = len(json.dumps(value))
        except:
            entry.size_bytes = 1000

        self._cache[key] = entry
        self._stats.size += entry.size_bytes

        # Index by tags
        for tag in entry.tags:
            if tag not in self._by_tag:
                self._by_tag[tag] = set()
            self._by_tag[tag].add(key)

    def invalidate(self, key: str) -> bool:
        """Invalidate a cache entry."""
        if key in self._cache:
            entry = self._cache[key]
            self._stats.size -= entry.size_bytes
            self._stats.evictions += 1

            # Remove from tag index
            for tag in entry.tags:
                if tag in self._by_tag:
                    self._by_tag[tag].discard(key)

            del self._cache[key]
            return True
        return False

    def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all entries with tag."""
        keys = self._by_tag.get(tag, set())
        count = 0
        for key in keys:
            if self.invalidate(key):
                count += 1
        return count

    def _evict_if_needed(self) -> None:
        """Evict entries if over memory limit."""
        while self._stats.size > self.max_memory_bytes and self._cache:
            if self.strategy == CacheStrategy.LRU:
                self._evict_lru()
            elif self.strategy == CacheStrategy.LFU:
                self._evict_lfu()
            else:
                self._evict_oldest()

    def _evict_lru(self) -> None:
        """Evict least recently used."""
        if not self._cache:
            return

        oldest = min(self._cache.values(), key=lambda e: e.last_accessed)
        self.invalidate(oldest.key)

    def _evict_lfu(self) -> None:
        """Evict least frequently used."""
        if not self._cache:
            return

        least_used = min(self._cache.values(), key=lambda e: e.access_count)
        self.invalidate(least_used.key)

    def _evict_oldest(self) -> None:
        """Evict oldest entry."""
        if not self._cache:
            return

        oldest = min(self._cache.values(), key=lambda e: e.created_at)
        self.invalidate(oldest.key)

    def clear(self) -> None:
        """Clear all cache."""
        self._cache.clear()
        self._by_tag.clear()
        self._stats = CacheStats()

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "entries": len(self._cache),
            "hits": self._stats.hits,
            "misses": self._stats.misses,
            "hit_rate": self._stats.hit_rate,
            "evictions": self._stats.evictions,
            "size_bytes": self._stats.size,
            "max_bytes": self.max_memory_bytes,
        }


# Global cache
_cache_manager: CacheManager | None = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
