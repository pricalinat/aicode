"""Prompt Optimization System.

Based on research about prompt engineering, optimization, and LLM instruction tuning.
Provides tools for analyzing, optimizing, and testing prompts.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class PromptType(Enum):
    """Types of prompts."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TASK = "task"
    FEWSHOT = "fewshot"


class OptimizationStrategy(Enum):
    """Prompt optimization strategies."""
    MANUAL = "manual"
    AUTO = "auto"
    EVOLUTIONARY = "evolutionary"
    GRADIENT = "gradient"


@dataclass
class PromptTemplate:
    """A prompt template with variables."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""

    # Template
    template: str = ""
    variables: list[str] = field(default_factory=list)

    # Type
    prompt_type: PromptType = PromptType.USER

    # Metadata
    version: str = "1.0"
    author: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def render(self, **kwargs) -> str:
        """Render template with variables."""
        return self.template.format(**kwargs)

    def get_variables(self) -> list[str]:
        """Extract variables from template."""
        import re
        return re.findall(r'\{(\w+)\}', self.template)


@dataclass
class PromptTest:
    """A test case for a prompt."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    input_variables: dict[str, Any] = field(default_factory=dict)
    expected_output: str = ""

    # Results
    actual_output: str = ""
    passed: bool = False
    metrics: dict[str, float] = field(default_factory=dict)

    # Timing
    latency_ms: int = 0
    tokens_used: int = 0


@dataclass
class PromptEvaluation:
    """Evaluation of a prompt."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    prompt_id: str = ""

    # Scores
    clarity: float = 0.0
    completeness: float = 0.0
    accuracy: float = 0.0
    efficiency: float = 0.0

    # Test results
    test_pass_rate: float = 0.0
    test_count: int = 0

    # Analysis
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    # Metadata
    evaluated_at: datetime = field(default_factory=datetime.now)


class PromptAnalyzer:
    """Analyzes prompts for quality and effectiveness."""

    def __init__(self) -> None:
        """Initialize prompt analyzer."""
        self._patterns = {
            "clear_instruction": ["You should", "Please", "Make sure to"],
            "ambiguous": ["maybe", "possibly", "might"],
            "constraint": ["Don't", "Never", "Avoid", "Must not"],
            "example": ["For example", "Such as", "Like"],
        }

    def analyze(self, prompt: str) -> PromptEvaluation:
        """Analyze a prompt."""
        evaluation = PromptEvaluation(prompt_id=prompt[:50])

        # Check length
        word_count = len(prompt.split())
        evaluation.clarity = self._score_clarity(prompt)
        evaluation.completeness = self._score_completeness(prompt)

        # Check patterns
        for pattern_name, patterns in self._patterns.items():
            for pattern in patterns:
                if pattern.lower() in prompt.lower():
                    if pattern_name in ["clear_instruction", "example"]:
                        evaluation.strengths.append(f"Uses {pattern_name}")
                    elif pattern_name in ["ambiguous"]:
                        evaluation.weaknesses.append(f"Contains ambiguous language: {pattern}")

        # Calculate overall scores
        evaluation.accuracy = (evaluation.clarity + evaluation.completeness) / 2
        evaluation.efficiency = min(1.0, word_count / 100)

        return evaluation

    def _score_clarity(self, prompt: str) -> float:
        """Score prompt clarity."""
        score = 0.5

        # Check for clear instructions
        if any(word in prompt.lower() for word in ["please", "should", "must", "need to"]):
            score += 0.2

        # Check for specific details
        if any(char in prompt for char in [".", "!", "?"]):
            score += 0.1

        # Penalize vagueness
        if any(word in prompt.lower() for word in ["stuff", "things", "whatever"]):
            score -= 0.2

        return max(0.0, min(1.0, score))

    def _score_completeness(self, prompt: str) -> float:
        """Score prompt completeness."""
        score = 0.5

        # Check for context
        if any(word in prompt.lower() for word in ["because", "context", "given"]):
            score += 0.15

        # Check for format specification
        if any(word in prompt.lower() for word in ["format", "output", "return"]):
            score += 0.15

        # Check for constraints
        if any(word in prompt.lower() for word in ["must", "should", "only", "avoid"]):
            score += 0.1

        # Check length (too short is usually incomplete)
        word_count = len(prompt.split())
        if word_count < 10:
            score -= 0.2
        elif word_count > 50:
            score += 0.1

        return max(0.0, min(1.0, score))


class PromptOptimizer:
    """Optimizes prompts based on feedback and testing.

    Features:
    - Template management
    - A/B testing
    - Evolutionary optimization
    - Performance tracking
    """

    def __init__(self) -> None:
        """Initialize prompt optimizer."""
        self._templates: dict[str, PromptTemplate] = {}
        self._tests: dict[str, list[PromptTest]] = {}
        self._evaluations: list[PromptEvaluation] = []
        self.analyzer = PromptAnalyzer()

    def create_template(
        self,
        name: str,
        template: str,
        description: str = "",
        prompt_type: PromptType = PromptType.USER,
    ) -> PromptTemplate:
        """Create a new prompt template."""
        tmpl = PromptTemplate(
            name=name,
            template=template,
            description=description,
            prompt_type=prompt_type,
        )
        tmpl.variables = tmpl.get_variables()

        self._templates[tmpl.id] = tmpl
        self._tests[tmpl.id] = []
        return tmpl

    def add_test(
        self,
        template_id: str,
        name: str,
        input_variables: dict[str, Any],
        expected_output: str = "",
    ) -> PromptTest | None:
        """Add test case to template."""
        if template_id not in self._templates:
            return None

        test = PromptTest(
            name=name,
            input_variables=input_variables,
            expected_output=expected_output,
        )
        self._tests[template_id].append(test)
        return test

    def evaluate_template(self, template_id: str) -> PromptEvaluation | None:
        """Evaluate a template."""
        template = self._templates.get(template_id)
        if not template:
            return None

        # Analyze rendered prompt
        rendered = template.render(**template.input_variables() if callable(getattr(template, 'input_variables', None)) else {})
        evaluation = self.analyzer.analyze(rendered)
        evaluation.prompt_id = template_id

        # Calculate test pass rate
        tests = self._tests.get(template_id, [])
        if tests:
            passed = sum(1 for t in tests if t.passed)
            evaluation.test_pass_rate = passed / len(tests)
            evaluation.test_count = len(tests)

        self._evaluations.append(evaluation)
        return evaluation

    def optimize(
        self,
        template_id: str,
        strategy: OptimizationStrategy = OptimizationStrategy.AUTO,
    ) -> PromptTemplate | None:
        """Optimize a template."""
        template = self._templates.get(template_id)
        if not template:
            return None

        # Get evaluation
        evaluation = self.evaluate_template(template_id)
        if not evaluation:
            return template

        # Apply optimizations based on suggestions
        optimized_template = PromptTemplate(
            name=f"{template.name} (optimized)",
            template=template.template,
            description=template.description,
            prompt_type=template.prompt_type,
            version=str(float(template.version) + 0.1),
        )

        # Apply common optimizations
        suggestions = evaluation.suggestions

        if evaluation.weaknesses:
            # Try adding clarifications
            optimized_template.template += "\n\nBe clear and specific in your response."

        if evaluation.completeness < 0.7:
            # Add context section
            optimized_template.template = (
                "Context: The user needs help with a task.\n\n"
                f"{optimized_template.template}\n\n"
                "Provide a complete and accurate response."
            )

        self._templates[optimized_template.id] = optimized_template
        self._tests[optimized_template.id] = []

        return optimized_template

    def compare_templates(
        self,
        template_id_1: str,
        template_id_2: str,
    ) -> dict[str, Any]:
        """Compare two templates."""
        eval1 = self.evaluate_template(template_id_1)
        eval2 = self.evaluate_template(template_id_2)

        if not eval1 or not eval2:
            return {"error": "Template not found"}

        return {
            "template_1": {
                "id": template_id_1,
                "clarity": eval1.clarity,
                "completeness": eval1.completeness,
                "test_pass_rate": eval1.test_pass_rate,
            },
            "template_2": {
                "id": template_id_2,
                "clarity": eval2.clarity,
                "completeness": eval2.completeness,
                "test_pass_rate": eval2.test_pass_rate,
            },
            "winner": template_id_1 if eval1.clarity > eval2.clarity else template_id_2,
        }

    def get_template(self, template_id: str) -> PromptTemplate | None:
        """Get template by ID."""
        return self._templates.get(template_id)

    def list_templates(self) -> list[PromptTemplate]:
        """List all templates."""
        return list(self._templates.values())


# Global optimizer
_prompt_optimizer: PromptOptimizer | None = None


def get_prompt_optimizer() -> PromptOptimizer:
    """Get global prompt optimizer."""
    global _prompt_optimizer
    if _prompt_optimizer is None:
        _prompt_optimizer = PromptOptimizer()
    return _prompt_optimizer
