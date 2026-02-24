"""Pagination utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, TypeVar

T = TypeVar("T")


@dataclass
class Page:
    """A page of results."""
    items: List[Any]
    page: int
    page_size: int
    total: int
    
    @property
    def total_pages(self) -> int:
        return (self.total + self.page_size - 1) // self.page_size
    
    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages
    
    @property
    def has_prev(self) -> bool:
        return self.page > 1


def paginate(items: List[T], page: int = 1, page_size: int = 10) -> Page:
    """Paginate a list of items."""
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return Page(
        items=items[start:end],
        page=page,
        page_size=page_size,
        total=total,
    )
