"""Agent behavior monitoring and observability module.

Provides real-time monitoring of agent behavior, performance, and health.
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
    """Types of metrics."""

    REQUEST_COUNT = "request_count"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    SUCCESS_RATE = "success_rate"
    TOKEN_USAGE = "token_usage"
    COST = "cost"
    CACHE_HIT_RATE = "cache_hit_rate"


class AgentStatus(Enum):
    """Agent status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class AgentMetrics:
    """Metrics for a single agent."""

    agent_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time_ms: float = 0.0
    total_tokens: int = 0
    total_cost: float = 0.0
    cache_hits: int = 0
    last_request_time: float = 0.0

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    @property
    def error_rate(self) -> float:
        return 1.0 - self.success_rate

    @property
    def avg_response_time_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_response_time_ms / self.total_requests

    @property
    def cache_hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests


@dataclass
class AgentHealth:
    """Health status of an agent."""

    agent_name: str
    status: AgentStatus
    score: float  # 0-1 health score
    last_check: str
    issues: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass
class MonitoringEvent:
    """A monitoring event."""

    event_id: str
    event_type: str
    agent_name: str
    timestamp: str
    data: dict[str, Any] = field(default_factory=dict)


class AgentMonitor:
    """Real-time monitoring for multi-agent systems.

    Tracks agent performance, health, and behavior.
    """

    def __init__(self, storage_path: str = "./data/monitoring") -> None:
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.metrics: dict[str, AgentMetrics] = {}
        self.events: list[MonitoringEvent] = []
        self.max_events = 1000

    def record_request(
        self,
        agent_name: str,
        success: bool,
        response_time_ms: float,
        tokens: int = 0,
        cost: float = 0.0,
        cache_hit: bool = False,
    ) -> None:
        """Record a request to an agent.

        Args:
            agent_name: Name of the agent
            success: Whether the request succeeded
            response_time_ms: Response time in milliseconds
            tokens: Number of tokens used
            cost: Cost of the request
            cache_hit: Whether cache was hit
        """
        import uuid

        if agent_name not in self.metrics:
            self.metrics[agent_name] = AgentMetrics(agent_name=agent_name)

        metrics = self.metrics[agent_name]
        metrics.total_requests += 1
        metrics.total_response_time_ms += response_time_ms
        metrics.total_tokens += tokens
        metrics.total_cost += cost
        metrics.last_request_time = time.time()

        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1

        if cache_hit:
            metrics.cache_hits += 1

        # Record event
        event = MonitoringEvent(
            event_id=str(uuid.uuid4())[:12],
            event_type="request",
            agent_name=agent_name,
            timestamp=datetime.now().isoformat(),
            data={
                "success": success,
                "response_time_ms": response_time_ms,
                "tokens": tokens,
                "cost": cost,
            },
        )
        self.events.append(event)

        # Trim events
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]

    def get_agent_metrics(self, agent_name: str) -> AgentMetrics | None:
        """Get metrics for a specific agent."""
        return self.metrics.get(agent_name)

    def get_all_metrics(self) -> dict[str, AgentMetrics]:
        """Get metrics for all agents."""
        return self.metrics

    def check_health(self, agent_name: str) -> AgentHealth:
        """Check health of a specific agent."""
        metrics = self.metrics.get(agent_name)

        if not metrics:
            return AgentHealth(
                agent_name=agent_name,
                status=AgentStatus.UNKNOWN,
                score=0.0,
                last_check=datetime.now().isoformat(),
                issues=["No metrics available"],
            )

        # Calculate health score
        score = 1.0

        # Deduct for error rate
        score -= metrics.error_rate * 0.5

        # Deduct for slow responses (if > 5 seconds)
        if metrics.avg_response_time_ms > 5000:
            score -= 0.2

        # Determine status
        if score >= 0.8:
            status = AgentStatus.HEALTHY
        elif score >= 0.5:
            status = AgentStatus.DEGRADED
        else:
            status = AgentStatus.UNHEALTHY

        issues = []
        if metrics.error_rate > 0.1:
            issues.append(f"High error rate: {metrics.error_rate:.1%}")
        if metrics.avg_response_time_ms > 5000:
            issues.append(f"Slow response time: {metrics.avg_response_time_ms:.0f}ms")
        if metrics.total_requests == 0:
            issues.append("No requests recorded")

        return AgentHealth(
            agent_name=agent_name,
            status=status,
            score=max(0.0, score),
            last_check=datetime.now().isoformat(),
            issues=issues,
            metrics={
                "success_rate": metrics.success_rate,
                "error_rate": metrics.error_rate,
                "avg_response_time_ms": metrics.avg_response_time_ms,
                "total_requests": metrics.total_requests,
                "total_cost": metrics.total_cost,
            },
        )

    def get_all_health(self) -> dict[str, AgentHealth]:
        """Get health status for all agents."""
        return {name: self.check_health(name) for name in self.metrics.keys()}

    def get_summary(self) -> dict[str, Any]:
        """Get monitoring summary."""
        total_requests = sum(m.total_requests for m in self.metrics.values())
        total_cost = sum(m.total_cost for m in self.metrics.values())
        total_tokens = sum(m.total_tokens for m in self.metrics.values())

        return {
            "total_requests": total_requests,
            "total_agents": len(self.metrics),
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "agents": {
                name: {
                    "requests": m.total_requests,
                    "success_rate": m.success_rate,
                    "avg_response_time_ms": m.avg_response_time_ms,
                }
                for name, m in self.metrics.items()
            },
        }

    def reset_metrics(self, agent_name: str | None = None) -> None:
        """Reset metrics for an agent or all agents."""
        if agent_name:
            if agent_name in self.metrics:
                self.metrics[agent_name] = AgentMetrics(agent_name=agent_name)
        else:
            self.metrics.clear()

    def save_snapshot(self) -> None:
        """Save monitoring snapshot to file."""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                name: {
                    "total_requests": m.total_requests,
                    "successful_requests": m.successful_requests,
                    "failed_requests": m.failed_requests,
                    "total_response_time_ms": m.total_response_time_ms,
                    "total_tokens": m.total_tokens,
                    "total_cost": m.total_cost,
                    "cache_hits": m.cache_hits,
                }
                for name, m in self.metrics.items()
            },
        }

        snapshot_file = self.storage_path / f"snapshot_{int(time.time())}.json"
        with open(snapshot_file, "w") as f:
            json.dump(snapshot, f, indent=2)


# Global instance
_agent_monitor: AgentMonitor | None = None


def get_agent_monitor(storage_path: str = "./data/monitoring") -> AgentMonitor:
    """Get global agent monitor instance."""
    global _agent_monitor
    if _agent_monitor is None:
        _agent_monitor = AgentMonitor(storage_path)
    return _agent_monitor
