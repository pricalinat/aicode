"""Workflow orchestration for multi-step tasks."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """Step execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    name: str
    handler: Callable[[dict], dict]
    required: bool = True
    retry_count: int = 0
    timeout: float = 30.0


@dataclass
class StepResult:
    """Result of a workflow step execution."""
    step_name: str
    status: StepStatus
    output: dict | None = None
    error: str | None = None
    duration_ms: float = 0.0


@dataclass
class WorkflowResult:
    """Result of a workflow execution."""
    workflow_name: str
    status: WorkflowStatus
    steps: List[StepResult] = field(default_factory=list)
    output: dict | None = None
    error: str | None = None
    duration_ms: float = 0.0


class Workflow:
    """A workflow consisting of multiple steps."""
    
    def __init__(self, name: str, steps: List[WorkflowStep] | None = None) -> None:
        self.name = name
        self.steps: List[WorkflowStep] = steps or []
        self._step_map: Dict[str, WorkflowStep] = {s.name: s for s in self.steps}
    
    def add_step(self, step: WorkflowStep) -> "Workflow":
        """Add a step to the workflow."""
        self.steps.append(step)
        self._step_map[step.name] = step
        return self
    
    def add_step_fn(
        self,
        name: str,
        handler: Callable[[dict], dict],
        required: bool = True,
        retry_count: int = 0,
    ) -> "Workflow":
        """Add a step function to the workflow."""
        step = WorkflowStep(
            name=name,
            handler=handler,
            required=required,
            retry_count=retry_count,
        )
        return self.add_step(step)
    
    def execute(self, input_data: dict) -> WorkflowResult:
        """Execute the workflow."""
        import time
        start_time = time.perf_counter()
        
        steps_result: List[StepResult] = []
        current_data = input_data.copy()
        
        for step in self.steps:
            step_start = time.perf_counter()
            
            try:
                # Execute step
                output = step.handler(current_data)
                current_data.update(output)
                
                step_duration = (time.perf_counter() - step_start) * 1000
                steps_result.append(StepResult(
                    step_name=step.name,
                    status=StepStatus.COMPLETED,
                    output=output,
                    duration_ms=step_duration,
                ))
                
            except Exception as e:
                step_duration = (time.perf_counter() - step_start) * 1000
                
                if step.retry_count > 0:
                    # Try retries
                    for _ in range(step.retry_count):
                        try:
                            output = step.handler(current_data)
                            current_data.update(output)
                            steps_result.append(StepResult(
                                step_name=step.name,
                                status=StepStatus.COMPLETED,
                                output=output,
                                duration_ms=step_duration,
                            ))
                            break
                        except:
                            continue
                    else:
                        # All retries failed
                        if step.required:
                            return WorkflowResult(
                                workflow_name=self.name,
                                status=WorkflowStatus.FAILED,
                                steps=steps_result,
                                error=str(e),
                                duration_ms=(time.perf_counter() - start_time) * 1000,
                            )
                        else:
                            steps_result.append(StepResult(
                                step_name=step.name,
                                status=StepStatus.SKIPPED,
                                error=str(e),
                                duration_ms=step_duration,
                            ))
                else:
                    if step.required:
                        return WorkflowResult(
                            workflow_name=self.name,
                            status=WorkflowStatus.FAILED,
                            steps=steps_result,
                            error=str(e),
                            duration_ms=(time.perf_counter() - start_time) * 1000,
                        )
                    else:
                        steps_result.append(StepResult(
                            step_name=step.name,
                            status=StepStatus.SKIPPED,
                            error=str(e),
                            duration_ms=step_duration,
                        ))
        
        return WorkflowResult(
            workflow_name=self.name,
            status=WorkflowStatus.COMPLETED,
            steps=steps_result,
            output=current_data,
            duration_ms=(time.perf_counter() - start_time) * 1000,
        )


class WorkflowEngine:
    """Engine for managing and executing workflows."""
    
    def __init__(self) -> None:
        self._workflows: Dict[str, Workflow] = {}
    
    def register(self, workflow: Workflow) -> None:
        """Register a workflow."""
        self._workflows[workflow.name] = workflow
    
    def execute(self, workflow_name: str, input_data: dict) -> WorkflowResult:
        """Execute a workflow by name."""
        workflow = self._workflows.get(workflow_name)
        if not workflow:
            return WorkflowResult(
                workflow_name=workflow_name,
                status=WorkflowStatus.FAILED,
                error=f"Workflow not found: {workflow_name}",
            )
        
        return workflow.execute(input_data)
    
    def list_workflows(self) -> List[str]:
        """List all registered workflows."""
        return list(self._workflows.keys())


# Global workflow engine
_workflow_engine: WorkflowEngine | None = None


def get_workflow_engine() -> WorkflowEngine:
    """Get the global workflow engine."""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
    return _workflow_engine


# Convenience function to create common workflows
def create_matching_workflow() -> Workflow:
    """Create a standard matching workflow."""
    from ..agents import EntityExtractionAgent, IntentClassificationAgent, MatchingAgent
    from ..core import Message
    
    def extract_entities(data: dict) -> dict:
        agent = EntityExtractionAgent()
        msg = Message(task_type="extract_entities", content={"text": data["text"]})
        resp = agent.handle(msg)
        return {"entities": resp.data}
    
    def classify_intent(data: dict) -> dict:
        agent = IntentClassificationAgent()
        msg = Message(task_type="classify_intent", content={"text": data["text"]})
        resp = agent.handle(msg)
        return {"intent": resp.data}
    
    def match(data: dict) -> dict:
        agent = MatchingAgent()
        msg = Message(
            task_type="match",
            content={
                "direction": data.get("direction", "人找供给"),
                "query": data.get("query", {}),
            },
        )
        resp = agent.handle(msg)
        return {"matches": resp.data}
    
    return Workflow("matching").add_step_fn("extract_entities", extract_entities) \
        .add_step_fn("classify_intent", classify_intent) \
        .add_step_fn("match", match)
