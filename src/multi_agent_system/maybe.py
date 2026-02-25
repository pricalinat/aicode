"""Maybe type."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

T = TypeVar("T")


class Maybe(Generic[T]):
    """Maybe monad."""
    
    def __init__(self, value: T | None) -> None:
        self._value = value
    
    @staticmethod
    def just(value: T) -> "Maybe[T]":
        return Maybe(value)
    
    @staticmethod
    def nothing() -> "Maybe[T]":
        return Maybe(None)
    
    def map(self, fn) -> "Maybe":
        if self._value is None:
            return self
        return Maybe(fn(self._value))
    
    def flat_map(self, fn) -> "Maybe":
        if self._value is None:
            return self
        return fn(self._value)
    
    def get_or_else(self, default: T) -> T:
        return self._value if self._value is not None else default
