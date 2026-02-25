"""Registry pattern."""

from __future__ import annotations

from typing import Any, Dict, Type


class Registry:
    """Generic registry."""
    
    def __init__(self) -> None:
        self._items: Dict[str, Any] = {}
    
    def register(self, name: str, item: Any) -> None:
        self._items[name] = item
    
    def get(self, name: str) -> Any:
        return self._items.get(name)
    
    def list(self) -> list:
        return list(self._items.keys())
    
    def unregister(self, name: str) -> bool:
        if name in self._items:
            del self._items[name]
            return True
        return False


class TypeRegistry(Registry):
    """Registry with type checking."""
    
    def register(self, name: str, item: Any, expected_type: Type = None) -> None:
        if expected_type and not isinstance(item, expected_type):
            raise TypeError(f"Expected {expected_type}, got {type(item)}")
        super().register(name, item)
