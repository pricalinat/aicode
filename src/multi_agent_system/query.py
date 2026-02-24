"""Query builder for structured queries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class Query:
    """A structured query."""
    text: str = ""
    filters: dict = field(default_factory=dict)
    sort_by: str = ""
    sort_order: str = "asc"
    limit: int = 20
    offset: int = 0


class QueryBuilder:
    """Build structured queries."""
    
    def __init__(self) -> None:
        self._text = ""
        self._filters: dict = {}
        self._sort_by = ""
        self._sort_order = "asc"
        self._limit = 20
        self._offset = 0
    
    def text(self, text: str) -> "QueryBuilder":
        self._text = text
        return self
    
    def filter(self, key: str, value: Any) -> "QueryBuilder":
        self._filters[key] = value
        return self
    
    def sort(self, field: str, order: str = "asc") -> "QueryBuilder":
        self._sort_by = field
        self._sort_order = order
        return self
    
    def limit(self, limit: int) -> "QueryBuilder":
        self._limit = limit
        return self
    
    def offset(self, offset: int) -> "QueryBuilder":
        self._offset = offset
        return self
    
    def build(self) -> Query:
        return Query(
            text=self._text,
            filters=self._filters.copy(),
            sort_by=self._sort_by,
            sort_order=self._sort_order,
            limit=self._limit,
            offset=self._offset,
        )
