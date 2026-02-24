"""Paper data model for academic paper storage and retrieval."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Paper:
    """Academic paper model with metadata and optional embedding."""

    id: str
    title: str
    summary: str
    authors: list[str] = field(default_factory=list)
    published: str = ""
    updated: str = ""
    pdf_url: str = ""
    categories: list[str] = field(default_factory=list)
    primary_category: str = ""
    embedding: list[float] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "authors": self.authors,
            "published": self.published,
            "updated": self.updated,
            "pdf_url": self.pdf_url,
            "categories": self.categories,
            "primary_category": self.primary_category,
            "embedding": self.embedding,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Paper":
        """Create Paper from dictionary."""
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            authors=data.get("authors", []),
            published=data.get("published", ""),
            updated=data.get("updated", ""),
            pdf_url=data.get("pdf_url", ""),
            categories=data.get("categories", []),
            primary_category=data.get("primary_category", ""),
            embedding=data.get("embedding"),
        )

    @property
    def year(self) -> int | None:
        """Extract publication year from published date."""
        if self.published:
            try:
                return int(self.published[:4])
            except (ValueError, IndexError):
                pass
        return None

    @property
    def authors_str(self) -> str:
        """Get authors as comma-separated string."""
        return ", ".join(self.authors)

    def matches_category(self, category: str) -> bool:
        """Check if paper belongs to given category."""
        return category in self.categories

    def matches_year(self, year: int) -> bool:
        """Check if paper is from given year."""
        return self.year == year

    def matches_author(self, author_query: str) -> bool:
        """Check if any author matches the query (case-insensitive)."""
        author_lower = author_query.lower()
        return any(author_lower in a.lower() for a in self.authors)


# Category constants for common arXiv categories
class PaperCategory:
    """Common arXiv paper categories."""

    # Computer Science
    CS_AI = "cs.AI"  # Artificial Intelligence
    CS_CL = "cs.CL"  # Computation and Language
    CS_LG = "cs.LG"  # Machine Learning
    CS_IR = "cs.IR"  # Information Retrieval
    CS_NLP = "cs.CL"  # NLP (alias for cs.CL)
    CS_NE = "cs.NE"  # Neural and Evolutionary Computing
    CS_CR = "cs.CR"  # Cryptography and Security

    # Computer Vision
    CS_CV = "cs.CV"  # Computer Vision

    # All CS categories
    CS_ALL = [
        "cs.AI", "cs.CL", "cs.LG", "cs.IR", "cs.NE", "cs.CR", "cs.CV",
        "cs.AR", "cs.CC", "cs.CE", "cs.CG", "cs.GT", "cs.GR", "cs.HC",
        "cs.IT", "cs.LO", "cs.MA", "cs.MS", "cs.NA", "cs.OS", "cs.PF",
        "cs.PL", "cs.RO", "cs.SC", "cs.SD", "cs.SE", "cs.SY",
    ]
