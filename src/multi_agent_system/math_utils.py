"""Math utilities."""

from __future__ import annotations

import math


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))


def round_to(value: float, decimals: int) -> float:
    """Round to specified decimal places."""
    return round(value, decimals)


def percentage(part: float, total: float) -> float:
    """Calculate percentage."""
    if total == 0:
        return 0.0
    return (part / total) * 100


def average(numbers: list) -> float:
    """Calculate average."""
    return sum(numbers) / len(numbers) if numbers else 0


def median(numbers: list) -> float:
    """Calculate median."""
    if not numbers:
        return 0
    sorted_nums = sorted(numbers)
    n = len(sorted_nums)
    mid = n // 2
    if n % 2 == 0:
        return (sorted_nums[mid - 1] + sorted_nums[mid]) / 2
    return sorted_nums[mid]
