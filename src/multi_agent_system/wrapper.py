"""Wrap."""

from __future__ import annotations

class Wrapper:
    def __init__(self, obj):
        self._obj = obj
    
    def __getattr__(self, name):
        return getattr(self._obj, name)
    
    def __setattr__(self, name, value):
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            setattr(self._obj, name, value)
