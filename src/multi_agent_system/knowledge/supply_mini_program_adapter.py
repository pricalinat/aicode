"""Mini-Program Structured Input Adapter.

This module provides adapters for converting mini-program structured inputs
into knowledge graph entities and relations.

Supports:
- Form data from mini-program pages
- Intent/slot extraction from user queries
- Product and service data from mini-program APIs
- Batch import from mini-program data exports
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .supply_graph_database import SupplyGraphDatabase
from .supply_graph_models import (
    SupplyEntity,
    SupplyEntityType,
    SupplyRelation,
    SupplyRelationType,
)
from .supply_ingestion import SupplyGraphIngestionPipeline, BatchConfig


@dataclass
class MiniProgramFormData:
    """Represents parsed form data from a mini-program page."""
    page_name: str
    fields: dict[str, Any]
    user_id: str | None = None
    timestamp: str | None = None
    session_id: str | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class MiniProgramIntent:
    """Represents an extracted intent from mini-program user interaction."""
    intent_name: str
    confidence: float = 1.0
    slots: dict[str, Any] = field(default_factory=dict)
    raw_query: str | None = None
    entities: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class MiniProgramProduct:
    """Represents a product from mini-program structured data."""
    name: str
    category: str | None = None
    brand: str | None = None
    price: float | None = None
    sku: str | None = None
    description: str | None = None
    merchant_id: str | None = None
    supplier_id: str | None = None
    region_ids: list[str] = field(default_factory=list)
    channel_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MiniProgramService:
    """Represents a service from mini-program structured data."""
    name: str
    category: str | None = None
    description: str | None = None
    procedure_ids: list[str] = field(default_factory=list)
    merchant_id: str | None = None
    region_ids: list[str] = field(default_factory=list)
    intent_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MiniProgramSlot:
    """Represents a slot (parameter) for intent recognition."""
    name: str
    slot_type: str
    value: Any = None
    required: bool = False
    description: str | None = None


@dataclass
class ConversionResult:
    """Result of converting mini-program data to KG entities."""
    entities_created: int = 0
    relations_created: int = 0
    entity_ids: list[str] = field(default_factory=list)
    relation_triplets: list[tuple[str, str, str]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class MiniProgramFormAdapter:
    """Adapter for parsing mini-program form data.

    Converts structured form submissions into knowledge graph entities.

    Example form types:
    - Product submission forms
    - Service registration forms
    - Merchant onboarding forms
    - Category management forms
    """

    # Form type to entity type mapping
    FORM_TYPE_MAPPING: dict[str, SupplyEntityType] = {
        "product": SupplyEntityType.PRODUCT,
        "service": SupplyEntityType.SERVICE,
        "procedure": SupplyEntityType.PROCEDURE,
        "intent": SupplyEntityType.INTENT,
        "slot": SupplyEntityType.SLOT,
        "category": SupplyEntityType.CATEGORY,
        "brand": SupplyEntityType.BRAND,
        "supplier": SupplyEntityType.SUPPLIER,
        "merchant": SupplyEntityType.MERCHANT,
        "region": SupplyEntityType.REGION,
        "channel": SupplyEntityType.CHANNEL,
    }

    # Field name normalization
    FIELD_ALIASES: dict[str, str] = {
        "product_name": "name",
        "product_name": "name",
        "service_name": "name",
        "prod_desc": "description",
        "srv_desc": "description",
        "prod_price": "price",
        "prod_category": "category",
        "prod_brand": "brand",
        "prod_sku": "sku",
        "merchant_name": "name",
        "supplier_name": "name",
    }

    def __init__(self, db: SupplyGraphDatabase | None = None):
        self.db = db or SupplyGraphDatabase()

    def parse_form_data(self, form_data: dict[str, Any]) -> MiniProgramFormData:
        """Parse raw form data into structured format.

        Args:
            form_data: Raw form data from mini-program

        Returns:
            Parsed MiniProgramFormData
        """
        return MiniProgramFormData(
            page_name=form_data.get("page_name", "unknown"),
            fields=form_data.get("fields", form_data),  # Fallback to whole dict
            user_id=form_data.get("user_id"),
            timestamp=form_data.get("timestamp"),
            session_id=form_data.get("session_id"),
        )

    def convert_to_entity(
        self,
        form_data: MiniProgramFormData,
        entity_type: str,
    ) -> SupplyEntity | None:
        """Convert form data to a knowledge graph entity.

        Args:
            form_data: Parsed form data
            entity_type: Type of entity to create

        Returns:
            SupplyEntity or None if conversion fails
        """
        if entity_type not in self.FORM_TYPE_MAPPING:
            return None

        # Generate ID if not provided
        entity_id = form_data.fields.get("id") or self._generate_entity_id(
            entity_type, form_data.fields.get("name", "")
        )

        # Normalize field names
        normalized_fields = self._normalize_fields(form_data.fields)

        # Determine name field
        name = normalized_fields.get("name") or entity_id

        # Create entity
        entity = SupplyEntity(
            id=entity_id,
            type=self.FORM_TYPE_MAPPING[entity_type],
            properties=normalized_fields,
        )

        # Add metadata
        entity.properties["_source"] = "mini_program"
        entity.properties["_page"] = form_data.page_name
        if form_data.user_id:
            entity.properties["_user_id"] = form_data.user_id
        if form_data.timestamp:
            entity.properties["_submitted_at"] = form_data.timestamp

        return entity

    def convert_form_to_entities(
        self,
        form_data: dict[str, Any],
        entity_type: str,
    ) -> ConversionResult:
        """Convert form data to entities and create in KG.

        Args:
            form_data: Raw form data from mini-program
            entity_type: Type of entity to create

        Returns:
            ConversionResult with creation status
        """
        result = ConversionResult()

        # Parse form data
        parsed = self.parse_form_data(form_data)

        # Convert to entity
        entity = self.convert_to_entity(parsed, entity_type)

        if entity is None:
            result.errors.append(f"Unknown entity type: {entity_type}")
            return result

        try:
            self.db.create_entity(entity, validate=False)
            result.entities_created = 1
            result.entity_ids.append(entity.id)
        except ValueError as e:
            result.errors.append(f"Failed to create entity: {e}")

        return result

    def _normalize_fields(self, fields: dict[str, Any]) -> dict[str, Any]:
        """Normalize field names using aliases."""
        normalized = {}
        for key, value in fields.items():
            # Skip internal fields
            if key.startswith("_"):
                continue
            # Apply alias if exists
            normalized_key = self.FIELD_ALIASES.get(key, key)
            normalized[normalized_key] = value
        return normalized

    def _generate_entity_id(self, entity_type: str, name: str) -> str:
        """Generate a unique entity ID."""
        # Create slug from name
        slug = name.lower().replace(" ", "_")[:30]
        # Add prefix and short UUID
        return f"{entity_type}_{slug}"


class MiniProgramIntentAdapter:
    """Adapter for extracting and managing intents from mini-program queries.

    Handles intent recognition from user queries in mini-program chats
    and converts them to KG entities.
    """

    # Common intent patterns for e-commerce mini-programs
    INTENT_PATTERNS: dict[str, list[str]] = {
        "search_product": ["search", "find", "look for", "找", "搜索"],
        "view_product": ["view", "show", "详情", "查看"],
        "add_to_cart": ["add", "buy", "加入购物车", "购买"],
        "checkout": ["checkout", "pay", "结算", "付款"],
        "query_order": ["order", "订单"],
        "view_cart": ["cart", "购物车"],
        "compare": ["compare", "对比", "比较"],
        "filter": ["filter", "筛选"],
        "sort": ["sort", "排序"],
    }

    def __init__(self, db: SupplyGraphDatabase | None = None):
        self.db = db or SupplyGraphDatabase()

    def extract_intent(
        self,
        query: str,
        slots: dict[str, Any] | None = None,
    ) -> MiniProgramIntent:
        """Extract intent from user query.

        Args:
            query: User query text
            slots: Pre-extracted slots/parameters

        Returns:
            Extracted intent with confidence
        """
        query_lower = query.lower()

        # Match against patterns
        best_match = None
        best_score = 0.0

        for intent_name, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if pattern in query_lower:
                    # Calculate confidence based on match position
                    position = query_lower.find(pattern)
                    score = len(pattern) / len(query)  # Longer matches = higher score
                    if score > best_score:
                        best_score = score
                        best_match = intent_name

        if best_match is None:
            # Default intent
            return MiniProgramIntent(
                intent_name="general_query",
                confidence=0.5,
                raw_query=query,
                slots=slots or {},
            )

        return MiniProgramIntent(
            intent_name=best_match,
            confidence=min(1.0, best_score + 0.3),  # Base confidence
            raw_query=query,
            slots=slots or {},
        )

    def convert_intent_to_entities(
        self,
        intent: MiniProgramIntent,
        service_id: str | None = None,
    ) -> ConversionResult:
        """Convert extracted intent to KG entities.

        Args:
            intent: Extracted intent
            service_id: Associated service ID

        Returns:
            ConversionResult with creation status
        """
        result = ConversionResult()

        # Create intent entity
        intent_id = f"intent_{intent.intent_name}_{uuid.uuid4().hex[:6]}"

        intent_entity = SupplyEntity(
            id=intent_id,
            type=SupplyEntityType.INTENT,
            properties={
                "name": intent.intent_name,
                "confidence": intent.confidence,
                "raw_query": intent.raw_query or "",
                "slots": list(intent.slots.keys()),
                "_source": "mini_program",
            },
        )

        try:
            self.db.create_entity(intent_entity, validate=False)
            result.entities_created += 1
            result.entity_ids.append(intent_id)
        except ValueError as e:
            result.errors.append(f"Failed to create intent: {e}")
            return result

        # Create slot entities if present
        for slot_name, slot_value in intent.slots.items():
            slot_id = f"slot_{slot_name}_{uuid.uuid4().hex[:6]}"

            # Determine slot type
            slot_type = self._infer_slot_type(slot_value)

            slot_entity = SupplyEntity(
                id=slot_id,
                type=SupplyEntityType.SLOT,
                properties={
                    "name": slot_name,
                    "slot_type": slot_type,
                    "value": str(slot_value) if slot_value is not None else None,
                    "_source": "mini_program",
                },
            )

            try:
                self.db.create_entity(slot_entity, validate=False)
                result.entities_created += 1
                result.entity_ids.append(slot_id)

                # Create HAS_SLOT relation
                slot_relation = SupplyRelation(
                    source_id=intent_id,
                    target_id=slot_id,
                    relation_type=SupplyRelationType.HAS_SLOT,
                )
                self.db.create_relation(slot_relation, validate=False)
                result.relations_created += 1
                result.relation_triplets.append((intent_id, "has_slot", slot_id))

            except (ValueError, KeyError) as e:
                result.warnings.append(f"Failed to create slot {slot_name}: {e}")

        # Link to service if provided
        if service_id:
            service_relation = SupplyRelation(
                source_id=service_id,
                target_id=intent_id,
                relation_type=SupplyRelationType.HAS_INTENT,
            )
            try:
                self.db.create_relation(service_relation, validate=False)
                result.relations_created += 1
                result.relation_triplets.append((service_id, "has_intent", intent_id))
            except (ValueError, KeyError) as e:
                result.warnings.append(f"Failed to link intent to service: {e}")

        return result

    def _infer_slot_type(self, value: Any) -> str:
        """Infer slot type from value."""
        if value is None:
            return "string"
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "integer"
        if isinstance(value, float):
            return "float"
        if isinstance(value, (list, tuple)):
            return "array"
        return "string"


class MiniProgramDataAdapter:
    """Adapter for batch importing mini-program data exports.

    Handles bulk conversion of mini-program data exports
    (JSON, CSV) into knowledge graph entities.
    """

    def __init__(
        self,
        db: SupplyGraphDatabase | None = None,
        pipeline: SupplyGraphIngestionPipeline | None = None,
    ):
        self.db = db or SupplyGraphDatabase()
        self.pipeline = pipeline or SupplyGraphIngestionPipeline(self.db)
        self.form_adapter = MiniProgramFormAdapter(self.db)
        self.intent_adapter = MiniProgramIntentAdapter(self.db)

    def import_products(
        self,
        products: list[dict[str, Any]],
        config: BatchConfig | None = None,
    ) -> ConversionResult:
        """Import products from mini-program data.

        Args:
            products: List of product data dictionaries
            config: Batch configuration

        Returns:
            ConversionResult with import status
        """
        result = ConversionResult()
        config = config or BatchConfig()

        for product_data in products:
            # Generate entity
            product_id = product_data.get("id") or f"product_{uuid.uuid4().hex[:8]}"

            entity = SupplyEntity(
                id=product_id,
                type=SupplyEntityType.PRODUCT,
                properties={
                    "name": product_data.get("name", "Unnamed Product"),
                    **{k: v for k, v in product_data.items() if k not in ("id",)},
                },
            )

            try:
                self.db.create_entity(entity, validate=False)
                result.entities_created += 1
                result.entity_ids.append(product_id)

                # Create relations based on referenced IDs
                self._create_product_relations(product_id, product_data, result)

            except ValueError as e:
                result.errors.append(f"Failed to create product: {e}")

        return result

    def import_services(
        self,
        services: list[dict[str, Any]],
        config: BatchConfig | None = None,
    ) -> ConversionResult:
        """Import services from mini-program data.

        Args:
            services: List of service data dictionaries
            config: Batch configuration

        Returns:
            ConversionResult with import status
        """
        result = ConversionResult()
        config = config or BatchConfig()

        for service_data in services:
            service_id = service_data.get("id") or f"service_{uuid.uuid4().hex[:8]}"

            entity = SupplyEntity(
                id=service_id,
                type=SupplyEntityType.SERVICE,
                properties={
                    "name": service_data.get("name", "Unnamed Service"),
                    **{k: v for k, v in service_data.items() if k not in ("id",)},
                },
            )

            try:
                self.db.create_entity(entity, validate=False)
                result.entities_created += 1
                result.entity_ids.append(service_id)

                # Create relations
                self._create_service_relations(service_id, service_data, result)

            except ValueError as e:
                result.errors.append(f"Failed to create service: {e}")

        return result

    def import_user_queries(
        self,
        queries: list[dict[str, Any]],
        service_id: str | None = None,
    ) -> ConversionResult:
        """Import user queries and extract intents.

        Args:
            queries: List of query data with 'query' field
            service_id: Optional service to link intents to

        Returns:
            ConversionResult with import status
        """
        result = ConversionResult()

        for query_data in queries:
            query_text = query_data.get("query")
            if not query_text:
                result.warnings.append("Query missing text field")
                continue

            slots = query_data.get("slots", {})

            # Extract intent
            intent = self.intent_adapter.extract_intent(query_text, slots)

            # Convert to KG entities
            conv_result = self.intent_adapter.convert_intent_to_entities(
                intent, service_id
            )

            result.entities_created += conv_result.entities_created
            result.relations_created += conv_result.relations_created
            result.entity_ids.extend(conv_result.entity_ids)
            result.relation_triplets.extend(conv_result.relation_triplets)
            result.errors.extend(conv_result.errors)
            result.warnings.extend(conv_result.warnings)

        return result

    def _create_product_relations(
        self,
        product_id: str,
        product_data: dict[str, Any],
        result: ConversionResult,
    ) -> None:
        """Create relations for imported product."""

        # Category relation
        if "category" in product_data:
            cat_id = str(product_data["category"])
            # Create category if not exists
            self._ensure_entity(
                SupplyEntityType.CATEGORY, cat_id, {"name": cat_id}, result
            )
            self._create_relation(
                product_id, cat_id, SupplyRelationType.BELONGS_TO, result
            )

        # Brand relation
        if "brand" in product_data:
            brand_id = str(product_data["brand"])
            self._ensure_entity(
                SupplyEntityType.BRAND, brand_id, {"name": brand_id}, result
            )
            self._create_relation(
                product_id, brand_id, SupplyRelationType.HAS_BRAND, result
            )

        # Supplier relation
        if "supplier" in product_data:
            supplier_id = str(product_data["supplier"])
            self._ensure_entity(
                SupplyEntityType.SUPPLIER, supplier_id, {"name": supplier_id}, result
            )
            self._create_relation(
                supplier_id, product_id, SupplyRelationType.SUPPLIES, result
            )

        # Merchant relation
        if "merchant" in product_data:
            merchant_id = str(product_data["merchant"])
            self._ensure_entity(
                SupplyEntityType.MERCHANT, merchant_id, {"name": merchant_id}, result
            )
            self._create_relation(
                merchant_id, product_id, SupplyRelationType.SELLS, result
            )

    def _create_service_relations(
        self,
        service_id: str,
        service_data: dict[str, Any],
        result: ConversionResult,
    ) -> None:
        """Create relations for imported service."""

        # Category relation
        if "category" in service_data:
            cat_id = str(service_data["category"])
            self._ensure_entity(
                SupplyEntityType.CATEGORY, cat_id, {"name": cat_id}, result
            )
            self._create_relation(
                service_id, cat_id, SupplyRelationType.BELONGS_TO, result
            )

        # Merchant relation
        if "merchant" in service_data:
            merchant_id = str(service_data["merchant"])
            self._ensure_entity(
                SupplyEntityType.MERCHANT, merchant_id, {"name": merchant_id}, result
            )
            self._create_relation(
                merchant_id, service_id, SupplyRelationType.OFFERS, result
            )

    def _ensure_entity(
        self,
        entity_type: SupplyEntityType,
        entity_id: str,
        properties: dict[str, Any],
        result: ConversionResult,
    ) -> None:
        """Ensure entity exists, create if not."""
        if self.db.get_entity(entity_id) is None:
            entity = SupplyEntity(
                id=entity_id,
                type=entity_type,
                properties=properties,
            )
            try:
                self.db.create_entity(entity, validate=False)
                result.entities_created += 1
                result.entity_ids.append(entity_id)
            except ValueError:
                pass  # Already exists

    def _create_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: SupplyRelationType,
        result: ConversionResult,
    ) -> None:
        """Create relation if both entities exist."""
        if source_id in self.db._entities and target_id in self.db._entities:
            relation = SupplyRelation(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type,
            )
            try:
                self.db.create_relation(relation, validate=False)
                result.relations_created += 1
                result.relation_triplets.append((source_id, relation_type.value, target_id))
            except (ValueError, KeyError):
                pass  # Already exists or entity missing


# Global instances
_global_form_adapter: MiniProgramFormAdapter | None = None
_global_intent_adapter: MiniProgramIntentAdapter | None = None
_global_data_adapter: MiniProgramDataAdapter | None = None


def get_form_adapter(db: SupplyGraphDatabase | None = None) -> MiniProgramFormAdapter:
    """Get the global form adapter instance."""
    global _global_form_adapter
    if _global_form_adapter is None:
        _global_form_adapter = MiniProgramFormAdapter(db)
    return _global_form_adapter


def get_intent_adapter(db: SupplyGraphDatabase | None = None) -> MiniProgramIntentAdapter:
    """Get the global intent adapter instance."""
    global _global_intent_adapter
    if _global_intent_adapter is None:
        _global_intent_adapter = MiniProgramIntentAdapter(db)
    return _global_intent_adapter


def get_data_adapter(
    db: SupplyGraphDatabase | None = None,
) -> MiniProgramDataAdapter:
    """Get the global data adapter instance."""
    global _global_data_adapter
    if _global_data_adapter is None:
        _global_data_adapter = MiniProgramDataAdapter(db)
    return _global_data_adapter
