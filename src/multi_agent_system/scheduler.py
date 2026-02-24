"""Task scheduler for periodic and delayed tasks."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List
from enum import Enum


class ScheduleType(Enum):
    """Type of schedule."""
    INTERVAL = "interval"
    CRON = "cron"
    DELAYED = "delayed"


@dataclass
class ScheduledTask:
    """A scheduled task."""
    name: str
    handler: Callable
    schedule_type: ScheduleType
    interval_seconds: float = 0
    cron_expression: str = ""
    delay_seconds: float = 0
    enabled: bool = True


class Scheduler:
    """Task scheduler."""
    
    def __init__(self) -> None:
        self._tasks: Dict[str, ScheduledTask] = {}
        self._running = False
    
    def add_interval(self, name: str, handler: Callable, interval_seconds: float) -> None:
        task = ScheduledTask(
            name=name,
            handler=handler,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=interval_seconds,
        )
        self._tasks[name] = task
    
    def add_delayed(self, name: str, handler: Callable, delay_seconds: float) -> None:
        task = ScheduledTask(
            name=name,
            handler=handler,
            schedule_type=ScheduleType.DELAYED,
            delay_seconds=delay_seconds,
        )
        self._tasks[name] = task
    
    def remove(self, name: str) -> bool:
        if name in self._tasks:
            del self._tasks[name]
            return True
        return False
    
    def enable(self, name: str) -> bool:
        if name in self._tasks:
            self._tasks[name].enabled = True
            return True
        return False
    
    def disable(self, name: str) -> bool:
        if name in self._tasks:
            self._tasks[name].enabled = False
            return True
        return False
    
    def list_tasks(self) -> List[str]:
        return list(self._tasks.keys())


# Global scheduler
_scheduler: Scheduler | None = None


def get_scheduler() -> Scheduler:
    """Get the global scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
    return _scheduler
