"""Event system for publish-subscribe messaging."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List
from datetime import datetime


@dataclass
class Event:
    """An event in the system."""
    type: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "system"


class EventHandler(ABC):
    """Abstract event handler."""
    
    @abstractmethod
    async def handle(self, event: Event) -> None:
        """Handle an event."""
        pass


class SyncEventHandler(EventHandler):
    """Synchronous event handler."""
    
    def __init__(self, handler: Callable[[Event], None]) -> None:
        self._handler = handler
    
    async def handle(self, event: Event) -> None:
        self._handler(event)


class AsyncEventHandler(EventHandler):
    """Asynchronous event handler."""
    
    def __init__(self, handler: Callable[[Event], asyncio.Task]) -> None:
        self._handler = handler
    
    async def handle(self, event: Event) -> None:
        await self._handler(event)


class EventBus:
    """Central event bus for publish-subscribe."""
    
    def __init__(self) -> None:
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000
    
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)
    
    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Notify handlers
        handlers = self._handlers.get(event.type, [])
        for handler in handlers:
            try:
                await handler.handle(event)
            except Exception as e:
                print(f"Error handling event {event.type}: {e}")
    
    def publish_sync(self, event: Event) -> None:
        """Publish an event synchronously."""
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Notify handlers
        handlers = self._handlers.get(event.type, [])
        for handler in handlers:
            try:
                # Run sync handlers directly
                if isinstance(handler, SyncEventHandler):
                    handler._handler(event)
                else:
                    # For async handlers, create a task
                    asyncio.create_task(handler.handle(event))
            except Exception as e:
                print(f"Error handling event {event.type}: {e}")
    
    def get_history(self, event_type: str | None = None, limit: int = 100) -> List[Event]:
        """Get event history."""
        if event_type:
            events = [e for e in self._event_history if e.type == event_type]
        else:
            events = self._event_history
        
        return events[-limit:]
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()


# Global event bus
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get the global event bus."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


# Predefined event types
class Events:
    """Event type constants."""
    AGENT_REGISTERED = "agent.registered"
    AGENT_DISPATCHED = "agent.dispatched"
    AGENT_COMPLETED = "agent.completed"
    AGENT_ERROR = "agent.error"
    GRAPH_ENTITY_CREATED = "graph.entity.created"
    GRAPH_ENTITY_UPDATED = "graph.entity.updated"
    GRAPH_ENTITY_DELETED = "graph.entity.deleted"
    GRAPH_RELATION_CREATED = "graph.relation.created"
    CACHE_HIT = "cache.hit"
    CACHE_MISS = "cache.miss"
    API_REQUEST = "api.request"
    API_RESPONSE = "api.response"
    USER_ACTION = "user.action"
    MATCHING_COMPLETED = "matching.completed"
    RECOMMENDATION_GENERATED = "recommendation.generated"
