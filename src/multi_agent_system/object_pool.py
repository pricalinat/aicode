"""Object pool."""

from __future__ import annotations

from typing import Any


class ObjectPool:
    """Object pool."""
    
    def __init__(self, factory) -> None:
        self._factory = factory
        self._available = []
        self._in_use = set()
    
    def acquire(self) -> Any:
        if self._available:
            obj = self._available.pop()
        else:
            obj = self._factory()
        self._in_use.add(id(obj))
        return obj
    
    def release(self, obj) -> None:
        obj_id = id(obj)
        if obj_id in self._in_use:
            self._in_use.remove(obj_id)
            self._available.append(obj)
