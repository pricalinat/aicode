"""Data layer: Relation definitions for knowledge graph."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class RelationType(Enum):
    """Relation types in the knowledge graph."""

    # User intent relations
    HAS_INTENT = "has_intent"  # User -> Intent
    PREFERS = "prefers"  # User -> Preference
    EXHIBITS = "exhibits"  # User -> Behavior
    SEARCHES = "searches"  # User -> Query
    ORIGINATES_FROM = "originates_from"  # Query -> User

    # Supply relations
    BELONGS_TO = "belongs_to"  # Product -> Category
    HAS_ATTR = "has_attr"  # Product -> Attribute
    HAS_BRAND = "has_brand"  # Product -> Brand
    MATCHES_INTENT = "matches_intent"  # Product -> Intent
    SIMILAR_TO = "similar_to"  # Product -> Product
    AVAILABLE_IN = "available_in"  # Product -> City

    # Service relations
    PROVIDES = "provides"  # Service -> Category
    OPERATES_IN = "operates_in"  # Service -> City
    CHANNELS_THROUGH = "channels_through"  # Service -> Channel

    # Context relations
    HAS_TIME_CONSTRAINT = "has_time_constraint"  # Intent/Search -> Time
    HAS_PRICE_RANGE = "has_price_range"  # Intent -> Price
    REQUIRES_SLOT = "requires_slot"  # Intent -> Slot

    # Cross-graph relations (user-supply matching)
    CAN_SATISFY = "can_satisfy"  # Supply -> User Intent
    LOOKS_FOR = "looks_for"  # User Intent -> Supply

    # Collaborative relations
    CO_OCCURS_WITH = "co_occurs_with"  # Entity -> Entity
    VIEWED_BY = "viewed_by"  # Product -> User
    PURCHASED_BY = "purchased_by"  # Product -> User


@dataclass
class Relation:
    """Relation between two entities."""

    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0
    properties: Optional[Dict[str, Any]] = None

    def to_tuple(self):
        return (self.source_id, self.target_id, self.relation_type.value, self.weight)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.relation_type.value,
            "weight": self.weight,
            "properties": self.properties or {},
        }

    def __hash__(self):
        return hash((self.source_id, self.target_id, self.relation_type.value))

    def __eq__(self, other):
        if not isinstance(other, Relation):
            return False
        return (
            self.source_id == other.source_id
            and self.target_id == other.target_id
            and self.relation_type == other.relation_type
        )


class RelationBuilder:
    """Builder for creating relations from data records."""

    @staticmethod
    def build_user_intent_relations(user_id: str, intent: str, label: Dict[str, Any]) -> list[Relation]:
        """Build relations from user intent label."""
        relations = []

        # User has intent
        relations.append(Relation(
            source_id=user_id,
            target_id=f"intent_{intent}",
            relation_type=RelationType.HAS_INTENT,
        ))

        # User prefers certain category
        target_category = label.get("target_category")
        if target_category:
            relations.append(Relation(
                source_id=user_id,
                target_id=f"category_{target_category}",
                relation_type=RelationType.PREFERS,
            ))

        # Price range preference
        price_range = label.get("price_range")
        if price_range:
            relations.append(Relation(
                source_id=user_id,
                target_id=f"price_{price_range.get('min')}_{price_range.get('max')}",
                relation_type=RelationType.PREFERS,
                properties={"price_range": price_range},
            ))

        # Must have attributes
        must_have = label.get("must_have", [])
        for attr in must_have:
            relations.append(Relation(
                source_id=user_id,
                target_id=f"attr_{attr}",
                relation_type=RelationType.PREFERS,
            ))

        # Exclude attributes
        exclude = label.get("exclude", [])
        for attr in exclude:
            relations.append(Relation(
                source_id=user_id,
                target_id=f"attr_{attr}",
                relation_type=RelationType.EXHIBITS,
                properties={"excluded": True},
            ))

        return relations

    @staticmethod
    def build_product_relations(product_id: str, product: Dict[str, Any], label: Dict[str, Any]) -> list[Relation]:
        """Build relations from product data."""
        relations = []

        # Category relation
        category_lv1 = product.get("category_lv1")
        category_lv2 = product.get("category_lv2")
        if category_lv1:
            relations.append(Relation(
                source_id=product_id,
                target_id=f"category_lv1_{category_lv1}",
                relation_type=RelationType.BELONGS_TO,
            ))
        if category_lv2:
            relations.append(Relation(
                source_id=product_id,
                target_id=f"category_lv2_{category_lv2}",
                relation_type=RelationType.BELONGS_TO,
            ))

        # Brand relation
        brand = product.get("brand")
        if brand:
            relations.append(Relation(
                source_id=product_id,
                target_id=f"brand_{brand}",
                relation_type=RelationType.HAS_BRAND,
            ))

        # Attributes
        attrs = product.get("attributes", {})
        for attr_type, value in attrs.items():
            relations.append(Relation(
                source_id=product_id,
                target_id=f"attr_{attr_type}_{value}",
                relation_type=RelationType.HAS_ATTR,
                properties={"attr_type": attr_type, "value": value},
            ))

        # Intent matching
        intent = label.get("intent")
        if intent:
            relations.append(Relation(
                source_id=product_id,
                target_id=f"intent_{intent}",
                relation_type=RelationType.MATCHES_INTENT,
            ))

        return relations

    @staticmethod
    def build_service_relations(service_id: str, service: Dict[str, Any], label: Dict[str, Any]) -> list[Relation]:
        """Build relations from service data."""
        relations = []

        # Category
        category = service.get("category")
        if category:
            relations.append(Relation(
                source_id=service_id,
                target_id=f"service_category_{category}",
                relation_type=RelationType.PROVIDES,
            ))

        # City
        city = service.get("city")
        if city:
            relations.append(Relation(
                source_id=service_id,
                target_id=f"city_{city}",
                relation_type=RelationType.OPERATES_IN,
            ))

        # Channel
        channel = service.get("channel")
        if channel:
            relations.append(Relation(
                source_id=service_id,
                target_id=f"channel_{channel}",
                relation_type=RelationType.CHANNELS_THROUGH,
            ))

        # Intent
        intent = label.get("intent")
        if intent:
            relations.append(Relation(
                source_id=service_id,
                target_id=f"intent_{intent}",
                relation_type=RelationType.MATCHES_INTENT,
            ))

        # Required slots
        required_slots = label.get("required_slots", [])
        for slot in required_slots:
            relations.append(Relation(
                source_id=service_id,
                target_id=f"slot_{slot}",
                relation_type=RelationType.REQUIRES_SLOT,
            ))

        # Time constraint
        time_constraint = label.get("time_constraint")
        if time_constraint:
            relations.append(Relation(
                source_id=service_id,
                target_id=f"time_{time_constraint.get('before', 'any')}",
                relation_type=RelationType.HAS_TIME_CONSTRAINT,
            ))

        return relations
