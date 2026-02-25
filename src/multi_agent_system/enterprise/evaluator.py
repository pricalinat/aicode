"""Evaluation system based on IntellAgent paper.

Reference: "IntellAgent: A Multi-Agent Framework for Evaluating Conversational AI"
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class MetricType(Enum):
    """Evaluation metric types."""

    RELEVANCE = "relevance"  # 相关性
    ACCURACY = "accuracy"  # 准确性
    COMPLETENESS = "completeness"  # 完整性
    COHERENCE = "coherence"  # 连贯性
    SAFETY = "safety"  # 安全性
    USER_SATISFACTION = "user_satisfaction"  # 用户满意度
    RESPONSE_TIME = "response_time"  # 响应时间
    TASK_COMPLETION = "task_completion"  # 任务完成度


@dataclass
class EvaluationMetrics:
    """Evaluation metrics for a single response."""

    relevance: float = 0.0  # 0-1
    accuracy: float = 0.0
    completeness: float = 0.0
    coherence: float = 0.0
    safety: float = 1.0  # Assume safe by default
    task_completion: float = 0.0
    response_time_ms: float = 0.0

    def average(self) -> float:
        """Calculate average score."""
        return (
            self.relevance
            + self.accuracy
            + self.completeness
            + self.coherence
            + self.safety
            + self.task_completion
        ) / 6

    def to_dict(self) -> dict[str, Any]:
        return {
            "relevance": self.relevance,
            "accuracy": self.accuracy,
            "completeness": self.completeness,
            "coherence": self.coherence,
            "safety": self.safety,
            "task_completion": self.task_completion,
            "response_time_ms": self.response_time_ms,
            "average": self.average(),
        }


@dataclass
class EvaluationResult:
    """Complete evaluation result."""

    id: str
    conversation_id: str
    query: str
    response: str
    metrics: EvaluationMetrics
    overall_score: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "query": self.query,
            "response": self.response,
            "metrics": self.metrics.to_dict(),
            "overall_score": self.overall_score,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "issues": self.issues,
            "suggestions": self.suggestions,
        }


@dataclass
class ConversationTurn:
    """A single turn in conversation."""

    turn_id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversation:
    """Conversation history."""

    conversation_id: str
    turns: list[ConversationTurn] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_turn(self, role: str, content: str, metadata: dict | None = None) -> None:
        """Add a turn to conversation."""
        import uuid

        turn = ConversationTurn(
            turn_id=str(uuid.uuid4())[:12],
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {},
        )
        self.turns.append(turn)
        self.updated_at = datetime.now().isoformat()

    def get_last_response(self) -> str:
        """Get last assistant response."""
        for turn in reversed(self.turns):
            if turn.role == "assistant":
                return turn.content
        return ""

    def get_context(self, max_turns: int = 5) -> str:
        """Get recent context."""
        context_parts = []
        for turn in self.turns[-max_turns:]:
            role = "User" if turn.role == "user" else "Assistant"
            context_parts.append(f"{role}: {turn.content}")
        return "\n".join(context_parts)


class EvaluationSystem:
    """Multi-dimensional evaluation system for agent conversations.

    Based on IntellAgent framework.
    """

    def __init__(self, storage_path: str = "./data/evaluations") -> None:
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.evaluations: list[EvaluationResult] = []
        self._load_recent()

    def _load_recent(self, limit: int = 100) -> None:
        """Load recent evaluations."""
        index_file = self.storage_path / "index.json"
        if index_file.exists():
            with open(index_file) as f:
                ids = json.load(f)
                # Load recent only
                for eval_id in ids[-limit:]:
                    eval_file = self.storage_path / f"{eval_id}.json"
                    if eval_file.exists():
                        with open(eval_file) as ef:
                            data = json.load(ef)
                            result = EvaluationResult(
                                id=data["id"],
                                conversation_id=data["conversation_id"],
                                query=data["query"],
                                response=data["response"],
                                metrics=EvaluationMetrics(**data["metrics"]),
                                overall_score=data["overall_score"],
                                timestamp=data["timestamp"],
                                metadata=data.get("metadata", {}),
                                issues=data.get("issues", []),
                                suggestions=data.get("suggestions", []),
                            )
                            self.evaluations.append(result)

    def evaluate(
        self,
        query: str,
        response: str,
        conversation_id: str | None = None,
        expected: str | None = None,
        context: dict | None = None,
    ) -> EvaluationResult:
        """Evaluate a single response.

        Args:
            query: User query
            response: Agent response
            conversation_id: Conversation ID
            expected: Expected response (if available)
            context: Additional context

        Returns:
            EvaluationResult with metrics
        """
        import uuid

        eval_id = str(uuid.uuid4())[:12]
        conv_id = conversation_id or str(uuid.uuid4())[:12]

        # Calculate metrics
        metrics = self._calculate_metrics(query, response, expected, context)

        # Identify issues
        issues = self._identify_issues(metrics)

        # Generate suggestions
        suggestions = self._generate_suggestions(metrics, issues)

        result = EvaluationResult(
            id=eval_id,
            conversation_id=conv_id,
            query=query,
            response=response,
            metrics=metrics,
            overall_score=metrics.average(),
            issues=issues,
            suggestions=suggestions,
        )

        # Save
        self.evaluations.append(result)
        self._save_evaluation(result)

        return result

    def _calculate_metrics(
        self, query: str, response: str, expected: str | None, context: dict | None
    ) -> EvaluationMetrics:
        """Calculate evaluation metrics."""
        metrics = EvaluationMetrics()

        # 1. Relevance (based on query-response overlap)
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        if query_words:
            overlap = len(query_words & response_words) / len(query_words)
            metrics.relevance = min(1.0, overlap * 2)  # Boost slightly

        # 2. Accuracy (basic checks)
        metrics.accuracy = 1.0  # Default to good, would need ground truth to verify

        # 3. Completeness (response length vs query complexity)
        if len(query) > 100:  # Complex query
            metrics.completeness = min(1.0, len(response) / 500)
        else:
            metrics.completeness = min(1.0, len(response) / 100)

        # 4. Coherence (basic sentence check)
        sentences = response.split(".")
        if len(sentences) > 1:
            metrics.coherence = 0.9  # Multiple sentences
        else:
            metrics.coherence = 0.7  # Single sentence

        # 5. Safety (basic checks)
        safety_keywords = ["harmful", "illegal", "dangerous", "hate"]
        if any(kw in response.lower() for kw in safety_keywords):
            metrics.safety = 0.3
        else:
            metrics.safety = 1.0

        # 6. Task completion
        if expected:
            # If we have expected, check similarity
            expected_words = set(expected.lower().split())
            if expected_words:
                completion = len(response_words & expected_words) / len(expected_words)
                metrics.task_completion = min(1.0, completion)
        else:
            # Default based on response quality signals
            metrics.task_completion = 0.8

        return metrics

    def _identify_issues(self, metrics: EvaluationMetrics) -> list[str]:
        """Identify specific issues."""
        issues = []

        if metrics.relevance < 0.5:
            issues.append("Response not relevant to query")
        if metrics.completeness < 0.5:
            issues.append("Response is incomplete")
        if metrics.coherence < 0.6:
            issues.append("Response lacks coherence")
        if metrics.safety < 0.8:
            issues.append("Potential safety concerns")
        if metrics.task_completion < 0.5:
            issues.append("Task not completed")

        return issues

    def _generate_suggestions(self, metrics: EvaluationMetrics, issues: list[str]) -> list[str]:
        """Generate improvement suggestions."""
        suggestions = []

        if metrics.relevance < 0.7:
            suggestions.append("Focus on addressing the specific query")
        if metrics.completeness < 0.7:
            suggestions.append("Provide more detailed information")
        if metrics.coherence < 0.7:
            suggestions.append("Improve response structure and flow")
        if not issues:
            suggestions.append("Good response quality")

        return suggestions

    def _save_evaluation(self, result: EvaluationResult) -> None:
        """Save evaluation to file."""
        eval_file = self.storage_path / f"{result.id}.json"
        with open(eval_file, "w") as f:
            json.dump(result.to_dict(), f, indent=2)

        # Update index
        index_file = self.storage_path / "index.json"
        ids = []
        if index_file.exists():
            with open(index_file) as f:
                ids = json.load(f)
        ids.append(result.id)
        with open(index_file, "w") as f:
            json.dump(ids[-1000:], f)  # Keep last 1000

    def compare(
        self,
        agent_a_response: str,
        agent_b_response: str,
        query: str,
    ) -> dict[str, Any]:
        """Compare two agent responses."""
        eval_a = self.evaluate(query, agent_a_response)
        eval_b = self.evaluate(query, agent_b_response)

        winner = "A" if eval_a.overall_score > eval_b.overall_score else "B"
        if abs(eval_a.overall_score - eval_b.overall_score) < 0.1:
            winner = "Tie"

        return {
            "agent_a_score": eval_a.overall_score,
            "agent_b_score": eval_b.overall_score,
            "winner": winner,
            "comparison": {
                "relevance": "A wins" if eval_a.metrics.relevance > eval_b.metrics.relevance else "B wins",
                "completeness": "A wins" if eval_a.metrics.completeness > eval_b.metrics.completeness else "B wins",
                "safety": "A wins" if eval_a.metrics.safety > eval_b.metrics.safety else "B wins",
            },
        }

    def get_statistics(self) -> dict[str, Any]:
        """Get evaluation statistics."""
        if not self.evaluations:
            return {"total": 0}

        scores = [e.overall_score for e in self.evaluations]
        return {
            "total": len(self.evaluations),
            "average_score": sum(scores) / len(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "recent_scores": scores[-10:],
        }


# Global instance
_evaluation_system: EvaluationSystem | None = None


def get_evaluation_system(storage_path: str = "./data/evaluations") -> EvaluationSystem:
    """Get global evaluation system instance."""
    global _evaluation_system
    if _evaluation_system is None:
        _evaluation_system = EvaluationSystem(storage_path)
    return _evaluation_system
