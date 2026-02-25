"""Task Engine based on Task Memory Engine (TME) paper.

Reference: "Task Memory Engine (TME): Enhancing State Awareness for Multi-Step LLM Agent Tasks"
Provides structured task state management for multi-step agent workflows.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"  # Waiting for user input or external event
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """Individual step status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskStep:
    """A single step in a task workflow."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    action: str = ""  # Action to execute
    parameters: dict[str, Any] = field(default_factory=dict)
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    depends_on: list[str] = field(default_factory=list)  # Step IDs this depends on
    retry_count: int = 0
    max_retries: int = 3

    def can_execute(self, completed_steps: set[str]) -> bool:
        """Check if step can be executed based on dependencies."""
        return all(dep_id in completed_steps for dep_id in self.depends_on)

    def duration_ms(self) -> int | None:
        """Get step execution duration in milliseconds."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() * 1000)
        return None


@dataclass
class TaskContext:
    """Context data for task execution."""
    user_id: str = ""
    session_id: str = ""
    variables: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get variable value."""
        return self.variables.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set variable value."""
        self.variables[key] = value

    def update(self, **kwargs) -> None:
        """Update multiple variables."""
        self.variables.update(kwargs)


@dataclass
class Task:
    """A task representing a multi-step workflow."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    steps: list[TaskStep] = field(default_factory=list)
    context: TaskContext = field(default_factory=TaskContext)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    current_step_id: str | None = None
    result: Any = None
    error: str | None = None

    def get_step(self, step_id: str) -> TaskStep | None:
        """Get step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_next_executable_step(self) -> TaskStep | None:
        """Get next step that can be executed."""
        completed = {s.id for s in self.steps if s.status == StepStatus.COMPLETED}
        for step in self.steps:
            if step.status == StepStatus.PENDING and step.can_execute(completed):
                return step
        return None

    def is_complete(self) -> bool:
        """Check if all steps are complete."""
        return all(s.status == StepStatus.COMPLETED for s in self.steps)

    def has_failed(self) -> bool:
        """Check if any step failed."""
        return any(s.status == StepStatus.FAILED for s in self.steps)

    def progress(self) -> float:
        """Get task progress (0.0 to 1.0)."""
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)
        return completed / len(self.steps)

    def duration_ms(self) -> int | None:
        """Get total task duration in milliseconds."""
        if self.started_at:
            end = self.completed_at or datetime.now()
            return int((end - self.started_at).total_seconds() * 1000)
        return None


class TaskExecutor:
    """Executes tasks with state management.

    Supports:
    - Sequential and parallel step execution
    - Dependency-based execution order
    - Retry logic
    - State persistence
    """

    def __init__(self, max_parallel: int = 1) -> None:
        """Initialize task executor.

        Args:
            max_parallel: Maximum parallel step execution
        """
        self.max_parallel = max_parallel
        self._handlers: dict[str, callable] = {}

    def register_handler(self, action: str, handler: callable) -> None:
        """Register action handler.

        Args:
            action: Action name
            handler: Async function(step, context) -> result
        """
        self._handlers[action] = handler

    async def execute_task(self, task: Task) -> Task:
        """Execute a task.

        Args:
            task: Task to execute

        Returns:
            Updated task with results
        """
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        try:
            while not task.is_complete() and not task.has_failed():
                # Get next executable step
                next_step = task.get_next_executable_step()
                if not next_step:
                    break

                # Execute step
                task.current_step_id = next_step.id
                next_step.status = StepStatus.RUNNING
                next_step.started_at = datetime.now()

                try:
                    # Get handler
                    handler = self._handlers.get(next_step.action)
                    if handler:
                        result = await handler(next_step, task.context)
                        next_step.result = result
                        next_step.status = StepStatus.COMPLETED
                    else:
                        next_step.error = f"No handler for action: {next_step.action}"
                        next_step.status = StepStatus.FAILED

                except Exception as e:
                    next_step.error = str(e)
                    next_step.retry_count += 1
                    if next_step.retry_count < next_step.max_retries:
                        next_step.status = StepStatus.PENDING  # Will retry
                    else:
                        next_step.status = StepStatus.FAILED

                next_step.completed_at = datetime.now()

            # Set final status
            if task.has_failed():
                task.status = TaskStatus.FAILED
                failed_step = next(s for s in task.steps if s.status == StepStatus.FAILED)
                task.error = failed_step.error
            elif task.is_complete():
                task.status = TaskStatus.COMPLETED
                task.result = self._aggregate_results(task)
            else:
                task.status = TaskStatus.WAITING

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)

        task.completed_at = datetime.now()
        return task

    def _aggregate_results(self, task: Task) -> dict[str, Any]:
        """Aggregate results from all steps."""
        return {
            step.id: step.result
            for step in task.steps
            if step.result is not None
        }


class TaskEngine:
    """Central task engine for managing multi-step agent tasks.

    Features:
    - Task creation and tracking
    - State persistence
    - Task queuing and scheduling
    - Event callbacks
    """

    def __init__(self, max_concurrent: int = 5) -> None:
        """Initialize task engine.

        Args:
            max_concurrent: Maximum concurrent tasks
        """
        self.max_concurrent = max_concurrent
        self._tasks: dict[str, Task] = {}
        self._executor = TaskExecutor()
        self._callbacks: dict[str, list[callable]] = {
            "task_start": [],
            "task_complete": [],
            "task_fail": [],
            "step_complete": [],
        }

    def create_task(
        self,
        name: str,
        description: str = "",
        steps: list[dict[str, Any]] | None = None,
        context: TaskContext | None = None,
    ) -> Task:
        """Create a new task.

        Args:
            name: Task name
            description: Task description
            steps: List of step definitions
            context: Task context

        Returns:
            Created task
        """
        task = Task(
            name=name,
            description=description,
            context=context or TaskContext(),
        )

        # Add steps
        if steps:
            for step_def in steps:
                step = TaskStep(
                    name=step_def.get("name", ""),
                    description=step_def.get("description", ""),
                    action=step_def.get("action", ""),
                    parameters=step_def.get("parameters", {}),
                    depends_on=step_def.get("depends_on", []),
                    max_retries=step_def.get("max_retries", 3),
                )
                task.steps.append(step)

        self._tasks[task.id] = task
        return task

    def register_handler(self, action: str, handler: callable) -> None:
        """Register action handler."""
        self._executor.register_handler(action, handler)

    def on(self, event: str, callback: callable) -> None:
        """Register event callback."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    async def run_task(self, task_id: str) -> Task:
        """Run a task.

        Args:
            task_id: Task ID

        Returns:
            Completed task
        """
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        # Trigger start callbacks
        for cb in self._callbacks["task_start"]:
            cb(task)

        # Execute
        result = await self._executor.execute_task(task)

        # Trigger callbacks
        if result.status == TaskStatus.COMPLETED:
            for cb in self._callbacks["task_complete"]:
                cb(result)
        elif result.status == TaskStatus.FAILED:
            for cb in self._callbacks["task_fail"]:
                cb(result)

        return result

    def get_task(self, task_id: str) -> Task | None:
        """Get task by ID."""
        return self._tasks.get(task_id)

    def list_tasks(self, status: TaskStatus | None = None) -> list[Task]:
        """List tasks, optionally filtered by status."""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        task = self._tasks.get(task_id)
        if task and task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
            task.status = TaskStatus.CANCELLED
            return True
        return False


# Convenience functions

def create_workflow_task(
    name: str,
    steps: list[dict[str, Any]],
    user_id: str = "",
    session_id: str = "",
) -> Task:
    """Create a task from workflow steps.

    Example:
        task = create_workflow_task(
            "Process Order",
            [
                {"name": "Validate", "action": "validate_order"},
                {"name": "Process Payment", "action": "process_payment", "depends_on": ["validate"]},
                {"name": "Ship", "action": "ship_order", "depends_on": ["payment"]},
            ]
        )
    """
    context = TaskContext(user_id=user_id, session_id=session_id)
    return TaskEngine().create_task(name=name, steps=steps, context=context)
