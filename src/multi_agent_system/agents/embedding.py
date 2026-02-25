"""Semantic embedding using sentence-transformers for production-quality similarity search."""

from __future__ import annotations

import threading
from typing import Any

from .semantic_search_agent import EmbeddingModel


class SentenceTransformerEmbedding(EmbeddingModel):
    """Production-quality semantic embedding using sentence-transformers.

    Uses 'all-MiniLM-L6-v2' model for fast, high-quality embeddings.
    Thread-safe model loading and caching.
    """

    _instance: "SentenceTransformerEmbedding | None" = None
    _lock = threading.Lock()

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str | None = None,
    ) -> None:
        """Initialize embedding model.

        Args:
            model_name: Name of the sentence-transformers model
            device: Device to use ('cpu', 'cuda', or None for auto)
        """
        self.model_name = model_name
        self._device = device
        self._model = None
        self._model_loaded = False

    def _load_model(self) -> Any:
        """Lazy load the model (thread-safe)."""
        if self._model_loaded:
            return self._model

        with self._lock:
            if self._model_loaded:
                return self._model

            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name, device=self._device)
            self._model_loaded = True
            return self._model

    def embed(self, text: str) -> list[float]:
        """Generate embedding vector for text."""
        model = self._load_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for multiple texts."""
        model = self._load_model()
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return [emb.tolist() for emb in embeddings]

    @classmethod
    def get_instance(cls, model_name: str = "all-MiniLM-L6-v2") -> "SentenceTransformerEmbedding":
        """Get singleton instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(model_name)
            return cls._instance


class BM25KeywordSearch:
    """BM25-based keyword search for hybrid retrieval.

    BM25 is a ranking function used for relevance scoring in information retrieval.
    Complements semantic search by capturing exact keyword matches.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        """Initialize BM25.

        Args:
            k1: Term frequency saturation parameter
            b: Length normalization parameter
        """
        self.k1 = k1
        self.b = b
        self._doc_lengths: dict[str, float] = {}
        self._avg_doc_length: float = 0.0
        self._doc_freqs: dict[str, int] = {}
        self._total_docs: int = 0
        self._documents: dict[str, str] = {}

    def add_document(self, doc_id: str, text: str) -> None:
        """Add a document to the index."""
        self._documents[doc_id] = text.lower()

        # Tokenize
        tokens = text.lower().split()
        self._doc_lengths[doc_id] = len(tokens)

        # Document frequencies
        for token in set(tokens):
            self._doc_freqs[token] = self._doc_freqs.get(token, 0) + 1

        self._total_docs = len(self._documents)

        if self._total_docs > 0:
            self._avg_doc_length = sum(self._doc_lengths.values()) / self._total_docs

    def search(self, query: str, doc_ids: list[str] | None = None, top_k: int = 10) -> list[tuple[str, float]]:
        """Search for documents matching query.

        Returns:
            List of (doc_id, score) tuples
        """
        if not self._documents:
            return []

        query_tokens = query.lower().split()
        scores: dict[str, float] = {}

        docs_to_search = doc_ids if doc_ids else self._documents.keys()

        for doc_id in docs_to_search:
            if doc_id not in self._documents:
                continue

            doc_text = self._documents[doc_id]
            doc_tokens = doc_text.split()
            doc_len = self._doc_lengths.get(doc_id, 0)

            score = 0.0
            for token in query_tokens:
                if token not in self._doc_freqs:
                    continue

                tf = doc_tokens.count(token)
                if tf == 0:
                    continue

                # IDF calculation
                df = self._doc_freqs[token]
                idf = self._total_docs / df
                idf = max(0, (self._total_docs - df + 0.5) / (df + 0.5))

                # BM25 term frequency component
                tf_component = (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * doc_len / self._avg_doc_length))

                score += idf * tf_component

            if score > 0:
                scores[doc_id] = score

        # Sort by score
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]

    def count(self) -> int:
        """Get number of indexed documents."""
        return len(self._documents)
