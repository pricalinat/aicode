"""Data persistence layer for graph and agent state."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..knowledge import Entity, EntityType, Relation, RelationType, get_graph


class PersistenceBackend(ABC):
    """Abstract interface for persistence backends."""
    
    @abstractmethod
    def save_entities(self, entities: list[Entity]) -> None:
        """Save entities to storage."""
        pass
    
    @abstractmethod
    def load_entities(self) -> list[Entity]:
        """Load entities from storage."""
        pass
    
    @abstractmethod
    def save_relations(self, relations: list[Relation]) -> None:
        """Save relations to storage."""
        pass
    
    @abstractmethod
    def load_relations(self) -> list[Relation]:
        """Load relations from storage."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all data."""
        pass


class JSONFileBackend(PersistenceBackend):
    """JSON file-based persistence."""
    
    def __init__(self, data_dir: str = "./data") -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.entities_file = self.data_dir / "entities.json"
        self.relations_file = self.data_dir / "relations.json"
    
    def save_entities(self, entities: list[Entity]) -> None:
        data = [
            {
                "id": e.id,
                "type": e.type.value,
                "properties": e.properties,
            }
            for e in entities
        ]
        with open(self.entities_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_entities(self) -> list[Entity]:
        if not self.entities_file.exists():
            return []
        
        with open(self.entities_file, encoding="utf-8") as f:
            data = json.load(f)
        
        entities = []
        for item in data:
            try:
                entities.append(Entity(
                    id=item["id"],
                    type=EntityType(item["type"]),
                    properties=item.get("properties", {}),
                ))
            except (KeyError, ValueError):
                continue
        
        return entities
    
    def save_relations(self, relations: list[Relation]) -> None:
        data = [
            {
                "source_id": r.source_id,
                "target_id": r.target_id,
                "relation_type": r.relation_type.value,
                "properties": r.properties,
            }
            for r in relations
        ]
        with open(self.relations_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_relations(self) -> list[Relation]:
        if not self.relations_file.exists():
            return []
        
        with open(self.relations_file, encoding="utf-8") as f:
            data = json.load(f)
        
        relations = []
        for item in data:
            try:
                relations.append(Relation(
                    source_id=item["source_id"],
                    target_id=item["target_id"],
                    relation_type=RelationType(item["relation_type"]),
                    properties=item.get("properties", {}),
                ))
            except (KeyError, ValueError):
                continue
        
        return relations
    
    def clear(self) -> None:
        if self.entities_file.exists():
            self.entities_file.unlink()
        if self.relations_file.exists():
            self.relations_file.unlink()


class GraphPersistence:
    """Manager for persisting graph data."""
    
    def __init__(self, backend: PersistenceBackend | None = None) -> None:
        self.backend = backend or JSONFileBackend()
    
    def save(self) -> None:
        """Save current graph state to backend."""
        graph = get_graph()
        
        # We need to get all entities - this is a workaround
        # In production, GraphDatabase should have a get_all method
        entities = []
        for etype in EntityType:
            entities.extend(graph.search(entity_type=etype, limit=10000))
        
        # Remove duplicates
        seen = set()
        unique_entities = []
        for e in entities:
            if e.id not in seen:
                seen.add(e.id)
                unique_entities.append(e)
        
        self.backend.save_entities(unique_entities)
        
        # For relations, we need to add a method to graph
        # This is a simplified version
        relations = []
        self.backend.save_relations(relations)
    
    def load(self) -> None:
        """Load graph state from backend."""
        graph = get_graph()
        
        # Clear existing
        graph.clear()
        
        # Load entities
        entities = self.backend.load_entities()
        for entity in entities:
            try:
                graph.create_entity(entity)
            except ValueError:
                # Already exists
                pass
        
        # Load relations
        relations = self.backend.load_relations()
        for relation in relations:
            try:
                graph.create_relation(relation)
            except Exception:
                pass
    
    def clear(self) -> None:
        """Clear all data."""
        self.backend.clear()
        get_graph().clear()


# Global persistence manager
_persistence: GraphPersistence | None = None


def get_persistence(backend: PersistenceBackend | None = None) -> GraphPersistence:
    """Get the global persistence manager."""
    global _persistence
    if _persistence is None:
        _persistence = GraphPersistence(backend)
    return _persistence
