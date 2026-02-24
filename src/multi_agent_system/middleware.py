"""Request validation and middleware system."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class ValidationError:
    """A validation error."""
    field: str
    message: str


class Validator(ABC):
    """Abstract validator interface."""
    
    @abstractmethod
    def validate(self, data: dict[str, Any]) -> list[ValidationError]:
        """Validate data and return list of errors."""
        pass


class RequestValidator(Validator):
    """Validates API requests."""
    
    def validate(self, data: dict[str, Any]) -> list[ValidationError]:
        errors = []
        
        # Validate action
        if "action" not in data:
            errors.append(ValidationError("action", "Missing required field: action"))
        
        # Validate platform if present
        if "platform" in data:
            if data["platform"] not in ("wechat", "alipay", None):
                errors.append(ValidationError("platform", "Invalid platform"))
        
        return errors


class Middleware(ABC):
    """Abstract middleware interface."""
    
    @abstractmethod
    def process(self, request: Any, next_handler: Callable) -> Any:
        """Process request and call next handler."""
        pass


class LoggingMiddleware(Middleware):
    """Middleware that logs requests."""
    
    def process(self, request: Any, next_handler: Callable) -> Any:
        print(f"[Middleware] Processing request: {request}")
        result = next_handler(request)
        print(f"[Middleware] Completed request: {request}")
        return result


class MetricsMiddleware(Middleware):
    """Middleware that collects metrics."""
    
    def process(self, request: Any, next_handler: Callable) -> Any:
        from ..metrics import get_metrics, Metrics
        import time
        
        metrics = get_metrics()
        start = time.perf_counter()
        
        try:
            result = next_handler(request)
            metrics.increment(Metrics.API_REQUESTS)
            return result
        except Exception as e:
            metrics.increment(Metrics.AGENT_ERRORS)
            raise
        finally:
            duration = (time.perf_counter() - start) * 1000
            metrics.timer(Metrics.API_LATENCY, duration)


class MiddlewareChain:
    """Chain of middleware processors."""
    
    def __init__(self) -> None:
        self._middleware: list[Middleware] = []
    
    def add(self, middleware: Middleware) -> "MiddlewareChain":
        self._middleware.append(middleware)
        return self
    
    def process(self, request: Any, final_handler: Callable) -> Any:
        """Process request through middleware chain."""
        
        def handle(index: int) -> Any:
            if index >= len(self._middleware):
                return final_handler(request)
            
            middleware = self._middleware[index]
            
            def next_handler():
                return handle(index + 1)
            
            return middleware.process(request, next_handler)
        
        return handle(0)
