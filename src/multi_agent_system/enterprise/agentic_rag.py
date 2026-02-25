"""Agentic RAG System based on "Retrieval Augmented Generation for Fintech: Agentic Design".

Reference: Agentic RAG systems where the LLM actively decides when and how to retrieve knowledge.
Features: autonomous retrieval, multi-source, self-verification, iterative refinement.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class RetrievalStrategy(Enum):
    """Retrieval strategy types."""
    SEMANTIC = "semantic"  # Vector similarity
    KEYWORD = "keyword"    # BM25/keyword match
    HYBRID = "hybrid"      # Combination
    AUTO = "auto"          # Let agent decide


class RelevanceLevel(Enum):
    """Relevance level of retrieved content."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class KnowledgeSource:
    """A knowledge source for RAG."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    source_type: str = ""  # "document", "api", "database", "web"
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None
    created_at: datetime = field(default_factory=datetime.now)

    def relevance_score(self, query_embedding: list[float]) -> float:
        """Calculate relevance score to query."""
        if not self.embedding or not query_embedding:
            return 0.0

        # Cosine similarity
        dot = sum(a * b for a, b in zip(self.embedding, query_embedding))
        mag_a = sum(a * a for a in self.embedding) ** 0.5
        mag_b = sum(b * b for b in query_embedding) ** 0.5

        if mag_a == 0 or mag_b == 0:
            return 0.0

        return dot / (mag_a * mag_b)


@dataclass
class RetrievedChunk:
    """A retrieved knowledge chunk."""
    source_id: str = ""
    source_name: str = ""
    content: str = ""
    relevance_score: float = 0.0
    relevance_level: RelevanceLevel = RelevanceLevel.LOW
    metadata: dict[str, Any] = field(default_factory=dict)
    verified: bool = False  # Whether content was verified

    def is_relevant(self, threshold: float = 0.5) -> bool:
        """Check if chunk is relevant."""
        return self.relevance_score >= threshold


@dataclass
class RetrievalQuery:
    """A retrieval query with metadata."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    strategy: RetrievalStrategy = RetrievalStrategy.AUTO
    top_k: int = 5
    min_relevance: float = 0.3
    filters: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class RetrievalResult:
    """Result of a retrieval operation."""
    query_id: str = ""
    chunks: list[RetrievedChunk] = field(default_factory=list)
    total_sources: int = 0
    verified_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def get_relevant_chunks(self, threshold: float = 0.3) -> list[RetrievedChunk]:
        """Get chunks above relevance threshold."""
        return [c for c in self.chunks if c.is_relevant(threshold)]

    def summary(self) -> dict[str, Any]:
        """Get summary of retrieval result."""
        return {
            "total_chunks": len(self.chunks),
            "relevant_chunks": len(self.get_relevant_chunks()),
            "verified_count": self.verified_count,
            "avg_relevance": sum(c.relevance_score for c in self.chunks) / len(self.chunks) if self.chunks else 0,
        }


class KnowledgeBase:
    """Knowledge base for agent retrieval.

    Manages multiple knowledge sources with different types.
    """

    def __init__(self) -> None:
        """Initialize knowledge base."""
        self._sources: dict[str, KnowledgeSource] = {}
        self._sources_by_type: dict[str, set[str]] = {}

    def add_source(self, source: KnowledgeSource) -> None:
        """Add a knowledge source."""
        self._sources[source.id] = source

        if source.source_type not in self._sources_by_type:
            self._sources_by_type[source.source_type] = set()
        self._sources_by_type[source.source_type].add(source.id)

    def get_source(self, source_id: str) -> KnowledgeSource | None:
        """Get source by ID."""
        return self._sources.get(source_id)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        source_types: list[str] | None = None,
    ) -> list[RetrievedChunk]:
        """Search knowledge base by embedding.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results
            source_types: Filter by source types

        Returns:
            List of retrieved chunks
        """
        candidates = []

        for source_id, source in self._sources.items():
            # Filter by type
            if source_types and source.source_type not in source_types:
                continue

            score = source.relevance_score(query_embedding)
            if score > 0:
                chunk = RetrievedChunk(
                    source_id=source.id,
                    source_name=source.name,
                    content=source.content[:1000],  # Truncate for efficiency
                    relevance_score=score,
                    relevance_level=self._classify_relevance(score),
                    metadata=source.metadata,
                )
                candidates.append(chunk)

        # Sort by relevance
        candidates.sort(key=lambda c: c.relevance_score, reverse=True)
        return candidates[:top_k]

    def _classify_relevance(self, score: float) -> RelevanceLevel:
        """Classify relevance level."""
        if score >= 0.7:
            return RelevanceLevel.HIGH
        elif score >= 0.4:
            return RelevanceLevel.MEDIUM
        return RelevanceLevel.LOW

    def count(self) -> int:
        """Get total source count."""
        return len(self._sources)

    def list_types(self) -> list[str]:
        """List available source types."""
        return list(self._sources_by_type.keys())


class AgenticRAG:
    """Agentic RAG system with autonomous retrieval capabilities.

    Features:
    - Autonomous query analysis and reformulation
    - Multi-source retrieval
    - Self-verification of retrieved content
    - Iterative refinement
    """

    def __init__(
        self,
        knowledge_base: KnowledgeBase | None = None,
        embedding_model: Any = None,
    ) -> None:
        """Initialize Agentic RAG.

        Args:
            knowledge_base: Knowledge base to query
            embedding_model: Model for generating embeddings
        """
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self._embedding_model = embedding_model
        self._retrieval_history: list[RetrievalResult] = []

    def _embed(self, text: str) -> list[float]:
        """Generate embedding for text."""
        if self._embedding_model:
            return self._embedding_model.embed(text)
        # Simple hash fallback
        import hashlib
        h = hashlib.md5(text.encode()).digest()
        return [float(b) / 255.0 for b in h[:32]]

    async def retrieve(
        self,
        query: str,
        strategy: RetrievalStrategy = RetrievalStrategy.AUTO,
        top_k: int = 5,
        verify: bool = True,
    ) -> RetrievalResult:
        """Retrieve knowledge for a query.

        Args:
            query: User query
            strategy: Retrieval strategy
            top_k: Number of chunks to retrieve
            verify: Whether to verify retrieved content

        Returns:
            Retrieval result
        """
        # Generate query embedding
        query_embedding = self._embed(query)

        # Determine strategy
        actual_strategy = strategy
        if strategy == RetrievalStrategy.AUTO:
            actual_strategy = self._choose_strategy(query)

        # Retrieve based on strategy
        chunks = []
        if actual_strategy == RetrievalStrategy.SEMANTIC:
            chunks = self.knowledge_base.search(query_embedding, top_k)
        # For now, hybrid falls back to semantic
        elif actual_strategy == RetrievalStrategy.HYBRID:
            chunks = self.knowledge_base.search(query_embedding, top_k * 2)

        # Verify if requested
        if verify:
            chunks = await self._verify_chunks(query, chunks)

        result = RetrievalResult(
            query_id=str(uuid.uuid4()),
            chunks=chunks,
            total_sources=self.knowledge_base.count(),
            verified_count=sum(1 for c in chunks if c.verified),
        )

        self._retrieval_history.append(result)
        return result

    def _choose_strategy(self, query: str) -> RetrievalStrategy:
        """Choose best retrieval strategy based on query."""
        query_lower = query.lower()

        # If query has specific keywords, use hybrid
        if any(kw in query_lower for kw in ["find", "list", "show", "what is", "how many"]):
            return RetrievalStrategy.HYBRID

        # If query is conceptual, use semantic
        if any(kw in query_lower for kw in ["explain", "why", "how does", "concept", "understanding"]):
            return RetrievalStrategy.SEMANTIC

        return RetrievalStrategy.HYBRID

    async def _verify_chunks(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """Verify relevance of retrieved chunks.

        In production, this would use an LLM to verify.
        For now, uses simple heuristics.
        """
        query_terms = set(query.lower().split())

        for chunk in chunks:
            chunk_terms = set(chunk.content.lower().split())
            overlap = len(query_terms & chunk_terms)

            # Verify if there's sufficient term overlap
            if overlap >= 2:
                chunk.verified = True
            else:
                # Keep but mark unverified
                chunk.verified = False

        return chunks

    async def retrieve_iterative(
        self,
        query: str,
        max_iterations: int = 3,
    ) -> RetrievalResult:
        """Iteratively refine retrieval.

        Args:
            query: Initial query
            max_iterations: Maximum refinement iterations

        Returns:
            Final retrieval result
        """
        current_query = query
        all_chunks: list[RetrievedChunk] = []

        for _ in range(max_iterations):
            result = await self.retrieve(current_query, top_k=5, verify=True)

            # Add new relevant chunks
            for chunk in result.get_relevant_chunks(0.4):
                if not any(c.source_id == chunk.source_id for c in all_chunks):
                    all_chunks.append(chunk)

            # If we have enough relevant chunks, stop
            if len(all_chunks) >= 5:
                break

            # Expand query with context from results
            if result.chunks:
                # Use top chunk to expand query
                top_chunk = result.chunks[0]
                # In production, use LLM to generate expanded query
                # Here, just add some context
                current_query = f"{query} {top_chunk.content[:100]}"

        return RetrievalResult(
            query_id=str(uuid.uuid4()),
            chunks=all_chunks[:10],
            total_sources=self.knowledge_base.count(),
            verified_count=sum(1 for c in all_chunks if c.verified),
        )

    def get_history(self) -> list[RetrievalResult]:
        """Get retrieval history."""
        return self._retrieval_history

    def add_knowledge(
        self,
        name: str,
        content: str,
        source_type: str = "document",
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeSource:
        """Add knowledge to the base.

        Args:
            name: Source name
            content: Content to add
            source_type: Type of source
            metadata: Additional metadata

        Returns:
            Created knowledge source
        """
        embedding = self._embed(content)

        source = KnowledgeSource(
            name=name,
            source_type=source_type,
            content=content,
            metadata=metadata or {},
            embedding=embedding,
        )

        self.knowledge_base.add_source(source)
        return source


# Global instance
_agentic_rag: AgenticRAG | None = None


def get_agentic_rag(
    knowledge_base: KnowledgeBase | None = None,
    embedding_model: Any = None,
) -> AgenticRAG:
    """Get global Agentic RAG instance."""
    global _agentic_rag
    if _agentic_rag is None:
        _agentic_rag = AgenticRAG(knowledge_base, embedding_model)
    return _agentic_rag
