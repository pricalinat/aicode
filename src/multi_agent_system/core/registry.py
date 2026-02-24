"""Agent Registry for capability-based agent management."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .agent import AgentResponse, BaseAgent
from .message import Message


@dataclass
class AgentRegistration:
    """Registration info for an agent."""
    agent: BaseAgent
    priority: int = 0  # Higher priority agents are matched first
    enabled: bool = True


class AgentRegistry:
    """Registry for managing agents with capability-based routing.
    
    Features:
    - Capability-based agent lookup
    - Priority routing (higher priority agents matched first)
    - Dynamic agent enable/disable
    - Agent filtering by custom predicates
    """
    
    def __init__(self) -> None:
        self._registrations: list[AgentRegistration] = []
        self._capability_index: dict[str, list[AgentRegistration]] = {}
    
    def register(
        self,
        agent: BaseAgent,
        priority: int = 0,
        enabled: bool = True,
    ) -> None:
        """Register an agent with the registry.
        
        Args:
            agent: The agent to register
            priority: Higher priority agents are matched first (default: 0)
            enabled: Whether the agent is enabled (default: True)
        """
        registration = AgentRegistration(
            agent=agent,
            priority=priority,
            enabled=enabled,
        )
        self._registrations.append(registration)
        
        # Build capability index
        for capability in agent.capabilities:
            if capability not in self._capability_index:
                self._capability_index[capability] = []
            self._capability_index[capability].append(registration)
        
        # Sort by priority (descending)
        self._registrations.sort(key=lambda r: r.priority, reverse=True)
    
    def unregister(self, agent_name: str) -> bool:
        """Unregister an agent by name.
        
        Args:
            agent_name: Name of the agent to unregister
            
        Returns:
            True if agent was found and removed, False otherwise
        """
        for i, reg in enumerate(self._registrations):
            if reg.agent.name == agent_name:
                del self._registrations[i]
                self._rebuild_index()
                return True
        return False
    
    def _rebuild_index(self) -> None:
        """Rebuild the capability index."""
        self._capability_index.clear()
        for reg in self._registrations:
            for capability in reg.agent.capabilities:
                if capability not in self._capability_index:
                    self._capability_index[capability] = []
                self._capability_index[capability].append(reg)
    
    def get_agent(self, task_type: str) -> BaseAgent | None:
        """Get the highest priority agent that can handle a task type.
        
        Args:
            task_type: The task type to find an agent for
            
        Returns:
            The matching agent, or None if no agent can handle the task
        """
        for reg in self._registrations:
            if reg.enabled and reg.agent.can_handle(Message(task_type=task_type, content={})):
                return reg.agent
        return None
    
    def get_agents(self, task_type: str) -> list[BaseAgent]:
        """Get all agents that can handle a task type.
        
        Args:
            task_type: The task type to find agents for
            
        Returns:
            List of matching agents (sorted by priority, highest first)
        """
        result = []
        for reg in self._registrations:
            if reg.enabled and reg.agent.can_handle(Message(task_type=task_type, content={})):
                result.append(reg.agent)
        return result
    
    def get_by_capability(self, capability: str) -> list[BaseAgent]:
        """Get all agents with a specific capability.
        
        Args:
            capability: The capability to filter by
            
        Returns:
            List of agents with the capability
        """
        registrations = self._capability_index.get(capability, [])
        return [r.agent for r in registrations if r.enabled]
    
    def enable(self, agent_name: str) -> bool:
        """Enable an agent by name.
        
        Args:
            agent_name: Name of the agent to enable
            
        Returns:
            True if agent was found and enabled, False otherwise
        """
        for reg in self._registrations:
            if reg.agent.name == agent_name:
                reg.enabled = True
                return True
        return False
    
    def disable(self, agent_name: str) -> bool:
        """Disable an agent by name.
        
        Args:
            agent_name: Name of the agent to disable
            
        Returns:
            True if agent was found and disabled, False otherwise
        """
        for reg in self._registrations:
            if reg.agent.name == agent_name:
                reg.enabled = False
                return True
        return False
    
    def list_agents(self) -> list[str]:
        """List all registered agent names.
        
        Returns:
            List of agent names
        """
        return [reg.agent.name for reg in self._registrations]
    
    def list_capabilities(self) -> set[str]:
        """List all available capabilities.
        
        Returns:
            Set of all capability names
        """
        return set(self._capability_index.keys())
    
    def clear(self) -> None:
        """Clear all agent registrations."""
        self._registrations.clear()
        self._capability_index.clear()


class PriorityOrchestrator:
    """Enhanced orchestrator using AgentRegistry for priority-based routing.
    """
    
    def __init__(self, registry: AgentRegistry | None = None) -> None:
        self.registry = registry or AgentRegistry()
    
    def dispatch(self, message: Message) -> AgentResponse:
        """Dispatch a message to the highest priority matching agent."""
        agent = self.registry.get_agent(message.task_type)
        
        if agent is None:
            return AgentResponse(
                agent="orchestrator",
                success=False,
                error=f"No agent can handle task_type='{message.task_type}'",
                trace_id=message.trace_id,
            )
        
        return agent.handle(message)
    
    async def adispatch(self, message: Message) -> AgentResponse:
        """Asynchronously dispatch a message to the highest priority matching agent."""
        agent = self.registry.get_agent(message.task_type)
        
        if agent is None:
            return AgentResponse(
                agent="orchestrator",
                success=False,
                error=f"No agent can handle task_type='{message.task_type}'",
                trace_id=message.trace_id,
            )
        
        # Use async handler - it's defined in BaseAgent
        return await agent.ahandle(message)
    
    def dispatch_all(self, message: Message) -> list[AgentResponse]:
        """Dispatch a message to ALL matching agents and collect responses.
        
        Useful for parallel agent execution patterns.
        """
        agents = self.registry.get_agents(message.task_type)
        
        if not agents:
            return [
                AgentResponse(
                    agent="orchestrator",
                    success=False,
                    error=f"No agent can handle task_type='{message.task_type}'",
                    trace_id=message.trace_id,
                )
            ]
        
        return [agent.handle(message) for agent in agents]
