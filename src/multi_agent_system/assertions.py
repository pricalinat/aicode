"""More utilities."""

from __future__ import annotations

def require(condition: bool, msg: str = "Requirement failed"):
    """Require condition."""
    if not condition:
        raise ValueError(msg)

def ensure(condition: bool, msg: str = "Ensure failed"):
    """Ensure condition."""
    if not condition:
        raise ValueError(msg)
