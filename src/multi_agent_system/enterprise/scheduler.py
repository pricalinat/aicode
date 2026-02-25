"""Agent Scheduler for Task Scheduling.

Provides scheduling, time management, and task coordination for multi-agent systems.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable


class ScheduleStatus(Enum):
    """Schedule status."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    MISSED = "missed"


class RecurrenceType(Enum):
    """Recurrence types."""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


@dataclass
class ScheduleEntry:
    """A scheduled task."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""

    # Timing
    scheduled_at: datetime = field(default_factory=datetime.now)
    duration_minutes: int = 60
    deadline: datetime | None = None

    # Recurrence
    recurrence: RecurrenceType = RecurrenceType.ONCE
    recurrence_interval: int = 1

    # Task
    task_id: str = ""
    handler: Callable | None = None

    # Status
    status: ScheduleStatus = ScheduleStatus.PENDING
    result: Any = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_run: datetime | None = None
    run_count: int = 0


class Scheduler:
    """Agent task scheduler.

    Features:
    - Schedule tasks at specific times
    - Recurring schedules
    - Deadline management
    - Missed task handling
    """

    def __init__(self) -> None:
        """Initialize scheduler."""
        self._schedules: dict[str, ScheduleEntry] = {}
        self._running = False

    def schedule(
        self,
        name: str,
        scheduled_at: datetime,
        task_id: str = "",
        duration_minutes: int = 60,
        recurrence: RecurrenceType = RecurrenceType.ONCE,
    ) -> ScheduleEntry:
        """Schedule a task."""
        entry = ScheduleEntry(
            name=name,
            scheduled_at=scheduled_at,
            task_id=task_id,
            duration_minutes=duration_minutes,
            recurrence=recurrence,
        )
        self._schedules[entry.id] = entry
        return entry

    def schedule_recurring(
        self,
        name: str,
        start_at: datetime,
        interval: RecurrenceType,
        task_id: str = "",
    ) -> ScheduleEntry:
        """Schedule a recurring task."""
        return self.schedule(
            name=name,
            scheduled_at=start_at,
            task_id=task_id,
            recurrence=interval,
        )

    def cancel(self, schedule_id: str) -> bool:
        """Cancel a schedule."""
        if schedule_id in self._schedules:
            self._schedules[schedule_id].status = ScheduleStatus.CANCELLED
            return True
        return False

    def get_pending(self) -> list[ScheduleEntry]:
        """Get pending schedules."""
        now = datetime.now()
        pending = []

        for entry in self._schedules.values():
            if entry.status in (ScheduleStatus.PENDING, ScheduleStatus.SCHEDULED):
                if entry.scheduled_at <= now:
                    pending.append(entry)

        return sorted(pending, key=lambda e: e.scheduled_at)

    def get_upcoming(self, hours: int = 24) -> list[ScheduleEntry]:
        """Get upcoming schedules."""
        now = datetime.now()
        until = now + timedelta(hours=hours)

        upcoming = []
        for entry in self._schedules.values():
            if entry.status == ScheduleStatus.PENDING:
                if now <= entry.scheduled_at <= until:
                    upcoming.append(entry)

        return sorted(upcoming, key=lambda e: e.scheduled_at)

    def execute_due(self) -> list[ScheduleEntry]:
        """Execute all due schedules."""
        due = self.get_pending()
        executed = []

        for entry in due:
            entry.status = ScheduleStatus.RUNNING
            # Would execute handler here
            entry.status = ScheduleStatus.COMPLETED
            entry.last_run = datetime.now()
            entry.run_count += 1
            executed.append(entry)

        return executed


# Global scheduler
_scheduler: Scheduler | None = None


def get_scheduler() -> Scheduler:
    """Get global scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
    return _scheduler
