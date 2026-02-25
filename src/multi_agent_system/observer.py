"""Observer pattern."""

from __future__ import annotations

from typing import Any, Callable, List


class Observable:
    """Observable subject."""
    
    def __init__(self) -> None:
        self._observers: List[Callable] = []
    
    def add_observer(self, observer: Callable) -> None:
        self._observers.append(observer)
    
    def remove_observer(self, observer: Callable) -> None:
        self._observers.remove(observer)
    
    def notify(self, *args, **kwargs) -> None:
        for observer in self._observers:
            observer(*args, **kwargs)


class Observer:
    """Observer base class."""
    
    def update(self, *args, **kwargs) -> None:
        raise NotImplementedError
