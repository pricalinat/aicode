"""Self-optimizing agent system based on AccelOpt paper.

Reference: "AccelOpt: A Self-Improving LLM Agentic System for AI Accelerator Kernel Optimization"

Enables agents to learn from past experiences and continuously improve.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Experience:
    """A single experience/lesson learned."""

    id: str
    task_type: str
    input_data: dict[str, Any]
    output: Any
    success: bool
    feedback: str | None = None
    improvement_hints: list[str] = field(default_factory=list)
    timestamp: float = 0.0


@dataclass
class OptimizationMemory:
    """Memory that stores experiences and insights for optimization."""

    task_type: str
    successful_patterns: list[dict] = field(default_factory=list)
    failed_patterns: list[dict] = field(default_factory=list)
    best_prompts: list[dict] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)


class SelfOptimizingAgent:
    """Self-optimizing agent that learns from experiences.

    Features:
    - Experience accumulation
    - Pattern discovery
    - Prompt optimization
    - Performance tracking
    """

    def __init__(self, storage_path: str = "./data/optimization") -> None:
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.experiences: list[Experience] = []
        self.optimization_memory: dict[str, OptimizationMemory] = {}

        self._load_experiences()

    def _load_experiences(self) -> None:
        """Load experiences from storage."""
        exp_file = self.storage_path / "experiences.json"
        if exp_file.exists():
            with open(exp_file) as f:
                data = json.load(f)
                for exp_data in data:
                    self.experiences.append(Experience(**exp_data))

        # Build optimization memory
        self._build_optimization_memory()

    def _save_experiences(self) -> None:
        """Save experiences to storage."""
        exp_file = self.storage_path / "experiences.json"
        data = [exp.to_dict() for exp in self.experiences]
        with open(exp_file, "w") as f:
            json.dump(data, f, indent=2)

    def _build_optimization_memory(self) -> None:
        """Build optimization memory from experiences."""
        # Group by task type
        task_experiences: dict[str, list[Experience]] = {}
        for exp in self.experiences:
            if exp.task_type not in task_experiences:
                task_experiences[exp.task_type] = []
            task_experiences[exp.task_type].append(exp)

        # Build memory for each task type
        for task_type, exps in task_experiences.items():
            memory = OptimizationMemory(task_type=task_type)

            successful = [e for e in exps if e.success]
            failed = [e for e in exps if not e.success]

            # Extract patterns
            for exp in successful[:50]:  # Keep last 50
                memory.successful_patterns.append({
                    "input": str(exp.input_data)[:200],
                    "output": str(exp.output)[:200] if exp.output else "",
                    "hints": exp.improvement_hints,
                })

            for exp in failed[:20]:  # Keep last 20
                memory.failed_patterns.append({
                    "input": str(exp.input_data)[:200],
                    "error": exp.feedback,
                })

            # Calculate metrics
            if exps:
                memory.metrics = {
                    "total_attempts": len(exps),
                    "success_rate": len(successful) / len(exps),
                    "avg_confidence": sum(e.improvement_hints for e in successful) / max(1, len(successful)),
                }

            self.optimization_memory[task_type] = memory

    def record_experience(
        self,
        task_type: str,
        input_data: dict[str, Any],
        output: Any,
        success: bool,
        feedback: str | None = None,
    ) -> str:
        """Record a new experience."""
        import uuid
        import time

        exp_id = str(uuid.uuid4())[:12]

        # Generate improvement hints based on success
        hints = []
        if success:
            hints.append("This approach worked well")
        else:
            hints.append("Consider alternative approaches")

        experience = Experience(
            id=exp_id,
            task_type=task_type,
            input_data=input_data,
            output=output,
            success=success,
            feedback=feedback,
            improvement_hints=hints,
            timestamp=time.time(),
        )

        self.experiences.append(experience)

        # Keep only last 1000 experiences
        if len(self.experiences) > 1000:
            self.experiences = self.experiences[-1000:]

        self._save_experiences()
        self._build_optimization_memory()

        return exp_id

    def get_optimization_hints(self, task_type: str) -> list[str]:
        """Get optimization hints for a task type."""
        memory = self.optimization_memory.get(task_type)
        if not memory:
            return []

        hints = []

        # From successful patterns
        if memory.successful_patterns:
            hints.append(f"Found {len(memory.successful_patterns)} successful approaches")

        # From failed patterns
        if memory.failed_patterns:
            hints.append(f"Learned {len(memory.failed_patterns)} patterns to avoid")

        # Metrics
        if memory.metrics:
            hints.append(f"Current success rate: {memory.metrics.get('success_rate', 0):.1%}")

        return hints

    def get_best_prompt(self, task_type: str) -> str | None:
        """Get the best performing prompt for a task type."""
        memory = self.optimization_memory.get(task_type)
        if not memory or not memory.successful_patterns:
            return None

        # Return the most recent successful pattern
        return memory.successful_patterns[-1].get("input", "")

    def optimize_prompt(self, base_prompt: str, task_type: str) -> str:
        """Optimize a prompt based on past experiences."""
        memory = self.optimization_memory.get(task_type)

        if not memory:
            return base_prompt

        # Build optimized prompt
        optimizations = []

        # Add successful pattern hints
        if memory.successful_patterns:
            patterns = "\n".join([
                f"- {p['input'][:100]}"
                for p in memory.successful_patterns[-3:]
            ])
            optimizations.append(f"Past successful approaches:\n{patterns}")

        # Add failure warnings
        if memory.failed_patterns:
            failures = "\n".join([
                f"- Avoid: {p['input'][:80]}"
                for p in memory.failed_patterns[-2:]
            ])
            optimizations.append(f"Patterns to avoid:\n{failures}")

        if optimizations:
            optimization_text = "\n\n".join(optimizations)
            return f"{base_prompt}\n\n[Optimization Context]\n{optimization_text}"

        return base_prompt

    def get_statistics(self) -> dict[str, Any]:
        """Get optimization statistics."""
        return {
            "total_experiences": len(self.experiences),
            "task_types": list(self.optimization_memory.keys()),
            "memory": {
                task: mem.metrics
                for task, mem in self.optimization_memory.items()
            }
        }


# Global instance
_self_optimizing_agent: SelfOptimizingAgent | None = None


def get_self_optimizing_agent(storage_path: str = "./data/optimization") -> SelfOptimizingAgent:
    """Get global self-optimizing agent instance."""
    global _self_optimizing_agent
    if _self_optimizing_agent is None:
        _self_optimizing_agent = SelfOptimizingAgent(storage_path)
    return _self_optimizing_agent
