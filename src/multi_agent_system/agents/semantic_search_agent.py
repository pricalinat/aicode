"""Semantic embedding agent for vector-based similarity search."""

from __future__ import annotations

import hashlib
import json
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ..core.agent import AgentResponse, BaseAgent
from ..core.message import Message
from ..knowledge import Entity, EntityType, get_graph


class EmbeddingModel(ABC):
    """Abstract interface for embedding models."""
    
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Generate embedding vector for text."""
        pass
    
    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for multiple texts."""
        pass


class SimpleHashEmbedding(EmbeddingModel):
    """Simple hash-based embedding for development.
    
    Generates deterministic vectors based on text hash.
    Not suitable for production but useful for testing.
    """
    
    def __init__(self, dimension: int = 128) -> None:
        self.dimension = dimension
    
    def embed(self, text: str) -> list[float]:
        """Generate embedding from text hash."""
        # Use MD5 hash as seed
        hash_bytes = hashlib.md5(text.encode()).digest()
        
        # Convert to float values
        vector = []
        for i in range(self.dimension):
            # Use different parts of hash for different dimensions
            idx = (i * 4) % len(hash_bytes)
            value = float(hash_bytes[idx]) / 255.0
            # Add some variation
            value = value * 0.7 + 0.15 * math.sin(i + hash_bytes[idx] / 10)
            vector.append(value)
        
        # Normalize
        magnitude = math.sqrt(sum(v * v for v in vector))
        if magnitude > 0:
            vector = [v / magnitude for v in vector]
        
        return vector
    
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]


class VectorStore:
    """In-memory vector store for embeddings."""
    
    def __init__(self, embedding_model: EmbeddingModel) -> None:
        self.embedding_model = embedding_model
        self._vectors: dict[str, list[float]] = {}
        self._entities: dict[str, Entity] = {}
    
    def add(self, entity: Entity) -> None:
        """Add an entity to the vector store."""
        # Generate text representation
        text = self._entity_to_text(entity)
        
        # Generate embedding
        vector = self.embedding_model.embed(text)
        
        # Store
        self._vectors[entity.id] = vector
        self._entities[entity.id] = entity
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        entity_type: EntityType | None = None,
    ) -> list[tuple[Entity, float]]:
        """Search for similar entities."""
        # Generate query embedding
        query_vector = self.embedding_model.embed(query)
        
        # Calculate similarities
        results = []
        for entity_id, vector in self._vectors.items():
            if entity_id not in self._entities:
                continue
            
            entity = self._entities[entity_id]
            
            # Filter by entity type if specified
            if entity_type and entity.type != entity_type:
                continue
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_vector, vector)
            results.append((entity, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
    
    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(ai * bi for ai, bi in zip(a, b))
        magnitude_a = math.sqrt(sum(ai * ai for ai in a))
        magnitude_b = math.sqrt(sum(bi * bi for bi in b))
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        return dot_product / (magnitude_a * magnitude_b)
    
    def _entity_to_text(self, entity: Entity) -> str:
        """Convert entity to text for embedding."""
        parts = [entity.name]
        
        if entity.description:
            parts.append(entity.description)
        
        # Add properties as text
        for key, value in entity.properties.items():
            if isinstance(value, str):
                parts.append(value)
        
        return " ".join(parts)
    
    def delete(self, entity_id: str) -> bool:
        """Delete an entity from the vector store."""
        if entity_id in self._vectors:
            del self._vectors[entity_id]
            del self._entities[entity_id]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all entities."""
        self._vectors.clear()
        self._entities.clear()
    
    def count(self) -> int:
        """Get number of entities in store."""
        return len(self._vectors)


# Global vector store
_vector_store: VectorStore | None = None


def get_vector_store(embedding_model: EmbeddingModel | None = None) -> VectorStore:
    """Get the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        model = embedding_model or SimpleHashEmbedding()
        _vector_store = VectorStore(model)
    return _vector_store


def set_vector_store(store: VectorStore) -> None:
    """Set the global vector store instance."""
    global _vector_store
    _vector_store = store


class SemanticSearchAgent(BaseAgent):
    """Agent for semantic search using embeddings.
    
    Provides vector-based similarity search for products and services.
    """
    
    name = "semantic-search-agent"
    capabilities = {"semantic_search", "vector_search", "similarity_search"}
    
    def __init__(self, embedding_model: EmbeddingModel | None = None) -> None:
        self.vector_store = get_vector_store(embedding_model)
    
    def handle(self, message: Message) -> AgentResponse:
        try:
            query = message.content.get("query", "")
            top_k = message.content.get("top_k", 10)
            entity_type_str = message.content.get("entity_type")
            
            if not query:
                return AgentResponse(
                    agent=self.name,
                    success=False,
                    error="Missing 'query' in content",
                    trace_id=message.trace_id,
                )
            
            # Convert entity type
            entity_type = None
            if entity_type_str:
                try:
                    entity_type = EntityType(entity_type_str)
                except ValueError:
                    pass
            
            # Build index from graph if empty
            if self.vector_store.count() == 0:
                self._build_index_from_graph()
            
            # Search
            results = self.vector_store.search(
                query=query,
                top_k=top_k,
                entity_type=entity_type,
            )
            
            return AgentResponse(
                agent=self.name,
                success=True,
                data={
                    "query": query,
                    "results": [
                        {
                            "id": entity.id,
                            "type": entity.type.value,
                            "name": entity.name,
                            "description": entity.description,
                            "properties": entity.properties,
                            "similarity": round(similarity, 4),
                        }
                        for entity, similarity in results
                    ],
                    "total": len(results),
                },
                trace_id=message.trace_id,
            )
            
        except Exception as exc:
            return AgentResponse(
                agent=self.name,
                success=False,
                error=str(exc),
                trace_id=message.trace_id,
            )
    
    def _build_index_from_graph(self) -> None:
        """Build vector index from knowledge graph."""
        graph = get_graph()
        
        # Index products
        products = graph.search(entity_type=EntityType.PRODUCT, limit=1000)
        for product in products:
            self.vector_store.add(product)
        
        # Index services
        services = graph.search(entity_type=EntityType.SERVICE, limit=1000)
        for service in services:
            self.vector_store.add(service)
        
        # Index merchants
        merchants = graph.search(entity_type=EntityType.MERCHANT, limit=1000)
        for merchant in merchants:
            self.vector_store.add(merchant)
