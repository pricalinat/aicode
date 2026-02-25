"""Context managers."""

from __future__ import annotations

import contextlib


@contextlib.contextmanager
def temp_override(obj: Any, attr: str, value: Any):
    """Temporarily override attribute."""
    original = getattr(obj, attr)
    setattr(obj, attr, value)
    try:
        yield
    finally:
        setattr(obj, attr, original)


@contextlib.contextmanager
def temp_env(**kwargs):
    """Temporarily set environment variables."""
    import os
    original = {}
    for k, v in kwargs.items():
        original[k] = os.environ.get(k)
        os.environ[k] = v
    try:
        yield
    finally:
        for k, v in original.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
