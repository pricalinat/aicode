"""Rate limiting per user/IP."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class RateLimitEntry:
    count: int
    reset_time: float


class UserRateLimiter:
    """Rate limiter per user/IP."""
    
    def __init__(self, rate: int = 60, window: float = 60.0) -> None:
        self._rate = rate
        self._window = window
        self._limits: Dict[str, RateLimitEntry] = {}
    
    def check(self, identifier: str) -> bool:
        now = time.time()
        
        if identifier not in self._limits:
            self._limits[identifier] = RateLimitEntry(1, now + self._window)
            return True
        
        entry = self._limits[identifier]
        
        if now > entry.reset_time:
            entry.count = 1
            entry.reset_time = now + self._window
            return True
        
        if entry.count >= self._rate:
            return False
        
        entry.count += 1
        return True
    
    def get_remaining(self, identifier: str) -> int:
        if identifier not in self._limits:
            return self._rate
        
        entry = self._limits[identifier]
        now = time.time()
        
        if now > entry.reset_time:
            return self._rate
        
        return max(0, self._rate - entry.count)
    
    def get_reset_time(self, identifier: str) -> float | None:
        if identifier not in self._limits:
            return None
        return self._limits[identifier].reset_time


class SlidingWindowLimiter:
    """Sliding window rate limiter."""
    
    def __init__(self, rate: int = 60, window: float = 60.0) -> None:
        self._rate = rate
        self._window = window
        self._requests: Dict[str, list] = {}
    
    def check(self, identifier: str) -> bool:
        now = time.time()
        
        if identifier not in self._requests:
            self._requests[identifier] = []
        
        requests = self._requests[identifier]
        requests = [t for t in requests if now - t < self._window]
        self._requests[identifier] = requests
        
        if len(requests) >= self._rate:
            return False
        
        requests.append(now)
        return True
