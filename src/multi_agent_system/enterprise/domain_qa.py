"""Domain-specific QA RAG system.

Combines RAG with multi-agent collaboration for domain-specific question answering.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DomainConfig:
    """Configuration for a domain."""

    name: str
    description: str
    knowledge_sources: list[str] = field(default_factory=list)
    required_entities: list[str] = field(default_factory=list)
    answer_format: str = "default"  # default, structured, narrative


@dataclass
class QAContext:
    """Context for a QA request."""

    query: str
    domain: str | None = None
    user_id: str | None = None
    history: list[dict] = field(default_factory=list)


@dataclass
class QAResult:
    """Result of a QA request."""

    answer: str
    confidence: float = 0.0
    sources: list[dict] = field(default_factory=list)
    entities_extracted: list[str] = field(default_factory=list)
    suggested_followups: list[str] = field(default_factory=list)


class DomainQASystem:
    """Domain-specific QA system with RAG and multi-agent collaboration.

    Features:
    - Domain-specific knowledge sources
    - Multi-stage retrieval
    - Entity-aware answering
    - Source citation
    """

    def __init__(self) -> None:
        self.domains: dict[str, DomainConfig] = {}
        self.knowledge_base: dict[str, Any] = {}
        self._load_domains()

    def _load_domains(self) -> None:
        """Load domain configurations."""
        domain_file = Path("./data/domains.json")
        if domain_file.exists():
            with open(domain_file) as f:
                data = json.load(f)
                for name, config in data.items():
                    self.domains[name] = DomainConfig(**config)

    def register_domain(self, config: DomainConfig) -> None:
        """Register a new domain."""
        self.domains[config.name] = config

    def add_knowledge(self, domain: str, source_name: str, content: list[dict]) -> None:
        """Add knowledge source to a domain."""
        if domain not in self.knowledge_base:
            self.knowledge_base[domain] = {}

        self.knowledge_base[domain][source_name] = content

    def answer(
        self,
        query: str,
        domain: str | None = None,
        context: dict | None = None,
    ) -> QAResult:
        """Answer a question using RAG and multi-agent collaboration.

        Args:
            query: User question
            domain: Specific domain (optional)
            context: Additional context

        Returns:
            QAResult with answer and sources
        """
        context = context or {}

        # Stage 1: Query understanding (would use IntentClassificationAgent)
        entities = self._extract_entities(query)

        # Stage 2: Multi-source retrieval
        sources = self._retrieve_sources(query, entities, domain)

        # Stage 3: Answer synthesis
        answer = self._synthesize_answer(query, sources, entities)

        # Stage 4: Generate follow-up suggestions
        followups = self._generate_followups(query, answer)

        return QAResult(
            answer=answer,
            sources=sources,
            confidence=min(1.0, len(sources) / 3),  # Simplified confidence
            entities_extracted=entities,
            suggested_followups=followups,
        )

    def _extract_entities(self, query: str) -> list[str]:
        """Extract key entities from query (simplified)."""
        # In production, would use EntityExtractionAgent
        words = query.lower().split()
        # Simple keyword extraction
        important = [w for w in words if len(w) > 4]
        return important[:5]

    def _retrieve_sources(
        self,
        query: str,
        entities: list[str],
        domain: str | None,
    ) -> list[dict]:
        """Retrieve relevant sources from knowledge base."""
        sources = []

        # Search papers if available
        papers_file = Path("./data/papers.json")
        if papers_file.exists():
            with open(papers_file) as f:
                papers = json.load(f)

            # Simple relevance scoring
            query_lower = query.lower()
            for paper in papers[:50]:  # Check top 50
                score = 0
                text = (paper.get("title", "") + " " + paper.get("summary", "")).lower()

                # Query match
                for word in query_lower.split():
                    if word in text:
                        score += 1

                # Entity match
                for entity in entities:
                    if entity in text:
                        score += 2

                if score > 0:
                    sources.append({
                        "type": "paper",
                        "title": paper.get("title"),
                        "id": paper.get("id"),
                        "score": score,
                        "content": paper.get("summary", "")[:200],
                    })

        # Sort by score
        sources.sort(key=lambda x: -x.get("score", 0))

        return sources[:5]

    def _synthesize_answer(
        self,
        query: str,
        sources: list[dict],
        entities: list[str],
    ) -> str:
        """Synthesize answer from sources."""
        if not sources:
            return "I couldn't find relevant information to answer your question."

        # Build answer
        answer_parts = []

        # Use top source
        top_source = sources[0]
        if top_source.get("type") == "paper":
            answer_parts.append(f"Based on the paper: {top_source.get('title')}")
            answer_parts.append(top_source.get("content", ""))

        # Add entity context
        if entities:
            answer_parts.append(f"\nKey concepts: {', '.join(entities[:3])}")

        return "\n\n".join(answer_parts)

    def _generate_followups(self, query: str, answer: str) -> list[str]:
        """Generate follow-up question suggestions."""
        followups = []

        # Generate based on answer content
        if "paper" in answer.lower():
            followups.append("Would you like more details about this paper?")
            followups.append("Should I search for related papers?")

        if len(query.split()) < 10:  # Short query
            followups.append("Could you provide more details about your question?")

        return followups[:3]

    def get_domain_info(self, domain: str) -> DomainConfig | None:
        """Get domain configuration."""
        return self.domains.get(domain)

    def list_domains(self) -> list[str]:
        """List all registered domains."""
        return list(self.domains.keys())


# Global instance
_domain_qa: DomainQASystem | None = None


def get_domain_qa() -> DomainQASystem:
    """Get global domain QA system instance."""
    global _domain_qa
    if _domain_qa is None:
        _domain_qa = DomainQASystem()
    return _domain_qa
