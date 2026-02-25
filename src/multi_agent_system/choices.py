"""Choices."""

from __future__ import annotations


class Choices:
    """Enum-like choices."""
    
    def __init__(self, *choices) -> None:
        self._choices = {c: c for c in choices}
    
    def __iter__(self):
        return iter(self._choices.values())
    
    def __len__(self):
        return len(self._choices)
    
    def __contains__(self, item):
        return item in self._choices
    
    def to_choices(self):
        return [(c, c) for c in self._choices.values()]
