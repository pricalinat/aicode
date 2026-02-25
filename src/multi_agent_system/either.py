"""Either type."""

from __future__ import annotations

from typing import Generic, TypeVar, Union

T = TypeVar("T")
L = TypeVar("L")


class Left(Generic[L]):
    def __init__(self, value: L) -> None:
        self.value = value


class Right(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value


Either = Union[Left[L], Right[T]]
