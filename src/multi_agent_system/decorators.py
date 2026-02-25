"""Decorator utilities."""

from __future__ import annotations

import functools


def once(func):
    """Execute only once."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not wrapper.called:
            wrapper.called = True
            return func(*args, **kwargs)
    wrapper.called = False
    return wrapper


def retry_on_error(max_attempts=3):
    """Retry on error."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == max_attempts - 1:
                        raise
        return wrapper
    return decorator


def deprecated(message="This function is deprecated"):
    """Mark as deprecated."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import warnings
            warnings.warn(message, DeprecationWarning)
            return func(*args, **kwargs)
        return wrapper
    return decorator
