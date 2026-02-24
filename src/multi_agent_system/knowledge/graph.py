"""Graph database abstraction layer for knowledge graph operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterator


class EntityType(Enum):
    """Types of entities in the knowledge graph."""
    PRODUCT = "product"
    SERVICE = "service"
    MERCHANT = "merchant"
    CATEGORY = "category"
    USER = "user"
    LOCATION = "location"
    BRAND = "brand"
    TAG = "tag"


class RelationType(Enum):
    """Types of relations between entities."""
    BELONGS_TO = "belongs_to"  # Product/Service -> Category
    OFFERS = "offers"  # Merchant -> Product/Service
    LOCATED_AT = "located_at"  # Merchant -> Location
    SIMILAR_TO = "similar_to"  # Product/Service <-> Product/Service
    RELATED_TO = "related_to"  # Generic relation
    HAS_TAG = "has_tag"  # Entity -> Tag
    HAS_BRAND = "has_brand"  # Product -> Brand
    PROVIDES = "provides"  # Merchant -> Service
    SELLS = "sells"  # Merchant -> Product


@dataclass
class Entity:
    """A node in the knowledge graph."""
    id: str
    type: EntityType
    properties: dict[str, Any] = field(default_factory=dict)
    
    @property
    def name(self) -> str:
        return self.properties.get("name", self.id)
    
    @property
    def description(self) -> str | None:
        return self.properties.get("description")


@dataclass
class Relation:
    """An edge in the knowledge graph."""
    source_id: str
    target_id: str
    relation_type: RelationType
    properties: dict[str, Any] = field(default_factory=dict)
    
    @property
    def weight(self) -> float:
        return self.properties.get("weight", 1.0)


@dataclass
class GraphQuery:
    """A query on the knowledge graph."""
    entity_type: EntityType | None = None
    entity_ids: list[str] = field(default_factory=list)
    relation_type: RelationType | None = None
    limit: int = 100
    filters: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphResult:
    """Result from a graph query."""
    entities: list[Entity] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class GraphDatabase(ABC):
    """Abstract interface for graph databases.
    
    Implement this to support different graph backends:
    - NetworkX (in-memory)
    - Neo4j
    - Amazon Neptune
    - etc.
    """
    
    @abstractmethod
    def create_entity(self, entity: Entity) -> Entity:
        """Create a new entity in the graph."""
        pass
    
    @abstractmethod
    def get_entity(self, entity_id: str) -> Entity | None:
        """Get an entity by ID."""
        pass
    
    @abstractmethod
    def update_entity(self, entity: Entity) -> Entity:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity by ID."""
        pass
    
    @abstractmethod
    def create_relation(self, relation: Relation) -> Relation:
        """Create a new relation in the graph."""
        pass
    
    @abstractmethod
    def delete_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
    ) -> bool:
        """Delete a relation."""
        pass
    
    @abstractmethod
    def query(self, query: GraphQuery) -> GraphResult:
        """Execute a graph query."""
        pass
    
    @abstractmethod
    def get_neighbors(
        self,
        entity_id: str,
        relation_type: RelationType | None = None,
        direction: str = "both",  # "in", "out", "both"
    ) -> list[Entity]:
        """Get neighboring entities."""
        pass
    
    @abstractmethod
    def get_outgoing_relations(
        self,
        entity_id: str,
        relation_type: RelationType | None = None,
    ) -> list[Relation]:
        """Get outgoing relations from an entity."""
        pass
    
    @abstractmethod
    def get_incoming_relations(
        self,
        entity_id: str,
        relation_type: RelationType | None = None,
    ) -> list[Relation]:
        """Get incoming relations to an entity."""
        pass
    
    @abstractmethod
    def search(
        self,
        entity_type: EntityType | None = None,
        text: str | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> list[Entity]:
        """Search for entities."""
        pass
    
    @abstractmethod
    def count(self, entity_type: EntityType | None = None) -> int:
        """Count entities in the graph."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all entities and relations."""
        pass


class InMemoryGraphDatabase(GraphDatabase):
    """In-memory graph database implementation using dictionaries.
    
    Suitable for development and small-scale deployments.
    """
    
    def __init__(self) -> None:
        self._entities: dict[str, Entity] = {}
        self._relations: list[Relation] = []
    
    def create_entity(self, entity: Entity) -> Entity:
        if entity.id in self._entities:
            raise ValueError(f"Entity with id {entity.id} already exists")
        self._entities[entity.id] = entity
        return entity
    
    def get_entity(self, entity_id: str) -> Entity | None:
        return self._entities.get(entity_id)
    
    def update_entity(self, entity: Entity) -> Entity:
        if entity.id not in self._entities:
            raise ValueError(f"Entity with id {entity.id} not found")
        self._entities[entity.id] = entity
        return entity
    
    def delete_entity(self, entity_id: str) -> bool:
        if entity_id not in self._entities:
            return False
        # Also delete all relations involving this entity
        self._relations = [
            r for r in self._relations
            if r.source_id != entity_id and r.target_id != entity_id
        ]
        del self._entities[entity_id]
        return True
    
    def create_relation(self, relation: Relation) -> Relation:
        self._relations.append(relation)
        return relation
    
    def delete_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
    ) -> bool:
        original_count = len(self._relations)
        self._relations = [
            r for r in self._relations
            if not (r.source_id == source_id and 
                    r.target_id == target_id and 
                    r.relation_type == relation_type)
        ]
        return len(self._relations) < original_count
    
    def query(self, query: GraphQuery) -> GraphResult:
        entities = []
        relations = []
        
        # Filter entities
        for entity in self._entities.values():
            if query.entity_type and entity.type != query.entity_type:
                continue
            if query.entity_ids and entity.id not in query.entity_ids:
                continue
            # Apply filters
            matches = True
            for key, value in query.filters.items():
                if entity.properties.get(key) != value:
                    matches = False
                    break
            if not matches:
                continue
            entities.append(entity)
        
        # Filter relations
        for relation in self._relations:
            if query.relation_type and relation.relation_type != query.relation_type:
                continue
            # Include relations between matched entities
            if query.entity_ids:
                if relation.source_id not in query.entity_ids and \
                   relation.target_id not in query.entity_ids:
                    continue
            relations.append(relation)
        
        # Apply limit
        return GraphResult(
            entities=entities[:query.limit],
            relations=relations[:query.limit],
            metadata={"total_entities": len(entities), "total_relations": len(relations)},
        )
    
    def get_neighbors(
        self,
        entity_id: str,
        relation_type: RelationType | None = None,
        direction: str = "both",
    ) -> list[Entity]:
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
        relation_type: RelationType | None = None,
    ) -> list[Relation]:
        return [
            r for r in self._relations
            if r.source_id == entity_id and (relation_type is None or r.relation_type == relation_type)
        ]
    
    def get_incoming_relations(
        self,
        entity_id: str,
        relation_type: RelationType | None = None,
    ) -> list[Relation]:
        return [
            r for r in self._relations
            if r.target_id == entity_id and (relation_type is None or r.relation_type == relation_type)
        ]
    
    def search(
        self,
        entity_type: EntityType | None = None,
        text: str | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> list[Entity]:
        results = []
        filters = filters or {}
        
        for entity in self._entities.values():
            if entity_type and entity.type != entity_type:
                continue
            
            # Text search on name and description
            if text:
                name_match = text.lower() in entity.name.lower()
                desc_match = entity.description and text.lower() in entity.description.lower()
                if not name_match and not desc_match:
                    continue
            
            # Apply filters
            matches = True
            for key, value in filters.items():
                if entity.properties.get(key) != value:
                    matches = False
                    break
            if not matches:
                continue
            
            results.append(entity)
        
        return results[:limit]
    
    def count(self, entity_type: EntityType | None = None) -> int:
        if entity_type is None:
            return len(self._entities)
        return sum(1 for e in self._entities.values() if e.type == entity_type)
    
    def clear(self) -> None:
        self._entities.clear()
        self._relations.clear()


# Global graph instance
_global_graph: GraphDatabase | None = None


def get_graph() -> GraphDatabase:
    """Get the global graph database instance."""
    global _global_graph
    if _global_graph is None:
        _global_graph = InMemoryGraphDatabase()
    return _global_graph


def set_graph(graph: GraphDatabase) -> None:
    """Set the global graph database instance."""
    global _global_graph
    _global_graph = graph
