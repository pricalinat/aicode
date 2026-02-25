"""Cost control and budget management for multi-agent systems.

Reference: "Controlling Performance and Budget of a Centralized Multi-agent LLM System with RL"

Provides budget tracking, cost optimization, and resource allocation.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class BudgetPeriod(Enum):
    """Budget period."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class CostAlertLevel(Enum):
    """Cost alert levels."""

    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EXCEEDED = "exceeded"


@dataclass
class CostEntry:
    """A single cost entry."""

    id: str
    agent_name: str
    operation: str
    tokens: int
    cost: float
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Budget:
    """Budget configuration."""

    total_limit: float
    period: BudgetPeriod
    spent: float = 0.0
    alert_thresholds: list[float] = field(default_factory=lambda: [0.5, 0.8, 1.0])


@dataclass
class CostAlert:
    """A cost alert."""

    level: CostAlertLevel
    message: str
    percentage: float
    timestamp: str


class CostController:
    """Cost control for multi-agent systems.

    Features:
    - Budget tracking
    - Cost alerts
    - Token usage monitoring
    - Agent-specific budgets
    """

    # Default cost per 1K tokens (USD)
    DEFAULT_COSTS = {
        "gpt-4": 0.03,  # Input
        "gpt-4-output": 0.06,
        "gpt-3.5-turbo": 0.0015,
        "claude-3-opus": 0.015,
        "claude-3-sonnet": 0.003,
        "claude-3-haiku": 0.00025,
        "default": 0.001,
    }

    def __init__(self, storage_path: str = "./data/costs") -> None:
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.budgets: dict[str, Budget] = {}
        self.cost_entries: list[CostEntry] = []
        self.alerts: list[CostAlert] = []

        self.agent_costs: dict[str, dict[str, float]] = {}  # agent -> {model -> cost}
        self._load_budgets()

    def _load_budgets(self) -> None:
        """Load budgets from storage."""
        budget_file = self.storage_path / "budgets.json"
        if budget_file.exists():
            with open(budget_file) as f:
                data = json.load(f)
                for name, config in data.items():
                    self.budgets[name] = Budget(**config)

    def _save_budgets(self) -> None:
        """Save budgets to storage."""
        budget_file = self.storage_path / "budgets.json"
        data = {
            name: {
                "total_limit": b.total_limit,
                "period": b.period.value,
                "spent": b.spent,
                "alert_thresholds": b.alert_thresholds,
            }
            for name, b in self.budgets.items()
        }
        with open(budget_file, "w") as f:
            json.dump(data, f, indent=2)

    def set_budget(self, name: str, limit: float, period: BudgetPeriod = BudgetPeriod.DAILY) -> None:
        """Set budget for an agent or system."""
        self.budgets[name] = Budget(total_limit=limit, period=period)
        self._save_budgets()

    def get_budget(self, name: str) -> Budget | None:
        """Get budget for an agent or system."""
        return self.budgets.get(name)

    def get_all_budgets(self) -> dict[str, Budget]:
        """Get all budgets."""
        return self.budgets

    def record_cost(
        self,
        agent_name: str,
        operation: str,
        tokens: int,
        model: str = "default",
        metadata: dict | None = None,
    ) -> CostEntry:
        """Record a cost entry.

        Args:
            agent_name: Name of the agent
            operation: Operation performed
            tokens: Number of tokens used
            model: Model used
            metadata: Additional metadata

        Returns:
            CostEntry
        """
        import uuid

        # Calculate cost
        cost_per_1k = self.DEFAULT_COSTS.get(model, self.DEFAULT_COSTS["default"])
        cost = (tokens / 1000) * cost_per_1k

        entry = CostEntry(
            id=str(uuid.uuid4())[:12],
            agent_name=agent_name,
            operation=operation,
            tokens=tokens,
            cost=cost,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {},
        )

        self.cost_entries.append(entry)

        # Update budgets
        self._update_budget_spending(agent_name, cost)
        self._update_budget_spending("system", cost)

        # Check for alerts
        self._check_alerts(agent_name)

        return entry

    def _update_budget_spending(self, name: str, cost: float) -> None:
        """Update budget spending."""
        if name in self.budgets:
            self.budgets[name].spent += cost

    def _check_alerts(self, agent_name: str) -> None:
        """Check for budget alerts."""
        budget = self.budgets.get(agent_name)
        if not budget:
            return

        percentage = budget.spent / budget.total_limit

        if percentage >= 1.0:
            alert = CostAlert(
                level=CostAlertLevel.EXCEEDED,
                message=f"Budget exceeded for {agent_name}",
                percentage=percentage,
                timestamp=datetime.now().isoformat(),
            )
            self.alerts.append(alert)
        elif percentage >= 0.8:
            alert = CostAlert(
                level=CostAlertLevel.CRITICAL,
                message=f"Critical: {agent_name} at {percentage:.0%} of budget",
                percentage=percentage,
                timestamp=datetime.now().isoformat(),
            )
            self.alerts.append(alert)
        elif percentage >= 0.5:
            alert = CostAlert(
                level=CostAlertLevel.WARNING,
                message=f"Warning: {agent_name} at {percentage:.0%} of budget",
                percentage=percentage,
                timestamp=datetime.now().isoformat(),
            )
            self.alerts.append(alert)

    def can_proceed(self, agent_name: str, estimated_cost: float = 0.0) -> bool:
        """Check if operation can proceed within budget."""
        budget = self.budgets.get(agent_name)
        if not budget:
            return True  # No budget limit

        return (budget.spent + estimated_cost) <= budget.total_limit

    def get_cost_summary(self, agent_name: str | None = None) -> dict[str, Any]:
        """Get cost summary.

        Args:
            agent_name: Filter by agent (None = all)
        """
        entries = self.cost_entries
        if agent_name:
            entries = [e for e in entries if e.agent_name == agent_name]

        total_cost = sum(e.cost for e in entries)
        total_tokens = sum(e.tokens for e in entries)

        # By agent
        by_agent = {}
        for e in entries:
            if e.agent_name not in by_agent:
                by_agent[e.agent_name] = {"cost": 0.0, "tokens": 0, "requests": 0}
            by_agent[e.agent_name]["cost"] += e.cost
            by_agent[e.agent_name]["tokens"] += e.tokens
            by_agent[e.agent_name]["requests"] += 1

        # Budget status
        budget_status = {}
        for name, budget in self.budgets.items():
            budget_status[name] = {
                "limit": budget.total_limit,
                "spent": budget.spent,
                "remaining": budget.total_limit - budget.spent,
                "percentage": budget.spent / budget.total_limit if budget.total_limit > 0 else 0,
            }

        return {
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "total_requests": len(entries),
            "by_agent": by_agent,
            "budgets": budget_status,
            "recent_alerts": [
                {"level": a.level.value, "message": a.message, "timestamp": a.timestamp}
                for a in self.alerts[-10:]
            ],
        }

    def reset_budgets(self, period: BudgetPeriod | None = None) -> None:
        """Reset budgets for a period."""
        if period:
            for budget in self.budgets.values():
                if budget.period == period:
                    budget.spent = 0.0
        else:
            for budget in self.budgets.values():
                budget.spent = 0.0

        self.alerts.clear()
        self._save_budgets()

    def get_optimization_suggestions(self) -> list[str]:
        """Get cost optimization suggestions."""
        suggestions = []

        # Check for high-cost agents
        summary = self.get_cost_summary()
        for agent, data in summary.get("by_agent", {}).items():
            if data["cost"] > 10:  # Arbitrary threshold
                suggestions.append(f"{agent} has high costs (${data['cost']:.2f}). Consider optimizing.")

        # Check for budget exceeded
        for name, status in summary.get("budgets", {}).items():
            if status["percentage"] >= 1.0:
                suggestions.append(f"Budget exceeded for {name}. Consider increasing budget or reducing usage.")

        # Check for low cache hit rate
        # (would need to integrate with monitoring)

        if not suggestions:
            suggestions.append("No optimization suggestions at this time.")

        return suggestions


# Global instance
_cost_controller: CostController | None = None


def get_cost_controller(storage_path: str = "./data/costs") -> CostController:
    """Get global cost controller instance."""
    global _cost_controller
    if _cost_controller is None:
        _cost_controller = CostController(storage_path)
    return _cost_controller
