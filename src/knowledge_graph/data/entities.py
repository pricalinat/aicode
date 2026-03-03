"""Data layer: Entity definitions for knowledge graph."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class EntityType(Enum):
    """Entity types in the knowledge graph."""

    # User intent side
    USER = "user"
    INTENT = "intent"
    PREFERENCE = "preference"
    BEHAVIOR = "behavior"
    QUERY = "query"

    # Supply side
    PRODUCT = "product"
    SERVICE = "service"
    CATEGORY = "category"
    CATEGORY_LV1 = "category_lv1"
    CATEGORY_LV2 = "category_lv2"
    ATTRIBUTE = "attribute"
    BRAND = "brand"
    SUPPLY_STATUS = "supply_status"

    # Context
    CITY = "city"
    CHANNEL = "channel"
    TIME_CONSTRAINT = "time_constraint"


@dataclass
class Entity:
    """Base entity class."""

    id: str
    type: EntityType
    properties: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "properties": self.properties,
        }

    def __hash__(self):
        return hash((self.id, self.type.value))

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return self.id == other.id and self.type == other.type


@dataclass
class UserEntity(Entity):
    """User entity representing a user in the system."""

    def __init__(self, user_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(
            id=user_id,
            type=EntityType.USER,
            properties=properties or {},
        )


@dataclass
class IntentEntity(Entity):
    """Intent entity representing user intent."""

    def __init__(self, intent: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(
            id=f"intent_{intent}",
            type=EntityType.INTENT,
            properties=properties or {"intent": intent},
        )


@dataclass
class ProductEntity(Entity):
    """Product entity representing a product."""

    def __init__(
        self,
        product_id: str,
        title: str,
        category_lv1: str,
        category_lv2: str,
        brand: str,
        price: float,
        attributes: Dict[str, Any],
        properties: Optional[Dict[str, Any]] = None,
    ):
        props = properties or {}
        props.update({
            "title": title,
            "category_lv1": category_lv1,
            "category_lv2": category_lv2,
            "brand": brand,
            "price": price,
            "attributes": attributes,
        })
        super().__init__(
            id=product_id,
            type=EntityType.PRODUCT,
            properties=props,
        )


@dataclass
class ServiceEntity(Entity):
    """Service entity representing a miniapp service."""

    def __init__(
        self,
        service_id: str,
        name: str,
        category: str,
        city: str,
        channel: str,
        properties: Optional[Dict[str, Any]] = None,
    ):
        props = properties or {}
        props.update({
            "name": name,
            "category": category,
            "city": city,
            "channel": channel,
        })
        super().__init__(
            id=service_id,
            type=EntityType.SERVICE,
            properties=props,
        )


@dataclass
class CategoryEntity(Entity):
    """Category entity representing product/service category."""

    def __init__(self, category_id: str, name: str, level: int = 1, properties: Optional[Dict[str, Any]] = None):
        props = properties or {}
        props.update({"name": name, "level": level})
        super().__init__(
            id=category_id,
            type=EntityType.CATEGORY_LV1 if level == 1 else EntityType.CATEGORY_LV2,
            properties=props,
        )


@dataclass
class AttributeEntity(Entity):
    """Attribute entity representing product attribute."""

    def __init__(self, attribute_id: str, attr_type: str, value: str, properties: Optional[Dict[str, Any]] = None):
        props = properties or {}
        props.update({"attr_type": attr_type, "value": value})
        super().__init__(
            id=attribute_id,
            type=EntityType.ATTRIBUTE,
            properties=props,
        )


@dataclass
class BrandEntity(Entity):
    """Brand entity representing product brand."""

    def __init__(self, brand_name: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(
            id=f"brand_{brand_name}",
            type=EntityType.BRAND,
            properties=properties or {"name": brand_name},
        )


@dataclass
class CityEntity(Entity):
    """City entity representing geographic location."""

    def __init__(self, city_name: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(
            id=f"city_{city_name}",
            type=EntityType.CITY,
            properties=properties or {"name": city_name},
        )


class EntityFactory:
    """Factory for creating entities from data records."""

    @staticmethod
    def create_product_from_record(record: Dict[str, Any]) -> ProductEntity:
        """Create product entity from e-commerce record."""
        product = record["product"]
        return ProductEntity(
            product_id=record["id"],
            title=product["title"],
            category_lv1=product["category_lv1"],
            category_lv2=product["category_lv2"],
            brand=product["brand"],
            price=product["price"],
            attributes=product.get("attributes", {}),
        )

    @staticmethod
    def create_service_from_record(record: Dict[str, Any]) -> ServiceEntity:
        """Create service entity from miniapp record."""
        service = record["service"]
        return ServiceEntity(
            service_id=record["id"],
            name=service["name"],
            category=service["category"],
            city=service["city"],
            channel=service["channel"],
        )

    @staticmethod
    def create_user_from_query(query_id: str, query: str) -> UserEntity:
        """Create user entity from query."""
        return UserEntity(
            user_id=query_id,
            properties={"query": query},
        )
