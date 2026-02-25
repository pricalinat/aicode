"""Alias utilities."""

from __future__ import annotations

def alias(name: str):
    """Create alias for function."""
    def decorator(fn):
        fn.__alias__ = name
        return fn
    return decorator
