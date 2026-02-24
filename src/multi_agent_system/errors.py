"""Error handling and retry utilities."""

from __future__ import annotations

import asyncio
import functools
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Type, TypeVar, Union

T = TypeVar("T")


class ErrorCode(Enum):
    """System error codes."""
    # Agent errors (1xxx)
    AGENT_NOT_FOUND = 1001
    AGENT_EXECUTION_ERROR = 1002
    AGENT_TIMEOUT = 1003
    
    # Graph errors (2xxx)
    GRAPH_ENTITY_NOT_FOUND = 2001
    GRAPH_RELATION_NOT_FOUND = 2002
    GRAPH_CONSTRAINT_VIOLATION = 2003
    
    # Validation errors (3xxx)
    VALIDATION_ERROR = 3001
    INVALID_INPUT = 3002
    MISSING_REQUIRED_FIELD = 3003
    
    # External errors (4xxx)
    EXTERNAL_API_ERROR = 4001
    NETWORK_ERROR = 4002
    TIMEOUT_ERROR = 4003
    
    # System errors (5xxx)
    INTERNAL_ERROR = 5001
    NOT_IMPLEMENTED = 5002
    CONFIGURATION_ERROR = 5003


@dataclass
class AgentError(Exception):
    """Base exception for agent errors."""
    code: ErrorCode
    message: str
    details: dict | None = None
    
    def __str__(self) -> str:
        if self.details:
            return f"[{self.code.name}] {self.message}: {self.details}"
        return f"[{self.code.name}] {self.message}"


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """Decorator to retry a function on failure."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
            
            raise last_exception
        
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return wrapper  # type: ignore
    
    return decorator


class ErrorHandler:
    """Central error handler with recovery strategies."""
    
    def __init__(self) -> None:
        self._handlers: dict[ErrorCode, Callable[[Exception], Any]] = {}
    
    def register_handler(self, code: ErrorCode, handler: Callable[[Exception], Any]) -> None:
        """Register a handler for an error code."""
        self._handlers[code] = handler
    
    def handle(self, error: Exception) -> Any:
        """Handle an error using registered handlers."""
        if isinstance(error, AgentError):
            handler = self._handlers.get(error.code)
            if handler:
                return handler(error)
        
        # Default handling
        return {"error": str(error), "handled": False}
    
    def get_error_response(self, error: Exception) -> dict[str, Any]:
        """Get a standardized error response."""
        if isinstance(error, AgentError):
            return {
                "success": False,
                "error": error.message,
                "code": error.code.value,
                "details": error.details,
            }
        
        return {
            "success": False,
            "error": str(error),
            "code": ErrorCode.INTERNAL_ERROR.value,
            "details": None,
        }


# Global error handler
_error_handler: ErrorHandler | None = None


def get_error_handler() -> ErrorHandler:
    """Get the global error handler."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_error(error: Exception) -> dict[str, Any]:
    """Convenience function to handle errors."""
    return get_error_handler().get_error_response(error)


class CircuitBreaker:
    """Circuit breaker for fault tolerance."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._state = "closed"  # closed, open, half_open
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open."""
        if self._state == "open":
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self._state = "half_open"
                return False
            return True
        return False
    
    @property
    def last_failure_time(self) -> float:
        return self._last_failure_time
    
    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Call a function with circuit breaker protection."""
        if self.is_open:
            raise Exception("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self) -> None:
        """Handle successful call."""
        self._failure_count = 0
        self._state = "closed"
    
    def _on_failure(self) -> None:
        """Handle failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= self.failure_threshold:
            self._state = "open"
