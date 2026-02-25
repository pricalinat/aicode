"""Time utilities."""

from __future__ import annotations

import time
from datetime import datetime, timedelta


def now() -> float:
    """Get current timestamp."""
    return time.time()


def now_ms() -> int:
    """Get current timestamp in milliseconds."""
    return int(time.time() * 1000)


def format_timestamp(ts: float, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format timestamp."""
    return datetime.fromtimestamp(ts).strftime(fmt)


def parse_timestamp(ts: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> float:
    """Parse timestamp string."""
    return datetime.strptime(ts, fmt).timestamp()


def elapsed_ms(start: float) -> float:
    """Get elapsed milliseconds since start."""
    return (time.time() - start) * 1000


def sleep_ms(ms: int) -> None:
    """Sleep for milliseconds."""
    time.sleep(ms / 1000)
