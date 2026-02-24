"""Knowledge graph module for e-commerce entity management."""

from .graph import (
    Entity,
    EntityType,
    GraphDatabase,
    GraphQuery,
    GraphResult,
    InMemoryGraphDatabase,
    Relation,
    RelationType,
    get_graph,
    set_graph,
)

__all__ = [
    "Entity",
    "EntityType",
    "GraphDatabase",
    "GraphQuery",
    "GraphResult",
    "InMemoryGraphDatabase",
    "Relation",
    "RelationType",
    "get_graph",
    "set_graph",
]
