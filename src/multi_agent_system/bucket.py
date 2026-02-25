"""Bucket."""

from __future__ import annotations

class Bucket:
    def __init__(self, items=None):
        self._items = items or []
    
    def add(self, item):
        self._items.append(item)
    
    def remove(self, item):
        if item in self._items:
            self._items.remove(item)
    
    def __iter__(self):
        return iter(self._items)
    
    def __len__(self):
        return len(self._items)
