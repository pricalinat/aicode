"""Router for agent selection."""

from __future__ import annotations

from typing import Any, Callable, Dict, List


class Router:
    """Simple router for agent selection."""
    
    def __init__(self) -> None:
        self._routes: Dict[str, Callable] = {}
        self._default: Callable | None = None
    
    def add_route(self, path: str, handler: Callable) -> None:
        self._routes[path] = handler
    
    def set_default(self, handler: Callable) -> None:
        self._default = handler
    
    def route(self, path: str, *args: Any, **kwargs: Any) -> Any:
        handler = self._routes.get(path, self._default)
        if handler:
            return handler(*args, **kwargs)
        raise ValueError(f"No route for {path}")
    
    def list_routes(self) -> List[str]:
        return list(self._routes.keys())


class WeightedRouter:
    """Router with weighted selection."""
    
    def __init__(self) -> None:
        self._handlers: Dict[str, float] = {}
    
    def add_handler(self, name: str, weight: float) -> None:
        self._handlers[name] = weight
    
    def select(self) -> str:
        import random
        total = sum(self._handlers.values())
        r = random.random() * total
        cumulative = 0
        for name, weight in self._handlers.items():
            cumulative += weight
            if r <= cumulative:
                return name
        return list(self._handlers.keys())[0]
