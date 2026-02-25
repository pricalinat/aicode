"""Memory system for multi-agent collaboration.

Provides short-term and long-term memory capabilities.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class MemoryEntry:
    """A single memory entry."""

    id: str
    content: str
    memory_type: str  # "short_term", "long_term", "user_profile", "context"
    timestamp: float = field(default_factory=time.time)
    importance: float = 1.0  # 0-1 importance score
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type,
            "timestamp": self.timestamp,
            "importance": self.importance,
            "metadata": self.metadata,
            "embedding": self.embedding,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryEntry":
        return cls(
            id=data["id"],
            content=data["content"],
            memory_type=data["memory_type"],
            timestamp=data.get("timestamp", time.time()),
            importance=data.get("importance", 1.0),
            metadata=data.get("metadata", {}),
            embedding=data.get("embedding"),
        )


class ShortTermMemory:
    """Short-term memory for current session context.

    Stores conversation history and current task context.
    """

    def __init__(self, max_size: int = 100) -> None:
        self.max_size = max_size
        self._memories: list[MemoryEntry] = []

    def store(self, content: str, importance: float = 1.0, metadata: dict | None = None) -> str:
        """Store a new short-term memory."""
        import uuid

        entry = MemoryEntry(
            id=str(uuid.uuid4())[:12],
            content=content,
            memory_type="short_term",
            importance=importance,
            metadata=metadata or {},
        )
        self._memories.append(entry)

        # Trim if needed
        if len(self._memories) > self.max_size:
            self._memories = self._memories[-self.max_size :]

        return entry.id

    def retrieve(self, query: str | None = None, limit: int = 10) -> list[MemoryEntry]:
        """Retrieve recent memories."""
        if query is None:
            return self._memories[-limit:]
        # Simple keyword matching
        results = [m for m in self._memories if query.lower() in m.content.lower()]
        return results[-limit:]

    def get_context(self, max_tokens: int = 2000) -> str:
        """Get context string for LLM."""
        context_parts = []
        for memory in reversed(self._memories[-10:]):
            context_parts.append(f"[{memory.memory_type}] {memory.content}")
        return "\n".join(context_parts[-max_tokens:])

    def clear(self) -> None:
        """Clear all short-term memories."""
        self._memories.clear()

    def __len__(self) -> int:
        return len(self._memories)


class LongTermMemory:
    """Long-term memory with persistent storage.

    Stores user profiles, learned knowledge, and important facts.
    """

    def __init__(self, storage_path: str = "./data/memory") -> None:
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, MemoryEntry] = {}
        self._load_index()

    def _load_index(self) -> None:
        """Load memory index."""
        index_file = self.storage_path / "index.json"
        if index_file.exists():
            with open(index_file) as f:
                index = json.load(f)
                # Load metadata only (lazy load content)
                for entry_data in index:
                    self._cache[entry_data["id"]] = MemoryEntry.from_dict(entry_data)

    def _save_index(self) -> None:
        """Save memory index."""
        index_file = self.storage_path / "index.json"
        index = [entry.to_dict() for entry in self._cache.values()]
        with open(index_file, "w") as f:
            json.dump(index, f, indent=2)

    def store(
        self,
        content: str,
        memory_type: str = "long_term",
        importance: float = 1.0,
        metadata: dict | None = None,
    ) -> str:
        """Store a long-term memory."""
        import uuid

        entry = MemoryEntry(
            id=str(uuid.uuid4())[:12],
            content=content,
            memory_type=memory_type,
            importance=importance,
            metadata=metadata or {},
        )
        self._cache[entry.id] = entry
        self._save_index()
        return entry.id

    def retrieve(self, query: str | None = None, memory_type: str | None = None, limit: int = 10) -> list[MemoryEntry]:
        """Retrieve long-term memories."""
        results = list(self._cache.values())

        # Filter by type
        if memory_type:
            results = [m for m in results if m.memory_type == memory_type]

        # Filter by query (simple contains)
        if query:
            results = [m for m in results if query.lower() in m.content.lower()]

        # Sort by importance and time
        results.sort(key=lambda m: (-m.importance, -m.timestamp))

        return results[:limit]

    def get_user_profile(self, user_id: str) -> dict[str, Any]:
        """Get user profile."""
        memories = self.retrieve(memory_type="user_profile")
        for m in memories:
            if m.metadata.get("user_id") == user_id:
                return m.metadata
        return {}

    def update_user_profile(self, user_id: str, updates: dict[str, Any]) -> None:
        """Update user profile."""
        # Find existing profile
        memories = self.retrieve(memory_type="user_profile")
        profile_entry = None
        for m in memories:
            if m.metadata.get("user_id") == user_id:
                profile_entry = m
                break

        if profile_entry:
            # Update existing
            profile_entry.metadata.update(updates)
            profile_entry.content = str(profile_entry.metadata)
        else:
            # Create new
            self.store(
                content=str(updates),
                memory_type="user_profile",
                importance=1.0,
                metadata={"user_id": user_id, **updates},
            )
        self._save_index()

    def __len__(self) -> int:
        return len(self._cache)


class MemorySystem:
    """Unified memory system combining short-term and long-term memory."""

    def __init__(self, storage_path: str = "./data/memory") -> None:
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(storage_path)

    def remember(self, content: str, memory_type: str = "short_term", importance: float = 1.0, **metadata: Any) -> str:
        """Store a memory."""
        if memory_type == "short_term":
            return self.short_term.store(content, importance, metadata)
        return self.long_term.store(content, memory_type, importance, metadata)

    def recall(self, query: str | None = None, memory_type: str | None = None, limit: int = 10) -> list[MemoryEntry]:
        """Recall memories."""
        if memory_type == "short_term" or memory_type is None:
            if not memory_type:
                # Search both
                st_results = self.short_term.retrieve(query, limit)
                lt_results = self.long_term.retrieve(query, None, limit)
                combined = st_results + lt_results
                combined.sort(key=lambda m: (-m.importance, -m.timestamp))
                return combined[:limit]
            return self.short_term.retrieve(query, limit)
        return self.long_term.retrieve(query, memory_type, limit)

    def get_context(self, max_tokens: int = 2000) -> str:
        """Get full context for LLM."""
        st_context = self.short_term.get_context(max_tokens)
        lt_context_parts = []
        for memory in self.long_term.retrieve(importance=0.8, limit=5):
            lt_context_parts.append(f"[{memory.memory_type}] {memory.content}")

        return f"=== Short-term Context ===\n{st_context}\n\n=== Long-term Knowledge ===\n" + "\n".join(
            lt_context_parts
        )

    def clear_session(self) -> None:
        """Clear short-term memory (new session)."""
        self.short_term.clear()


# Global instance
_memory_system: MemorySystem | None = None


def get_memory_system(storage_path: str = "./data/memory") -> MemorySystem:
    """Get global memory system instance."""
    global _memory_system
    if _memory_system is None:
        _memory_system = MemorySystem(storage_path)
    return _memory_system
