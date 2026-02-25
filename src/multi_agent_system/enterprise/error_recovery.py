"""Agent Error Handling and Recovery System.

Provides comprehensive error handling, recovery strategies, and fallback mechanisms
for multi-agent LLM systems.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories."""
    TIMEOUT = "timeout"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    NETWORK = "network"
    RESOURCE = "resource"
    EXTERNAL_API = "external_api"
    INTERNAL = "internal"
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    """Recovery strategies."""
    RETRY = "retry"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    FALLBACK = "fallback"
    DEGRADED = "degraded"
    ESCALATE = "escalate"
    ABORT = "abort"


@dataclass
class ErrorRecord:
    """Record of an error occurrence."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    error_id: str = ""  # Unique error identifier
    category: ErrorCategory = ErrorCategory.UNKNOWN
    severity: ErrorSeverity = ErrorSeverity.ERROR

    # Error details
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    # Context
    source: str = ""  # Where error occurred
    operation: str = ""  # What operation was being performed
    context: dict[str, Any] = field(default_factory=dict)

    # Recovery
    strategy: RecoveryStrategy | None = None
    recovery_attempted: bool = False
    recovery_successful: bool | None = None

    # Timing
    occurred_at: datetime = field(default_factory=datetime.now)
    resolved_at: datetime | None = None
    recovery_time_ms: int = 0


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    initial_delay_ms: int = 1000
    max_delay_ms: int = 30000
    backoff_multiplier: float = 2.0
    jitter: bool = True

    def get_delay(self, attempt: int) -> int:
        """Calculate delay for given attempt."""
        import random

        delay = min(
            self.initial_delay_ms * (self.backoff_multiplier ** attempt),
            self.max_delay_ms
        )

        if self.jitter:
            delay = int(delay * (0.5 + random.random() * 0.5))

        return delay


@dataclass
class FallbackConfig:
    """Configuration for fallback behavior."""
    fallback_handler: Callable | None = None
    fallback_value: Any = None
    max_fallback_attempts: int = 1


class ErrorClassifier:
    """Classifies errors and suggests recovery strategies."""

    # Error pattern matching
    PATTERNS = {
        ErrorCategory.TIMEOUT: [
            "timeout", "timed out", "took too long", "deadline exceeded",
        ],
        ErrorCategory.AUTHENTICATION: [
            "auth", "unauthorized", "invalid credentials", "token expired",
        ],
        ErrorCategory.AUTHORIZATION: [
            "permission denied", "forbidden", "access denied", "not authorized",
        ],
        ErrorCategory.VALIDATION: [
            "invalid", "validation failed", "bad request", "malformed",
        ],
        ErrorCategory.NETWORK: [
            "network", "connection", "dns", "refused", "unreachable",
        ],
        ErrorCategory.RESOURCE: [
            "quota", "rate limit", "out of", "exceeded", "insufficient",
        ],
        ErrorCategory.EXTERNAL_API: [
            "api error", "external", "third party", "service unavailable",
        ],
    }

    def __init__(self) -> None:
        """Initialize error classifier."""
        self._severity_weights = {
            ErrorSeverity.CRITICAL: 1.0,
            ErrorSeverity.ERROR: 0.7,
            ErrorSeverity.WARNING: 0.3,
            ErrorSeverity.INFO: 0.1,
        }

    def classify(self, error: Exception | str) -> tuple[ErrorCategory, ErrorSeverity]:
        """Classify an error.

        Args:
            error: Exception or error message

        Returns:
            Tuple of (category, severity)
        """
        # Convert to string
        error_str = str(error).lower()

        # Match patterns
        category = ErrorCategory.UNKNOWN
        for cat, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if pattern in error_str:
                    category = cat
                    break
            if category != ErrorCategory.UNKNOWN:
                break

        # Determine severity
        severity = ErrorSeverity.ERROR
        if "critical" in error_str or "fatal" in error_str:
            severity = ErrorSeverity.CRITICAL
        elif "warning" in error_str or "warn" in error_str:
            severity = ErrorSeverity.WARNING

        return category, severity

    def suggest_strategy(
        self,
        category: ErrorCategory,
        severity: ErrorSeverity,
        attempt: int,
        max_attempts: int,
    ) -> RecoveryStrategy:
        """Suggest recovery strategy based on error and attempt.

        Args:
            category: Error category
            severity: Error severity
            attempt: Current attempt number
            max_attempts: Maximum attempts

        Returns:
            Recommended recovery strategy
        """
        # Critical errors should escalate or abort
        if severity == ErrorSeverity.CRITICAL:
            if attempt >= max_attempts - 1:
                return RecoveryStrategy.ESCALATE
            return RecoveryStrategy.RETRY_WITH_BACKOFF

        # Category-specific strategies
        if category == ErrorCategory.TIMEOUT:
            return RecoveryStrategy.RETRY_WITH_BACKOFF
        elif category == ErrorCategory.AUTHENTICATION:
            if attempt >= 1:
                return RecoveryStrategy.ESCALATE
            return RecoveryStrategy.RETRY
        elif category == ErrorCategory.AUTHORIZATION:
            return RecoveryStrategy.ESCALATE
        elif category == ErrorCategory.VALIDATION:
            return RecoveryStrategy.FALLBACK
        elif category == ErrorCategory.RESOURCE:
            return RecoveryStrategy.DEGRADED
        elif category == ErrorCategory.NETWORK:
            return RecoveryStrategy.RETRY_WITH_BACKOFF

        # Default: retry with backoff
        if attempt >= max_attempts - 1:
            return RecoveryStrategy.FALLBACK
        return RecoveryStrategy.RETRY_WITH_BACKOFF


class ErrorRecovery:
    """Error recovery system with retry, fallback, and degradation strategies.

    Features:
    - Configurable retry with exponential backoff
    - Fallback handlers
    - Graceful degradation
    - Error tracking and analysis
    """

    def __init__(
        self,
        retry_config: RetryConfig | None = None,
        fallback_config: FallbackConfig | None = None,
    ) -> None:
        """Initialize error recovery.

        Args:
            retry_config: Retry configuration
            fallback_config: Fallback configuration
        """
        self.retry_config = retry_config or RetryConfig()
        self.fallback_config = fallback_config or FallbackConfig()
        self.classifier = ErrorClassifier()

        # Error tracking
        self._errors: list[ErrorRecord] = []
        self._error_counts: dict[str, int] = {}

    async def execute_with_recovery(
        self,
        operation: Callable,
        *args,
        **kwargs,
    ) -> tuple[Any, ErrorRecord | None]:
        """Execute operation with error recovery.

        Args:
            operation: Async function to execute
            *args, **kwargs: Arguments to pass to operation

        Returns:
            Tuple of (result, error_record)
        """
        max_attempts = self.retry_config.max_attempts
        last_error = None

        for attempt in range(max_attempts):
            try:
                # Execute operation
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)

                # Success
                return result, None

            except Exception as e:
                last_error = e

                # Classify error
                category, severity = self.classifier.classify(e)

                # Create error record
                record = ErrorRecord(
                    error_id=str(uuid.uuid4())[:8],
                    category=category,
                    severity=severity,
                    message=str(e),
                    source=operation.__name__ if hasattr(operation, "__name__") else "unknown",
                    operation=operation.__name__ if hasattr(operation, "__name__") else "unknown",
                )

                # Determine strategy
                strategy = self.classifier.suggest_strategy(
                    category, severity, attempt, max_attempts
                )
                record.strategy = strategy

                # Apply recovery
                if strategy == RecoveryStrategy.RETRY:
                    continue
                elif strategy == RecoveryStrategy.RETRY_WITH_BACKOFF:
                    delay = self.retry_config.get_delay(attempt)
                    await asyncio.sleep(delay / 1000)
                    continue
                elif strategy == RecoveryStrategy.FALLBACK:
                    if self.fallback_config.fallback_handler:
                        try:
                            result = self.fallback_config.fallback_handler()
                            record.recovery_successful = True
                            return result, record
                        except Exception:
                            pass
                    if self.fallback_config.fallback_value is not None:
                        record.recovery_successful = True
                        return self.fallback_config.fallback_value, record
                elif strategy == RecoveryStrategy.ESCALATE:
                    record.recovery_attempted = True
                    record.recovery_successful = False
                    self._errors.append(record)
                    raise e
                elif strategy == RecoveryStrategy.ABORT:
                    record.recovery_attempted = True
                    self._errors.append(record)
                    raise e

        # All retries exhausted
        record = ErrorRecord(
            error_id=str(uuid.uuid4())[:8],
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.ERROR,
            message=str(last_error),
            strategy=RecoveryStrategy.ABORT,
            recovery_attempted=True,
            recovery_successful=False,
        )
        self._errors.append(record)
        raise last_error

    def get_error_statistics(self) -> dict[str, Any]:
        """Get error statistics."""
        if not self._errors:
            return {"total_errors": 0}

        by_category = {}
        by_severity = {}
        by_strategy = {}

        for error in self._errors:
            cat = error.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

            sev = error.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1

            if error.strategy:
                strat = error.strategy.value
                by_strategy[strat] = by_strategy.get(strat, 0) + 1

        return {
            "total_errors": len(self._errors),
            "by_category": by_category,
            "by_severity": by_severity,
            "by_strategy": by_strategy,
            "recovery_rate": sum(1 for e in self._errors if e.recovery_successful) / len(self._errors),
        }


import asyncio


# Global error recovery
_error_recovery: ErrorRecovery | None = None


def get_error_recovery() -> ErrorRecovery:
    """Get global error recovery instance."""
    global _error_recovery
    if _error_recovery is None:
        _error_recovery = ErrorRecovery()
    return _error_recovery
