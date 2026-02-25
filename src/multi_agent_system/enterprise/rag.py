"""RAG (Retrieval-Augmented Generation) knowledge augmentation.

Combines vector search, knowledge graph, and paper repository.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RetrievedChunk:
    """A retrieved knowledge chunk."""

    id: str
    content: str
    source: str  # "arxiv", "knowledge_graph", "papers", "web"
    score: float  # Relevance score
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievedContext:
    """Complete retrieved context."""

    query: str
    chunks: list[RetrievedChunk] = field(default_factory=list)
    total_chunks: int = 0

    def to_prompt(self) -> str:
        """Convert to prompt context."""
        if not self.chunks:
            return "No relevant context found."

        context_parts = ["=== Relevant Context ==="]
        for i, chunk in enumerate(self.chunks, 1):
            context_parts.append(f"\n[Source: {chunk.source}, Relevance: {chunk.score:.2f}]")
            context_parts.append(chunk.content)

        return "\n".join(context_parts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "chunks": [
                {"id": c.id, "content": c.content[:100] + "...", "source": c.source, "score": c.score}
                for c in self.chunks
            ],
            "total_chunks": self.total_chunks,
        }


class KnowledgeSource(ABC):
    """Abstract knowledge source."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        """Retrieve relevant chunks."""
        pass


class VectorStoreSource(KnowledgeSource):
    """Vector store based retrieval."""

    def __init__(self, vector_store: Any = None) -> None:
        self.vector_store = vector_store

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        """Retrieve from vector store."""
        # Placeholder - would integrate with actual vector store
        return []


class PaperRepositorySource(KnowledgeSource):
    """Paper repository based retrieval."""

    def __init__(self, papers_file: str = "./data/papers.json") -> None:
        self.papers_file = Path(papers_file)
        self._papers: list[dict] = []
        self._load()

    def _load(self) -> None:
        """Load papers."""
        if self.papers_file.exists():
            with open(self.papers_file) as f:
                self._papers = json.load(f)

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        """Retrieve from paper repository."""
        query_lower = query.lower()
        results = []

        # Simple keyword matching (would use vector store in production)
        for paper in self._papers:
            score = 0.0
            text = (
                paper.get("title", "")
                + " "
                + paper.get("summary", "")
                + " "
                + " ".join(paper.get("authors", []))
            ).lower()

            # Calculate simple relevance score
            query_words = query_lower.split()
            for word in query_words:
                if word in text:
                    score += 1.0

            if score > 0:
                content = f"Title: {paper.get('title')}\nAuthors: {', '.join(paper.get('authors', []))}\nAbstract: {paper.get('summary', '')[:300]}..."
                results.append(
                    RetrievedChunk(
                        id=paper.get("id", ""),
                        content=content,
                        source="papers",
                        score=score,
                        metadata={"published": paper.get("published"), "categories": paper.get("categories", [])},
                    )
                )

        # Sort by score and return top_k
        results.sort(key=lambda x: -x.score)
        return results[:top_k]


class KnowledgeGraphSource(KnowledgeSource):
    """Knowledge graph based retrieval."""

    def __init__(self, graph_data_file: str = "./data/entities.json") -> None:
        self.graph_file = Path(graph_data_file)
        self._entities: list[dict] = []
        self._load()

    def _load(self) -> None:
        """Load entities."""
        if self.graph_file.exists():
            with open(self.graph_file) as f:
                self._entities = json.load(f)

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        """Retrieve from knowledge graph."""
        query_lower = query.lower()
        results = []

        for entity in self._entities:
            score = 0.0
            text = (entity.get("name", "") + " " + entity.get("description", "")).lower()

            query_words = query_lower.split()
            for word in query_words:
                if word in text:
                    score += 1.0

            if score > 0:
                results.append(
                    RetrievedChunk(
                        id=entity.get("id", ""),
                        content=f"{entity.get('name')}: {entity.get('description', '')}",
                        source="knowledge_graph",
                        score=score,
                        metadata={"type": entity.get("type")},
                    )
                )

        results.sort(key=lambda x: -x.score)
        return results[:top_k]


class KnowledgeAugmentation:
    """Multi-source knowledge augmentation system.

    Combines vector search, knowledge graph, and paper repository.
    """

    def __init__(self) -> None:
        self.sources: dict[str, KnowledgeSource] = {}
        self._register_default_sources()

    def _register_default_sources(self) -> None:
        """Register default knowledge sources."""
        # Paper repository
        if Path("./data/papers.json").exists():
            self.register_source("papers", PaperRepositorySource())

        # Knowledge graph
        if Path("./data/entities.json").exists():
            self.register_source("knowledge_graph", KnowledgeGraphSource())

    def register_source(self, name: str, source: KnowledgeSource) -> None:
        """Register a knowledge source."""
        self.sources[name] = source

    def retrieve(
        self,
        query: str,
        sources: list[str] | None = None,
        top_k: int = 5,
    ) -> RetrievedContext:
        """Retrieve context from multiple sources.

        Args:
            query: Search query
            sources: List of source names to use (None = all)
            top_k: Number of results per source

        Returns:
            RetrievedContext with combined results
        """
        if sources is None:
            sources = list(self.sources.keys())

        all_chunks: list[RetrievedChunk] = []

        for source_name in sources:
            source = self.sources.get(source_name)
            if source:
                chunks = source.retrieve(query, top_k)
                all_chunks.extend(chunks)

        # Merge and re-rank (simple score-based)
        all_chunks.sort(key=lambda x: -x.score)

        return RetrievedContext(query=query, chunks=all_chunks[:top_k * len(sources)], total_chunks=len(all_chunks))

    def augment_prompt(self, query: str, prompt: str, max_context: int = 2000) -> str:
        """Augment a prompt with retrieved context.

        Args:
            query: Original query
            prompt: Original prompt
            max_context: Max context characters

        Returns:
            Augmented prompt
        """
        context = self.retrieve(query)

        if not context.chunks:
            return prompt

        # Build augmented prompt
        augmented = f"{prompt}\n\n{context.to_prompt()}"

        # Truncate if too long
        if len(augmented) > max_context:
            augmented = augmented[:max_context] + "\n...(truncated)"

        return augmented

    def get_sources_status(self) -> dict[str, Any]:
        """Get status of all sources."""
        status = {}
        for name, source in self.sources.items():
            status[name] = {"registered": True, "type": type(source).__name__}
        return status


# Global instance
_knowledge_augmentation: KnowledgeAugmentation | None = None


def get_knowledge_augmentation() -> KnowledgeAugmentation:
    """Get global knowledge augmentation instance."""
    global _knowledge_augmentation
    if _knowledge_augmentation is None:
        _knowledge_augmentation = KnowledgeAugmentation()
    return _knowledge_augmentation
