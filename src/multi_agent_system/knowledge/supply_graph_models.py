"""Supply Knowledge Graph data models.

This module extends the base graph models with entities and relations
specific to e-commerce product supply and mini-program services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SupplyEntityType(Enum):
    """Entity types for supply knowledge graph.

    Covers e-commerce products, suppliers, and mini-program services.
    """
    # E-commerce core
    PRODUCT = "product"
    SKU = "sku"
    BRAND = "brand"
    CATEGORY = "category"
    MERCHANT = "merchant"
    SUPPLIER = "supplier"

    # Mini-program services
    SERVICE = "service"
    PROCEDURE = "procedure"
    INTENT = "intent"
    SLOT = "slot"

    # Geographic/Policy
    CHANNEL = "channel"
    REGION = "region"
    POLICY = "policy"

    # Risk & Tags
    RISK_TAG = "risk_tag"

    # Users
    USER = "user"


class SupplyRelationType(Enum):
    """Relation types for supply knowledge graph."""

    # Product relations
    HAS_SKU = "has_sku"  # Product -> SKU
    HAS_BRAND = "has_brand"  # Product -> Brand
    BELONGS_TO = "belongs_to"  # Product/Service -> Category

    # Supply chain relations
    SUPPLIES = "supplies"  # Supplier -> Product
    SELLS = "sells"  # Merchant -> Product
    OFFERS = "offers"  # Merchant/Supplier -> Service

    # Mini-program relations
    PROVIDES_SERVICE = "provides_service"  # Procedure -> Service
    HAS_INTENT = "has_intent"  # Service -> Intent
    HAS_SLOT = "has_slot"  # Intent -> Slot

    # Channel relations
    AVAILABLE_IN = "available_in"  # Product/Service -> Channel
    OPERATES_IN = "operates_in"  # Merchant/Supplier -> Region

    # Policy relations
    GOVERNED_BY = "governed_by"  # Product/Service -> Policy

    # Risk relations
    HAS_RISK = "has_risk"  # Product/Supplier -> RiskTag

    # Generic relations
    SIMILAR_TO = "similar_to"
    RELATED_TO = "related_to"


# Extended entity type mapping for graph compatibility
ENTITY_TYPE_MAPPING = {
    SupplyEntityType.PRODUCT: "product",
    SupplyEntityType.SKU: "sku",
    SupplyEntityType.BRAND: "brand",
    SupplyEntityType.CATEGORY: "category",
    SupplyEntityType.MERCHANT: "merchant",
    SupplyEntityType.SUPPLIER: "supplier",
    SupplyEntityType.SERVICE: "service",
    SupplyEntityType.PROCEDURE: "procedure",
    SupplyEntityType.INTENT: "intent",
    SupplyEntityType.SLOT: "slot",
    SupplyEntityType.CHANNEL: "channel",
    SupplyEntityType.REGION: "region",
    SupplyEntityType.POLICY: "policy",
    SupplyEntityType.RISK_TAG: "risk_tag",
    SupplyEntityType.USER: "user",
}


# Extended relation type mapping for graph compatibility
RELATION_TYPE_MAPPING = {
    SupplyRelationType.HAS_SKU: "has_sku",
    SupplyRelationType.HAS_BRAND: "has_brand",
    SupplyRelationType.BELONGS_TO: "belongs_to",
    SupplyRelationType.SUPPLIES: "supplies",
    SupplyRelationType.SELLS: "sells",
    SupplyRelationType.OFFERS: "offers",
    SupplyRelationType.PROVIDES_SERVICE: "provides_service",
    SupplyRelationType.HAS_INTENT: "has_intent",
    SupplyRelationType.HAS_SLOT: "has_slot",
    SupplyRelationType.AVAILABLE_IN: "available_in",
    SupplyRelationType.OPERATES_IN: "operates_in",
    SupplyRelationType.GOVERNED_BY: "governed_by",
    SupplyRelationType.HAS_RISK: "has_risk",
    SupplyRelationType.SIMILAR_TO: "similar_to",
    SupplyRelationType.RELATED_TO: "related_to",
}


@dataclass
class SupplyEntity:
    """An entity in the supply knowledge graph.

    Extends base Entity with supply-specific properties.
    """
    id: str
    type: SupplyEntityType
    properties: dict[str, Any] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.properties.get("name", self.id)

    @property
    def description(self) -> str | None:
        return self.properties.get("description")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "type": ENTITY_TYPE_MAPPING.get(self.type, self.type.value),
            "properties": self.properties,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SupplyEntity:
        """Create entity from dictionary."""
        entity_type = SupplyEntityType(data.get("type", "product"))
        return cls(
            id=data["id"],
            type=entity_type,
            properties=data.get("properties", {}),
        )


@dataclass
class SupplyRelation:
    """A relation in the supply knowledge graph.

    Extends base Relation with supply-specific properties.
    """
    source_id: str
    target_id: str
    relation_type: SupplyRelationType
    properties: dict[str, Any] = field(default_factory=dict)

    @property
    def weight(self) -> float:
        return self.properties.get("weight", 1.0)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": RELATION_TYPE_MAPPING.get(self.relation_type, self.relation_type.value),
            "properties": self.properties,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SupplyRelation:
        """Create relation from dictionary."""
        rel_type = SupplyRelationType(data.get("relation_type", "related_to"))
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            relation_type=rel_type,
            properties=data.get("properties", {}),
        )


@dataclass
class SupplyGraph:
    """Container for supply knowledge graph data.

    Holds entities and relations for export/import.
    """
    entities: list[SupplyEntity] = field(default_factory=list)
    relations: list[SupplyRelation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "entities": [e.to_dict() for e in self.entities],
            "relations": [r.to_dict() for r in self.relations],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SupplyGraph:
        """Create graph from dictionary."""
        entities = [SupplyEntity.from_dict(e) for e in data.get("entities", [])]
        relations = [SupplyRelation.from_dict(r) for r in data.get("relations", [])]
        metadata = data.get("metadata", {})
        return cls(entities=entities, relations=relations, metadata=metadata)

    def add_entity(self, entity: SupplyEntity) -> None:
        """Add entity to graph."""
        self.entities.append(entity)

    def add_relation(self, relation: SupplyRelation) -> None:
        """Add relation to graph."""
        self.relations.append(relation)

    def get_entities_by_type(self, entity_type: SupplyEntityType) -> list[SupplyEntity]:
        """Get all entities of a specific type."""
        return [e for e in self.entities if e.type == entity_type]

    def get_neighbors(
        self,
        entity_id: str,
        relation_type: SupplyRelationType | None = None,
    ) -> list[SupplyEntity]:
        """Get neighboring entities."""
        neighbor_ids = set()

        for relation in self.relations:
            if relation_type and relation.relation_type != relation_type:
                continue
            if relation.source_id == entity_id:
                neighbor_ids.add(relation.target_id)
            if relation.target_id == entity_id:
                neighbor_ids.add(relation.source_id)

        return [e for e in self.entities if e.id in neighbor_ids]

    def count_entities(self) -> int:
        """Count total entities."""
        return len(self.entities)

    def count_relations(self) -> int:
        """Count total relations."""
        return len(self.relations)
