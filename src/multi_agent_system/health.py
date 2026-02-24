"""System health and status monitoring."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SystemStatus:
    """Overall system status."""
    healthy: bool
    uptime_seconds: float
    components: dict[str, Any]
    metrics: dict[str, Any] = field(default_factory=dict)


class HealthChecker:
    """System health checker."""
    
    def __init__(self) -> None:
        self._start_time = time.time()
        self._component_health: dict[str, bool] = {}
    
    def check(self) -> SystemStatus:
        """Check system health."""
        
        # Collect component health
        components = {
            "orchestrator": self._check_orchestrator(),
            "graph": self._check_graph(),
            "cache": self._check_cache(),
            "agents": self._check_agents(),
        }
        
        overall_healthy = all(c["healthy"] for c in components.values())
        
        return SystemStatus(
            healthy=overall_healthy,
            uptime_seconds=time.time() - self._start_time,
            components=components,
            metrics=self._get_metrics(),
        )
    
    def _check_orchestrator(self) -> dict[str, Any]:
        return {
            "healthy": True,
            "status": "running",
        }
    
    def _check_graph(self) -> dict[str, Any]:
        try:
            from ..knowledge import get_graph
            graph = get_graph()
            count = graph.count()
            return {
                "healthy": True,
                "entity_count": count,
                "status": "running",
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "status": "error",
            }
    
    def _check_cache(self) -> dict[str, Any]:
        try:
            from ..core.cache import get_cache
            cache = get_cache()
            return {
                "healthy": True,
                "status": "running",
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "status": "error",
            }
    
    def _check_agents(self) -> dict[str, Any]:
        return {
            "healthy": True,
            "status": "running",
        }
    
    def _get_metrics(self) -> dict[str, Any]:
        try:
            from ..metrics import get_metrics
            return get_metrics().get_all()
        except Exception:
            return {}


# Global health checker
_health_checker: HealthChecker | None = None


def get_health_checker() -> HealthChecker:
    """Get the global health checker."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker
