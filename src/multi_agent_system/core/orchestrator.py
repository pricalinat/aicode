from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from .agent import AgentResponse, BaseAgent
from .message import Message
from .tracing import TraceLevel, trace


@dataclass
class Orchestrator:
    """Orchestrator for managing and dispatching tasks to agents.
    
    Supports both sync and async agents. The orchestrator automatically
    detects agent type and uses the appropriate execution method.
    """
    
    agents: list[BaseAgent] = field(default_factory=list)

    def register(self, agent: BaseAgent) -> None:
        self.agents.append(agent)

    def dispatch(self, message: Message) -> AgentResponse:
        """Synchronous dispatch to an agent.
        
        For async agents, this will run them in a new event loop.
        Use adispatch() for async contexts.
        """
        trace(message.trace_id, TraceLevel.ORCHESTRATOR_START, message="Task dispatch started")
        
        start_time = time.perf_counter()
        
        for agent in self.agents:
            if agent.can_handle(message):
                trace(
                    message.trace_id,
                    TraceLevel.AGENT_DISPATCH,
                    agent=agent.name,
                    message=f"Dispatching to {agent.name}",
                )
                
                agent_start = time.perf_counter()
                trace(message.trace_id, TraceLevel.AGENT_START, agent=agent.name, message="Agent execution started")
                
                try:
                    # Use async handler if available and preferred
                    if agent.is_async():
                        response = asyncio.run(agent.ahandle(message))
                    else:
                        response = agent.handle(message)
                    
                    duration_ms = (time.perf_counter() - agent_start) * 1000
                    
                    trace(
                        message.trace_id,
                        TraceLevel.AGENT_END,
                        agent=agent.name,
                        message="Agent execution completed",
                        duration_ms=duration_ms,
                    )
                    
                    if response.trace_id is None:
                        response.trace_id = message.trace_id
                    return response
                    
                except Exception as exc:
                    duration_ms = (time.perf_counter() - agent_start) * 1000
                    trace(
                        message.trace_id,
                        TraceLevel.AGENT_ERROR,
                        agent=agent.name,
                        message=f"Agent error: {exc}",
                        duration_ms=duration_ms,
                    )
                    return AgentResponse(
                        agent=agent.name,
                        success=False,
                        error=str(exc),
                        trace_id=message.trace_id,
                    )
        
        total_duration = (time.perf_counter() - start_time) * 1000
        trace(
            message.trace_id,
            TraceLevel.ORCHESTRATOR_END,
            message="No agent found for task",
            duration_ms=total_duration,
        )
        
        return AgentResponse(
            agent="orchestrator",
            success=False,
            error=f"No agent can handle task_type='{message.task_type}'",
            trace_id=message.trace_id,
        )

    async def adispatch(self, message: Message) -> AgentResponse:
        """Asynchronous dispatch to an agent.
        
        Preferred method when running in an async context.
        """
        trace(message.trace_id, TraceLevel.ORCHESTRATOR_START, message="Task dispatch started (async)")
        
        start_time = time.perf_counter()
        
        for agent in self.agents:
            if agent.can_handle(message):
                trace(
                    message.trace_id,
                    TraceLevel.AGENT_DISPATCH,
                    agent=agent.name,
                    message=f"Async dispatching to {agent.name}",
                )
                
                agent_start = time.perf_counter()
                trace(message.trace_id, TraceLevel.AGENT_START, agent=agent.name, message="Async agent execution started")
                
                try:
                    # Use async handler in async context
                    response = await agent.ahandle(message)
                    
                    duration_ms = (time.perf_counter() - agent_start) * 1000
                    
                    trace(
                        message.trace_id,
                        TraceLevel.AGENT_END,
                        agent=agent.name,
                        message="Async agent execution completed",
                        duration_ms=duration_ms,
                    )
                    
                    if response.trace_id is None:
                        response.trace_id = message.trace_id
                    return response
                    
                except Exception as exc:
                    duration_ms = (time.perf_counter() - agent_start) * 1000
                    trace(
                        message.trace_id,
                        TraceLevel.AGENT_ERROR,
                        agent=agent.name,
                        message=f"Async agent error: {exc}",
                        duration_ms=duration_ms,
                    )
                    return AgentResponse(
                        agent=agent.name,
                        success=False,
                        error=str(exc),
                        trace_id=message.trace_id,
                    )
        
        total_duration = (time.perf_counter() - start_time) * 1000
        trace(
            message.trace_id,
            TraceLevel.ORCHESTRATOR_END,
            message="No agent found for task",
            duration_ms=total_duration,
        )
        
        return AgentResponse(
            agent="orchestrator",
            success=False,
            error=f"No agent can handle task_type='{message.task_type}'",
            trace_id=message.trace_id,
        )
