"""Task planning module based on Routine paper.

Reference: "Routine: A Structural Planning Framework for LLM Agent System"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskType(Enum):
    """Task type classification."""

    QUESTION_ANSWER = "question_answer"  # 问答
    INFORMATION_RETRIEVAL = "info_retrieval"  # 信息检索
    TEXT_GENERATION = "text_generation"  # 文本生成
    ANALYSIS = "analysis"  # 分析
    REASONING = "reasoning"  # 推理
    MULTI_STEP = "multi_step"  # 多步骤任务
    UNKNOWN = "unknown"


class StepStatus(Enum):
    """Step execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskStep:
    """A single step in the execution plan."""

    step_id: str
    name: str
    description: str
    agent_type: str  # Required agent type
    input_data: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)  # Step IDs this depends on
    status: StepStatus = StepStatus.PENDING
    output: Any = None
    error: str | None = None

    def can_execute(self, completed_steps: set[str]) -> bool:
        """Check if all dependencies are satisfied."""
        return all(dep in completed_steps for dep in self.dependencies)


@dataclass
class ExecutionPlan:
    """Complete execution plan for a task."""

    plan_id: str
    original_request: str
    task_type: TaskType
    steps: list[TaskStep] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def get_step(self, step_id: str) -> TaskStep | None:
        """Get step by ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def get_ready_steps(self, completed: set[str]) -> list[TaskStep]:
        """Get steps that are ready to execute."""
        ready = []
        for step in self.steps:
            if step.status == StepStatus.PENDING and step.can_execute(completed):
                ready.append(step)
        return ready

    def is_complete(self) -> bool:
        """Check if all steps are completed."""
        return all(s.status == StepStatus.COMPLETED for s in self.steps)

    def has_failed(self) -> bool:
        """Check if any step failed."""
        return any(s.status == StepStatus.FAILED for s in self.steps)


class TaskPlanner:
    """Task planner based on Routine framework.

    Generates structured execution plans from user requests.
    """

    # Agent capability mapping
    AGENT_CAPABILITIES = {
        "arxiv": ["search_arxiv", "paper_search"],
        "intent_classification": ["classify_intent", "intent_detection"],
        "entity_extraction": ["extract_entity", "ner"],
        "semantic_search": ["semantic_search", "vector_search"],
        "matching": ["match", "recommend"],
        "paper_search": ["search_papers", "find_papers"],
    }

    # Task type to required capabilities mapping
    TASK_REQUIREMENTS = {
        TaskType.QUESTION_ANSWER: ["intent_classification", "entity_extraction", "semantic_search"],
        TaskType.INFORMATION_RETRIEVAL: ["arxiv", "semantic_search"],
        TaskType.TEXT_GENERATION: ["intent_classification", "entity_extraction"],
        TaskType.ANALYSIS: ["entity_extraction", "semantic_search", "matching"],
        TaskType.REASONING: ["intent_classification", "semantic_search"],
        TaskType.MULTI_STEP: ["intent_classification", "entity_extraction", "semantic_search", "matching"],
    }

    def __init__(self) -> None:
        self.plans: dict[str, ExecutionPlan] = {}

    def plan(self, user_request: str, context: dict[str, Any] | None = None) -> ExecutionPlan:
        """Generate execution plan from user request.

        Args:
            user_request: The user's request text
            context: Additional context information

        Returns:
            ExecutionPlan with structured steps
        """
        import uuid

        plan_id = str(uuid.uuid4())[:8]
        context = context or {}

        # Classify task type
        task_type = self._classify_task(user_request, context)

        # Generate steps
        steps = self._generate_steps(task_type, user_request, context)

        plan = ExecutionPlan(
            plan_id=plan_id,
            original_request=user_request,
            task_type=task_type,
            steps=steps,
            context=context,
        )

        self.plans[plan_id] = plan
        return plan

    def _classify_task(self, request: str, context: dict) -> TaskType:
        """Classify the task type based on request and context."""
        request_lower = request.lower()

        # Question detection
        if any(q in request_lower for q in ["what", "how", "why", "when", "where", "which", "?"]):
            # Check if it's multi-step
            if len(request.split()) > 50 or "and" in request_lower or "then" in request_lower:
                return TaskType.MULTI_STEP
            return TaskType.QUESTION_ANSWER

        # Information retrieval
        if any(k in request_lower for k in ["find", "search", "look for", "retrieve", "get"]):
            return TaskType.INFORMATION_RETRIEVAL

        # Text generation
        if any(k in request_lower for k in ["write", "generate", "create", "compose", "draft"]):
            return TaskType.TEXT_GENERATION

        # Analysis
        if any(k in request_lower for k in ["analyze", "compare", "evaluate", "assess", "review"]):
            return TaskType.ANALYSIS

        # Reasoning
        if any(k in request_lower for k in ["reason", "infer", "deduce", "conclude", "explain"]):
            return TaskType.REASONING

        # Multi-step
        if context.get("multi_step_expected"):
            return TaskType.MULTI_STEP

        return TaskType.UNKNOWN

    def _generate_steps(self, task_type: TaskType, request: str, context: dict) -> list[TaskStep]:
        """Generate execution steps based on task type."""
        import uuid

        steps = []
        required_agents = self.TASK_REQUIREMENTS.get(task_type, [])

        if not required_agents:
            # Default: single step with intent classification
            return [
                TaskStep(
                    step_id=str(uuid.uuid4())[:8],
                    name="classify_intent",
                    description="Classify user intent",
                    agent_type="intent_classification",
                )
            ]

        # Generate steps for each required agent
        for i, agent in enumerate(required_agents):
            step_id = str(uuid.uuid4())[:8]

            # Determine step name and description
            if agent == "intent_classification":
                name = "classify_intent"
                description = "Identify user intent and extract key parameters"
            elif agent == "entity_extraction":
                name = "extract_entities"
                description = "Extract entities (people, places, organizations) from request"
            elif agent == "semantic_search":
                name = "semantic_lookup"
                description = "Perform semantic search for relevant information"
            elif agent == "arxiv":
                name = "search_papers"
                description = "Search academic papers from arXiv"
            elif agent == "matching":
                name = "match_results"
                description = "Match and rank results based on relevance"
            elif agent == "paper_search":
                name = "search_papers"
                description = "Search in local paper repository"
            else:
                name = f"step_{i}"
                description = f"Execute {agent} task"

            # Set dependencies (previous step)
            dependencies = [steps[-1].step_id] if steps else []

            step = TaskStep(
                step_id=step_id,
                name=name,
                description=description,
                agent_type=agent,
                dependencies=dependencies,
            )
            steps.append(step)

        return steps

    def get_plan(self, plan_id: str) -> ExecutionPlan | None:
        """Get plan by ID."""
        return self.plans.get(plan_id)

    def update_step_status(
        self, plan_id: str, step_id: str, status: StepStatus, output: Any = None, error: str | None = None
    ) -> bool:
        """Update step execution status."""
        plan = self.plans.get(plan_id)
        if not plan:
            return False

        step = plan.get_step(step_id)
        if not step:
            return False

        step.status = status
        step.output = output
        step.error = error
        return True


# Global planner instance
_planner: TaskPlanner | None = None


def get_planner() -> TaskPlanner:
    """Get global task planner instance."""
    global _planner
    if _planner is None:
        _planner = TaskPlanner()
    return _planner
