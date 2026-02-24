"""Tracing and logging infrastructure for the multi-agent system."""

from __future__ import annotations

import sys
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from loguru import logger


# Configure logger
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)


# Trace context for request-scoped tracing
trace_context: ContextVar[dict[str, Any] | None] = ContextVar("trace_context", default=None)


class TraceLevel(Enum):
    """Trace event types."""
    AGENT_DISPATCH = "agent_dispatch"
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    AGENT_ERROR = "agent_error"
    ORCHESTRATOR_START = "orchestrator_start"
    ORCHESTRATOR_END = "orchestrator_end"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    GRAPH_QUERY = "graph_query"
    MATCHING_START = "matching_start"
    MATCHING_END = "matching_end"


@dataclass
class TraceEvent:
    """A single trace event."""
    level: TraceLevel
    trace_id: str
    agent: str | None = None
    message: str | None = None
    duration_ms: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Tracer:
    """Distributed tracing for the multi-agent system."""
    
    def __init__(self) -> None:
        self._events: list[TraceEvent] = []
    
    def record(self, event: TraceEvent) -> None:
        """Record a trace event."""
        self._events.append(event)
        self._log_event(event)
    
    def _log_event(self, event: TraceEvent) -> None:
        """Log trace event to logger."""
        log_level = "INFO"
        if event.level == TraceLevel.AGENT_ERROR:
            log_level = "ERROR"
        
        msg_parts = [f"[{event.level.value}]"]
        if event.agent:
            msg_parts.append(f"agent={event.agent}")
        if event.message:
            msg_parts.append(event.message)
        if event.duration_ms is not None:
            msg_parts.append(f"duration={event.duration_ms:.2f}ms")
        
        logger.info(" ".join(msg_parts), extra={"trace_id": event.trace_id})
    
    def get_events(self, trace_id: str | None = None) -> list[TraceEvent]:
        """Get all events, optionally filtered by trace_id."""
        if trace_id is None:
            return self._events
        return [e for e in self._events if e.trace_id == trace_id]
    
    def clear(self) -> None:
        """Clear all events."""
        self._events.clear()


# Global tracer instance
_global_tracer = Tracer()


def get_tracer() -> Tracer:
    """Get the global tracer instance."""
    return _global_tracer


def trace(trace_id: str, level: TraceLevel, agent: str | None = None, message: str | None = None, duration_ms: float | None = None, **metadata: Any) -> None:
    """Convenience function to record a trace event."""
    event = TraceEvent(
        level=level,
        trace_id=trace_id,
        agent=agent,
        message=message,
        duration_ms=duration_ms,
        metadata=metadata,
    )
    _global_tracer.record(event)


def set_trace_context(trace_id: str, **context: Any) -> None:
    """Set trace context for the current request."""
    trace_context.set({"trace_id": trace_id, **context})


def get_trace_context() -> dict[str, Any] | None:
    """Get the current trace context."""
    return trace_context.get()
