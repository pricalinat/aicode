"""Lock utilities for concurrency control."""

from __future__ import annotations

import asyncio
from typing import Any


class AsyncLock:
    """Async lock with context manager."""
    
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
    
    async def __aenter__(self) -> None:
        await self._lock.acquire()
    
    async def __aexit__(self, *args: Any) -> None:
        self._lock.release()


class Lock:
    """Sync lock with context manager."""
    
    def __init__(self) -> None:
        import threading
        self._lock = threading.Lock()
    
    def __enter__(self) -> None:
        self._lock.acquire()
    
    def __exit__(self, *args: Any) -> None:
        self._lock.release()
