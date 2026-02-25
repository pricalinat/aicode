"""Supply Graph Database with validation, confidence scoring, and query APIs.

This module provides a specialized graph database implementation for the supply
knowledge graph with schema validation, relation confidence scoring, and
advanced traversal/query capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable
import re

from .supply_graph_models import (
    SupplyEntity,
    SupplyEntityType,
    SupplyGraph,
    SupplyRelation,
    SupplyRelationType,
)


class ValidationError(Exception):
    """Raised when entity or relation fails validation."""
    pass


class CycleDetectedError(Exception):
    """Raised when a cycle is detected in the graph."""
    pass


@dataclass
class DuplicateGroup:
    """A group of duplicate entities."""
    canonical_id: str
    entities: list[SupplyEntity]
    similarity_scores: list[float]

    @property
    def count(self) -> int:
        return len(self.entities)


@dataclass
class MergeResult:
    """Result of a merge operation."""
    merged_entity: SupplyEntity
    source_ids: list[str]
    relations_preserved: int
    relations_removed: int


@dataclass
class ValidationRule:
    """A validation rule for entities or relations."""
    name: str
    description: str
    validator: Callable[[SupplyEntity | SupplyRelation], bool]
    error_message: str


@dataclass
class GraphPath:
    """A path through the graph."""
    entities: list[SupplyEntity] = field(default_factory=list)
    relations: list[SupplyRelation] = field(default_factory=list)

    @property
    def length(self) -> int:
        return len(self.relations)

    @property
    def total_weight(self) -> float:
        return sum(r.weight for r in self.relations)


class ChangeType(Enum):
    """Types of changes that can be tracked."""
    ENTITY_CREATED = "entity_created"
    ENTITY_UPDATED = "entity_updated"
    ENTITY_DELETED = "entity_deleted"
    RELATION_CREATED = "relation_created"
    RELATION_DELETED = "relation_deleted"


@dataclass
class ChangeEvent:
    """A single change event in the graph."""
    change_type: ChangeType
    entity_id: str | None = None
    relation: SupplyRelation | None = None
    timestamp: str | None = None
    user: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timestamp is None:
            from datetime import datetime, timezone
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class ChangeHistory:
    """Tracks all changes to the graph."""
    events: list[ChangeEvent] = field(default_factory=list)
    version: int = 0

    def add_event(self, event: ChangeEvent) -> None:
        """Add a change event to history."""
        self.events.append(event)
        self.version += 1

    def get_entity_history(self, entity_id: str) -> list[ChangeEvent]:
        """Get all changes for a specific entity."""
        return [
            e for e in self.events
            if e.entity_id == entity_id
        ]

    def get_recent_changes(self, limit: int = 10) -> list[ChangeEvent]:
        """Get the most recent changes."""
        return self.events[-limit:]


@dataclass
class Transaction:
    """A batch of operations to be applied atomically."""
    operations: list[tuple[str, Any]] = field(default_factory=list)
    _committed: bool = False

    def add_operation(self, operation_type: str, data: Any) -> None:
        """Add an operation to the transaction."""
        self.operations.append((operation_type, data))

    @property
    def is_committed(self) -> bool:
        return self._committed


class SupplyGraphDatabase:
    """Graph database for supply knowledge graph.

    Provides validation, confidence scoring, and advanced query APIs
    specific to e-commerce and mini-program supply domain.
    """

    def __init__(self) -> None:
        self._entities: dict[str, SupplyEntity] = {}
        self._relations: list[SupplyRelation] = []
        self._entity_index: dict[SupplyEntityType, list[str]] = {}
        self._entity_validation_rules: list[ValidationRule] = []
        self._relation_validation_rules: list[ValidationRule] = []
        self._change_history: ChangeHistory = ChangeHistory()
        self._current_transaction: Transaction | None = None
        self._initialize_validation_rules()

    def _initialize_validation_rules(self) -> None:
        """Initialize default validation rules."""

        # Entity validation rules
        self._entity_validation_rules.append(ValidationRule(
            name="entity_has_id",
            description="Entity must have a non-empty ID",
            validator=lambda e: bool(e.id and e.id.strip()),
            error_message="Entity ID cannot be empty",
        ))

        self._entity_validation_rules.append(ValidationRule(
            name="entity_has_valid_type",
            description="Entity must have a valid type",
            validator=lambda e: isinstance(e.type, SupplyEntityType),
            error_message="Entity must have a valid SupplyEntityType",
        ))

        self._entity_validation_rules.append(ValidationRule(
            name="product_has_name",
            description="Product entities must have a name",
            validator=lambda e: (
                e.type != SupplyEntityType.PRODUCT or
                "name" in e.properties or bool(e.id)
            ),
            error_message="Product must have a name in properties",
        ))

        # Relation validation rules
        self._relation_validation_rules.append(ValidationRule(
            name="relation_has_valid_entities",
            description="Relation must reference existing entities",
            validator=lambda r: (
                r.source_id in self._entities and
                r.target_id in self._entities
            ),
            error_message="Relation references non-existent entities",
        ))

        self._relation_validation_rules.append(ValidationRule(
            name="relation_has_valid_type",
            description="Relation must have a valid type",
            validator=lambda r: isinstance(r.relation_type, SupplyRelationType),
            error_message="Relation must have a valid SupplyRelationType",
        ))

        self._relation_validation_rules.append(ValidationRule(
            name="weight_in_valid_range",
            description="Relation weight must be between 0 and 1",
            validator=lambda r: 0.0 <= r.weight <= 1.0,
            error_message="Relation weight must be between 0 and 1",
        ))

    def _reindex_entity(self, entity: SupplyEntity) -> None:
        """Update the entity type index."""
        if entity.type not in self._entity_index:
            self._entity_index[entity.type] = []
        if entity.id not in self._entity_index[entity.type]:
            self._entity_index[entity.type].append(entity.id)

    def _validate_entity(self, entity: SupplyEntity) -> list[str]:
        """Validate an entity against all rules.

        Returns list of error messages (empty if valid).
        """
        errors = []
        for rule in self._entity_validation_rules:
            try:
                if not rule.validator(entity):
                    errors.append(f"{rule.name}: {rule.error_message}")
            except Exception as e:
                errors.append(f"{rule.name}: Validation error - {e}")
        return errors

    def _validate_relation(self, relation: SupplyRelation) -> list[str]:
        """Validate a relation against all rules.

        Returns list of error messages (empty if valid).
        """
        errors = []
        for rule in self._relation_validation_rules:
            try:
                if not rule.validator(relation):
                    errors.append(f"{rule.name}: {rule.error_message}")
            except Exception as e:
                errors.append(f"{rule.name}: Validation error - {e}")
        return errors

    # CRUD Operations

    def create_entity(self, entity: SupplyEntity, validate: bool = True) -> SupplyEntity:
        """Create a new entity in the graph."""
        try:
            if validate:
                errors = self._validate_entity(entity)
                if errors:
                    raise ValidationError(f"Entity validation failed: {'; '.join(errors)}")

            if entity.id in self._entities:
                raise ValueError(f"Entity with id {entity.id} already exists")

            self._entities[entity.id] = entity
            self._reindex_entity(entity)

            # Record change
            self._record_entity_create(entity)

            # Track in transaction if one is active
            if self._current_transaction:
                self._current_transaction.add_operation("create_entity", entity)

            return entity
        except (ValidationError, ValueError):
            # Auto-rollback on error if in transaction
            if self._current_transaction is not None:
                try:
                    self.rollback()
                except RuntimeError:
                    pass  # Transaction already ended
            raise

    def get_entity(self, entity_id: str) -> SupplyEntity | None:
        """Get an entity by ID."""
        return self._entities.get(entity_id)

    def update_entity(self, entity: SupplyEntity, validate: bool = True) -> SupplyEntity:
        """Update an existing entity."""
        try:
            if validate:
                errors = self._validate_entity(entity)
                if errors:
                    raise ValidationError(f"Entity validation failed: {'; '.join(errors)}")

            if entity.id not in self._entities:
                raise ValueError(f"Entity with id {entity.id} not found")

            previous = self._entities[entity.id]

            # Auto-increment version if not explicitly set higher
            # Only increment if the entity version is at or below the stored version
            # This handles the case where the entity is the same object as stored
            if entity.version <= previous.version:
                entity.version = previous.version + 1
            # If entity.version > previous.version, it was already incremented (e.g., by upsert)
            # Don't increment again

            self._entities[entity.id] = entity

            # Record change
            self._record_entity_update(entity, previous)

            # Track in transaction if one is active
            if self._current_transaction:
                self._current_transaction.add_operation("update_entity", {
                    "entity_id": entity.id,
                    "previous_entity": previous,
                })

            return entity
        except (ValidationError, ValueError):
            # Auto-rollback on error if in transaction
            if self._current_transaction is not None:
                try:
                    self.rollback()
                except RuntimeError:
                    pass  # Transaction already ended
            raise

    def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity and all its relations."""
        try:
            if entity_id not in self._entities:
                return False

            entity = self._entities[entity_id]

            # Collect relations before deletion for potential rollback
            affected_relations = [
                r for r in self._relations
                if r.source_id == entity_id or r.target_id == entity_id
            ]

            # Delete all relations involving this entity
            self._relations = [
                r for r in self._relations
                if r.source_id != entity_id and r.target_id != entity_id
            ]

            # Remove from index
            if entity.type in self._entity_index:
                self._entity_index[entity.type] = [
                    eid for eid in self._entity_index[entity.type]
                    if eid != entity_id
                ]

            del self._entities[entity_id]

            # Record change
            self._record_entity_delete(entity)

            # Track in transaction if one is active
            if self._current_transaction:
                self._current_transaction.add_operation("delete_entity", {
                    "entity": entity,
                    "relations": affected_relations,
                })

            return True
        except (ValidationError, ValueError):
            # Auto-rollback on error if in transaction
            if self._current_transaction is not None:
                try:
                    self.rollback()
                except RuntimeError:
                    pass  # Transaction already ended
            raise

    def create_relation(
        self,
        relation: SupplyRelation,
        validate: bool = True,
    ) -> SupplyRelation:
        """Create a new relation in the graph."""
        try:
            if validate:
                errors = self._validate_relation(relation)
                if errors:
                    raise ValidationError(f"Relation validation failed: {'; '.join(errors)}")

            # Check entities exist
            if relation.source_id not in self._entities:
                raise ValueError(f"Source entity {relation.source_id} not found")
            if relation.target_id not in self._entities:
                raise ValueError(f"Target entity {relation.target_id} not found")

            self._relations.append(relation)

            # Record change
            self._record_relation_create(relation)

            # Track in transaction if one is active
            if self._current_transaction:
                self._current_transaction.add_operation("create_relation", relation)

            return relation
        except (ValidationError, ValueError):
            # Auto-rollback on error if in transaction
            if self._current_transaction is not None:
                try:
                    self.rollback()
                except RuntimeError:
                    pass  # Transaction already ended
            raise

    def delete_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: SupplyRelationType,
    ) -> bool:
        """Delete a relation."""
        # Find the relation to delete (for recording)
        deleted_relation = None
        for r in self._relations:
            if (r.source_id == source_id and
                r.target_id == target_id and
                r.relation_type == relation_type):
                deleted_relation = r
                break

        original_count = len(self._relations)
        self._relations = [
            r for r in self._relations
            if not (r.source_id == source_id and
                    r.target_id == target_id and
                    r.relation_type == relation_type)
        ]

        deleted = len(self._relations) < original_count

        # Record change if actually deleted
        if deleted and deleted_relation:
            self._record_relation_delete(deleted_relation)

            # Track in transaction if one is active
            if self._current_transaction:
                self._current_transaction.add_operation("delete_relation", deleted_relation)

        return deleted

    # Query Operations

    def query_by_type(self, entity_type: SupplyEntityType) -> list[SupplyEntity]:
        """Get all entities of a specific type."""
        if entity_type not in self._entity_index:
            return []
        return [
            self._entities[eid]
            for eid in self._entity_index[entity_type]
            if eid in self._entities
        ]

    def query_by_property(
        self,
        entity_type: SupplyEntityType | None,
        property_key: str,
        property_value: Any,
    ) -> list[SupplyEntity]:
        """Query entities by property value."""
        results = []
        for entity in self._entities.values():
            if entity_type and entity.type != entity_type:
                continue
            if entity.properties.get(property_key) == property_value:
                results.append(entity)
        return results

    def search(
        self,
        text: str,
        entity_types: list[SupplyEntityType] | None = None,
    ) -> list[SupplyEntity]:
        """Search entities by text in name or description."""
        text_lower = text.lower()
        results = []

        for entity in self._entities.values():
            if entity_types and entity.type not in entity_types:
                continue

            # Search in name
            if text_lower in entity.name.lower():
                results.append(entity)
                continue

            # Search in description
            if entity.description and text_lower in entity.description.lower():
                results.append(entity)

        return results

    # Multi-Criteria Query API

    def query_by_properties(
        self,
        entity_type: SupplyEntityType | None,
        properties: dict[str, Any],
        match_all: bool = True,
    ) -> list[SupplyEntity]:
        """Query entities by multiple property values.

        Args:
            entity_type: Optional entity type to filter by
            properties: Dictionary of property key-value pairs to match
            match_all: If True, all properties must match (AND).
                       If False, at least one must match (OR).

        Returns:
            List of matching entities
        """
        results = []
        for entity in self._entities.values():
            if entity_type and entity.type != entity_type:
                continue

            if match_all:
                # AND: all properties must match
                if all(
                    entity.properties.get(k) == v
                    for k, v in properties.items()
                ):
                    results.append(entity)
            else:
                # OR: at least one property must match
                if any(
                    entity.properties.get(k) == v
                    for k, v in properties.items()
                ):
                    results.append(entity)
        return results

    def query_by_property_range(
        self,
        entity_type: SupplyEntityType | None,
        property_key: str,
        min_value: float | None = None,
        max_value: float | None = None,
    ) -> list[SupplyEntity]:
        """Query entities by numeric property range.

        Args:
            entity_type: Optional entity type to filter by
            property_key: The property key to check
            min_value: Minimum value (inclusive), None for no minimum
            max_value: Maximum value (inclusive), None for no maximum

        Returns:
            List of entities with property in range
        """
        results = []
        for entity in self._entities.values():
            if entity_type and entity.type != entity_type:
                continue

            value = entity.properties.get(property_key)
            if value is None:
                continue

            # Try to compare as numbers
            try:
                num_value = float(value)
                if min_value is not None and num_value < min_value:
                    continue
                if max_value is not None and num_value > max_value:
                    continue
                results.append(entity)
            except (TypeError, ValueError):
                # Not a numeric value, skip
                continue
        return results

    def query_with_relations(
        self,
        entity_type: SupplyEntityType | None,
        required_relations: list[tuple[str, SupplyRelationType, str]] | None = None,
        min_relations: int = 0,
    ) -> list[SupplyEntity]:
        """Query entities that have specific relations.

        Args:
            entity_type: Optional entity type to filter by
            required_relations: List of (source_id, relation_type, target_id) tuples.
                              Can use None for wildcard matching.
            min_relations: Minimum number of relations the entity must have

        Returns:
            List of entities matching the relation criteria
        """
        results = []
        for entity in self._entities.values():
            if entity_type and entity.type != entity_type:
                continue

            # Check minimum relations
            outgoing = self.get_outgoing_relations(entity.id)
            incoming = self.get_incoming_relations(entity.id)
            total_relations = len(outgoing) + len(incoming)

            if total_relations < min_relations:
                continue

            # Check required relations
            if required_relations:
                matched = False
                for src, rel_type, tgt in required_relations:
                    for relation in self._relations:
                        src_match = src is None or relation.source_id == src
                        tgt_match = tgt is None or relation.target_id == tgt
                        rel_match = rel_type is None or relation.relation_type == rel_type
                        if src_match and tgt_match and rel_match:
                            matched = True
                            break
                    if not matched:
                        break

                if not matched:
                    continue

            results.append(entity)
        return results

    def advanced_search(
        self,
        text: str,
        entity_types: list[SupplyEntityType] | None = None,
        property_filters: dict[str, Any] | None = None,
        min_confidence: float | None = None,
        require_relations: list[SupplyRelationType] | None = None,
    ) -> list[SupplyEntity]:
        """Advanced search with multiple criteria.

        Args:
            text: Text to search in name and description
            entity_types: List of entity types to include
            property_filters: Additional property filters to apply
            min_confidence: Minimum confidence score for related relations
            require_relations: Entity must have at least one of these relation types

        Returns:
            List of matching entities
        """
        text_lower = text.lower()
        results = []

        for entity in self._entities.values():
            # Filter by entity type
            if entity_types and entity.type not in entity_types:
                continue

            # Text search
            name_match = text_lower in entity.name.lower()
            desc_match = entity.description and text_lower in entity.description.lower()

            if not name_match and not desc_match:
                # Also check properties for text
                prop_match = False
                for v in entity.properties.values():
                    if isinstance(v, str) and text_lower in v.lower():
                        prop_match = True
                        break
                if not prop_match:
                    continue

            # Property filters
            if property_filters:
                if not all(
                    entity.properties.get(k) == v
                    for k, v in property_filters.items()
                ):
                    continue

            # Relation requirements
            if require_relations:
                outgoing = self.get_outgoing_relations(entity.id)
                incoming = self.get_incoming_relations(entity.id)
                all_relations = outgoing + incoming

                has_required = any(
                    r.relation_type in require_relations
                    for r in all_relations
                )
                if not has_required:
                    continue

                # Check confidence if specified
                if min_confidence is not None:
                    confidences = [
                        self.calculate_relation_confidence(r)
                        for r in all_relations
                        if r.relation_type in require_relations
                    ]
                    if confidences and max(confidences) < min_confidence:
                        continue

            results.append(entity)
        return results

    def count_by_type(self) -> dict[SupplyEntityType, int]:
        """Get count of entities by type.

        Returns:
            Dictionary mapping entity type to count
        """
        counts: dict[SupplyEntityType, int] = {}
        for entity in self._entities.values():
            counts[entity.type] = counts.get(entity.type, 0) + 1
        return counts

    def get_entities_with_most_relations(
        self,
        entity_type: SupplyEntityType | None = None,
        limit: int = 10,
    ) -> list[tuple[SupplyEntity, int]]:
        """Get entities with the most relations.

        Args:
            entity_type: Optional filter by entity type
            limit: Maximum number of entities to return

        Returns:
            List of (entity, degree) tuples sorted by degree descending
        """
        entities_with_degree = []

        for entity in self._entities.values():
            if entity_type and entity.type != entity_type:
                continue
            degree = self.get_degree(entity.id)
            entities_with_degree.append((entity, degree))

        entities_with_degree.sort(key=lambda x: x[1], reverse=True)
        return entities_with_degree[:limit]

    # Graph Traversal

    def get_neighbors(
        self,
        entity_id: str,
        relation_type: SupplyRelationType | None = None,
        direction: str = "both",
    ) -> list[SupplyEntity]:
        """Get neighboring entities."""
        neighbor_ids = set()

        for relation in self._relations:
            if relation_type and relation.relation_type != relation_type:
                continue

            if direction in ("out", "both") and relation.source_id == entity_id:
                neighbor_ids.add(relation.target_id)
            if direction in ("in", "both") and relation.target_id == entity_id:
                neighbor_ids.add(relation.source_id)

        return [self._entities[nid] for nid in neighbor_ids if nid in self._entities]

    def get_outgoing_relations(
        self,
        entity_id: str,
        relation_type: SupplyRelationType | None = None,
    ) -> list[SupplyRelation]:
        """Get outgoing relations from an entity."""
        return [
            r for r in self._relations
            if r.source_id == entity_id and
            (relation_type is None or r.relation_type == relation_type)
        ]

    def get_incoming_relations(
        self,
        entity_id: str,
        relation_type: SupplyRelationType | None = None,
    ) -> list[SupplyRelation]:
        """Get incoming relations to an entity."""
        return [
            r for r in self._relations
            if r.target_id == entity_id and
            (relation_type is None or r.relation_type == relation_type)
        ]

    # Path Finding

    def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_length: int = 5,
    ) -> list[GraphPath]:
        """Find all paths between two entities up to max_length."""
        if source_id not in self._entities or target_id not in self._entities:
            return []

        paths: list[GraphPath] = []
        visited: set[str] = set()

        def dfs(current_id: str, path: GraphPath) -> None:
            if current_id == target_id:
                paths.append(GraphPath(
                    entities=list(path.entities),
                    relations=list(path.relations),
                ))
                return

            if path.length >= max_length:
                return

            for relation in self.get_outgoing_relations(current_id):
                if relation.target_id in visited:
                    continue

                visited.add(relation.target_id)
                path.entities.append(self._entities[relation.target_id])
                path.relations.append(relation)

                dfs(relation.target_id, path)

                path.entities.pop()
                path.relations.pop()
                visited.remove(relation.target_id)

        visited.add(source_id)
        path = GraphPath(entities=[self._entities[source_id]], relations=[])
        dfs(source_id, path)

        return paths

    def find_shortest_path(
        self,
        source_id: str,
        target_id: str,
        max_length: int = 10,
    ) -> GraphPath | None:
        """Find the shortest path between two entities using BFS."""
        from collections import deque

        if source_id not in self._entities or target_id not in self._entities:
            return None

        queue: deque[tuple[str, list[SupplyRelation]]] = deque([(source_id, [])])
        visited: set[str] = {source_id}

        while queue:
            current_id, relations = queue.popleft()

            if len(relations) >= max_length:
                continue

            for relation in self.get_outgoing_relations(current_id):
                if relation.target_id in visited:
                    continue

                new_relations = relations + [relation]

                if relation.target_id == target_id:
                    entities = [self._entities[source_id]]
                    for r in new_relations:
                        entities.append(self._entities[r.target_id])
                    return GraphPath(entities=entities, relations=new_relations)

                visited.add(relation.target_id)
                queue.append((relation.target_id, new_relations))

        return None

    # Confidence Scoring

    def calculate_relation_confidence(
        self,
        relation: SupplyRelation,
    ) -> float:
        """Calculate confidence score for a relation.

        Based on multiple factors:
        - Relation type weight (certain relations are more reliable)
        - Property completeness
        - Graph structure (cycles may indicate lower confidence)
        """
        score = 0.5  # Base score

        # Relation type weights
        type_weights = {
            SupplyRelationType.HAS_SKU: 0.9,
            SupplyRelationType.HAS_BRAND: 0.9,
            SupplyRelationType.BELONGS_TO: 0.8,
            SupplyRelationType.SUPPLIES: 0.7,
            SupplyRelationType.SELLS: 0.7,
            SupplyRelationType.OFFERS: 0.7,
            SupplyRelationType.PROVIDES_SERVICE: 0.8,
            SupplyRelationType.HAS_INTENT: 0.8,
            SupplyRelationType.HAS_SLOT: 0.8,
            SupplyRelationType.AVAILABLE_IN: 0.7,
            SupplyRelationType.OPERATES_IN: 0.7,
            SupplyRelationType.GOVERNED_BY: 0.6,
            SupplyRelationType.HAS_RISK: 0.9,
            SupplyRelationType.SIMILAR_TO: 0.5,
            SupplyRelationType.RELATED_TO: 0.4,
        }

        type_weight = type_weights.get(relation.relation_type, 0.5)
        score = score * 0.6 + type_weight * 0.4

        # Property completeness bonus
        if relation.properties:
            score += min(0.1, len(relation.properties) * 0.02)

        # Check for reverse relation (increases confidence)
        has_reverse = any(
            r.source_id == relation.target_id and
            r.target_id == relation.source_id
            for r in self._relations
        )
        if has_reverse:
            score = min(1.0, score + 0.1)

        return min(1.0, max(0.0, score))

    def get_high_confidence_relations(
        self,
        threshold: float = 0.7,
    ) -> list[tuple[SupplyRelation, float]]:
        """Get relations with confidence above threshold."""
        results = []
        for relation in self._relations:
            confidence = self.calculate_relation_confidence(relation)
            if confidence >= threshold:
                results.append((relation, confidence))
        return sorted(results, key=lambda x: x[1], reverse=True)

    # Graph Statistics

    def count(self, entity_type: SupplyEntityType | None = None) -> int:
        """Count entities in the graph."""
        if entity_type is None:
            return len(self._entities)
        return len(self._entity_index.get(entity_type, []))

    def count_relations(self, relation_type: SupplyRelationType | None = None) -> int:
        """Count relations in the graph."""
        if relation_type is None:
            return len(self._relations)
        return sum(1 for r in self._relations if r.relation_type == relation_type)

    def get_degree(self, entity_id: str) -> int:
        """Get the degree (number of connections) of an entity."""
        return len(self.get_neighbors(entity_id))

    def get_in_degree(self, entity_id: str) -> int:
        """Get the in-degree of an entity."""
        return len(self.get_incoming_relations(entity_id))

    def get_out_degree(self, entity_id: str) -> int:
        """Get the out-degree of an entity."""
        return len(self.get_outgoing_relations(entity_id))

    def get_graph_stats(self) -> dict[str, Any]:
        """Get statistics about the graph."""
        entity_counts = {
            etype.value: len(ids)
            for etype, ids in self._entity_index.items()
        }

        relation_counts = {
            rtype.value: sum(1 for r in self._relations if r.relation_type == rtype)
            for rtype in SupplyRelationType
        }

        return {
            "total_entities": len(self._entities),
            "total_relations": len(self._relations),
            "entity_counts": entity_counts,
            "relation_counts": relation_counts,
            "avg_degree": (
                sum(self.get_degree(eid) for eid in self._entities) /
                len(self._entities) if self._entities else 0
            ),
        }

    # Import/Export

    def load_graph(self, graph: SupplyGraph) -> None:
        """Load entities and relations from a SupplyGraph."""
        for entity in graph.entities:
            try:
                self.create_entity(entity, validate=False)
            except ValueError:
                # Entity already exists, update it
                self.update_entity(entity, validate=False)

        for relation in graph.relations:
            try:
                self.create_relation(relation, validate=False)
            except ValueError:
                # Relation already exists, skip
                pass

    def export_graph(self) -> SupplyGraph:
        """Export the graph as a SupplyGraph."""
        return SupplyGraph(
            entities=list(self._entities.values()),
            relations=self._relations.copy(),
        )

    def clear(self) -> None:
        """Clear all entities and relations."""
        self._entities.clear()
        self._relations.clear()
        self._entity_index.clear()

    # Advanced Query APIs

    def query_entities_matching_pattern(
        self,
        entity_type: SupplyEntityType,
        required_relations: list[tuple[SupplyRelationType, SupplyEntityType | None, str]] | None = None,
        property_filters: dict[str, Any] | None = None,
    ) -> list[SupplyEntity]:
        """Query entities matching a specific graph pattern.

        Args:
            entity_type: The type of entities to find
            required_relations: List of (relation_type, target_type, direction) tuples.
                direction can be 'out' (outgoing) or 'in' (incoming).
                If target_type is None, any target type matches.
            property_filters: Optional property key-value pairs to filter by

        Returns:
            List of entities matching the pattern

        Example:
            # Find products that have a brand and are supplied by a specific supplier
            db.query_entities_matching_pattern(
                entity_type=SupplyEntityType.PRODUCT,
                required_relations=[
                    (SupplyRelationType.HAS_BRAND, None, 'out'),
                    (SupplyRelationType.SUPPLIES, SupplyEntityType.SUPPLIER, 'out'),
                ]
            )
        """
        candidates = self.query_by_type(entity_type)
        results = []

        for entity in candidates:
            # Check property filters
            if property_filters:
                match = all(
                    entity.properties.get(k) == v
                    for k, v in property_filters.items()
                )
                if not match:
                    continue

            # Check required relations
            if required_relations:
                entity_relations = {
                    'out': self.get_outgoing_relations(entity.id),
                    'in': self.get_incoming_relations(entity.id),
                }

                all_match = True
                for rel_type, target_type, direction in required_relations:
                    relevant_rels = entity_relations.get(direction, [])
                    has_match = False
                    for r in relevant_rels:
                        if r.relation_type == rel_type:
                            if target_type is None:
                                has_match = True
                                break
                            related_entity_id = r.target_id if direction == 'out' else r.source_id
                            related_entity = self._entities.get(related_entity_id)
                            if related_entity is not None and related_entity.type == target_type:
                                has_match = True
                                break
                    if not has_match:
                        all_match = False
                        break

                if not all_match:
                    continue

            results.append(entity)

        return results

    def get_entity_statistics(self) -> dict[str, Any]:
        """Get comprehensive statistics about the graph.

        Returns:
            Dictionary with entity counts, relation counts, and graph metrics
        """
        stats = {
            "total_entities": len(self._entities),
            "total_relations": len(self._relations),
            "entities_by_type": {},
            "relations_by_type": {},
            "avg_relations_per_entity": 0.0,
            "entities_with_no_relations": 0,
            "entities_with_high_confidence": 0,
        }

        # Count entities by type
        for entity in self._entities.values():
            type_name = entity.type.value
            stats["entities_by_type"][type_name] = stats["entities_by_type"].get(type_name, 0) + 1

        # Count relations by type
        for relation in self._relations:
            type_name = relation.relation_type.value
            stats["relations_by_type"][type_name] = stats["relations_by_type"].get(type_name, 0) + 1

        # Calculate average relations per entity
        if self._entities:
            relation_counts = []
            for entity in self._entities.values():
                out_count = len(self.get_outgoing_relations(entity.id))
                in_count = len(self.get_incoming_relations(entity.id))
                total = out_count + in_count
                relation_counts.append(total)

                if total == 0:
                    stats["entities_with_no_relations"] += 1

            stats["avg_relations_per_entity"] = sum(relation_counts) / len(relation_counts)

        # Count entities with high confidence relations
        high_conf_threshold = 0.7
        for entity in self._entities.values():
            outgoing = self.get_outgoing_relations(entity.id)
            if any(self.calculate_relation_confidence(r) >= high_conf_threshold for r in outgoing):
                stats["entities_with_high_confidence"] += 1

        return stats

    def find_similar_entities(
        self,
        entity_id: str,
        max_results: int = 10,
    ) -> list[tuple[SupplyEntity, float]]:
        """Find entities similar to the given entity based on properties and relations.

        Similarity is calculated based on:
        - Shared relation types
        - Shared property keys
        - Same entity type (higher weight)

        Args:
            entity_id: The ID of the entity to find similar entities for
            max_results: Maximum number of results to return

        Returns:
            List of (entity, similarity_score) tuples sorted by similarity
        """
        if entity_id not in self._entities:
            return []

        source_entity = self._entities[entity_id]
        source_outgoing = self.get_outgoing_relations(entity_id)
        source_incoming = self.get_incoming_relations(entity_id)

        similarities: list[tuple[SupplyEntity, float]] = []

        for entity in self._entities.values():
            if entity.id == entity_id:
                continue

            score = 0.0

            # Same type bonus
            if entity.type == source_entity.type:
                score += 0.3

            # Compare outgoing relations
            target_outgoing = self.get_outgoing_relations(entity.id)
            source_out_types = set(r.relation_type for r in source_outgoing)
            target_out_types = set(r.relation_type for r in target_outgoing)
            shared_out = source_out_types & target_out_types
            score += len(shared_out) * 0.1

            # Compare incoming relations
            target_incoming = self.get_incoming_relations(entity.id)
            source_in_types = set(r.relation_type for r in source_incoming)
            target_in_types = set(r.relation_type for r in target_incoming)
            shared_in = source_in_types & target_in_types
            score += len(shared_in) * 0.1

            # Compare properties
            source_props = set(source_entity.properties.keys())
            target_props = set(entity.properties.keys())
            shared_props = source_props & target_props
            score += len(shared_props) * 0.05

            # Cap score at 1.0
            score = min(1.0, score)
            similarities.append((entity, score))

        # Sort by similarity score descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:max_results]

    def get_connected_entities(
        self,
        entity_id: str,
        max_distance: int = 2,
        relation_types: list[SupplyRelationType] | None = None,
    ) -> dict[int, list[SupplyEntity]]:
        """Get all entities connected to the given entity within max_distance hops.

        Args:
            entity_id: The ID of the starting entity
            max_distance: Maximum number of hops to traverse
            relation_types: Optional list of relation types to filter by

        Returns:
            Dictionary mapping distance to list of entities at that distance
        """
        if entity_id not in self._entities:
            return {}

        result: dict[int, list[SupplyEntity]] = {i: [] for i in range(1, max_distance + 1)}
        visited: set[str] = {entity_id}

        for distance in range(1, max_distance + 1):
            current_level: set[str] = set()

            # Get all entities at previous distance
            if distance == 1:
                prev_level = {entity_id}
            else:
                prev_level = {e.id for e in result[distance - 1]}

            for prev_id in prev_level:
                neighbors = self.get_neighbors(
                    prev_id,
                    relation_type=None if relation_types is None else relation_types[0] if relation_types else None,
                    direction="both"
                )

                for neighbor in neighbors:
                    if neighbor.id not in visited:
                        # Filter by relation types if specified
                        if relation_types:
                            neighbor_rels = self.get_outgoing_relations(prev_id) + self.get_incoming_relations(prev_id)
                            if any(r.relation_type in relation_types for r in neighbor_rels):
                                current_level.add(neighbor.id)
                                result[distance].append(neighbor)
                        else:
                            current_level.add(neighbor.id)
                            result[distance].append(neighbor)

            visited.update(current_level)

        return result

    # Entity Normalization and Deduplication

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison.

        Converts to lowercase, removes extra whitespace, and strips special chars.
        """
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s]', '', text)
        return text

    def calculate_entity_similarity(
        self,
        entity1: SupplyEntity,
        entity2: SupplyEntity,
    ) -> float:
        """Calculate similarity score between two entities.

        Uses multiple factors:
        - Name similarity (edit distance based)
        - Property overlap
        - Same entity type (bonus)

        Returns score between 0.0 and 1.0.
        """
        if entity1.id == entity2.id:
            return 1.0

        # Type bonus: same type is more likely to be duplicate
        type_bonus = 0.0
        if entity1.type == entity2.type:
            type_bonus = 0.2

        # Name similarity
        name1 = self._normalize_text(entity1.name)
        name2 = self._normalize_text(entity2.name)

        if name1 == name2:
            name_score = 1.0
        elif name1 in name2 or name2 in name1:
            name_score = 0.8
        else:
            # Simple character-based similarity
            name_score = self._calculate_string_similarity(name1, name2)

        # Property similarity
        props1 = set(entity1.properties.keys())
        props2 = set(entity2.properties.keys())

        if not props1 or not props2:
            prop_score = 0.0
        else:
            common = props1 & props2
            total = props1 | props2
            prop_score = len(common) / len(total) if total else 0.0

        # Combine scores with weights
        score = (name_score * 0.6 + prop_score * 0.2 + type_bonus)
        return min(1.0, max(0.0, score))

    def _calculate_string_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity between two strings using character overlap.

        Returns score between 0.0 and 1.0.
        """
        if not s1 or not s2:
            return 0.0

        # Character-level Jaccard similarity
        set1 = set(s1.split())
        set2 = set(s2.split())

        if not set1 or not set2:
            return 0.0

        intersection = set1 & set2
        union = set1 | set2

        return len(intersection) / len(union) if union else 0.0

    def find_potential_duplicates(
        self,
        entity_type: SupplyEntityType | None = None,
        similarity_threshold: float = 0.8,
    ) -> list[DuplicateGroup]:
        """Find potential duplicate entities in the graph.

        Args:
            entity_type: Optional entity type to filter by
            similarity_threshold: Minimum similarity score (0.0-1.0) to consider as duplicate

        Returns:
            List of DuplicateGroup objects, each containing entities that may be duplicates
        """
        candidates = list(self._entities.values())
        if entity_type:
            candidates = [e for e in candidates if e.type == entity_type]

        duplicate_groups: dict[str, DuplicateGroup] = {}
        processed: set[tuple[str, str]] = set()

        for i, entity1 in enumerate(candidates):
            for entity2 in candidates[i + 1:]:
                # Skip if already processed
                pair = tuple(sorted([entity1.id, entity2.id]))
                if pair in processed:
                    continue

                similarity = self.calculate_entity_similarity(entity1, entity2)

                if similarity >= similarity_threshold:
                    processed.add(pair)

                    # Check if either entity is already in a group
                    found_group = None
                    for group in duplicate_groups.values():
                        if entity1.id in [e.id for e in group.entities]:
                            found_group = group
                            break
                        if entity2.id in [e.id for e in group.entities]:
                            found_group = group
                            break

                    if found_group:
                        # Add to existing group
                        found_group.entities.append(entity2)
                        found_group.similarity_scores.append(similarity)
                    else:
                        # Create new group
                        # Use the entity with lower ID as canonical for determinism
                        canonical_id = entity1.id if entity1.id < entity2.id else entity2.id
                        duplicate_groups[pair[0] + "_" + pair[1]] = DuplicateGroup(
                            canonical_id=canonical_id,
                            entities=[entity1, entity2],
                            similarity_scores=[similarity, similarity],
                        )

        return list(duplicate_groups.values())

    def merge_entities(
        self,
        entity_ids: list[str],
        canonical_id: str | None = None,
        preserve_properties: bool = True,
    ) -> MergeResult:
        """Merge multiple entities into one.

        Args:
            entity_ids: List of entity IDs to merge
            canonical_id: ID to use for the merged entity (if None, uses first ID)
            preserve_properties: If True, merge properties from all entities

        Returns:
            MergeResult with the merged entity and statistics
        """
        if len(entity_ids) < 2:
            raise ValueError("At least 2 entities required for merge")

        # Validate all entities exist
        entities = []
        for eid in entity_ids:
            entity = self._entities.get(eid)
            if not entity:
                raise ValueError(f"Entity {eid} not found")
            entities.append(entity)

        # Determine canonical entity
        if canonical_id and canonical_id in self._entities:
            canonical = self._entities[canonical_id]
        else:
            canonical = entities[0]
            canonical_id = canonical.id

        # Collect all relations to preserve
        all_relations: list[SupplyRelation] = []
        for entity in entities:
            all_relations.extend(self.get_outgoing_relations(entity.id))
            all_relations.extend(self.get_incoming_relations(entity.id))

        # Merge properties if requested
        merged_properties = dict(canonical.properties)
        if preserve_properties:
            for entity in entities:
                for key, value in entity.properties.items():
                    if key not in merged_properties:
                        merged_properties[key] = value
                    elif merged_properties[key] != value:
                        # Keep as list if different values
                        existing = merged_properties[key]
                        if not isinstance(existing, list):
                            merged_properties[key] = [existing, value]
                        elif value not in existing:
                            merged_properties[key] = existing + [value]

        # Create merged entity
        merged_entity = SupplyEntity(
            id=canonical_id,
            type=canonical.type,
            properties=merged_properties,
            version=canonical.version + 1,
        )

        # Update graph: replace all entities with merged one
        relations_preserved = 0
        relations_removed = 0
        updated_relations: list[SupplyRelation] = []

        for rel in self._relations:
            source_in_merge = rel.source_id in entity_ids
            target_in_merge = rel.target_id in entity_ids

            if source_in_merge and target_in_merge:
                # Both in merge - remove (self-loop after merge)
                relations_removed += 1
            elif source_in_merge:
                # Source in merge - update to canonical
                updated_relations.append(SupplyRelation(
                    source_id=canonical_id,
                    target_id=rel.target_id,
                    relation_type=rel.relation_type,
                    properties=rel.properties,
                    version=rel.version,
                ))
                relations_preserved += 1
            elif target_in_merge:
                # Target in merge - update to canonical
                updated_relations.append(SupplyRelation(
                    source_id=rel.source_id,
                    target_id=canonical_id,
                    relation_type=rel.relation_type,
                    properties=rel.properties,
                    version=rel.version,
                ))
                relations_preserved += 1
            else:
                # Neither in merge - keep as is
                updated_relations.append(rel)

        # Delete all source entities except canonical
        for entity in entities:
            if entity.id != canonical_id:
                self.delete_entity(entity.id)

        # Update canonical entity
        self._entities[canonical_id] = merged_entity

        # Update relations
        self._relations = updated_relations

        return MergeResult(
            merged_entity=merged_entity,
            source_ids=entity_ids,
            relations_preserved=relations_preserved,
            relations_removed=relations_removed,
        )

    def deduplicate(
        self,
        similarity_threshold: float = 0.8,
        entity_type: SupplyEntityType | None = None,
    ) -> list[MergeResult]:
        """Automatically find and merge duplicate entities.

        Args:
            similarity_threshold: Minimum similarity to consider as duplicate
            entity_type: Optional entity type to limit deduplication to

        Returns:
            List of MergeResult for each merge performed
        """
        duplicate_groups = self.find_potential_duplicates(
            entity_type=entity_type,
            similarity_threshold=similarity_threshold,
        )

        results: list[MergeResult] = []
        merged_ids: set[str] = set()

        for group in duplicate_groups:
            # Skip if any entity already merged
            entity_ids = [e.id for e in group.entities]
            if any(eid in merged_ids for eid in entity_ids):
                continue

            try:
                result = self.merge_entities(
                    entity_ids=entity_ids,
                    canonical_id=group.canonical_id,
                )
                results.append(result)
                merged_ids.update(entity_ids)
            except ValueError:
                # Skip if merge fails
                continue

        return results

    def get_normalized_entity_representatives(
        self,
        entity_type: SupplyEntityType | None = None,
    ) -> list[SupplyEntity]:
        """Get representative entities for each unique entity (after normalization).

        Uses deduplication to find canonical representatives.
        """
        duplicates = self.find_potential_duplicates(
            entity_type=entity_type,
            similarity_threshold=0.8,
        )

        # Collect all entity IDs that have duplicates
        duplicate_ids: set[str] = set()
        for group in duplicates:
            for entity in group.entities:
                if entity.id != group.canonical_id:
                    duplicate_ids.add(entity.id)

        # Return all entities except those marked as duplicates
        candidates = self.query_by_type(entity_type) if entity_type else list(self._entities.values())
        return [e for e in candidates if e.id not in duplicate_ids]

    # Incremental Update Pipeline

    def begin_transaction(self) -> Transaction:
        """Begin a new transaction for batch operations.

        Returns:
            A new Transaction object

        Example:
            db.begin_transaction()
            db.create_entity(entity1)
            db.create_entity(entity2)
            db.create_relation(relation)
            db.commit()
        """
        if self._current_transaction is not None:
            raise RuntimeError("A transaction is already in progress")
        self._current_transaction = Transaction()
        return self._current_transaction

    def commit(self) -> None:
        """Commit the current transaction."""
        if self._current_transaction is None:
            raise RuntimeError("No transaction in progress")
        self._current_transaction._committed = True
        self._current_transaction = None

    def rollback(self) -> None:
        """Rollback the current transaction.

        This will revert all operations performed since the transaction began.
        """
        if self._current_transaction is None:
            raise RuntimeError("No transaction in progress")

        # Reverse operations in LIFO order
        for op_type, data in reversed(self._current_transaction.operations):
            if op_type == "create_entity":
                self._entities.pop(data.id, None)
                # Remove from index
                if data.type in self._entity_index:
                    self._entity_index[data.type] = [
                        eid for eid in self._entity_index[data.type]
                        if eid != data.id
                    ]
            elif op_type == "update_entity":
                # Restore previous version
                self._entities[data["entity_id"]] = data["previous_entity"]
            elif op_type == "delete_entity":
                # Restore entity and its relations
                self._entities[data["entity_id"]] = data["entity"]
                self._reindex_entity(data["entity"])
                for rel in data.get("relations", []):
                    if rel not in self._relations:
                        self._relations.append(rel)
            elif op_type == "create_relation":
                # Remove the relation
                self._relations = [
                    r for r in self._relations
                    if not (r.source_id == data.source_id and
                            r.target_id == data.target_id and
                            r.relation_type == data.relation_type)
                ]
            elif op_type == "delete_relation":
                # Restore the relation
                self._relations.append(data)

        self._current_transaction = None

    def _record_entity_create(self, entity: SupplyEntity) -> None:
        """Record entity creation in change history."""
        event = ChangeEvent(
            change_type=ChangeType.ENTITY_CREATED,
            entity_id=entity.id,
            metadata={"entity_type": entity.type.value},
        )
        self._change_history.add_event(event)

    def _record_entity_update(self, entity: SupplyEntity, previous: SupplyEntity) -> None:
        """Record entity update in change history."""
        event = ChangeEvent(
            change_type=ChangeType.ENTITY_UPDATED,
            entity_id=entity.id,
            metadata={
                "entity_type": entity.type.value,
                "previous_version": previous.version,
                "new_version": entity.version,
            },
        )
        self._change_history.add_event(event)

    def _record_entity_delete(self, entity: SupplyEntity) -> None:
        """Record entity deletion in change history."""
        event = ChangeEvent(
            change_type=ChangeType.ENTITY_DELETED,
            entity_id=entity.id,
            metadata={"entity_type": entity.type.value},
        )
        self._change_history.add_event(event)

    def _record_relation_create(self, relation: SupplyRelation) -> None:
        """Record relation creation in change history."""
        event = ChangeEvent(
            change_type=ChangeType.RELATION_CREATED,
            relation=relation,
            metadata={"relation_type": relation.relation_type.value},
        )
        self._change_history.add_event(event)

    def _record_relation_delete(self, relation: SupplyRelation) -> None:
        """Record relation deletion in change history."""
        event = ChangeEvent(
            change_type=ChangeType.RELATION_DELETED,
            relation=relation,
            metadata={"relation_type": relation.relation_type.value},
        )
        self._change_history.add_event(event)

    def get_change_history(
        self,
        entity_id: str | None = None,
        limit: int = 100,
    ) -> ChangeHistory:
        """Get the change history.

        Args:
            entity_id: Optional entity ID to filter changes
            limit: Maximum number of events to return

        Returns:
            ChangeHistory object containing relevant events
        """
        if entity_id is None:
            # Return all events limited
            limited_history = ChangeHistory(
                events=self._change_history.events[-limit:],
                version=self._change_history.version,
            )
            return limited_history

        # Filter for specific entity
        entity_events = self._change_history.get_entity_history(entity_id)
        return ChangeHistory(
            events=entity_events[-limit:],
            version=self._change_history.version,
        )

    def get_change_count(self) -> int:
        """Get the total number of changes recorded."""
        return self._change_history.version

    def incrementally_update_entity(
        self,
        entity: SupplyEntity,
        merge_properties: bool = True,
    ) -> SupplyEntity:
        """Incrementally update an entity, creating if not exists.

        This method handles both create and update operations:
        - If entity doesn't exist: creates it (like create_entity)
        - If entity exists: merges properties and updates (like update_entity)

        Args:
            entity: The entity to update
            merge_properties: If True, merge new properties with existing.
                              If False, replace entirely.

        Returns:
            The updated entity
        """
        existing = self._entities.get(entity.id)

        if existing is None:
            # Create new entity
            return self.create_entity(entity)

        # Merge properties if requested
        if merge_properties:
            merged_properties = dict(existing.properties)
            merged_properties.update(entity.properties)
            entity.properties = merged_properties

        # Let update_entity handle versioning - don't set it here
        # This avoids the double-increment issue when entity is same object as stored
        return self.update_entity(entity)

    def batch_create_entities(
        self,
        entities: list[SupplyEntity],
        validate: bool = True,
    ) -> list[SupplyEntity]:
        """Batch create multiple entities.

        Args:
            entities: List of entities to create
            validate: Whether to validate entities

        Returns:
            List of created entities

        Raises:
            ValidationError: If any entity fails validation
            ValueError: If any entity already exists
        """
        # Validate all first
        if validate:
            for entity in entities:
                errors = self._validate_entity(entity)
                if errors:
                    raise ValidationError(f"Entity {entity.id} validation failed: {'; '.join(errors)}")

        # Check for duplicates
        existing_ids = [e.id for e in entities if e.id in self._entities]
        if existing_ids:
            raise ValueError(f"Entities already exist: {existing_ids}")

        # Create all
        created = []
        for entity in entities:
            self._entities[entity.id] = entity
            self._reindex_entity(entity)
            self._record_entity_create(entity)
            created.append(entity)

        return created

    def batch_create_relations(
        self,
        relations: list[SupplyRelation],
        validate: bool = True,
    ) -> list[SupplyRelation]:
        """Batch create multiple relations.

        Args:
            relations: List of relations to create
            validate: Whether to validate relations

        Returns:
            List of created relations

        Raises:
            ValidationError: If any relation fails validation
            ValueError: If any entity doesn't exist
        """
        # Validate all first
        if validate:
            for relation in relations:
                errors = self._validate_relation(relation)
                if errors:
                    raise ValidationError(f"Relation validation failed: {'; '.join(errors)}")

        # Check entities exist
        for relation in relations:
            if relation.source_id not in self._entities:
                raise ValueError(f"Source entity {relation.source_id} not found")
            if relation.target_id not in self._entities:
                raise ValueError(f"Target entity {relation.target_id} not found")

        # Create all
        created = []
        for relation in relations:
            self._relations.append(relation)
            self._record_relation_create(relation)
            created.append(relation)

        return created

    def upsert_entity(
        self,
        entity: SupplyEntity,
        merge_properties: bool = True,
    ) -> tuple[SupplyEntity, bool]:
        """Upsert an entity (update if exists, insert if new).

        Args:
            entity: The entity to upsert
            merge_properties: If True, merge properties on update

        Returns:
            Tuple of (entity, created) where created is True if entity was newly created
        """
        existing = self._entities.get(entity.id)

        if existing is None:
            created_entity = self.create_entity(entity)
            return created_entity, True

        # Merge properties if requested
        if merge_properties:
            merged_properties = dict(existing.properties)
            merged_properties.update(entity.properties)
            entity.properties = merged_properties

        # Let update_entity handle versioning - don't set it here
        # This avoids the double-increment issue when entity is same object as stored
        updated_entity = self.update_entity(entity)
        return updated_entity, False

    def apply_incremental_changes(
        self,
        entities_to_create: list[SupplyEntity] | None = None,
        entities_to_update: list[SupplyEntity] | None = None,
        entities_to_delete: list[str] | None = None,
        relations_to_create: list[SupplyRelation] | None = None,
        relations_to_delete: list[tuple[str, str, SupplyRelationType]] | None = None,
    ) -> dict[str, Any]:
        """Apply a batch of incremental changes to the graph.

        This method performs all operations in a single transaction,
        rolling back all if any operation fails.

        Args:
            entities_to_create: List of entities to create
            entities_to_update: List of entities to update
            entities_to_delete: List of entity IDs to delete
            relations_to_create: List of relations to create
            relations_to_delete: List of (source_id, target_id, relation_type) to delete

        Returns:
            Dictionary with counts of each operation type performed

        Example:
            result = db.apply_incremental_changes(
                entities_to_create=[new_entity],
                entities_to_update=[existing_entity],
                entities_to_delete=["old_entity_id"],
                relations_to_create=[new_relation],
                relations_to_delete=[("source", "target", SupplyRelationType.HAS_BRAND)],
            )
        """
        self.begin_transaction()

        try:
            results = {
                "entities_created": 0,
                "entities_updated": 0,
                "entities_deleted": 0,
                "relations_created": 0,
                "relations_deleted": 0,
            }

            # Create entities
            if entities_to_create:
                for entity in entities_to_create:
                    self.create_entity(entity)
                    results["entities_created"] += 1

            # Update entities
            if entities_to_update:
                for entity in entities_to_update:
                    self.update_entity(entity)
                    results["entities_updated"] += 1

            # Delete entities
            if entities_to_delete:
                for entity_id in entities_to_delete:
                    if self.delete_entity(entity_id):
                        results["entities_deleted"] += 1

            # Create relations
            if relations_to_create:
                for relation in relations_to_create:
                    self.create_relation(relation)
                    results["relations_created"] += 1

            # Delete relations
            if relations_to_delete:
                for source_id, target_id, rel_type in relations_to_delete:
                    if self.delete_relation(source_id, target_id, rel_type):
                        results["relations_deleted"] += 1

            self.commit()
            return results

        except Exception as e:
            if self._current_transaction is not None:
                try:
                    self.rollback()
                except RuntimeError:
                    pass  # Transaction already ended
            raise e

    def get_entity_version(self, entity_id: str) -> int | None:
        """Get the current version of an entity.

        Args:
            entity_id: The ID of the entity

        Returns:
            The version number, or None if entity doesn't exist
        """
        entity = self._entities.get(entity_id)
        return entity.version if entity else None

    def get_graph_version(self) -> int:
        """Get the overall graph version (total changes).

        Returns:
            The total number of changes recorded
        """
        return self._change_history.version


# Global instance
_global_supply_graph: SupplyGraphDatabase | None = None


def get_supply_graph() -> SupplyGraphDatabase:
    """Get the global supply graph database instance."""
    global _global_supply_graph
    if _global_supply_graph is None:
        _global_supply_graph = SupplyGraphDatabase()
    return _global_supply_graph


def set_supply_graph(graph: SupplyGraphDatabase) -> None:
    """Set the global supply graph database instance."""
    global _global_supply_graph
    _global_supply_graph = graph
