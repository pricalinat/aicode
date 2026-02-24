"""Batch processing for handling multiple requests."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, List, TypeVar

T = TypeVar("T")


@dataclass
class BatchResult:
    """Result of batch processing."""
    total: int
    successful: int
    failed: int
    results: List[Any] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class BatchProcessor:
    """Process multiple items in batches."""
    
    def __init__(
        self,
        batch_size: int = 10,
        max_concurrency: int = 5,
    ) -> None:
        self.batch_size = batch_size
        self.max_concurrency = max_concurrency
    
    def process(
        self,
        items: List[T],
        processor: Callable[[T], Any],
    ) -> BatchResult:
        """Process items in batches synchronously."""
        results = []
        errors = []
        
        # Process in batches
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            
            for item in batch:
                try:
                    result = processor(item)
                    results.append(result)
                except Exception as e:
                    errors.append(str(e))
        
        return BatchResult(
            total=len(items),
            successful=len(results),
            failed=len(errors),
            results=results,
            errors=errors,
        )
    
    async def process_async(
        self,
        items: List[T],
        processor: Callable[[T], Any],
    ) -> BatchResult:
        """Process items in batches asynchronously."""
        results = []
        errors = []
        semaphore = asyncio.Semaphore(self.max_concurrency)
        
        async def process_with_semaphore(item: T) -> None:
            async with semaphore:
                try:
                    if asyncio.iscoroutinefunction(processor):
                        result = await processor(item)
                    else:
                        result = processor(item)
                    results.append(result)
                except Exception as e:
                    errors.append(str(e))
        
        await asyncio.gather(*[process_with_semaphore(item) for item in items], return_exceptions=True)
        
        return BatchResult(
            total=len(items),
            successful=len(results),
            failed=len(errors),
            results=results,
            errors=errors,
        )


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(
        self,
        rate: float,  # requests per second
        burst: int = 1,
    ) -> None:
        self.rate = rate
        self.burst = burst
        self._tokens = float(burst)
        self._last_update = asyncio.get_event_loop().time()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Acquire a token, waiting if necessary."""
        async with self._lock:
            while self._tokens < 1:
                # Calculate how long to wait
                deficit = 1 - self._tokens
                wait_time = deficit / self.rate
                
                # Update tokens
                now = asyncio.get_event_loop().time()
                elapsed = now - self._last_update
                self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
                self._last_update = now
                
                if self._tokens < 1:
                    await asyncio.sleep(wait_time)
            
            self._tokens -= 1
            return True
    
    def try_acquire(self) -> bool:
        """Try to acquire a token without waiting."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_update
        self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
        self._last_update = now
        
        if self._tokens >= 1:
            self._tokens -= 1
            return True
        return False


class RateLimiterGroup:
    """Group of rate limiters for different resources."""
    
    def __init__(self) -> None:
        self._limiters: dict[str, RateLimiter] = {}
    
    def get_limiter(self, name: str, rate: float = 1.0, burst: int = 1) -> RateLimiter:
        """Get or create a rate limiter."""
        if name not in self._limiters:
            self._limiters[name] = RateLimiter(rate, burst)
        return self._limiters[name]
    
    async def acquire(self, name: str) -> bool:
        """Acquire from a named limiter."""
        limiter = self._limiters.get(name)
        if limiter:
            return await limiter.acquire()
        return True


# Global rate limiter group
_rate_limiter_group: RateLimiterGroup | None = None


def get_rate_limiter_group() -> RateLimiterGroup:
    """Get the global rate limiter group."""
    global _rate_limiter_group
    if _rate_limiter_group is None:
        _rate_limiter_group = RateLimiterGroup()
    return _rate_limiter_group
