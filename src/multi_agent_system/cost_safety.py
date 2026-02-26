"""Cost and Safety Controls for LLM Operations.

This module provides:
- Model routing based on complexity, cost, and capability
- Audit logging for compliance and debugging
- Rate limiting and budget controls
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable


class ModelTier(Enum):
    """Model capability tiers."""
    FAST = "fast"  # Haiku-level, low cost
    STANDARD = "standard"  # Sonnet-level, balanced
    ADVANCED = "advanced"  # Opus-level, high capability
    CUSTOM = "custom"  # Custom model


@dataclass
class ModelConfig:
    """Configuration for a model."""
    name: str
    tier: ModelTier
    cost_per_1k_tokens: float = 0.0
    max_tokens: int = 4096
    capabilities: list[str] = field(default_factory=list)
    is_available: bool = True


@dataclass
class RoutingDecision:
    """Result of a routing decision."""
    selected_model: str
    reasoning: str
    confidence: float
    estimated_cost: float
    fallback_models: list[str] = field(default_factory=list)


@dataclass
class AuditLogEntry:
    """Single audit log entry."""
    timestamp: str
    operation: str
    user_id: str | None
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    latency_ms: float
    success: bool
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "operation": self.operation,
            "user_id": self.user_id,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost": self.cost,
            "latency_ms": self.latency_ms,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata,
        }


class CostBudget:
    """Track and enforce cost budgets."""

    def __init__(
        self,
        daily_limit: float = 100.0,
        monthly_limit: float = 1000.0,
    ):
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit
        self._daily_spend: dict[str, float] = {}
        self._monthly_spend: dict[str, float] = {}
        self._last_reset: str = datetime.now(timezone.utc).date().isoformat()

    def check_budget(self, user_id: str, amount: float) -> tuple[bool, str]:
        """Check if budget allows the operation."""
        today = datetime.now(timezone.utc).date().isoformat()

        # Reset daily if needed
        if today != self._last_reset:
            self._daily_spend.clear()
            self._last_reset = today

        current_daily = self._daily_spend.get(user_id, 0)
        current_monthly = self._monthly_spend.get(user_id, 0)

        if current_daily + amount > self.daily_limit:
            return False, f"Daily budget exceeded: ${current_daily + amount:.2f} > ${self.daily_limit:.2f}"

        if current_monthly + amount > self.monthly_limit:
            return False, f"Monthly budget exceeded: ${current_monthly + amount:.2f} > ${self.monthly_limit:.2f}"

        return True, "OK"

    def record_spend(self, user_id: str, amount: float) -> None:
        """Record spending after operation."""
        today = datetime.now(timezone.utc).date().isoformat()

        if today != self._last_reset:
            self._daily_spend.clear()
            self._last_reset = today

        self._daily_spend[user_id] = self._daily_spend.get(user_id, 0) + amount
        self._monthly_spend[user_id] = self._monthly_spend.get(user_id, 0) + amount

    def get_remaining(self, user_id: str) -> dict[str, float]:
        """Get remaining budget."""
        today = datetime.now(timezone.utc).date().isoformat()

        if today != self._last_reset:
            self._daily_spend.clear()
            self._last_reset = today

        return {
            "daily_remaining": max(0, self.daily_limit - self._daily_spend.get(user_id, 0)),
            "monthly_remaining": max(0, self.monthly_limit - self._monthly_spend.get(user_id, 0)),
        }


class ModelRouter:
    """Routes requests to appropriate models based on complexity."""

    # Default model configurations
    DEFAULT_MODELS: dict[str, ModelConfig] = {
        "haiku": ModelConfig(
            name="haiku",
            tier=ModelTier.FAST,
            cost_per_1k_tokens=0.0002,
            max_tokens=4096,
            capabilities=["fast", "simple", "realtime"],
        ),
        "sonnet": ModelConfig(
            name="sonnet",
            tier=ModelTier.STANDARD,
            cost_per_1k_tokens=0.003,
            max_tokens=4096,
            capabilities=["balanced", "reasoning", "coding"],
        ),
        "opus": ModelConfig(
            name="opus",
            tier=ModelTier.ADVANCED,
            cost_per_1k_tokens=0.015,
            max_tokens=4096,
            capabilities=["advanced", "complex", "analysis"],
        ),
    }

    def __init__(
        self,
        models: dict[str, ModelConfig] | None = None,
        budget: CostBudget | None = None,
    ):
        self._models = models or self.DEFAULT_MODELS.copy()
        self._budget = budget
        self._routing_rules: list[Callable] = []

    def add_routing_rule(self, rule: Callable) -> None:
        """Add a custom routing rule."""
        self._routing_rules.append(rule)

    def route(
        self,
        request: dict[str, Any],
        user_id: str | None = None,
    ) -> RoutingDecision:
        """Route request to appropriate model.

        Args:
            request: The request to route
            user_id: Optional user ID for budget checking

        Returns:
            RoutingDecision with selected model and reasoning
        """
        # Extract complexity signals from request
        complexity = self._estimate_complexity(request)

        # Check budget if available
        if self._budget and user_id:
            estimated_cost = self._estimate_cost(complexity)
            allowed, reason = self._budget.check_budget(user_id, estimated_cost)
            if not allowed:
                # Fall back to cheaper model
                return RoutingDecision(
                    selected_model="haiku",
                    reasoning=f"Budget exceeded, falling back: {reason}",
                    confidence=0.5,
                    estimated_cost=0,
                    fallback_models=["haiku"],
                )

        # Apply custom routing rules first
        for rule in self._routing_rules:
            result = rule(request, self._models)
            if result:
                return result

        # Default routing based on complexity
        return self._default_route(complexity)

    def _estimate_complexity(self, request: dict[str, Any]) -> str:
        """Estimate request complexity."""
        # Simple heuristics
        text = request.get("text", "")
        prompt = request.get("prompt", "")

        combined = text + prompt
        length = len(combined)

        # Check for complexity indicators
        has_code = any(kw in combined.lower() for kw in ["code", "function", "class", "def "])
        has_analysis = any(kw in combined.lower() for kw in ["analyze", "compare", "evaluate", "explain"])
        has_math = any(kw in combined.lower() for kw in ["calculate", "compute", "math", "equation"])

        complexity_score = 0
        if length > 1000:
            complexity_score += 1
        if has_code:
            complexity_score += 2
        if has_analysis:
            complexity_score += 2
        if has_math:
            complexity_score += 2

        if complexity_score >= 4:
            return "high"
        elif complexity_score >= 2:
            return "medium"
        else:
            return "low"

    def _estimate_cost(self, complexity: str) -> float:
        """Estimate cost for complexity level."""
        estimates = {
            "low": 0.001,   # ~500 tokens
            "medium": 0.01,  # ~3000 tokens
            "high": 0.05,    # ~10000 tokens
        }
        return estimates.get(complexity, 0.01)

    def _default_route(self, complexity: str) -> RoutingDecision:
        """Default routing logic."""
        if complexity == "high":
            return RoutingDecision(
                selected_model="opus",
                reasoning="High complexity detected - using advanced model",
                confidence=0.9,
                estimated_cost=0.05,
                fallback_models=["sonnet", "haiku"],
            )
        elif complexity == "medium":
            return RoutingDecision(
                selected_model="sonnet",
                reasoning="Medium complexity - using balanced model",
                confidence=0.8,
                estimated_cost=0.01,
                fallback_models=["haiku"],
            )
        else:
            return RoutingDecision(
                selected_model="haiku",
                reasoning="Low complexity - using fast model",
                confidence=0.7,
                estimated_cost=0.001,
                fallback_models=[],
            )


class AuditLogger:
    """Audit logger for compliance and debugging."""

    def __init__(
        self,
        log_dir: str | Path | None = None,
        retention_days: int = 90,
    ):
        self.log_dir = Path(log_dir) if log_dir else None
        self.retention_days = retention_days
        self._entries: list[AuditLogEntry] = []
        self._in_memory = log_dir is None

        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        operation: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        success: bool,
        user_id: str | None = None,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLogEntry:
        """Log an operation."""
        entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            operation=operation,
            user_id=user_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=self._calculate_cost(model, input_tokens, output_tokens),
            latency_ms=latency_ms,
            success=success,
            error=error,
            metadata=metadata or {},
        )

        self._entries.append(entry)

        # Write to file if configured
        if self.log_dir:
            self._write_to_file(entry)

        return entry

    def _calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Calculate cost based on model and tokens."""
        costs = {
            "haiku": 0.0002,
            "sonnet": 0.003,
            "opus": 0.015,
        }
        rate = costs.get(model, 0.001)
        return (input_tokens + output_tokens) / 1000 * rate

    def _write_to_file(self, entry: AuditLogEntry) -> None:
        """Write entry to log file."""
        date = datetime.now(timezone.utc).date().isoformat()
        log_file = self.log_dir / f"audit_{date}.jsonl"

        with open(log_file, "a") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

    def query(
        self,
        user_id: str | None = None,
        operation: str | None = None,
        model: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        limit: int = 100,
    ) -> list[AuditLogEntry]:
        """Query audit logs."""
        results = self._entries

        if user_id:
            results = [e for e in results if e.user_id == user_id]
        if operation:
            results = [e for e in results if e.operation == operation]
        if model:
            results = [e for e in results if e.model == model]
        if start_time:
            results = [e for e in results if e.timestamp >= start_time]
        if end_time:
            results = [e for e in results if e.timestamp <= end_time]

        return results[-limit:]

    def get_statistics(
        self,
        start_date: str | None = None,
    ) -> dict[str, Any]:
        """Get usage statistics."""
        entries = self._entries
        if start_date:
            entries = [e for e in entries if e.timestamp >= start_date]

        if not entries:
            return {
                "total_requests": 0,
                "total_cost": 0,
                "total_tokens": 0,
                "avg_latency_ms": 0,
            }

        total_cost = sum(e.cost for e in entries)
        total_tokens = sum(e.input_tokens + e.output_tokens for e in entries)
        success_count = sum(1 for e in entries if e.success)

        return {
            "total_requests": len(entries),
            "successful_requests": success_count,
            "failed_requests": len(entries) - success_count,
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "avg_latency_ms": sum(e.latency_ms for e in entries) / len(entries),
            "by_model": self._group_by_model(entries),
            "by_operation": self._group_by_operation(entries),
        }

    def _group_by_model(self, entries: list[AuditLogEntry]) -> dict[str, int]:
        """Group entries by model."""
        result: dict[str, int] = {}
        for e in entries:
            result[e.model] = result.get(e.model, 0) + 1
        return result

    def _group_by_operation(self, entries: list[AuditLogEntry]) -> dict[str, int]:
        """Group entries by operation."""
        result: dict[str, int] = {}
        for e in entries:
            result[e.operation] = result.get(e.operation, 0) + 1
        return result


class SafetyFilter:
    """Content safety filter for requests and responses."""

    def __init__(self):
        self._blocked_patterns: list[str] = []
        self._allowed_patterns: list[str] = []

    def add_blocked_pattern(self, pattern: str) -> None:
        """Add a blocked pattern (regex)."""
        self._blocked_patterns.append(pattern)

    def check_request(self, text: str) -> tuple[bool, str]:
        """Check if request content is safe."""
        import re

        for pattern in self._blocked_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False, f"Content blocked by pattern: {pattern}"

        return True, "OK"

    def check_response(self, text: str) -> tuple[bool, str]:
        """Check if response content is safe."""
        # Same as request for now
        return self.check_request(text)


# Global instances
_audit_logger: AuditLogger | None = None
_model_router: ModelRouter | None = None
_cost_budget: CostBudget | None = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def set_audit_logger(logger: AuditLogger) -> None:
    """Set global audit logger."""
    global _audit_logger
    _audit_logger = logger


def get_model_router() -> ModelRouter:
    """Get global model router."""
    global _model_router
    if _model_router is None:
        _model_router = ModelRouter()
    return _model_router


def set_model_router(router: ModelRouter) -> None:
    """Set global model router."""
    global _model_router
    _model_router = router


def get_cost_budget() -> CostBudget:
    """Get global cost budget."""
    global _cost_budget
    if _cost_budget is None:
        _cost_budget = CostBudget()
    return _cost_budget


def set_cost_budget(budget: CostBudget) -> None:
    """Set global cost budget."""
    global _cost_budget
    _cost_budget = budget
