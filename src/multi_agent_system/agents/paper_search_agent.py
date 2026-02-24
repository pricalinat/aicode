"""Paper search agent with vector-based semantic retrieval."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from ..core.agent import AgentResponse, BaseAgent
from ..core.message import Message
from ..knowledge.paper import Paper
from .semantic_search_agent import EmbeddingModel, SimpleHashEmbedding


class PaperRepository:
    """Paper repository with JSON file storage."""

    def __init__(self, data_dir: str = "./data") -> None:
        self.data_dir = Path(data_dir)
        self.papers_file = self.data_dir / "papers.json"
        self._papers: dict[str, Paper] = {}

    def _ensure_data_dir(self) -> None:
        """Ensure data directory exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def save_papers(self, papers: list[Paper]) -> int:
        """Save papers to repository. Returns count of new papers added."""
        self._load_papers()
        count = 0
        for paper in papers:
            if paper.id not in self._papers:
                self._papers[paper.id] = paper
                count += 1
        if count > 0:
            self._save_papers()
        return count

    def _save_papers(self) -> None:
        """Save papers to JSON file."""
        self._ensure_data_dir()
        data = [paper.to_dict() for paper in self._papers.values()]
        with open(self.papers_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_papers(self) -> None:
        """Load papers from JSON file."""
        if not self.papers_file.exists():
            self._papers = {}
            return

        with open(self.papers_file, encoding="utf-8") as f:
            data = json.load(f)

        self._papers = {}
        for item in data:
            paper = Paper.from_dict(item)
            self._papers[paper.id] = paper

    def load_papers(self) -> list[Paper]:
        """Load all papers from repository."""
        self._load_papers()
        return list(self._papers.values())

    def get_paper(self, paper_id: str) -> Paper | None:
        """Get paper by ID."""
        self._load_papers()
        return self._papers.get(paper_id)

    def delete_paper(self, paper_id: str) -> bool:
        """Delete paper by ID."""
        self._load_papers()
        if paper_id in self._papers:
            del self._papers[paper_id]
            self._save_papers()
            return True
        return False

    def clear(self) -> None:
        """Clear all papers."""
        self._papers = {}
        self._ensure_data_dir()
        if self.papers_file.exists():
            self.papers_file.unlink()

    def count(self) -> int:
        """Get count of papers."""
        self._load_papers()
        return len(self._papers)

    def filter_by_category(self, category: str) -> list[Paper]:
        """Filter papers by category."""
        papers = self.load_papers()
        return [p for p in papers if p.matches_category(category)]

    def filter_by_year(self, year: int) -> list[Paper]:
        """Filter papers by year."""
        papers = self.load_papers()
        return [p for p in papers if p.matches_year(year)]

    def filter_by_author(self, author: str) -> list[Paper]:
        """Filter papers by author."""
        papers = self.load_papers()
        return [p for p in papers if p.matches_author(author)]


class PaperVectorStore:
    """Vector store for paper semantic search."""

    def __init__(self, embedding_model: EmbeddingModel | None = None) -> None:
        self.embedding_model = embedding_model or SimpleHashEmbedding()
        self._vectors: dict[str, list[float]] = {}
        self._papers: dict[str, Paper] = {}

    def add_paper(self, paper: Paper) -> None:
        """Add a paper to the vector store."""
        # Generate text representation for embedding
        text = self._paper_to_text(paper)

        # Generate embedding
        vector = self.embedding_model.embed(text)

        # Store
        self._vectors[paper.id] = vector
        self._papers[paper.id] = paper

    def build_index(self, papers: list[Paper]) -> None:
        """Build index from list of papers."""
        self._vectors.clear()
        self._papers.clear()
        for paper in papers:
            self.add_paper(paper)

    def search(
        self,
        query: str,
        top_k: int = 10,
        category: str | None = None,
        year: int | None = None,
    ) -> list[tuple[Paper, float]]:
        """Search for similar papers."""
        # Generate query embedding
        query_vector = self.embedding_model.embed(query)

        # Calculate similarities
        results = []
        for paper_id, vector in self._vectors.items():
            paper = self._papers[paper_id]

            # Filter by category if specified
            if category and not paper.matches_category(category):
                continue

            # Filter by year if specified
            if year and not paper.matches_year(year):
                continue

            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_vector, vector)
            results.append((paper, similarity))

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

    def _paper_to_text(self, paper: Paper) -> str:
        """Convert paper to text for embedding."""
        parts = [paper.title, paper.summary]
        parts.extend(paper.authors)
        parts.extend(paper.categories)
        return " ".join(parts)

    def count(self) -> int:
        """Get number of papers in store."""
        return len(self._vectors)


# Global instances
_paper_repository: PaperRepository | None = None
_paper_vector_store: PaperVectorStore | None = None


def get_paper_repository(data_dir: str = "./data") -> PaperRepository:
    """Get global paper repository instance."""
    global _paper_repository
    if _paper_repository is None:
        _paper_repository = PaperRepository(data_dir)
    return _paper_repository


def get_paper_vector_store() -> PaperVectorStore:
    """Get global paper vector store instance."""
    global _paper_vector_store
    if _paper_vector_store is None:
        _paper_vector_store = PaperVectorStore()
    return _paper_vector_store


def set_paper_vector_store(store: PaperVectorStore) -> None:
    """Set global paper vector store instance."""
    global _paper_vector_store
    _paper_vector_store = store


class PaperSearchAgent(BaseAgent):
    """Agent for paper search and retrieval."""

    name = "paper-search-agent"
    capabilities = {"search_papers", "find_papers", "paper_retrieval", "list_papers"}

    def __init__(
        self,
        data_dir: str = "./data",
        embedding_model: EmbeddingModel | None = None,
    ) -> None:
        self.repository = get_paper_repository(data_dir)
        self.vector_store = get_paper_vector_store()
        if embedding_model:
            self.vector_store = PaperVectorStore(embedding_model)

    def handle(self, message: Message) -> AgentResponse:
        try:
            action = message.content.get("action", "search")

            if action == "search":
                return self._handle_search(message)
            elif action == "list":
                return self._handle_list(message)
            elif action == "save":
                return self._handle_save(message)
            elif action == "count":
                return self._handle_count(message)
            elif action == "clear":
                return self._handle_clear(message)
            else:
                return AgentResponse(
                    agent=self.name,
                    success=False,
                    error=f"Unknown action: {action}",
                    trace_id=message.trace_id,
                )

        except Exception as exc:
            return AgentResponse(
                agent=self.name,
                success=False,
                error=str(exc),
                trace_id=message.trace_id,
            )

    def _handle_search(self, message: Message) -> AgentResponse:
        """Handle paper search request."""
        query = message.content.get("query", "")
        top_k = message.content.get("top_k", 10)
        category = message.content.get("category")
        year = message.content.get("year")

        if not query:
            return AgentResponse(
                agent=self.name,
                success=False,
                error="Missing 'query' in content",
                trace_id=message.trace_id,
            )

        # Load papers into vector store if empty
        if self.vector_store.count() == 0:
            papers = self.repository.load_papers()
            self.vector_store.build_index(papers)

        # Search
        results = self.vector_store.search(
            query=query,
            top_k=top_k,
            category=category,
            year=year,
        )

        return AgentResponse(
            agent=self.name,
            success=True,
            data={
                "query": query,
                "results": [
                    {
                        "id": paper.id,
                        "title": paper.title,
                        "authors": paper.authors,
                        "published": paper.published,
                        "primary_category": paper.primary_category,
                        "pdf_url": paper.pdf_url,
                        "similarity": round(similarity, 4),
                    }
                    for paper, similarity in results
                ],
                "total": len(results),
            },
            trace_id=message.trace_id,
        )

    def _handle_list(self, message: Message) -> AgentResponse:
        """Handle list papers request."""
        category = message.content.get("category")
        year = message.content.get("year")
        author = message.content.get("author")
        limit = message.content.get("limit", 100)

        papers = self.repository.load_papers()

        # Apply filters
        if category:
            papers = [p for p in papers if p.matches_category(category)]
        if year:
            papers = [p for p in papers if p.matches_year(year)]
        if author:
            papers = [p for p in papers if p.matches_author(author)]

        papers = papers[:limit]

        return AgentResponse(
            agent=self.name,
            success=True,
            data={
                "papers": [
                    {
                        "id": paper.id,
                        "title": paper.title,
                        "authors": paper.authors,
                        "published": paper.published,
                        "primary_category": paper.primary_category,
                        "categories": paper.categories,
                        "pdf_url": paper.pdf_url,
                    }
                    for paper in papers
                ],
                "total": len(papers),
            },
            trace_id=message.trace_id,
        )

    def _handle_save(self, message: Message) -> AgentResponse:
        """Handle save papers request."""
        papers_data = message.content.get("papers", [])

        if not papers_data:
            return AgentResponse(
                agent=self.name,
                success=False,
                error="Missing 'papers' in content",
                trace_id=message.trace_id,
            )

        papers = [Paper.from_dict(p) for p in papers_data]
        count = self.repository.save_papers(papers)

        # Rebuild vector index
        all_papers = self.repository.load_papers()
        self.vector_store.build_index(all_papers)

        return AgentResponse(
            agent=self.name,
            success=True,
            data={
                "saved": count,
                "total": len(all_papers),
            },
            trace_id=message.trace_id,
        )

    def _handle_count(self, message: Message) -> AgentResponse:
        """Handle count papers request."""
        count = self.repository.count()

        return AgentResponse(
            agent=self.name,
            success=True,
            data={"count": count},
            trace_id=message.trace_id,
        )

    def _handle_clear(self, message: Message) -> AgentResponse:
        """Handle clear papers request."""
        self.repository.clear()
        self.vector_store.clear()

        return AgentResponse(
            agent=self.name,
            success=True,
            data={"message": "All papers cleared"},
            trace_id=message.trace_id,
        )
