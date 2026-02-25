"""Hierarchical Planning System.

Based on research about hierarchical planning for LLM agents,
multi-level task decomposition and execution.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class PlanLevel(Enum):
    """Planning hierarchy levels."""
    STRATEGIC = "strategic"   # High-level goals
    TACTICAL = "tactical"    # Mid-level plans
    EXECUTION = "execution"  # Low-level actions


class PlanStatus(Enum):
    """Plan execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class Goal:
    """A high-level goal."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    priority: int = 0  # Higher = more important
    deadline: datetime | None = None

    # Status
    status: PlanStatus = PlanStatus.PENDING
    progress: float = 0.0  # 0-1

    # Hierarchy
    parent_id: str = ""
    child_plan_ids: list[str] = field(default_factory=list)

    # Metrics
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None


@dataclass
class Task:
    """A task in the plan."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""

    # Level
    level: PlanLevel = PlanLevel.TACTICAL

    # Dependencies
    depends_on: list[str] = field(default_factory=list)

    # Status
    status: PlanStatus = PlanStatus.PENDING
    result: Any = None
    error: str | None = None

    # Timing
    estimated_duration_minutes: int = 0
    actual_duration_minutes: int = 0

    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class Plan:
    """A hierarchical plan."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""

    # Goals
    goals: list[Goal] = field(default_factory=list)

    # Tasks by level
    strategic_tasks: list[Task] = field(default_factory=list)
    tactical_tasks: list[Task] = field(default_factory=list)
    execution_tasks: list[Task] = field(default_factory=list)

    # Status
    status: PlanStatus = PlanStatus.PENDING
    progress: float = 0.0

    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None


class HierarchicalPlanner:
    """Hierarchical planning system.

    Features:
    - Multi-level goal decomposition
    - Strategic, tactical, and execution levels
    - Task dependencies and ordering
    - Progress tracking
    """

    def __init__(self) -> None:
        """Initialize hierarchical planner."""
        self._plans: dict[str, Plan] = {}
        self._goals: dict[str, Goal] = {}
        self._tasks: dict[str, Task] = {}

    def create_plan(
        self,
        name: str,
        description: str = "",
    ) -> Plan:
        """Create a new plan."""
        plan = Plan(name=name, description=description)
        self._plans[plan.id] = plan
        return plan

    def add_goal(
        self,
        plan_id: str,
        name: str,
        description: str = "",
        priority: int = 0,
    ) -> Goal | None:
        """Add a goal to plan."""
        plan = self._plans.get(plan_id)
        if not plan:
            return None

        goal = Goal(
            name=name,
            description=description,
            priority=priority,
        )
        plan.goals.append(goal)
        self._goals[goal.id] = goal
        return goal

    def add_task(
        self,
        plan_id: str,
        name: str,
        level: PlanLevel = PlanLevel.TACTICAL,
        depends_on: list[str] | None = None,
    ) -> Task | None:
        """Add task to plan."""
        plan = self._plans.get(plan_id)
        if not plan:
            return None

        task = Task(
            name=name,
            level=level,
            depends_on=depends_on or [],
        )

        if level == PlanLevel.STRATEGIC:
            plan.strategic_tasks.append(task)
        elif level == PlanLevel.TACTICAL:
            plan.tactical_tasks.append(task)
        else:
            plan.execution_tasks.append(task)

        self._tasks[task.id] = task
        return task

    def decompose_goal(
        self,
        goal_id: str,
        plan_id: str,
    ) -> list[Task] | None:
        """Decompose goal into tasks."""
        goal = self._goals.get(goal_id)
        if not goal:
            return None

        # Create tactical task for goal
        tactical = self.add_task(
            plan_id,
            f"Tactical: {goal.name}",
            PlanLevel.TACTICAL,
        )

        # Create execution tasks
        tasks = []
        for i in range(3):  # Simplified - would use LLM in real impl
            exec_task = self.add_task(
                plan_id,
                f"Execute: {goal.name} - Step {i+1}",
                PlanLevel.EXECUTION,
                depends_on=[tactical.id] if tactical else [],
            )
            if exec_task:
                tasks.append(exec_task)

        return tasks

    def get_executable_tasks(
        self,
        plan_id: str,
    ) -> list[Task]:
        """Get tasks ready to execute."""
        plan = self._plans.get(plan_id)
        if not plan:
            return []

        all_tasks = (
            plan.strategic_tasks +
            plan.tactical_tasks +
            plan.execution_tasks
        )

        executable = []
        completed = {t.id for t in all_tasks if t.status == PlanStatus.COMPLETED}

        for task in all_tasks:
            if task.status == PlanStatus.PENDING:
                if all(dep in completed for dep in task.depends_on):
                    executable.append(task)

        return executable

    def update_progress(self, plan_id: str) -> float:
        """Update plan progress."""
        plan = self._plans.get(plan_id)
        if not plan:
            return 0.0

        all_tasks = (
            plan.strategic_tasks +
            plan.tactical_tasks +
            plan.execution_tasks
        )

        if not all_tasks:
            return 0.0

        completed = sum(1 for t in all_tasks if t.status == PlanStatus.COMPLETED)
        plan.progress = completed / len(all_tasks)

        return plan.progress


# Global planner
_hierarchical_planner: HierarchicalPlanner | None = None


def get_hierarchical_planner() -> HierarchicalPlanner:
    """Get global hierarchical planner."""
    global _hierarchical_planner
    if _hierarchical_planner is None:
        _hierarchical_planner = HierarchicalPlanner()
    return _hierarchical_planner
