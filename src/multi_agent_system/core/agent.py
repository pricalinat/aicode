from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, TypeVar

from .message import Message

T = TypeVar("T")


@dataclass
class AgentResponse:
    agent: str
    success: bool
    data: Any = None
    error: str | None = None
    trace_id: str | None = None


def _run_async(
    coro: Awaitable[T],
    sync_func: Callable[[Message], AgentResponse],
    message: Message,
) -> AgentResponse:
    """
    Bridge async coroutine to sync call.
    Used when an async agent is called in a sync context.
    """
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context but agent is sync
        # This shouldn't happen normally, but handle gracefully
        return sync_func(message)
    except RuntimeError:
        # No running loop - we can run the async function
        return asyncio.run(coro)


class BaseAgent(ABC):
    """Base class for all agents in the multi-agent system.
    
    Agents can implement either sync handle() or async ahandle() method.
    The orchestrator will automatically detect and use the appropriate method.
    """
    
    name: str = "base-agent"
    capabilities: set[str] = set()

    def can_handle(self, message: Message) -> bool:
        return message.task_type in self.capabilities

    @abstractmethod
    def handle(self, message: Message) -> AgentResponse:
        """Synchronous handler for a message.
        
        Override this method for sync agents.
        For async agents, override ahandle() instead.
        """
        raise NotImplementedError

    async def ahandle(self, message: Message) -> AgentResponse:
        """Asynchronous handler for a message.
        
        Override this method for async agents.
        Default implementation calls sync handle() for backwards compatibility.
        """
        return self.handle(message)

    def is_async(self) -> bool:
        """Check if this agent prefers async execution.
        
        Returns True if ahandle is overridden (not the default implementation).
        """
        # Check if ahandle is overridden in subclass
        return type(self).ahandle is not BaseAgent.ahandle
