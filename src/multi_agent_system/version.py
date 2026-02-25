"""Version utilities."""

from __future__ import annotations


def parse_version(version: str) -> tuple:
    """Parse version string."""
    parts = version.split(".")
    return tuple(int(p) for p in parts)


def compare_versions(v1: str, v2: str) -> int:
    """Compare versions. Returns -1, 0, or 1."""
    p1 = parse_version(v1)
    p2 = parse_version(v2)
    if p1 < p2:
        return -1
    elif p1 > p2:
        return 1
    return 0
