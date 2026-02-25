"""Memoization."""

from __future__ import annotations

from functools import lru_cache

memoize = lru_cache(maxsize=None)
