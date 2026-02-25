"""Collection utilities."""

from __future__ import annotations

from typing import Any, Callable, List, TypeVar

T = TypeVar("T")


def first(items: List[T], predicate: Callable[[T], bool]) -> T | None:
    """Get first item matching predicate."""
    for item in items:
        if predicate(item):
            return item
    return None


def last(items: List[T]) -> T | None:
    """Get last item."""
    return items[-1] if items else None


def find_index(items: List[T], predicate: Callable[[T], bool]) -> int:
    """Find index of first matching item."""
    for i, item in enumerate(items):
        if predicate(item):
            return i
    return -1


def partition(items: List[T], predicate: Callable[[T], bool]) -> tuple:
    """Partition items into two lists."""
    matched = []
    unmatched = []
    for item in items:
        if predicate(item):
            matched.append(item)
        else:
            unmatched.append(item)
    return matched, unmatched


def flatten(items: List[List[T]]) -> List[T]:
    """Flatten nested list."""
    result = []
    for item in items:
        if isinstance(item, list):
            result.extend(item)
        else:
            result.append(item)
    return result
