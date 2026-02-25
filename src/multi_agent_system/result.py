"""Result type."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


class Ok(Generic[T]):
    """Ok result."""
    def __init__(self, value: T) -> None:
        self.value = value


class Err(Generic[E]):
    """Error result."""
    def __init__(self, error: E) -> None:
        self.error = error


Result = Ok[T] | Err[E]
