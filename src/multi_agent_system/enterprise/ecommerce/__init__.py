"""E-commerce knowledge graph modules."""

from .product_graph import (
    ProductGraph,
    Product,
    ProductCategory,
    ProductRelation,
    RelationType,
)
from .user_graph import (
    UserGraph,
    UserProfile,
    UserBehavior,
    UserPreference,
    UserType,
    UserSegment,
)
from .scene_graph import (
    SceneGraph,
    SceneContext,
    ScenePattern,
    SceneType,
    TimeContext,
    LocationContext,
)

__all__ = [
    # Product Graph
    "ProductGraph",
    "Product",
    "ProductCategory",
    "ProductRelation",
    "RelationType",
    # User Graph
    "UserGraph",
    "UserProfile",
    "UserBehavior",
    "UserPreference",
    "UserType",
    "UserSegment",
    # Scene Graph
    "SceneGraph",
    "SceneContext",
    "ScenePattern",
    "SceneType",
    "TimeContext",
    "LocationContext",
]
