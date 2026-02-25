"""Supply Graph Database with validation, confidence scoring, and query APIs.

This module provides a specialized graph database implementation for the supply
knowledge graph with schema validation, relation confidence scoring, and
advanced traversal/query capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

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


class SupplyGraphDatabase:
    """Graph database for supply knowledge graph.

    Provides validation, confidence scoring, and advanced query APIs
    specific to e-commerce and mini-program supply domain.
    """

    def __init__(self) -> None:
        self._entities: dict[str, SupplyEntity] = {}
        self._relations: list[SupplyRelation] = []
        self._entity_index: dict[SupplyEntityType, list[str]] = {}
        self._validation_rules: list[ValidationRule] = []
        self._initialize_validation_rules()

    def _initialize_validation_rules(self) -> None:
        """Initialize default validation rules."""

        # Entity validation rules
        self._validation_rules.append(ValidationRule(
            name="entity_has_id",
            description="Entity must have a non-empty ID",
            validator=lambda e: bool(e.id and e.id.strip()),
            error_message="Entity ID cannot be empty",
        ))

        self._validation_rules.append(ValidationRule(
            name="entity_has_valid_type",
            description="Entity must have a valid type",
            validator=lambda e: isinstance(e.type, SupplyEntityType),
            error_message="Entity must have a valid SupplyEntityType",
        ))

        self._validation_rules.append(ValidationRule(
            name="product_has_name",
            description="Product entities must have a name",
            validator=lambda e: (
                e.type != SupplyEntityType.PRODUCT or
                "name" in e.properties or bool(e.id)
            ),
            error_message="Product must have a name in properties",
        ))

        # Relation validation rules
        self._validation_rules.append(ValidationRule(
            name="relation_has_valid_entities",
            description="Relation must reference existing entities",
            validator=lambda r: (
                r.source_id in self._entities and
                r.target_id in self._entities
            ),
            error_message="Relation references non-existent entities",
        ))

        self._validation_rules.append(ValidationRule(
            name="relation_has_valid_type",
            description="Relation must have a valid type",
            validator=lambda r: isinstance(r.relation_type, SupplyRelationType),
            error_message="Relation must have a valid SupplyRelationType",
        ))

        self._validation_rules.append(ValidationRule(
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
        for rule in self._validation_rules:
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
        for rule in self._validation_rules:
            try:
                if not rule.validator(relation):
                    errors.append(f"{rule.name}: {rule.error_message}")
            except Exception as e:
                errors.append(f"{rule.name}: Validation error - {e}")
        return errors

    # CRUD Operations

    def create_entity(self, entity: SupplyEntity, validate: bool = True) -> SupplyEntity:
        """Create a new entity in the graph."""
        if validate:
            errors = self._validate_entity(entity)
            if errors:
                raise ValidationError(f"Entity validation failed: {'; '.join(errors)}")

        if entity.id in self._entities:
            raise ValueError(f"Entity with id {entity.id} already exists")

        self._entities[entity.id] = entity
        self._reindex_entity(entity)
        return entity

    def get_entity(self, entity_id: str) -> SupplyEntity | None:
        """Get an entity by ID."""
        return self._entities.get(entity_id)

    def update_entity(self, entity: SupplyEntity, validate: bool = True) -> SupplyEntity:
        """Update an existing entity."""
        if validate:
            errors = self._validate_entity(entity)
            if errors:
                raise ValidationError(f"Entity validation failed: {'; '.join(errors)}")

        if entity.id not in self._entities:
            raise ValueError(f"Entity with id {entity.id} not found")

        self._entities[entity.id] = entity
        return entity

    def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity and all its relations."""
        if entity_id not in self._entities:
            return False

        # Delete all relations involving this entity
        self._relations = [
            r for r in self._relations
            if r.source_id != entity_id and r.target_id != entity_id
        ]

        # Remove from index
        entity = self._entities[entity_id]
        if entity.type in self._entity_index:
            self._entity_index[entity.type] = [
                eid for eid in self._entity_index[entity.type]
                if eid != entity_id
            ]

        del self._entities[entity_id]
        return True

    def create_relation(
        self,
        relation: SupplyRelation,
        validate: bool = True,
    ) -> SupplyRelation:
        """Create a new relation in the graph."""
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
        return relation

    def delete_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: SupplyRelationType,
    ) -> bool:
        """Delete a relation."""
        original_count = len(self._relations)
        self._relations = [
            r for r in self._relations
            if not (r.source_id == source_id and
                    r.target_id == target_id and
                    r.relation_type == relation_type)
        ]
        return len(self._relations) < original_count

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
