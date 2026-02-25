"""Builder pattern."""

from __future__ import annotations

from typing import Any


class Builder:
    """Base builder class."""
    
    def __init__(self) -> None:
        self._values = {}
    
    def set(self, key: str, value: Any) -> "Builder":
        self._values[key] = value
        return self
    
    def build(self) -> dict:
        return self._values.copy()


class FluentBuilder:
    """Fluent interface builder."""
    
    def with_(self, **kwargs) -> "FluentBuilder":
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self
    
    def build(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
