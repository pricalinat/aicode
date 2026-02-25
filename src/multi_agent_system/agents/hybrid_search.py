"""Hybrid paper retrieval combining semantic and keyword search."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from ..knowledge.paper import Paper
from .embedding import BM25KeywordSearch, SentenceTransformerEmbedding
from .semantic_search_agent import EmbeddingModel, SimpleHashEmbedding


class HybridPaperVectorStore:
    """Hybrid vector store combining semantic and keyword search.

    Uses reciprocal rank fusion to combine results from:
    1. Semantic search (sentence-transformers embeddings)
    2. Keyword search (BM25)
    """

    def __init__(
        self,
        embedding_model: EmbeddingModel | None = None,
        use_semantic: bool = True,
        use_keyword: bool = True,
        semantic_weight: float = 0.6,
        keyword_weight: float = 0.4,
    ) -> None:
        """Initialize hybrid store.

        Args:
            embedding_model: Semantic embedding model (uses SentenceTransformer if None)
            use_semantic: Enable semantic search
            use_keyword: Enable keyword search
            semantic_weight: Weight for semantic scores (0-1)
            keyword_weight: Weight for keyword scores (0-1)
        """
        self._embedding_model = embedding_model
        self._semantic_model = None
        self._use_semantic = use_semantic
        self._use_keyword = use_keyword

        # Normalize weights
        total = semantic_weight + keyword_weight
        self._semantic_weight = semantic_weight / total if total > 0 else 0.5
        self._keyword_weight = keyword_weight / total if total > 0 else 0.5

        self._vectors: dict[str, list[float]] = {}
        self._papers: dict[str, Paper] = {}
        self._bm25 = BM25KeywordSearch()

    def _get_semantic_model(self) -> EmbeddingModel:
        """Get or create semantic model."""
        if self._semantic_model is None:
            if self._embedding_model is not None:
                self._semantic_model = self._embedding_model
            else:
                # Try to use sentence-transformers, fall back to simple
                try:
                    self._semantic_model = SentenceTransformerEmbedding()
                except ImportError:
                    self._semantic_model = SimpleHashEmbedding()
        return self._semantic_model

    def add_paper(self, paper: Paper) -> None:
        """Add a paper to the store."""
        # Semantic indexing
        if self._use_semantic:
            text = self._paper_to_text(paper)
            vector = self._get_semantic_model().embed(text)
            self._vectors[paper.id] = vector
            self._papers[paper.id] = paper

        # Keyword indexing
        if self._use_keyword:
            text = self._paper_to_text(paper)
            self._bm25.add_document(paper.id, text)

    def build_index(self, papers: list[Paper]) -> None:
        """Build index from list of papers."""
        self._vectors.clear()
        self._papers.clear()
        self._bm25 = BM25KeywordSearch()

        for paper in papers:
            self.add_paper(paper)

    def search(
        self,
        query: str,
        top_k: int = 10,
        category: str | None = None,
        year: int | None = None,
        min_score: float = 0.0,
    ) -> list[tuple[Paper, float]]:
        """Search for similar papers using hybrid approach.

        Args:
            query: Search query
            top_k: Maximum results to return
            category: Filter by category
            year: Filter by year
            min_score: Minimum score threshold

        Returns:
            List of (Paper, score) tuples sorted by score
        """
        # Get candidate papers
        candidate_ids = self._get_candidate_ids(category, year)

        # Semantic search
        semantic_scores: dict[str, float] = {}
        if self._use_semantic and self._vectors:
            try:
                query_vector = self._get_semantic_model().embed(query)
                for paper_id in candidate_ids:
                    if paper_id not in self._vectors:
                        continue
                    sim = self._cosine_similarity(query_vector, self._vectors[paper_id])
                    semantic_scores[paper_id] = sim
            except Exception:
                pass

        # Keyword search
        keyword_scores: dict[str, float] = {}
        if self._use_keyword and self._bm25.count() > 0:
            keyword_results = self._bm25.search(query, candidate_ids)
            keyword_scores = {doc_id: score for doc_id, score in keyword_results}

        # Normalize scores to 0-1 range
        semantic_scores = self._normalize_scores(semantic_scores)
        keyword_scores = self._normalize_scores(keyword_scores)

        # Combine scores using weighted sum
        combined_scores: dict[str, float] = {}
        all_ids = set(semantic_scores.keys()) | set(keyword_scores.keys())

        for paper_id in all_ids:
            sem_score = semantic_scores.get(paper_id, 0.0)
            key_score = keyword_scores.get(paper_id, 0.0)
            combined = (sem_score * self._semantic_weight + key_score * self._keyword_weight)
            combined_scores[paper_id] = combined

        # Filter and sort
        results = [
            (self._papers[pid], score)
            for pid, score in combined_scores.items()
            if score >= min_score
        ]
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def _get_candidate_ids(self, category: str | None, year: int | None) -> list[str]:
        """Get candidate paper IDs based on filters."""
        if category is None and year is None:
            return list(self._papers.keys())

        candidates = []
        for paper_id, paper in self._papers.items():
            if category and not paper.matches_category(category):
                continue
            if year and not paper.matches_year(year):
                continue
            candidates.append(paper_id)
        return candidates

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Calculate cosine similarity."""
        dot_product = sum(ai * bi for ai, bi in zip(a, b))
        mag_a = math.sqrt(sum(ai * ai for ai in a))
        mag_b = math.sqrt(sum(bi * bi for bi in b))

        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot_product / (mag_a * mag_b)

    def _normalize_scores(self, scores: dict[str, float]) -> dict[str, float]:
        """Normalize scores to 0-1 range."""
        if not scores:
            return {}

        max_score = max(scores.values())
        min_score = min(scores.values())

        if max_score == min_score:
            return {k: 1.0 for k in scores}

        return {
            k: (v - min_score) / (max_score - min_score)
            for k, v in scores.items()
        }

    def _paper_to_text(self, paper: Paper) -> str:
        """Convert paper to text for indexing."""
        parts = [paper.title, paper.summary]
        parts.extend(paper.authors)
        parts.extend(paper.categories)
        return " ".join(parts)

    def count(self) -> int:
        """Get number of papers in store."""
        return len(self._papers)


class SmartQueryExpander:
    """Query expansion using synonyms and related concepts.

    Expands user queries to improve recall.
    """

    # Common multi-agent system related expansions
    EXPANSIONS = {
        "multi-agent": ["multi agent", "multiple agents", "multiagent", "agent collaboration", "agent system"],
        "llm": ["large language model", "language model", "gpt", "transformer", "language model"],
        "agent": ["agent", "ai agent", "autonomous agent", "intelligent agent"],
        "rag": ["retrieval augmented", "retrieval", "knowledge retrieval", "rag"],
        "memory": ["memory", "long-term memory", "short-term memory", "context memory"],
        "planning": ["planning", "task planning", "reasoning", "reasoning chain"],
        "evaluation": ["evaluation", "assessment", "benchmark", "metrics"],
        "collaboration": ["collaboration", "cooperation", "teamwork", "coordination"],
        "consensus": ["consensus", "agreement", "voting", "negotiation"],
        "proactive": ["proactive", "anticipatory", "prediction", "user intent"],
        "security": ["security", "safety", "jailbreak", "adversarial", "attack"],
        "optimization": ["optimization", "improvement", "self-tuning", "adaptation"],
        "continual": ["continual", "continuous learning", "lifelong", "incremental"],
        "orchestration": ["orchestration", "coordination", "management", "workflow"],
    }

    def expand(self, query: str) -> list[str]:
        """Expand query with synonyms and related terms.

        Returns:
            List of expanded queries
        """
        query_lower = query.lower()
        expanded_queries = [query]  # Original query

        # Check for known terms and expand
        for term, synonyms in self.EXPANSIONS.items():
            if term in query_lower:
                for syn in synonyms[:2]:  # Limit expansions
                    # Replace term with synonym
                    expanded = query_lower.replace(term, syn)
                    if expanded != query_lower and expanded not in expanded_queries:
                        expanded_queries.append(expanded)

        return expanded_queries[:5]  # Limit to 5 queries
