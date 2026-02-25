"""Counter."""

from __future__ import annotations


class Counter:
    def __init__(self, start=0):
        self._count = start
    
    def inc(self, n=1):
        self._count += n
        return self._count
    
    def dec(self, n=1):
        self._count -= n
        return self._count
    
    @property
    def value(self):
        return self._count
