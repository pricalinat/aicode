"""Enhanced orchestrator with multi-agent collaboration support.

Extends the base orchestrator with planning, consensus, and evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..core.agent import AgentResponse, BaseAgent
from ..core.message import Message

from .planner import TaskPlanner, get_planner
from .memory import MemorySystem, get_memory_system
from .evaluator import EvaluationSystem, get_evaluation_system
from .consensus import ConsensusManager, get_consensus_manager
from .rag import KnowledgeAugmentation, get_knowledge_augmentation
from .proactive import ProactiveLayer, get_proactive_layer
from .continual import ContinualLearning, get_continual_learning


class ExecutionStrategy(Enum):
    """Multi-agent execution strategies."""

    SINGLE = "single"  # Single agent
    PARALLEL = "parallel"  # Multiple agents in parallel
    SEQUENTIAL = "sequential"  # Multiple agents sequentially
    CONSENSUS = "consensus"  # Multiple agents with consensus
    DEBATE = "debate"  # Multiple agents with debate


@dataclass
class ExecutionConfig:
    """Configuration for task execution."""

    strategy: ExecutionStrategy = ExecutionStrategy.SINGLE
    max_agents: int = 3
    timeout_seconds: int = 60
    enable_evaluation: bool = True
    enable_memory: bool = True
    enable_rag: bool = False


class EnhancedOrchestrator:
    """Enhanced orchestrator with enterprise features.

    Features:
    - Task planning (Routine)
    - Multi-agent collaboration
    - Consensus decision making
    - Evaluation system
    - Memory system
    - RAG augmentation
    - Proactive suggestions
    """

    def __init__(
        self,
        agents: list[BaseAgent],
        config: ExecutionConfig | None = None,
    ) -> None:
        self.agents = {agent.name: agent for agent in agents}
        self.config = config or ExecutionConfig()

        # Enterprise components
        self.planner = get_planner()
        self.memory = get_memory_system()
        self.evaluator = get_evaluation_system()
        self.consensus = get_consensus_manager()
        self.rag = get_knowledge_augmentation()
        self.proactive = get_proactive_layer()
        self.continual = get_continual_learning()

    def dispatch(self, message: Message, user_id: str | None = None) -> AgentResponse:
        """Dispatch task with enhanced processing."""
        import time

        start_time = time.time()

        try:
            # 1. Update context
            if user_id and self.config.enable_memory:
                self.proactive.update_context(user_id, message.content.get("query", ""))

            # 2. Generate execution plan
            plan = self.planner.plan(
                message.content.get("query", ""),
                {"task_type": message.task_type, "user_id": user_id},
            )

            # 3. Execute based on strategy
            if self.config.strategy == ExecutionStrategy.SINGLE:
                response = self._execute_single(message)
            elif self.config.strategy == ExecutionStrategy.PARALLEL:
                response = self._execute_parallel(message, plan)
            elif self.config.strategy == ExecutionStrategy.CONSENSUS:
                response = self._execute_consensus(message, plan)
            else:
                response = self._execute_single(message)

            # 4. Evaluate if enabled
            if self.config.enable_evaluation and message.content.get("query"):
                eval_result = self.evaluator.evaluate(
                    query=message.content.get("query", ""),
                    response=str(response.data),
                    context={"task_type": message.task_type},
                )
                response.data = response.data or {}
                response.data["_evaluation"] = eval_result.to_dict()

            # 5. Update memory
            if self.config.enable_memory and message.content.get("query"):
                self.memory.remember(
                    content=f"Query: {message.content.get('query')} -> Response: {response.data}",
                    memory_type="short_term",
                )

            # 6. Add proactive suggestions
            if user_id:
                suggestion = self.proactive.get_proactive_suggestion(user_id)
                if suggestion:
                    response.data = response.data or {}
                    response.data["_suggestion"] = suggestion

            # 7. Track execution time
            response.data = response.data or {}
            response.data["_execution_time_ms"] = (time.time() - start_time) * 1000

            return response

        except Exception as e:
            return AgentResponse(
                agent="enhanced-orchestrator",
                success=False,
                error=str(e),
                trace_id=message.trace_id,
            )

    def _execute_single(self, message: Message) -> AgentResponse:
        """Execute with single agent."""
        # Find appropriate agent
        agent = self._find_agent(message)
        if not agent:
            return AgentResponse(
                agent="enhanced-orchestrator",
                success=False,
                error="No suitable agent found",
                trace_id=message.trace_id,
            )

        return agent.handle(message)

    def _execute_parallel(self, message: Message, plan: Any) -> AgentResponse:
        """Execute with multiple agents in parallel."""
        import concurrent.futures
        import uuid

        # Get agents for each step
        agent_tasks = []
        for step in plan.steps:
            agent = self._find_agent_by_type(step.agent_type)
            if agent:
                agent_tasks.append((step, agent))

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(agent_tasks)) as executor:
            futures = {}
            for step, agent in agent_tasks:
                msg = Message(
                    task_type=message.task_type,
                    content={**message.content, "step_id": step.step_id},
                    trace_id=message.trace_id,
                )
                future = executor.submit(agent.handle, msg)
                futures[future] = step

            for future in concurrent.futures.as_completed(futures):
                step = futures[future]
                try:
                    result = future.result()
                    results.append((step.step_id, result))
                except Exception as e:
                    results.append((step.step_id, None))

        # Aggregate results
        combined_data = {"steps": [], "final_result": None}
        for step_id, result in results:
            if result:
                combined_data["steps"].append(
                    {"step_id": step_id, "success": result.success, "data": result.data}
                )
                if result.success:
                    combined_data["final_result"] = result.data

        return AgentResponse(
            agent="enhanced-orchestrator",
            success=any(r[1].success if r[1] else False for r in results),
            data=combined_data,
            trace_id=message.trace_id,
        )

    def _execute_consensus(self, message: Message, plan: Any) -> AgentResponse:
        """Execute with consensus among multiple agents."""
        from .consensus import AgentOpinion

        # Get multiple agent opinions
        opinions = []
        for step in plan.steps[:3]:  # Limit to 3 agents
            agent = self._find_agent_by_type(step.agent_type)
            if agent:
                result = agent.handle(message)
                if result.success:
                    opinion = AgentOpinion(
                        agent_id=agent.name,
                        agent_type=agent.name,
                        decision=str(result.data),
                        confidence=0.8,  # Default confidence
                        reasoning="Agent output",
                    )
                    opinions.append(opinion)

        if not opinions:
            return self._execute_single(message)

        # Make consensus decision
        decision_result = self.consensus.make_decision(opinions)

        return AgentResponse(
            agent="enhanced-orchestrator",
            success=True,
            data={
                "decision": decision_result.decision,
                "confidence": decision_result.confidence,
                "agreed_by": decision_result.agreed_by,
                "disagreed_by": decision_result.disagreed_by,
                "all_opinions": [{"agent": o.agent_id, "decision": o.decision} for o in opinions],
            },
            trace_id=message.trace_id,
        )

    def _find_agent(self, message: Message) -> BaseAgent | None:
        """Find first suitable agent."""
        for agent in self.agents.values():
            if hasattr(agent, "capabilities") and message.task_type in agent.capabilities:
                return agent
        # Fallback to any agent
        return list(self.agents.values())[0] if self.agents else None

    def _find_agent_by_type(self, agent_type: str) -> BaseAgent | None:
        """Find agent by type/capability."""
        # Map agent_type to actual agent
        type_map = {
            "arxiv": "arxiv-agent",
            "intent_classification": "intent-classification-agent",
            "entity_extraction": "entity-extraction-agent",
            "semantic_search": "semantic-search-agent",
            "matching": "matching-agent",
            "paper_search": "paper-search-agent",
        }

        agent_name = type_map.get(agent_type, agent_type)
        return self.agents.get(agent_name)

    def register_agent(self, agent: BaseAgent) -> None:
        """Register a new agent."""
        self.agents[agent.name] = agent

    def set_strategy(self, strategy: ExecutionStrategy) -> None:
        """Set execution strategy."""
        self.config.strategy = strategy

    def enable_rag(self, enabled: bool = True) -> None:
        """Enable/disable RAG augmentation."""
        self.config.enable_rag = enabled
