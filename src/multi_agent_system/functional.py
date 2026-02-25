"""Functional programming utilities."""

from __future__ import annotations

from typing import Any, Callable, TypeVar

T = TypeVar("T")
R = TypeVar("R")


def compose(*functions: Callable) -> Callable:
    """Compose functions."""
    def composed(x: Any) -> Any:
        result = x
        for fn in reversed(functions):
            result = fn(result)
        return result
    return composed


def pipe(value: Any, *functions: Callable) -> Any:
    """Pipe value through functions."""
    result = value
    for fn in functions:
        result = fn(result)
    return result


def memoize(fn: Callable) -> Callable:
    """Memoize function."""
    cache = {}
    def wrapper(*args: Any) -> Any:
        key = str(args)
        if key not in cache:
            cache[key] = fn(*args)
        return cache[key]
    return wrapper


def curry(fn: Callable) -> Callable:
    """Curry function."""
    def curried(*args: Any) -> Any:
        if len(args) >= fn.__code__.co_argcount:
            return fn(*args)
        return lambda *more: curried(*(args + more))
    return curried
