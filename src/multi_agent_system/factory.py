"""Base factory."""

from __future__ import annotations

from typing import Any, Dict


class Factory:
    """Generic factory."""
    
    def __init__(self) -> None:
        self._creators: Dict[str, Any] = {}
    
    def register(self, name: str, creator: Any) -> None:
        self._creators[name] = creator
    
    def create(self, name: str, *args, **kwargs) -> Any:
        creator = self._creators.get(name)
        if not creator:
            raise ValueError(f"Unknown creator: {name}")
        return creator(*args, **kwargs)
    
    def list_creators(self) -> list:
        return list(self._creators.keys())
