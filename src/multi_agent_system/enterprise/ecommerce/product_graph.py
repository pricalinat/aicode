"""E-commerce Knowledge Graph - Product Graph.

Provides product knowledge representation, relationships, and queries
for e-commerce scenarios.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ProductCategory(Enum):
    """Product categories."""
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    FOOD = "food"
    HOME = "home"
    SPORTS = "sports"
    BOOKS = "books"
    OTHER = "other"


class RelationType(Enum):
    """Product relationship types."""
    IS_A = "is_a"              # Category relationship
    HAS_FEATURE = "has_feature"  # Has specific feature
    SIMILAR_TO = "similar_to"   # Similar products
    COMPETES_WITH = "competes_with"  # Competing products
    COMplements = "complements"  # Complementary products
    BUNDLED_WITH = "bundled_with"  # Bundle deals


@dataclass
class ProductAttribute:
    """Product attribute."""
    name: str = ""
    value: Any = None
    unit: str = ""


@dataclass
class Product:
    """Product entity."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    sku: str = ""
    name: str = ""
    description: str = ""

    # Category
    category: ProductCategory = ProductCategory.OTHER
    subcategory: str = ""

    # Attributes
    attributes: dict[str, ProductAttribute] = field(default_factory=dict)

    # Pricing
    price: float = 0.0
    original_price: float = 0.0
    discount: float = 0.0

    # Stock
    stock: int = 0
    stock_status: str = "in_stock"  # in_stock, low_stock, out_of_stock

    # Brand & Supplier
    brand: str = ""
    supplier: str = ""

    # Tags
    tags: list[str] = field(default_factory=list)

    # Metrics
    rating: float = 0.0
    review_count: int = 0
    sales_count: int = 0

    # Embedding for similarity
    embedding: list[float] | None = None

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def get_attribute(self, name: str) -> Any:
        """Get attribute value."""
        attr = self.attributes.get(name)
        return attr.value if attr else None

    def set_attribute(self, name: str, value: Any, unit: str = "") -> None:
        """Set attribute."""
        self.attributes[name] = ProductAttribute(name=name, value=value, unit=unit)


@dataclass
class ProductRelation:
    """Product relationship."""
    product_id_1: str = ""
    product_id_2: str = ""
    relation_type: RelationType = RelationType.SIMILAR_TO
    weight: float = 1.0  # Relationship strength
    metadata: dict[str, Any] = field(default_factory=dict)


class ProductGraph:
    """Product knowledge graph.

    Features:
    - Product entity management
    - Relationship mapping
    - Category hierarchy
    - Similarity search
    """

    def __init__(self) -> None:
        """Initialize product graph."""
        self._products: dict[str, Product] = {}
        self._relations: list[ProductRelation] = []
        self._by_category: dict[ProductCategory, set[str]] = {}
        self._by_brand: dict[str, set[str]] = {}

    def add_product(self, product: Product) -> Product:
        """Add product to graph."""
        self._products[product.id] = product

        # Index by category
        if product.category not in self._by_category:
            self._by_category[product.category] = set()
        self._by_category[product.category].add(product.id)

        # Index by brand
        if product.brand:
            if product.brand not in self._by_brand:
                self._by_brand[product.brand] = set()
            self._by_brand[product.brand].add(product.id)

        return product

    def add_relation(
        self,
        product_id_1: str,
        product_id_2: str,
        relation_type: RelationType,
        weight: float = 1.0,
    ) -> ProductRelation | None:
        """Add product relationship."""
        if product_id_1 not in self._products or product_id_2 not in self._products:
            return None

        relation = ProductRelation(
            product_id_1=product_id_1,
            product_id_2=product_id_2,
            relation_type=relation_type,
            weight=weight,
        )
        self._relations.append(relation)
        return relation

    def get_product(self, product_id: str) -> Product | None:
        """Get product by ID."""
        return self._products.get(product_id)

    def get_by_category(self, category: ProductCategory) -> list[Product]:
        """Get products by category."""
        ids = self._by_category.get(category, set())
        return [self._products[i] for i in ids if i in self._products]

    def get_by_brand(self, brand: str) -> list[Product]:
        """Get products by brand."""
        ids = self._by_brand.get(brand, set())
        return [self._products[i] for i in ids if i in self._products]

    def get_related(
        self,
        product_id: str,
        relation_type: RelationType | None = None,
    ) -> list[Product]:
        """Get related products."""
        related = []

        for rel in self._relations:
            if rel.product_id_1 == product_id or rel.product_id_2 == product_id:
                if relation_type and rel.relation_type != relation_type:
                    continue

                other_id = rel.product_id_2 if rel.product_id_1 == product_id else rel.product_id_1
                if other_id in self._products:
                    related.append(self._products[other_id])

        return related

    def search(
        self,
        query: str,
        category: ProductCategory | None = None,
        brand: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        tags: list[str] | None = None,
        limit: int = 20,
    ) -> list[Product]:
        """Search products."""
        results = []

        for product in self._products.values():
            # Category filter
            if category and product.category != category:
                continue

            # Brand filter
            if brand and product.brand.lower() != brand.lower():
                continue

            # Price filter
            if min_price and product.price < min_price:
                continue
            if max_price and product.price > max_price:
                continue

            # Tags filter
            if tags:
                if not any(tag in product.tags for tag in tags):
                    continue

            # Text match
            query_lower = query.lower()
            match = (
                query_lower in product.name.lower() or
                query_lower in product.description.lower() or
                query_lower in product.brand.lower()
            )

            if match or not query:
                results.append(product)

        # Sort by rating
        results.sort(key=lambda p: p.rating, reverse=True)
        return results[:limit]

    def recommend_similar(
        self,
        product_id: str,
        limit: int = 5,
    ) -> list[Product]:
        """Recommend similar products."""
        return self.get_related(product_id, RelationType.SIMILAR_TO)[:limit]

    def recommend_complementary(
        self,
        product_id: str,
        limit: int = 5,
    ) -> list[Product]:
        """Recommend complementary products."""
        return self.get_related(product_id, RelationType.COMPLEMENTS)[:limit]

    def get_stats(self) -> dict[str, Any]:
        """Get graph statistics."""
        return {
            "total_products": len(self._products),
            "total_relations": len(self._relations),
            "by_category": {
                cat.value: len(ids)
                for cat, ids in self._by_category.items()
            },
            "brands": list(self._by_brand.keys()),
        }


# Global product graph
_product_graph: ProductGraph | None = None


def get_product_graph() -> ProductGraph:
    """Get global product graph."""
    global _product_graph
    if _product_graph is None:
        _product_graph = ProductGraph()
    return _product_graph
