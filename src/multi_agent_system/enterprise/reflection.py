"""Agent Reflection and Self-Correction System.

Based on "ODA: Observation-Driven Agent" and related work on agent self-reflection,
self-correction, and iterative improvement.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class ReflectionType(Enum):
    """Types of reflection."""
    RESULT_CHECK = "result_check"       # Check if result is correct
    PLAN_REVIEW = "plan_review"         # Review execution plan
    ERROR_ANALYSIS = "error_analysis"   # Analyze errors
    QUALITY_ASSESS = "quality_assess"  # Assess output quality
    STRATEGY_ADJUST = "strategy_adjust"  # Adjust strategy


class CorrectionType(Enum):
    """Types of corrections."""
    PARAMETER_ADJUST = "parameter_adjust"  # Adjust parameters
    STRATEGY_CHANGE = "strategy_change"    # Change strategy
    RETRY = "retry"                         # Retry with same approach
    FALLBACK = "fallback"                   # Use alternative approach
    ESCALATE = "escalate"                   # Escalate to human


class ReflectionStatus(Enum):
    """Status of reflection."""
    PENDING = "pending"
    COMPLETED = "completed"
    CORRECTION_APPLIED = "correction_applied"
    FAILED = "failed"


@dataclass
class ReflectionContext:
    """Context for reflection."""
    task: str = ""
    plan: str = ""
    execution_result: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Reflection:
    """A reflection on agent behavior."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    reflection_type: ReflectionType = ReflectionType.RESULT_CHECK

    # Context
    context: ReflectionContext = field(default_factory=ReflectionContext)

    # Analysis
    status: ReflectionStatus = ReflectionStatus.PENDING
    observations: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)

    # Assessment
    quality_score: float = 0.0  # 0-1
    confidence: float = 0.0     # 0-1

    # Correction
    correction: CorrectionType | None = None
    correction_details: str = ""
    correction_result: Any = None

    # Metadata
    reflection_time_ms: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    applied_at: datetime | None = None

    def is_successful(self) -> bool:
        """Check if reflection indicates success."""
        return self.quality_score >= 0.7 and len(self.issues) == 0

    def needs_correction(self) -> bool:
        """Check if correction is needed."""
        return self.quality_score < 0.5 or len(self.issues) > 0


@dataclass
class CorrectionPlan:
    """Plan for correcting identified issues."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    reflection_id: str = ""
    corrections: list[dict[str, Any]] = field(default_factory=list)
    priority: int = 0  # Higher = more urgent
    estimated_impact: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


class ReflectionEngine:
    """Engine for agent reflection and self-correction.

    Features:
    - Automatic result validation
    - Error analysis and recovery suggestions
    - Quality assessment
    - Strategy adjustment
    """

    def __init__(
        self,
        quality_threshold: float = 0.7,
        max_retries: int = 3,
    ) -> None:
        """Initialize reflection engine.

        Args:
            quality_threshold: Minimum quality score to consider successful
            max_retries: Maximum retry attempts
        """
        self.quality_threshold = quality_threshold
        self.max_retries = max_retries

        # Reflection history
        self._reflections: list[Reflection] = []

        # Custom analyzers
        self._analyzers: dict[ReflectionType, Callable] = {}

        # Statistics
        self._stats = {
            "total_reflections": 0,
            "successful": 0,
            "corrected": 0,
            "failed": 0,
        }

    def register_analyzer(
        self,
        reflection_type: ReflectionType,
        analyzer: Callable[[ReflectionContext], Reflection],
    ) -> None:
        """Register custom analyzer for reflection type."""
        self._analyzers[reflection_type] = analyzer

    async def reflect(
        self,
        context: ReflectionContext,
        reflection_type: ReflectionType = ReflectionType.RESULT_CHECK,
    ) -> Reflection:
        """Perform reflection on execution context.

        Args:
            context: Execution context
            reflection_type: Type of reflection to perform

        Returns:
            Reflection result
        """
        start_time = datetime.now()

        reflection = Reflection(
            reflection_type=reflection_type,
            context=context,
        )

        # Use custom analyzer if registered
        if reflection_type in self._analyzers:
            result = self._analyzers[reflection_type](context)
            reflection = result
        else:
            # Use default reflection logic
            reflection = await self._default_reflect(reflection)

        # Calculate reflection time
        reflection.reflection_time_ms = int(
            (datetime.now() - start_time).total_seconds() * 1000
        )

        # Store reflection
        self._reflections.append(reflection)
        self._stats["total_reflections"] += 1

        if reflection.is_successful():
            self._stats["successful"] += 1
        elif reflection.needs_correction():
            self._stats["corrected"] += 1
        else:
            self._stats["failed"] += 1

        return reflection

    async def _default_reflect(self, reflection: Reflection) -> Reflection:
        """Default reflection logic."""
        context = reflection.context

        # Analyze based on type
        if reflection.reflection_type == ReflectionType.RESULT_CHECK:
            await self._check_result(reflection)
        elif reflection.reflection_type == ReflectionType.ERROR_ANALYSIS:
            await self._analyze_error(reflection)
        elif reflection.reflection_type == ReflectionType.QUALITY_ASSESS:
            await self._assess_quality(reflection)

        # Determine status
        if reflection.is_successful():
            reflection.status = ReflectionStatus.COMPLETED
        elif reflection.needs_correction():
            reflection.status = ReflectionStatus.COMPLETED
            # Generate correction
            reflection.correction = self._suggest_correction(reflection)
            if reflection.correction:
                reflection.status = ReflectionStatus.CORRECTION_APPLIED
        else:
            reflection.status = ReflectionStatus.FAILED

        return reflection

    async def _check_result(self, reflection: Reflection) -> None:
        """Check if result is correct."""
        context = reflection.context

        # Check for errors
        if context.error:
            reflection.issues.append(f"Error occurred: {context.error}")

        # Check result quality
        if context.execution_result is None:
            reflection.issues.append("No result produced")
        else:
            reflection.strengths.append("Result produced")

            # Check result type
            if isinstance(context.execution_result, dict):
                if "error" in context.execution_result:
                    reflection.issues.append(f"Result contains error: {context.execution_result['error']}")
                elif "success" in context.execution_result and context.execution_result["success"]:
                    reflection.strengths.append("Result indicates success")

        # Calculate quality score
        if len(reflection.issues) == 0:
            reflection.quality_score = 1.0
        else:
            reflection.quality_score = max(0.0, 1.0 - len(reflection.issues) * 0.3)

    async def _analyze_error(self, reflection: Reflection) -> None:
        """Analyze error and suggest fixes."""
        context = reflection.context

        if not context.error:
            reflection.observations.append("No error to analyze")
            reflection.quality_score = 1.0
            return

        error = context.error.lower()

        # Categorize error
        if "timeout" in error:
            reflection.issues.append("Timeout error - operation took too long")
            reflection.correction = CorrectionType.PARAMETER_ADJUST
            reflection.correction_details = "Increase timeout or optimize operation"
        elif "not found" in error or "404" in error:
            reflection.issues.append("Resource not found")
            reflection.correction = CorrectionType.FALLBACK
            reflection.correction_details = "Try alternative resource or create new"
        elif "permission" in error or "denied" in error:
            reflection.issues.append("Permission error")
            reflection.correction = CorrectionType.ESCALATE
            reflection.correction_details = "Request elevated permissions"
        elif "invalid" in error or "400" in error:
            reflection.issues.append("Invalid input or parameters")
            reflection.correction = CorrectionType.PARAMETER_ADJUST
            reflection.correction_details = "Validate and fix input parameters"
        else:
            reflection.issues.append(f"Unknown error: {context.error}")
            reflection.correction = CorrectionType.RETRY

        # Calculate quality score
        reflection.quality_score = max(0.0, 1.0 - len(reflection.issues) * 0.4)

    async def _assess_quality(self, reflection: Reflection) -> None:
        """Assess output quality."""
        # This would typically use an LLM for quality assessment
        # Here we use simple heuristics

        context = reflection.context

        if context.execution_result:
            # Check result structure
            if isinstance(context.execution_result, str):
                # Text result
                if len(context.execution_result) < 10:
                    reflection.issues.append("Result too short")
                elif len(context.execution_result) > 10000:
                    reflection.issues.append("Result excessively long")
                else:
                    reflection.strengths.append("Result length appropriate")
            elif isinstance(context.execution_result, dict):
                reflection.strengths.append("Result is structured")

        # Quality score
        reflection.quality_score = 1.0 - (len(reflection.issues) * 0.25)

    def _suggest_correction(self, reflection: Reflection) -> CorrectionType:
        """Suggest correction type based on reflection."""
        if reflection.reflection_type == ReflectionType.ERROR_ANALYSIS:
            return reflection.correction or CorrectionType.RETRY

        # For other types, default to retry
        return CorrectionType.RETRY

    async def correct_and_retry(
        self,
        context: ReflectionContext,
        max_attempts: int | None = None,
    ) -> tuple[Reflection, Any]:
        """Reflect, apply correction, and retry.

        Args:
            context: Execution context
            max_attempts: Maximum attempts (uses default if None)

        Returns:
            Tuple of (final reflection, final result)
        """
        max_attempts = max_attempts or self.max_retries
        last_result = context.execution_result

        for attempt in range(max_attempts):
            # Reflect
            reflection = await self.reflect(context, ReflectionType.RESULT_CHECK)

            if reflection.is_successful():
                return reflection, context.execution_result

            # Apply correction if suggested
            if reflection.correction == CorrectionType.RETRY:
                # Simple retry
                pass
            elif reflection.correction == CorrectionType.PARAMETER_ADJUST:
                # Adjust parameters (would need custom logic)
                pass
            elif reflection.correction == CorrectionType.FALLBACK:
                # Use fallback approach
                pass

            # If last attempt, return failure
            if attempt == max_attempts - 1:
                reflection.status = ReflectionStatus.FAILED
                return reflection, None

        return reflection, last_result

    def get_reflection_history(
        self,
        limit: int = 100,
        reflection_type: ReflectionType | None = None,
    ) -> list[Reflection]:
        """Get reflection history."""
        reflections = self._reflections

        if reflection_type:
            reflections = [r for r in reflections if r.reflection_type == reflection_type]

        return reflections[-limit:]

    def get_statistics(self) -> dict[str, Any]:
        """Get reflection statistics."""
        total = self._stats["total_reflections"]
        return {
            **self._stats,
            "success_rate": self._stats["successful"] / total if total > 0 else 0,
            "correction_rate": self._stats["corrected"] / total if total > 0 else 0,
        }


# Global reflection engine
_reflection_engine: ReflectionEngine | None = None


def get_reflection_engine() -> ReflectionEngine:
    """Get global reflection engine."""
    global _reflection_engine
    if _reflection_engine is None:
        _reflection_engine = ReflectionEngine()
    return _reflection_engine
