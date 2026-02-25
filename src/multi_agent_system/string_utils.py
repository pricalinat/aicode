"""String utilities."""

from __future__ import annotations

import re
from typing import List


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def camel_to_snake(text: str) -> str:
    """Convert camelCase to snake_case."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", text).lower()


def snake_to_camel(text: str) -> str:
    """Convert snake_case to camelCase."""
    components = text.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def truncate(text: str, length: int, suffix: str = "...") -> str:
    """Truncate string to length."""
    if len(text) <= length:
        return text
    return text[:length - len(suffix)] + suffix


def strip_html(text: str) -> str:
    """Remove HTML tags."""
    return re.sub(r"<[^>]+>", "", text)


def word_count(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def strip_whitespace(text: str) -> str:
    """Strip extra whitespace."""
    return " ".join(text.split())
