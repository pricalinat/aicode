"""Final utilities."""

from __future__ import annotations

def freeze(obj):
    """Freeze object."""
    return frozenset(obj.items()) if hasattr(obj, "items") else frozenset(obj)

def unfreeze(obj):
    """Unfreeze object."""
    return dict(obj) if isinstance(obj, frozenset) else obj
