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
from .supply_graph_database import (
    CycleDetectedError,
    GraphPath,
    SupplyGraphDatabase,
    ValidationError,
    get_supply_graph,
    set_supply_graph,
)
from .supply_graph_evaluation import (
    EntityQualityMetrics,
    EvaluationResult,
    GraphBenchmark,
    GraphMetrics,
    PerformanceMetrics,
    RelationQualityMetrics,
    SupplyGraphEvaluator,
)
from .supply_graph_models import (
    SupplyEntity,
    SupplyEntityType,
    SupplyGraph,
    SupplyRelation,
    SupplyRelationType,
)

__all__ = [
    # Base graph
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
    # Supply graph models
    "SupplyEntity",
    "SupplyEntityType",
    "SupplyGraph",
    "SupplyRelation",
    "SupplyRelationType",
    # Supply graph database
    "SupplyGraphDatabase",
    "ValidationError",
    "CycleDetectedError",
    "GraphPath",
    "get_supply_graph",
    "set_supply_graph",
    # Supply graph evaluation
    "SupplyGraphEvaluator",
    "GraphBenchmark",
    "EntityQualityMetrics",
    "RelationQualityMetrics",
    "GraphMetrics",
    "PerformanceMetrics",
    "EvaluationResult",
]
