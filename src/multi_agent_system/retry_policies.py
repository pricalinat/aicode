"""Retry policies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class RetryPolicy:
    """Retry policy configuration."""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0


class ExponentialBackoff:
    """Exponential backoff retry strategy."""
    
    def __init__(self, policy: RetryPolicy) -> None:
        self._policy = policy
    
    def get_delay(self, attempt: int) -> float:
        import math
        delay = self._policy.initial_delay * (self._policy.backoff_factor ** attempt)
        return min(delay, self._policy.max_delay)


class LinearBackoff:
    """Linear backoff retry strategy."""
    
    def __init__(self, policy: RetryPolicy) -> None:
        self._policy = policy
    
    def get_delay(self, attempt: int) -> float:
        delay = self._policy.initial_delay + (attempt * self._policy.initial_delay)
        return min(delay, self._policy.max_delay)


class ConstantBackoff:
    """Constant backoff retry strategy."""
    
    def __init__(self, policy: RetryPolicy) -> None:
        self._policy = policy
    
    def get_delay(self, attempt: int) -> float:
        return self._policy.initial_delay
