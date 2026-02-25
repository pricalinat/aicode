"""Lazy evaluation."""

from __future__ import annotations

from typing import Any, Callable


class Lazy:
    """Lazy evaluation wrapper."""
    
    def __init__(self, factory: Callable[[], Any]) -> None:
        self._factory = factory
        self._value = None
        self._evaluated = False
    
    @property
    def value(self) -> Any:
        if not self._evaluated:
            self._value = self._factory()
            self._evaluated = True
        return self._value


def lazy(fn: Callable) -> Callable:
    """Make function return Lazy."""
    def wrapper(*args, **kwargs):
        return Lazy(lambda: fn(*args, **kwargs))
    return wrapper
