"""Multi-Agent Simulation System.

Based on research about emergent behavior in multi-agent simulations,
agent interactions, and social system modeling.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class AgentState(Enum):
    """Agent state in simulation."""
    IDLE = "idle"
    ACTIVE = "active"
    WAITING = "waiting"
    COMPLETED = "completed"


@dataclass
class SimulationConfig:
    """Configuration for simulation."""
    max_steps: int = 100
    tick_rate_ms: int = 1000  # Time between steps
    enable_emergence: bool = True
    record_history: bool = True
    allow_communication: bool = True


@dataclass
class SimulationAgent:
    """An agent in the simulation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    agent_type: str = ""  # "worker", "manager", "observer", etc.

    # State
    state: AgentState = AgentState.IDLE
    properties: dict[str, Any] = field(default_factory=dict)

    # Behavior
    behavior_script: str = ""  # What the agent does
    goals: list[str] = field(default_factory=list)

    # Memory
    memory: list[dict[str, Any]] = field(default_factory=list)

    # Interactions
    interactions: list[str] = field(default_factory=list)  # Other agent IDs

    # Metrics
    actions_taken: int = 0
    successful_actions: int = 0

    def take_action(self, action: str, target: Any = None) -> dict[str, Any]:
        """Take an action."""
        self.actions_taken += 1
        self.state = AgentState.ACTIVE

        result = {
            "agent_id": self.id,
            "action": action,
            "target": target,
            "success": True,  # Would be determined by actual execution
            "timestamp": datetime.now().isoformat(),
        }

        self.memory.append(result)
        return result


@dataclass
class Environment:
    """Simulation environment."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""

    # Resources
    resources: dict[str, float] = field(default_factory=dict)

    # State
    state: dict[str, Any] = field(default_factory=dict)

    # Rules
    rules: list[str] = field(default_factory=list)

    def update(self, changes: dict[str, Any]) -> None:
        """Update environment state."""
        self.state.update(changes)

    def get_resource(self, name: str) -> float:
        """Get resource amount."""
        return self.resources.get(name, 0.0)

    def consume_resource(self, name: str, amount: float) -> bool:
        """Consume resource if available."""
        current = self.resources.get(name, 0.0)
        if current >= amount:
            self.resources[name] = current - amount
            return True
        return False


@dataclass
class SimulationEvent:
    """An event in the simulation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    event_type: str = ""
    agent_id: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SimulationStep:
    """A single simulation step."""
    step_number: int = 0
    agents: dict[str, AgentState] = field(default_factory=dict)
    environment_state: dict[str, Any] = field(default_factory=dict)
    events: list[SimulationEvent] = field(default_factory=list)
    emergent_behaviors: list[str] = field(default_factory=list)


@dataclass
class Simulation:
    """A complete simulation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""

    # Components
    agents: dict[str, SimulationAgent] = field(default_factory=dict)
    environment: Environment = field(default_factory=Environment)

    # Configuration
    config: SimulationConfig = field(default_factory=SimulationConfig)

    # State
    current_step: int = 0
    is_running: bool = False
    is_paused: bool = False

    # History
    steps: list[SimulationStep] = field(default_factory=list)

    # Callbacks
    on_step: list[Callable] = field(default_factory=list)
    on_event: list[Callable] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None


class SimulationEngine:
    """Engine for running multi-agent simulations.

    Features:
    - Configurable agent behaviors
    - Environment management
    - Event tracking
    - Emergent behavior detection
    """

    def __init__(self) -> None:
        """Initialize simulation engine."""
        self._simulations: dict[str, Simulation] = {}
        self._handlers: dict[str, Callable] = {}

    def create_simulation(
        self,
        name: str,
        description: str = "",
        config: SimulationConfig | None = None,
    ) -> Simulation:
        """Create a new simulation."""
        sim = Simulation(
            name=name,
            description=description,
            config=config or SimulationConfig(),
        )
        self._simulations[sim.id] = sim
        return sim

    def add_agent(
        self,
        simulation_id: str,
        name: str,
        agent_type: str = "generic",
        behavior_script: str = "",
    ) -> SimulationAgent | None:
        """Add agent to simulation."""
        sim = self._simulations.get(simulation_id)
        if not sim:
            return None

        agent = SimulationAgent(
            name=name,
            agent_type=agent_type,
            behavior_script=behavior_script,
        )
        sim.agents[agent.id] = agent
        return agent

    def add_environment(
        self,
        simulation_id: str,
        name: str,
        resources: dict[str, float] | None = None,
    ) -> Environment | None:
        """Add environment to simulation."""
        sim = self._simulations.get(simulation_id)
        if not sim:
            return None

        env = Environment(name=name, resources=resources or {})
        sim.environment = env
        return env

    async def run_simulation(self, simulation_id: str) -> Simulation | None:
        """Run simulation to completion."""
        sim = self._simulations.get(simulation_id)
        if not sim:
            return None

        sim.is_running = True

        while sim.current_step < sim.config.max_steps and sim.is_running:
            if sim.is_paused:
                await self._wait_for_resume()

            # Execute step
            await self._execute_step(sim)

            # Check for completion
            if self._check_completion(sim):
                break

        sim.is_running = False
        sim.completed_at = datetime.now()
        return sim

    async def _execute_step(self, sim: Simulation) -> None:
        """Execute one simulation step."""
        step = SimulationStep(step_number=sim.current_step)

        # Record agent states
        for agent_id, agent in sim.agents.items():
            step.agents[agent_id] = agent.state

        # Record environment state
        step.environment_state = dict(sim.environment.state)

        # Execute agent behaviors
        for agent_id, agent in sim.agents.items():
            if agent.state != AgentState.IDLE:
                action_result = self._execute_agent_behavior(agent, sim.environment)
                if action_result.get("success"):
                    agent.successful_actions += 1

        # Record step
        if sim.config.record_history:
            sim.steps.append(step)

        sim.current_step += 1

        # Trigger callbacks
        for callback in sim.on_step:
            await callback(sim, step)

    def _execute_agent_behavior(
        self,
        agent: SimulationAgent,
        env: Environment,
    ) -> dict[str, Any]:
        """Execute agent behavior."""
        # In a real implementation, this would use LLM or behavior trees
        # Here we simulate basic behavior

        if agent.behavior_script:
            # Would execute actual behavior script
            return {"success": True, "action": "executed_script"}

        # Default behavior
        return {"success": True, "action": "idle"}

    def _check_completion(self, sim: Simulation) -> bool:
        """Check if simulation is complete."""
        # Check if all agents are completed
        all_completed = all(
            agent.state == AgentState.COMPLETED
            for agent in sim.agents.values()
        )

        # Check for deadlock
        no_progress = (
            sim.current_step > 0 and
            len(sim.steps) > 0 and
            sim.steps[-1] == sim.steps[-2] if len(sim.steps) > 1 else False
        )

        return all_completed or no_progress

    async def _wait_for_resume(self) -> None:
        """Wait for simulation to be resumed."""
        import asyncio
        while True:
            await asyncio.sleep(0.1)

    def pause_simulation(self, simulation_id: str) -> bool:
        """Pause simulation."""
        sim = self._simulations.get(simulation_id)
        if sim and sim.is_running:
            sim.is_paused = True
            return True
        return False

    def resume_simulation(self, simulation_id: str) -> bool:
        """Resume simulation."""
        sim = self._simulations.get(simulation_id)
        if sim and sim.is_paused:
            sim.is_paused = False
            return True
        return False

    def stop_simulation(self, simulation_id: str) -> bool:
        """Stop simulation."""
        sim = self._simulations.get(simulation_id)
        if sim:
            sim.is_running = False
            sim.completed_at = datetime.now()
            return True
        return False

    def get_simulation(self, simulation_id: str) -> Simulation | None:
        """Get simulation by ID."""
        return self._simulations.get(simulation_id)

    def get_statistics(self, simulation_id: str) -> dict[str, Any]:
        """Get simulation statistics."""
        sim = self._simulations.get(simulation_id)
        if not sim:
            return {}

        agent_stats = {}
        for agent_id, agent in sim.agents.items():
            agent_stats[agent_id] = {
                "name": agent.name,
                "actions_taken": agent.actions_taken,
                "successful_actions": agent.successful_actions,
                "success_rate": agent.successful_actions / agent.actions_taken if agent.actions_taken > 0 else 0,
            }

        return {
            "total_steps": sim.current_step,
            "total_agents": len(sim.agents),
            "total_events": sum(len(s.events) for s in sim.steps),
            "agent_stats": agent_stats,
        }


# Global simulation engine
_simulation_engine: SimulationEngine | None = None


def get_simulation_engine() -> SimulationEngine:
    """Get global simulation engine."""
    global _simulation_engine
    if _simulation_engine is None:
        _simulation_engine = SimulationEngine()
    return _simulation_engine
