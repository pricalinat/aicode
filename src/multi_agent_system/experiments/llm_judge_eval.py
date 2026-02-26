"""LLM-Judge-Compatible Evaluation Framework.

This module provides evaluation capabilities that produce structured outputs
compatible with LLM-as-judge evaluation systems.

Features:
- Rubric-based evaluation with defined criteria
- Calibration hooks for score normalization
- Structured output format for LLM consumption
- Multi-dimensional scoring (relevance, quality, safety, etc.)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable
import json


class EvaluationDimension(Enum):
    """Dimensions for evaluating supply matching quality."""
    RELEVANCE = "relevance"
    QUALITY = "quality"
    SAFETY = "safety"
    DIVERSITY = "diversity"
    FRESHNESS = "freshness"
    COMPLETENESS = "completeness"


class ScoreLevel(Enum):
    """Categorical score levels for LLM judgment."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    VERY_POOR = "very_poor"


@dataclass
class RubricCriterion:
    """A single criterion in the evaluation rubric."""
    dimension: EvaluationDimension
    description: str
    weight: float  # 0.0 to 1.0, relative weight within rubric
    score_range: tuple[float, float]  # min, max

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "description": self.description,
            "weight": self.weight,
            "score_range": list(self.score_range),
        }


@dataclass
class EvaluationScore:
    """A single evaluation score with rationale."""
    dimension: EvaluationDimension
    raw_score: float  # Original score (0-1)
    normalized_score: float  # Normalized to rubric range
    level: ScoreLevel  # Categorical level
    rationale: str  # Explanation for the score
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "raw_score": self.raw_score,
            "normalized_score": self.normalized_score,
            "level": self.level.value,
            "rationale": self.rationale,
            "evidence": self.evidence,
        }


@dataclass
class CalibrationConfig:
    """Configuration for score calibration."""
    method: str = "linear"  # linear, zscore, percentile
    reference_distribution: dict[str, float] | None = None  # For percentile

    @classmethod
    def linear(cls) -> CalibrationConfig:
        """Linear calibration (no change)."""
        return cls(method="linear")

    @classmethod
    def zscore(cls, mean: float, std: float) -> CalibrationConfig:
        """Z-score normalization."""
        return cls(
            method="zscore",
            reference_distribution={"mean": mean, "std": std},
        )

    @classmethod
    def percentile(cls, distribution: dict[str, float]) -> CalibrationConfig:
        """Percentile-based calibration."""
        return cls(method="percentile", reference_distribution=distribution)


@dataclass
class LlmJudgeRubric:
    """Complete rubric for LLM-as-judge evaluation."""

    name: str
    criteria: list[RubricCriterion]
    calibration: CalibrationConfig = field(default_factory=CalibrationConfig.linear)
    version: str = "1.0"

    def __post_init__(self) -> None:
        # Validate weights sum to 1.0
        total_weight = sum(c.weight for c in self.criteria)
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Rubric weights must sum to 1.0, got {total_weight}")

    @classmethod
    def default_supply_matching(cls) -> "LlmJudgeRubric":
        """Default rubric for supply-demand matching evaluation."""
        return cls(
            name="supply_matching_v1",
            version="1.0",
            criteria=[
                RubricCriterion(
                    dimension=EvaluationDimension.RELEVANCE,
                    description="How well does the supply match the user's query or intent?",
                    weight=0.35,
                    score_range=(0.0, 1.0),
                ),
                RubricCriterion(
                    dimension=EvaluationDimension.QUALITY,
                    description="Is the supply from a trusted source with good quality indicators?",
                    weight=0.25,
                    score_range=(0.0, 1.0),
                ),
                RubricCriterion(
                    dimension=EvaluationDimension.SAFETY,
                    description="Does the supply meet safety and compliance requirements?",
                    weight=0.20,
                    score_range=(0.0, 1.0),
                ),
                RubricCriterion(
                    dimension=EvaluationDimension.DIVERSITY,
                    description="Does the result set provide diverse options?",
                    weight=0.10,
                    score_range=(0.0, 1.0),
                ),
                RubricCriterion(
                    dimension=EvaluationDimension.FRESHNESS,
                    description="Is the supply information up-to-date?",
                    weight=0.10,
                    score_range=(0.0, 1.0),
                ),
            ],
        )

    def to_prompt_format(self) -> str:
        """Convert rubric to LLM prompt format."""
        lines = [
            f"# Evaluation Rubric: {self.name}",
            f"Version: {self.version}",
            "",
            "## Scoring Criteria",
            "",
        ]

        for criterion in self.criteria:
            lines.append(f"### {criterion.dimension.value.upper()}")
            lines.append(f"- **Weight**: {criterion.weight:.0%}")
            lines.append(f"- **Description**: {criterion.description}")
            lines.append(f"- **Score Range**: {criterion.score_range[0]:.1f} - {criterion.score_range[1]:.1f}")
            lines.append("")

        lines.extend([
            "## Score Levels",
            "- **Excellent (5)**: Outstanding performance, exceeds expectations",
            "- **Good (4)**: Meets expectations with minor areas for improvement",
            "- **Fair (3)**: Adequate performance, some significant gaps",
            "- **Poor (2)**: Below expectations, major gaps identified",
            "- **Very Poor (1)**: Does not meet minimum requirements",
            "",
            "Provide your evaluation with a rationale for each dimension.",
        ])

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "criteria": [c.to_dict() for c in self.criteria],
            "calibration": {
                "method": self.calibration.method,
                "reference_distribution": self.calibration.reference_distribution,
            },
        }


@dataclass
class LlmJudgeResult:
    """Result of LLM-judge evaluation."""
    rubric_name: str
    query: str
    result_id: str
    scores: list[EvaluationScore]
    overall_score: float
    overall_level: ScoreLevel
    summary: str
    raw_llm_response: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_llm_input_format(self) -> dict[str, Any]:
        """Format result for consumption by another LLM."""
        return {
            "rubric": self.rubric_name,
            "query": self.query,
            "result_id": self.result_id,
            "dimensions": [s.to_dict() for s in self.scores],
            "overall": {
                "score": self.overall_score,
                "level": self.overall_level.value,
                "summary": self.summary,
            },
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_llm_input_format(), indent=2, ensure_ascii=False)


class LlmJudgeEvaluator:
    """Evaluator that produces LLM-judge-compatible outputs.

    This class generates structured evaluations that can be:
    1. Used directly by LLM-as-judge systems
    2. Fed back into the system for calibration
    3. Used for human review of LLM decisions
    """

    def __init__(self, rubric: LlmJudgeRubric | None = None):
        self.rubric = rubric or LlmJudgeRubric.default_supply_matching()
        self._score_history: list[dict[str, Any]] = []

    def evaluate(
        self,
        query: str,
        result: dict[str, Any],
        score_fn: Callable[[EvaluationDimension, dict[str, Any]], tuple[float, str, list[str]]] | None = None,
    ) -> LlmJudgeResult:
        """Evaluate a single result against the rubric.

        Args:
            query: The original query/intent
            result: The result to evaluate (dict with supply info)
            score_fn: Optional function to compute scores. If not provided,
                      uses default heuristic scoring.

        Returns:
            LlmJudgeResult with scores for each dimension
        """
        scores: list[EvaluationScore] = []

        for criterion in self.rubric.criteria:
            if score_fn:
                raw_score, rationale, evidence = score_fn(criterion.dimension, result)
            else:
                raw_score, rationale, evidence = self._default_score(
                    criterion.dimension, result
                )

            # Normalize score
            normalized = self._normalize_score(
                raw_score, criterion.score_range
            )

            # Determine level
            level = self._score_to_level(normalized)

            scores.append(EvaluationScore(
                dimension=criterion.dimension,
                raw_score=raw_score,
                normalized_score=normalized,
                level=level,
                rationale=rationale,
                evidence=evidence,
            ))

        # Calculate weighted overall
        overall = sum(
            s.normalized_score * c.weight
            for s, c in zip(scores, self.rubric.criteria)
        )
        overall_level = self._score_to_level(overall)

        # Generate summary
        summary = self._generate_summary(query, scores, overall, overall_level)

        result_obj = LlmJudgeResult(
            rubric_name=self.rubric.name,
            query=query,
            result_id=result.get("id", "unknown"),
            scores=scores,
            overall_score=overall,
            overall_level=overall_level,
            summary=summary,
            metadata={"result": result},
        )

        # Store for calibration
        self._score_history.append(result_obj.to_llm_input_format())

        return result_obj

    def _default_score(
        self,
        dimension: EvaluationDimension,
        result: dict[str, Any],
    ) -> tuple[float, str, list[str]]:
        """Default heuristic scoring for each dimension."""
        evidence = []

        if dimension == EvaluationDimension.RELEVANCE:
            # Check if supply matches query category/preferences
            query_cat = result.get("category", "")
            user_prefs = result.get("user_preferences", [])
            if query_cat in user_prefs:
                score = 0.9
                evidence.append(f"Category '{query_cat}' matches user preference")
            elif user_prefs:
                score = 0.5
                evidence.append(f"Category mismatch, expected one of {user_prefs}")
            else:
                score = 0.7
            rationale = "Category relevance based on user preferences"

        elif dimension == EvaluationDimension.QUALITY:
            # Check quality indicators
            quality_score = result.get("quality_score", 0.5)
            rating = result.get("rating", 0.0)
            score = (quality_score + rating) / 2
            evidence.append(f"Quality score: {quality_score}, Rating: {rating}")
            rationale = "Based on quality indicators"

        elif dimension == EvaluationDimension.SAFETY:
            # Check safety/risk indicators
            risk_level = result.get("risk_level", "medium")
            risk_map = {"low": 0.9, "medium": 0.6, "high": 0.3, "critical": 0.1}
            score = risk_map.get(risk_level, 0.5)
            evidence.append(f"Risk level: {risk_level}")
            rationale = "Based on risk assessment"

        elif dimension == EvaluationDimension.DIVERSITY:
            # Placeholder - would need result set context
            score = 0.7
            rationale = "Diversity scoring requires result set context"

        elif dimension == EvaluationDimension.FRESHNESS:
            # Check update timestamp
            updated_at = result.get("updated_at", "")
            if updated_at:
                score = 0.8
            else:
                score = 0.5
            rationale = "Based on update timestamp"

        else:
            score = 0.5
            rationale = "Default scoring"
            evidence.append("No specific indicators found")

        return score, rationale, evidence

    def _normalize_score(
        self,
        raw_score: float,
        score_range: tuple[float, float],
    ) -> float:
        """Normalize score to rubric range."""
        min_val, max_val = score_range
        normalized = min_val + (raw_score * (max_val - min_val))
        return max(min_val, min(max_val, normalized))

    def _score_to_level(self, score: float) -> ScoreLevel:
        """Convert numeric score to categorical level."""
        if score >= 0.9:
            return ScoreLevel.EXCELLENT
        elif score >= 0.7:
            return ScoreLevel.GOOD
        elif score >= 0.5:
            return ScoreLevel.FAIR
        elif score >= 0.3:
            return ScoreLevel.POOR
        else:
            return ScoreLevel.VERY_POOR

    def _generate_summary(
        self,
        query: str,
        scores: list[EvaluationScore],
        overall: float,
        overall_level: ScoreLevel = ScoreLevel.FAIR,
    ) -> str:
        """Generate human-readable summary."""
        dimension_scores = ", ".join(
            f"{s.dimension.value}: {s.normalized_score:.1f}"
            for s in sorted(scores, key=lambda x: x.normalized_score, reverse=True)[:3]
        )

        return (
            f"For query '{query}', the result scored {overall:.1f} overall "
            f"(top dimensions: {dimension_scores}). "
            f"Assessment: {overall_level.value.replace('_', ' ').title()}."
        )

    def calibrate(
        self,
        calibration_config: CalibrationConfig,
    ) -> dict[str, Any]:
        """Calibrate scores based on historical distribution.

        Returns calibration statistics and updated configuration.
        """
        if not self._score_history:
            return {"status": "no_data", "message": "No score history to calibrate"}

        # Collect overall scores
        overall_scores = [
            h["overall"]["score"] for h in self._score_history
        ]

        if calibration_config.method == "linear":
            # No calibration needed
            return {
                "status": "calibrated",
                "method": "linear",
                "scores": overall_scores,
            }

        elif calibration_config.method == "zscore":
            import statistics
            mean = statistics.mean(overall_scores)
            std = statistics.stdev(overall_scores) if len(overall_scores) > 1 else 1.0

            calibrated = [
                (s - mean) / std if std > 0 else 0.0
                for s in overall_scores
            ]

            return {
                "status": "calibrated",
                "method": "zscore",
                "original_mean": mean,
                "original_std": std,
                "calibrated_scores": calibrated,
            }

        elif calibration_config.method == "percentile":
            sorted_scores = sorted(overall_scores)
            n = len(sorted_scores)

            calibrated = []
            for s in overall_scores:
                rank = sum(1 for x in sorted_scores if x <= s)
                percentile = rank / n if n > 0 else 0.5
                calibrated.append(percentile)

            return {
                "status": "calibrated",
                "method": "percentile",
                "calibrated_scores": calibrated,
            }

        return {"status": "unknown_method", "method": calibration_config.method}

    def get_calibration_hooks(self) -> dict[str, Callable]:
        """Get calibration hooks for integration."""
        return {
            "on_score": lambda result: self._score_history.append(
                result.to_llm_input_format()
            ),
            "calibrate": self.calibrate,
            "get_history": lambda: self._score_history.copy(),
        }


class EvaluationBenchmark:
    """Benchmark for comparing evaluation methods."""

    @staticmethod
    def run_evaluation_set(
        evaluator: LlmJudgeEvaluator,
        test_cases: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Run evaluation on a set of test cases.

        Args:
            evaluator: The evaluator to use
            test_cases: List of {query, result} dicts

        Returns:
            Statistics on the evaluation results
        """
        results = []
        for case in test_cases:
            result = evaluator.evaluate(
                query=case.get("query", ""),
                result=case.get("result", {}),
            )
            results.append(result)

        # Aggregate statistics
        overall_scores = [r.overall_score for r in results]
        level_counts: dict[str, int] = {}
        for r in results:
            level = r.overall_level.value
            level_counts[level] = level_counts.get(level, 0) + 1

        dimension_stats: dict[str, dict[str, float]] = {}
        for dim in EvaluationDimension:
            dim_scores = [
                s.normalized_score for s in r.scores
                if s.dimension == dim
            ]
            if dim_scores:
                dimension_stats[dim.value] = {
                    "mean": sum(dim_scores) / len(dim_scores),
                    "min": min(dim_scores),
                    "max": max(dim_scores),
                }

        return {
            "total_cases": len(results),
            "overall_mean": sum(overall_scores) / len(overall_scores) if overall_scores else 0,
            "level_distribution": level_counts,
            "dimension_stats": dimension_stats,
            "results": [r.to_llm_input_format() for r in results],
        }
