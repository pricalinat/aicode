"""Continual learning module based on GenCNER paper.

Reference: "GenCNER: A Generative Framework for Continual Named Entity Recognition"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DomainConfig:
    """Configuration for a domain."""

    domain_name: str
    entity_types: list[str]  # e.g., ["PERSON", "ORG", "DATE"]
    examples: list[dict[str, str]] = field(default_factory=list)  # {"text": "...", "entities": [...]}
    model_config: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConceptDrift:
    """Detected concept drift."""

    drift_type: str  # "sudden", "gradual", "recurring"
    severity: float  # 0-1
    detected_at: str
    description: str
    affected_domains: list[str] = field(default_factory=list)


class ConceptDriftDetector:
    """Detects concept drift in data distribution."""

    def __init__(self) -> None:
        self.baseline_stats: dict[str, Any] = {}
        self.recent_stats: dict[str, Any] = {}

    def update_baseline(self, stats: dict[str, Any]) -> None:
        """Update baseline statistics."""
        self.baseline_stats = stats

    def update_recent(self, stats: dict[str, Any]) -> None:
        """Update recent statistics."""
        self.recent_stats = stats

    def detect(self) -> ConceptDrift | None:
        """Detect concept drift."""
        if not self.baseline_stats or not self.recent_stats:
            return None

        # Simple drift detection: compare key metrics
        drift_score = 0.0
        for key in self.baseline_stats:
            if key in self.recent_stats:
                baseline_val = self.baseline_stats[key]
                recent_val = self.recent_stats[key]
                if isinstance(baseline_val, (int, float)) and isinstance(recent_val, (int, float)):
                    # Calculate relative change
                    if baseline_val != 0:
                        change = abs(recent_val - baseline_val) / abs(baseline_val)
                        drift_score = max(drift_score, change)

        # Threshold for drift detection
        if drift_score > 0.2:
            return ConceptDrift(
                drift_type="gradual",
                severity=min(1.0, drift_score),
                detected_at="",
                description=f"Detected distribution change: {drift_score:.2f}",
            )

        return None


class DomainAdapter:
    """Adapts agents to new domains."""

    def __init__(self) -> None:
        self.domains: dict[str, DomainConfig] = {}
        self.current_domain: str | None = None

    def add_domain(self, config: DomainConfig) -> None:
        """Add a new domain configuration."""
        self.domains[config.domain_name] = config

    def switch_domain(self, domain_name: str) -> bool:
        """Switch to a different domain."""
        if domain_name in self.domains:
            self.current_domain = domain_name
            return True
        return False

    def get_prompt_suffix(self) -> str:
        """Get prompt suffix for current domain."""
        if not self.current_domain:
            return ""

        config = self.domains.get(self.current_domain)
        if not config:
            return ""

        # Build entity type instructions
        entity_types = ", ".join(config.entity_types)
        suffix = f"\n\n[Domain Context] Current domain: {config.domain_name}\n"
        suffix += f"Entity types to recognize: {entity_types}\n"

        if config.examples:
            suffix += "\nExamples:\n"
            for ex in config.examples[:3]:
                suffix += f"- {ex['text']} -> {ex['entities']}\n"

        return suffix


class ContinualLearning:
    """Continual learning system for agent adaptation.

    Enables agents to learn from new data without full retraining.
    """

    def __init__(self) -> None:
        self.domain_adapter = DomainAdapter()
        self.drift_detector = ConceptDriftDetector()
        self.learned_patterns: list[dict[str, Any]] = []

    def add_domain(self, domain_name: str, entity_types: list[str], examples: list[dict] | None = None) -> None:
        """Add a new domain."""
        config = DomainConfig(
            domain_name=domain_name,
            entity_types=entity_types,
            examples=examples or [],
        )
        self.domain_adapter.add_domain(config)

    def adapt_to_domain(self, domain_name: str) -> bool:
        """Adapt to a new domain."""
        return self.domain_adapter.switch_domain(domain_name)

    def learn_from_feedback(self, feedback: dict[str, Any]) -> None:
        """Learn from user feedback."""
        # Extract pattern from feedback
        pattern = {
            "query_type": feedback.get("query_type"),
            "correct_response": feedback.get("correct_response"),
            "incorrect_response": feedback.get("incorrect_response"),
            "lesson": feedback.get("lesson", ""),
        }
        self.learned_patterns.append(pattern)

    def get_adaptation_prompt(self) -> str:
        """Get prompt adaptation based on learned patterns."""
        if not self.learned_patterns:
            return ""

        # Get domain-specific suffix
        domain_suffix = self.domain_adapter.get_prompt_suffix()

        # Add learned patterns
        patterns_suffix = ""
        if self.learned_patterns:
            patterns_suffix = "\n\n[Learned Patterns]"
            for pattern in self.learned_patterns[-5:]:
                if pattern.get("lesson"):
                    patterns_suffix += f"\n- {pattern['lesson']}"

        return domain_suffix + patterns_suffix

    def detect_and_adapt(self, stats: dict[str, Any]) -> str | None:
        """Detect drift and potentially adapt."""
        # Update stats
        self.drift_detector.update_recent(stats)

        # Detect drift
        drift = self.drift_detector.detect()

        if drift:
            return f"Concept drift detected: {drift.description}. Consider retraining or adaptation."

        return None


# Global instance
_continual_learning: ContinualLearning | None = None


def get_continual_learning() -> ContinualLearning:
    """Get global continual learning instance."""
    global _continual_learning
    if _continual_learning is None:
        _continual_learning = ContinualLearning()
    return _continual_learning
