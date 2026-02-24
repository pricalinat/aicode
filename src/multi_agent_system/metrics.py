"""Metrics and monitoring system."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Metric:
    """A single metric measurement."""
    name: str
    value: float
    timestamp: float
    tags: dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collects and aggregates metrics."""
    
    def __init__(self) -> None:
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._timers: dict[str, list[float]] = defaultdict(list)
    
    def increment(self, name: str, value: float = 1.0, tags: dict[str, str] | None = None) -> None:
        """Increment a counter."""
        key = self._make_key(name, tags)
        self._counters[key] += value
    
    def gauge(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Set a gauge value."""
        key = self._make_key(name, tags)
        self._gauges[key] = value
    
    def histogram(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record a histogram value."""
        key = self._make_key(name, tags)
        self._histograms[key].append(value)
    
    def timer(self, name: str, duration_ms: float, tags: dict[str, str] | None = None) -> None:
        """Record a timing measurement."""
        key = self._make_key(name, tags)
        self._timers[key].append(duration_ms)
    
    def _make_key(self, name: str, tags: dict[str, str] | None = None) -> str:
        """Create a metric key from name and tags."""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"
    
    def get_counter(self, name: str, tags: dict[str, str] | None = None) -> float:
        """Get counter value."""
        key = self._make_key(name, tags)
        return self._counters.get(key, 0.0)
    
    def get_gauge(self, name: str, tags: dict[str, str] | None = None) -> float | None:
        """Get gauge value."""
        key = self._make_key(name, tags)
        return self._gauges.get(key)
    
    def get_histogram_stats(self, name: str, tags: dict[str, str] | None = None) -> dict[str, float] | None:
        """Get histogram statistics."""
        key = self._make_key(name, tags)
        values = self._histograms.get(key)
        if not values:
            return None
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return {
            "count": count,
            "sum": sum(sorted_values),
            "mean": sum(sorted_values) / count,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "p50": sorted_values[count // 2],
            "p95": sorted_values[int(count * 0.95)],
            "p99": sorted_values[int(count * 0.99)],
        }
    
    def get_timer_stats(self, name: str, tags: dict[str, str] | None = None) -> dict[str, float] | None:
        """Get timer statistics."""
        key = self._make_key(name, tags)
        values = self._timers.get(key)
        if not values:
            return None
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return {
            "count": count,
            "sum": sum(sorted_values),
            "mean": sum(sorted_values) / count,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "p50": sorted_values[count // 2],
            "p95": sorted_values[int(count * 0.95)],
            "p99": sorted_values[int(count * 0.99)],
        }
    
    def get_all(self) -> dict[str, Any]:
        """Get all metrics."""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                k: self.get_histogram_stats(k) 
                for k in self._histograms
            },
            "timers": {
                k: self.get_timer_stats(k) 
                for k in self._timers
            },
        }
    
    def clear(self) -> None:
        """Clear all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._timers.clear()


class Timer:
    """Context manager for timing operations."""
    
    def __init__(self, collector: MetricsCollector, name: str, tags: dict[str, str] | None = None) -> None:
        self.collector = collector
        self.name = name
        self.tags = tags
        self.start_time = 0.0
    
    def __enter__(self) -> "Timer":
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        self.collector.timer(self.name, duration_ms, self.tags)


# Global metrics collector
_metrics: MetricsCollector | None = None


def get_metrics() -> MetricsCollector:
    """Get the global metrics collector."""
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics


def timer(name: str, tags: dict[str, str] | None = None) -> Timer:
    """Create a timer context manager."""
    return Timer(get_metrics(), name, tags)


# Predefined metric names
class Metrics:
    """Metric name constants."""
    # Agent metrics
    AGENT_REQUESTS = "agent.requests"
    AGENT_ERRORS = "agent.errors"
    AGENT_LATENCY = "agent.latency"
    
    # Graph metrics
    GRAPH_ENTITIES = "graph.entities"
    GRAPH_RELATIONS = "graph.relations"
    GRAPH_QUERIES = "graph.queries"
    
    # Cache metrics
    CACHE_HITS = "cache.hits"
    CACHE_MISSES = "cache.misses"
    
    # API metrics
    API_REQUESTS = "api.requests"
    API_LATENCY = "api.latency"
