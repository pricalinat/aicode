"""Data transformation utilities."""

from __future__ import annotations

from typing import Any, Dict, List


def transform_keys(data: dict, transformer: callable) -> dict:
    """Transform dictionary keys."""
    return {transformer(k): v for k, v in data.items()}


def transform_values(data: dict, transformer: callable) -> dict:
    """Transform dictionary values."""
    return {k: transformer(v) for k, v in data.items()}


def filter_dict(data: dict, predicate: callable) -> dict:
    """Filter dictionary by predicate."""
    return {k: v for k, v in data.items() if predicate(k, v)}


def group_by(items: list, key_fn: callable) -> dict:
    """Group items by key function."""
    result = {}
    for item in items:
        key = key_fn(item)
        if key not in result:
            result[key] = []
        result[key].append(item)
    return result


def unique(items: list, key_fn: callable = None) -> list:
    """Get unique items."""
    if key_fn is None:
        return list(dict.fromkeys(items))
    seen = set()
    result = []
    for item in items:
        key = key_fn(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def chunk(items: list, size: int) -> list:
    """Split list into chunks."""
    return [items[i:i + size] for i in range(0, len(items), size)]


def deep_get(data: dict, path: str, default: Any = None) -> Any:
    """Get nested value using dot notation."""
    keys = path.split(".")
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return default
        if current is None:
            return default
    return current


def deep_set(data: dict, path: str, value: Any) -> None:
    """Set nested value using dot notation."""
    keys = path.split(".")
    current = data
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value
