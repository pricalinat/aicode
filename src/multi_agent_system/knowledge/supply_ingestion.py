"""Supply Knowledge Graph Ingestion Pipeline.

This module provides entity normalization, deduplication, and batch ingestion
capabilities for the supply knowledge graph.

Supports:
- Entity normalization (name cleaning, standardization)
- Entity deduplication (finding and merging duplicates)
- Batch ingestion with transaction semantics
- Incremental updates with change tracking and version control
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable
from collections import defaultdict

from .supply_graph_database import SupplyGraphDatabase
from .supply_graph_models import (
    SupplyEntity,
    SupplyEntityType,
    SupplyRelation,
    SupplyRelationType,
)


class ChangeOperation(Enum):
    """Type of change operation."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


@dataclass
class NormalizedEntity:
    """An entity with normalized properties for deduplication."""
    original: SupplyEntity
    normalized_name: str
    normalized_key: str  #用于去重的标准化键


@dataclass
class ChangeRecord:
    """A record of a single change operation."""
    operation: ChangeOperation
    entity_type: str
    entity_id: str
    timestamp: str
    old_version: int | None = None
    new_version: int | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation.value,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "timestamp": self.timestamp,
            "old_version": self.old_version,
            "new_version": self.new_version,
            "details": self.details,
        }


@dataclass
class IngestionResult:
    """Result of an ingestion operation."""
    created: int = 0
    updated: int = 0
    skipped: int = 0
    deleted: int = 0
    errors: list[str] = field(default_factory=list)
    duplicates_found: list[tuple[str, str]] = field(default_factory=list)  # (original_id, existing_id)
    changes: list[ChangeRecord] = field(default_factory=list)

    def add_change(self, change: ChangeRecord) -> None:
        """Add a change record and update counters."""
        self.changes.append(change)
        if change.operation == ChangeOperation.CREATE:
            self.created += 1
        elif change.operation == ChangeOperation.UPDATE:
            self.updated += 1
        elif change.operation == ChangeOperation.DELETE:
            self.deleted += 1


@dataclass
class BatchConfig:
    """Configuration for batch ingestion."""
    skip_duplicates: bool = True
    merge_duplicates: bool = False
    normalize_names: bool = True
    create_relations: bool = True
    batch_size: int = 100
    dry_run: bool = False


class EntityNormalizer:
    """Normalizes entity names for consistent processing.

    Handles:
    - Unicode normalization (NFC)
    - Whitespace trimming and normalization
    - Case normalization (optional)
    - Punctuation removal
    - Chinese character handling
    """

    def __init__(self, lowercase: bool = False, remove_punctuation: bool = True):
        self.lowercase = lowercase
        self.remove_punctuation = remove_punctuation

    def normalize(self, text: str) -> str:
        """Normalize a string for comparison."""
        if not text:
            return ""

        # Unicode normalization (NFC form)
        result = unicodedata.normalize('NFC', text)

        # Convert to lowercase if configured
        if self.lowercase:
            result = result.lower()

        # Normalize whitespace
        result = re.sub(r'\s+', ' ', result).strip()

        # Remove punctuation if configured
        if self.remove_punctuation:
            result = re.sub(r'[^\w\s\u4e00-\u9fff]', '', result)

        return result

    def get_normalized_key(
        self,
        entity: SupplyEntity,
        additional_fields: list[str] | None = None,
    ) -> str:
        """Generate a normalized key for deduplication.

        The key is based on entity type + normalized name + optional fields.
        """
        parts = [entity.type.value, self.normalize(entity.name)]

        if additional_fields:
            for field_name in additional_fields:
                value = entity.properties.get(field_name)
                if value:
                    parts.append(self.normalize(str(value)))

        return "|".join(parts)


class EntityDeduplicator:
    """Finds and handles duplicate entities in the graph.

    Uses normalized name matching to detect potential duplicates.
    """

    def __init__(self, normalizer: EntityNormalizer | None = None):
        self.normalizer = normalizer or EntityNormalizer()

    def find_duplicates(
        self,
        entities: list[SupplyEntity],
        db: SupplyGraphDatabase,
        match_fields: list[str] | None = None,
    ) -> dict[str, list[str]]:
        """Find potential duplicates in a batch of entities.

        Returns a dict mapping normalized keys to lists of entity IDs
        that match that key.
        """
        # Index existing entities by normalized key
        existing_keys: dict[str, str] = {}
        for entity in db._entities.values():
            key = self.normalizer.get_normalized_key(entity, match_fields)
            existing_keys[key] = entity.id

        # Find duplicates in the new batch
        duplicates: dict[str, list[str]] = defaultdict(list)
        seen_keys: dict[str, str] = {}  # key -> entity_id

        for entity in entities:
            key = self.normalizer.get_normalized_key(entity, match_fields)

            # Check within batch first (these are the primary duplicates)
            if key in seen_keys:
                if key not in duplicates:
                    duplicates[key].append(seen_keys[key])
                duplicates[key].append(entity.id)
            else:
                seen_keys[key] = entity.id
                # Also check against existing entities
                if key in existing_keys:
                    duplicates[key].append(entity.id)

        return dict(duplicates)

    def merge_entities(
        self,
        primary: SupplyEntity,
        secondary: SupplyEntity,
        merge_strategy: str = "primary_wins",
    ) -> SupplyEntity:
        """Merge two entities into one.

        Strategies:
        - primary_wins: Primary entity wins, secondary's properties added if missing
        - secondary_wins: Secondary entity wins
        - merge: Properties are merged, lists combined
        """
        if merge_strategy == "primary_wins":
            merged_props = primary.properties.copy()
            for key, value in secondary.properties.items():
                if key not in merged_props:
                    merged_props[key] = value
            return SupplyEntity(
                id=primary.id,
                type=primary.type,
                properties=merged_props,
            )
        elif merge_strategy == "secondary_wins":
            merged_props = secondary.properties.copy()
            for key, value in primary.properties.items():
                if key not in merged_props:
                    merged_props[key] = value
            return SupplyEntity(
                id=primary.id,  # Keep primary ID
                type=primary.type,
                properties=merged_props,
            )
        else:  # merge
            merged_props = {}
            for key, value in primary.properties.items():
                if isinstance(value, list) and key in secondary.properties:
                    merged_props[key] = value + secondary.properties[key]
                else:
                    merged_props[key] = value
            for key, value in secondary.properties.items():
                if key not in merged_props:
                    merged_props[key] = value
            return SupplyEntity(
                id=primary.id,
                type=primary.type,
                properties=merged_props,
            )


class SupplyGraphIngestionPipeline:
    """Ingestion pipeline for supply knowledge graph.

    Provides:
    - Entity normalization
    - Deduplication
    - Batch operations
    - Incremental updates
    """

    def __init__(
        self,
        db: SupplyGraphDatabase | None = None,
        normalizer: EntityNormalizer | None = None,
        deduplicator: EntityDeduplicator | None = None,
    ):
        self.db = db or SupplyGraphDatabase()
        self.normalizer = normalizer or EntityNormalizer()
        self.deduplicator = deduplicator or EntityDeduplicator(self.normalizer)
        self._change_log: list[ChangeRecord] = []

    def ingest_product(
        self,
        product_data: dict[str, Any],
        config: BatchConfig | None = None,
    ) -> IngestionResult:
        """Ingest a single product entity.

        Expected product_data format:
        {
            "id": "product_123",
            "name": "Product Name",
            "description": "...",
            "category": "category_id",
            "brand": "brand_id",
            "price": 99.99,
            "sku": "sku_123",
            "supplier": "supplier_id",
            "merchant": "merchant_id",
            "region": "region_id",
            "channel": "channel_id",
            "tags": ["tag1", "tag2"],
            ...
        }
        """
        config = config or BatchConfig()
        result = IngestionResult()

        try:
            # Normalize name if configured
            name = product_data.get("name", product_data.get("id", ""))
            if config.normalize_names:
                name = self.normalizer.normalize(name)

            # Create entity (exclude 'name' from spread to preserve normalized value)
            entity = SupplyEntity(
                id=product_data["id"],
                type=SupplyEntityType.PRODUCT,
                properties={
                    **{k: v for k, v in product_data.items() if k not in ("id", "name")},
                    "name": name,
                },
            )

            # Check for duplicates
            if config.skip_duplicates:
                existing = self.db.get_entity(entity.id)
                if existing:
                    result.skipped += 1
                    return result

            timestamp = self._get_timestamp()

            # Add timestamp to entity
            entity.created_at = timestamp
            entity.updated_at = timestamp

            # Create entity in graph
            try:
                self.db.create_entity(entity, validate=False)

                # Track change (this also increments created count)
                change = ChangeRecord(
                    operation=ChangeOperation.CREATE,
                    entity_type="product",
                    entity_id=entity.id,
                    timestamp=timestamp,
                    new_version=1,
                )
                result.add_change(change)
                self._change_log.append(change)

            except ValueError:
                # Entity exists, update if configured
                self.db.update_entity(entity, validate=False)

                # Track change (this also increments updated count)
                change = ChangeRecord(
                    operation=ChangeOperation.UPDATE,
                    entity_type="product",
                    entity_id=entity.id,
                    timestamp=timestamp,
                    new_version=entity.version,
                )
                result.add_change(change)
                self._change_log.append(change)

            # Create relations if configured
            if config.create_relations:
                self._create_product_relations(entity, product_data, result)

        except Exception as e:
            result.errors.append(f"Error ingesting product {product_data.get('id')}: {e}")

        return result

    def _create_product_relations(
        self,
        product: SupplyEntity,
        product_data: dict[str, Any],
        result: IngestionResult,
    ) -> None:
        """Create relations for a product entity."""
        relations_to_create = []

        # Category relation
        if "category" in product_data:
            relations_to_create.append(SupplyRelation(
                source_id=product.id,
                target_id=product_data["category"],
                relation_type=SupplyRelationType.BELONGS_TO,
            ))

        # Brand relation
        if "brand" in product_data:
            relations_to_create.append(SupplyRelation(
                source_id=product.id,
                target_id=product_data["brand"],
                relation_type=SupplyRelationType.HAS_BRAND,
            ))

        # SKU relation
        if "sku" in product_data:
            relations_to_create.append(SupplyRelation(
                source_id=product.id,
                target_id=product_data["sku"],
                relation_type=SupplyRelationType.HAS_SKU,
            ))

        # Supplier relation
        if "supplier" in product_data:
            relations_to_create.append(SupplyRelation(
                source_id=product_data["supplier"],
                target_id=product.id,
                relation_type=SupplyRelationType.SUPPLIES,
            ))

        # Merchant relation
        if "merchant" in product_data:
            relations_to_create.append(SupplyRelation(
                source_id=product_data["merchant"],
                target_id=product.id,
                relation_type=SupplyRelationType.SELLS,
            ))

        # Region relation
        if "region" in product_data:
            relations_to_create.append(SupplyRelation(
                source_id=product.id,
                target_id=product_data["region"],
                relation_type=SupplyRelationType.AVAILABLE_IN,
            ))

        # Channel relation
        if "channel" in product_data:
            relations_to_create.append(SupplyRelation(
                source_id=product.id,
                target_id=product_data["channel"],
                relation_type=SupplyRelationType.AVAILABLE_IN,
            ))

        # Create relations
        for rel in relations_to_create:
            try:
                self.db.create_relation(rel, validate=False)
            except (ValueError, KeyError):
                # Entity doesn't exist, skip
                pass

    def ingest_service(
        self,
        service_data: dict[str, Any],
        config: BatchConfig | None = None,
    ) -> IngestionResult:
        """Ingest a service entity.

        Expected service_data format:
        {
            "id": "service_123",
            "name": "Service Name",
            "description": "...",
            "category": "category_id",
            "procedure": "procedure_id",
            "merchant": "merchant_id",
            "region": "region_id",
            "intents": ["intent_id1", "intent_id2"],
            ...
        }
        """
        config = config or BatchConfig()
        result = IngestionResult()

        try:
            name = service_data.get("name", service_data.get("id", ""))
            if config.normalize_names:
                name = self.normalizer.normalize(name)

            entity = SupplyEntity(
                id=service_data["id"],
                type=SupplyEntityType.SERVICE,
                properties={
                    "name": name,
                    **{k: v for k, v in service_data.items() if k not in ("id", "name")},
                },
            )

            if config.skip_duplicates:
                existing = self.db.get_entity(entity.id)
                if existing:
                    result.skipped += 1
                    return result

            try:
                self.db.create_entity(entity, validate=False)
                result.created += 1
            except ValueError:
                self.db.update_entity(entity, validate=False)
                result.updated += 1

            if config.create_relations:
                self._create_service_relations(entity, service_data, result)

        except Exception as e:
            result.errors.append(f"Error ingesting service {service_data.get('id')}: {e}")

        return result

    def _create_service_relations(
        self,
        service: SupplyEntity,
        service_data: dict[str, Any],
        result: IngestionResult,
    ) -> None:
        """Create relations for a service entity."""
        # Category
        if "category" in service_data:
            try:
                self.db.create_relation(SupplyRelation(
                    source_id=service.id,
                    target_id=service_data["category"],
                    relation_type=SupplyRelationType.BELONGS_TO,
                ), validate=False)
            except (ValueError, KeyError):
                pass

        # Procedure
        if "procedure" in service_data:
            try:
                self.db.create_relation(SupplyRelation(
                    source_id=service_data["procedure"],
                    target_id=service.id,
                    relation_type=SupplyRelationType.PROVIDES_SERVICE,
                ), validate=False)
            except (ValueError, KeyError):
                pass

        # Merchant
        if "merchant" in service_data:
            try:
                self.db.create_relation(SupplyRelation(
                    source_id=service_data["merchant"],
                    target_id=service.id,
                    relation_type=SupplyRelationType.OFFERS,
                ), validate=False)
            except (ValueError, KeyError):
                pass

        # Intents
        if "intents" in service_data:
            for intent_id in service_data["intents"]:
                try:
                    self.db.create_relation(SupplyRelation(
                        source_id=service.id,
                        target_id=intent_id,
                        relation_type=SupplyRelationType.HAS_INTENT,
                    ), validate=False)
                except (ValueError, KeyError):
                    pass

    def ingest_procedure(
        self,
        procedure_data: dict[str, Any],
        config: BatchConfig | None = None,
    ) -> IngestionResult:
        """Ingest a procedure entity."""
        config = config or BatchConfig()
        result = IngestionResult()

        try:
            name = procedure_data.get("name", procedure_data.get("id", ""))
            if config.normalize_names:
                name = self.normalizer.normalize(name)

            entity = SupplyEntity(
                id=procedure_data["id"],
                type=SupplyEntityType.PROCEDURE,
                properties={
                    "name": name,
                    **{k: v for k, v in procedure_data.items() if k not in ("id", "name")},
                },
            )

            if config.skip_duplicates:
                existing = self.db.get_entity(entity.id)
                if existing:
                    result.skipped += 1
                    return result

            try:
                self.db.create_entity(entity, validate=False)
                result.created += 1
            except ValueError:
                self.db.update_entity(entity, validate=False)
                result.updated += 1

        except Exception as e:
            result.errors.append(f"Error ingesting procedure {procedure_data.get('id')}: {e}")

        return result

    def ingest_intent(
        self,
        intent_data: dict[str, Any],
        config: BatchConfig | None = None,
    ) -> IngestionResult:
        """Ingest an intent entity."""
        config = config or BatchConfig()
        result = IngestionResult()

        try:
            name = intent_data.get("name", intent_data.get("id", ""))
            if config.normalize_names:
                name = self.normalizer.normalize(name)

            entity = SupplyEntity(
                id=intent_data["id"],
                type=SupplyEntityType.INTENT,
                properties={
                    "name": name,
                    **{k: v for k, v in intent_data.items() if k not in ("id", "name")},
                },
            )

            if config.skip_duplicates:
                existing = self.db.get_entity(entity.id)
                if existing:
                    result.skipped += 1
                    return result

            try:
                self.db.create_entity(entity, validate=False)
                result.created += 1
            except ValueError:
                self.db.update_entity(entity, validate=False)
                result.updated += 1

            # Create slot relations
            if config.create_relations and "slots" in intent_data:
                for slot_id in intent_data["slots"]:
                    try:
                        self.db.create_relation(SupplyRelation(
                            source_id=entity.id,
                            target_id=slot_id,
                            relation_type=SupplyRelationType.HAS_SLOT,
                        ), validate=False)
                    except (ValueError, KeyError):
                        pass

        except Exception as e:
            result.errors.append(f"Error ingesting intent {intent_data.get('id')}: {e}")

        return result

    def ingest_slot(
        self,
        slot_data: dict[str, Any],
        config: BatchConfig | None = None,
    ) -> IngestionResult:
        """Ingest a slot entity."""
        config = config or BatchConfig()
        result = IngestionResult()

        try:
            name = slot_data.get("name", slot_data.get("id", ""))
            if config.normalize_names:
                name = self.normalizer.normalize(name)

            entity = SupplyEntity(
                id=slot_data["id"],
                type=SupplyEntityType.SLOT,
                properties={
                    "name": name,
                    "slot_type": slot_data.get("slot_type", "string"),
                    "required": slot_data.get("required", False),
                    **{k: v for k, v in slot_data.items() if k not in ("id", "name", "slot_type", "required")},
                },
            )

            if config.skip_duplicates:
                existing = self.db.get_entity(entity.id)
                if existing:
                    result.skipped += 1
                    return result

            try:
                self.db.create_entity(entity, validate=False)
                result.created += 1
            except ValueError:
                self.db.update_entity(entity, validate=False)
                result.updated += 1

        except Exception as e:
            result.errors.append(f"Error ingesting slot {slot_data.get('id')}: {e}")

        return result

    def _ingest_generic_entity(self, entity_type: SupplyEntityType):
        """Create a generic entity ingestor for the given type."""
        def _ingestor(
            entity_data: dict[str, Any],
            config: BatchConfig | None = None,
        ) -> IngestionResult:
            config = config or BatchConfig()
            result = IngestionResult()

            try:
                name = entity_data.get("name", entity_data.get("id", ""))
                if config.normalize_names:
                    name = self.normalizer.normalize(name)

                entity = SupplyEntity(
                    id=entity_data["id"],
                    type=entity_type,
                    properties={
                        "name": name,
                        **{k: v for k, v in entity_data.items() if k not in ("id", "name")},
                    },
                )

                if config.skip_duplicates:
                    existing = self.db.get_entity(entity.id)
                    if existing:
                        result.skipped += 1
                        return result

                try:
                    self.db.create_entity(entity, validate=False)
                    result.created += 1
                except ValueError:
                    self.db.update_entity(entity, validate=False)
                    result.updated += 1

            except Exception as e:
                result.errors.append(f"Error ingesting {entity_type.value} {entity_data.get('id')}: {e}")

            return result

        return _ingestor

    def ingest_batch(
        self,
        entities: list[dict[str, Any]],
        entity_type: str,
        config: BatchConfig | None = None,
    ) -> IngestionResult:
        """Ingest a batch of entities.

        Args:
            entities: List of entity data dicts
            entity_type: Type of entities - "product", "service", "procedure", "intent", "slot"
            config: Batch configuration
        """
        config = config or BatchConfig()
        result = IngestionResult()

        if config.dry_run:
            # Just count what would be created/updated
            for entity_data in entities:
                entity_id = entity_data.get("id", "")
                if not entity_id:
                    result.errors.append("Entity missing ID")
                    continue

                existing = self.db.get_entity(entity_id)
                if existing:
                    result.skipped += 1
                else:
                    result.created += 1
            return result

        # Map entity types to ingestion methods
        ingestors: dict[str, Callable[[dict, BatchConfig], IngestionResult]] = {
            "product": self.ingest_product,
            "service": self.ingest_service,
            "procedure": self.ingest_procedure,
            "intent": self.ingest_intent,
            "slot": self.ingest_slot,
            # Generic entity types
            "category": self._ingest_generic_entity(SupplyEntityType.CATEGORY),
            "brand": self._ingest_generic_entity(SupplyEntityType.BRAND),
            "supplier": self._ingest_generic_entity(SupplyEntityType.SUPPLIER),
            "merchant": self._ingest_generic_entity(SupplyEntityType.MERCHANT),
            "region": self._ingest_generic_entity(SupplyEntityType.REGION),
            "channel": self._ingest_generic_entity(SupplyEntityType.CHANNEL),
        }

        if entity_type not in ingestors:
            result.errors.append(f"Unknown entity type: {entity_type}")
            return result

        ingestor = ingestors[entity_type]

        # Process in batches
        for i in range(0, len(entities), config.batch_size):
            batch = entities[i:i + config.batch_size]
            for entity_data in batch:
                batch_result = ingestor(entity_data, config)
                result.created += batch_result.created
                result.updated += batch_result.updated
                result.skipped += batch_result.skipped
                result.errors.extend(batch_result.errors)

        return result

    def ingest_full_schema(
        self,
        data: dict[str, list[dict[str, Any]]],
        config: BatchConfig | None = None,
    ) -> IngestionResult:
        """Ingest a full schema with multiple entity types.

        Expected format:
        {
            "products": [...],
            "services": [...],
            "procedures": [...],
            "intents": [...],
            "slots": [...],
            "categories": [...],
            "brands": [...],
            "merchants": [...],
            "suppliers": [...],
            "regions": [...],
            "channels": [...],
        }

        Order matters - entities should be created before their relations.
        """
        config = config or BatchConfig()
        result = IngestionResult()

        # Define ingestion order (dependencies first)
        # Categories, brands, suppliers, merchants, regions, channels -> products, services
        # Procedures -> services
        # Intents -> slots
        order = [
            ("categories", "category"),
            ("brands", "brand"),
            ("suppliers", "supplier"),
            ("merchants", "merchant"),
            ("regions", "region"),
            ("channels", "channel"),
            ("procedures", "procedure"),
            ("slots", "slot"),
            ("intents", "intent"),
            ("products", "product"),
            ("services", "service"),
        ]

        for entity_key, entity_type in order:
            if entity_key in data:
                batch_result = self.ingest_batch(data[entity_key], entity_type, config)
                result.created += batch_result.created
                result.updated += batch_result.updated
                result.skipped += batch_result.skipped
                result.errors.extend(batch_result.errors)

        return result

    # Incremental Update Methods

    def _get_timestamp(self) -> str:
        """Get current ISO timestamp."""
        return datetime.now(timezone.utc).isoformat()

    def incremental_update_entity(
        self,
        entity_data: dict[str, Any],
        entity_type: SupplyEntityType,
        partial: bool = True,
    ) -> IngestionResult:
        """Incrementally update an entity.

        Args:
            entity_data: Entity data to update
            entity_type: Type of entity
            partial: If True, only update provided fields; if False, replace entire entity

        Returns:
            IngestionResult with change record
        """
        result = IngestionResult()
        entity_id = entity_data.get("id")
        if not entity_id:
            result.errors.append("Entity ID required for incremental update")
            return result

        timestamp = self._get_timestamp()
        existing = self.db.get_entity(entity_id)

        if existing is None:
            # Create new entity with version tracking
            name = entity_data.get("name", entity_id)
            if BatchConfig().normalize_names:
                name = self.normalizer.normalize(name)

            new_entity = SupplyEntity(
                id=entity_id,
                type=entity_type,
                properties={
                    "name": name,
                    **{k: v for k, v in entity_data.items() if k not in ("id", "name")},
                },
                version=1,
                created_at=timestamp,
                updated_at=timestamp,
            )

            try:
                self.db.create_entity(new_entity, validate=False)
                change = ChangeRecord(
                    operation=ChangeOperation.CREATE,
                    entity_type=entity_type.value,
                    entity_id=entity_id,
                    timestamp=timestamp,
                    new_version=1,
                )
                result.add_change(change)
            except ValueError as e:
                result.errors.append(f"Error creating entity: {e}")

            return result

        # Update existing entity
        old_version = existing.version
        new_version = old_version + 1

        if partial:
            # Merge properties - copy existing first
            new_properties = existing.properties.copy()
            # If entity_data has a "properties" key, merge that
            if "properties" in entity_data:
                new_properties.update(entity_data["properties"])
            # Also update top-level fields that are in entity_data (except id)
            for key, value in entity_data.items():
                if key != "id":
                    new_properties[key] = value
        else:
            # Replace entire properties
            new_properties = entity_data.get("properties", entity_data.copy())
            new_properties.pop("id", None)  # Remove id if present in properties

        # Update entity
        updated_entity = SupplyEntity(
            id=entity_id,
            type=entity_type,
            properties=new_properties,
            version=new_version,
            created_at=existing.created_at or timestamp,
            updated_at=timestamp,
        )

        try:
            self.db.update_entity(updated_entity, validate=False)

            # Record the change
            change = ChangeRecord(
                operation=ChangeOperation.UPDATE,
                entity_type=entity_type.value,
                entity_id=entity_id,
                timestamp=timestamp,
                old_version=old_version,
                new_version=new_version,
                details={"partial": partial},
            )
            result.add_change(change)

        except Exception as e:
            result.errors.append(f"Error updating entity {entity_id}: {e}")

        return result

    def incremental_update_relations(
        self,
        relations: list[dict[str, Any]],
    ) -> IngestionResult:
        """Incrementally update relations.

        Handles creating new relations and updating existing ones.
        """
        result = IngestionResult()
        timestamp = self._get_timestamp()

        for rel_data in relations:
            source_id = rel_data.get("source_id")
            target_id = rel_data.get("target_id")
            rel_type_str = rel_data.get("relation_type")

            if not all([source_id, target_id, rel_type_str]):
                result.errors.append("Relation missing required fields")
                continue

            try:
                rel_type = SupplyRelationType(rel_type_str)
            except ValueError:
                result.errors.append(f"Invalid relation type: {rel_type_str}")
                continue

            # Check if relation exists
            existing = None
            for rel in self.db._relations:
                if (rel.source_id == source_id and
                    rel.target_id == target_id and
                    rel.relation_type == rel_type):
                    existing = rel
                    break

            if existing:
                # Update existing relation
                old_version = existing.version
                new_version = old_version + 1

                # Update properties
                new_props = existing.properties.copy()
                new_props.update(rel_data.get("properties", {}))

                updated_rel = SupplyRelation(
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=rel_type,
                    properties=new_props,
                    version=new_version,
                    created_at=existing.created_at or timestamp,
                    updated_at=timestamp,
                )

                # Delete old, add new (simplest approach for in-memory)
                self.db.delete_relation(source_id, target_id, rel_type)
                self.db.create_relation(updated_rel, validate=False)

                change = ChangeRecord(
                    operation=ChangeOperation.UPDATE,
                    entity_type="relation",
                    entity_id=f"{source_id}->{target_id}",
                    timestamp=timestamp,
                    old_version=old_version,
                    new_version=new_version,
                )
                result.add_change(change)
            else:
                # Create new relation
                new_rel = SupplyRelation(
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=rel_type,
                    properties=rel_data.get("properties", {}),
                    version=1,
                    created_at=timestamp,
                    updated_at=timestamp,
                )

                try:
                    self.db.create_relation(new_rel, validate=False)
                    change = ChangeRecord(
                        operation=ChangeOperation.CREATE,
                        entity_type="relation",
                        entity_id=f"{source_id}->{target_id}",
                        timestamp=timestamp,
                        new_version=1,
                    )
                    result.add_change(change)
                except (ValueError, KeyError) as e:
                    result.errors.append(f"Error creating relation: {e}")

        return result

    def delete_entity_cascade(
        self,
        entity_id: str,
    ) -> IngestionResult:
        """Delete an entity and all its relations.

        Returns:
            IngestionResult with delete count and change records
        """
        result = IngestionResult()
        timestamp = self._get_timestamp()

        entity = self.db.get_entity(entity_id)
        if entity is None:
            result.errors.append(f"Entity {entity_id} not found")
            return result

        # Delete all relations involving this entity first
        relation_count = 0
        for rel in list(self.db._relations):
            if rel.source_id == entity_id or rel.target_id == entity_id:
                relation_count += 1
                change = ChangeRecord(
                    operation=ChangeOperation.DELETE,
                    entity_type="relation",
                    entity_id=f"{rel.source_id}->{rel.target_id}",
                    timestamp=timestamp,
                )
                result.add_change(change)

        # Delete the entity
        deleted = self.db.delete_entity(entity_id)
        if deleted:
            change = ChangeRecord(
                operation=ChangeOperation.DELETE,
                entity_type=entity.type.value,
                entity_id=entity_id,
                timestamp=timestamp,
                old_version=entity.version,
            )
            result.add_change(change)

        return result

    def get_changes_since(
        self,
        since_timestamp: str,
    ) -> list[ChangeRecord]:
        """Get all changes since a given timestamp.

        This requires the pipeline to track changes during ingestion.
        """
        return [
            c for c in self._change_log
            if c.timestamp > since_timestamp
        ]

    def sync_incremental(
        self,
        data: dict[str, Any],
        since_timestamp: str | None = None,
    ) -> IngestionResult:
        """Synchronize the graph with incremental updates.

        This method handles:
        - New entities (CREATE)
        - Updated entities (UPDATE)
        - Deleted entities (DELETE)

        Args:
            data: Dictionary with entity updates, format:
                {
                    "products": {"upsert": [...], "delete": [...]},
                    "services": {"upsert": [...], "delete": [...]},
                    ...
                }
            since_timestamp: Only process changes since this timestamp

        Returns:
            IngestionResult with all changes
        """
        result = IngestionResult()
        timestamp = self._get_timestamp()

        # Map entity type strings to enum (supports both singular and plural)
        type_map = {
            "product": SupplyEntityType.PRODUCT,
            "products": SupplyEntityType.PRODUCT,
            "service": SupplyEntityType.SERVICE,
            "services": SupplyEntityType.SERVICE,
            "procedure": SupplyEntityType.PROCEDURE,
            "procedures": SupplyEntityType.PROCEDURE,
            "intent": SupplyEntityType.INTENT,
            "intents": SupplyEntityType.INTENT,
            "slot": SupplyEntityType.SLOT,
            "slots": SupplyEntityType.SLOT,
            "category": SupplyEntityType.CATEGORY,
            "categories": SupplyEntityType.CATEGORY,
            "brand": SupplyEntityType.BRAND,
            "brands": SupplyEntityType.BRAND,
            "supplier": SupplyEntityType.SUPPLIER,
            "suppliers": SupplyEntityType.SUPPLIER,
            "merchant": SupplyEntityType.MERCHANT,
            "merchants": SupplyEntityType.MERCHANT,
            "region": SupplyEntityType.REGION,
            "regions": SupplyEntityType.REGION,
            "channel": SupplyEntityType.CHANNEL,
            "channels": SupplyEntityType.CHANNEL,
        }

        for entity_type_str, entity_updates in data.items():
            if not isinstance(entity_updates, dict):
                result.errors.append(f"Invalid format for {entity_type_str}")
                continue

            entity_type = type_map.get(entity_type_str)
            if entity_type is None:
                result.errors.append(f"Unknown entity type: {entity_type_str}")
                continue

            # Handle upserts
            upserts = entity_updates.get("upsert", [])
            for entity_data in upserts:
                if since_timestamp:
                    # Check if entity was updated after since_timestamp
                    existing = self.db.get_entity(entity_data.get("id"))
                    if existing and existing.updated_at and existing.updated_at <= since_timestamp:
                        continue  # Skip unchanged entities

                update_result = self.incremental_update_entity(
                    entity_data,
                    entity_type,
                    partial=True,
                )
                result.created += update_result.created
                result.updated += update_result.updated
                result.errors.extend(update_result.errors)
                result.changes.extend(update_result.changes)

            # Handle deletes
            delete_ids = entity_updates.get("delete", [])
            for entity_id in delete_ids:
                delete_result = self.delete_entity_cascade(entity_id)
                result.deleted += delete_result.deleted
                result.errors.extend(delete_result.errors)
                result.changes.extend(delete_result.changes)

        # Handle relation updates
        if "relations" in data:
            rel_result = self.incremental_update_relations(data["relations"])
            result.created += rel_result.created
            result.updated += rel_result.updated
            result.errors.extend(rel_result.errors)
            result.changes.extend(rel_result.changes)

        return result

    def get_change_log(self) -> list[ChangeRecord]:
        """Get the change log from last ingestion."""
        return self._change_log.copy()

    def get_change_log_dicts(self) -> list[dict[str, Any]]:
        """Get the change log as dictionaries."""
        return [c.to_dict() for c in self._change_log.copy()]

    def clear_change_log(self) -> None:
        """Clear the change log."""
        self._change_log.clear()


# Global instance
_global_pipeline: SupplyGraphIngestionPipeline | None = None


def get_ingestion_pipeline() -> SupplyGraphIngestionPipeline:
    """Get the global ingestion pipeline instance."""
    global _global_pipeline
    if _global_pipeline is None:
        _global_pipeline = SupplyGraphIngestionPipeline()
    return _global_pipeline


def set_ingestion_pipeline(pipeline: SupplyGraphIngestionPipeline) -> None:
    """Set the global ingestion pipeline instance."""
    global _global_pipeline
    _global_pipeline = pipeline
